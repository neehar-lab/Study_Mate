import os

import requests
import streamlit as st
from dotenv import load_dotenv

from services.groq_service import get_groq_models

load_dotenv()

LANGUAGES = {
    "English": ("en", "en"),
    "Hindi": ("hi", "hi"),
    "Telugu": ("te", "te"),
    "Bengali": ("bn", "bn"),
    "Spanish": ("es", "es"),
    "French": ("fr", "fr"),
    "German": ("de", "de"),
    "Japanese": ("ja", "ja"),
    "Chinese (Simplified)": ("zh-CN", "zh"),
}


def render_settings():
    with st.sidebar:
        st.header("Groq settings")
        api_key = st.text_input("Groq API key", value=os.getenv("GROQ_API_KEY", ""), type="password")
        st.caption("Set GROQ_API_KEY in .env or enter your key here.")
        language = st.selectbox("Response language", list(LANGUAGES))
        available_models = []
        if api_key:
            try:
                available_models = get_groq_models(api_key)
            except requests.RequestException as error:
                st.caption(f"Could not load available models: {error}")
        preferred_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        if available_models:
            default_index = available_models.index(preferred_model) if preferred_model in available_models else 0
            model = st.selectbox("Available Groq chat model", available_models, index=default_index)
        else:
            model = st.text_input("Groq model", value=preferred_model)
    tts_language, whisper_language = LANGUAGES[language]
    return api_key, model, language, tts_language, whisper_language
