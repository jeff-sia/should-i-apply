import streamlit as st
from google import genai
from openai import OpenAI
from groq import Groq
import PyPDF2
from docx import Document
import io

# --- 1. CONFIG & UI ---
st.set_page_config(page_title="JobScore Pro: All-Access", layout="wide")

def extract_text(uploaded_file):
    """Parses PDF or DOCX and returns text."""
    try:
        if uploaded_file.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
            return "".join([page.extract_text() for page in pdf_reader.pages])
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(io.BytesIO(uploaded_file.read()))
            return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        st.error(f"Error reading file: {e}")
    return ""

# --- 2. SESSION STATE ---
if "consent" not in st.session_state: st.session_state.consent = False
if "jd_text" not in st.session_state: st.session_state.jd_text = ""
if "resume_text" not in st.session_state: st.session_state.resume_text = ""

# --- 3. CALLBACKS ---
def update_jd():
    if st.session_state.jd_upload: st.session_state.jd_text = extract_text(st.session_state.jd_upload)
def update_resume():
    if st.session_state.resume_upload: st.session_state.resume_text = extract_text(st.session_state.resume_upload)

# --- 4. CONSENT GATE (FIXED SIDE-BY-SIDE) ---
if not st.session_state.consent:
    st.title("🛡️ Secure Analysis Gateway")
    st.info("Consent Required: Your data is processed in real-time and never stored for training.")
    
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("1 - Yes, I consent", use_container_width=True):
            st.session_state.consent = True
            st.rerun()
    with col_no:
        if st.button("2 - No, I do not consent", use_container_width=True):
            st.error("Understood. I will not process any personal information.")
            st.stop()
    st.stop()

# --- 5. SIDEBAR (API COMMAND CENTER) ---
with st.sidebar:
    st.header("🔑 API Key Tank")
    g_key = st.text_input("Gemini API Key", type="password")
    oa_key = st.text_input("OpenAI API Key", type="password")
