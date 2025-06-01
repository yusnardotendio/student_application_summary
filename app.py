import gradio as gr
import os
import fitz
import openai
from PIL import Image
import pytesseract
import io

# Load your CSS file
with open("style.css") as f:
    css = f.read()

openai.api_key = os.environ.get("GROQ_API_KEY")

def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    full_text = ""
    for page in doc:
        # Extract text from page
        full_text += page.get_text()
        
        # Extract images on page and OCR them
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

def analyze_documents( motivation_content, transcript_content):
    file_text = motivation_content + "\n\n" + transcript_content
    prompt = f"""
You are an expert Admissions Committee Member for a competitive Master's program.

Applicant Documents: Essay, Transcript:
{file_text}

Using the following criteria, evaluate the applicant:

---

**ECTS Requirements:**

- Minimum total 140 ECTS required to pass.
- If below 140 ECTS, reject directly.

**Curriculum Scoring (Total 50 points):**

| Module Group               | Minimum ECTS | Weight |
|----------------------------|--------------|--------|
| Business Management Field   | 25 ECTS      | 20     |
| Economics Field             | 10 ECTS      | 10     |
| Empirical Research Methods  | 5 ECTS       | 10     |
| Operations Research         | 5 ECTS       | 5      |
| Computer Science Field      | 5 ECTS       | 5      |

Calculate scores for each group based on ECTS achieved relative to minimum. For example, if applicant has 20 ECTS in Business Management (minimum 25), score is (20/25)*20 = 16 points.

**GPA Scoring (Total 10 points):**

- 1.0 - 1.5 : 10 points
- 1.6 - 2.0 : 6 points
- 2.1 - 2.5 : 3 points
- 2.6 or below : 0 points

Estimate GPA from transcript if available.

**Essay Scoring (Total 40 points):**

Evaluate Essay on:

- Logic and Reasoning (20 points)
- Structural Coherence (10 points)
- Language Complexity (10 points)

**Final evaluation:**

- Calculate total score (ECTS + Curriculum + GPA + Essay).
- Applicant must have total score >= 70 and minimum 140 ECTS to pass.
- Provide detailed breakdown of scores.
- Make clear pass or reject recommendation.
- Provide suggestions for improvement if rejected.

---

Answer in a structured format with scores and recommendations.
"""
    return generate_response(prompt, system_prompt="You are an expert Admissions Committee Member for TUM Campus.")

# Gradio UI with CSS
with gr.Blocks(css=css, theme=gr.themes.Soft()) as demo:
    with gr.Row():
        gr.Markdown("## Upload PDFs")
      
        with gr.Column():
            motivation_file = gr.File(label="Upload Motivation Letter")
            motivation_content = gr.Textbox(label="Parsed Motivation Letter Content", lines=10)
        with gr.Column():
            transcript_file = gr.File(label="Upload Transcript")
            transcript_content = gr.Textbox(label="Parsed Transcript Content", lines=10)
    with gr.Row():
        with gr.Column():
            #gr.Markdown("## Summarize")
            summarize_button = gr.Button("Summarize", elem_classes=["summarize-button"])

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

    
    motivation_file.upload(process_file, motivation_file, motivation_content)
    transcript_file.upload(process_file, transcript_file, transcript_content)

    summarize_button.click(
        fn=analyze_documents,
        inputs=[ motivation_content, transcript_content],
        outputs=[output]
    )

if __name__ == "__main__":
    demo.launch()
