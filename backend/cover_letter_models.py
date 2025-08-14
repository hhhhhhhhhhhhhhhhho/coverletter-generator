from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
import json
import os

class SectionVersion(BaseModel):
    """섹션 버전을 나타내는 모델"""
    version_id: str
    content: str
    created_at: str
    change_description: Optional[str] = None

class CoverLetterSection(BaseModel):
    """Cover Letter 섹션을 나타내는 모델"""
    section_name: str
    content: str
    is_edited: bool = False
    edited_at: Optional[str] = None
    version_history: List[SectionVersion] = []

class CoverLetterVersion(BaseModel):
    """Cover Letter 버전을 나타내는 모델"""
    version_id: str
    original_content: str
    sections: Dict[str, CoverLetterSection]
    created_at: str
    updated_at: str
    job_title: str
    company_name: str
    user_background: Optional[str] = None
    user_question: Optional[str] = None

class CoverLetterEditRequest(BaseModel):
    """Cover Letter 편집 요청 모델"""
    version_id: str
    section_name: str
    new_content: str

class CoverLetterSaveRequest(BaseModel):
    """Cover Letter 저장 요청 모델"""
    version_id: str
    sections: Dict[str, str]  # section_name -> content

class SectionVersionRequest(BaseModel):
    """섹션 버전 관리 요청 모델"""
    version_id: str
    section_name: str
    change_description: Optional[str] = None

class RevertSectionRequest(BaseModel):
    """섹션 되돌리기 요청 모델"""
    version_id: str
    section_name: str
    target_version_id: str

class CoverLetterResponse(BaseModel):
    """Cover Letter 응답 모델"""
    version_id: str
    content: str
    sections: Dict[str, CoverLetterSection]
    created_at: str
    updated_at: str
    job_title: str
    company_name: str
    has_edits: bool

class CoverLetterManager:
    """Cover Letter 관리를 위한 클래스"""
    
    def __init__(self, storage_dir: str = "cover_letters"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
    
    def _get_file_path(self, version_id: str) -> str:
        """버전 ID에 해당하는 파일 경로를 반환합니다."""
        return os.path.join(self.storage_dir, f"{version_id}.json")
    
    def save_cover_letter(self, cover_letter: CoverLetterVersion) -> bool:
        """Cover Letter를 파일에 저장합니다."""
        try:
            file_path = self._get_file_path(cover_letter.version_id)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(cover_letter.dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Cover Letter 저장 실패: {str(e)}")
            return False
    
    def load_cover_letter(self, version_id: str) -> Optional[CoverLetterVersion]:
        """Cover Letter를 파일에서 로드합니다."""
        try:
            file_path = self._get_file_path(version_id)
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return CoverLetterVersion(**data)
        except Exception as e:
            print(f"Cover Letter 로드 실패: {str(e)}")
            return None
    
    def update_section(self, version_id: str, section_name: str, new_content: str, change_description: str = None) -> bool:
        """특정 섹션을 업데이트하고 버전 히스토리에 추가합니다."""
        try:
            cover_letter = self.load_cover_letter(version_id)
            if not cover_letter:
                return False
            
            # 섹션 업데이트
            if section_name in cover_letter.sections:
                section = cover_letter.sections[section_name]
                
                # 현재 내용을 버전 히스토리에 추가
                if section.content != new_content:
                    section_version = SectionVersion(
                        version_id=str(uuid.uuid4()),
                        content=section.content,
                        created_at=datetime.now().isoformat(),
                        change_description=change_description or f"{section_name} 섹션 수정"
                    )
                    section.version_history.append(section_version)
                
                # 새 내용으로 업데이트
                section.content = new_content
                section.is_edited = True
                section.edited_at = datetime.now().isoformat()
                cover_letter.updated_at = datetime.now().isoformat()
                
                return self.save_cover_letter(cover_letter)
            return False
        except Exception as e:
            print(f"섹션 업데이트 실패: {str(e)}")
            return False

    def get_section_history(self, version_id: str, section_name: str) -> List[SectionVersion]:
        """특정 섹션의 버전 히스토리를 반환합니다."""
        try:
            cover_letter = self.load_cover_letter(version_id)
            if not cover_letter or section_name not in cover_letter.sections:
                return []
            
            return cover_letter.sections[section_name].version_history
        except Exception as e:
            print(f"섹션 히스토리 조회 실패: {str(e)}")
            return []

    def revert_section(self, version_id: str, section_name: str, target_version_id: str) -> bool:
        """특정 섹션을 이전 버전으로 되돌립니다."""
        try:
            cover_letter = self.load_cover_letter(version_id)
            if not cover_letter or section_name not in cover_letter.sections:
                return False
            
            section = cover_letter.sections[section_name]
            
            # 타겟 버전 찾기
            target_version = None
            for version in section.version_history:
                if version.version_id == target_version_id:
                    target_version = version
                    break
            
            if not target_version:
                return False
            
            # 현재 내용을 히스토리에 추가
            current_version = SectionVersion(
                version_id=str(uuid.uuid4()),
                content=section.content,
                created_at=datetime.now().isoformat(),
                change_description=f"{section_name} 섹션 되돌리기"
            )
            section.version_history.append(current_version)
            
            # 타겟 버전으로 되돌리기
            section.content = target_version.content
            section.is_edited = True
            section.edited_at = datetime.now().isoformat()
            cover_letter.updated_at = datetime.now().isoformat()
            
            return self.save_cover_letter(cover_letter)
        except Exception as e:
            print(f"섹션 되돌리기 실패: {str(e)}")
            return False
    
    def get_all_versions(self) -> List[str]:
        """모든 버전 ID를 반환합니다."""
        try:
            files = [f for f in os.listdir(self.storage_dir) if f.endswith('.json')]
            return [f.replace('.json', '') for f in files]
        except Exception as e:
            print(f"버전 목록 조회 실패: {str(e)}")
            return []
    
    def delete_cover_letter(self, version_id: str) -> bool:
        """Cover Letter를 삭제합니다."""
        try:
            file_path = self._get_file_path(version_id)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Cover Letter 삭제 실패: {str(e)}")
            return False

# 전역 인스턴스
cover_letter_manager = CoverLetterManager()
