import streamlit as st
import PyPDF2
import io
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="AI Resume Critiquer", page_icon="📄", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

* { font-family: 'DM Sans', sans-serif; }

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 3rem; padding-bottom: 3rem; max-width: 720px; }
.stApp { background-color: #0d0d0d; }

.hero { margin-bottom: 2.5rem; }
.hero h1 {
    font-size: 2.4rem;
    font-weight: 600;
    color: #f5f5f5;
    letter-spacing: -0.02em;
    margin-bottom: 0.4rem;
}
.hero p { color: #888; font-size: 1rem; font-weight: 300; }

.tag {
    display: inline-block;
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    color: #aaa;
    font-size: 0.72rem;
    font-family: 'DM Mono', monospace;
    padding: 3px 10px;
    border-radius: 20px;
    margin-bottom: 1.2rem;
    letter-spacing: 0.05em;
}

.card-label {
    font-size: 0.78rem;
    font-weight: 500;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.6rem;
}

[data-testid="stFileUploader"] {
    background: #111 !important;
    border: 1.5px dashed #2a2a2a !important;
    border-radius: 12px !important;
    padding: 1.2rem !important;
    transition: border-color 0.2s;
}
[data-testid="stFileUploader"]:hover { border-color: #444 !important; }
[data-testid="stFileUploader"] label { display: none !important; }

.stTextInput input {
    background: #161616 !important;
    border: 1.5px solid #2a2a2a !important;
    border-radius: 10px !important;
    color: #f5f5f5 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 0.7rem 1rem !important;
    transition: border-color 0.2s;
}
.stTextInput input:focus { border-color: #555 !important; box-shadow: none !important; }
.stTextInput input::placeholder { color: #444 !important; }
.stTextInput label { display: none !important; }

.stButton button, [data-testid="stFormSubmitButton"] button {
    background: #f5f5f5 !important;
    color: #000000 !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.95rem !important;
    padding: 0.65rem 2rem !important;
    width: 100% !important;
    transition: opacity 0.2s !important;
}
.stButton button:hover, [data-testid="stFormSubmitButton"] button:hover { opacity: 0.85 !important; }
.stButton button p, [data-testid="stFormSubmitButton"] button p { color: #000000 !important; }

.results-header {
    font-size: 0.78rem;
    font-weight: 500;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 2rem 0 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.results-header::after { content: ''; flex: 1; height: 1px; background: #222; }

[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
    color: #ccc !important;
    line-height: 1.75 !important;
    font-size: 0.95rem !important;
}
[data-testid="stMarkdownContainer"] h3 {
    color: #f5f5f5 !important;
    font-size: 1rem !important;
    font-weight: 500 !important;
    margin-top: 1.4rem !important;
}

.stSpinner > div { border-top-color: #f5f5f5 !important; }
.stAlert { border-radius: 10px !important; }
hr { border-color: #1e1e1e !important; }
</style>

<div class="hero">
    <div class="tag">GPT-4o-mini powered</div>
    <h1>Resume Critiquer</h1>
    <p>Upload your resume and get structured AI feedback in seconds.</p>
</div>
""", unsafe_allow_html=True)

try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

with st.form(key="resume_form", clear_on_submit=False):
    st.markdown('<div class="card-label">Resume</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload your resume (PDF or TXT)", type={"pdf", "txt"}, label_visibility="collapsed")
    st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
    st.markdown('<div class="card-label">Target Role <span style="color:#444;font-size:0.72rem">(optional)</span></div>', unsafe_allow_html=True)
    job_role = st.text_input("Job role", placeholder="e.g. Software Engineer Intern, Data Analyst", label_visibility="collapsed")
    st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
    analyze = st.form_submit_button("Analyze Resume")

def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + '\n'
    return text

def extract_text_from_file(uploaded_file):
    if uploaded_file.type == "application/pdf":
        return extract_text_from_pdf(io.BytesIO(uploaded_file.read()))
    return uploaded_file.read().decode("utf-8")

if analyze and uploaded_file:
    try:
        file_content = extract_text_from_file(uploaded_file)
        if not file_content.strip():
            st.error("File does not have any content.")
            st.stop()

        prompt = f"""Please analyze this resume and provide constructive feedback.
Focus on the following aspects:
1. Content clarity and impact
2. Skills presentation
3. Experience descriptions
4. Specific improvements for {job_role if job_role else 'general job application'}
5. Add bullet rewrites
6. Scorecard /10 + summary line

Resume content:
{file_content}

Please provide your analysis in a clear, structured format with specific recommendations."""

        with st.spinner("Analyzing your resume..."):
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert resume reviewer with years of experience in HR and recruitment."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

        st.markdown('<div class="results-header">Analysis</div>', unsafe_allow_html=True)
        st.markdown(response.choices[0].message.content)

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

elif analyze and not uploaded_file:
    st.warning("Please upload a resume first.")