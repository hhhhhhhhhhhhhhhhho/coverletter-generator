import React, { useState, useEffect } from 'react';
import './UnifiedCoverLetterApp.css';

const UnifiedCoverLetterApp = () => {
  // 상태 관리
  const [activeTab, setActiveTab] = useState('upload'); // upload, generate, edit, files
  const [pdfFiles, setPdfFiles] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // PDF 업로드 상태
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [uploadProgress, setUploadProgress] = useState({});
  
  // Job Posting 상태
  const [jobPosting, setJobPosting] = useState({
    jobTitle: '',
    companyName: '',
    jobDescription: '',
    requirements: '',
    companyVision: ''
  });
  
  // Cover Letter 생성 상태
  const [coverLetterData, setCoverLetterData] = useState({
    userBackground: '',
    userQuestion: '',
    includeVariations: false,
    numVariations: 3
  });
  
  const [generatedCoverLetter, setGeneratedCoverLetter] = useState(null);
  const [savedVersions, setSavedVersions] = useState([]);
  const [showVersions, setShowVersions] = useState(false);
  
  // 편집 상태
  const [editedCoverLetter, setEditedCoverLetter] = useState(null);
  const [showEditor, setShowEditor] = useState(false);
  
  // 디버그 상태
  const [debugInfo, setDebugInfo] = useState(null);
  const [showDebugInfo, setShowDebugInfo] = useState(false);

  // 컴포넌트 마운트 시 PDF 파일 목록 로드
  useEffect(() => {
    loadPdfFiles();
  }, []);

  // PDF 파일 목록 로드
  const loadPdfFiles = async () => {
    try {
      const response = await fetch('http://localhost:8000/pdf-files');
      if (response.ok) {
        const data = await response.json();
        setPdfFiles(data.files || []);
      }
    } catch (err) {
      console.error('PDF 파일 목록 로드 실패:', err);
    }
  };

  // 파일 업로드 처리
  const handleFileUpload = async (event) => {
    const files = Array.from(event.target.files);
    setUploadedFiles(files);
    setUploadProgress({});
    setError(null);
    setSuccess(null);

    for (const file of files) {
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        setError(`${file.name}은 PDF 파일이 아닙니다.`);
        continue;
      }

      const formData = new FormData();
      formData.append('file', file);

      try {
        setUploadProgress(prev => ({ ...prev, [file.name]: 'uploading' }));
        
        const response = await fetch('http://localhost:8000/upload-pdf', {
          method: 'POST',
          body: formData,
        });

        if (response.ok) {
          setUploadProgress(prev => ({ ...prev, [file.name]: 'success' }));
          setSuccess(`${file.name} 업로드 성공!`);
          // PDF 파일 목록 새로고침
          setTimeout(() => loadPdfFiles(), 1000);
        } else {
          const errorData = await response.json();
          setUploadProgress(prev => ({ ...prev, [file.name]: 'error' }));
          setError(`${file.name} 업로드 실패: ${errorData.detail}`);
        }
      } catch (err) {
        setUploadProgress(prev => ({ ...prev, [file.name]: 'error' }));
        setError(`${file.name} 업로드 중 오류: ${err.message}`);
      }
    }
  };

  // Job Posting 저장
  const handleJobPostingSave = async () => {
    if (!jobPosting.jobTitle || !jobPosting.companyName) {
      setError('직무 제목과 회사명은 필수입니다.');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch('http://localhost:8000/job-postings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(jobPosting),
      });

      if (response.ok) {
        const data = await response.json();
        setSuccess('Job Posting이 성공적으로 저장되었습니다!');
        setJobPosting({
          jobTitle: '',
          companyName: '',
          jobDescription: '',
          requirements: '',
          companyVision: ''
        });
      } else {
        const errorData = await response.json();
        setError(`Job Posting 저장 실패: ${errorData.detail}`);
      }
    } catch (err) {
      setError('Job Posting 저장 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  // Cover Letter 생성
  const handleGenerateCoverLetter = async () => {
    if (!jobPosting.jobTitle || !jobPosting.companyName) {
      setError('직무 제목과 회사명을 입력해주세요.');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch('http://localhost:8000/generate-cover-letter', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job_title: jobPosting.jobTitle,
          company_name: jobPosting.companyName,
          user_question: coverLetterData.userQuestion,
          user_background: coverLetterData.userBackground,
          include_variations: coverLetterData.includeVariations,
          num_variations: coverLetterData.numVariations
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setGeneratedCoverLetter(data);
        setSuccess('Cover Letter가 성공적으로 생성되었습니다!');
        setActiveTab('edit');
      } else {
        const errorData = await response.json();
        setError(`Cover Letter 생성 실패: ${errorData.detail}`);
      }
    } catch (err) {
      setError('Cover Letter 생성 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  // 디버그 정보 확인
  const handleDebugContext = async () => {
    try {
      const response = await fetch('http://localhost:8000/debug/context-analysis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job_title: jobPosting.jobTitle,
          company_name: jobPosting.companyName,
          user_question: coverLetterData.userQuestion || null
        }),
      });

      if (response.ok) {
        const data = await response.json();
        // 안전한 데이터 처리
        const safeContextAnalysis = {
          pdf_documents_found: data.context_analysis?.pdf_documents_found || 0,
          job_postings_found: data.context_analysis?.job_postings_found || 0,
          avg_pdf_similarity: data.context_analysis?.avg_pdf_similarity || 'N/A',
          pdf_documents: Array.isArray(data.context_analysis?.pdf_documents) 
            ? data.context_analysis.pdf_documents.map(doc => ({
                similarity_score: typeof doc.similarity_score === 'number' ? doc.similarity_score : 'N/A',
                content_preview: typeof doc.content_preview === 'string' ? doc.content_preview : '내용 없음'
              }))
            : []
        };
        setDebugInfo(safeContextAnalysis);
        setShowDebugInfo(true);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || '컨텍스트 분석에 실패했습니다.');
      }
    } catch (err) {
      setError('컨텍스트 분석 중 오류가 발생했습니다.');
    }
  };

  // 편집 모드 시작
  const handleStartEdit = () => {
    if (generatedCoverLetter) {
      setEditedCoverLetter(generatedCoverLetter);
      setShowEditor(true);
    }
  };

  // 편집 완료
  const handleSaveEditedCoverLetter = async (editedData) => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch('http://localhost:8000/cover-letters', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job_title: jobPosting.jobTitle,
          company_name: jobPosting.companyName,
          cover_letter: editedData,
          user_background: coverLetterData.userBackground,
          user_question: coverLetterData.userQuestion
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setSuccess('Cover Letter가 성공적으로 저장되었습니다!');
        setShowEditor(false);
        setEditedCoverLetter(null);
        // 저장된 버전 목록 새로고침
        loadSavedVersions();
      } else {
        const errorData = await response.json();
        setError(`저장 실패: ${errorData.detail}`);
      }
    } catch (err) {
      setError('저장 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  // 저장된 버전 로드
  const loadSavedVersions = async () => {
    try {
      const response = await fetch('http://localhost:8000/cover-letters');
      if (response.ok) {
        const data = await response.json();
        setSavedVersions(data.versions || []);
      }
    } catch (err) {
      console.error('저장된 버전 로드 실패:', err);
    }
  };

  // 버전 불러오기
  const loadVersion = async (versionId) => {
    try {
      const response = await fetch(`http://localhost:8000/cover-letters/${versionId}`);
      if (response.ok) {
        const data = await response.json();
        setGeneratedCoverLetter(data);
        setActiveTab('edit');
        setSuccess('버전을 성공적으로 불러왔습니다!');
      }
    } catch (err) {
      setError('버전 불러오기 실패');
    }
  };

  // 버전 삭제
  const deleteVersion = async (versionId) => {
    if (!window.confirm('정말로 이 버전을 삭제하시겠습니까?')) return;

    try {
      const response = await fetch(`http://localhost:8000/cover-letters/${versionId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setSuccess('버전이 삭제되었습니다.');
        loadSavedVersions();
      } else {
        setError('버전 삭제 실패');
      }
    } catch (err) {
      setError('버전 삭제 중 오류가 발생했습니다.');
    }
  };

  // 입력 필드 변경 처리
  const handleInputChange = (section, field, value) => {
    if (section === 'jobPosting') {
      setJobPosting(prev => ({ ...prev, [field]: value }));
    } else if (section === 'coverLetter') {
      setCoverLetterData(prev => ({ ...prev, [field]: value }));
    }
  };

  // 알림 메시지 초기화
  const clearMessages = () => {
    setError(null);
    setSuccess(null);
  };

  return (
    <div className="unified-app">
      <div className="app-header">
        <h1>📄 Cover Letter Generator</h1>
        <p>AI 기반 맞춤형 자기소개서 생성 도구</p>
      </div>

      {/* 네비게이션 탭 */}
      <div className="nav-tabs">
        <button 
          className={`nav-tab ${activeTab === 'upload' ? 'active' : ''}`}
          onClick={() => setActiveTab('upload')}
        >
          📁 PDF 업로드
        </button>
        <button 
          className={`nav-tab ${activeTab === 'generate' ? 'active' : ''}`}
          onClick={() => setActiveTab('generate')}
        >
          ✍️ Cover Letter 생성
        </button>
        <button 
          className={`nav-tab ${activeTab === 'edit' ? 'active' : ''}`}
          onClick={() => setActiveTab('edit')}
        >
          ✏️ 편집 & 저장
        </button>
        <button 
          className={`nav-tab ${activeTab === 'files' ? 'active' : ''}`}
          onClick={() => setActiveTab('files')}
        >
          📋 파일 관리
        </button>
      </div>

      {/* 알림 메시지 */}
      {error && (
        <div className="alert alert-error" onClick={clearMessages}>
          ❌ {error}
        </div>
      )}
      {success && (
        <div className="alert alert-success" onClick={clearMessages}>
          ✅ {success}
        </div>
      )}

      {/* 로딩 인디케이터 */}
      {isLoading && (
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
          <p>처리 중...</p>
        </div>
      )}

      {/* PDF 업로드 탭 */}
      {activeTab === 'upload' && (
        <div className="tab-content">
          <div className="upload-section">
            <h2>📁 PDF 문서 업로드</h2>
            <p>이력서나 포트폴리오 PDF를 업로드하여 Cover Letter 생성에 활용하세요.</p>
            
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
                <div className="upload-icon">📄</div>
                <p>PDF 파일을 선택하거나 여기에 드래그하세요</p>
                <span className="upload-hint">여러 파일을 동시에 선택할 수 있습니다</span>
              </label>
            </div>

            {/* 업로드 진행 상황 */}
            {Object.keys(uploadProgress).length > 0 && (
              <div className="upload-progress">
                <h3>업로드 진행 상황</h3>
                {Object.entries(uploadProgress).map(([filename, status]) => (
                  <div key={filename} className={`progress-item ${status}`}>
                    <span className="filename">{filename}</span>
                    <span className="status">
                      {status === 'uploading' && '⏳ 업로드 중...'}
                      {status === 'success' && '✅ 완료'}
                      {status === 'error' && '❌ 실패'}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Cover Letter 생성 탭 */}
      {activeTab === 'generate' && (
        <div className="tab-content">
          <div className="generate-section">
            <h2>✍️ Cover Letter 생성</h2>
            
            {/* Job Posting 입력 */}
            <div className="form-section">
              <h3>💼 Job Posting 정보</h3>
              <div className="form-grid">
                <div className="form-group">
                  <label>직무 제목 *</label>
                  <input
                    type="text"
                    value={jobPosting.jobTitle}
                    onChange={(e) => handleInputChange('jobPosting', 'jobTitle', e.target.value)}
                    placeholder="예: Senior Software Engineer"
                    required
                  />
                </div>
                <div className="form-group">
                  <label>회사명 *</label>
                  <input
                    type="text"
                    value={jobPosting.companyName}
                    onChange={(e) => handleInputChange('jobPosting', 'companyName', e.target.value)}
                    placeholder="예: Tech Corp"
                    required
                  />
                </div>
                <div className="form-group full-width">
                  <label>직무 설명</label>
                  <textarea
                    value={jobPosting.jobDescription}
                    onChange={(e) => handleInputChange('jobPosting', 'jobDescription', e.target.value)}
                    placeholder="직무에 대한 상세한 설명을 입력하세요..."
                    rows="3"
                  />
                </div>
                <div className="form-group">
                  <label>요구사항</label>
                  <textarea
                    value={jobPosting.requirements}
                    onChange={(e) => handleInputChange('jobPosting', 'requirements', e.target.value)}
                    placeholder="필요한 기술이나 경험을 입력하세요..."
                    rows="3"
                  />
                </div>
                <div className="form-group">
                  <label>회사 비전</label>
                  <textarea
                    value={jobPosting.companyVision}
                    onChange={(e) => handleInputChange('jobPosting', 'companyVision', e.target.value)}
                    placeholder="회사의 비전이나 문화를 입력하세요..."
                    rows="3"
                  />
                </div>
              </div>
              <button 
                className="btn btn-secondary"
                onClick={handleJobPostingSave}
                disabled={isLoading}
              >
                💾 Job Posting 저장
              </button>
            </div>

            {/* Cover Letter 설정 */}
            <div className="form-section">
              <h3>📝 Cover Letter 설정</h3>
              <div className="form-grid">
                <div className="form-group full-width">
                  <label>지원자 배경</label>
                  <textarea
                    value={coverLetterData.userBackground}
                    onChange={(e) => handleInputChange('coverLetter', 'userBackground', e.target.value)}
                    placeholder="본인의 경험, 기술, 성과 등을 입력하세요..."
                    rows="4"
                  />
                </div>
                <div className="form-group full-width">
                  <label>추가 요청사항</label>
                  <textarea
                    value={coverLetterData.userQuestion}
                    onChange={(e) => handleInputChange('coverLetter', 'userQuestion', e.target.value)}
                    placeholder="특별히 강조하고 싶은 점이나 요청사항이 있다면 입력하세요..."
                    rows="3"
                  />
                </div>
                <div className="form-group">
                  <label>
                    <input
                      type="checkbox"
                      checked={coverLetterData.includeVariations}
                      onChange={(e) => handleInputChange('coverLetter', 'includeVariations', e.target.checked)}
                    />
                    여러 버전 생성
                  </label>
                </div>
                {coverLetterData.includeVariations && (
                  <div className="form-group">
                    <label>생성할 버전 수</label>
                    <select
                      value={coverLetterData.numVariations}
                      onChange={(e) => handleInputChange('coverLetter', 'numVariations', parseInt(e.target.value))}
                    >
                      <option value={2}>2개</option>
                      <option value={3}>3개</option>
                      <option value={4}>4개</option>
                      <option value={5}>5개</option>
                    </select>
                  </div>
                )}
              </div>
              
              <div className="action-buttons">
                <button 
                  className="btn btn-primary"
                  onClick={handleGenerateCoverLetter}
                  disabled={isLoading || !jobPosting.jobTitle || !jobPosting.companyName}
                >
                  🚀 Cover Letter 생성
                </button>
                <button 
                  className="btn btn-info"
                  onClick={handleDebugContext}
                  disabled={isLoading || !jobPosting.jobTitle || !jobPosting.companyName}
                >
                  🔍 PDF 참조 상태 확인
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 편집 탭 */}
      {activeTab === 'edit' && (
        <div className="tab-content">
          <div className="edit-section">
            <h2>✏️ Cover Letter 편집 & 저장</h2>
            
            {generatedCoverLetter ? (
              <div className="cover-letter-display">
                <div className="cover-letter-header">
                  <h3>생성된 Cover Letter</h3>
                  <div className="header-actions">
                    <button 
                      className="btn btn-primary"
                      onClick={handleStartEdit}
                    >
                      ✏️ 편집하기
                    </button>
                    <button 
                      className="btn btn-secondary"
                      onClick={() => setShowVersions(!showVersions)}
                    >
                      📋 저장된 버전 보기
                    </button>
                  </div>
                </div>
                
                <div className="cover-letter-content">
                  {generatedCoverLetter.cover_letter}
                </div>
              </div>
            ) : (
              <div className="no-content">
                <p>생성된 Cover Letter가 없습니다.</p>
                <button 
                  className="btn btn-primary"
                  onClick={() => setActiveTab('generate')}
                >
                  Cover Letter 생성하기
                </button>
              </div>
            )}

            {/* 저장된 버전 목록 */}
            {showVersions && (
              <div className="saved-versions">
                <h3>📋 저장된 버전</h3>
                {savedVersions.length === 0 ? (
                  <p className="no-versions">저장된 버전이 없습니다.</p>
                ) : (
                  <div className="version-grid">
                    {savedVersions.map((version) => (
                      <div key={version.version_id} className="version-card">
                        <div className="version-info">
                          <h4>{version.job_title} - {version.company_name}</h4>
                          <p><strong>생성일:</strong> {new Date(version.created_at).toLocaleString()}</p>
                          <p><strong>수정일:</strong> {new Date(version.updated_at).toLocaleString()}</p>
                          {version.has_edits && (
                            <div className="edit-status">
                              <span className="edited-badge">편집됨</span>
                              <span className="edit-count">
                                {version.edited_sections}/{version.total_sections} 섹션 편집됨
                              </span>
                            </div>
                          )}
                        </div>
                        <div className="version-actions">
                          <button 
                            className="btn btn-sm btn-primary"
                            onClick={() => loadVersion(version.version_id)}
                          >
                            불러오기
                          </button>
                          <button 
                            className="btn btn-sm btn-danger"
                            onClick={() => deleteVersion(version.version_id)}
                          >
                            삭제
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* 파일 관리 탭 */}
      {activeTab === 'files' && (
        <div className="tab-content">
          <div className="files-section">
            <h2>📋 파일 관리</h2>
            
            <div className="files-header">
              <h3>📄 업로드된 PDF 파일</h3>
              <button 
                className="btn btn-secondary"
                onClick={loadPdfFiles}
              >
                🔄 새로고침
              </button>
            </div>

            {pdfFiles.length === 0 ? (
              <div className="no-files">
                <p>업로드된 PDF 파일이 없습니다.</p>
                <button 
                  className="btn btn-primary"
                  onClick={() => setActiveTab('upload')}
                >
                  PDF 업로드하기
                </button>
              </div>
            ) : (
              <div className="files-grid">
                {pdfFiles.map((file, index) => (
                  <div key={index} className="file-card">
                    <div className="file-icon">📄</div>
                    <div className="file-info">
                      <h4>{file.filename}</h4>
                      <p><strong>크기:</strong> {file.size_mb} MB</p>
                      <p><strong>업로드:</strong> {new Date(file.uploaded_at).toLocaleString()}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* 디버그 정보 */}
      {debugInfo && showDebugInfo && (
        <div className="debug-info">
          <h4>📊 PDF 참조 상태</h4>
          <p><strong>업로드된 PDF 수:</strong> {debugInfo.pdf_documents_found || 0}</p>
          <p><strong>Job Posting 수:</strong> {debugInfo.job_postings_found || 0}</p>
          <p><strong>평균 PDF 유사도:</strong> {
            typeof debugInfo.avg_pdf_similarity === 'number' 
              ? debugInfo.avg_pdf_similarity.toFixed(3) 
              : (typeof debugInfo.avg_pdf_similarity === 'object' 
                  ? JSON.stringify(debugInfo.avg_pdf_similarity) 
                  : 'N/A')
          }</p>
          
          {debugInfo.pdf_documents && Array.isArray(debugInfo.pdf_documents) && debugInfo.pdf_documents.length > 0 ? (
            <div>
              <h5>📄 참조된 PDF 문서:</h5>
              {debugInfo.pdf_documents.map((doc, index) => (
                <div key={index} className="debug-doc">
                  <p><strong>유사도:</strong> {
                    typeof doc.similarity_score === 'number' 
                      ? doc.similarity_score.toFixed(3) 
                      : (typeof doc.similarity_score === 'object' 
                          ? JSON.stringify(doc.similarity_score) 
                          : 'N/A')
                  }</p>
                  <p><strong>내용 미리보기:</strong></p>
                  <p className="content-preview">
                    {typeof doc.content_preview === 'string' ? doc.content_preview : '내용 없음'}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="warning">⚠️ 참조할 PDF 문서가 없습니다.</p>
          )}
          
          <button 
            className="btn btn-secondary"
            onClick={() => setShowDebugInfo(false)}
          >
            닫기
          </button>
        </div>
      )}
    </div>
  );
};

export default UnifiedCoverLetterApp;
