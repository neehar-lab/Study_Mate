import re
import time

import requests
import streamlit as st

from prompts.study_prompts import (
    GROUNDED_ANSWER_INSTRUCTIONS,
    PRACTICE_INSTRUCTIONS,
    SECTION_SUMMARY_INSTRUCTIONS,
    COMBINED_SUMMARY_INSTRUCTIONS,
)
from services.pdf_service import select_document_context
from services.vector_service import retrieve_rag_chunks

GROQ_API_URL = "https://api.groq.com/openai/v1"
NO_EVIDENCE_MESSAGES = {
    "English": "I couldn't find relevant information in the uploaded PDFs. Try rephrasing your question or check that the PDFs contain selectable text.",
    "Hindi": "अपलोड की गई PDF में इस प्रश्न से संबंधित जानकारी नहीं मिली। प्रश्न को दूसरे शब्दों में पूछें या जाँचें कि PDF में चयन योग्य टेक्स्ट है।",
    "Telugu": "అప్‌లోడ్ చేసిన PDFల్లో ఈ ప్రశ్నకు సంబంధించిన సమాచారం కనుగొనలేకపోయాను. ప్రశ్నను మరోలా అడగండి లేదా PDFల్లో ఎంపిక చేయగల టెక్స్ట్ ఉందో లేదో చూడండి.",
    "Bengali": "আপলোড করা PDF-এ এই প্রশ্নের প্রাসঙ্গিক তথ্য খুঁজে পাইনি। প্রশ্নটি অন্যভাবে করুন অথবা PDF-এ নির্বাচনযোগ্য লেখা আছে কি না দেখুন।",
    "Spanish": "No encontré información relevante en los PDF. Prueba a reformular la pregunta o comprueba que los PDF tengan texto seleccionable.",
    "French": "Je n’ai pas trouvé d’informations pertinentes dans les PDF. Reformulez la question ou vérifiez que les PDF contiennent du texte sélectionnable.",
    "German": "In den PDFs habe ich keine passenden Informationen gefunden. Formuliere die Frage um oder prüfe, ob die PDFs auswählbaren Text enthalten.",
    "Japanese": "アップロードされたPDFに関連情報が見つかりませんでした。質問を言い換えるか、PDFに選択可能なテキストがあるか確認してください。",
    "Chinese (Simplified)": "在上传的 PDF 中没有找到相关信息。请尝试改写问题，或确认 PDF 中包含可选文本。",
}


def _groq_error(response):
    try:
        detail = response.json().get("error", {}).get("message", response.text)
    except ValueError:
        detail = response.text
    return RuntimeError(f"Groq request failed (HTTP {response.status_code}): {detail}")


def ask_groq(prompt, system_prompt, model, api_key, max_completion_tokens=700):
    if not api_key:
        raise ValueError("Add your Groq API key in the sidebar or GROQ_API_KEY in .env.")
    for attempt in range(3):
        response = requests.post(
            f"{GROQ_API_URL}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.25,
                "max_completion_tokens": max_completion_tokens,
            },
            timeout=120,
        )
        if response.status_code == 429 and attempt < 2:
            retry_after = response.headers.get("retry-after")
            if retry_after:
                try:
                    delay = float(retry_after)
                except ValueError:
                    delay = 15
            else:
                detail = _groq_error(response).args[0]
                match = re.search(r"try again in ([0-9.]+)s", detail, re.IGNORECASE)
                delay = float(match.group(1)) if match else 15
            time.sleep(min(max(delay, 1), 60))
            continue
        if not response.ok:
            raise _groq_error(response)
        result = response.json()["choices"][0]
        if result.get("finish_reason") == "length":
            if attempt == 0:
                max_completion_tokens = min(max_completion_tokens * 2, 8192)
                continue
            raise RuntimeError("Groq truncated the response after retrying with a larger output limit.")
        return result["message"]["content"].strip()
    raise RuntimeError("Groq rate limit persisted after retries. Wait for the reset interval and retry the summary.")


@st.cache_data(ttl=300, show_spinner=False)
def get_groq_models(api_key):
    response = requests.get(
        f"{GROQ_API_URL}/models",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=20,
    )
    response.raise_for_status()
    model_ids = [item["id"] for item in response.json().get("data", []) if item.get("active", True)]
    non_chat_markers = ("whisper", "guard", "orpheus", "tts", "speech", "transcription", "distil")
    return [model_id for model_id in model_ids if not any(marker in model_id.lower() for marker in non_chat_markers)]


def answer_question(question, collection_name, model, api_key, language="English", conversation_history=None):
    evidence = retrieve_rag_chunks(collection_name, question)
    if not evidence:
        return NO_EVIDENCE_MESSAGES.get(language, NO_EVIDENCE_MESSAGES["English"]), []
    context = "\n\n".join(
        f"[Source: {item['source']} | Page {item['page']}] {item['text']}"
        for item in evidence
    )
    history = [
        f"Student: {entry[0]}\nAssistant: {entry[1][:500]}"
        for entry in (conversation_history or [])[-3:]
        if len(entry) >= 2
    ]
    history_text = "\n\n".join(history) or "No earlier conversation."
    prompt = (
        f"Retrieved study material (the source of factual answers):\n{context}\n\n"
        f"Recent conversation (use only to resolve follow-up references):\n{history_text}\n\n"
        f"Current question: {question}"
    )
    instructions = f"{GROUNDED_ANSWER_INSTRUCTIONS} Respond in {language}. Treat the PDF passages as the only source of facts."
    answer = ask_groq(prompt, instructions, model, api_key)
    return answer, evidence


def _summary_sections(pages, max_chars=3000):
    sections = []
    for page in pages:
        text = page["text"].strip()
        start = 0
        while start < len(text):
            end = min(start + max_chars, len(text))
            if end < len(text):
                boundary = text.rfind(" ", start + int(max_chars * 0.75), end)
                if boundary > start:
                    end = boundary
            excerpt = text[start:end].strip()
            if excerpt:
                sections.append(f"[Source: {page['source']} | Page {page['page']}] {excerpt}")
            start = end
    return sections


def generate_summaries(pages, model, api_key, language="English"):
    sections = _summary_sections(pages)
    if not sections:
        raise ValueError("No selectable text was found. Try an OCR-processed PDF.")
    instructions = COMBINED_SUMMARY_INSTRUCTIONS.format(language=language)
    full_text = "\n\n".join(sections)
    if len(full_text) <= 7000:
        result = ask_groq(full_text, instructions, model, api_key, 2200)
    else:
        section_notes = []
        for index, section in enumerate(sections, start=1):
            notes = ask_groq(
                section,
                f"{SECTION_SUMMARY_INSTRUCTIONS} Write in {language}.",
                model,
                api_key,
                350,
            )
            section_notes.append(f"Section {index} notes:\n{notes}")
        result = ask_groq("\n\n".join(section_notes), instructions, model, api_key, 2600)

    short_match = re.search(r"(?im)^##\s*Short Summary\s*$", result)
    detailed_match = re.search(r"(?im)^##\s*Detailed Summary\s*$", result)
    if short_match and detailed_match and detailed_match.start() > short_match.end():
        short_summary = result[short_match.end():detailed_match.start()].strip()
        detailed_summary = result[detailed_match.end():].strip()
        if short_summary and detailed_summary:
            return short_summary, detailed_summary
    raise RuntimeError("The model returned an incomplete summary format. Click Retry summaries to generate it again.")


def generate_study_material(chunks, study_mode, difficulty, model, api_key, language="English"):
    if not chunks:
        raise ValueError("No readable PDF text is available for practice generation.")
    context = select_document_context(chunks)
    instructions = PRACTICE_INSTRUCTIONS.format(
        difficulty=difficulty.lower(),
        study_mode=study_mode.lower(),
        language=language,
    )
    return ask_groq(context, instructions, model, api_key, 1400)


def transcribe_audio(audio_bytes, mime_type, api_key, language_code="en"):
    if not api_key:
        raise ValueError("Add your Groq API key in the sidebar or GROQ_API_KEY in .env.")
    response = requests.post(
        f"{GROQ_API_URL}/audio/transcriptions",
        headers={"Authorization": f"Bearer {api_key}"},
        files={"file": ("question.wav", audio_bytes, mime_type or "audio/wav")},
        data={"model": "whisper-large-v3-turbo", "response_format": "json", "language": language_code},
        timeout=120,
    )
    if not response.ok:
        raise _groq_error(response)
    return response.json().get("text", "").strip()
