from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import fitz  # PyMuPDF
import pdfplumber
import os
import tempfile
import json
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import numpy as np
from pydantic import BaseModel
from datetime import datetime
import uuid
from vector_store import get_vector_store
from cover_letter_pipeline import get_cover_letter_pipeline
from cover_letter_models import (
    CoverLetterVersion, 
    CoverLetterSection, 
    CoverLetterEditRequest, 
    CoverLetterSaveRequest as CLSaveRequest, 
    CoverLetterResponse,
    SectionVersionRequest,
    RevertSectionRequest,
    cover_letter_manager
)


# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="LangChain Test API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React 개발 서버
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 업로드된 파일을 저장할 디렉토리
UPLOAD_DIR = "uploads"
JOB_POSTINGS_DIR = "job_postings"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(JOB_POSTINGS_DIR, exist_ok=True)

# 임베딩 모델 초기화 (한 번만 로드)
embedding_model = None

def get_embedding_model():
    global embedding_model
    if embedding_model is None:
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    return embedding_model

# Pydantic 모델
class JobPosting(BaseModel):
    jobTitle: str
    companyName: str
    jobDescription: Optional[str] = None
    requirements: Optional[str] = None
    companyVision: Optional[str] = None

class JobPostingResponse(BaseModel):
    id: str
    jobTitle: str
    companyName: str
    jobDescription: Optional[str] = None
    requirements: Optional[str] = None
    companyVision: Optional[str] = None
    createdAt: str
    status: str

class CoverLetterRequest(BaseModel):
    job_title: str
    company_name: str
    user_question: Optional[str] = None
    user_background: Optional[str] = None
    include_variations: bool = False
    num_variations: int = 3

@app.get("/")
async def root():
    return {"message": "Hello World from FastAPI"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/vector-store/stats")
async def get_vector_store_stats():
    """
    벡터 스토어 통계를 반환합니다.
    """
    try:
        vector_store = get_vector_store()
        stats = vector_store.get_collection_stats()
        return {
            "status": "success",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"벡터 스토어 통계 조회 실패: {str(e)}")

@app.post("/generate-cover-letter")
@app.post("/api/generate-cover-letter")
async def generate_cover_letter(request: dict):
    """
    Cover Letter를 생성합니다.
    프론트엔드에서 job_posting 필드로 전송하는 경우를 처리합니다.
    """
    try:
        # 프론트엔드에서 job_posting으로 전송하는 경우 처리
        if 'job_posting' in request:
            job_posting = request['job_posting']
            lines = job_posting.split('\n')
            job_title = lines[0] if lines else 'Unknown Position'
            company_name = lines[1] if len(lines) > 1 else 'Unknown Company'
        else:
            # 기존 CoverLetterRequest 형식 처리
            job_title = request.get('job_title', 'Unknown Position')
            company_name = request.get('company_name', 'Unknown Company')
        
        pipeline = get_cover_letter_pipeline()
        
        result = pipeline.generate_cover_letter(
            job_title=job_title,
            company_name=company_name,
            user_question=request.get('user_question'),
            user_background=request.get('user_background'),
            include_variations=request.get('include_variations', False),
            num_variations=request.get('num_variations', 3)
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cover Letter 생성 실패: {str(e)}")

@app.post("/analyze-job-posting")
async def analyze_job_posting(job_description: str):
    """
    Job Posting을 분석합니다.
    """
    try:
        from llm_integration import get_llm_integration
        llm = get_llm_integration()
        
        result = llm.analyze_job_posting(job_description)
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job Posting 분석 실패: {str(e)}")

@app.get("/pipeline/stats")
async def get_pipeline_stats():
    """
    파이프라인 통계를 반환합니다.
    """
    try:
        pipeline = get_cover_letter_pipeline()
        stats = pipeline.get_pipeline_stats()
        return stats
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파이프라인 통계 조회 실패: {str(e)}")

@app.post("/upload-pdf")
@app.post("/api/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """
    PDF 파일을 업로드하고 텍스트를 추출합니다.
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드 가능합니다.")
    
    temp_file_path = None
    try:
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', dir=UPLOAD_DIR) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # PDF 파싱
        extracted_text = await parse_pdf(temp_file_path)
        
        if not extracted_text or not any(text.strip() for text in extracted_text):
            raise HTTPException(status_code=400, detail="PDF에서 텍스트를 추출할 수 없습니다.")
        
        # 텍스트를 임베딩으로 변환
        embeddings = await generate_embeddings(extracted_text)
        
        # 벡터 스토어에 저장
        vector_store = get_vector_store()
        documents = []
        for i, text in enumerate(extracted_text):
            if text.strip():  # 빈 텍스트는 제외
                documents.append({
                    'filename': file.filename,
                    'text': text,
                    'pages': len(extracted_text),
                    'page_number': i + 1
                })
        
        vector_ids = []
        if documents:
            vector_ids = vector_store.add_pdf_documents(documents)
        
        # 임시 파일 삭제
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        
        return {
            "filename": file.filename,
            "text": extracted_text,
            "pages": len(extracted_text),
            "embeddings": embeddings,
            "embedding_dimension": len(embeddings[0]) if embeddings else 0,
            "vector_ids": vector_ids,
            "status": "success"
        }
    
    except HTTPException:
        # HTTPException은 그대로 재발생
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        raise
    except Exception as e:
        # 임시 파일 정리
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        raise HTTPException(status_code=500, detail=f"PDF 파싱 중 오류가 발생했습니다: {str(e)}")

@app.post("/submit-job-posting")
async def submit_job_posting(job_posting: JobPosting):
    """
    텍스트로 입력된 Job Posting을 저장합니다.
    """
    try:
        # 고유 ID 생성
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(job_posting.jobTitle)}"
        
        # Job Posting 데이터 준비
        job_data = {
            "id": job_id,
            "jobTitle": job_posting.jobTitle,
            "companyName": job_posting.companyName,
            "jobDescription": job_posting.jobDescription,
            "requirements": job_posting.requirements,
            "companyVision": job_posting.companyVision,
            "createdAt": datetime.now().isoformat(),
            "status": "active"
        }
        
        # 파일로 저장
        file_path = os.path.join(JOB_POSTINGS_DIR, f"{job_id}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(job_data, f, ensure_ascii=False, indent=2)
        
        # 벡터 스토어에 저장
        vector_store = get_vector_store()
        vector_store.add_job_posting(job_data)
        
        return JobPostingResponse(**job_data)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job Posting 저장 중 오류가 발생했습니다: {str(e)}")

@app.post("/upload-job-posting")
async def upload_job_posting(
    file: UploadFile = File(...),
    jobTitle: str = Form(...),
    companyName: str = Form(...)
):
    """
    파일로 업로드된 Job Posting을 처리합니다.
    """
    try:
        # 파일 확장자 확인
        if not (file.filename.endswith('.txt') or file.filename.endswith('.pdf')):
            raise HTTPException(status_code=400, detail="텍스트 파일(.txt) 또는 PDF 파일만 업로드 가능합니다.")
        
        # 고유 ID 생성
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(jobTitle)}"
        
        # 파일 내용 추출
        content = await file.read()
        
        if file.filename.endswith('.txt'):
            # 텍스트 파일 처리
            text_content = content.decode('utf-8')
        else:
            # PDF 파일 처리
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', dir=UPLOAD_DIR) as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            extracted_text = await parse_pdf(temp_file_path)
            text_content = "\n".join(extracted_text)
            
            # 임시 파일 삭제
            os.unlink(temp_file_path)
        
        # Job Posting 데이터 준비
        job_data = {
            "id": job_id,
            "jobTitle": jobTitle,
            "companyName": companyName,
            "jobDescription": text_content,
            "requirements": None,
            "companyVision": None,
            "createdAt": datetime.now().isoformat(),
            "status": "active",
            "sourceFile": file.filename
        }
        
        # 파일로 저장
        file_path = os.path.join(JOB_POSTINGS_DIR, f"{job_id}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(job_data, f, ensure_ascii=False, indent=2)
        
        # 벡터 스토어에 저장
        vector_store = get_vector_store()
        vector_store.add_job_posting(job_data)
        
        return JobPostingResponse(**job_data)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job Posting 업로드 중 오류가 발생했습니다: {str(e)}")

@app.get("/job-postings")
async def get_job_postings():
    """
    저장된 모든 Job Posting을 조회합니다.
    """
    try:
        job_postings = []
        for filename in os.listdir(JOB_POSTINGS_DIR):
            if filename.endswith('.json'):
                file_path = os.path.join(JOB_POSTINGS_DIR, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    job_data = json.load(f)
                    job_postings.append(JobPostingResponse(**job_data))
        
        return {"job_postings": job_postings, "count": len(job_postings)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job Posting 조회 중 오류가 발생했습니다: {str(e)}")

@app.get("/job-postings/{job_id}")
async def get_job_posting(job_id: str):
    """
    특정 Job Posting을 조회합니다.
    """
    try:
        file_path = os.path.join(JOB_POSTINGS_DIR, f"{job_id}.json")
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Job Posting을 찾을 수 없습니다.")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            job_data = json.load(f)
            return JobPostingResponse(**job_data)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job Posting 조회 중 오류가 발생했습니다: {str(e)}")

@app.post("/search")
async def search_documents(query: str, collection: str = "pdf_documents", n_results: int = 5):
    """
    벡터 스토어에서 문서를 검색합니다.
    """
    try:
        vector_store = get_vector_store()
        results = vector_store.search_similar_documents(query, collection, n_results)
        
        return {
            "query": query,
            "collection": collection,
            "results": results,
            "status": "success"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 중 오류가 발생했습니다: {str(e)}")

async def parse_pdf(file_path: str) -> List[str]:
    """
    PDF 파일을 파싱하여 텍스트를 추출합니다.
    PyMuPDF와 pdfplumber를 모두 사용하여 더 나은 결과를 얻습니다.
    """
    pages_text = []
    
    try:
        # PyMuPDF로 파싱 시도
        doc = fitz.open(file_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            pages_text.append(text.strip())
        doc.close()
        
        # 텍스트가 충분하지 않으면 pdfplumber로 재시도
        if not any(text.strip() for text in pages_text):
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    pages_text.append(text.strip())
    
    except Exception as e:
        # PyMuPDF 실패 시 pdfplumber로 재시도
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    pages_text.append(text.strip())
        except Exception as e2:
            raise Exception(f"PDF 파싱 실패: {str(e)}, {str(e2)}")
    
    return pages_text

async def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    텍스트 리스트를 임베딩으로 변환합니다.
    """
    if not texts:
        return []
    
    try:
        model = get_embedding_model()
        # 빈 텍스트 필터링
        non_empty_texts = [text for text in texts if text.strip()]
        
        if not non_empty_texts:
            return []
        
        # 임베딩 생성
        embeddings = model.encode(non_empty_texts)
        
        # numpy 배열을 리스트로 변환
        return embeddings.tolist()
    
    except Exception as e:
        raise Exception(f"임베딩 생성 실패: {str(e)}")

@app.post("/generate-embeddings")
async def generate_embeddings_endpoint(texts: List[str]):
    """
    텍스트 리스트를 받아서 임베딩을 생성합니다.
    """
    try:
        embeddings = await generate_embeddings(texts)
        return {
            "embeddings": embeddings,
            "dimension": len(embeddings[0]) if embeddings else 0,
            "count": len(embeddings)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"임베딩 생성 실패: {str(e)}")

@app.get("/pdf-info/{filename}")
async def get_pdf_info(filename: str):
    """
    업로드된 PDF 파일의 정보를 반환합니다.
    """
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    
    try:
        doc = fitz.open(file_path)
        info = {
            "filename": filename,
            "pages": len(doc),
            "size": os.path.getsize(file_path),
            "metadata": doc.metadata
        }
        doc.close()
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 정보 읽기 실패: {str(e)}")

def parse_cover_letter_sections(cover_letter: str) -> Dict[str, CoverLetterSection]:
    """
    Cover Letter를 섹션으로 파싱합니다.
    """
    lines = cover_letter.split('\n')
    sections = {
        'header': CoverLetterSection(section_name='header', content=''),
        'introduction': CoverLetterSection(section_name='introduction', content=''),
        'body': CoverLetterSection(section_name='body', content=''),
        'conclusion': CoverLetterSection(section_name='conclusion', content=''),
        'signature': CoverLetterSection(section_name='signature', content='')
    }
    
    current_section = 'header'
    section_content = []
    
    for line in lines:
        line = line.strip()
        
        # 섹션 경계 감지
        if line.lower().find('dear') != -1 and line.lower().find('hiring manager') != -1:
            if section_content:
                sections[current_section].content = '\n'.join(section_content)
                section_content = []
            current_section = 'introduction'
        elif line.lower().find('sincerely') != -1 or line.lower().find('best regards') != -1:
            if section_content:
                sections[current_section].content = '\n'.join(section_content)
                section_content = []
            current_section = 'conclusion'
        elif line.lower().find('thank you') != -1 and line.lower().find('consideration') != -1:
            if section_content:
                sections[current_section].content = '\n'.join(section_content)
                section_content = []
            current_section = 'signature'
        
        section_content.append(line)
    
    # 남은 내용을 현재 섹션에 추가
    if section_content:
        sections[current_section].content = '\n'.join(section_content)
    
    return sections

# Cover Letter 편집 관련 API 엔드포인트들

class CoverLetterSaveRequest(BaseModel):
    cover_letter: str
    job_title: str
    company_name: str
    user_background: Optional[str] = None
    user_question: Optional[str] = None

@app.post("/cover-letter/save")
async def save_cover_letter_for_editing(request: CoverLetterSaveRequest):
    """
    Cover Letter를 편집을 위해 저장합니다.
    """
    try:
        version_id = str(uuid.uuid4())
        sections = parse_cover_letter_sections(request.cover_letter)
        
        cover_letter_version = CoverLetterVersion(
            version_id=version_id,
            original_content=request.cover_letter,
            sections=sections,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            job_title=request.job_title,
            company_name=request.company_name,
            user_background=request.user_background,
            user_question=request.user_question
        )
        
        success = cover_letter_manager.save_cover_letter(cover_letter_version)
        if not success:
            raise HTTPException(status_code=500, detail="Cover Letter 저장 실패")
        
        return {
            "version_id": version_id,
            "message": "Cover Letter가 성공적으로 저장되었습니다."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cover Letter 저장 실패: {str(e)}")

@app.get("/cover-letter/{version_id}")
async def get_cover_letter(version_id: str):
    """
    저장된 Cover Letter를 조회합니다.
    """
    try:
        cover_letter = cover_letter_manager.load_cover_letter(version_id)
        if not cover_letter:
            raise HTTPException(status_code=404, detail="Cover Letter를 찾을 수 없습니다.")
        
        # 편집 여부 확인
        has_edits = any(section.is_edited for section in cover_letter.sections.values())
        
        response = CoverLetterResponse(
            version_id=cover_letter.version_id,
            content=cover_letter.original_content,
            sections=cover_letter.sections,
            created_at=cover_letter.created_at,
            updated_at=cover_letter.updated_at,
            job_title=cover_letter.job_title,
            company_name=cover_letter.company_name,
            has_edits=has_edits
        )
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cover Letter 조회 실패: {str(e)}")

@app.put("/cover-letter/{version_id}/section")
async def update_cover_letter_section(request: CoverLetterEditRequest):
    """
    Cover Letter의 특정 섹션을 업데이트합니다.
    """
    try:
        success = cover_letter_manager.update_section(
            request.version_id,
            request.section_name,
            request.new_content
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Cover Letter 또는 섹션을 찾을 수 없습니다.")
        
        return {
            "message": "섹션이 성공적으로 업데이트되었습니다.",
            "version_id": request.version_id,
            "section_name": request.section_name
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"섹션 업데이트 실패: {str(e)}")

@app.put("/cover-letter/{version_id}/save-all")
async def save_all_sections(request: CLSaveRequest):
    """
    Cover Letter의 모든 섹션을 한 번에 저장합니다.
    """
    try:
        cover_letter = cover_letter_manager.load_cover_letter(request.version_id)
        if not cover_letter:
            raise HTTPException(status_code=404, detail="Cover Letter를 찾을 수 없습니다.")
        
        # 모든 섹션 업데이트
        for section_name, content in request.sections.items():
            if section_name in cover_letter.sections:
                cover_letter.sections[section_name].content = content
                cover_letter.sections[section_name].is_edited = True
                cover_letter.sections[section_name].edited_at = datetime.now().isoformat()
        
        cover_letter.updated_at = datetime.now().isoformat()
        
        success = cover_letter_manager.save_cover_letter(cover_letter)
        if not success:
            raise HTTPException(status_code=500, detail="Cover Letter 저장 실패")
        
        return {
            "message": "모든 섹션이 성공적으로 저장되었습니다.",
            "version_id": request.version_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"섹션 저장 실패: {str(e)}")

@app.get("/cover-letter/versions")
async def get_all_cover_letter_versions():
    """
    모든 Cover Letter 버전 목록을 반환합니다.
    """
    try:
        version_ids = cover_letter_manager.get_all_versions()
        versions = []
        
        for version_id in version_ids:
            cover_letter = cover_letter_manager.load_cover_letter(version_id)
            if cover_letter:
                has_edits = any(section.is_edited for section in cover_letter.sections.values())
                versions.append({
                    "version_id": version_id,
                    "job_title": cover_letter.job_title,
                    "company_name": cover_letter.company_name,
                    "created_at": cover_letter.created_at,
                    "updated_at": cover_letter.updated_at,
                    "has_edits": has_edits
                })
        
        return {"versions": versions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"버전 목록 조회 실패: {str(e)}")

@app.delete("/cover-letter/{version_id}")
async def delete_cover_letter(version_id: str):
    """
    Cover Letter를 삭제합니다.
    """
    try:
        success = cover_letter_manager.delete_cover_letter(version_id)
        if not success:
            raise HTTPException(status_code=404, detail="Cover Letter를 찾을 수 없습니다.")
        
        return {"message": "Cover Letter가 성공적으로 삭제되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cover Letter 삭제 실패: {str(e)}")

# 섹션별 버전 관리 API 엔드포인트들

@app.get("/cover-letter/{version_id}/section/{section_name}/history")
async def get_section_history(version_id: str, section_name: str):
    """
    특정 섹션의 버전 히스토리를 조회합니다.
    """
    try:
        history = cover_letter_manager.get_section_history(version_id, section_name)
        return {
            "version_id": version_id,
            "section_name": section_name,
            "history": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"섹션 히스토리 조회 실패: {str(e)}")

@app.post("/cover-letter/{version_id}/section/{section_name}/version")
async def create_section_version(request: SectionVersionRequest):
    """
    섹션의 현재 상태를 새로운 버전으로 저장합니다.
    """
    try:
        cover_letter = cover_letter_manager.load_cover_letter(request.version_id)
        if not cover_letter or request.section_name not in cover_letter.sections:
            raise HTTPException(status_code=404, detail="Cover Letter 또는 섹션을 찾을 수 없습니다.")
        
        section = cover_letter.sections[request.section_name]
        
        # 현재 내용을 새로운 버전으로 저장
        section_version = SectionVersion(
            version_id=str(uuid.uuid4()),
            content=section.content,
            created_at=datetime.now().isoformat(),
            change_description=request.change_description or f"{request.section_name} 섹션 버전 저장"
        )
        section.version_history.append(section_version)
        
        success = cover_letter_manager.save_cover_letter(cover_letter)
        if not success:
            raise HTTPException(status_code=500, detail="버전 저장 실패")
        
        return {
            "message": "섹션 버전이 성공적으로 저장되었습니다.",
            "version_id": section_version.version_id,
            "section_name": request.section_name
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"섹션 버전 저장 실패: {str(e)}")

@app.post("/cover-letter/{version_id}/section/{section_name}/revert")
async def revert_section(request: RevertSectionRequest):
    """
    특정 섹션을 이전 버전으로 되돌립니다.
    """
    try:
        success = cover_letter_manager.revert_section(
            request.version_id,
            request.section_name,
            request.target_version_id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="버전을 찾을 수 없거나 되돌리기 실패")
        
        return {
            "message": "섹션이 성공적으로 되돌려졌습니다.",
            "version_id": request.version_id,
            "section_name": request.section_name,
            "target_version_id": request.target_version_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"섹션 되돌리기 실패: {str(e)}")

@app.put("/cover-letter/{version_id}/section/{section_name}/update-with-description")
async def update_section_with_description(
    version_id: str,
    section_name: str,
    new_content: str,
    change_description: str = None
):
    """
    섹션을 업데이트하고 변경 설명과 함께 버전 히스토리에 추가합니다.
    """
    try:
        success = cover_letter_manager.update_section(
            version_id,
            section_name,
            new_content,
            change_description
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Cover Letter 또는 섹션을 찾을 수 없습니다.")
        
        return {
            "message": "섹션이 성공적으로 업데이트되었습니다.",
            "version_id": version_id,
            "section_name": section_name
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"섹션 업데이트 실패: {str(e)}")

@app.get("/cover-letter/{version_id}/save-status")
async def get_save_status(version_id: str):
    """
    Cover Letter의 저장 상태를 확인합니다.
    """
    try:
        cover_letter = cover_letter_manager.load_cover_letter(version_id)
        if not cover_letter:
            raise HTTPException(status_code=404, detail="Cover Letter를 찾을 수 없습니다.")
        
        # 편집된 섹션 수 계산
        edited_sections = sum(1 for section in cover_letter.sections.values() if section.is_edited)
        total_sections = len(cover_letter.sections)
        
        return {
            "version_id": version_id,
            "last_updated": cover_letter.updated_at,
            "created_at": cover_letter.created_at,
            "edited_sections": edited_sections,
            "total_sections": total_sections,
            "has_edits": edited_sections > 0,
            "job_title": cover_letter.job_title,
            "company_name": cover_letter.company_name
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"저장 상태 조회 실패: {str(e)}")

@app.get("/debug/pdf-contents")
async def debug_pdf_contents():
    """
    업로드된 모든 PDF 문서의 내용을 확인합니다.
    """
    try:
        vector_store = get_vector_store()
        results = vector_store.collections['pdf_documents'].get()
        
        pdf_contents = []
        for i, doc_id in enumerate(results['ids']):
            pdf_contents.append({
                'id': doc_id,
                'content': results['documents'][i][:500] + "..." if len(results['documents'][i]) > 500 else results['documents'][i],
                'metadata': results['metadatas'][i],
                'full_content_length': len(results['documents'][i])
            })
        
        return {
            "total_pdfs": len(pdf_contents),
            "pdf_contents": pdf_contents
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 내용 조회 실패: {str(e)}")

@app.post("/debug/test-retrieval")
async def test_retrieval(query: str, n_results: int = 3):
    """
    특정 쿼리로 PDF 검색을 테스트합니다.
    """
    try:
        from retrieval import get_retrieval_component
        retrieval = get_retrieval_component()
        results = retrieval.retrieve_relevant_pdf_documents(query, n_results)
        
        return {
            "query": query,
            "results": results,
            "total_found": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 테스트 실패: {str(e)}")

@app.get("/pdf-files")
async def get_pdf_files():
    """
    업로드된 PDF 파일 목록을 반환합니다.
    """
    try:
        pdf_files = []
        if os.path.exists(UPLOAD_DIR):
            for filename in os.listdir(UPLOAD_DIR):
                if filename.lower().endswith('.pdf'):
                    file_path = os.path.join(UPLOAD_DIR, filename)
                    file_stats = os.stat(file_path)
                    pdf_files.append({
                        "filename": filename,
                        "size_bytes": file_stats.st_size,
                        "size_mb": round(file_stats.st_size / (1024 * 1024), 2),
                        "uploaded_at": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                        "file_path": file_path
                    })
        
        return {
            "total_files": len(pdf_files),
            "files": sorted(pdf_files, key=lambda x: x["uploaded_at"], reverse=True)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 파일 목록 조회 중 오류: {str(e)}")

@app.get("/debug/vector-store-stats")
async def get_vector_store_stats():
    """
    벡터 스토어의 통계 정보를 확인합니다.
    """
    try:
        vector_store = get_vector_store()
        stats = {}
        
        for collection_name, collection in vector_store.collections.items():
            try:
                count = collection.count()
                stats[collection_name] = {
                    'document_count': count,
                    'status': 'active'
                }
            except Exception as e:
                stats[collection_name] = {
                    'document_count': 0,
                    'status': f'error: {str(e)}'
                }
        
        return {
            "vector_store_stats": stats,
            "total_documents": sum(stat['document_count'] for stat in stats.values())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"벡터 스토어 통계 조회 실패: {str(e)}")

@app.post("/debug/context-analysis")
async def analyze_context_for_cover_letter(
    job_title: str,
    company_name: str,
    user_question: str = None
):
    """
    Cover Letter 생성을 위한 컨텍스트 분석을 수행합니다.
    """
    try:
        from retrieval import get_retrieval_component
        retrieval = get_retrieval_component()
        context = retrieval.retrieve_context_for_cover_letter(
            job_title=job_title,
            company_name=company_name,
            user_question=user_question
        )
        
        # PDF 문서 내용 요약
        pdf_summary = []
        for doc in context['pdf_documents']:
            pdf_summary.append({
                'id': doc['id'],
                'similarity_score': doc['similarity_score'],
                'content_preview': doc['content'][:200] + "..." if len(doc['content']) > 200 else doc['content'],
                'metadata': doc['metadata']
            })
        
        return {
            "context_analysis": {
                "job_postings_found": len(context['job_postings']),
                "pdf_documents_found": len(context['pdf_documents']),
                "pdf_documents": pdf_summary,
                "avg_job_similarity": context['summary']['avg_job_similarity'],
                "avg_pdf_similarity": context['summary']['avg_pdf_similarity'],
                "query_info": context['query_info']
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"컨텍스트 분석 실패: {str(e)}")

@app.post("/api/debug-context")
async def debug_context_api(request: dict):
    """
    프론트엔드에서 호출하는 debug-context API
    """
    try:
        job_posting = request.get('job_posting', '')
        
        # job_posting에서 job_title과 company_name 추출 (간단한 추출)
        lines = job_posting.split('\n')
        job_title = lines[0] if lines else 'Unknown Position'
        company_name = lines[1] if len(lines) > 1 else 'Unknown Company'
        
        from retrieval import get_retrieval_component
        retrieval = get_retrieval_component()
        context = retrieval.retrieve_context_for_cover_letter(
            job_title=job_title,
            company_name=company_name,
            user_question=None
        )
        
        # PDF 문서 내용 요약
        pdf_summary = []
        for doc in context['pdf_documents']:
            pdf_summary.append({
                'id': doc['id'],
                'similarity_score': doc['similarity_score'],
                'content_preview': doc['content'][:200] + "..." if len(doc['content']) > 200 else doc['content'],
                'metadata': doc['metadata']
            })
        
        return {
            "context_analysis": {
                "job_postings_found": len(context['job_postings']),
                "pdf_documents_found": len(context['pdf_documents']),
                "pdf_documents": pdf_summary,
                "avg_job_similarity": context['summary']['avg_job_similarity'],
                "avg_pdf_similarity": context['summary']['avg_pdf_similarity'],
                "query_info": context['query_info']
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"컨텍스트 분석 실패: {str(e)}")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 