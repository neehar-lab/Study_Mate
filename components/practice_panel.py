import re

import requests
import streamlit as st

from services.groq_service import generate_study_material


def render_practice_panel(chunks, document_id, model, api_key, language, usable_pages):
    st.caption("Try questions from your PDFs before revealing the answers.")
    study_mode = st.selectbox("Study activity", ["Multiple-choice quiz", "Flashcards", "Exam questions"])
    difficulty = st.select_slider("Difficulty", options=["Beginner", "Intermediate", "Advanced"], value="Intermediate")
    signature = (document_id, model, language, study_mode, difficulty)
    if st.button("Generate study set", disabled=not usable_pages or not api_key):
        with st.spinner(f"Creating {difficulty.lower()} {study_mode.lower()}…"):
            try:
                material = generate_study_material(chunks, study_mode, difficulty, model, api_key, language)
                st.session_state.study_set = {"signature": signature, "material": material}
            except (requests.RequestException, ValueError, KeyError, RuntimeError) as error:
                st.error(f"Study set generation failed: {error}")
    study_set = st.session_state.get("study_set")
    if study_set and study_set.get("signature") == signature:
        parts = re.split(r"(?im)^##\s*Answer key\s*$", study_set["material"], maxsplit=1)
        if len(parts) == 2:
            try_first = re.sub(r"(?im)^##\s*Try first\s*$", "", parts[0], count=1).strip()
            st.markdown(try_first)
            with st.expander("Reveal answers and explanations"):
                st.markdown(parts[1].strip())
        else:
            st.markdown(study_set["material"])
