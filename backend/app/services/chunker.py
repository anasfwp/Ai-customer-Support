from typing import List, Dict
import re

class Chunker:
    def __init__(self, chunk_size: int = 300, overlap: int = 50):
        self.chunk_size = chunk_size  # Reduced from 500 to 300 for better granularity
        self.overlap = overlap
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """Split text into overlapping chunks by sentences/paragraphs"""
        if not text or not text.strip():
            return []
        
        # Clean the text
        text = re.sub(r'\n+', '\n', text)  # Remove multiple newlines
        text = re.sub(r'[^\S\n]+', ' ', text)  # Normalize whitespace but keep newlines, or paragraphs collapse into one chunk

        # Try to split by paragraphs first (better semantic chunks); split any paragraph longer than a chunk into word windows
        paragraphs = []
        for p in text.split('\n'):
            words = p.split()
            paragraphs += [' '.join(words[i:i + self.chunk_size]) for i in range(0, len(words), self.chunk_size)]
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for paragraph in paragraphs:
            paragraph_length = len(paragraph.split())
            
            # If adding this paragraph exceeds chunk size, save current chunk
            if current_length + paragraph_length > self.chunk_size and current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunk_metadata = (metadata or {}).copy()
                chunk_metadata["chunk_index"] = len(chunks)
                chunks.append({
                    "content": chunk_text,
                    "metadata": chunk_metadata
                })
                
                # Keep overlap: carry the last `overlap` words into the next chunk
                overlap_words = chunk_text.split()[-self.overlap:]
                current_chunk = [' '.join(overlap_words)]
                current_length = len(overlap_words)
            
            current_chunk.append(paragraph)
            current_length += paragraph_length
        
        # Don't forget the last chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk_metadata = (metadata or {}).copy()
            chunk_metadata["chunk_index"] = len(chunks)
            chunks.append({
                "content": chunk_text,
                "metadata": chunk_metadata
            })
        
        return chunks
    
    def chunk_pages(self, pages: List[Dict]) -> List[Dict]:
        """Chunk content from parsed pages"""
        all_chunks = []
        for page in pages:
            chunks = self.chunk_text(
                page["content"], 
                metadata=page.get("metadata", {})
            )
            all_chunks.extend(chunks)
        return all_chunks