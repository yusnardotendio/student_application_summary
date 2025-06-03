from .base import GenAIProvider
from google import genai
from google.genai import types

class GoogleProvider(GenAIProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key


    def generate_text(self, prompt: str, system_prompt: str, model: str, temperature, max_tokens) -> str:
        client = genai.Client(api_key="GEMINI_API_KEY")
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                max_output_tokens=max_tokens
            ),
            contents=prompt
        )
        return response.text
