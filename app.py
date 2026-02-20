import streamlit as st
from google import genai
from openai import OpenAI
import PyPDF2
from docx import Document
import io

# --- 1. CONFIG & UI ---
st.set_page_config(page_title="JobScore Pro: Triple Engine", layout="wide")

def extract_text(uploaded_file):
    try:
        if uploaded_file.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
            return "".join([page.extract_text() for page in pdf_reader.pages])
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(io.BytesIO(uploaded_file.read()))
            return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        st.error(f"File Parsing Error: {e}")
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

# --- 4. CONSENT GATE (MANDATORY) ---
if not st.session_state.consent:
    st.title("🛡️ Secure Analysis Gateway")
    st.info("Consent Required: Your information will be used only to process your request. It will not be stored, reused, shared, or used for training.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("1 - Yes, I consent"):
            st.session_state.consent = True
            st.rerun()
    with col2:
        if st.button("2 - No, I do not consent"):
            st.error("Understood. I will not process any personal information.")
else:
    # --- 5. MAIN INTERFACE ---
    st.title("🚀 JobScore & Resume Optimizer")
    
    with st.sidebar:
        st.header("⚙️ LLM Backend")
        gemini_key = st.text_input("Gemini API Key", type="password")
        openai_key = st.text_input("OpenAI API Key", type="password")
        or_key = st.text_input("OpenRouter Key", type="password")
        
        st.markdown("---")
        mode = st.radio("Primary Engine", ["Gemini", "OpenAI", "OpenRouter"])
        
        if st.button("Reset / Revoke Consent"):
            st.session_state.consent = False
            st.rerun()

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
            st.error("Missing inputs.")
        else:
            prompt = f"""
            You are a brutally honest jobseeker assistant. Evaluate the RESUME against the JD.
            
            SCORING:
            - Hard Skills (H): 50% | Industry Experience (I): 30% | Valued Extras (V): 20%.
            - Formula: (H/5 * 50) + (I/5 * 30) + (V/5 * 20).
            
            RULES:
            - Blunt, direct tone. No assumptions.
            - If score < 60%, output '❌ Not Recommended'.
            
            JD: {st.session_state.jd_text}
            RESUME: {st.session_state.resume_text}
            """
            
            success = False
            
            # ENGINE 1: GEMINI
            if mode == "Gemini" and gemini_key:
                try:
                    with st.spinner("Analyzing via Gemini..."):
                        client = genai.Client(api_key=gemini_key)
                        response = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
                        st.markdown(response.text)
                        success = True
                except Exception as e:
                    st.warning(f"Gemini failed: {e}")

            # ENGINE 2: OPENAI (Direct)
            if not success and mode == "OpenAI" and openai_key:
                try:
                    with st.spinner("Analyzing via GPT-4o..."):
                        oa_client = OpenAI(api_key=openai_key)
                        completion = oa_client.chat.completions.create(
                            model="gpt-4o",
                            messages=[{"role": "user", "content": prompt}]
                        )
                        st.markdown(completion.choices[0].message.content)
                        success = True
                except Exception as e:
                    st.warning(f"OpenAI failed: {e}")

            # ENGINE 3: OPENROUTER (Final Failover)
            if not success and or_key:
                try:
                    with st.spinner("Analyzing via OpenRouter (Claude)..."):
                        or_client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=or_key)
                        completion = or_client.chat.completions.create(
                            model="anthropic/claude-3.5-sonnet",
                            messages=[{"role": "user", "content": prompt}]
                        )
                        st.markdown(completion.choices[0].message.content)
                        success = True
                except Exception as e:
                    st.error(f"All engines failed: {e}")

            if not success and not (gemini_key or openai_key or or_key):
                st.error("Please provide an API key for your selected engine in the sidebar.")
