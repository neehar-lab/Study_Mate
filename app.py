import hashlib

import streamlit as st

from components.chat_panel import render_chat_panel
from components.practice_panel import render_practice_panel
from components.settings import render_settings
from components.summary_panel import render_summary_panel
from services.pdf_service import chunk_pages, extract_pages
from services.vector_service import build_rag_index, delete_rag_index

st.set_page_config(page_title="StudyMate AI", page_icon="📚", layout="wide")
st.title("📚 StudyMate AI")
st.caption("Turn your study PDFs into clear summaries and grounded answers, by text or voice.")

api_key, model, language, tts_language, whisper_language = render_settings()
uploaded_files = st.file_uploader(
    "Upload study material",
    type=["pdf"],
    help="Text-based PDFs work best. Scanned PDFs need OCR first.",
    accept_multiple_files=True,
)

if not uploaded_files:
    st.info("Upload one or more PDFs to get started. Documents are processed in this app session.")
    st.stop()

cached_pages = st.session_state.get("pdf_cache", {})
documents = []
for uploaded in uploaded_files:
    pdf_bytes = uploaded.getvalue()
    content_id = hashlib.sha256(pdf_bytes).hexdigest()
    try:
        pages = cached_pages.get(content_id)
        if pages is None:
            with st.spinner(f"Reading {uploaded.name}…"):
                pages = extract_pages(pdf_bytes)
        documents.append({"id": content_id, "name": uploaded.name, "pages": pages})
    except Exception as error:
        st.error(f"Could not read {uploaded.name}: {error}")

if not documents:
    st.warning("No uploaded PDF could be read.")
    st.stop()

st.session_state.pdf_cache = {document["id"]: document["pages"] for document in documents}
document_signature = hashlib.sha256(
    "|".join(sorted(f"{document['id']}:{document['name']}" for document in documents)).encode()
).hexdigest()
pages = [
    {"source": document["name"], "page": page_number, "text": text}
    for document in documents
    for page_number, text in enumerate(document["pages"], start=1)
]
chunks = [
    {**chunk, "source": document["name"]}
    for document in documents
    for chunk in chunk_pages(document["pages"])
]
usable_pages = sum(bool(page["text"]) for page in pages)
st.success(f"{len(documents)} PDF(s) · {sum(len(document['pages']) for document in documents)} pages · text found on {usable_pages} pages")
with st.expander("Uploaded documents"):
    for document in documents:
        st.write(f"• {document['name']} — {len(document['pages'])} pages")

if st.session_state.get("rag_signature") != document_signature:
    previous_index = st.session_state.get("rag_collection")
    try:
        if chunks:
            with st.spinner("Building the semantic search index…"):
                collection_name = build_rag_index(chunks)
        else:
            collection_name = None
        st.session_state.rag_collection = collection_name
        st.session_state.rag_signature = document_signature
        if previous_index:
            delete_rag_index(previous_index)
        for key in ("short_summary", "detailed_summary", "summary_identity", "summary_attempted", "summary_error", "study_set"):
            st.session_state.pop(key, None)
    except Exception as error:
        st.error(f"Could not build the ChromaDB search index: {error}")
        st.stop()

if "chat" not in st.session_state:
    st.session_state.chat = []

if not usable_pages:
    st.warning("These PDFs have no selectable text. Run OCR on them and upload searchable PDFs.")
elif not api_key:
    st.info("Add your Groq API key in the sidebar to generate summaries and ask questions.")

summary_tab, ask_tab, practice_tab = st.tabs(["📝 Summaries", "💬 Ask your PDFs", "🎯 Practice"])
with summary_tab:
    render_summary_panel(pages, document_signature, model, api_key, language, usable_pages)
with ask_tab:
    render_chat_panel(st.session_state.get("rag_collection"), model, api_key, language, tts_language, whisper_language, usable_pages)
with practice_tab:
    render_practice_panel(chunks, document_signature, model, api_key, language, usable_pages)
