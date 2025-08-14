from typing import List, Dict, Any, Optional
from retrieval import get_retrieval_component
from llm_integration import get_llm_integration
import json
from datetime import datetime

class CoverLetterPipeline:
    def __init__(self):
        """
        Cover Letter 생성 파이프라인을 초기화합니다.
        """
        self.retrieval = get_retrieval_component()
        self.llm = get_llm_integration()
    
    def generate_cover_letter(
        self,
        job_title: str,
        company_name: str,
        user_question: str = None,
        user_background: str = None,
        include_variations: bool = False,
        num_variations: int = 3
    ) -> Dict[str, Any]:
        """
        Cover Letter를 생성하는 메인 파이프라인입니다.
        """
        try:
            # 1단계: 관련 컨텍스트 검색
            context = self.retrieval.retrieve_context_for_cover_letter(
                job_title=job_title,
                company_name=company_name,
                user_question=user_question
            )
            
            # 2단계: Job Posting 정보 추출
            job_description = self._extract_job_description(context['job_postings'])
            
            # 3단계: 관련 컨텍스트 결합
            relevant_context = self._combine_context(context)
            
            # 4단계: Cover Letter 생성
            if include_variations:
                result = self.llm.generate_cover_letter_variations(
                    job_title=job_title,
                    company_name=company_name,
                    job_description=job_description,
                    user_question=user_question,
                    relevant_context=relevant_context,
                    user_background=user_background,
                    num_variations=num_variations
                )
            else:
                result = self.llm.generate_cover_letter(
                    job_title=job_title,
                    company_name=company_name,
                    job_description=job_description,
                    user_question=user_question,
                    relevant_context=relevant_context,
                    user_background=user_background
                )
            
            # 5단계: 결과에 컨텍스트 정보 추가
            result['context_info'] = {
                'job_postings_found': len(context['job_postings']),
                'pdf_documents_found': len(context['pdf_documents']),
                'avg_job_similarity': context['summary']['avg_job_similarity'],
                'avg_pdf_similarity': context['summary']['avg_pdf_similarity']
            }
            
            result['pipeline_info'] = {
                'generated_at': datetime.now().isoformat(),
                'pipeline_version': '1.0',
                'components_used': ['retrieval', 'llm_integration']
            }
            
            return result
        
        except Exception as e:
            raise Exception(f"Cover Letter 파이프라인 실행 실패: {str(e)}")
    
    def _extract_job_description(self, job_postings: List[Dict[str, Any]]) -> str:
        """
        Job Posting에서 직무 설명을 추출합니다.
        """
        if not job_postings:
            return "직무 설명이 제공되지 않았습니다."
        
        # 가장 관련성 높은 Job Posting 선택
        best_job = max(job_postings, key=lambda x: x.get('similarity_score', 0))
        
        # Job Posting 내용에서 직무 설명 부분 추출
        content = best_job.get('content', '')
        
        # "Description:" 부분이 있으면 추출
        if 'Description:' in content:
            desc_start = content.find('Description:') + len('Description:')
            desc_end = content.find('\n', desc_start)
            if desc_end == -1:
                desc_end = len(content)
            return content[desc_start:desc_end].strip()
        
        return content
    
    def _combine_context(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        검색된 컨텍스트를 결합합니다.
        """
        combined = []
        
        # Job Posting 정보 추가
        for job in context['job_postings']:
            combined.append({
                'type': 'job_posting',
                'content': job['content'],
                'similarity_score': job['similarity_score'],
                'metadata': job['metadata']
            })
        
        # PDF 문서 정보 추가
        for doc in context['pdf_documents']:
            combined.append({
                'type': 'pdf_document',
                'content': doc['content'],
                'similarity_score': doc['similarity_score'],
                'metadata': doc['metadata']
            })
        
        # 유사도 점수로 정렬
        combined.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return combined[:5]  # 상위 5개만 반환
    
    def analyze_and_generate(
        self,
        job_title: str,
        company_name: str,
        job_description: str,
        user_question: str = None,
        user_background: str = None
    ) -> Dict[str, Any]:
        """
        Job Posting을 분석하고 Cover Letter를 생성합니다.
        """
        try:
            # 1단계: Job Posting 분석
            analysis = self.llm.analyze_job_posting(job_description)
            
            # 2단계: 관련 컨텍스트 검색
            context = self.retrieval.retrieve_context_for_cover_letter(
                job_title=job_title,
                company_name=company_name,
                user_question=user_question
            )
            
            # 3단계: 관련 컨텍스트 결합
            relevant_context = self._combine_context(context)
            
            # 4단계: Cover Letter 생성
            result = self.llm.generate_cover_letter(
                job_title=job_title,
                company_name=company_name,
                job_description=job_description,
                user_question=user_question,
                relevant_context=relevant_context,
                user_background=user_background
            )
            
            # 5단계: 결과에 분석 정보 추가
            result['job_analysis'] = analysis['analysis']
            result['context_info'] = {
                'job_postings_found': len(context['job_postings']),
                'pdf_documents_found': len(context['pdf_documents']),
                'avg_job_similarity': context['summary']['avg_job_similarity'],
                'avg_pdf_similarity': context['summary']['avg_pdf_similarity']
            }
            
            return result
        
        except Exception as e:
            raise Exception(f"분석 및 생성 파이프라인 실행 실패: {str(e)}")
    
    def batch_generate_cover_letters(
        self,
        requests: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        여러 Cover Letter를 일괄 생성합니다.
        """
        try:
            results = []
            
            for i, request in enumerate(requests):
                try:
                    result = self.generate_cover_letter(
                        job_title=request['job_title'],
                        company_name=request['company_name'],
                        user_question=request.get('user_question'),
                        user_background=request.get('user_background'),
                        include_variations=request.get('include_variations', False),
                        num_variations=request.get('num_variations', 3)
                    )
                    
                    result['request_index'] = i
                    result['request_info'] = request
                    results.append(result)
                
                except Exception as e:
                    # 개별 요청 실패 시 에러 정보 포함
                    results.append({
                        'request_index': i,
                        'request_info': request,
                        'error': str(e),
                        'status': 'failed'
                    })
            
            return {
                'batch_results': results,
                'total_requests': len(requests),
                'successful': len([r for r in results if r.get('status') != 'failed']),
                'failed': len([r for r in results if r.get('status') == 'failed']),
                'batch_completed_at': datetime.now().isoformat()
            }
        
        except Exception as e:
            raise Exception(f"일괄 생성 파이프라인 실행 실패: {str(e)}")
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """
        파이프라인 통계를 반환합니다.
        """
        try:
            retrieval_stats = self.retrieval.get_retrieval_stats()
            
            return {
                'pipeline_info': {
                    'name': 'Cover Letter Generation Pipeline',
                    'version': '1.0',
                    'components': ['retrieval', 'llm_integration'],
                    'last_updated': datetime.now().isoformat()
                },
                'retrieval_stats': retrieval_stats,
                'llm_info': {
                    'model': self.llm.model_name,
                    'temperature': self.llm.temperature
                }
            }
        
        except Exception as e:
            raise Exception(f"파이프라인 통계 조회 실패: {str(e)}")

# 전역 파이프라인 인스턴스
cover_letter_pipeline = None

def get_cover_letter_pipeline():
    """
    전역 Cover Letter 파이프라인 인스턴스를 반환합니다.
    """
    global cover_letter_pipeline
    if cover_letter_pipeline is None:
        cover_letter_pipeline = CoverLetterPipeline()
    return cover_letter_pipeline 