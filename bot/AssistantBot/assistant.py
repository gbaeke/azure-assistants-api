import os
import time
import json
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv("../../.env")

# Create Azure OpenAI client
client = AzureOpenAI(
    api_key=os.getenv('AZURE_OPENAI_API_KEY'),
    azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
    api_version=os.getenv('AZURE_OPENAI_API_VERSION')
)

# hard coded assistant id
assistant_id = "asst_Ol9RnLsiDCD6khGtF05LarPm"

# provide Chroma db and helper search function
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import AzureOpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

pdf = PyPDFLoader("./pdfs/Innovatek.pdf").load()
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
documents = text_splitter.split_documents(pdf)
db = Chroma.from_documents(documents, AzureOpenAIEmbeddings(client=client, model="embedding", api_version="2023-05-15"))
print("Database created... (memory)")

# function to retrieve HR questions
def hr_query(query):
    docs = db.similarity_search(query, k=3)
    docs_dict = [doc.__dict__ for doc in docs]
    return json.dumps(docs_dict)

# create thread and return id
def create_thread():
    thread = client.beta.threads.create()
    return thread.id

def wait_for_run(run, thread_id):
    while run.status == 'queued' or run.status == 'in_progress':
        run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
        )
        time.sleep(0.5)

    return run

def check_for_tools(run, thread_id):
    if run is None or thread_id is None:
        return None

    if run.required_action:
        # get tool calls and print them
        # check the output to see what tools_calls contains
        tool_calls = run.required_action.submit_tool_outputs.tool_calls
        print("Tool calls:", tool_calls)

        # we might need to call multiple tools
        # the assistant API supports parallel tool calls
        # we account for this here although we only have one tool call
        tool_outputs = []
        for tool_call in tool_calls:
            func_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            # call the function with the arguments provided by the assistant
            if func_name == "request_raise":
                result = "Raise requested. It will be approved by your manager for sure."
            elif func_name == "hr_query":
                result = hr_query(**arguments)
            
            # append the results to the tool_outputs list
            # you need to specify the tool_call_id so the assistant knows which tool call the output belongs to
            tool_outputs.append({
                "tool_call_id": tool_call.id,
                "output": json.dumps(result)
            })

        # now that we have the tool call outputs, pass them to the assistant
        run = client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread_id,
            run_id=run.id,
            tool_outputs=tool_outputs
        )

        # now we wait for the run again
        run = wait_for_run(run, thread_id)

        return run
    else:
        return None

# send message to assistant
def send_message(thread_id, message):
    if thread_id is None:
        return None

    # create message
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message
    )

    # create a run 
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id # use the assistant id defined in the first cell
    )

    # wait for the run to complete
    run = wait_for_run(run, thread_id)

    return run


def return_message(thread_id):
    if thread_id is None:
        print("Thread id is None")
        return "No response"
    
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    messages_json = json.loads(messages.model_dump_json())

    # get first message
    message_content = messages_json['data'][0]['content']
    print(message_content)

    text = message_content[0].get('text', {}).get('value')

    return text