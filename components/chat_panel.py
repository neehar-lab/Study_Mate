import requests
import streamlit as st

from services.groq_service import answer_question, transcribe_audio
from services.speech_service import text_to_speech


def render_chat_panel(collection_name, model, api_key, language, tts_language, whisper_language, usable_pages):
    st.caption("Answers use relevant passages from your PDFs and include source and page references.")
    st.caption("Conversation history stays in this browser session until you clear it.")
    if st.button("Clear conversation history"):
        st.session_state.chat = []
        st.rerun()
    voice = st.audio_input("Ask by voice")
    if voice and st.button("Transcribe and ask", disabled=not api_key, help="Voice transcription uses Groq Whisper."):
        try:
            recognized = transcribe_audio(voice.getvalue(), voice.type, api_key, whisper_language)
            st.write(f"**You asked:** {recognized}")
            if recognized:
                with st.spinner("Finding the answer in your PDFs…"):
                    response_text, evidence = answer_question(
                        recognized, collection_name, model, api_key, language, st.session_state.chat
                    )
                st.session_state.chat.append((recognized, response_text, evidence, tts_language))
        except (requests.RequestException, ValueError, KeyError, RuntimeError) as error:
            st.error(f"Voice request failed: {error}")
    with st.form("question_form", clear_on_submit=True):
        question = st.text_input("Your question", placeholder="Explain the main concept on page 4…")
        submitted = st.form_submit_button("Ask", disabled=not usable_pages or not api_key)
    if submitted and question.strip():
        with st.spinner("Finding the answer in your PDFs…"):
            try:
                response_text, evidence = answer_question(
                    question.strip(), collection_name, model, api_key, language, st.session_state.chat
                )
                st.session_state.chat.append((question.strip(), response_text, evidence, tts_language))
            except (requests.RequestException, ValueError, KeyError, RuntimeError) as error:
                st.error(f"Answer failed: {error}")
    for index, entry in enumerate(st.session_state.get("chat", [])):
        user_question, response_text, evidence = entry[:3]
        answer_voice_language = entry[3] if len(entry) > 3 else tts_language
        with st.chat_message("user"):
            st.write(user_question)
        with st.chat_message("assistant"):
            st.markdown(response_text)
            if evidence:
                citations = sorted({(item["source"], item["page"]) for item in evidence})
                st.caption("Sources: " + "; ".join(f"{source}, p. {page}" for source, page in citations))
            if st.button("🔊 Play answer", key=f"speak-{index}"):
                try:
                    st.audio(text_to_speech(response_text, answer_voice_language), format="audio/mp3")
                except Exception as error:
                    st.error(f"Speech generation failed: {error}")
