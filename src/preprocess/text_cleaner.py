import re
from langdetect import detect

def clean_text(text):
    text = re.sub(r"<.*?>", "", text)
    text = re.sub(r"[\n\r\t]", " ", text)
    text = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9\s.,!?]", "", text)
    return text.strip()

