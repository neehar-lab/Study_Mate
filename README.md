# StudyMate AI — GenAI Study Assistant

An AI study companion built with Python and Streamlit. Upload one or more study PDFs to get summaries, source-grounded answers, quizzes, flashcards, exam questions, voice input, and spoken answers in your chosen language.

## Problem Statement

Students spend time searching long study documents for key ideas and explanations. This app turns PDF material into summaries and practice activities, and answers questions from the uploaded source documents.

## Objectives

- Extract text from one or more study PDFs.
- Generate short and detailed summaries across the uploaded materials.
- Answer questions using relevant passages with filename and page citations.
- Generate quizzes, flashcards, and important exam questions.
- Support voice questions, multilingual output, and spoken answers.
- Keep API credentials out of source control.

## Features

- Multiple PDF upload with page-by-page text extraction.
- ChromaDB vector indexing and semantic RAG across the active PDFs.
- Short and detailed summaries.
- Typed Q&A and voice questions transcribed with Groq Whisper.
- Responses cite source PDF filenames and page numbers.
- Multiple-choice quizzes, flashcards, and exam questions at Beginner, Intermediate, or Advanced difficulty.
- Hidden answer keys for self-testing.
- English, Hindi, Telugu, Bengali, Spanish, French, German, Japanese, and Simplified Chinese response/audio language selection.
- Conversation history remains available in the current Streamlit session and can be cleared from the chat panel.

## Technology Stack

| Component | Technology |
| --- | --- |
| Programming | Python 3.10+ |
| UI | Streamlit |
| LLM and STT | Groq API and Whisper |
| PDF extraction | PyMuPDF |
| RAG/vector database | ChromaDB with local default embeddings |
| TTS | gTTS |
| Environment | python-dotenv and `.env` |

## Application Architecture

```text
Multiple PDFs -> PyMuPDF -> text chunks -> ChromaDB vector index ---+
                                                                    +-> Groq LLM -> answer / summaries / study set
Voice -> Groq Whisper -> question ---------------------------------+                    |
                                                                                       +-> gTTS audio
```

ChromaDB embeds and retrieves relevant chunks across the active documents. Retrieved text carries its source filename and page number into the answer prompt and citation display. Study prompts are maintained separately from UI and service code.

## Project Structure

```text
ai-study-assistant/
├── app.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
├── components/
│   ├── chat_panel.py
│   ├── practice_panel.py
│   ├── settings.py
│   └── summary_panel.py
├── services/
│   ├── groq_service.py
│   ├── pdf_service.py
│   ├── speech_service.py
│   └── vector_service.py
├── prompts/
│   └── study_prompts.py
└── screenshots/
```

## Installation Steps

1. Install Python 3.10 or newer.
2. Clone the repository and enter its directory:

   ```bash
   git clone https://github.com/neehar-lab/Study_Mate.git
   cd Study_Mate
   ```

3. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   On macOS or Linux, activate it with `source .venv/bin/activate`.

4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Environment Setup

Copy `.env.example` to `.env`, then add your Groq API key:

```env
GROQ_API_KEY=your_actual_groq_api_key
GROQ_MODEL=openai/gpt-oss-120b
```

Alternatively, enter the key in the app sidebar. Never commit `.env` or paste a real key into `.env.example`, source code, or screenshots. `.gitignore` excludes local secrets and Chroma data. Revoke and replace any key that has been exposed.

## How to Run

From the activated environment, run:

```bash
streamlit run app.py
```

Open the local URL shown by Streamlit. Add your key, select a response language, and upload one or more text-based PDFs. Use **Summaries**, **Ask your PDFs**, and **Practice**. Scanned PDFs need OCR before upload. ChromaDB downloads its default local embedding model on first use, so allow internet access for initial indexing. gTTS also requires internet access.

## Screenshots

Add app screenshots to `screenshots/` before submitting. Capture the upload view, generated summaries, an answer with source/page citations, and a practice activity. Mask API keys and private PDF content. See [`screenshots/README.md`](screenshots/README.md).

## Future Enhancements

- Add OCR for scanned documents.
- Improve cross-language retrieval with a multilingual embedding model.
- Add interactive quiz scoring, spaced repetition, and exportable notes.
- Add optional conversation persistence across sessions.

## Notes and Limitations

- Long-document summaries are generated from sections and combined, so the app does not discard everything after a fixed character limit. If Groq returns a 429 rate-limit error, the app waits and retries; persistent limits are shown for manual retry.
- PDF text and conversation history are held in Streamlit session state. ChromaDB indexes are in memory and disappear when the app process stops.
- Extracted passages and questions are sent to Groq for summaries, answers, and generated study materials.
