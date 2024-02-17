from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security.api_key import APIKeyHeader, APIKey
from pydantic import BaseModel
from typing import Optional, List
import logging
import uvicorn
from openai import AzureOpenAI
from dotenv import load_dotenv
import os
import asyncio
import json
import base64

load_dotenv("../.env")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define API key header and check
API_KEY = os.getenv("API_KEY")
if API_KEY is None:
    raise ValueError("API_KEY environment variable not set")

# caller needs to pass http header with key "access_token" and value of API_KEY
API_KEY_NAME = "access_token"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

# Check API key helper for POST methods
async def get_api_key(api_key_header: str = Depends(api_key_header)):
    if api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )

app = FastAPI()

# Pydantic models
class MessageRequest(BaseModel):
    message: str
    thread_id: str

class MessageResponse(BaseModel):
    message: str
    images: Optional[List[str]] = []

class ThreadResponse(BaseModel):
    thread_id: str

client = AzureOpenAI(
    api_key=os.getenv('AZURE_OPENAI_API_KEY'),
    azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
    api_version=os.getenv('AZURE_OPENAI_API_VERSION')
)

# this refers to an assistant without functions
# it does have code interpreter
assistant_id = "asst_fRWdahKY1vWamWODyKnwtXxj"

# helper to wait for a thread run to complete
async def wait_for_run(run, thread_id):
    while run.status == 'queued' or run.status == 'in_progress':
        run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
        )
        await asyncio.sleep(0.5)

    return run.status, run.id

# Example endpoint using different models for request and response
@app.post("/message/", response_model=MessageResponse)
async def message(item: MessageRequest, api_key: APIKey = Depends(get_api_key)):
    logger.info(f"Message received: {item.message}")

    # try to send message to assistant
    try:
        message = client.beta.threads.messages.create(
            thread_id=item.thread_id,
            role="user",
            content=item.message
        )
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return MessageResponse(message="Your message could not be sent. Try again or start over.")

    
    

    try:
        run = client.beta.threads.runs.create(
            thread_id=item.thread_id,
            assistant_id=assistant_id # use the assistant id defined aboe
        )
        status, run_id = await asyncio.wait_for(wait_for_run(run, item.thread_id), timeout=60)
    except asyncio.TimeoutError:
        status = 'timeout'
        logger.info(f"Run timed out")

        # try to cancel the run
        run = client.beta.threads.runs.cancel(
            thread_id=item.thread_id,
            run_id=run.id
            )

    except Exception as e:
        status = 'error'
        logger.error(f"Error running thread: {e}")

    # inspect the run status
    if status == 'completed':
        text = ""
        images = []

        # only pick the last message and convert to JSON
        messages = client.beta.threads.messages.list(limit=1, thread_id=item.thread_id)
        messages_json = json.loads(messages.model_dump_json())

        # message content is an array with text and possibly multiple images
        message_content = messages_json['data'][0]['content']

        for content in message_content:
            if 'text' in content:
                text = content['text']['value']

            # Check for images in response
            if 'image_file' in content:
                file_id = content['image_file']['file_id']
                logger.info(f"Image file ID: {file_id}")

                # download file from assistant
                file_content = client.files.content(file_id).read()
                logger.info(f"File content: {file_content[:100]}")

                # convert to base64 string for web display
                file_content = base64.b64encode(file_content).decode('utf-8')
                logger.info(f"File content (base64): {file_content[:100]}")

                # prepend base64 URL prefix
                file_content = f"data:image/png;base64,{file_content}"
                logger.info(f"File content (base64 URL): {file_content[:100]}")

                images.append(file_content)

        if images:
            logger.info(f"Assistant response with images: {text}")
            return MessageResponse(message=text, images=images)
        else:
            logger.info(f"Assistant response with text only: {text}")
            return MessageResponse(message=text)
    elif status == 'timeout':
        logger.info(f"Assistant response timed out.")
        return MessageResponse(message="Assistant response timed out. Try again or start over.")
    else:
        logger.info(f"Assistant reported {status}.")
        return MessageResponse(message=f"Assistant reported {status}. Try again or start over.")


@app.post("/thread/", response_model=ThreadResponse)
async def thread(api_key: APIKey = Depends(get_api_key)):
    thread = client.beta.threads.create()
    logger.info(f"Thread created with ID: {thread.id}")
    return ThreadResponse(thread_id=thread.id)

# Uvicorn startup
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8324)
