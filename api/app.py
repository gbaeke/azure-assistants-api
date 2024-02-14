from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security.api_key import APIKeyHeader, APIKey
from pydantic import BaseModel
import logging
import uvicorn
from openai import AzureOpenAI
from dotenv import load_dotenv
import os
import time
import json

load_dotenv("../.env")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define API key header
API_KEY = os.getenv("API_KEY")

# Check for API key
if API_KEY is None:
    raise ValueError("API_KEY environment variable not set")

API_KEY_NAME = "access_token"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

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

class ThreadResponse(BaseModel):
    thread_id: str

client = AzureOpenAI(
    api_key=os.getenv('AZURE_OPENAI_API_KEY'),
    azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
    api_version=os.getenv('AZURE_OPENAI_API_VERSION')
)

# this refers to an assistant without functions
assistant_id = "asst_fRWdahKY1vWamWODyKnwtXxj"

def wait_for_run(run, thread_id):
    while run.status == 'queued' or run.status == 'in_progress':
        run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
        )
        time.sleep(0.5)

    return run

# Example endpoint using different models for request and response
@app.post("/message/", response_model=MessageResponse)
async def message(item: MessageRequest, api_key: APIKey = Depends(get_api_key)):
    logger.info(f"Message received: {item.message}")

    # Send message to assistant
    message = client.beta.threads.messages.create(
        thread_id=item.thread_id,
        role="user",
        content=item.message
    )

    run = client.beta.threads.runs.create(
        thread_id=item.thread_id,
        assistant_id=assistant_id # use the assistant id defined aboe
    )

    run = wait_for_run(run, item.thread_id)

    if run.status == 'completed':
        messages = client.beta.threads.messages.list(limit=1, thread_id=item.thread_id)
        messages_json = json.loads(messages.model_dump_json())
        message_content = messages_json['data'][0]['content']
        text = message_content[0].get('text', {}).get('value')
        return MessageResponse(message=text)
    else:
        return MessageResponse(message="Assistant reported an error.")


@app.post("/thread/", response_model=ThreadResponse)
async def thread(api_key: APIKey = Depends(get_api_key)):
    thread = client.beta.threads.create()
    logger.info(f"Thread created with ID: {thread.id}")
    return ThreadResponse(thread_id=thread.id)

# Uvicorn startup
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8324)
