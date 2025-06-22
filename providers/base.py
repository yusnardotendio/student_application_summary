class GenAIProvider:
    def upload_file_to_model(
        self,
        file_path
    ):
        raise NotImplementedError("Subclasses must implement upload_file_to_model()")
        
    def generate_text(
        self, 
        model: str, 
        prompt: str, 
        system_prompt:str, 
        temperature: float = 0.5, 
        max_tokens: int = 5000,
        contents: list = []
    ) -> str:
        raise NotImplementedError("Subclasses must implement generate_text()")