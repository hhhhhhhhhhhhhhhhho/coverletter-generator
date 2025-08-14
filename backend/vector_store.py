import chromadb
from chromadb.config import Settings
import os
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import numpy as np
import json
from datetime import datetime

class VectorStore:
    def __init__(self, persist_directory: str = "chroma_db"):
        """
        ChromaDB 벡터 스토어를 초기화합니다.
        """
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        # ChromaDB 클라이언트 초기화
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # 컬렉션 초기화
        self.collections = {
            'pdf_documents': self._get_or_create_collection('pdf_documents'),
            'job_postings': self._get_or_create_collection('job_postings'),
            'cover_letters': self._get_or_create_collection('cover_letters')
        }
        
        # 임베딩 모델 초기화
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def _get_or_create_collection(self, name: str):
        """
        컬렉션을 가져오거나 생성합니다.
        """
        try:
            return self.client.get_collection(name=name)
        except:
            return self.client.create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
    
    def add_pdf_documents(self, documents: List[Dict[str, Any]]):
        """
        PDF 문서를 벡터 스토어에 추가합니다.
        """
        if not documents:
            return
        
        ids = []
        texts = []
        metadatas = []
        embeddings = []
        
        for doc in documents:
            doc_id = f"pdf_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(doc.get('filename', ''))}"
            ids.append(doc_id)
            texts.append(doc.get('text', ''))
            metadatas.append({
                'filename': doc.get('filename', ''),
                'pages': doc.get('pages', 0),
                'type': 'pdf_document',
                'created_at': datetime.now().isoformat()
            })
        
        # 임베딩 생성
        if texts:
            embeddings = self.embedding_model.encode(texts).tolist()
        
        # ChromaDB에 추가
        self.collections['pdf_documents'].add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings
        )
        
        return ids
    
    def add_job_posting(self, job_posting: Dict[str, Any]):
        """
        Job Posting을 벡터 스토어에 추가합니다.
        """
        job_id = job_posting.get('id', f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        # Job Posting 텍스트 구성
        text_parts = []
        if job_posting.get('jobTitle'):
            text_parts.append(f"Job Title: {job_posting['jobTitle']}")
        if job_posting.get('companyName'):
            text_parts.append(f"Company: {job_posting['companyName']}")
        if job_posting.get('jobDescription'):
            text_parts.append(f"Description: {job_posting['jobDescription']}")
        if job_posting.get('requirements'):
            text_parts.append(f"Requirements: {job_posting['requirements']}")
        if job_posting.get('companyVision'):
            text_parts.append(f"Company Vision: {job_posting['companyVision']}")
        
        text = "\n".join(text_parts)
        
        # 임베딩 생성
        embedding = self.embedding_model.encode([text]).tolist()[0]
        
        # ChromaDB에 추가
        self.collections['job_postings'].add(
            ids=[job_id],
            documents=[text],
            metadatas=[{
                'job_title': job_posting.get('jobTitle', ''),
                'company_name': job_posting.get('companyName', ''),
                'type': 'job_posting',
                'created_at': job_posting.get('createdAt', datetime.now().isoformat())
            }],
            embeddings=[embedding]
        )
        
        return job_id
    
    def search_similar_documents(self, query: str, collection_name: str = 'pdf_documents', n_results: int = 5):
        """
        쿼리와 유사한 문서를 검색합니다.
        """
        if collection_name not in self.collections:
            raise ValueError(f"Collection '{collection_name}' not found")
        
        # 쿼리 임베딩 생성
        query_embedding = self.embedding_model.encode([query]).tolist()[0]
        
        # 유사도 검색
        results = self.collections[collection_name].query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        return {
            'documents': results['documents'][0] if results['documents'] else [],
            'metadatas': results['metadatas'][0] if results['metadatas'] else [],
            'distances': results['distances'][0] if results['distances'] else [],
            'ids': results['ids'][0] if results['ids'] else []
        }
    
    def search_job_postings(self, query: str, n_results: int = 3):
        """
        Job Posting을 검색합니다.
        """
        return self.search_similar_documents(query, 'job_postings', n_results)
    
    def search_pdf_documents(self, query: str, n_results: int = 5):
        """
        PDF 문서를 검색합니다.
        """
        return self.search_similar_documents(query, 'pdf_documents', n_results)
    
    def get_collection_stats(self, collection_name: str = None):
        """
        컬렉션 통계를 반환합니다.
        """
        if collection_name:
            if collection_name not in self.collections:
                raise ValueError(f"Collection '{collection_name}' not found")
            collections = {collection_name: self.collections[collection_name]}
        else:
            collections = self.collections
        
        stats = {}
        for name, collection in collections.items():
            try:
                count = collection.count()
                stats[name] = {
                    'document_count': count,
                    'name': name
                }
            except Exception as e:
                stats[name] = {
                    'document_count': 0,
                    'name': name,
                    'error': str(e)
                }
        
        return stats
    
    def delete_collection(self, collection_name: str):
        """
        컬렉션을 삭제합니다.
        """
        if collection_name in self.collections:
            self.client.delete_collection(name=collection_name)
            del self.collections[collection_name]
            return True
        return False
    
    def reset_collection(self, collection_name: str):
        """
        컬렉션을 리셋합니다.
        """
        if collection_name in self.collections:
            self.delete_collection(collection_name)
            self.collections[collection_name] = self._get_or_create_collection(collection_name)
            return True
        return False

# 전역 벡터 스토어 인스턴스
vector_store = None

def get_vector_store():
    """
    전역 벡터 스토어 인스턴스를 반환합니다.
    """
    global vector_store
    if vector_store is None:
        vector_store = VectorStore()
    return vector_store 