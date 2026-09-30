from io import BytesIO

from gtts import gTTS


def text_to_speech(text, language="en"):
    audio = BytesIO()
    gTTS(text, lang=language).write_to_fp(audio)
    return audio.getvalue()
