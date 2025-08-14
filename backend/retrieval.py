from typing import List, Dict, Any, Optional
from vector_store import get_vector_store
import json
from datetime import datetime

class InformationRetrieval:
    def __init__(self):
        """
        정보 검색 컴포넌트를 초기화합니다.
        """
        self.vector_store = get_vector_store()
    
    def retrieve_relevant_job_postings(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """
        쿼리와 관련된 Job Posting을 검색합니다.
        """
        try:
            results = self.vector_store.search_job_postings(query, n_results)
            
            relevant_postings = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'], 
                results['metadatas'], 
                results['distances']
            )):
                relevant_postings.append({
                    'id': results['ids'][i],
                    'content': doc,
                    'metadata': metadata,
                    'similarity_score': 1 - distance,  # 거리를 유사도 점수로 변환
                    'rank': i + 1
                })
            
            return relevant_postings
        
        except Exception as e:
            raise Exception(f"Job Posting 검색 실패: {str(e)}")
    
    def retrieve_relevant_pdf_documents(self, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
        """
        쿼리와 관련된 PDF 문서를 검색합니다.
        """
        try:
            results = self.vector_store.search_pdf_documents(query, n_results)
            
            relevant_documents = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'], 
                results['metadatas'], 
                results['distances']
            )):
                relevant_documents.append({
                    'id': results['ids'][i],
                    'content': doc,
                    'metadata': metadata,
                    'similarity_score': 1 - distance,
                    'rank': i + 1
                })
            
            return relevant_documents
        
        except Exception as e:
            raise Exception(f"PDF 문서 검색 실패: {str(e)}")
    
    def retrieve_context_for_cover_letter(
        self, 
        job_title: str, 
        company_name: str, 
        user_question: str = None,
        max_job_results: int = 2,
        max_pdf_results: int = 3
    ) -> Dict[str, Any]:
        """
        Cover Letter 생성을 위한 컨텍스트를 검색합니다.
        """
        try:
            # Job Posting 검색
            job_query = f"{job_title} {company_name}"
            relevant_jobs = self.retrieve_relevant_job_postings(job_query, max_job_results)
            
            # PDF 문서 검색 - 더 적극적으로 검색
            relevant_pdfs = []
            
            # 1. 사용자 질문이 있는 경우 해당 질문으로 검색
            if user_question:
                pdfs_from_question = self.retrieve_relevant_pdf_documents(user_question, max_pdf_results)
                relevant_pdfs.extend(pdfs_from_question)
            
            # 2. 직무 제목으로도 검색 (중복 제거)
            pdfs_from_job = self.retrieve_relevant_pdf_documents(job_title, max_pdf_results)
            for pdf in pdfs_from_job:
                if not any(existing['id'] == pdf['id'] for existing in relevant_pdfs):
                    relevant_pdfs.append(pdf)
            
            # 3. 회사명으로도 검색 (중복 제거)
            pdfs_from_company = self.retrieve_relevant_pdf_documents(company_name, max_pdf_results)
            for pdf in pdfs_from_company:
                if not any(existing['id'] == pdf['id'] for existing in relevant_pdfs):
                    relevant_pdfs.append(pdf)
            
            # 4. 일반적인 키워드로 검색 (경험, 프로젝트, 기술 등)
            general_keywords = ["경험", "프로젝트", "기술", "개발", "관리", "분석", "설계", "구현"]
            for keyword in general_keywords:
                if len(relevant_pdfs) < max_pdf_results * 2:  # 너무 많이 가져오지 않도록 제한
                    pdfs_from_keyword = self.retrieve_relevant_pdf_documents(keyword, 1)
                    for pdf in pdfs_from_keyword:
                        if not any(existing['id'] == pdf['id'] for existing in relevant_pdfs):
                            relevant_pdfs.append(pdf)
            
            # 유사도 점수로 정렬하고 상위 결과만 선택
            relevant_pdfs.sort(key=lambda x: x['similarity_score'], reverse=True)
            relevant_pdfs = relevant_pdfs[:max_pdf_results]
            
            # 컨텍스트 구성
            context = {
                'job_postings': relevant_jobs,
                'pdf_documents': relevant_pdfs,
                'query_info': {
                    'job_title': job_title,
                    'company_name': company_name,
                    'user_question': user_question,
                    'retrieved_at': datetime.now().isoformat(),
                    'search_strategy': 'multi_query_enhanced'
                },
                'summary': {
                    'total_job_postings': len(relevant_jobs),
                    'total_pdf_documents': len(relevant_pdfs),
                    'avg_job_similarity': sum(job['similarity_score'] for job in relevant_jobs) / len(relevant_jobs) if relevant_jobs else 0,
                    'avg_pdf_similarity': sum(doc['similarity_score'] for doc in relevant_pdfs) / len(relevant_pdfs) if relevant_pdfs else 0
                }
            }
            
            return context
        
        except Exception as e:
            raise Exception(f"컨텍스트 검색 실패: {str(e)}")
    
    def search_across_all_collections(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """
        모든 컬렉션에서 검색을 수행합니다.
        """
        try:
            results = {
                'job_postings': self.retrieve_relevant_job_postings(query, n_results),
                'pdf_documents': self.retrieve_relevant_pdf_documents(query, n_results),
                'query': query,
                'total_results': 0
            }
            
            results['total_results'] = len(results['job_postings']) + len(results['pdf_documents'])
            
            return results
        
        except Exception as e:
            raise Exception(f"전체 검색 실패: {str(e)}")
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """
        검색 통계를 반환합니다.
        """
        try:
            stats = self.vector_store.get_collection_stats()
            
            return {
                'collections': stats,
                'total_documents': sum(stat.get('document_count', 0) for stat in stats.values()),
                'available_collections': list(stats.keys())
            }
        
        except Exception as e:
            raise Exception(f"검색 통계 조회 실패: {str(e)}")

# 전역 검색 컴포넌트 인스턴스
retrieval_component = None

def get_retrieval_component():
    """
    전역 검색 컴포넌트 인스턴스를 반환합니다.
    """
    global retrieval_component
    if retrieval_component is None:
        retrieval_component = InformationRetrieval()
    return retrieval_component 