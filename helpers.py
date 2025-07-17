from config import ACTIVE_PROVIDER, API_KEYS, MODEL_TO_USE
from providers.openai_provider import OpenAIProvider
from providers.google_provider import GoogleProvider
from database.evaluation_result_db import EvaluationResultDB 
import gradio as gr

db = EvaluationResultDB()

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

def get_decision(evaluation_summary):
    instruction_prompt = get_prompt_text("prompt_text/get_decision_from_evaluation_summary.txt")  
    final_prompt = f"""
    {instruction_prompt}
    {evaluation_summary}
    """
    decision = generate_response(
        final_prompt, 
        system_prompt="You judge an evaluation summary by providing answer of ACCEPTED or REJECTED"
    )

    if len(decision) >= 9:
        return 'REJECTED'

    return decision

def save_evaluation(data, markdown):
    db.add_result(data['applicant_name'], markdown, data['created_at'], data['decision'])
    return f"Evaluation saved successfully!"

def show_markdown(selected_row):
    try:
        if selected_row is None or selected_row.empty:
            return "No row selected."

        row_id = int(selected_row.iloc[0]["id"])
        print(f"Row ID: {row_id}")
    except Exception as e:
        print("Error extracting ID:", e)
        return "Failed to extract row ID."

    result = db.get_result(row_id)
    return result[4] if result else "Result not found."

def get_df():
    return db.get_dataframe()

def get_result(result_id):
    return db.get_result(result_id)
