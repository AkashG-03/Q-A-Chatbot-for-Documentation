from __future__ import annotations

import os
import fitz  # PyMuPDF for general text extraction
import pdfplumber  # For table extraction
import faiss
import numpy as np
from typing import Dict, Any, List

from backend.rag.utils import clean_text, chunk_text
from backend.rag.embeddings import embed_texts
from backend.rag.store import save_index


# -----------------------------
# Small helper utilities
# -----------------------------

def format_table_as_text(table: List[List[str]]) -> str:
    """
    Convert table data to readable text format.
    
    Args:
        table: 2D list representing table data.
        
    Returns:
        Formatted table as text string.
    """
    if not table:
        return ""

    formatted_rows = []
    for row in table:
        formatted_row = [str(cell).strip() if cell is not None else "" for cell in row]
        if any(cell for cell in formatted_row):  # keep only non-empty rows
            formatted_rows.append(" | ".join(formatted_row))

    return "\n".join(formatted_rows)


# -----------------------------
# Extraction utilities
# -----------------------------

def extract_pdf_pages_fallback(path: str) -> List[Dict[str, Any]]:
    """
    Fallback PDF extraction using PyMuPDF for basic text.
    
    Args:
        path: Path to PDF file.
        
    Returns:
        List of page dictionaries.
    """
    try:
        doc = fitz.open(path)
        pages = []
        filename = os.path.basename(path)

        for i, page in enumerate(doc, start=1):
            text = page.get_text("text")
            if text and text.strip():
                pages.append({
                    "page": i,
                    "text": text,
                    "source": filename,
                    "type": "text"
                })

        doc.close()
        return pages

    except Exception as e:
        print(f"Error extracting PDF {path}: {e}")
        return []


def extract_text_and_tables(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extract both plain text and tables from PDF using pdfplumber.
    
    Args:
        pdf_path: Path to the PDF file.
        
    Returns:
        List of dictionaries containing page text and table data.
    """
    chunks = []
    filename = os.path.basename(pdf_path)

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                # Extract plain text
                text = page.extract_text()
                if text and text.strip():
                    chunks.append({
                        "page": page_num,
                        "text": text,
                        "source": filename,
                        "type": "text"
                    })

                # Extract tables and convert to text format
                tables = page.extract_tables()
                for table_idx, table in enumerate(tables):
                    if table:
                        table_text = format_table_as_text(table)
                        if table_text.strip():
                            chunks.append({
                                "page": page_num,
                                "text": table_text,
                                "source": filename,
                                "type": f"table_{table_idx + 1}"
                            })

        return chunks

    except Exception as e:
        print(f"Error extracting from {pdf_path} with pdfplumber: {e}")
        return extract_pdf_pages_fallback(pdf_path)


# -----------------------------
# Main ingestion pipeline
# -----------------------------

def ingest_pdfs(pdf_dir: str = "data/pdfs", index_dir: str = "data/index") -> Dict[str, Any]:
    """
    Process all PDFs in a directory and create search index with table support.
    
    Args:
        pdf_dir: Directory containing PDF files.
        index_dir: Directory to save search index.
        
    Returns:
        Dictionary containing ingestion statistics.
    """
    if not os.path.isdir(pdf_dir):
        return {
            "chunks": 0,
            "message": f"PDF directory not found: {pdf_dir}",
            "pdf_count": 0,
            "success": False,
        }

    entries = []
    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")]

    if not pdf_files:
        return {
            "chunks": 0,
            "message": "No PDF files found in directory",
            "pdf_count": 0,
            "success": False,
        }

    print(f"Processing {len(pdf_files)} PDF files...")

    for filename in pdf_files:
        full_path = os.path.join(pdf_dir, filename)
        print(f"Processing: {filename}")

        # Extract both text and tables
        page_data = extract_text_and_tables(full_path)

        for page_info in page_data:
            cleaned_text = clean_text(page_info["text"] or "")
            if not cleaned_text.strip():
                continue

            # Split into chunks with appropriate size for tables vs text
            max_tokens = 1200 if page_info["type"].startswith("table") else 800
            chunks = chunk_text(cleaned_text, max_tokens=max_tokens, overlap=120)

            for chunk in chunks:
                if len(chunk.strip()) > 50:  # only keep substantial chunks
                    entries.append({
                        "text": chunk,
                        "page": page_info["page"],
                        "source": page_info["source"],
                        "type": page_info["type"],
                    })

    if not entries:
        return {
            "chunks": 0,
            "message": "No extractable text found in PDFs",
            "pdf_count": len(pdf_files),
            "success": False,
        }

    print(f"Created {len(entries)} text chunks from {len(pdf_files)} PDFs")

    # Create embeddings
    print("Generating embeddings...")
    texts = [entry["text"] for entry in entries]
    embeddings = embed_texts(texts)

    # Create FAISS index
    print("Building search index...")
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
    index.add(embeddings)

    # Save everything
    print(f"Saving index to {index_dir}...")
    save_index(index_dir=index_dir, index=index, embeddings=embeddings, metadatas=entries)

    # Count different content types
    text_count = sum(1 for e in entries if e["type"] == "text")
    table_count = sum(1 for e in entries if e["type"].startswith("table"))

    return {
        "chunks": len(entries),
        "text_chunks": text_count,
        "table_chunks": table_count,
        "index_dir": index_dir,
        "pdf_count": len(pdf_files),
        "success": True,
        "message": (
            f"Successfully indexed {len(entries)} chunks "
            f"({text_count} text, {table_count} table) from {len(pdf_files)} PDFs"
        ),
    }
