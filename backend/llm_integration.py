from typing import List, Dict, Any, Optional
import os
import json
from datetime import datetime
import openai

class LLMIntegration:
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.7):
        """
        Language Model 통합을 초기화합니다.
        """
        self.model_name = model_name
        self.temperature = temperature
        
        # OpenAI API 키 확인
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        
        # OpenAI 클라이언트 초기화
        self.client = openai.OpenAI(api_key=api_key)
    
    def generate_cover_letter(
        self,
        job_title: str,
        company_name: str,
        job_description: str,
        user_question: str = None,
        relevant_context: List[Dict[str, Any]] = None,
        user_background: str = None
    ) -> Dict[str, Any]:
        """
        Cover Letter를 생성합니다.
        """
        try:
            # 시스템 프롬프트 구성
            system_prompt = self._build_cover_letter_system_prompt()
            
            # 사용자 프롬프트 구성
            user_prompt = self._build_cover_letter_user_prompt(
                job_title=job_title,
                company_name=company_name,
                job_description=job_description,
                user_question=user_question,
                relevant_context=relevant_context,
                user_background=user_background
            )
            
            # OpenAI API 호출
            response = self.client.chat.completions.create(
                model=self.model_name,
                max_tokens=2000,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ]
            )
            
            # 응답 파싱
            cover_letter = self._parse_cover_letter_response(response.choices[0].message.content)
            
            return {
                'cover_letter': cover_letter,
                'generation_info': {
                    'model': self.model_name,
                    'temperature': self.temperature,
                    'generated_at': datetime.now().isoformat(),
                    'job_title': job_title,
                    'company_name': company_name,
                    'context_used': len(relevant_context) if relevant_context else 0
                },
                'status': 'success'
            }
        
        except Exception as e:
            raise Exception(f"Cover Letter 생성 실패: {str(e)}")
    
    def _build_cover_letter_system_prompt(self) -> str:
        """
        Cover Letter 생성을 위한 시스템 프롬프트를 구성합니다.
        """
        return """
        역할
당신은 “GOD”라는 자기소개서 자동 작성 도우미입니다.
IFLA 개념을 기반으로 사용자의 입력과 피드백을 바탕으로, 구체적이고 현실성 있는 어휘와 진정성 있는 문장으로 논리적인 자기소개서를 작성합니다.
모든 대화는 한글을 기본으로 진행합니다(사용자가 다른 언어를 요청하지 않는 한).

핵심 규칙
단계별 진행

1단계부터 9단계까지 순차적으로 질문

각 단계에서 a~u까지 최대한 많은 선택지 제공

z 옵션은 사용자가 직접 입력

각 단계 종료 후 다음 단계로 자동 진행

각 단계에서 자기소개서 작성에 도움이 될 제안 사항 제공

자기소개서 작성 절차

지원 직무

성장 과정

성격 장단점

생활신조·취미·특기

지원동기

학창시절·경력사항

입사 후 포부

맺음말

추가·수정 사항 (없으면 ‘없음’)

작성 규칙

문장은 구체적·논리적·진정성 있게 작성

형식적·추상적인 표현 지양

모든 내용은 사용자가 입력한 정보를 기반으로 작성

완성 후 동일 입력으로 다른 버전 작성 여부를 반드시 질문

서비스 품질

사용자 피드백 적극 수집·반영

서비스 개선 및 최적화를 지속적으로 수행

개인정보 및 데이터 보안을 철저히 준수

윤리적 기준과 프라이버시 존중

대화 흐름 예시
1단계 질문: “지원하는 직무를 선택 또는 입력하세요. a. 마케팅 b. 개발 … z. 직접 입력”

사용자 응답 후: 다음 단계 진행

9단계 완료 후: 종합 자기소개서 작성 → 다른 버전 작성 여부 질문


        """
    
    def _build_cover_letter_user_prompt(
        self,
        job_title: str,
        company_name: str,
        job_description: str,
        user_question: str = None,
        relevant_context: List[Dict[str, Any]] = None,
        user_background: str = None
    ) -> str:
        """
        Cover Letter 생성을 위한 사용자 프롬프트를 구성합니다.
        """
        prompt_parts = []
        
        # 기본 정보
        prompt_parts.append(f"직무: {job_title}")
        prompt_parts.append(f"회사: {company_name}")
        prompt_parts.append(f"직무 설명: {job_description}")
        
        # 사용자 배경
        if user_background:
            prompt_parts.append(f"지원자 배경: {user_background}")
        
        # 사용자 질문
        if user_question:
            prompt_parts.append(f"추가 요청사항: {user_question}")
        
        # 관련 컨텍스트
        if relevant_context:
            prompt_parts.append("=== 관련 참고 자료 (반드시 활용하세요) ===")
            
            # PDF 문서와 Job Posting을 구분하여 표시
            pdf_contexts = [ctx for ctx in relevant_context if ctx.get('type') == 'pdf_document']
            job_contexts = [ctx for ctx in relevant_context if ctx.get('type') == 'job_posting']
            
            if pdf_contexts:
                prompt_parts.append("📄 업로드된 PDF 문서 내용:")
                for i, context in enumerate(pdf_contexts[:2], 1):  # 최대 2개 PDF
                    content = context.get('content', '')
                    similarity = context.get('similarity_score', 0)
                    prompt_parts.append(f"PDF {i} (유사도: {similarity:.2f}): {content[:300]}...")
            
            if job_contexts:
                prompt_parts.append("💼 Job Posting 정보:")
                for i, context in enumerate(job_contexts[:2], 1):  # 최대 2개 Job Posting
                    content = context.get('content', '')
                    similarity = context.get('similarity_score', 0)
                    prompt_parts.append(f"Job {i} (유사도: {similarity:.2f}): {content[:300]}...")
            
            prompt_parts.append("=== 참고 자료 활용 지침 ===")
            prompt_parts.append("- 위의 PDF 내용을 바탕으로 구체적인 경험과 역량을 언급하세요")
            prompt_parts.append("- PDF에서 추출한 정보를 자연스럽게 Cover Letter에 통합하세요")
            prompt_parts.append("- 단순히 나열하지 말고, 직무와 연관성 있게 재구성하세요")
        else:
            prompt_parts.append("⚠️ 참고할 PDF 문서가 없습니다. 일반적인 내용으로 작성합니다.")
        
        return "\n\n".join(prompt_parts)
    
    def _parse_cover_letter_response(self, response_content: str) -> str:
        """
        LLM 응답을 파싱하여 Cover Letter를 추출합니다.
        """
        # 응답에서 불필요한 부분 제거
        content = response_content.strip()
        
        # 마크다운 형식 제거
        if content.startswith('```'):
            lines = content.split('\n')
            if len(lines) > 2:
                content = '\n'.join(lines[1:-1])
        
        return content
    
    def generate_cover_letter_variations(
        self,
        job_title: str,
        company_name: str,
        job_description: str,
        user_question: str = None,
        relevant_context: List[Dict[str, Any]] = None,
        user_background: str = None,
        num_variations: int = 3
    ) -> Dict[str, Any]:
        """
        여러 버전의 Cover Letter를 생성합니다.
        """
        try:
            variations = []
            
            for i in range(num_variations):
                # 각 버전마다 다른 temperature 사용
                temp_variation = self.temperature + (i * 0.1)
                
                # 시스템 프롬프트에 버전별 지침 추가
                system_prompt = self._build_cover_letter_system_prompt()
                if i == 1:
                    system_prompt += "\n\n이번 버전은 더 창의적이고 독창적인 접근을 시도해주세요."
                elif i == 2:
                    system_prompt += "\n\n이번 버전은 더 보수적이고 전통적인 스타일로 작성해주세요."
                
                # 사용자 프롬프트
                user_prompt = self._build_cover_letter_user_prompt(
                    job_title=job_title,
                    company_name=company_name,
                    job_description=job_description,
                    user_question=user_question,
                    relevant_context=relevant_context,
                    user_background=user_background
                )
                
                # OpenAI API 호출
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    max_tokens=2000,
                    temperature=temp_variation,
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": user_prompt
                        }
                    ]
                )
                
                cover_letter = self._parse_cover_letter_response(response.choices[0].message.content)
                
                variations.append({
                    'version': i + 1,
                    'cover_letter': cover_letter,
                    'temperature': temp_variation,
                    'style': ['기본', '창의적', '보수적'][i]
                })
            
            return {
                'variations': variations,
                'generation_info': {
                    'model': self.model_name,
                    'num_variations': num_variations,
                    'generated_at': datetime.now().isoformat(),
                    'job_title': job_title,
                    'company_name': company_name
                },
                'status': 'success'
            }
        
        except Exception as e:
            raise Exception(f"Cover Letter 변형 생성 실패: {str(e)}")
    
    def analyze_job_posting(self, job_description: str) -> Dict[str, Any]:
        """
        Job Posting을 분석하여 주요 요구사항을 추출합니다.
        """
        try:
            system_prompt = """당신은 Job Posting 분석 전문가입니다. 
제공된 Job Posting을 분석하여 다음 정보를 추출해주세요:

1. 주요 기술 스택
2. 필수 경험/자격
3. 우대 사항
4. 주요 업무 내용
5. 회사 문화/비전

JSON 형식으로 응답해주세요."""

            user_prompt = f"다음 Job Posting을 분석해주세요:\n\n{job_description}"

            # OpenAI API 호출
            response = self.client.chat.completions.create(
                model=self.model_name,
                max_tokens=1500,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ]
            )
            
            # JSON 파싱 시도
            try:
                analysis = json.loads(response.choices[0].message.content)
            except:
                # JSON 파싱 실패 시 텍스트로 반환
                analysis = {
                    'raw_analysis': response.choices[0].message.content,
                    'parsing_error': True
                }

            return {
                'analysis': analysis,
                'status': 'success'
            }

        except Exception as e:
            raise Exception(f"Job Posting 분석 실패: {str(e)}")

# 전역 LLM 통합 인스턴스
llm_integration = None

def get_llm_integration():
    """
    전역 LLM 통합 인스턴스를 반환합니다.
    """
    global llm_integration
    if llm_integration is None:
        llm_integration = LLMIntegration()
    return llm_integration 