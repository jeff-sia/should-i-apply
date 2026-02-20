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

# --- 3. AUTO-POPULATE CALLBACKS ---
def update_jd():
    if st.session_state.jd_upload: st.session_state.jd_text = extract_text(st.session_state.jd_upload)
def update_resume():
    if st.session_state.resume_upload: st.session_state.resume_text = extract_text(st.session_state.resume_upload)

# --- 4. CONSENT GATE (FIXED SIDE-BY-SIDE) ---
if not st.session_state.consent:
    st.title("🛡️ Secure Analysis Gateway")
    st.info("Consent Required: Your information will be used only to process your request. It will not be stored, reused, shared, or used for training.")
    
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("1 - Yes, I consent", use_container_width=True):
            st.session_state.consent = True
            st.rerun()
    with col_no:
        if st.button("2 - No, I do not consent", use_container_width=True):
            st.error("Understood. I will not process any personal information. Please close this tab.")
            st.stop()
    st.stop()

# --- 5. MAIN APP INTERFACE ---
st.title("🚀 JobScore & Resume Optimizer")

with st.sidebar:
    st.header("⚙️ API Key Tank")
    g_key = st.text_input("Gemini API Key", type="password")
    oa_key = st.text_input("OpenAI API Key", type="password")
    or_key = st.text_input("OpenRouter Key", type="password")
    groq_key = st.text_input("Groq Key (Fastest)", type="password")
    di_key = st.text_input("DeepInfra Key (Cheapest)", type="password")
    
    st.markdown("---")
    # Identify which engines are ready to go
    available = []
    if g_key: available.append("Gemini")
    if oa_key: available.append("OpenAI")
    if or_key: available.append("OpenRouter")
    if groq_key: available.append("Groq")
    if di_key: available.append("DeepInfra")
    
    if available:
        mode = st.radio("Primary Engine", available)
    else:
        st.warning("No API keys detected in sidebar.")
        mode = None

# Input Fields
col_a, col_b = st.columns(2, gap="large")
with col_a:
    st.subheader("📋 1. Job Description")
    st.file_uploader("Upload JD", type=["pdf", "docx"], key="jd_upload", on_change=update_jd)
    st.session_state.jd_text = st.text_area("JD Content:", value=st.session_state.jd_text, height=350)
with col_b:
    st.subheader("📄 2. Your Resume")
    st.file_uploader("Upload Resume", type=["pdf", "docx"], key="resume_upload", on_change=update_resume)
    st.session_state.resume_text = st.text_area("Resume Content:", value=st.session_state.resume_text, height=350)

# --- 6. SCORING ENGINE ---
if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
    if not st.session_state.jd_text or not st.session_state.resume_text:
        st.error("Missing inputs: Please provide both documents.")
    elif not mode:
        st.error("Missing API Key: Provide at least one key in the sidebar.")
    else:
        prompt = f"""
        You are a brutally honest jobseeker assistant. Evaluate the RESUME against the JD.
        Weighting: Hard Skills (50%), Industry (30%), Valued Extras (20%).
        Formula: (H/5 * 50) + (I/5 * 30) + (V/5 * 20).
        Output format: 'Self-Match Report'.
        
        JD: {st.session_state.jd_text}
        RESUME: {st.session_state.resume_text}
        """
        
        success = False
        
        # Priority Failover Logic
        try:
            # TRY GROQ (If Selected or Failover)
            if (mode == "Groq" or not success) and groq_key:
                try:
                    with st.spinner("Analyzing via Groq..."):
                        client = Groq(api_key=groq_key)
                        resp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
                        st.markdown(resp.choices[0].message.content); success = True
                except: pass

            # TRY DEEPINFRA
            if (mode == "DeepInfra" or not success) and di_key:
                try:
                    with st.spinner("Analyzing via DeepInfra..."):
                        client = OpenAI(api_key=di_key, base_url="https://api.deepinfra.com/v1/openai")
                        resp = client.chat.completions.create(model="meta-llama/Llama-3.3-70B-Instruct", messages=[{"role": "user", "content": prompt}])
                        st.markdown(resp.choices[0].message.content); success = True
                except: pass

            # TRY GEMINI
            if (mode == "Gemini" or not success) and g_key:
                try:
                    with st.spinner("Analyzing via Gemini..."):
                        client = genai.Client(api_key=g_key)
                        resp = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
                        st.markdown(resp.text); success = True
                except: pass

        except Exception as e:
            st.error(f"System Failure: {e}")
        
        if not success:
            st.error("All engines failed or ran out of credits. Check your keys.")
