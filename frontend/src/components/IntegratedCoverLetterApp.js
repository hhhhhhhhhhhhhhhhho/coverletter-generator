import React, { useState, useEffect, useCallback } from 'react';
import './IntegratedCoverLetterApp.css';

const IntegratedCoverLetterApp = () => {
  // 상태 관리
  const [jobPosting, setJobPosting] = useState('');
  const [coverLetter, setCoverLetter] = useState('');
  const [generatedCoverLetter, setGeneratedCoverLetter] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [debugInfo, setDebugInfo] = useState(null);
  const [showDebug, setShowDebug] = useState(false);
  const [autoSaveTimer, setAutoSaveTimer] = useState(null);
  const [lastSaved, setLastSaved] = useState(null);

  // 자동 저장 기능
  const autoSave = useCallback(() => {
    const data = {
      jobPosting,
      coverLetter,
      generatedCoverLetter,
      timestamp: new Date().toISOString()
    };
    localStorage.setItem('coverLetterAutoSave', JSON.stringify(data));
    setLastSaved(new Date());
  }, [jobPosting, coverLetter, generatedCoverLetter]);

  // 자동 저장 타이머 설정
  useEffect(() => {
    if (autoSaveTimer) clearTimeout(autoSaveTimer);
    const timer = setTimeout(autoSave, 3000);
    setAutoSaveTimer(timer);
    return () => clearTimeout(timer);
  }, [jobPosting, coverLetter, generatedCoverLetter, autoSave]);

  // 페이지 로드 시 자동 저장된 데이터 복원
  useEffect(() => {
    const saved = localStorage.getItem('coverLetterAutoSave');
    if (saved) {
      try {
        const data = JSON.parse(saved);
        setJobPosting(data.jobPosting || '');
        setCoverLetter(data.coverLetter || '');
        setGeneratedCoverLetter(data.generatedCoverLetter || '');
      } catch (error) {
        console.error('자동 저장 데이터 복원 실패:', error);
      }
    }
  }, []);

  // 파일 업로드 처리
  const handleFileUpload = async (event) => {
    const files = Array.from(event.target.files);
    const newFiles = [];

    for (const file of files) {
      if (file.type === 'application/pdf') {
        const formData = new FormData();
        formData.append('file', file);

        try {
          const response = await fetch('/api/upload-pdf', {
            method: 'POST',
            body: formData,
          });

          if (response.ok) {
            const result = await response.json();
            newFiles.push({
              name: file.name,
              content: result.content,
              id: Date.now() + Math.random()
            });
          } else {
            alert(`파일 업로드 실패: ${file.name}`);
          }
        } catch (error) {
          console.error('파일 업로드 오류:', error);
          alert(`파일 업로드 중 오류가 발생했습니다: ${file.name}`);
        }
      } else {
        alert('PDF 파일만 업로드 가능합니다.');
      }
    }

    setUploadedFiles(prev => [...prev, ...newFiles]);
  };

  // 파일 삭제
  const removeFile = (fileId) => {
    setUploadedFiles(prev => prev.filter(file => file.id !== fileId));
  };

  // 커버레터 생성
  const generateCoverLetter = async () => {
    if (!jobPosting.trim()) {
      alert('채용공고를 입력해주세요.');
      return;
    }

    if (uploadedFiles.length === 0) {
      alert('PDF 파일을 업로드해주세요.');
      return;
    }

    setIsGenerating(true);
    try {
      const response = await fetch('/api/generate-cover-letter', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job_posting: jobPosting,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setGeneratedCoverLetter(data.cover_letter);
        setCoverLetter(data.cover_letter);
      } else {
        const errorData = await response.json();
        alert(`커버레터 생성 실패: ${errorData.detail}`);
      }
    } catch (error) {
      console.error('커버레터 생성 오류:', error);
      alert('커버레터 생성 중 오류가 발생했습니다.');
    } finally {
      setIsGenerating(false);
    }
  };

  // 디버그 정보 조회
  const handleDebugContext = async () => {
    if (!jobPosting.trim() || uploadedFiles.length === 0) {
      alert('채용공고와 PDF 파일을 업로드해주세요.');
      return;
    }

    try {
      const response = await fetch('/api/debug-context', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job_posting: jobPosting,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setDebugInfo(data.context_analysis);
        setShowDebug(true);
      } else {
        const errorData = await response.json();
        alert(`디버그 정보 조회 실패: ${errorData.detail}`);
      }
    } catch (error) {
      console.error('디버그 정보 조회 오류:', error);
      alert('디버그 정보 조회 중 오류가 발생했습니다.');
    }
  };

  // 편집 모드 토글
  const toggleEditMode = () => {
    setIsEditing(!isEditing);
  };

  // 편집 내용 저장
  const saveEdits = () => {
    setCoverLetter(generatedCoverLetter);
    setIsEditing(false);
    alert('편집 내용이 저장되었습니다.');
  };

  // 편집 취소
  const cancelEdits = () => {
    setGeneratedCoverLetter(coverLetter);
    setIsEditing(false);
  };

  // 모든 내용 지우기
  const clearAll = () => {
    if (window.confirm('모든 내용을 지우시겠습니까?')) {
      setJobPosting('');
      setCoverLetter('');
      setGeneratedCoverLetter('');
      setUploadedFiles([]);
      setDebugInfo(null);
      setShowDebug(false);
      localStorage.removeItem('coverLetterAutoSave');
    }
  };

  return (
    <div className="integrated-app">
      {/* 헤더 */}
      <header className="app-header">
        <h1>📝 통합 커버레터 생성기</h1>
        <div className="header-controls">
          <button 
            className="clear-btn"
            onClick={clearAll}
            title="모든 내용 지우기"
          >
            🗑️ 전체 삭제
          </button>
          {lastSaved && (
            <span className="auto-save-indicator">
              💾 {lastSaved.toLocaleTimeString()}에 자동 저장됨
            </span>
          )}
        </div>
      </header>

      <div className="app-content">
        {/* 정보 입력 및 AI 생성 섹션 */}
        <div className="main-section">
          <div className="input-section">
            <div className="input-grid">
              {/* 채용공고 입력 */}
              <div className="input-card">
                <h3>📄 채용공고</h3>
                <textarea
                  value={jobPosting}
                  onChange={(e) => setJobPosting(e.target.value)}
                  placeholder="채용공고 내용을 입력하거나 붙여넣으세요..."
                  rows={8}
                />
              </div>

              {/* AI 생성 버튼 */}
              <div className="generator-card">
                <h3>🤖 AI 커버레터 생성</h3>
                <p className="generator-info">
                  채용공고와 업로드된 PDF를 바탕으로 AI가 맞춤형 커버레터를 생성합니다.
                </p>
                
                <div className="generator-controls">
                  <button 
                    onClick={generateCoverLetter}
                    disabled={isGenerating || !jobPosting.trim() || uploadedFiles.length === 0}
                    className="generate-btn"
                  >
                    {isGenerating ? '🔄 생성 중...' : '🚀 커버레터 생성'}
                  </button>
                </div>

                {isGenerating && (
                  <div className="loading-indicator">
                    <div className="spinner"></div>
                    <p>AI가 커버레터를 생성하고 있습니다...</p>
                  </div>
                )}
              </div>
            </div>

            {/* PDF 파일 업로드 */}
            <div className="upload-section">
              <h3>📁 PDF 파일 업로드</h3>
              <div className="upload-area">
                <input
                  type="file"
                  multiple
                  accept=".pdf"
                  onChange={handleFileUpload}
                  id="file-upload"
                  className="file-input"
                />
                <label htmlFor="file-upload" className="upload-label">
                  <span>📎 PDF 파일 선택</span>
                  <small>여러 파일 선택 가능</small>
                </label>
              </div>

              {/* 업로드된 파일 목록 */}
              {uploadedFiles.length > 0 && (
                <div className="uploaded-files">
                  <h4>업로드된 파일:</h4>
                  <div className="file-list">
                    {uploadedFiles.map((file) => (
                      <div key={file.id} className="file-item">
                        <span className="file-name">📄 {file.name}</span>
                        <button 
                          onClick={() => removeFile(file.id)}
                          className="remove-file-btn"
                        >
                          ❌
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* 디버그 정보 */}
            <div className="debug-section">
              <button 
                onClick={handleDebugContext}
                className="debug-btn"
                disabled={!jobPosting.trim() || uploadedFiles.length === 0}
              >
                🔍 PDF 참조 상태 확인
              </button>
              
              {showDebug && debugInfo && (
                <div className="debug-info">
                  <h4>📊 분석 결과</h4>
                  <div className="debug-stats">
                    <p>평균 유사도: {typeof debugInfo.avg_pdf_similarity === 'number' ? debugInfo.avg_pdf_similarity.toFixed(3) : 'N/A'}</p>
                    <p>참조된 문서 수: {debugInfo.relevant_documents?.length || 0}</p>
                  </div>
                  
                  {debugInfo.relevant_documents && debugInfo.relevant_documents.length > 0 && (
                    <div className="relevant-docs">
                      <h5>관련 문서:</h5>
                      {debugInfo.relevant_documents.map((doc, index) => (
                        <div key={index} className="doc-item">
                          <p><strong>유사도:</strong> {typeof doc.similarity_score === 'number' ? doc.similarity_score.toFixed(3) : 'N/A'}</p>
                          <p><strong>내용 미리보기:</strong> {typeof doc.content_preview === 'string' ? doc.content_preview.substring(0, 100) + '...' : 'N/A'}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* 편집 & 미리보기 섹션 */}
          {generatedCoverLetter && (
            <div className="editor-section">
              <div className="editor-header">
                <h3>✏️ 생성된 커버레터 편집 & 미리보기</h3>
                <div className="editor-controls">
                  <button 
                    onClick={toggleEditMode}
                    className="edit-toggle-btn"
                  >
                    {isEditing ? '👁️ 미리보기' : '✏️ 편집'}
                  </button>
                  
                  {isEditing && (
                    <>
                      <button onClick={saveEdits} className="save-btn">
                        💾 저장
                      </button>
                      <button onClick={cancelEdits} className="cancel-btn">
                        ❌ 취소
                      </button>
                    </>
                  )}
                </div>
              </div>

              <div className="editor-content">
                {isEditing ? (
                  <textarea
                    value={generatedCoverLetter}
                    onChange={(e) => setGeneratedCoverLetter(e.target.value)}
                    className="editor-textarea"
                    placeholder="커버레터 내용을 편집하세요..."
                  />
                ) : (
                  <div className="preview-content">
                    <div className="cover-letter-preview">
                      {generatedCoverLetter ? (
                        generatedCoverLetter.split('\n').map((line, index) => (
                          <p key={index}>{line}</p>
                        ))
                      ) : (
                        <p className="no-content">생성된 커버레터가 없습니다.</p>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* 최종 커버레터 */}
              {coverLetter && (
                <div className="final-cover-letter">
                  <h4>📄 최종 커버레터</h4>
                  <div className="final-content">
                    {coverLetter.split('\n').map((line, index) => (
                      <p key={index}>{line}</p>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 푸터 */}
      <footer className="app-footer">
        <p>💡 팁: 모든 내용은 자동으로 저장됩니다. 브라우저를 새로고침해도 데이터가 유지됩니다.</p>
      </footer>
    </div>
  );
};

export default IntegratedCoverLetterApp;
