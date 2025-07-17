import os
import gradio as gr
import time
from datetime import datetime
from config import ACTIVE_PROVIDER
from fpdf import FPDF
from helpers import *
from markdown_pdf import *
import fitz
from blue_theme import BlueTheme

# Load your CSS file
with open("style.css") as f:
    css = f.read()

provider = get_provider(ACTIVE_PROVIDER)

essay_sample = [["sample_document/sample_essay.pdf"]]
transcript_sample = [["sample_document/sample_transcript.pdf"]]
vpd_sample = [["sample_document/sample_vpd.pdf"]]

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
        if text is not None:
            encoded_text = text.encode('latin-1', 'replace').decode('latin-1')
        else:
            encoded_text = "" 
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
with gr.Blocks(
    css=css, 
    theme = BlueTheme(),
    title="TUM Admission Assistant"
) as student_application_evaluator:
    gr.Image(value="img/tum_logo.png", show_label=False, interactive=False, width=50, show_download_button=False, show_fullscreen_button=False)
    gr.Markdown("<h1 style='color: #4889CE;'>Admission Assistant</h1>", elem_classes="section-title")

    with gr.Tab("Admission Assistant App"):
        gr.Markdown("## Upload PDFs / Images", elem_classes="section-title")
        with gr.Row(equal_height=True):
            with gr.Column(elem_classes=["upload-column"]):
                essay_file = gr.File (
                    label="Upload Essay (PDF or Image)", 
                    file_types=['image', '.pdf'],
                    elem_id="essay-file-upload"
                )
                    
                essay_example = gr.File(visible=False)
                gr.Examples(
                    examples=essay_sample,
                    inputs=[essay_example]
                )      
            with gr.Column(elem_classes=["upload-column"]):
                transcript_file = gr.File(
                    label="Upload Transcript (PDF or Image)", 
                    file_types=['image', '.pdf'],
                    elem_id= "transcript-file-upload"
                )

                transcript_example = gr.File(visible=False)
                gr.Examples(
                    examples=transcript_sample,
                    inputs=[transcript_example],
                )                 
            with gr.Column(elem_classes=["upload-column"]):
                vpd_file = gr.File(
                    label="Upload VPD (PDF or Image), Optional", 
                    file_types=['image', '.pdf'],
                    elem_id= "vpd-file-upload",
                )
                
                vpd_example = gr.File(visible=False)
                gr.Examples(
                    examples=vpd_sample,
                    inputs=[vpd_example],
                )       
                
            gr.File(visible=False)

        with gr.Row(equal_height=True):
            with gr.Column(elem_classes=["upload-column"]):
                essay_content = gr.Textbox(label="Parsed Essay Content", lines=10)
            with gr.Column(elem_classes=["upload-column"]):
                transcript_content = gr.Textbox(label="Parsed Transcript Content", lines=10)
            with gr.Column(elem_classes=["upload-column"]):
                vpd_content = gr.Textbox(label="Parsed VPD Content", lines=10)
        with gr.Row():
            summarize_button = gr.Button("Summarize & Evaluate", elem_classes=["summarize-button"], elem_id="summarize-button")

        with gr.Row():
            progress_bar = gr.Slider(
                minimum=0, 
                maximum=100, 
                value=0, 
                label="Processing", 
                visible=False, 
                interactive=False,
            )

        with gr.Row():
            output = gr.Markdown(
                visible=False,
                max_height=600, 
                container=True
            )

        with gr.Row():
            applicant_result_data = gr.JSON(visible=False)

        with gr.Row():
            download_pdf = gr.File(
                label="Download Evaluation PDF", 
                interactive=False, 
                visible=False,
                elem_classes=["download-evaluation-container"]
            )

        with gr.Row():
            caution_markdown = gr.Markdown("""
                **Caution**: This system uses a Large Language Model (LLM), which may occasionally produce inaccurate or misleading outputs (hallucinations).  
                **Human judgment is still essential** in all final admission decisions.
            """, visible=False)

    with gr.Tab("Evaluation History") as tab_history:

        with gr.Row():
            result_table = gr.Dataframe(
                interactive=False,
                row_count=0,
                max_height=1000,
                elem_id="table",
                wrap=True,
                type="pandas",
                show_search='filter'
            )

        modal_box = gr.Group(visible=False)

        with modal_box:
            markdown_viewer = gr.Markdown(
                visible=False, 
                max_height=600, 
                container=True
            )
        with gr.Row():
            close_btn = gr.Button("Close", elem_classes=["close-btn"], visible=False)

        def on_select(evt: gr.SelectData, dataframe):
            row_idx, col_idx = evt.index
            try:
                selected_id = dataframe.iloc[row_idx]["ID"]
                result = get_result(str(selected_id.item()))
                if result:
                    markdown = result[4] 
                else:
                    markdown = "Result not found."
                return gr.update(value=markdown, visible=True), gr.update(visible=True), gr.update(visible=True)
            except Exception as e:
                print(e)
                return gr.update(value=f"Error: {e}", visible=True), gr.update(visible=True), gr.update(visible=False)

        result_table.select(on_select, inputs=[result_table], outputs=[markdown_viewer, modal_box, close_btn])
        close_btn.click(lambda: (gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)), outputs=[modal_box, markdown_viewer, close_btn])

    tab_history.select(fn=get_df, outputs=result_table)

    
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

    essay_example.change(
        fn=process_essay_and_count,
        inputs=[essay_example, gr.State("essay")],
        outputs=essay_content
    )

    transcript_example.change(
        fn=process_file,
        inputs=[transcript_example, gr.State("transcript")],
        outputs=transcript_content
    )

    def on_summarize(essay_text, transcript_text, vpd_text=""):
        # Step 1: Start - hide button, show progress bar
        yield (
            gr.update(visible=False),  # output_summary
            gr.update(visible=True, value=0),  # progress_bar
            gr.update(visible=False),  # hide summarize_button
            gr.update(visible=False), #download_pdf
            gr.update(visible=False)
        )

        # Step 2: Input validation

        data = {}
        if not essay_text.strip() or not transcript_text.strip():
            warning_txt = "## Please upload and parse both Essay and Transcript before summarizing."
            yield (
                gr.update(value=warning_txt, visible=True),
                gr.update(visible=False),
                gr.update(visible=True),
                gr.update(visible=False), #download_pdf
                gr.update(visible=False)
            )
            return

        # Step 3: LLM document analysis
        summary_text = analyze_documents(essay_text, transcript_text, vpd_text)
        yield (
            gr.update(visible=False),
            gr.update(value=60), 
            gr.update(visible=False), 
            gr.update(visible=False), #download_pdf
            gr.update(visible=False)
        )

        # Step 4: Extract name
        applicant_name = extract_applicant_name(transcript_text)
        yield (
            gr.update(visible=False),
            gr.update(value=75), 
            gr.update(visible=False), 
            gr.update(visible=False), #download_pdf
            gr.update(visible=False)
        )

        # Step 5: Generate PDF
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
        filename = f"{applicant_name}_Evaluation_{timestamp}.pdf"
        pdf_path = generate_pdf(summary_text, filename)

        yield (
            gr.update(visible=False),
            gr.update(value=90), 
            gr.update(visible=False), 
            gr.update(visible=False), #download_pdf
            gr.update(visible=False)
        )

        data['applicant_name'] = applicant_name
        data['created_at'] = timestamp
        data['decision'] = get_decision(summary_text[len(summary_text) * 3 // 5:])

        save_evaluation(data, summary_text)
        
        download_label = f"Download Evaluation"
        yield (
            gr.update(value=summary_text, visible=True),
            gr.update(visible=False), 
            gr.update(visible=False), 
            gr.update(value=pdf_path, visible=True, interactive=True, label=download_label), #download_pdf
            gr.update(visible=True)
        )

    summarize_button.click(
        fn=on_summarize,
        inputs=[essay_content, transcript_content, vpd_content],
        outputs=[output, progress_bar, summarize_button, download_pdf, caution_markdown],
        concurrency_limit=1,
        queue=True,
        show_progress=False
    )

if __name__ == "__main__":
    student_application_evaluator.launch(
        favicon_path="img/tum_logo.png",
        show_api=False,
        share_server_protocol='https'
    )