import gradio as gr
from datetime import datetime
import string
from config import ACTIVE_PROVIDER
from fpdf import FPDF
from helpers import *
from markdown_pdf import *

# Load your CSS file
with open("style.css") as f:
    css = f.read()

provider = get_provider(ACTIVE_PROVIDER)

def extract_text_with_model(file_path, file_label):
    full_text = ""

    if file_label == "essay":
        prompt = get_prompt_text("prompt_text/essay_parsing_prompt.txt") + get_prompt_text("prompt_text/essay_topics.txt")
    elif file_label == "transcript":
        prompt = get_prompt_text("prompt_text/transcript_parsing_prompt.txt")
    elif file_label == "vpd":
        prompt = get_prompt_text("prompt_text/vpd_parsing_prompt.txt")
    else:
        return
    
    file = provider.upload_file_to_model(file_path=file_path)
    response = generate_response(
        message=prompt,
        system_prompt="You are an assistant to extract text from files",
        contents=[file]
    )
    
    return response

def generate_pdf(text):
    full_name = ""
    try:
        match = re.search(r"[*\-]?\s*full name:\s*(.+)", text.lower())
        if match:
            full_name = match.group(1).strip()
            full_name = full_name.strip(string.punctuation + " ").capitalize()
    except:
        full_name = ""

    try:
        pdf = MarkdownPDF()
        pdf.render_markdown(text)

        filename = f"application_evaluation_{full_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
        pdf.output(filename)
    except:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
    
        for line in text.split('\n'):
            pdf.multi_cell(0, 10, line)

        filename = f"application_evaluation_{full_name}_{datetime.now().strftime('%Y%m%d')}.pdf"
        pdf.output(filename)
    return filename


def analyze_documents(essay_content, transcript_content, vpd_content=""):
    instruction_prompt = get_prompt_text("prompt_text/summary_evaluation_prompt.txt")

    final_prompt = f"""
{instruction_prompt}
--- BEGIN ESSAY ---
{essay_content}
--- END ESSAY ---

--- BEGIN TRANSCRIPT ---
{transcript_content}
--- END TRANSCRIPT ---
{
    "" if vpd_content == "" else
    "--- BEGIN vpd_german_grade --- " +
    vpd_content +
    "--- END vpd_german_grade ---"
}
"""
    return generate_response(
        final_prompt, 
        system_prompt="You are an expert Admissions Committee Member for a competitive Master's program that gives score exactly based on provided documents"
    )


def evaluate_and_return_pdf_and_text(essay, transcript, vpd=""):
    result = analyze_documents(essay, transcript, vpd)
    pdf_path = generate_pdf(result)
    return result, pdf_path


# Gradio interface
with gr.Blocks(css=css, theme=gr.themes.Soft(), title="TUM Application Evaluation") as student_application_evaluator:

    with gr.Row():
        gr.Markdown(
            """
            # TUM LLM-Powered Application Evaluation

            ### How to Use
            <details>
            <summary><em>Expand</em></summary>

            1. **Upload Required Documents**  
            Upload the applicant's **essay** , **transcript** , and other **required documents** .  
            _(Optional: The admission committee can also upload the VPD document.)_

            2. **Parse Documents**  
            The system will automatically extract relevant data from the uploaded files.

            3. **Click "Summarize & Evaluate"**  
            Once parsing is complete, click the **Summarize & Evaluate** button.  
            _Note: Evaluation may take some time as the model processes the information._

            4. **View Results**  
            A **comprehensive evaluation** will be displayed after processing.  
            A **downloadable PDF report** will also be available at the bottom — click the file size to download.
            </details>
            ---
            """
        )

    gr.Markdown("## Upload PDFs / Images", elem_classes="section-title")

    with gr.Row(equal_height=True):
        with gr.Column(elem_classes=["upload-column"]):
            essay_file = gr.File(
                label="Upload Essay (PDF or Image)", 
                file_types=['image', '.pdf']
            )
            essay_content = gr.Textbox(label="Parsed Essay Content", lines=10)
        with gr.Column(elem_classes=["upload-column"]):
            transcript_file = gr.File(
                label="Upload Transcript (PDF or Image)", 
                file_types=['image', '.pdf']
            )
            transcript_content = gr.Textbox(label="Parsed Transcript Content", lines=10)
        with gr.Column(elem_classes=["upload-column"]):
            vpd_file = gr.File(
                label="Upload VPD (PDF or Image), Optional", 
                file_types=['image', '.pdf']
            )
            vpd_content = gr.Textbox(label="Parsed VPD Content", lines=10)

    with gr.Row():
        summarize_button = gr.Button("Summarize & Evaluate", elem_classes=["summarize-button"])

    with gr.Row():
        output = gr.Markdown()

    with gr.Row():
        download_pdf = gr.File(label="Download Evaluation PDF", interactive=False, visible=False)

    with gr.Row():
        caution_markdown = gr.Markdown("""
            ⚠️ **Caution**: This system uses a Large Language Model (LLM), which may occasionally produce inaccurate or misleading outputs (hallucinations).  
            **Human judgment is still essential** in all final admission decisions.
        """, visible=False)

    

    # Functions for file parsing based on extension
    def process_file(file, file_label):
        extracted_text = ""
        if file is not None:
            return extract_text_with_model(file.name, file_label) 
        return ""

    def process_essay_and_count(file, file_label):
        extracted_text = process_file(file, file_label)
        try:
            word_count = len(extracted_text["content"].replace("\n", " ").split())
        except:
            word_count = len(extracted_text.split())
        new_label = f"Parsed Essay Content (Word Count: {word_count})"
        return gr.update(value=extracted_text, label=new_label)


    essay_file.upload(
        fn=process_essay_and_count, 
        inputs= [essay_file, gr.State("essay")], 
        outputs=essay_content
    )
    transcript_file.upload(
        fn=process_file, 
        inputs= [transcript_file, gr.State("transcript")], 
        outputs=transcript_content
    )
    vpd_file.upload(
        fn=process_file, 
        inputs= [vpd_file, gr.State("vpd")], 
        outputs=vpd_content
    )

    def on_summarize(essay_text, transcript_text, vpd_text=""):
        if not essay_text.strip() or not transcript_text.strip():
            return "Please upload and parse both Essay and Transcript before summarizing.", gr.update(visible=False)
        summary_text, pdf_path = evaluate_and_return_pdf_and_text(essay_text, transcript_text, vpd_text)
        return summary_text, gr.update(value=pdf_path, visible=True, interactive=True), gr.update(visible=True)

    summarize_button.click(
        fn=on_summarize,
        inputs=[essay_content, transcript_content, vpd_content],
        outputs=[output, download_pdf, caution_markdown],
        show_progress=True
    )


if __name__ == "__main__":
    student_application_evaluator.launch()