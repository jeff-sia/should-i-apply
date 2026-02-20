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
        st.error(f"Error parsing file: {e}")
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

# --- 4. CONSENT GATE ---
if not st.session_state.consent:
    st.title("🛡️ Secure Analysis Gateway")
    st.info("Consent Required: Your data is processed in real-time and never stored for training.")
    if st.button("1 - Yes, I consent"):
        st.session_state.consent = True
        st.rerun()
    st.stop()

# --- 5. SIDEBAR (THE API COMMAND CENTER) ---
with st.sidebar:
    st.header("🔑 API Key Tank")
    g_key = st.text_input("Gemini Key", type="password")
    oa_key = st.text_input("OpenAI Key", type="password")
    or_key = st.text_input("OpenRouter Key", type="password")
    groq_key = st.text_input("Groq Key (Fastest)", type="password")
    di_key = st.text_input("DeepInfra Key (Cheapest)", type="password")
    
    st.markdown("---")
    # Dynamically list only keys that are provided
    available_engines = []
    if g_key: available_engines.append("Gemini")
    if oa_key: available_engines.append("OpenAI")
    if groq_key: available_engines.append("Groq")
    if di_key: available_engines.append("DeepInfra")
    if or_key: available_engines.append("OpenRouter")
    
    if available_engines:
        mode = st.radio("Primary Engine", available_engines)
    else:
        st.warning("No keys detected. Add a key above.")
        mode = None

# --- 6. MAIN UI ---
st.title("🚀 JobScore & Resume Optimizer")

col_a, col_b = st.columns(2, gap="large")
with col_a:
    st.subheader("📋 1. Job Description")
    st.file_uploader("Upload JD", type=["pdf", "docx"], key="jd_upload", on_change=update_jd)
    st.session_state.jd_text = st.text_area("JD Content:", value=st.session_state.jd_text, height=300)
with col_b:
    st.subheader("📄 2. Your Resume")
    st.file_uploader("Upload Resume", type=["pdf", "docx"], key="resume_upload", on_change=update_resume)
    st.session_state.resume_text = st.text_area("Resume Content:", value=st.session_state.resume_text, height=300)

# --- 7. ANALYSIS LOGIC ---
if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
    if not st.session_state.jd_text or not st.session_state.resume_text:
        st.error("Missing input data.")
    elif not mode:
        st.error("Please provide at least one API key in the sidebar.")
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
        
        # Priority Failover Chain
        try:
            # OPTION 1: GROQ (Speed Priority)
            if mode == "Groq" or (not success and groq_key):
                try:
                    with st.spinner("Analyzing via Groq (Llama 3.3)..."):
                        client = Groq(api_key=groq_key)
                        resp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
                        st.markdown(resp.choices[0].message.content)
                        success = True
                except: pass

            # OPTION 2: DEEPINFRA (Cost Priority)
            if (mode == "DeepInfra" or not success) and di_key:
                try:
                    with st.spinner("Analyzing via DeepInfra (Meta-Llama)..."):
                        client = OpenAI(api_key=di_key, base_url="https://api.deepinfra.com/v1/openai")
                        resp = client.chat.completions.create(model="meta-llama/Llama-3.3-70B-Instruct", messages=[{"role": "user", "content": prompt}])
                        st.markdown(resp.choices[0].message.content)
                        success = True
                except: pass

            # OPTION 3: GEMINI (Original Primary)
            if (mode == "Gemini" or not success) and g_key:
                try:
                    with st.spinner("Analyzing via Gemini..."):
                        client = genai.Client(api_key=g_key)
                        resp = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
                        st.markdown(resp.text)
                        success = True
                except: pass

            # (OpenAI and OpenRouter blocks follow the same pattern if needed)

        except Exception as e:
            st.error(f"Critical System Error: {e}")
        
        if not success:
            st.error("All available engines failed or were out of credits.")
