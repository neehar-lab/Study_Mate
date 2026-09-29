import io
import hashlib
import os
import re
from collections import Counter

import fitz
import requests
import streamlit as st
from dotenv import load_dotenv
from gtts import gTTS

load_dotenv()

st.set_page_config(page_title="StudyMate AI", page_icon="📚", layout="wide")


def extract_pages(pdf_bytes):
    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    return [page.get_text("text").strip() for page in document]


def chunk_pages(pages, size=1150, overlap=180):
    chunks = []
    for page_number, text in enumerate(pages, start=1):
        words = text.split()
        start = 0
        while start < len(words):
            part = " ".join(words[start : start + size])
            if part:
                chunks.append({"page": page_number, "text": part})
            start += size - overlap
    return chunks


def retrieve(question, chunks, limit=5):
    terms = re.findall(r"[a-zA-Z0-9]+", question.lower())
    query = Counter(term for term in terms if len(term) > 2)
    scored = []
    for chunk in chunks:
        words = re.findall(r"[a-zA-Z0-9]+", chunk["text"].lower())
        counts = Counter(words)
        score = sum(min(counts[term], 3) * weight for term, weight in query.items())
        if score:
            scored.append((score, chunk))
    return [chunk for _, chunk in sorted(scored, key=lambda item: item[0], reverse=True)[:limit]]


def ask_llm(prompt, system_prompt, backend, model, api_key, base_url, max_completion_tokens=700):
    if backend == "Groq":
        if not api_key:
            raise ValueError("Add your Groq API key in the sidebar or GROQ_API_KEY in .env.")
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": model, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}], "temperature": 0.25, "max_completion_tokens": max_completion_tokens},
            timeout=120,
        )
        if not response.ok:
            try:
                detail = response.json().get("error", {}).get("message", response.text)
            except ValueError:
                detail = response.text
            raise RuntimeError(f"Groq chat request failed (HTTP {response.status_code}): {detail}")
        return response.json()["choices"][0]["message"]["content"].strip()
    response = requests.post(
        f"{base_url.rstrip('/')}/api/chat",
        json={"model": model, "stream": False, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]},
        timeout=180,
    )
    response.raise_for_status()
    return response.json()["message"]["content"].strip()


@st.cache_data(ttl=300, show_spinner=False)
def get_groq_models(api_key):
    response = requests.get(
        "https://api.groq.com/openai/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=20,
    )
    response.raise_for_status()
    model_ids = [item["id"] for item in response.json().get("data", []) if item.get("active", True)]
    non_chat_markers = ("whisper", "guard", "orpheus", "tts", "speech", "transcription", "distil")
    return [model_id for model_id in model_ids if not any(marker in model_id.lower() for marker in non_chat_markers)]


def answer_question(question, backend, model, api_key, base_url, chunks):
    evidence = retrieve(question, chunks)
    if not evidence:
        return "I couldn't find relevant information in the uploaded PDF. Try rephrasing your question or check that the PDF contains selectable text.", []
    context = "\n\n".join(f"[Page {item['page']}] {item['text']}" for item in evidence)
    system = "Answer using only the supplied study material. If it does not contain the answer, say so. Be clear and student-friendly. Cite supporting page numbers like (p. 3)."
    return ask_llm(f"Study material:\n{context}\n\nQuestion: {question}", system, backend, model, api_key, base_url), evidence


def summarize(pages, backend, model, api_key, base_url, detailed=False):
    text = "\n".join(f"[Page {number}] {content}" for number, content in enumerate(pages, 1) if content)
    if not text.strip():
        raise ValueError("No selectable text was found in this PDF. Try an OCR-processed PDF.")
    limit = 10500
    if len(text) > limit:
        text = text[:limit] + "\n[Document excerpt truncated; summarize the available material only.]"
    instruction = "Create a detailed, well-structured study guide. Explain key concepts, relationships, terminology, and takeaways using headings and bullets. Cite page numbers where possible." if detailed else "Write a concise summary of the central ideas and most important takeaways in 5–8 bullets. Cite page numbers where possible."
    if detailed:
        instruction += " Keep the guide compact, with no more than 8 key concepts and about 500 words."
        max_completion_tokens = 1000
    else:
        instruction += " Keep the summary under 150 words."
        max_completion_tokens = 400
    return ask_llm(text, instruction, backend, model, api_key, base_url, max_completion_tokens)


st.title("📚 StudyMate AI")
st.caption("Turn your study PDFs into clear summaries and grounded answers, by text or voice.")

with st.sidebar:
    st.header("Groq settings")
    backend = "Groq"
    api_key = st.text_input("Groq API key", value=os.getenv("GROQ_API_KEY", ""), type="password")
    base_url = ""
    st.caption("Set GROQ_API_KEY in .env or enter your key here.")
    available_models = []
    model_list_error = None
    if api_key:
        try:
            available_models = get_groq_models(api_key)
        except requests.RequestException as error:
            model_list_error = str(error)
    preferred_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    if available_models:
        default_index = available_models.index(preferred_model) if preferred_model in available_models else 0
        model = st.selectbox("Available Groq chat model", available_models, index=default_index)
    else:
        model = st.text_input("Groq model", value=preferred_model)
        if model_list_error:
            st.caption(f"Could not load available models: {model_list_error}")

uploaded = st.file_uploader("Upload study material", type=["pdf"], help="Text-based PDFs work best. Scanned PDFs need OCR first.")
if uploaded:
    pdf_bytes = uploaded.getvalue()
    identity = hashlib.sha256(pdf_bytes).hexdigest()
    if st.session_state.get("document_identity") != identity:
        with st.spinner("Reading PDF pages…"):
            pages = extract_pages(pdf_bytes)
        st.session_state.document_identity = identity
        st.session_state.pages = pages
        st.session_state.chunks = chunk_pages(pages)
        st.session_state.chat = []
        st.session_state.pop("short_summary", None)
        st.session_state.pop("detailed_summary", None)
        st.session_state.pop("summary_identity", None)
        st.session_state.pop("summary_attempted", None)

    pages = st.session_state.pages
    chunks = st.session_state.chunks
    usable_pages = sum(bool(page) for page in pages)
    st.success(f"{uploaded.name} · {len(pages)} pages · text found on {usable_pages} pages")
    if not usable_pages:
        st.warning("This PDF has no selectable text. Run OCR on it and upload the searchable PDF.")
    elif not api_key:
        st.info("Add your Groq API key in the sidebar to generate summaries and ask questions.")
    elif st.session_state.get("summary_identity") != (identity, model) and st.session_state.get("summary_attempted") != (identity, model):
        with st.spinner("Generating your short and detailed summaries…"):
            st.session_state.summary_attempted = (identity, model)
            try:
                st.session_state.short_summary = summarize(pages, backend, model, api_key, base_url)
                st.session_state.detailed_summary = summarize(pages, backend, model, api_key, base_url, detailed=True)
                st.session_state.summary_identity = (identity, model)
            except (requests.RequestException, ValueError, KeyError, RuntimeError) as error:
                st.error(f"Automatic summary failed: {error}")
                if st.button("Retry summaries"):
                    st.session_state.pop("summary_attempted", None)
                    st.rerun()

    summary_tab, ask_tab = st.tabs(["📝 Summaries", "💬 Ask your PDF"])
    with summary_tab:
        first, second = st.columns(2)
        with first:
            if st.button("Generate short summary", disabled=not usable_pages or not api_key, use_container_width=True):
                with st.spinner("Summarizing the key ideas…"):
                    try:
                        st.session_state.short_summary = summarize(pages, backend, model, api_key, base_url)
                    except (requests.RequestException, ValueError, KeyError, RuntimeError) as error:
                        st.error(f"Summary failed: {error}")
        with second:
            if st.button("Generate detailed summary", disabled=not usable_pages or not api_key, use_container_width=True):
                with st.spinner("Building your study guide…"):
                    try:
                        st.session_state.detailed_summary = summarize(pages, backend, model, api_key, base_url, detailed=True)
                    except (requests.RequestException, ValueError, KeyError, RuntimeError) as error:
                        st.error(f"Summary failed: {error}")
        if st.session_state.get("short_summary"):
            st.subheader("Short summary")
            st.markdown(st.session_state.short_summary)
        if st.session_state.get("detailed_summary"):
            st.subheader("Detailed summary")
            st.markdown(st.session_state.detailed_summary)

    with ask_tab:
        st.caption("Answers use relevant passages from your PDF and include page references.")
        voice = st.audio_input("Ask by voice")
        if voice and st.button("Transcribe and ask", disabled=backend != "Groq", help="Voice transcription uses Groq Whisper."):
            try:
                if not api_key:
                    raise ValueError("Add your Groq API key in the sidebar or GROQ_API_KEY in .env.")
                response = requests.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    files={"file": ("question.wav", voice.getvalue(), voice.type or "audio/wav")},
                    data={"model": "whisper-large-v3-turbo", "response_format": "json"},
                    timeout=120,
                )
                response.raise_for_status()
                recognized = response.json().get("text", "").strip()
                st.write(f"**You asked:** {recognized}")
                if recognized:
                    with st.spinner("Finding the answer in your PDF…"):
                        response_text, evidence = answer_question(recognized, backend, model, api_key, base_url, chunks)
                    st.session_state.chat.append((recognized, response_text, evidence))
            except (requests.RequestException, ValueError, KeyError) as error:
                st.error(f"Voice request failed: {error}")
        with st.form("question_form", clear_on_submit=True):
            question = st.text_input("Your question", placeholder="Explain the main concept on page 4…")
            submitted = st.form_submit_button("Ask", disabled=not usable_pages or not api_key)
        if submitted and question.strip():
            with st.spinner("Finding the answer in your PDF…"):
                try:
                    response_text, evidence = answer_question(question.strip(), backend, model, api_key, base_url, chunks)
                    st.session_state.chat.append((question.strip(), response_text, evidence))
                except (requests.RequestException, ValueError, KeyError, RuntimeError) as error:
                    st.error(f"Answer failed: {error}")

        for user_question, response_text, evidence in st.session_state.get("chat", []):
            with st.chat_message("user"):
                st.write(user_question)
            with st.chat_message("assistant"):
                st.markdown(response_text)
                if evidence:
                    pages_cited = sorted({item["page"] for item in evidence})
                    st.caption("Relevant PDF pages: " + ", ".join(map(str, pages_cited)))
                if st.button("🔊 Play answer", key=f"speak-{len(user_question)}-{hash(response_text)}"):
                    try:
                        audio = io.BytesIO()
                        gTTS(response_text).write_to_fp(audio)
                        st.audio(audio.getvalue(), format="audio/mp3")
                    except Exception as error:
                        st.error(f"Speech generation failed: {error}")
else:
    st.info("Upload a PDF to get started. Your document is processed in this app session.")