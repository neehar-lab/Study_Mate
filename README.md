<<<<<<< HEAD
# StudyMate AI — GenAI Study Assistant

An AI study companion built with Python and Streamlit. Upload a study PDF to get concise and detailed summaries, ask questions grounded in its content, use your voice to ask questions, and listen to spoken answers.

## Problem Statement

Students often spend significant time searching long study documents for key ideas and explanations. StudyMate AI turns PDF material into summaries and answers questions using the uploaded document as its source.

## Objectives

- Accept a study PDF and extract its text page by page.
- Generate short and detailed summaries of the material.
- Answer questions using relevant passages from the uploaded document.
- Support voice questions through speech recognition.
- Convert answers to playable speech.
- Keep API credentials out of source control.

## Features

- PDF upload and text extraction with PyMuPDF.
- Automatic short and detailed summaries after upload when a Groq API key is configured.
- Typed questions and voice questions transcribed with Groq Whisper.
- Relevant passage retrieval with page references in answers.
- Text-to-speech playback using gTTS.
- Groq chat model choices loaded for the configured API key.
- Session-based document and conversation state; uploaded documents are not saved by the app.

## Technology Stack

| Component | Technology |
| --- | --- |
| Programming language | Python 3.10+ |
| User interface | Streamlit |
| LLM and speech recognition | Groq API and Whisper |
| PDF processing | PyMuPDF |
| Text-to-speech | gTTS |
| Environment configuration | python-dotenv and `.env` |

## Application Architecture

```text
PDF upload ──> PyMuPDF extraction ──> page chunks ──┐
                                                    ├──> Groq LLM ──> answer / summaries
Voice input ──> Groq Whisper ──> question ──────────┘                     │
                                                                          └──> gTTS audio
```

PDF questions retrieve matching text chunks and include their source page numbers in the prompt and answer. The Streamlit interface is in `app.py` and `components/`; external service and document operations are in `services/`; model instructions are in `prompts/`.

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
│   ├── settings.py
│   └── summary_panel.py
├── services/
│   ├── groq_service.py
│   ├── pdf_service.py
│   └── speech_service.py
├── prompts/
│   └── study_prompts.py
└── screenshots/
```

## Installation Steps

1. Install Python 3.10 or newer.
2. Clone the repository and move into its folder:

   ```bash
   git clone https://github.com/YOUR_USERNAME/ai-study-assistant.git
   cd ai-study-assistant
   ```

3. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   # Windows PowerShell: .venv\Scripts\Activate.ps1
   # macOS/Linux: source .venv/bin/activate
   ```

4. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Environment Setup

1. Copy `.env.example` to `.env`.
2. Add your Groq API key to `.env`:

   ```env
   GROQ_API_KEY=your_actual_groq_api_key
   GROQ_MODEL=openai/gpt-oss-120b
   ```

The app can also accept the API key in its sidebar. Never commit `.env`, paste API keys into source files, or include them in screenshots. `.gitignore` excludes `.env` and common local environment files. If a key is exposed, revoke it and create a replacement in the Groq Console.

## How to Run

From the repository root, activate the virtual environment and run:

```bash
streamlit run app.py
```

Open the local URL printed by Streamlit. Enter a Groq API key if it is not configured in `.env`, upload a text-based PDF, and use the Summaries and Ask your PDF tabs. Scanned PDFs need OCR before upload. Text-to-speech uses gTTS and requires an internet connection.

## Screenshots

Add screenshots of the running application to `screenshots/`. Suggested captures are the upload/home view, generated summaries, a PDF-grounded answer with page references, and the audio playback control. Only include screenshots that do not reveal API keys or private documents.

See [`screenshots/README.md`](screenshots/README.md) for capture guidance.

## Future Enhancements

- Add OCR for scanned PDFs.
- Support multiple PDFs and document selection.
- Improve retrieval with embeddings and a vector store such as FAISS or Chroma.
- Add flashcards, multiple-choice quizzes, and exam-question generation.
- Add difficulty selection and multilingual summaries and speech.
- Add user-configurable conversation history and exportable notes.

## Notes and Limitations

- Very long document summaries use the first 10,500 characters; question answering retrieves from all extracted pages.
- Summary outputs are capped to help fit Groq token-per-minute limits. If a 429 rate-limit response occurs, wait for the reset interval in the message and retry, or review your Groq plan and organization limits.
- PDF files and conversation history are held in Streamlit session state and are not persisted by this app.
=======
# Study_Mate
>>>>>>> 293af529c910c882ecf1d4dfe5af7976b60687ad
