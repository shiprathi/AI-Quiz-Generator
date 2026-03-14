from pypdf import PdfReader


def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)

    text = ""

    for page in reader.pages:
        content = page.extract_text()
        if content:
            text += content

    return text


def chunk_text(text, chunk_size=800):
    chunks = []

    for i in range(0, len(text), chunk_size):
        chunk = text[i:i + chunk_size]
        chunks.append(chunk)

    return chunks