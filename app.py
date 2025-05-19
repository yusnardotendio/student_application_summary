import gradio as gr
import os
import fitz
import openai
from PIL import Image
import pytesseract
import io

openai.api_key = os.environ.get("GROQ_API_KEY")

def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    full_text = ""
    for page in doc:
        # Extract text from page
        full_text += page.get_text()
        
        # Extract images on page
        for img_info in page.get_images(full=True):
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image = Image.open(io.BytesIO(image_bytes))
            ocr_text = pytesseract.image_to_string(image)
            full_text += "\n" + ocr_text + "\n"
    return full_text

def extract_text_from_image(file_obj):
    img = Image.open(file_obj)
    text = pytesseract.image_to_string(img)
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
    return generate_response(prompt, "You are an expert Admissions Committee Member for TUM Campus.")

# Gradio UI
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    with gr.Row():
        gr.Markdown("## 1. Upload PDFs or Images")
        with gr.Column():
            resume_file = gr.File(label="Upload Resume (PDF or Image)")
            resume_content = gr.Textbox(label="Parsed Resume Content", lines=10)
        with gr.Column():
            motivation_letter_file = gr.File(label="Upload Motivation Letter (PDF or Image)")
            motivation_content = gr.Textbox(label="Parsed Motivation Letter Content", lines=10)
        with gr.Column():
            transcript_file = gr.File(label="Upload Transcript (PDF or Image)")
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
            elif file_type in ['png', 'jpg', 'jpeg']:
                return extract_text_from_image(file)
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
