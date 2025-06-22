from .base import GenAIProvider
from google import genai
from google.genai import types

class GoogleProvider(GenAIProvider):
    def __init__(self, api_key: str):
        self.client = genai.Client(
            api_key=api_key,
        )

    def upload_file_to_model(
        self,
        file_path
    ):
        file = self.client.files.upload(file=file_path)
        return file


    def generate_text(
        self, 
        model: str, 
        prompt: str, 
        system_prompt: str, 
        temperature: float = 0.5, 
        max_tokens: int = 5000,
        contents: list = []
    ) -> str:
        contents.append(prompt)
        try:
            response = self.client.models.generate_content(
                model=model,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                    max_output_tokens=max_tokens
                ),
                contents=contents
            )
            return response.text
        except:
            return "Unable to generate text/content because the given API KEY is not active"
