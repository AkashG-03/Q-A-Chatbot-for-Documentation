# cleanup_embeddings.py - Run this script to clean existing embeddings
from __future__ import annotations
import os
import json
import shutil
import re
from datetime import datetime
from backend.rag.ingest import ingest_pdfs

def clean_html_from_text(text: str) -> str:
    """Remove HTML tags and clean text"""
    # Remove HTML tags
    clean_text = re.sub(r'<[^>]+>', '', text)
    
    # Clean up extra spaces that might be left
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    return clean_text.strip()

def backup_current_index():
    """Backup current index before cleaning"""
    index_dir = "data/index"
    backup_dir = f"data/index_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if os.path.exists(index_dir):
        shutil.copytree(index_dir, backup_dir)
        print(f"Current index backed up to: {backup_dir}")
        return backup_dir
    else:
        print("No existing index found to backup")
        return None

def clean_existing_metadata():
    """Clean HTML from existing metadata if present"""
    meta_path = "data/index/meta.json"
    
    if not os.path.exists(meta_path):
        print("No existing metadata found")
        return False
    
    with open(meta_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # Check if any entries have HTML tags
    has_html = False
    for entry in metadata:
        if '<' in entry.get('text', ''):
            has_html = True
            break
    
    if has_html:
        print(f"Found HTML tags in {len(metadata)} metadata entries")
        
        # Clean the text in each entry
        for entry in metadata:
            if 'text' in entry:
                original_text = entry['text']
                clean_text = clean_html_from_text(original_text)
                entry['text'] = clean_text
                
                if original_text != clean_text:
                    print(f"Cleaned entry from {entry.get('source', 'unknown')} page {entry.get('page', '?')}")
        
        # Save cleaned metadata
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print("Metadata cleaned and saved")
        return True
    else:
        print("No HTML tags found in metadata")
        return False

def main():
    """Main cleanup process"""
    print("Starting embeddings cleanup process...")
    
    # Step 1: Backup current index
    backup_path = backup_current_index()
    
    # Step 2: Check and clean existing metadata
    metadata_had_html = clean_existing_metadata()
    
    # Step 3: If HTML was found, we need to re-generate embeddings
    if metadata_had_html:
        print("\nHTML tags were found and cleaned from metadata.")
        print("Re-generating embeddings to ensure consistency...")
        
        # Remove the index and embeddings files (keep cleaned metadata temporarily)
        index_files = ["data/index/index.faiss", "data/index/embeddings.npy"]
        for file_path in index_files:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Removed {file_path}")
        
        # Re-ingest PDFs with clean text
        print("\nRe-ingesting PDFs with cleaned text processing...")
        try:
            result = ingest_pdfs(pdf_dir="data/pdfs", index_dir="data/index")
            print(f"\nCleanup completed successfully!")
            print(f"- {result.get('chunks', 0)} clean chunks created")
            print(f"- {result.get('text_chunks', 0)} text chunks")
            print(f"- {result.get('table_chunks', 0)} table chunks")
            print(f"- From {result.get('pdf_count', 0)} PDF files")
            
        except Exception as e:
            print(f"\nError during re-ingestion: {e}")
            print("You may need to manually upload PDFs again")
    else:
        print("\nNo cleanup needed - embeddings are already clean")
    
    print(f"\nCleanup process completed.")
    if backup_path:
        print(f"Original index backed up to: {backup_path}")

if __name__ == "__main__":
    main()