import streamlit as st
import google.generativeai as genai
import PyPDF2
import io

# --- 1. MANDATORY CONSENT GATE ---
if "consent" not in st.session_state:
    st.session_state.consent = False

if not st.session_state.consent:
    st.title("Consent Required")
    st.write("You may be asked to share your resume or other personal information. This information will be used only to process your request (job fit scoring, resume evaluation, or interview preparation) within this conversation. Your information will not be stored, reused, shared, or used for training.")
    
    st.write("Choose one option:")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("1 - Yes, I consent"):
            st.session_state.consent = True
            st.rerun()
    with col2:
        if st.button("2 - No, I do not consent"):
            st.error("Understood. I will not process any personal information. Let me know if you change your mind.")
            st.stop()

# --- 2. APP UI (Visible only after consent) ---
st.title("🚀 JobScore & Resume Optimizer")
st.sidebar.header("Setup")
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password", help="Get one for free at aistudio.google.com")

if not api_key:
    st.info("Please enter your Gemini API Key in the sidebar to begin.")
    st.stop()

genai.configure(api_key=api_key)

jd_text = st.text_area("1. Paste the Job Description (JD) here:", height=200)
uploaded_file = st.file_uploader("2. Upload your Resume (PDF)", type="pdf")

if st.button("Analyze My Fit"):
    if jd_text and uploaded_file:
        with st.spinner("Analyzing with brutal honesty..."):
            # Extract text from PDF
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
            resume_text = "".join([page.extract_text() for page in pdf_reader.pages])
            
            # AI Prompting
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"""
            You are a brutally honest jobseeker assistant. 
            Evaluate this Resume against the Job Description.
            
            JD: {jd_text}
            RESUME: {resume_text}
            
            Follow the SCORING SYSTEM:
            - Hard Skills (50%)
            - Industry Experience (30%)
            - Valued Extras (20%)
            Score using 0-5 per item.
            Final Formula: (H/5 * 50) + (I/5 * 30) + (V/5 * 20)
            
            Use the EXACT Output Format:
            ### Your Self-Match Report
            ... (Position, Company, Final Match Score, Tier)
            ---
            ### 🔹 1️⃣ Hard Skills Fit (50%)
            ...
            ---
            ### 📌 Summary
            ...
            ### 🟢 Action Plan (if score >= 60%)
            ...
            ### ❌ Not Recommended (if score < 60%)
            """
            
            response = model.generate_content(prompt)
            st.markdown(response.text)
    else:
        st.error("Please provide both the Job Description and your Resume.")
