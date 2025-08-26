# check_embeddings.py - Simple script to check if embeddings contain HTML
from __future__ import annotations
import os
import json

def check_embeddings_for_html():
    """Check if existing embeddings contain HTML tags"""
    meta_path = "data/index/meta.json"
    
    if not os.path.exists(meta_path):
        print("No embeddings found at data/index/meta.json")
        print("This means no PDFs have been ingested yet.")
        return False
    
    print("Checking embeddings for HTML content...")
    
    with open(meta_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    html_entries = []
    total_entries = len(metadata)
    
    for i, entry in enumerate(metadata):
        text = entry.get('text', '')
        if '<' in text and '>' in text:  # Simple HTML tag detection
            html_entries.append({
                'index': i,
                'source': entry.get('source', 'unknown'),
                'page': entry.get('page', '?'),
                'preview': text[:200] + '...' if len(text) > 200 else text
            })
    
    print(f"Total entries: {total_entries}")
    print(f"Entries with HTML: {len(html_entries)}")
    
    if html_entries:
        print("\nHTML found in the following entries:")
        print("-" * 50)
        for entry in html_entries[:5]:  # Show first 5
            print(f"Source: {entry['source']}, Page: {entry['page']}")
            print(f"Preview: {entry['preview']}")
            print()
        
        if len(html_entries) > 5:
            print(f"... and {len(html_entries) - 5} more entries")
        
        print("\nACTION REQUIRED:")
        print("Your embeddings contain HTML tags and need cleaning.")
        print("Run: python cleanup_embeddings.py")
        return True
    else:
        print("\nGood news! Your embeddings are clean (no HTML found).")
        return False

if __name__ == "__main__":
    check_embeddings_for_html()