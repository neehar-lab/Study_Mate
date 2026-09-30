import requests
import streamlit as st

from services.groq_service import generate_summaries


def _generate_summaries(pages, model, api_key, language):
    short_summary, detailed_summary = generate_summaries(pages, model, api_key, language)
    st.session_state.short_summary = short_summary
    st.session_state.detailed_summary = detailed_summary


def render_summary_panel(pages, document_id, model, api_key, language, usable_pages):
    summary_signature = (document_id, model, language, "sectioned-v2")
    if st.session_state.get("summary_identity") != summary_signature:
        st.session_state.pop("short_summary", None)
        st.session_state.pop("detailed_summary", None)
    if usable_pages and api_key and st.session_state.get("summary_identity") != summary_signature and st.session_state.get("summary_attempted") != summary_signature:
        with st.spinner("Generating your short and detailed summaries…"):
            st.session_state.summary_attempted = summary_signature
            try:
                _generate_summaries(pages, model, api_key, language)
                st.session_state.summary_identity = summary_signature
                st.session_state.pop("summary_error", None)
            except (requests.RequestException, ValueError, KeyError, RuntimeError) as error:
                st.session_state.summary_error = str(error)

    if api_key and st.session_state.get("summary_attempted") == summary_signature and st.session_state.get("summary_error"):
        st.error(f"Summary failed: {st.session_state.summary_error}")
        if st.button("Retry summaries"):
            st.session_state.pop("summary_attempted", None)
            st.session_state.pop("summary_error", None)
            st.rerun()

    if usable_pages and api_key and not st.session_state.get("summary_identity") and not st.session_state.get("summary_attempted"):
        if st.button("Generate both summaries", use_container_width=True):
            with st.spinner("Summarizing all document sections…"):
                try:
                    _generate_summaries(pages, model, api_key, language)
                    st.session_state.summary_identity = summary_signature
                    st.session_state.pop("summary_error", None)
                except (requests.RequestException, ValueError, KeyError, RuntimeError) as error:
                    st.error(f"Summary failed: {error}")
    if st.session_state.get("short_summary"):
        st.subheader("Short summary")
        st.markdown(st.session_state.short_summary)
    if st.session_state.get("detailed_summary"):
        st.subheader("Detailed summary")
        st.markdown(st.session_state.detailed_summary)
