"""
Vector Memory - Semantic search and embeddings
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
import json
import os
import pickle
from datetime import datetime
import numpy as np

class VectorMemory:
    def __init__(self, config: Dict):
        self.config = config
        self.storage_path = config.get('vector_storage_path', 'vector_memory.pkl')
        self.embeddings = {}  # id -> embedding vector
        self.metadata = {}    # id -> metadata
        self.documents = {}   # id -> text
        self.initialized = False
        self.use_gemini_embeddings = config.get('use_gemini_embeddings', True)
    
    async def initialize(self):
        """Initialize vector memory"""
        # Load existing data if available
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'rb') as f:
                    data = pickle.load(f)
                    self.embeddings = data.get('embeddings', {})
                    self.metadata = data.get('metadata', {})
                    self.documents = data.get('documents', {})
                print(f"Vector Memory loaded: {len(self.documents)} documents")
            except Exception as e:
                print(f"Error loading vector memory: {e}")
        
        self.initialized = True
    
    async def add_text(self, text: str, metadata: Dict = None) -> str:
        """Add text with vector embedding"""
        import hashlib
        
        # Generate ID
        doc_id = hashlib.md5(f"{text}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        # Generate embedding (simplified - uses TF-IDF like approach)
        embedding = await self._generate_embedding(text)
        
        self.embeddings[doc_id] = embedding
        self.documents[doc_id] = text
        self.metadata[doc_id] = metadata or {}
        
        # Save periodically
        await self._save()
        
        return doc_id
    
    async def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate text embedding"""
        try:
            # Try to use Gemini embeddings
            if self.use_gemini_embeddings:
                try:
                    import google.generativeai as genai
                    result = await asyncio.to_thread(
                        genai.embed_content,
                        model="models/embedding-001",
                        content=text,
                        task_type="retrieval_document"
                    )
                    return np.array(result['embedding'])
                except:
                    pass
            
            # Fallback: simple TF-IDF-like vectorization
            words = text.lower().split()
            word_freq = {}
            
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # Create simple 100-dimensional vector using hash
            vector = np.zeros(100)
            for word, freq in word_freq.items():
                idx = hash(word) % 100
                vector[idx] += freq
            
            # Normalize
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
            
            return vector
            
        except Exception as e:
            print(f"Embedding generation error: {e}")
            return np.random.randn(100) * 0.01  # Random small vector as fallback
    
    async def search_similar(self, query: str, filter_type: str = None, top_k: int = 5) -> List[Dict]:
        """Search for similar documents"""
        if not self.documents:
            return []
        
        # Generate query embedding
        query_embedding = await self._generate_embedding(query)
        
        # Calculate similarities
        similarities = []
        
        for doc_id, embedding in self.embeddings.items():
            # Filter by type if specified
            if filter_type and self.metadata.get(doc_id, {}).get('type') != filter_type:
                continue
            
            # Cosine similarity
            similarity = np.dot(query_embedding, embedding)
            similarities.append((doc_id, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top results
        results = []
        for doc_id, score in similarities[:top_k]:
            if score > 0.1:  # Minimum similarity threshold
                results.append({
                    'id': doc_id,
                    'text': self.documents[doc_id][:200],
                    'metadata': self.metadata.get(doc_id, {}),
                    'score': float(score)
                })
        
        return results
    
    async def get_by_id(self, doc_id: str) -> Optional[Dict]:
        """Get document by ID"""
        if doc_id in self.documents:
            return {
                'id': doc_id,
                'text': self.documents[doc_id],
                'metadata': self.metadata.get(doc_id, {})
            }
        return None
    
    async def delete(self, doc_id: str) -> bool:
        """Delete a document"""
        if doc_id in self.documents:
            del self.embeddings[doc_id]
            del self.documents[doc_id]
            if doc_id in self.metadata:
                del self.metadata[doc_id]
            await self._save()
            return True
        return False
    
    async def update_metadata(self, doc_id: str, metadata: Dict) -> bool:
        """Update document metadata"""
        if doc_id in self.documents:
            self.metadata[doc_id] = metadata
            await self._save()
            return True
        return False
    
    async def get_stats(self) -> Dict:
        """Get vector memory statistics"""
        return {
            "total_documents": len(self.documents),
            "total_embeddings": len(self.embeddings),
            "storage_path": self.storage_path,
            "using_gemini": self.use_gemini_embeddings
        }
    
    async def _save(self):
        """Save to disk"""
        try:
            data = {
                'embeddings': self.embeddings,
                'metadata': self.metadata,
                'documents': self.documents
            }
            
            with open(self.storage_path, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            print(f"Error saving vector memory: {e}")
    
    async def clear(self):
        """Clear all vector memory"""
        self.embeddings.clear()
        self.metadata.clear()
        self.documents.clear()
        
        if os.path.exists(self.storage_path):
            os.remove(self.storage_path)
    
    async def shutdown(self):
        """Cleanup and save"""
        await self._save()
        self.initialized = False
