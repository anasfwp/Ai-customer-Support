from typing import List, Dict

class Chunker:
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """Split text into overlapping chunks"""
        if not text or not text.strip():
            return []
        
        words = text.split()
        if len(words) <= self.chunk_size:
            return [{
                "content": text,
                "metadata": metadata or {}
            }]
        
        chunks = []
        for i in range(0, len(words), self.chunk_size - self.overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = " ".join(chunk_words)
            
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata["chunk_index"] = len(chunks)
            
            chunks.append({
                "content": chunk_text,
                "metadata": chunk_metadata
            })
            
            if i + self.chunk_size >= len(words):
                break
        
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