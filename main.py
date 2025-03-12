from fastapi import FastAPI
from pydantic import BaseModel

from ollama import chat
from ollama import ChatResponse

import re

app = FastAPI()


class TextRequest(BaseModel):
    text: str


models = ["llama3.2", "deepseek-r1:1.5b", "phi4", "phi4-mini", "gemma3:27b"]
model = models[3]
sensitive_data_prompt_template = ('Given a text containing sensitive information, return a comma-separated list of the '
                                  'sensitive information, the list should only contain single words, no phrases. This '
                                  'is the text: ')


def detect_sensitive_words(text):
    sensitive_data_response: ChatResponse = chat(model=model, messages=[{
            'role': 'user',
            'content': sensitive_data_prompt_template + text}])
    sensitive_data = sensitive_data_response.message.content
    sensitive_data_list = sensitive_data.split(",")
    sensitive_data_list = [x[1:] if x.startswith(" ") else x for x in sensitive_data_list]
    print(sensitive_data_list)
    return sensitive_data_list


def replace_sensitive_words(text):
    # Replace detected words with placeholders
    return re.sub(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b", "[REDACTED]", text)


@app.post("/detect")
def detect_sensitive_info(request: TextRequest):
    sensitive_words = detect_sensitive_words(request.text)
    return {"sensitive_words": sensitive_words}


@app.post("/replace")
def replace_sensitive_info(request: TextRequest):
    anonymized_text = replace_sensitive_words(request.text)
    return {"anonymized_text": anonymized_text}
