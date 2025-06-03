class GenAIProvider:
    def generate_text(self, prompt: str) -> str:
        raise NotImplementedError("Subclasses must implement generate_text()")