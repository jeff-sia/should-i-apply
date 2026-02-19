import streamlit as st
import google.generativeai as genai
import PyPDF2
from docx import Document
import io

# --- 1. CONFIG & CSS ---
st.set_page_config(page_title="JobScore Pro", layout="wide")

# --- 2. SESSION STATE ---
if "consent" not in st.session_state: st.session_state.consent = False
if "jd_text" not in st.session_state: st.session_state.jd_text = ""
if "resume_text" not in st.session_state: st.session_state.resume_text = ""

# --- 3. PARSING LOGIC ---
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
    st.info("Consent Required: Your information will not be stored, reused, shared, or used for training.")
    col_y, col_n = st.columns(2)
    with col_y:
        if st.button("1 - Yes, I consent"):
            st.session_state.consent = True
            st.rerun()
    with col_n:
        if st.button("2 - No, I do not consent"):
            st.error("Understood. I will not process any personal information. Let me know if you change your mind.")
            st.stop()
    st.stop()

# --- 5. MAIN UI ---
st.title("🚀 JobScore & Resume Optimizer")
with st.sidebar:
    api_key = st.text_input("Enter Gemini API Key", type="password")
    if api_key: genai.configure(api_key=api_key)

if not api_key:
    st.warning("Please enter your API Key in the sidebar to begin.")
    st.stop()

col1, col2 = st.columns(2, gap="large")
with col1:
    st.subheader("📋 Job Description")
    st.file_uploader("Upload JD", type=["pdf", "docx"], key="jd_upload", on_change=update_jd)
    st.session_state.jd_text = st.text_area("Paste JD:", value=st.session_state.jd_text, height=300)
with col2:
    st.subheader("📄 Resume")
    st.file_uploader("Upload Resume", type=["pdf", "docx"], key="resume_upload", on_change=update_resume)
    st.session_state.resume_text = st.text_area("Paste Resume:", value=st.session_state.resume_text, height=300)

# --- 6. SCORING ENGINE ---
if st.button("🚀 Run Brutally Honest Analysis", type="primary", use_container_width=True):
    if st.session_state.jd_text and st.session_state.resume_text:
        with st.spinner("Analyzing..."):
            model = genai.GenerativeModel('gemini-3-flash')
            
            # This prompt hardcodes your specific logic and rules
            prompt = f"""
            You are a brutally honest jobseeker assistant. Evaluate the RESUME against the JD.
            
            STRICT RULES:
            1. Root analysis in EVIDENCE. No assumptions or fabrications. [cite: 38, 48]
            2. SCORING:
               - Hard Skills (H): 50% weight
               - Industry Experience (I): 30% weight
               - Valued Extras (V): 20% weight
               - Use 0-5 scale per item.
            3. FORMULA: (H/5 * 50) + (I/5 * 30) + (V/5 * 20). Cap at 100%.
            4. TONE: Brutally honest. If score < 60%, trigger the 'Not Recommended' block. [cite: 27]
            
            JD: {st.session_state.jd_text}
            RESUME: {st.session_state.resume_text}
            
            OUTPUT FORMAT:
            ### Your Self-Match Report
            **Position**: {{Role}}
            **Company**: {{Org}}
            **Final Match Score**: **{{X}}%**
            **Tier**: {{Excellent | Strong | Moderate | Low}}
            ---
            ### 🔹 1️⃣ Hard Skills Fit (50%)
            ### 🔹 2️⃣ Industry Experience Fit (30%)
            ### 🔹 3️⃣ Valued Extras Fit (20%)
            ---
            ### 📌 Summary
            ### 🟢 Action Plan (if score >= 60%)
            ### ❌ Not Recommended (if score < 60%)
            """
            
            response = model.generate_content(prompt)
            st.markdown(response.text)
    else:
        st.error("Missing input data.")
