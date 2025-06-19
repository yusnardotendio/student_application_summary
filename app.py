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
You are an expert Admissions Committee Member for a competitive Master's program. Your task is to give a score based *exactly* on the provided documents and evaluation criteria. Do not make assumptions or guess information that is not present.

**EVALUATION CRITERIA & SCORING**

**Part 1: ECTS Requirements (Hard Cutoff)**
- Minimum total ECTS required: **140**.
- If the total ECTS credits identified from the transcript are less than 140, the applicant is **REJECTED**. Do not proceed with further scoring and state this as the reason.

**Part 2: Curriculum Scoring (Max 50 points)**
- Group subjects from the transcript into the module groups below. Only assign a subject if it clearly belongs.
- If a module group's total ECTS meets the minimum, award the full points for that group. Otherwise, award 0.

| Module Group                | Minimum ECTS | Score  |
|-----------------------------|--------------|--------|
| Business Management Field   | 25 ECTS      | 20     |
| Economics Field             | 10 ECTS      | 10     |
| Empirical Research Methods  | 5 ECTS       | 10     |
| Operations Research         | 5 ECTS       | 5      |
| Computer Science Field      | 5 ECTS       | 5      |

**Part 3: GPA Scoring (Max 10 points)**
*This is a multi-step process. Follow it carefully.*

**Step 3.A: Identify Grading System from Transcript**
- Carefully search the transcript text to find the applicant's grading system. You need three specific values:
    - `P_d_foreign`: The applicant's final cumulative grade/GPA.
    - `P_max_foreign`: The best possible grade in that system (e.g., 4.0, 100).
    - `P_min_foreign`: The minimum passing grade in that system (e.g., 2.0, 50).
- **If the transcript already uses the German 1.0-5.0 scale (where 1.0 is best)**, you can use the applicant's GPA directly as the final German grade `N`. Note this in your summary.
- **If you cannot find clear information for all three values in the transcript, you cannot calculate the GPA score. Award 0 points and explicitly state that the necessary GPA information was missing.**

**Step 3.B: Convert to German Grade (if not already German)**
- If the grade is not on the German scale, use the **Modified Bavarian Formula**: `N = 1 + 3 * ((P_max_foreign - P_d_foreign) / (P_max_foreign - P_min_foreign))`
- Calculate `N` and round to one decimal place.

**Step 3.C: Award Points based on the calculated German Grade `N`**
- 1.0 to 1.5: **10 points**
- 1.6 to 2.0: **6 points**
- 2.1 to 2.5: **3 points**
- 2.6 or higher: **0 points**

**Part 4: Essay Scoring (Max 40 points)**
- Evaluate the essay on three criteria:
    - **Logic and Reasoning:** Clarity, depth, and consistency of arguments. (Max 20 points)
    - **Structural Coherence:** Organization and flow of ideas. (Max 10 points)
    - **Language Complexity:** Vocabulary, sentence variety, and sophistication. (Max 10 points)

**FINAL DECISION**
- Calculate **Total Score** = (Curriculum Score + GPA Score + Essay Score).
- An applicant is **ACCEPTED** only if: **Total ECTS >= 140** AND **Total Score >= 70**.
- Otherwise, the applicant is **REJECTED**.

---
**OUTPUT STRUCTURE**

Provide your response in the following structured Markdown format.

**1. FINAL DECISION**
- **Decision:** [ACCEPTED / REJECTED]
- **Total Score:** [Number] / 100
- **Total ECTS:** [Number]

**2. OVERALL ASSESSMENT**
- **Strengths:** [List 2-3 key strengths from the essay and transcript.]
- **Weaknesses:** [List 2-3 key weaknesses. For transcript weaknesses, specify the module groups that did not meet the ECTS criteria.]

**3. SUGGESTIONS FOR IMPROVEMENT**
- [Provide this section ONLY if the final decision is REJECTED. Give specific, actionable advice.]

**4. DETAILED EVALUATION BREAKDOWN**

**A. ECTS Evaluation**
- **Summary:** [Briefly state if the requirement was met.]
- **Total ECTS Identified:** [Number]
- **Requirement Met (>= 140 ECTS):** [Yes/No]

**B. Curriculum Scoring**
- **Summary:** [Briefly summarize performance in curriculum.]
- **Total Curriculum Score:** [Number] / 50
- **Score Breakdown:**
    - **Business Management Field (Score: [0 or 20]):**
        - Matched Courses: [List course name (ECTS, Grade), ...]
    - **Economics Field (Score: [0 or 10]):**
        - Matched Courses: [List course name (ECTS, Grade), ...]
    - **Empirical Research Methods (Score: [0 or 10]):**
        - Matched Courses: [List course name (ECTS, Grade), ...]
    - **Operations Research (Score: [0 or 5]):**
        - Matched Courses: [List course name (ECTS, Grade), ...]
    - **Computer Science Field (Score: [0 or 5]):**
        - Matched Courses: [List course name (ECTS, Grade), ...]

**C. GPA Scoring**
- **Summary:** [Briefly explain the calculation and result.]
- **GPA Score:** [0, 3, 6, or 10] / 10
- **Calculation Details:**
    - Original System Found: [e.g., "US 4.0 Scale" or "Not Found"]
    - Applicant's Grade (`P_d_foreign`): [Value]
    - System Best (`P_max_foreign`): [Value]
    - System Min Pass (`P_min_foreign`): [Value]
    - Calculated German Grade (N): [Value, or "N/A if already German"]

**D. Essay Scoring**
- **Summary:** [Briefly summarize the essay's quality.]
- **Total Essay Score:** [Number] / 40
- **Score Breakdown:**
    - Logic and Reasoning: [Score] / 20
    - Structural Coherence: [Score] / 10
    - Language Complexity: [Score] / 10
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