import streamlit as st
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
import openai
from config import (
    FORM_RECOGNIZER_ENDPOINT,
    FORM_RECOGNIZER_KEY,
    OPENAI_ENDPOINT,
    OPENAI_KEY,
    OPENAI_DEPLOYMENT_NAME
)

# Azure Form Recognizer setup
form_client = DocumentAnalysisClient(
    endpoint=FORM_RECOGNIZER_ENDPOINT,
    credential=AzureKeyCredential(FORM_RECOGNIZER_KEY)
)

# Azure OpenAI setup
openai.api_type = "azure"
openai.api_base = OPENAI_ENDPOINT
openai.api_version = "2023-07-01-preview"
openai.api_key = OPENAI_KEY

# Streamlit UI
st.set_page_config(page_title="Resume Analyzer")
st.title("📄 Resume Analyzer using Azure AI")

uploaded_file = st.file_uploader("Upload your resume (PDF only)", type=["pdf"])

if uploaded_file:
    st.success("Resume uploaded successfully!")

    # Save uploaded file
    with open("temp_resume.pdf", "wb") as f:
        f.write(uploaded_file.read())

    try:
        with open("temp_resume.pdf", "rb") as f:
            poller = form_client.begin_analyze_document(
                model_id="prebuilt-document",
                document=f
            )
            result = poller.result()

        resume_text = ""
        for page in result.pages:
            for line in page.lines:
                resume_text += line.content + "\n"

        st.subheader("📃 Extracted Resume Text")
        st.text_area("Resume Text", resume_text, height=200)

        # Send to Azure OpenAI for feedback
        st.info("Sending resume to GPT for analysis...")

        response = openai.ChatCompletion.create(
            engine=OPENAI_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "You are a resume reviewer."},
                {"role": "user", "content": f"""
Here is the text from a resume:

{resume_text}

Please:
1. Summarize the candidate.
2. Highlight 3 strengths.
3. Suggest 3 improvements.
4. Give a readiness score out of 10 for a software developer role.
"""}
            ]
        )

        ai_output = response['choices'][0]['message']['content']

        st.subheader("🧠 GPT Feedback")
        st.text_area("AI Feedback", ai_output, height=300)

    except Exception as e:
        st.error(f"❌ Error analyzing document: {e}")
