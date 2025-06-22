from .base import GenAIProvider
from openai import OpenAI

class OpenAIProvider(GenAIProvider):
    def __init__(self, api_key: str):
        self.client = OpenAI(
            api_key=api_key,
        )

    def upload_file_to_model(
        self,
        file_path
    ):
        file_result = self.client.files.create(
            file=open(file_path, "rb"), 
            purpose="assistants"
        )
        return file_result.id
    
    def generate_text(
        self, 
        model: str, 
        prompt: str, 
        system_prompt:str, 
        temperature: float = 0.5,
        max_tokens: int = 5000,
        contents: list = []
    ) -> str:
        file_inputs = [{"type": "input_file", "file_id": file_id} for file_id in contents]
        file_inputs.append({
            "type": "input_text",
            "text": prompt
        })
        conversation = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": file_inputs}
        ]
        
        response = self.client.responses.create(
            model=model,
            input=conversation,
            temperature=temperature,
            max_output_tokens=max_tokens,
            stream=False
        )
        return response.output_text

    # def generate_text(
    #     self, 
    #     model: str, 
    #     prompt: str, 
    #     system_prompt:str, 
    #     temperature: float = 0.5,
    #     max_tokens: int = 5000,
    #     contents: list = []
    # ) -> str:
    #     conversation = [
    #         {"role": "system", "content": system_prompt},
    #         {"role": "user", "content": prompt}
    #     ]
        
    #     response = self.client.chat.completions.create(
    #         model=model,
    #         messages=conversation,
    #         temperature=temperature,
    #         max_tokens=max_tokens,
    #         stream=False
    #     )
    #     return response.choices[0].message.content
