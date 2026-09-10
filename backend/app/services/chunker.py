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
        text = re.sub(r'\s+', ' ', text)   # Normalize whitespace
        
        # Try to split by paragraphs first (better semantic chunks)
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        
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
                
                # Keep overlap: keep last few sentences
                overlap_text = current_chunk[-1] if current_chunk else ""
                current_chunk = [overlap_text] if overlap_text else []
                current_length = len(overlap_text.split()) if overlap_text else 0
            
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