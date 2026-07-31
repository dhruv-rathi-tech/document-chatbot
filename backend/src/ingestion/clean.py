import re

def clean_text(text: str) -> str:
    text = text.replace("-\n", "")
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\[\d+\]", "", text)

    return text.strip()
