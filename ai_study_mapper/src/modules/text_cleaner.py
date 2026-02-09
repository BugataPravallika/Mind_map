import re
from typing import List

class TextCleaner:
    """
    Cleans and segments text for further processing.
    """

    def __init__(self):
        # Regex patterns for cleaning
        self.citation_pattern = r'\[\d+\]'  # Matches [1], [12], etc.
        self.parenthetical_ref_pattern = r'\([A-Za-z]+, \d{4}\)' # Matches (Smith, 2020) roughly
        self.et_al_ref_pattern = r'\([A-Za-z][A-Za-z\-]+ et al\.,?\s*\d{4}\)'  # (Smith et al., 2020)
        self.url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        self.doi_pattern = r'\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b'
        self.latex_block_pattern = r'(\$\$[\s\S]*?\$\$)|\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\)'
        self.multiple_spaces = r'\s+'
        self.references_heading_pattern = re.compile(
            r'^\s*(references|bibliography|works cited|citations)\s*$', re.IGNORECASE
        )

    def clean_text(self, text: str) -> str:
        """
        Removes noise from the text (citations, URLs, equations, reference sections).
        """
        if not text:
            return ""

        # Cut off trailing references/bibliography (common in PDFs)
        lines = text.splitlines()
        trimmed_lines = []
        for line in lines:
            if self.references_heading_pattern.match(line.strip()):
                break
            trimmed_lines.append(line)
        text = "\n".join(trimmed_lines)

        # Remove latex/math blocks
        text = re.sub(self.latex_block_pattern, " ", text)

        # Remove citation noise
        text = re.sub(self.citation_pattern, '', text)
        text = re.sub(self.parenthetical_ref_pattern, '', text)
        text = re.sub(self.et_al_ref_pattern, '', text)
        text = re.sub(self.url_pattern, '', text)
        text = re.sub(self.doi_pattern, '', text, flags=re.IGNORECASE)

        # Drop lines that look like dense equations/symbol soup (simple heuristic)
        cleaned_lines = []
        for line in text.splitlines():
            s = line.strip()
            if not s:
                cleaned_lines.append("")
                continue
            symbol_ratio = sum(1 for ch in s if ch in "=<>±×÷^_{}[]\\|~") / max(1, len(s))
            digit_ratio = sum(1 for ch in s if ch.isdigit()) / max(1, len(s))
            if symbol_ratio > 0.18 and digit_ratio > 0.08:
                continue
            cleaned_lines.append(s)
        text = "\n".join(cleaned_lines)

        # Normalize whitespace
        text = re.sub(self.multiple_spaces, ' ', text)
        # Restore paragraph breaks (collapse multiple blank lines)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def segment_text(self, text: str, max_chunk_size: int = 1000, min_chunk_size: int = 250) -> List[str]:
        """
        Segments text into chunks of approximately max_chunk_size, 
        respecting sentence + paragraph boundaries.
        """
        if not text:
            return []

        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
        sentences: List[str] = []
        for p in paragraphs:
            # Basic sentence splitting (good enough after pivot-to-English)
            sentences.extend([s.strip() for s in re.split(r'(?<=[.!?])\s+', p) if s.strip()])

        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_len = len(sentence)
            if current_length + sentence_len > max_chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk).strip())
                current_chunk = [sentence]
                current_length = sentence_len
            else:
                current_chunk.append(sentence)
                current_length += sentence_len
        
        if current_chunk:
            chunks.append(" ".join(current_chunk).strip())

        # Merge tiny chunks to avoid summarizer underflow
        merged: List[str] = []
        buf = ""
        for ch in chunks:
            if not buf:
                buf = ch
                continue
            if len(buf) < min_chunk_size:
                buf = (buf + " " + ch).strip()
            else:
                merged.append(buf)
                buf = ch
        if buf:
            merged.append(buf)
            
        return merged

if __name__ == "__main__":
    cleaner = TextCleaner()
    sample = "This is a test sentence. [1] It has a citation (Doe, 2023). And a url http://example.com."
    cleaned = cleaner.clean_text(sample)
    print(f"Original: {sample}")
    print(f"Cleaned: {cleaned}")
