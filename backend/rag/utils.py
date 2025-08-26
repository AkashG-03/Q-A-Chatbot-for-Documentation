# backend/rag/utils.py
from __future__ import annotations

import re


# -----------------------------
# Simple Cleaning / Normalization
# -----------------------------

def clean_text(t: str) -> str:
    """
    Clean and normalize text for better processing and indexing.
    
    Args:
        t: Raw text string to clean
        
    Returns:
        Cleaned and normalized text
    """
    if not t:
        return ""
    
    # Replace bullet points and special Unicode characters
    t = t.replace('\u2022', '•').replace('\u00b7', '•')
    t = t.replace('\u2013', '-').replace('\u2014', '--')  # En/em dashes
    t = t.replace('\u201c', '"').replace('\u201d', '"')  # Smart quotes
    t = t.replace('\u2018', "'").replace('\u2019', "'")  # Smart apostrophes
    
    # Fix common PDF extraction issues
    t = re.sub(r'(\w)-\s+(\w)', r'\1\2', t)  # Hyphenated words split across lines
    t = re.sub(r'\s+', ' ', t)  # Normalize whitespace
    t = re.sub(r'\n{3,}', '\n\n', t)  # Reduce excessive line breaks
    
    # Clean up medical text formatting
    t = re.sub(r'(\d+)\s*\.\s*(\d+)', r'\1.\2', t)  # Decimal numbers
    t = re.sub(r'(\w)\s+%', r'\1%', t)  # Percentage spacing
    t = re.sub(r'(\d+)\s+(mg|mcg|g|ml|L|kg|lb)', r'\1 \2', t)  # Dosage units
    t = re.sub(r'(\d+)\s*(°[CF])', r'\1\2', t)  # Temperature units
    
    # Clean up extra spaces around punctuation
    t = re.sub(r'\s+([,.!?;:])', r'\1', t)
    t = re.sub(r'([,.!?;:])\s*([,.!?;:])', r'\1 \2', t)
    
    return t.strip()


def normalize_medical_text(text: str) -> str:
    """
    Normalize medical text for better search and matching.
    
    Args:
        text: Input medical text
        
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # Convert to lowercase
    normalized = text.lower()
    
    # Standardize common medical abbreviations
    abbrev_mappings = {
        r'\bp\.?o\.?\b': 'by mouth',
        r'\bi\.?v\.?\b': 'intravenous',
        r'\bi\.?m\.?\b': 'intramuscular',
        r'\bs\.?c\.?\b': 'subcutaneous',
        r'\bb\.?i\.?d\.?\b': 'twice daily',
        r'\bt\.?i\.?d\.?\b': 'three times daily',
        r'\bq\.?i\.?d\.?\b': 'four times daily',
        r'\bq\.?d\.?\b': 'once daily',
        r'\bp\.?r\.?n\.?\b': 'as needed'
    }
    for pattern, replacement in abbrev_mappings.items():
        normalized = re.sub(pattern, replacement, normalized)
    
    # Standardize dosage formats
    normalized = re.sub(r'(\d+)\s*mgs?\b', r'\1 mg', normalized)
    normalized = re.sub(r'(\d+)\s*mcgs?\b', r'\1 mcg', normalized)
    
    return normalized


def format_table_text(table_rows: list) -> str:
    """
    Format table data into readable text format.
    
    Args:
        table_rows: List of table rows (each row is a list of cells)
        
    Returns:
        Formatted table as text string
    """
    if not table_rows:
        return ""
    
    formatted_rows = []
    for row in table_rows:
        formatted_cells = []
        for cell in row:
            if cell is not None:
                cell_text = str(cell).strip()
                formatted_cells.append(cell_text if cell_text else "-")
            else:
                formatted_cells.append("-")
        
        # Only add non-empty rows
        if any(cell != "-" for cell in formatted_cells):
            formatted_rows.append(" | ".join(formatted_cells))
    
    return "\n".join(formatted_rows)


# -----------------------------
# Chunking Helpers
# -----------------------------

def _chunk_by_words(words: list[str], max_tokens: int = 800, overlap: int = 120) -> list[str]:
    """
    Fallback word-based chunking when sentence splitting fails.
    
    Args:
        words: List of words to chunk
        max_tokens: Maximum tokens per chunk
        overlap: Overlap tokens between chunks
        
    Returns:
        List of text chunks
    """
    chunks = []
    i = 0
    step = max_tokens - overlap

    while i < len(words):
        chunk_words = words[i:i+max_tokens]
        chunk_text = ' '.join(chunk_words)
        if chunk_text.strip() and len(chunk_text) > 50:
            chunks.append(chunk_text)
        i += step

    return chunks


def chunk_text(text: str, max_tokens: int = 800, overlap: int = 120) -> list[str]:
    """
    Split text into overlapping chunks with better sentence awareness.
    Approximate tokens by words (rough estimate: 1 token ≈ 0.75 words).
    
    Args:
        text: Text to chunk
        max_tokens: Maximum tokens per chunk
        overlap: Overlap tokens between chunks
        
    Returns:
        List of text chunks
    """
    if not text or not text.strip():
        return []

    # Sentence-based splitting
    sentences = re.split(r'(?<=[.!?])\s+', text)
    if len(sentences) <= 1:
        # Fallback to word-based chunking
        words = text.split()
        return _chunk_by_words(words, max_tokens, overlap) if words else []

    chunks = []
    current_chunk, current_length = [], 0
    
    i = 0
    while i < len(sentences):
        sentence = sentences[i].strip()
        sentence_length = len(sentence.split())
        
        if current_length + sentence_length > max_tokens and current_chunk:
            # Commit current chunk
            chunk_text = ' '.join(current_chunk).strip()
            if chunk_text and len(chunk_text) > 50:
                chunks.append(chunk_text)
            
            # Start new chunk with overlap
            overlap_sentences = current_chunk[-2:] if len(current_chunk) >= 2 else current_chunk
            current_chunk = overlap_sentences.copy()
            current_length = sum(len(s.split()) for s in current_chunk)
        
        # Add current sentence
        current_chunk.append(sentence)
        current_length += sentence_length
        i += 1
    
    # Final chunk
    if current_chunk:
        chunk_text = ' '.join(current_chunk).strip()
        if chunk_text and len(chunk_text) > 50:
            chunks.append(chunk_text)
    
    print(f"Created {len(chunks)} chunks from text of length {len(text)}")
    return chunks


# -----------------------------
# Entity Extraction
# -----------------------------

def extract_medical_entities(text: str) -> dict:
    """
    Extract common medical entities from text for better processing.
    
    Args:
        text: Input medical text
        
    Returns:
        Dictionary containing extracted entities
    """
    entities = {
        "dosages": [],
        "medications": [],
        "conditions": [],
        "units": []
    }
    
    # Dosage patterns
    dosage_patterns = [
        r'\d+\s*(?:mg|mcg|g|ml|L|units?|IU)',
        r'\d+\s*(?:times?|x)\s*(?:daily|per day|a day)',
        r'(?:once|twice|three times?)\s*(?:daily|per day|a day)'
    ]
    for pattern in dosage_patterns:
        entities["dosages"].extend(re.findall(pattern, text, re.IGNORECASE))
    
    # Abbreviations
    entities["abbreviations"] = re.findall(r'\b[A-Z]{2,5}\b', text)
    
    # Numeric values with units
    entities["units"] = re.findall(r'\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|L|°[CF]|%)', text)
    
    return entities
