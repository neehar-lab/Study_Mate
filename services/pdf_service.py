import fitz


def extract_pages(pdf_bytes):
    with fitz.open(stream=pdf_bytes, filetype="pdf") as document:
        return [page.get_text("text").strip() for page in document]


def chunk_pages(pages, size=160, overlap=30):
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


def select_document_context(chunks, max_chunks=8, chars_per_chunk=1000):
    if not chunks:
        return ""
    count = min(len(chunks), max_chunks)
    indices = sorted({round(index * (len(chunks) - 1) / max(count - 1, 1)) for index in range(count)})
    excerpts = [
        f"[Source: {chunks[index]['source']} | Page {chunks[index]['page']}] {chunks[index]['text'][:chars_per_chunk]}"
        for index in indices
    ]
    return "\n\n".join(excerpts)
