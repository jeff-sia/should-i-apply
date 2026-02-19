import streamlit as st
import google.generativeai as genai
import PyPDF2
from docx import Document
import io

# --- 1. CONFIG & CSS ---
st.set_page_config(page_title="JobScore Pro", layout="wide")

# Custom CSS for a clean Dashboard look
st.markdown("""
    <style>
    .stTextArea textarea { border-radius: 10px; border: 1px solid #ddd; }
    .stButton>button { border-radius: 20px; font-weight: bold; height: 3em; }
    </style>
""", unsafe_allow_html=True)

def extract_text(uploaded_file):
    """Parses PDF or DOCX and returns text."""
    if uploaded_file.type == "application/pdf":
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
        return "".join([page.extract_text() for page in pdf_reader.pages])
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(io.BytesIO(uploaded_file.read()))
        return "\n".join([para.text for para in doc.paragraphs])
    return ""

# --- 2. SESSION STATE (The "Memory") ---
if "jd_text" not in st.session_state:
    st.session_state.jd_text = ""
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""

# --- 3. AUTO-POPULATE LOGIC ---
def update_jd():
    if st.session_state.jd_upload:
        st.session_state.jd_text = extract_text(st.session_state.jd_upload)

def update_resume():
    if st.session_state.resume_upload:
        st.session_state.resume_text = extract_text(st.session_state.resume_upload)

# --- 4. CONSENT GATE ---
if "consent" not in st.session_state:
    st.session_state.consent = False

if not st.session_state.consent:
    st.title("🛡️ Secure Analysis Gateway")
    st.info("Consent Required: Your information will not be stored, reused, shared, or used for training. [cite: 8-12]")
    
    col_y, col_n = st.columns(2)
    with col_y:
        if st.button("1 - Yes, I consent"):
            st.session_state.consent = True
            st.rerun()
    with col_n:
        if st.button("2 - No, I do not consent"):
            st.error("Understood. I will not process any personal information. Let me know if you change your mind. [cite: 28-29]")
            st.stop() # This stops the app execution immediately per guardrail 21
    st.stop()

# --- 5. MAIN APP UI ---
st.title("🚀 JobScore & Resume Optimizer")

with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Gemini API Key", type="password")
    if api_key:
        genai.configure(api_key=api_key)

if not api_key:
    st.warning("Please enter your Gemini API Key in the sidebar.")
    st.stop()

# Split-screen layout
col1, col2 = st.columns(2, gap="large")

with col1:
    st.subheader("📋 1. Job Description")
    # File Uploader with Callback
    st.file_uploader("Upload JD (PDF/Docx)", type=["pdf", "docx"], key="jd_upload", on_change=update_jd)
    # Linked Text Area
    st.session_state.jd_text = st.text_area("OR Paste JD text here:", value=st.session_state.jd_text, height=350)

with col2:
    st.subheader("📄 2. Your Resume")
    # File Uploader with Callback
    st.file_uploader("Upload Resume (PDF/Docx)", type=["pdf", "docx"], key="resume_upload", on_change=update_resume)
    # Linked Text Area
    st.session_state.resume_text = st.text_area("OR Paste Resume text here:", value=st.session_state.resume_text, height=350)

st.markdown("---")

# --- 6. BRUTALLY HONEST ANALYSIS ---
if st.button("🚀 Run Brutally Honest Analysis", type="primary", use_container_width=True):
    if st.session_state.jd_text and st.session_state.resume_text:
        with st.spinner("Analyzing match... this may take 10-15 seconds."):
            model = genai.GenerativeModel('gemini-1.5-flash')
            # The prompt includes your exact instructions from the knowledge base
            full_prompt = f"""
            You are a brutally honest jobseeker assistant. 
            Evaluate this Resume against the Job Description.
            JD: {st.session_state.jd_text}
            RESUME: {st.session_state.resume_text}
            
            Follow the SCORING SYSTEM: Hard Skills (50%), Industry Experience (30%), Valued Extras (20%).
            Weights: (H/5 * 50) + (I/5 * 30) + (V/5 * 20).
            """
            response = model.generate_content(full_prompt)
            st.markdown(response.text)
    else:
        st.error("Please provide both a Job Description and a Resume to proceed.")
