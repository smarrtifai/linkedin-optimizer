import fitz  # PyMuPDF

def extract_text_from_pdf(file_stream):
    doc = fitz.open(stream=file_stream.read(), filetype="pdf")
    lines = []
    links = []

    for page in doc:
        # Visible blocks
        blocks = page.get_text("blocks")
        for b in sorted(blocks, key=lambda x: (x[1], x[0])):
            text = b[4].strip()
            if text:
                lines.append(text)

        # Links
        for link in page.get_links():
            uri = link.get("uri")
            if uri and uri not in links:
                links.append(uri)

    return lines, links
