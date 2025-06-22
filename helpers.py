import gradio as gr
import os
import fitz
import pymupdf
import openai
from PIL import Image
import pytesseract
import io
from google import genai
from google.api_core import exceptions
from config import ACTIVE_PROVIDER, API_KEYS, MODEL_TO_USE
from providers.openai_provider import OpenAIProvider
from providers.google_provider import GoogleProvider

def get_provider(name: str):
    if name == "openai":
        return OpenAIProvider(API_KEYS["openai_api_key"])
    elif name == "gemini":
        return GoogleProvider(API_KEYS["gemini_api_key"])
    else:
        raise ValueError(f"Unsupported provider: {name}")
    
provider = get_provider(ACTIVE_PROVIDER)

def get_prompt_text(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
            headers_to_be_removed = [
                "[ PROFILE ]",
                "[ DIRECTIVE ]",
                "[ CONTEXT ]",
                "[ WORKFLOW ]",
                "[ CONSTRAINT ]",
                "[ OUTPUT STYLE ]",
                "[ EXAMPLE ]"
            ]

            for header in headers_to_be_removed:
                content = content.replace(header, "")
            
            content = content.replace("\n", "")
        return content
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def generate_response(
    message: str,
    system_prompt: str, 
    temperature: float = 0.5, 
    max_tokens: int = 6000,
    contents: list = []
):
    response = provider.generate_text(
        model=MODEL_TO_USE,
        prompt=message,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        contents=contents
    )
    return response       