from .base import GenAIProvider
from google import genai
from google.genai import types

class GoogleProvider(GenAIProvider):
    def __init__(self, api_key: str):
        self.client = genai.Client(
            api_key=api_key,
        )


    def generate_text(self, model: str, prompt: str, system_prompt: str, temperature: float = 0.5, max_tokens: int = 5000) -> str:
        response = self.client.models.generate_content(
            model=model,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                max_output_tokens=max_tokens
            ),
            contents=prompt
        )
        return response.text
