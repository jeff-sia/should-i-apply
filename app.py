import streamlit as st
import google.generativeai as genai
import PyPDF2
from docx import Document
import io

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="JobScore Pro", layout="wide")

# --- 2. SESSION STATE MANAGEMENT ---
if "consent" not in st.session_state: st.session_state.consent = False
if "jd_text" not in st.session_state: st.session_state.jd_text = ""
if "resume_text" not in st.session_state: st.session_state.resume_text = ""

# --- 3. UNIVERSAL FILE PARSER ---
def extract_text(uploaded_file):
    if uploaded_file.type == "application/pdf":
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
        return "".join([page.extract_text() for page in pdf_reader.pages])
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(io.BytesIO(uploaded_file.read()))
        return "\n".join([para.text for para in doc.paragraphs])
    return ""

def update_jd():
    if st.session_state.jd_upload: st.session_state.jd_text = extract_text(st.session_state.jd_upload)
def update_resume():
    if st.session_state.resume_upload: st.session_state.resume_text = extract_text(st.session_state.resume_upload)

# --- 4. GLOBAL CONSENT GATE (MANDATORY) ---
if not st.session_state.consent:
    st.title("🛡️ Secure Analysis Gateway")
    st.info("Consent Required: Your information will not be stored, reused, shared, or used for training. [cite: 8-12]")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("1 - Yes, I consent"):
            st.session_state.consent = True
            st.rerun()
    with col2:
        if st.button("2 - No, I do not consent"):
            st.error("Understood. I will not process any personal information. Let me know if you change your mind. [cite: 28-29]")
            st.stop() 
    st.stop()

# --- 5. MAIN INTERFACE ---
st.title("🚀 JobScore & Resume Optimizer")

with st.sidebar:
    st.header("⚙️ API Setup")
    api_key = st.text_input("Enter Gemini API Key", type="password")
    if api_key: genai.configure(api_key=api_key)

if not api_key:
    st.warning("Please enter your API Key in the sidebar to proceed.")
    st.stop()

col_a, col_b = st.columns(2, gap="large")
with col_a:
    st.subheader("📋 1. Job Description")
    st.file_uploader("Upload JD", type=["pdf", "docx"], key="jd_upload", on_change=update_jd)
    st.session_state.jd_text = st.text_area("Paste JD:", value=st.session_state.jd_text, height=350)

with col_b:
    st.subheader("📄 2. Your Resume")
    st.file_uploader("Upload Resume", type=["pdf", "docx"], key="resume_upload", on_change=update_resume)
    st.session_state.resume_text = st.text_area("Paste Resume:", value=st.session_state.resume_text, height=350)

# --- 6. SCORING BACKEND & BRUTALLY HONEST LOGIC ---
if st.button("🚀 Run Brutally Honest Analysis", type="primary", use_container_width=True):
    if st.session_state.jd_text and st.session_state.resume_text:
        with st.spinner("Executing Scoring Logic..."):
            try:
                # 2026 STABLE PRODUCTION MODEL PATH
                model = genai.GenerativeModel('models/gemini-1.5-flash-8b') 
                
                prompt = f"""
                You are a brutally honest jobseeker assistant. Evaluate the RESUME against the JD.
                
                SCORING SYSTEM & RUBRIC:
                1. Hard Skills (H): 50%
                2. Industry Experience (I): 30%
                3. Valued Extras (V): 20%
                
                STRICT GUIDELINES:
                - Mapping: Use ONLY evidence from the resume. No assumptions. [cite: 37, 48-49]
                - Formula: (H/5 * 50) + (I/5 * 30) + (V/5 * 20). Cap at 100%.
                - Tone: Brutally honest, neutral, and blunt. [cite: 53-54]
                - Failsafe: If score < 60%, output the '❌ Not Recommended' block.
                - Output Format: Must follow 'Self-Match Report' structure.
                
                JD: {st.session_state.jd_text}
                RESUME: {st.session_state.resume_text}
                """
                response = model.generate_content(prompt)
                st.markdown("---")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Analysis failed. Error: {e}")
    else:
        st.error("Missing input data. Both JD and Resume are required.")
