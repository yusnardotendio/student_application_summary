import gradio as gr
import os
from PyPDF2 import PdfReader
import openai 

openai.api_key = os.environ.get("GROQ_API_KEY")

def extract_text_from_pdf(files):
    reader = PdfReader(files)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def generate_response(message: str, system_prompt: str, temperature: float = 0.5, max_tokens: int = 512):
    conversation = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=conversation,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=False
    )

    return response.choices[0].message.content

def analyze_documents(resume_content, motivation_content, transctipt_content):
    file_text = resume_content + motivation_content + transctipt_content
    prompt = f"""
    Please analyze the following resume, transcript and motivation letter. Provide the following details:
    1. Extract relevant academic and extracurricular experiences
    2. Alignment with program goals or specialization tracks
    3. Flag missing or weak areas in the applicant's background
    4. A curriculum match score for each program section based on the applicant passed courses
    5. Highlight supporting evidence from transcripts that match applicant with the master program
    6. Overall recommendation summaries and confidence levels to assist the committee in final decisions
    Resume, Motivation letter, Transcript: {file_text}.
    """
    # Please update the promp later to a better one
    return generate_response(prompt, "You are an expert Admissions Committee Member for TUM Campus.")

# Gradio UI
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    with gr.Row():
        gr.Markdown("## 1. Upload PDFs")
        with gr.Column():
            resume_file = gr.File(label="Upload Resume (PDF)")
            resume_content = gr.Textbox(label="Parsed Resume Content", lines=10)
        with gr.Column():
            motivation_letter_file = gr.File(label="Upload Motivation Letter (PDF)")
            motivation_content = gr.Textbox(label="Parsed Motivation Letter Content", lines=10)
        with gr.Column():
            transcript_file = gr.File(label="Upload Transcript (PDF)")
            transctipt_content = gr.Textbox(label="Parsed Transcript Content", lines=10)
    with gr.Row():
        summarize_button = gr.Button("2. Summarize")
    with gr.Row():
        output = gr.Markdown()

    def process_file(file):
        if file is not None:
            file_type = file.name.split('.')[-1].lower()
            if file_type == 'pdf':
                return extract_text_from_pdf(file.name)
        
        return ""
    
    resume_file.upload(process_file, resume_file, resume_content)
    motivation_letter_file.upload(process_file, motivation_letter_file, motivation_content)
    transcript_file.upload(process_file, transcript_file, transctipt_content)

    summarize_button.click(
        fn=analyze_documents, 
        inputs=[resume_content, motivation_content, transctipt_content], 
        outputs=[output]
    )

if __name__ == "__main__":
    demo.launch()