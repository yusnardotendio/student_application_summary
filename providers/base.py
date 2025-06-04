class GenAIProvider:
    def generate_text(self, model: str, prompt: str, system_prompt:str, temperature: float = 0.5, max_tokens: int = 5000) -> str:
        raise NotImplementedError("Subclasses must implement generate_text()")