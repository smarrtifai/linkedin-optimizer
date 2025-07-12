import fitz  # PyMuPDF

def extract_text_from_pdf(file_stream):
    try:
        doc = fitz.open(stream=file_stream.read(), filetype="pdf")
    except Exception as e:
        print("❌ Error reading PDF:", repr(e))
        raise ValueError("Invalid or unreadable PDF file.")

    lines = []
    links = []

    for page in doc:
        try:
            # Text blocks
            blocks = page.get_text("blocks")
            for b in sorted(blocks, key=lambda x: (x[1], x[0])):
                text = b[4].strip()
                if text:
                    lines.append(text)

            # Hyperlinks
            for link in page.get_links():
                uri = link.get("uri")
                if uri and uri not in links:
                    links.append(uri)
        except Exception as page_error:
            print("❌ Error processing page:", repr(page_error))
            continue  # Skip problematic page

    return lines, links
