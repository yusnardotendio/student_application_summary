import gradio as gr
import os
import fitz
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
    print(image_parsing_prompt)
    doc = pymupdf.open(file_path)
    image_list = []
    full_text = ""
    for page in doc:
        image_list += page.get_images(full=True)

    if len(image_list) <= 0:
        for page in doc:
            # Extract text from page
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

def analyze_documents(essay_content, transcript_content):
    file_text = essay_content + "\n\n" + transcript_content
    prompt = f"""
You are an expert Admissions Committee Member for a competitive Master's program that gives score exactly based on provided documents and do not make assumption.

Applicant Documents: Essay, Transcript, respectively:
{file_text}

Using the following criteria, evaluate the applicant's documents with following evaluation criteria:

1. ECTS Requirements:
- Minimum total 140 ECTS required to pass.
- If below 140 ECTS, reject directly.

2. Curriculum Scoring (max 50 points):

| Module Group                | Minimum ECTS | Score  |
|-----------------------------|--------------|--------|
| Business Management Field   | 25 ECTS      | 20     |
| Economics Field             | 10 ECTS      | 10     |
| Empirical Research Methods  | 5 ECTS       | 10     |
| Operations Research         | 5 ECTS       | 5      |
| Computer Science Field      | 5 ECTS       | 5      |

Based on the transcript, group each subject into the appropriate module group using the subject name. 
Only assign a subject to a module if it clearly belongs. Do not guess or force a match.
For each module group, calculate the total ECTS achieved.
If the total ECTS for a group meets or exceeds the minimum required ECTS, assign the corresponding score to that group.
Otherwise, assign a score of 0 for that module group.

3. GPA Scoring (max 10 points):
calculate the student's overall GPA based on all relevant grades in the transcript. 
Then, assign a GPA score out of 10 based on the following criteria: 
if the GPA is between 1.0 and 1.5, assign 10 points; 
if it is between 1.6 and 2.0, assign 6 points; 
if it falls between 2.1 and 2.5, assign 3 points; and 
if the GPA is 2.6 or higher, assign 0 points.

If you cannot find it in the transcript, do not guess and force it. Just put score 0

4. Essay Scoring (max 40 points):
Evaluate the essay based on the following three criteria. 
First, assess logic and reasoning, awarding up to 20 points 
based on the clarity, depth, and consistency of the arguments presented. 
Second, evaluate the structural coherence of the essay, 
assigning up to 10 points for how well the ideas are organized and 
how effectively the essay transitions between sections. 
Finally, examine the language complexity, giving up to 10 points based on the richness of vocabulary, sentence variety, and overall language sophistication used in the essay.

The expected output should be in a structured format and seperated into some sections. 
The first section should be the pass or rejection (Applicant must have total score more than or equal to 70 and minimum 140 ECTS to pass.), the total score, and total credits in ECTS the student gets.
The second section should be strength and weakness of the student based on the transcript and essay. 
For the weakness of transcript, you should specify the module groups that don't satisfy with the evaluation criteriia.
Also remember that In the German grading system, GPA is calculated using a scale from 1.0 to 5.0, with 1.0 representing the highest grade and 5.0 representing a failing grade.
The next section should be suggestions for improvement if only the student gets rejected other.
The last section should be those four evaluation criteria. 
On each evaluation criteria, you should put detail summary, and the score student gets.
For the Curriculum Scoring, you should put detail breakdown of scores and module groups with the subjects that fall into the group
and specify each subject with the credit in ECTS and grade in German GPA.
"""
    return generate_response(prompt, system_prompt="You are an expert Admissions Committee Member for a competitive Master's program that gives score exactly based on provided documents and do not make assumption.")


# Gradio UI with CSS
with gr.Blocks(css=css, theme=gr.themes.Soft(), title="TUM Application Evaluation") as demo:
    gr.Markdown("## 📄 Upload PDFs", elem_classes="section-title")

    with gr.Row(equal_height=True):
        with gr.Column(elem_classes=["upload-column"]):
            essay_file = gr.File(label="Upload Essay")
            essay_content = gr.Textbox(label="Parsed Essay Content", lines=10)
        with gr.Column(elem_classes=["upload-column"]):
            transcript_file = gr.File(label="Upload Transcript")
            transcript_content = gr.Textbox(label="Parsed Transcript Content", lines=10)

    with gr.Row():
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

    essay_file.upload(process_file, essay_file, essay_content)
    transcript_file.upload(process_file, transcript_file, transcript_content)

    summarize_button.click(
        fn=analyze_documents,
        inputs=[essay_content, transcript_content],
        outputs=[output]
    )

if __name__ == "__main__":
    demo.launch()