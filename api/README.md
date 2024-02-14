# FastAPI API to interact with the OpenAI Assistants API

## Introduction

The idea of this API is to provide a way to interact with the Azure OpenAI Assistants API. The API will be called from a Copilot Studio bot via an HTTP call.

## Available endpoints

The API has the following endpoints:
- `create_thread`: creates a new thread for the Assistant and return the thread ID
- `add_message`: adds a message to the thread and returns the response from the Assistant

## Assistant

The assistant will not be created in this code. The assistant ID of an assistant that already exists in the Azure region of choice will be used. If you do not have an assistant, create one in the Azure OpenAI Assistants playground. You do not gave to enable any functions or tools, we will simply use a default assistant based on the gpt-4-preview model.

