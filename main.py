import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ollama import chat
from ollama import ChatResponse

import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to your frontend's actual URL for better security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TextRequest(BaseModel):
    text: str


models = ["llama3.2", "deepseek-r1:1.5b", "phi4", "phi4-mini", "gemma3:27b"]
model = models[3]
sensitive_data_prompt_template = ('Given a text containing sensitive information, return a comma-separated list of the '
                                  'sensitive information, the list should only contain single words, no phrases. This '
                                  'is the text: ')

place_holder_prompt_template = ("You get a comma-separated list of attributes and your task is to find a generic, "
                                "descriptive, short place holder for each element. Return a JSON formatted key-value "
                                "pairs, where the key is the original element. This is the list: ")
opts = options = {"temperature": 0}


def detect_sensitive_words(text):
    sensitive_data_response: ChatResponse = chat(model=model, messages=[{
        'role': 'user',
        'content': sensitive_data_prompt_template + text}], options=opts)
    sensitive_data = sensitive_data_response.message.content
    sensitive_data_list = sensitive_data.split(",")
    sensitive_data_list = [x[1:] if x.startswith(" ") else x for x in sensitive_data_list]
    print(sensitive_data_list)
    return sensitive_data_list


def replace_sensitive_words(text):
    # Replace detected words with placeholders
    return re.sub(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b", "[REDACTED]", text)


def find_place_holders(sensitive_data):
    place_holder_response: ChatResponse = chat(model=model, messages=[{
        'role': 'user',
        'content': place_holder_prompt_template + sensitive_data}], options=opts)
    place_holders = str(place_holder_response.message.content)
    if place_holders[:7] == '```json' and place_holders[-3:] == '```':
        place_holders = place_holders[7:-3]
    print(place_holders)
    place_holders_dict = json.loads(place_holders)
    place_holders_dict = {key: "[{}]".format(place_holders_dict[key]) for key in place_holders_dict}
    print(place_holders_dict)
    return place_holders_dict


@app.post("/detect")
def detect_sensitive_info(request: TextRequest):
    print("--------------------------------------")
    print(request.text)
    print("--------------------------------------")
    sensitive_words = detect_sensitive_words(request.text)
    return {"sensitive_words": sensitive_words}


@app.post("/place_holder")
def replace_sensitive_info(request: TextRequest):
    print("--------------------------------------")
    print(request.text)
    print("--------------------------------------")
    place_holders = find_place_holders(request.text)
    return {"place_holders": place_holders}


@app.post("/hello")
def hello():
    print("--------------------------------------")
    print("HELLO")
    print("--------------------------------------")
    return {"message": "Hello World!"}
