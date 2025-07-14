import os
import gradio as gr
from datetime import datetime
from config import ACTIVE_PROVIDER
from fpdf import FPDF
from helpers import *
from markdown_pdf import *
import fitz

# Load your CSS file
with open("style.css") as f:
    css = f.read()

provider = get_provider(ACTIVE_PROVIDER)

def extract_raw_text_from_file(file_path):
    """
    Extracts text from an essay.
    """
    raw_text = ""
    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                raw_text += page.get_text()
        
    except Exception as e:
        print(f"Error during raw text extraction: {e}")
    return raw_text

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

def extract_applicant_name(transcript_content):
    """
    Extracts the applicant's name to create a sanitized filename.
    """
    prompt = get_prompt_text("prompt_text/extract_applicant_name.txt")
    try:
        # Use the existing generate_response helper
        name_response = generate_response(
            message=transcript_content,
            system_prompt=prompt
        )
        # Clean the response to get just the name
        name = name_response.strip().split('\n')[0]
        # Sanitize for use in a filename
        sanitized_name = re.sub(r'[^\w\s-]', '', name).strip()
        sanitized_name = re.sub(r'[-\s]+', '_', sanitized_name)
        return sanitized_name if sanitized_name else "Unknown_Applicant"
    except Exception as e:
        print(f"Could not extract applicant name: {e}")
        return "Unknown_Applicant"

def generate_pdf(text, output_filename="evaluation.pdf"):
    """
    Generates a PDF from markdown text and saves it to a specific path.
    """
    output_dir = "evaluations"
    os.makedirs(output_dir, exist_ok=True)
    full_path = os.path.join(output_dir, output_filename)

    try:
        pdf = MarkdownPDF()
        pdf.render_markdown(text)
        pdf.output(full_path)
    except Exception:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        # FPDF requires latin-1, so we encode and replace unknown characters
        encoded_text = text.encode('latin-1', 'replace').decode('latin-1')
        for line in encoded_text.split('\n'):
            pdf.multi_cell(0, 10, line)
        pdf.output(full_path)
    return full_path


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


# Gradio interface
with gr.Blocks(css=css, theme=gr.themes.Soft(), title="TUM Application Evaluation") as student_application_evaluator:

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
        progress_bar = gr.Slider(
            0, 
            100, 
            interactive=False,
            label="Please wait for the model to process the provided documents .....",
            show_label=True,
            visible=False
        )

    with gr.Row():
        output = gr.Markdown(
            show_copy_button=True
        )

    with gr.Row():
        download_pdf = gr.File(label="Download Evaluation PDF", interactive=False, visible=False)

    with gr.Row():
        caution_markdown = gr.Markdown("""
            **Caution**: This system uses a Large Language Model (LLM), which may occasionally produce inaccurate or misleading outputs (hallucinations).  
            **Human judgment is still essential** in all final admission decisions.
        """, visible=False)

    

    # Functions for file parsing based on extension
    def process_file(file, file_label):
        extracted_text = ""
        if file is not None:
            return extract_text_with_model(file.name, file_label) 
        return ""

   
    def process_essay_and_count(file, file_label):
        if file is None:
            return gr.update(value="", label="Parsed Essay Content")
        raw_text = extract_raw_text_from_file(file.name)
        word_count = len(raw_text.split())
        new_label = f"Parsed Essay Content (Word Count: {word_count})"
        parsed_text = extract_text_with_model(file.name, "essay")
        return gr.update(value=parsed_text, label=new_label)
    

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
            yield 0, "Please upload and parse both Essay and Transcript before summarizing.", gr.update(visible=False), gr.update(visible=False)
            return
        yield gr.update(visible=True), "", gr.update(visible=False), gr.update(visible=False)
        yield (0) * 100 // 4, "", gr.update(visible=False), gr.update(visible=False)
        yield (1) * 100 // 4, "", gr.update(visible=False), gr.update(visible=False)
        summary_text = analyze_documents(essay_text, transcript_text, vpd_text)
        yield (2) * 100 // 4, "", gr.update(visible=False), gr.update(visible=False)
        applicant_name = extract_applicant_name(transcript_text)
        yield (3) * 100 // 4, "", gr.update(visible=False), gr.update(visible=False)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        filename = f"{applicant_name}_Evaluation_{timestamp}.pdf"
        pdf_path = generate_pdf(summary_text, filename)
        
        download_label = f"Download Evaluation"
        #yield (4) * 100 // 4, summary_text, gr.update(value=pdf_path, visible=True, interactive=True, label=download_label), gr.update(visible=True)
        yield gr.update(visible=False), summary_text, gr.update(value=pdf_path, visible=True, interactive=True, label=download_label), gr.update(visible=True)


    summarize_button.click(
        fn=on_summarize,
        inputs=[essay_content, transcript_content, vpd_content],
        outputs=[progress_bar, output, download_pdf, caution_markdown],
        show_progress=True,
        show_progress_on=output
    )


if __name__ == "__main__":
    student_application_evaluator.launch()