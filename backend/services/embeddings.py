import numpy as np
import faiss
import pickle
import os
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Dict
import config

class EmbeddingsService:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = 384
        self.index = None
        self.chunks = []
        self.chunk_metadata = []
        
        self.index_path = os.path.join(config.EMBEDDINGS_DIR, 'faiss_index.bin')
        self.chunks_path = os.path.join(config.EMBEDDINGS_DIR, 'chunks.pkl')
        self.metadata_path = os.path.join(config.EMBEDDINGS_DIR, 'metadata.pkl')
        
        self._load_or_create_index()
    
    def _load_or_create_index(self):
        if os.path.exists(self.index_path) and os.path.exists(self.chunks_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.chunks_path, 'rb') as f:
                    self.chunks = pickle.load(f)
                with open(self.metadata_path, 'rb') as f:
                    self.chunk_metadata = pickle.load(f)
                print(f"Loaded existing index with {len(self.chunks)} chunks")
            except Exception as e:
                print(f"Error loading index: {e}, creating new one")
                self._create_new_index()
        else:
            self._create_new_index()

    def _create_new_index(self):
        self.index = faiss.IndexFlatL2(self.dimension)
        self.chunks = []
        self.chunk_metadata = []
        print("Created new FAISS index")

    def add_document(self, text: str, filename: str, chunk_size: int = 1000, overlap: int = 200):
        from .file_parser import FileParser

        chunks = FileParser.chunk_text(text, chunk_size, overlap)

        if not chunks:
            print(f"No chunks created for {filename}")
            return

        embeddings = self.model.encode(chunks, convert_to_numpy=True)

        if embeddings.shape[1] != self.dimension:
            print(f"Dimension mismatch: expected {self.dimension}, got {embeddings.shape[1]}")
            return

        self.index.add(embeddings.astype('float32'))

        for i, chunk in enumerate(chunks):
            self.chunks.append(chunk)
            self.chunk_metadata.append({
                'filename': filename,
                'chunk_index': i,
                'total_chunks': len(chunks)
            })

        print(f"Added {len(chunks)} chunks from {filename}")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        if self.index.ntotal == 0:
            return []

        query_embedding = self.model.encode([query], convert_to_numpy=True)

        distances, indices = self.index.search(query_embedding.astype('float32'), min(top_k, self.index.ntotal))
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < len(self.chunks):
                results.append({
                    'text': self.chunks[idx],
                    'metadata': self.chunk_metadata[idx],
                    'score': float(dist)
                })
        
        return results
    
    def get_context(self, query: str, top_k: int = 5, max_length: int = 4000) -> str:
        results = self.search(query, top_k)
        
        if not results:
            return ""
        
        context_parts = []
        current_length = 0
        
        for result in results:
            text = result['text']
            metadata = result['metadata']

            chunk_text = f"[Документ: {metadata['filename']}]\n{text}\n"
            chunk_length = len(chunk_text)
            
            if current_length + chunk_length > max_length:
                break
            
            context_parts.append(chunk_text)
            current_length += chunk_length
        
        return "\n---\n".join(context_parts)
    
    def save_index(self):
        try:
            faiss.write_index(self.index, self.index_path)
            with open(self.chunks_path, 'wb') as f:
                pickle.dump(self.chunks, f)
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.chunk_metadata, f)
            print("Index saved successfully")
        except Exception as e:
            print(f"Error saving index: {e}")

    def rebuild_index(self):
        from backend.models import Document

        self._create_new_index()

        documents = Document.select()

        if not documents:
            print("No documents to index")
            return

        for doc in documents:
            if doc.content:
                try:
                    self.add_document(doc.content, doc.filename)
                except Exception as e:
                    print(f"Error indexing {doc.filename}: {e}")

        self.save_index()
        print(f"Rebuilt index with {self.index.ntotal} vectors")
    
    def get_stats(self) -> Dict:
        return {
            'total_chunks': len(self.chunks),
            'total_vectors': self.index.ntotal if self.index else 0,
            'dimension': self.dimension,
            'unique_documents': len(set(m['filename'] for m in self.chunk_metadata))
        }