# LLM-Assisted Student Application Evaluation

This project explores the integration of the Large Language Model (LLM) to support the evaluation of student applications. The main goal is to use LLM to help admissions staff read and summarize application documents, such as transcript and essay. The project involves prompting, integrating to LLM, and software engineering (for frontend and backend).

## Features

1. Extract relevant academic and extracurricular experiences from provided application
2. Identify alignment with program goals or specialization tracks
3. Flag missing or weak areas in the applicant's background
4. Overall recommendation summaries and confidence levels to assist the committee in final decisions

## Installation

1. Make sure to have python installed.
2. Clone the repo.
3. Install the required packages: pip install -r requirements.txt
4. Create .env file on the main directory. You can copy-paste the .env_example and put your own API KEY

## How to Start

Follow the **Installation** section and run the application: python app.py

## Dependencies

1. gradio
2. PyMuPDF
3. openai
4. matplotlib
5. fpdf
6. google-genai
7. dotenv
8. python-dotenv
