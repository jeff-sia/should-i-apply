import streamlit as st
from google import genai
from openai import OpenAI
from groq import Groq
import PyPDF2
from docx import Document
import io
import time

# --- 1. CONFIG & UI ---
st.set_page_config(page_title="JobScore Pro: Infinite Edition", layout="wide")

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

# --- 3. CALLBACKS ---
def update_jd():
    if st.session_state.jd_upload: st.session_state.jd_text = extract_text(st.session_state.jd_upload)
def update_resume():
    if st.session_state.resume_upload: st.session_state.resume_text = extract_text(st.session_state.resume_upload)

# --- 4. CONSENT GATE (FIXED SIDE-BY-SIDE) ---
if not st.session_state.consent:
    st.title("🛡️ Secure Analysis Gateway")
    st.info("Consent Required: Your information is used only for real-time processing and is never stored.")
    col_y, col_n = st.columns(2)
    with col_y:
        if st.button("1 - Yes, I consent", use_container_width=True):
            st.session_state.consent = True
            st.rerun()
    with col_n:
        if st.button("2 - No, I do not consent", use_container_width=True):
            st.error("Access Denied. Please close the tab.")
            st.stop()
    st.stop()

# --- 5. SIDEBAR ---
with st.sidebar:
    st.header("🔑 API Key Tank")
    g_key = st.text_input("Gemini API Key", type="password")
    oa_key = st.text_input("OpenAI API Key", type="password")
    or_key = st.text_input("OpenRouter Key", type="password")
    groq_key = st.text_input("Groq Key (Free Tier Available)", type="password")
    di_key = st.text_input("DeepInfra Key (Cheapest)", type="password")
    
    st.markdown("---")
    available = []
    if g_key: available.append("Gemini")
    if oa_key: available.append("OpenAI")
    if groq_key: available.append("Groq")
    if di_key: available.append("DeepInfra")
    if or_key: available.append("OpenRouter")
    
    mode = st.radio("Primary Engine", available) if available else None

# --- 6. MAIN INTERFACE ---
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

# --- 7. ANALYSIS LOGIC (SMART FAILOVER) ---
if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
    if not st.session_state.jd_text or not st.session_state.resume_text:
        st.error("Missing inputs: Please provide both documents.")
    elif not mode:
        st.error("No API keys found. Add keys in the sidebar.")
    else:
        prompt = f"Evaluate the RESUME against the JD using the H/I/V rubric. JD: {st.session_state.jd_text} Resume: {st.session_state.resume_text}"
        
        # Priority Order: Your choice first, then other available keys
        engine_order = [mode] + [e for e in available if e != mode]
        success = False
        
        for engine in engine_order:
            if success: break
            try:
                if engine == "Groq" and groq_key:
                    with st.spinner("Analyzing via Groq (Fastest)..."):
                        client = Groq(api_key=groq_key)
                        resp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
                        st.markdown(resp.choices[0].message.content); success = True
                
                elif engine == "DeepInfra" and di_key:
                    with st.spinner("Analyzing via DeepInfra (Llama 3.3)..."):
                        client = OpenAI(api_key=di_key, base_url="https://api.deepinfra.com/v1/openai")
                        resp = client.chat.completions.create(model="meta-llama/Llama-3.3-70B-Instruct", messages=[{"role": "user", "content": prompt}])
                        st.markdown(resp.choices[0].message.content); success = True
                
                elif engine == "Gemini" and g_key:
                    with st.spinner("Analyzing via Gemini..."):
                        client = genai.Client(api_key=g_key)
                        resp = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
                        st.markdown(resp.text); success = True

                elif engine == "OpenAI" and oa_key:
                    with st.spinner("Analyzing via OpenAI..."):
                        client = OpenAI(api_key=oa_key)
                        resp = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
                        st.markdown(resp.choices[0].message.content); success = True

            except Exception as e:
                # Clean error reporting
                st.warning(f"⚠️ {engine} failed (Credits/Rate Limit). Attempting next backup...")

        if not success:
            st.error("❌ Total System Failure: All available API keys have exhausted their credits.")
