from .base import GenAIProvider
from openai import OpenAI

class OpenAIProvider(GenAIProvider):
    def __init__(self, api_key: str):
        self.client = OpenAI(
            api_key=api_key,
        )

    def generate_text(self, model: str, prompt: str, system_prompt:str, temperature, max_tokens) -> str:
        conversation = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        response = self.client.chat.completions.create(
            model=model,
            messages=conversation,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False
        )
        return response.choices[0].message["content"]
