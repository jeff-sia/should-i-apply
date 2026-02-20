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
    or_key = st.text_input("OpenRouter Key", type="password")
    groq_key = st.text_input("Groq Key (Fastest)", type="password")
    di_key = st.text_input("DeepInfra Key (Cheapest)", type="password")
    
    st.markdown("---")
    # Identify which engines are ready
    available = []
    if g_key: available.append("Gemini")
    if oa_key: available.append("OpenAI")
    if or_key: available.append("OpenRouter")
    if groq_key: available.append("Groq")
    if di_key: available.append("DeepInfra")
    
    if available:
        mode = st.radio("Primary Engine", available)
    else:
        st.warning("No API keys detected.")
        mode = None

# --- 6. MAIN APP INTERFACE ---
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

# --- 7. ANALYSIS LOGIC (SMART SEQUENCE) ---
if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
    if not st.session_state.jd_text or not st.session_state.resume_text:
        st.error("Missing input data.")
    elif not mode:
        st.error("Please provide at least one API key in the sidebar.")
    else:
        prompt = f"Evaluate RESUME against JD... [Rest of your prompt]"
        
        # Define the priority order based on your radio selection
        all_keys = {
            "Gemini": g_key, 
            "OpenAI": oa_key, 
            "OpenRouter": or_key, 
            "Groq": groq_key, 
            "DeepInfra": di_key
        }
        
        # Put your chosen engine at the very front of the line
        engine_order = [mode] + [e for e in available if e != mode]
        
        success = False
        for current_engine in engine_order:
            if success: break
            
            try:
                # 🟡 1. Try Gemini
                if current_engine == "Gemini" and g_key:
                    with st.spinner("Analyzing via Gemini..."):
                        client = genai.Client(api_key=g_key)
                        resp = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
                        st.markdown(resp.text); success = True

                # 🔵 2. Try Groq
                elif current_engine == "Groq" and groq_key:
                    with st.spinner("Analyzing via Groq (Llama 3.3)..."):
                        client = Groq(api_key=groq_key)
                        resp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
                        st.markdown(resp.choices[0].message.content); success = True

                # 🟢 3. Try OpenAI
                elif current_engine == "OpenAI" and oa_key:
                    with st.spinner("Analyzing via OpenAI (GPT-4o)..."):
                        client = OpenAI(api_key=oa_key)
                        resp = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                        st.markdown(resp.choices[0].message.content); success = True

                # [Add similar blocks for DeepInfra and OpenRouter here]

            except Exception as e:
                st.warning(f"⚠️ {current_engine} failed: {e}. Moving to next available backup...")
        
        if not success:
            st.error("All engines failed. Please check your credit balances.")
