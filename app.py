import os
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path

import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
from PyPDF2 import PdfReader

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "app.log.json"

EIT_PERSONALITY = """You are Khalifa Mamadou NIAMADIO, a full-stack developer, technology innovator, and entrepreneur passionate about building solutions that solve real problems through software and community impact.

What defines you most isn't simply what you can build — it's how you approach the world around you:

* 🌟 Driven and Detail-Oriented
You dive deep into technology, not for prestige, but for mastery. You enjoy understanding how things work and why they work that way. This analytical instinct shines not only in code, but also in how you organize teams, structure projects, and plan your roadmap.

* 🧠 Learner at Heart
Your journey shows that you thrive when learning. From mastering backend logic to building sleek user-focused interfaces, you continuously expand your skillset — even when you've already mastered the fundamentals.

* 🤝 Collaborative and Vision-Oriented
You don't just code alone — you work with others. Whether it's coordinating a project team or partnering with clients, your communication, leadership, and vision help turn ideas into reality. Projects like ADEC Education bear your mark — initiatives where technical skill meets educational impact.

Your approach to technology reflects a blend of strategy and craftsmanship:

* 🔍 Thoughtful Planning
You don't jump into code blind. Every feature, integration, or architecture decision starts with a clear plan — considering both current needs and future expansion.

* 🧩 Balance Between Performance and Usability
Your systems are built to be fast, scalable, and user-friendly, not just technically impressive. You are deliberate about how users will interact with your products and how those products will hold up under growth.

* 📈 Vision for Continuous Growth
You don't view projects as finished when you launch — you see them as evolving ecosystems. You iterate, improve, and gather feedback — applying lessons from each deployment to make the next version even stronger.

You are currently an Entrepreneur In Training at MEST Africa.

When responding to user requests:
- Be helpful, concise, and friendly
- Use a conversational tone
- Show enthusiasm for technology and learning
- Be detailed and analytical when explaining concepts
- Keep responses focused and practical"""


def setup_logging():
    LOG_DIR.mkdir(exist_ok=True)
    if not LOG_FILE.exists():
        with open(LOG_FILE, "w") as f:
            json.dump([], f)


def log_event(level: str, event_type: str, metadata: dict):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "type": event_type,
        "metadata": metadata
    }
    
    try:
        with open(LOG_FILE, "r") as f:
            logs = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        logs = []
    
    logs.append(log_entry)
    
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)


def check_api_key() -> tuple[bool, str]:
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        return False, "❌ API Key Not Found\n\nPlease create a `.env` file in the project root and add your Google API key:\n\n```\nGOOGLE_API_KEY=your_api_key_here\n```\n\nGet your API key from: https://aistudio.google.com/app/apikey"
    
    if api_key == "your_api_key_here" or api_key.strip() == "":
        return False, "❌ API Key Not Configured\n\nPlease update your `.env` file with a valid Google API key.\n\nGet your API key from: https://aistudio.google.com/app/apikey"
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-3-flash-preview")
        model.generate_content("Hello")
        return True, "✅ API Key Initialized Successfully"
    except Exception as e:
        return False, f"❌ API Key Error: {str(e)}\n\nPlease check your API key and try again."


def summarize_link(url: str, model) -> str:
    prompt = f"""Please summarize the content from the following URL. Provide a clear, concise summary that captures the main points and key information:

URL: {url}

Summary:"""
    
    response = model.generate_content(prompt)
    return response.text


def summarize_pdf(pdf_file, model) -> str:
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    
    if len(text) > 50000:
        text = text[:50000] + "\n\n[Content truncated due to length]"
    
    prompt = f"""Please summarize the following PDF content. Provide a clear, concise summary that captures the main points and key information:

{text}

Summary:"""
    
    response = model.generate_content(prompt)
    return response.text


def initialize_session():
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "user_id" not in st.session_state:
        st.session_state.user_id = f"user_{uuid.uuid4().hex[:8]}"
    if "api_verified" not in st.session_state:
        st.session_state.api_verified = False
    if "api_message" not in st.session_state:
        st.session_state.api_message = ""
    if "messages" not in st.session_state:
        st.session_state.messages = []


def main():
    setup_logging()
    initialize_session()
    
    st.set_page_config(
        page_title="EIT AI Assistant",
        page_icon="🤖",
        layout="wide"
    )
    
    st.session_state.api_verified, st.session_state.api_message = check_api_key()
    
    with st.sidebar:
        st.title("🤖 EIT AI Assistant")
        st.markdown("---")
        
        if st.session_state.api_verified:
            st.success(st.session_state.api_message)
            st.markdown("### ℹ️ About")
            st.info("I'm **Khalifa Mamadou NIAMADIO**, an Entrepreneur In Training at MEST Africa. I'm a full-stack developer passionate about building solutions that solve real problems.")
        else:
            st.error(st.session_state.api_message)
            st.markdown("### 🚀 Setup Guide")
            st.markdown("""
            1. Get a Google API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
            2. Copy `.env.example` to `.env`
            3. Add your API key to `.env`
            4. Restart the app
            """)
        
        st.markdown("---")
        st.markdown(f"**Session ID:** `{st.session_state.session_id[:8]}...`")
    
    st.title("📚 EIT AI Assistant")
    st.markdown("Your personal AI assistant powered by Gemini 3 Flash")
    
    if not st.session_state.api_verified:
        st.warning("⚠️ Please configure your API key to use this application.")
        log_event("WARNING", "api_key_missing", {
            "user_id": st.session_state.user_id,
            "session_id": st.session_state.session_id
        })
        return
    
    tab1, tab2 = st.tabs(["🔗 Summarize Link", "📄 Summarize PDF"])
    
    with tab1:
        st.header("Summarize Article from Link")
        url = st.text_input("Enter article URL:", placeholder="https://example.com/article")
        
        if st.button("Summarize Link", type="primary"):
            if url:
                with st.spinner("🔄 Summarizing the article..."):
                    try:
                        model = genai.GenerativeModel("gemini-3-flash-preview")
                        summary = summarize_link(url, model)
                        
                        st.success("✅ Summary Generated!")
                        st.markdown("### 📝 Summary")
                        st.markdown(summary)
                        
                        log_event("INFO", "link_summarized", {
                            "user_id": st.session_state.user_id,
                            "session_id": st.session_state.session_id,
                            "model": "gemini-3-flash-preview",
                            "url": url
                        })
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        log_event("ERROR", "link_summarization_failed", {
                            "user_id": st.session_state.user_id,
                            "session_id": st.session_state.session_id,
                            "error": str(e)
                        })
            else:
                st.warning("Please enter a URL")
    
    with tab2:
        st.header("Summarize Article from PDF")
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
        
        if uploaded_file is not None and st.button("Summarize PDF", type="primary"):
            with st.spinner("🔄 Extracting and summarizing the PDF..."):
                try:
                    model = genai.GenerativeModel("gemini-3-flash-preview")
                    summary = summarize_pdf(uploaded_file, model)
                    
                    st.success("✅ Summary Generated!")
                    st.markdown("### 📝 Summary")
                    st.markdown(summary)
                    
                    log_event("INFO", "pdf_summarized", {
                        "user_id": st.session_state.user_id,
                        "session_id": st.session_state.session_id,
                        "model": "gemini-3-flash-preview",
                        "filename": uploaded_file.name
                    })
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    log_event("ERROR", "pdf_summarization_failed", {
                        "user_id": st.session_state.user_id,
                        "session_id": st.session_state.session_id,
                        "error": str(e)
                    })


if __name__ == "__main__":
    main()
