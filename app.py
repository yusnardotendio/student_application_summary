import gradio as gr
import os
import fitz  # pymupdf alias
import pymupdf
import openai
from PIL import Image
import pytesseract
import io
from google import genai
from google.api_core import exceptions
from config import ACTIVE_PROVIDER, API_KEYS, MODEL_TO_USE
from providers.openai_provider import OpenAIProvider
from providers.google_provider import GoogleProvider
from fpdf import FPDF
import tempfile
from helpers import *

# Load your CSS file
with open("style.css") as f:
    css = f.read()


def get_provider(name: str):
    if name == "openai":
        return OpenAIProvider(API_KEYS["openai_api_key"])
    elif name == "gemini":
        return GoogleProvider(API_KEYS["gemini_api_key"])
    else:
        raise ValueError(f"Unsupported provider: {name}")


provider = get_provider(ACTIVE_PROVIDER)

def extract_text_from_pdf(file_path):
    image_parsing_prompt = get_prompt_text("prompt_text/transcript_image_parsing.txt")
    doc = pymupdf.open(file_path)
    image_list = []
    full_text = ""
    for page in doc:
        image_list += page.get_images(full=True)

    if len(image_list) <= 0:
        for page in doc:
            full_text += page.get_text()
    else:
        try:
            client = genai.Client(api_key=API_KEYS["image_parsing_api_key"])
            my_file = client.files.upload(file=file_path)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[my_file, image_parsing_prompt],
            )
            full_text += response.text
        except (exceptions.ClientError):
            return "Unable to parse the image because the given API KEY is not active"
    return full_text


def extract_text_from_image(file_obj):
    img = Image.open(file_obj)
    text = pytesseract.image_to_string(img)
    return text


def generate_response(message: str, system_prompt: str, temperature: float = 0.5, max_tokens: int = 5000):
    response = provider.generate_text(
        model=MODEL_TO_USE,
        prompt=message,
        system_prompt=system_prompt
    )
    return response


def generate_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in text.split('\n'):
        pdf.multi_cell(0, 10, line)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_file.name)
    return temp_file.name


def analyze_documents(essay_content, transcript_content):
    instruction_prompt = """
You are an expert AI admissions evaluation assistant. Your task is to analyze an applicant's transcript and essay text according to a specific set of criteria and provide a structured evaluation.

Input Data:
You have been provided with:
1.  The full text extracted from the applicant's academic transcript. This text contains course names, grades, and ECTS credits. The applicant's GPA information is also included, which should clearly state:
    a. The scale of the grading system (e.g., 0-100, A-F where A is best, 1-5 where 1 is best).
    b. The numerical value representing the best possible achievable grade in their system (`P_max_foreign`).
    c. The numerical value representing the minimum passing grade in their system (`P_min_foreign`).
    d. If letter grades are used, a clear numerical mapping for the applicant's specific grade.
2.  The full text extracted from the applicant's essay.

Evaluation Criteria and Scoring Rules:
Part 1: ECTS Credits Evaluation
1.  Extract Total ECTS: From the transcript text, identify and sum all ECTS credits earned by the applicant.
2.  ECTS Requirement Check:
       If Total ECTS >= 110, proceed to Part 2.
       If Total ECTS < 110, the applicant is REJECTED. Do not proceed further with other scoring. Output the rejection reason.

Part 2: Curriculum Scoring (Total Possible: 50 points)
(Details of module groups, example courses, weights, and minimum ECTS as previously defined)
   A. Business Management Field (Minimal 25 ECTs, Weight: 20 points)
   B. Economics Field (Minimal 10 ECTs, Weight: 10 points)
   C. Empirical Research Methods (Minimal 5 ECTs, Weight: 10 points)
   D. Operations Research (Minimal 5 ECTs, Weight: 5 points)
   E. Computer Science Field (Minimal 5 ECTs, Weight: 5 points)
   Total Curriculum Score: Sum of points awarded.

Part 3: GPA Conversion and Scoring (Total Possible: 10 points)
1.  Determine Applicant's Numerical Grade (`P_d_foreign`). It's the grade achieved by applicant.
2.  Identify System Parameters (`P_max_foreign`, `P_min_foreign`).
    Maximum possible grade in the original system: P_max_foreign
    Minimum passing grade in the original system: P_min_foreign
3.  Check for Direct German Scale. Whether the grade is already in the German scale (1.0 – 4.0).
4.  Convert to German Grade (`N`) using Modified Bavarian Formula (if not direct German scale):
    N = 1 + 3 * ((P_max_foreign - P_d_foreign) / (P_max_foreign - P_min_foreign))
    Round N to one decimal point.
5.  GPA Scoring based on `N`:
       1.0 - 1.5: 10 points
       1.6 - 2.0: 6 points
       2.1 - 2.5: 3 points
       2.6 or below (N >= 2.6): 0 points
6. Letter Grade Systems:
    If the input grading system uses letters (A+, A, B, C, D, E), convert them to numeric values:
    A+ = 1
    A = 2
    B = 3
    C = 4
    D = 5
    E = 6

Part 4: Essay Scoring (Total Possible: 40 points)
(Details of areas, evaluation criteria, and weights as previously defined)
   A. Logic and Reasoning (Weight: 20 points)
   B. Structural Coherence (Weight: 10 points)
   C. Language Complexity (Weight: 10 points)
   Total Essay Score: Sum of points awarded.

Part 5: Final Decision
1.  Calculate Overall Total Score: Total Curriculum Score + GPA Score + Total Essay Score.
2.  Admission Check:
       If Overall Total Score >= 70 AND Total ECTS >= 110, the applicant is ACCEPTED.
       Otherwise, the applicant is REJECTED.

Output Instructions:

1. Readable Summary Output:
After the JSON output, provide a concise, human-readable summary of the evaluation. Use clear language and bullet points for scores.

Example of Readable Summary Format:

--- APPLICANT EVALUATION SUMMARY ---

ECTS Credits:
   Total ECTS Identified: [Number]
   ECTS Requirement (>= 110): [Met/Not Met]
   Status: [Proceed/Rejected due to ECTS]

(If not rejected due to ECTS, continue with the following):

Curriculum Score:
   Total Curriculum Points: [Number] / 50

GPA Score:
   Applicant's Original GPA: [String, e.g., "3.5" or "B"]
   Calculated German Grade (N): [Number, e.g., 1.8]
   GPA Points: [Number] / 10

Essay Score:
   Logic and Reasoning: [Number] / 20
   Structural Coherence: [Number] / 10
   Language Complexity: [Number] / 10
   Total Essay Points: [Number] / 40

Overall Performance:
   Overall Total Score: [Number] / 100 (Target: >= 70)

Final Admission Decision:
   Decision: [ACCEPTED/REJECTED]
   Reasoning: [Brief summary justification, e.g., "Applicant meets ECTS and total score requirements." or "Applicant did not meet the minimum ECTS requirement." or "Applicant's total score is below the 70-point threshold."]
"""

    final_prompt = f"""
APPLICANT'S ESSAY:
---
{essay_content}
---

APPLICANT'S TRANSCRIPT:
---
{transcript_content}
---

Based on the essay and transcript provided above, please follow these instructions to evaluate the documents:
{instruction_prompt}
"""
    return generate_response(final_prompt, system_prompt="You are an expert Admissions Committee Member for a competitive Master's program that gives score exactly based on provided documents")


def evaluate_and_return_pdf_and_text(essay, transcript):
    result = analyze_documents(essay, transcript)
    pdf_path = generate_pdf(result)
    return result, pdf_path


# Gradio interface
with gr.Blocks(css=css, theme=gr.themes.Soft(), title="TUM Application Evaluation") as demo:
    gr.Markdown("## 📄 Upload PDFs / Images", elem_classes="section-title")

    with gr.Row(equal_height=True):
        with gr.Column(elem_classes=["upload-column"]):
            essay_file = gr.File(label="Upload Essay (PDF or Image)")
            essay_content = gr.Textbox(label="Parsed Essay Content", lines=10)
        with gr.Column(elem_classes=["upload-column"]):
            transcript_file = gr.File(label="Upload Transcript (PDF or Image)")
            transcript_content = gr.Textbox(label="Parsed Transcript Content", lines=10)

    with gr.Row():
        summarize_button = gr.Button("Summarize & Evaluate", elem_classes=["summarize-button"])

    with gr.Row():
        output = gr.Markdown()

    # Hidden file output for PDF download
    download_pdf = gr.File(label="Download Evaluation PDF", interactive=False, visible=False)

    # Functions for file parsing based on extension
    def process_file(file):
        extracted_text = ""
        if file is not None:
            file_type = os.path.splitext(file.name)[-1].lower()
            if file_type == '.pdf':
                return extract_text_from_pdf(file.name)
            elif file_type in ['.png', '.jpg', '.jpeg']:
                with open(file.name, "rb") as f:
                    return extract_text_from_image(f)
        return ""

    def process_essay_and_count(file):
        extracted_text = process_file(file)
        word_count = len(extracted_text.split())
        new_label = f"Parsed Essay Content (Word Count: {word_count})"
        return gr.update(value=extracted_text, label=new_label)


    essay_file.upload(fn=process_essay_and_count, inputs=essay_file, outputs=essay_content)
    transcript_file.upload(fn=process_file, inputs=transcript_file, outputs=transcript_content)

    def on_summarize(essay_text, transcript_text):
        if not essay_text.strip() or not transcript_text.strip():
            return "Please upload and parse both Essay and Transcript before summarizing.", gr.update(visible=False)
        summary_text, pdf_path = evaluate_and_return_pdf_and_text(essay_text, transcript_text)
        return summary_text, gr.update(value=pdf_path, visible=True, interactive=True)

    summarize_button.click(
        fn=on_summarize,
        inputs=[essay_content, transcript_content],
        outputs=[output, download_pdf]
        )


if __name__ == "__main__":
    demo.launch()