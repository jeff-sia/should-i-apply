import streamlit as st
from google import genai
from openai import OpenAI
from groq import Groq
import PyPDF2
from docx import Document
import io

# --- 1. CONFIG & UI ---
st.set_page_config(page_title="JobScore Pro: SIA Standard", layout="wide")

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

# --- 4. CONSENT GATE (MANDATORY) ---
if not st.session_state.consent:
    st.title("🛡️ Secure Analysis Gateway")
    st.info("Consent Required: Your information is processed in real-time and never stored for training.")
    col_y, col_n = st.columns(2)
    with col_y:
        if st.button("1 - Yes, I consent", use_container_width=True):
            st.session_state.consent = True
            st.rerun()
    with col_n:
        if st.button("2 - No, I do not consent", use_container_width=True):
            st.error("Access Denied.")
            st.stop()
    st.stop()

# --- 5. SIDEBAR (API KEY TANK) ---
with st.sidebar:
    st.header("🔑 API Key Tank")
    g_key = st.text_input("Gemini API Key", type="password")
    oa_key = st.text_input("OpenAI API Key", type="password")
    or_key = st.text_input("OpenRouter Key", type="password")
    groq_key = st.text_input("Groq Key", type="password")
    di_key = st.text_input("DeepInfra Key", type="password")
    
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
    st.file_uploader("Upload JD or paste in the text field below", type=["pdf", "docx"], key="jd_upload", on_change=update_jd)
    st.session_state.jd_text = st.text_area("JD Content:", value=st.session_state.jd_text, height=300)
with col_b:
    st.subheader("📄 2. Your Resume")
    st.file_uploader("Upload Resume or paste in the text field below", type=["pdf", "docx"], key="resume_upload", on_change=update_resume)
    st.session_state.resume_text = st.text_area("Resume Content:", value=st.session_state.resume_text, height=300)

# --- 7. THE PRECISION SIA ANALYSIS ENGINE ---
if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
    if not st.session_state.jd_text or not st.session_state.resume_text:
        st.error("Please provide both documents.")
    elif not mode:
        st.error("Add an API key in the sidebar.")
    else:
        # MASTER PROMPT: Enforces SIA Standard
        prompt = f"""
        ACT AS: A Brutally Honest Recruitment Expert. 
        TASK: Produce a 'Self-Match Report' following the exact hierarchy and scoring rigor of the SIA Gold Standard.

        PHASE 1: EVIDENCE MAPPING (Internal Thinking)
        - List every key requirement from the JD.
        - Map EXACT sentences from the Resume to these requirements.
        - No evidence = 0 points. Do not infer skills.

        PHASE 2: SCORING ALGORITHM
        1. Hard Skills (H): Scale 0-5. Weight 50%.
        2. Industry Experience (I): Scale 0-5. Weight 30%.
        3. Valued Extras (V): Scale 0-5. Weight 20%.
        
        FORMULA: (H_Score/5 * 50) + (I_Score/5 * 30) + (V_Score/5 * 20).
        Round to the nearest whole number.

        PHASE 3: SIA OUTPUT GENERATION (Strict Structure)
        Use the following EXACT Markdown hierarchy:

        ### Your Self-Match Report is [Score]%
        **Tier**: [Excellent/Strong/Moderate/Low Fit]
        **Position**: [Parsed Role]
        **Company**: [Parsed Company]

        ---
        ### 🔹 1. Hard Skills Fit (50%)
        **Score**: [X]/5 ([X]%) - **Weighted**: [X]/50
        | Requirement | Match | Evidence |
        | :--- | :--- | :--- |
        | [Requirement Name] | [✅ or ❌] | [Direct Evidence Quote or "No direct mention"] |

        ### 🔹 2. Industry Experience Fit (30%)
        **Score**: [X]/5 ([X]%) - **Weighted**: [X]/30
        - [Mapping of tenure, sector-specific experience, and seniority]

        ### 🔹 3. Valued Extras Fit (20%)
        **Score**: [X]/5 ([X]%) - **Weighted**: [X]/20
        - [Assets, soft skills, and certifications]

        ---
        ### 📝 Summary
        [Mention the score and their tier. Follow with a brutally honest 2-sentence summary of the match]

        ### 🟢 Action Plan (Strategic Positioning)
        1. [Advice on shifting positioning to match this specific role]
        2. **Resume Optimization Module**[trigger only if score >60%]: Rewrite a specific bullet point from the current resume to better align with the JD requirements.

        ### 🎯 Strategic Advice
        [Final 'Apply' or 'Do Not Apply' recommendation]

        JD: {st.session_state.jd_text}
        Resume: {st.session_state.resume_text}
        """
        
        engine_order = [mode] + [e for e in available if e != mode]
        success = False
        
        for engine in engine_order:
            if success: break
            try:
                if engine == "Groq" and groq_key:
                    with st.spinner("Analyzing via Groq..."):
                        client = Groq(api_key=groq_key)
                        resp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
                        st.markdown(resp.choices[0].message.content); success = True
                elif engine == "Gemini" and g_key:
                    with st.spinner("Analyzing via Gemini..."):
                        client = genai.Client(api_key=g_key)
                        resp = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
                        st.markdown(resp.text); success = True
                elif engine == "OpenAI" and oa_key:
                    with st.spinner("Analyzing via OpenAI..."):
                        client = OpenAI(api_key=oa_key)
                        resp = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                        st.markdown(resp.choices[0].message.content); success = True
                elif engine == "DeepInfra" and di_key:
                    with st.spinner("Analyzing via DeepInfra..."):
                        client = OpenAI(api_key=di_key, base_url="https://api.deepinfra.com/v1/openai")
                        resp = client.chat.completions.create(model="meta-llama/Llama-3.3-70B-Instruct", messages=[{"role": "user", "content": prompt}])
                        st.markdown(resp.choices[0].message.content); success = True
                elif engine == "OpenRouter" and or_key:
                    with st.spinner("Analyzing via OpenRouter..."):
                        client = OpenAI(api_key=or_key, base_url="https://openrouter.ai/api/v1")
                        resp = client.chat.completions.create(model="anthropic/claude-3.5-sonnet", messages=[{"role": "user", "content": prompt}])
                        st.markdown(resp.choices[0].message.content); success = True
            except Exception as e:
                st.warning(f"⚠️ {engine} failed. Trying backup...")

        if not success:
            st.error("❌ All engines failed. Please check your API keys.")
