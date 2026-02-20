# --- 6. SCORING ENGINE (WITH CLEAR FAILOVER ALERTS) ---
if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
    if not st.session_state.jd_text or not st.session_state.resume_text:
        st.error("Missing inputs: Please provide both documents.")
    elif not mode:
        st.error("Missing API Key: Provide at least one key in the sidebar.")
    else:
        prompt = f"Evaluate RESUME against JD... [Rest of your prompt]"
        success = False
        
        # 🟢 Priority 1: Gemini
        if (mode == "Gemini" or not success) and g_key:
            try:
                with st.spinner("Analyzing via Gemini..."):
                    client = genai.Client(api_key=g_key)
                    resp = client.models.generate_content(model="gemini-3-flash-preview", contents=prompt)
                    st.markdown(resp.text)
                    success = True
            except Exception as e:
                # NEW: Clear warning so you know it failed
                st.warning(f"⚠️ Gemini Engine failed ({e}). Switching to backup...")

        # 🟠 Priority 2: Groq (Failover)
        if (not success) and groq_key:
            try:
                with st.spinner("🔄 Failover: Analyzing via Groq (Llama 3.3)..."):
                    client = Groq(api_key=groq_key)
                    resp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
                    st.markdown(resp.choices[0].message.content)
                    success = True
                    st.toast("✅ Analysis completed via Groq backup!")
            except Exception as e:
                st.warning(f"⚠️ Groq Failover also failed ({e}).")

        # 🔴 Priority 3: DeepInfra (Last Resort)
        if (not success) and di_key:
            try:
                with st.spinner("🔄 Final Failover: Analyzing via DeepInfra..."):
                    client = OpenAI(api_key=di_key, base_url="https://api.deepinfra.com/v1/openai")
                    resp = client.chat.completions.create(model="meta-llama/Llama-3.3-70B-Instruct", messages=[{"role": "user", "content": prompt}])
                    st.markdown(resp.choices[0].message.content)
                    success = True
            except Exception as e:
                st.error(f"❌ Critical Failure: All engines failed.")
