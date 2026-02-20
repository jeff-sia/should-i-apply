import streamlit as st
from google import genai # Updated to match your discovery
import PyPDF2
from docx import Document
import io

# --- 1. CONFIG & UI ---
st.set_page_config(page_title="JobScore Pro", layout="wide")

def extract_text(uploaded_file):
    if uploaded_file.type == "application/pdf":
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
        return "".join([page.extract_text() for page in pdf_reader.pages])
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = Document(io.BytesIO(uploaded_file.read()))
        return "\n".join([para.text for para in doc.paragraphs])
    return ""

# --- 2. SESSION STATE ---
if "consent" not in st.session_state: st.session_state.consent = False
if "jd_text" not in st.session_state: st.session_state.jd_text = ""
if "resume_text" not in st.session_state: st.session_state.resume_text = ""

# --- 3. AUTO-POPULATE CALLBACKS ---
def update_jd():
    if st.session_state.jd_upload: st.session_state.jd_text = extract_text(st.session_state.jd_upload)
def update_resume():
    if st.session_state.resume_upload: st.session_state.resume_text = extract_text(st.session_state.resume_upload)

# --- 4. GLOBAL CONSENT GATE (MANDATORY) ---
if not st.session_state.consent:
    st.title("🛡️ Secure Analysis Gateway")
    st.info("Consent Required: You may be asked to share your resume. This information will be used only to process your request within this conversation. It will not be stored, reused, shared, or used for training. [cite: 8-12]")
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
    st.header("⚙️ API Configuration")
    api_key = st.text_input("Enter Gemini API Key", type="password")

if not api_key:
    st.warning("Please enter your API Key in the sidebar to proceed.")
    st.stop()

# Initialize Client using the new SDK from your screenshot
client = genai.Client(api_key=api_key)

col_a, col_b = st.columns(2, gap="large")
with col_a:
    st.subheader("📋 1. Job Description")
    st.file_uploader("Upload JD", type=["pdf", "docx"], key="jd_upload", on_change=update_jd)
    st.session_state.jd_text = st.text_area("Paste or Verify JD:", value=st.session_state.jd_text, height=350)
with col_b:
    st.subheader("📄 2. Your Resume")
    st.file_uploader("Upload Resume", type=["pdf", "docx"], key="resume_upload", on_change=update_resume)
    st.session_state.resume_text = st.text_area("Paste or Verify Resume:", value=st.session_state.resume_text, height=350)

# --- 6. SCORING BACKEND & RUBRIC ---
if st.button("🚀 Run Brutally Honest Analysis", type="primary", use_container_width=True):
    if st.session_state.jd_text and st.session_state.resume_text:
        with st.spinner("Executing Scoring Logic..."):
            try:
                # Prompt includes all original backend conditions
                prompt = f"""
                You are a brutally honest jobseeker assistant. Evaluate the RESUME against the JD.
                
                SCORING SYSTEM & RUBRIC:
                1. Step 1: Extract criteria (Hard Skills (H), Industry Experience (I), Valued Extras (V)).
                2. Step 2: Map Evidence. No cited evidence = 0 points. Do not infer or fabricate. [cite: 48-49]
                3. Step 3: Score each on a 0-5 scale.
                
                WEIGHTS: Hard Skills = 50%, Industry Experience = 30%, Valued Extras = 20%.
                FORMULA: (H/5 * 50) + (I/5 * 30) + (V/5 * 20). Cap at 100%.
                
                STRICT GUIDELINES:
                - Tone: Blunt, direct, and neutral. No false encouragement [cite: 53-54].
                - Failsafe: If score < 60%, output '❌ Not Recommended' block.
                - Output MUST follow 'Self-Match Report' format.
                
                JD: {st.session_state.jd_text}
                RESUME: {st.session_state.resume_text}
                """
                
                # Use the exact method from your screenshot
                response = client.models.generate_content(
                    model="gemini-3-flash-preview", 
                    contents=prompt
                )
                st.markdown("---")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"Analysis failed. Error details: {e}")
    else:
        st.error("Missing input data: Both a JD and a Resume are required.")
