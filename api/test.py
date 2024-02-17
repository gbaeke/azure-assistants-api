import requests
import random
import string
from concurrent.futures import ThreadPoolExecutor

# define an array of strings with questions
questions = [
    "What is the capital of France?",
    "What is the capital of Germany?",
    "What is the capital of Italy?",
    "What is the capital of Spain?",
    "What is the capital of Portugal?",
    "What is the capital of Belgium?",
    "What is the capital of Netherlands?",
    "What is the capital of Luxembourg?",
    "What is the capital of Switzerland?",
    "What is the capital of Austria?"
]

def create_thread():
    url = "http://127.0.0.1:8324/thread"
    headers = {
        "Content-Type": "application/json",
        "access_token": "12345678"
    }
    response = requests.post(url, headers=headers)
    return response.json().get("thread_id")

def send_request():
    url = "http://127.0.0.1:8324/message"
    headers = {
        "Content-Type": "application/json",
        "access_token": "12345678"
    }
    # pick random question from the array
    message = random.choice(questions)
    print(f"Sending message: {message}")
    
    data = {
        "message": message,
        "thread_id": create_thread()
    }
    response = requests.post(url, headers=headers, json=data)
    return str(response.status_code) + " " + response.json().get("message")

with ThreadPoolExecutor(max_workers=50) as executor:
    futures = [executor.submit(send_request) for _ in range(20)]

for future in futures:
    print(future.result())