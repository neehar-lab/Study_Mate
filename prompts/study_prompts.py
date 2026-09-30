GROUNDED_ANSWER_INSTRUCTIONS = (
    "Answer using only the supplied study material. If it does not contain the answer, say so. "
    "Be clear and student-friendly. Cite the source filename and page, for example (notes.pdf, p. 3)."
)

SHORT_SUMMARY_INSTRUCTIONS = (
    "Write a concise summary of the central ideas and most important takeaways in 5–8 bullets. "
    "Cite source filenames and page numbers where possible. Keep the summary under 150 words."
)

DETAILED_SUMMARY_INSTRUCTIONS = (
    "Create a detailed, well-structured study guide. Explain key concepts, relationships, terminology, "
    "and takeaways using headings and bullets. Cite source filenames and page numbers where possible. "
    "Keep the guide compact, with no more than 8 key concepts and about 500 words."
)

SECTION_SUMMARY_INSTRUCTIONS = (
    "Summarize this section of a study document as concise notes. Capture its key ideas, "
    "definitions, examples, and relationships. Retain source filename and page references. "
    "Use up to 6 bullets and do not claim this is a summary of the whole document."
)

COMBINED_SUMMARY_INSTRUCTIONS = (
    "Using all the supplied source text or section notes, produce both requested summaries. "
    "Keep all substantive sections represented and preserve important concepts, definitions, "
    "and relationships. Cite source filenames and page numbers where provided. "
    "Format exactly with headings '## Short Summary' and '## Detailed Summary'. "
    "Under Short Summary, write 5–8 concise bullets. Under Detailed Summary, use headings and bullets "
    "to cover the important concepts without arbitrarily stopping mid-sentence. "
    "Write both summaries in {language}."
)

PRACTICE_INSTRUCTIONS = (
    "Create a {difficulty} level {study_mode} using only the provided study material. "
    "Cite source PDF filenames and page numbers in questions or answers where possible. "
    "Use exactly two Markdown sections: '## Try first' and '## Answer key'. "
    "Put all questions or flashcard fronts under Try first; do not reveal answers there. "
    "Put concise correct answers and explanations under Answer key. For multiple-choice quizzes, "
    "write 5 questions with four options labeled A–D. For flashcards, write 8 focused cards. "
    "For exam questions, write 5 open-ended prompts and concise answer outlines. "
    "Write in {language}. Do not invent facts that are absent from the source."
)
