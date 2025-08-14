import React, { useState, useEffect } from 'react';
import './CoverLetterGenerator.css';
import CoverLetterEditor from './CoverLetterEditor';

const CoverLetterGenerator = () => {
  const [formData, setFormData] = useState({
    jobTitle: '',
    companyName: '',
    userQuestion: '',
    userBackground: '',
    includeVariations: false,
    numVariations: 3
  });
  
  const [jobPostings, setJobPostings] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [showEditor, setShowEditor] = useState(false);
  const [editedCoverLetter, setEditedCoverLetter] = useState(null);
  const [savedVersions, setSavedVersions] = useState([]);
  const [showVersions, setShowVersions] = useState(false);
  const [debugInfo, setDebugInfo] = useState(null);
  const [showDebugInfo, setShowDebugInfo] = useState(false);

  useEffect(() => {
    loadJobPostings();
  }, []);

  const loadJobPostings = async () => {
    try {
      const response = await fetch('http://localhost:8000/job-postings');
      if (response.ok) {
        const data = await response.json();
        setJobPostings(data.job_postings || []);
      }
    } catch (err) {
      console.error('Job Postings 로드 실패:', err);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleJobSelect = (job) => {
    setSelectedJob(job);
    setFormData(prev => ({
      ...prev,
      jobTitle: job.jobTitle,
      companyName: job.companyName
    }));
  };

  const handleGenerate = async (e) => {
    e.preventDefault();
    
    if (!formData.jobTitle || !formData.companyName) {
      setError('직무 제목과 회사명을 입력해주세요.');
      return;
    }

    setIsGenerating(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch('http://localhost:8000/generate-cover-letter', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job_title: formData.jobTitle,
          company_name: formData.companyName,
          user_question: formData.userQuestion || null,
          user_background: formData.userBackground || null,
          include_variations: formData.includeVariations,
          num_variations: parseInt(formData.numVariations)
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setResult(data);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Cover Letter 생성 중 오류가 발생했습니다.');
      }
    } catch (err) {
      setError('서버 연결에 실패했습니다.');
    } finally {
      setIsGenerating(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      alert('클립보드에 복사되었습니다.');
    });
  };

  const handleEditCoverLetter = (coverLetterText) => {
    setEditedCoverLetter(coverLetterText);
    setShowEditor(true);
  };

  const handleSaveEditedCoverLetter = (editedText) => {
    // Update the result with the edited cover letter
    if (result.variations) {
      // If there are variations, update the first one for now
      const updatedResult = {
        ...result,
        variations: result.variations.map((variation, index) => 
          index === 0 ? { ...variation, cover_letter: editedText } : variation
        )
      };
      setResult(updatedResult);
    } else {
      // If it's a single cover letter
      setResult({
        ...result,
        cover_letter: editedText
      });
    }
    setShowEditor(false);
    setEditedCoverLetter(null);
  };

  const handleCancelEdit = () => {
    setShowEditor(false);
    setEditedCoverLetter(null);
  };

  const loadSavedVersions = async () => {
    try {
      const response = await fetch('http://localhost:8000/cover-letter/versions');
      if (response.ok) {
        const data = await response.json();
        const versions = data.versions || [];
        
        // 각 버전의 상세 정보 로드
        const detailedVersions = await Promise.all(
          versions.map(async (version) => {
            try {
              const statusResponse = await fetch(`http://localhost:8000/cover-letter/${version.version_id}/save-status`);
              if (statusResponse.ok) {
                const statusData = await statusResponse.json();
                return { ...version, ...statusData };
              }
            } catch (err) {
              console.error(`버전 ${version.version_id} 상태 로드 실패:`, err);
            }
            return version;
          })
        );
        
        setSavedVersions(detailedVersions);
      }
    } catch (err) {
      console.error('저장된 버전 로드 실패:', err);
    }
  };

  const loadVersion = async (versionId) => {
    try {
      const response = await fetch(`http://localhost:8000/cover-letter/${versionId}`);
      if (response.ok) {
        const data = await response.json();
        // 섹션들을 다시 조합하여 전체 Cover Letter 생성
        const fullContent = Object.values(data.sections).join('\n\n');
        setEditedCoverLetter(fullContent);
        setShowEditor(true);
        setShowVersions(false);
      }
    } catch (err) {
      console.error('버전 로드 실패:', err);
    }
  };

  const deleteVersion = async (versionId) => {
    if (!window.confirm('이 버전을 삭제하시겠습니까?')) return;
    
    try {
      const response = await fetch(`http://localhost:8000/cover-letter/${versionId}`, {
        method: 'DELETE'
      });
      if (response.ok) {
        await loadSavedVersions(); // 목록 새로고침
      }
    } catch (err) {
      console.error('버전 삭제 실패:', err);
    }
  };

  const handleDebugContext = async () => {
    try {
      const response = await fetch('http://localhost:8000/debug/context-analysis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job_title: formData.jobTitle,
          company_name: formData.companyName,
          user_question: formData.userQuestion || null
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setDebugInfo(data.context_analysis);
        setShowDebugInfo(true);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || '컨텍스트 분석에 실패했습니다.');
      }
    } catch (err) {
      setError('컨텍스트 분석 중 오류가 발생했습니다.');
    }
  };

  return (
    <div className="cover-letter-generator">
      <h2>Cover Letter Generator</h2>
      
      <div className="generator-container">
        <div className="form-section">
          <h3>Cover Letter 생성</h3>
          
          <form onSubmit={handleGenerate}>
            <div className="form-group">
              <label htmlFor="jobTitle">직무 제목 *</label>
              <input
                type="text"
                id="jobTitle"
                name="jobTitle"
                value={formData.jobTitle}
                onChange={handleInputChange}
                className="form-control"
                required
                placeholder="예: Senior Software Engineer"
              />
            </div>

            <div className="form-group">
              <label htmlFor="companyName">회사명 *</label>
              <input
                type="text"
                id="companyName"
                name="companyName"
                value={formData.companyName}
                onChange={handleInputChange}
                className="form-control"
                required
                placeholder="예: Tech Corp"
              />
            </div>

            <div className="form-group">
              <label htmlFor="userBackground">지원자 배경</label>
              <textarea
                id="userBackground"
                name="userBackground"
                value={formData.userBackground}
                onChange={handleInputChange}
                className="form-control"
                rows="4"
                placeholder="본인의 경험, 기술, 성과 등을 입력하세요..."
              />
            </div>

            <div className="form-group">
              <label htmlFor="userQuestion">추가 요청사항</label>
              <textarea
                id="userQuestion"
                name="userQuestion"
                value={formData.userQuestion}
                onChange={handleInputChange}
                className="form-control"
                rows="3"
                placeholder="특별히 강조하고 싶은 점이나 요청사항이 있다면 입력하세요..."
              />
            </div>

            <div className="form-group checkbox-group">
              <label>
                <input
                  type="checkbox"
                  name="includeVariations"
                  checked={formData.includeVariations}
                  onChange={handleInputChange}
                />
                여러 버전 생성
              </label>
            </div>

            {formData.includeVariations && (
              <div className="form-group">
                <label htmlFor="numVariations">생성할 버전 수</label>
                <select
                  id="numVariations"
                  name="numVariations"
                  value={formData.numVariations}
                  onChange={handleInputChange}
                  className="form-control"
                >
                  <option value="2">2개</option>
                  <option value="3">3개</option>
                  <option value="4">4개</option>
                  <option value="5">5개</option>
                </select>
              </div>
            )}

            {error && (
              <div className="error-message">
                <p>{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={isGenerating}
              className="generate-button"
            >
              {isGenerating ? '생성 중...' : 'Cover Letter 생성'}
            </button>
            
            <button
              type="button"
              onClick={handleDebugContext}
              className="debug-button"
              style={{ marginLeft: '10px', backgroundColor: '#6c757d' }}
            >
              PDF 참조 상태 확인
            </button>
          </form>
        </div>

        <div className="job-postings-section">
          <h3>저장된 Job Postings</h3>
          <button onClick={loadJobPostings} className="refresh-button">
            새로고침
          </button>
          
          <div className="job-postings-list">
            {jobPostings.map((job) => (
              <div 
                key={job.id} 
                className={`job-posting-item ${selectedJob?.id === job.id ? 'selected' : ''}`}
                onClick={() => handleJobSelect(job)}
              >
                <h4>{job.jobTitle}</h4>
                <p><strong>회사:</strong> {job.companyName}</p>
                <p><strong>생성일:</strong> {new Date(job.createdAt).toLocaleString()}</p>
                {job.jobDescription && (
                  <p><strong>설명:</strong> {job.jobDescription.substring(0, 100)}...</p>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {result && (
        <div className="result-section">
          <h3>생성된 Cover Letter</h3>
          
          {result.variations ? (
            <div className="variations-container">
              {result.variations.map((variation, index) => (
                <div key={index} className="variation-item">
                  <div className="variation-header">
                    <h4>버전 {variation.version} ({variation.style})</h4>
                    <div className="variation-controls">
                      <button 
                        onClick={() => handleEditCoverLetter(variation.cover_letter)}
                        className="edit-button"
                      >
                        편집
                      </button>
                      <button 
                        onClick={() => copyToClipboard(variation.cover_letter)}
                        className="copy-button"
                      >
                        복사
                      </button>
                    </div>
                  </div>
                  <div className="cover-letter-content">
                    {variation.cover_letter.split('\n').map((line, i) => (
                      <p key={i}>{line}</p>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="single-cover-letter">
              <div className="cover-letter-header">
                <h4>Cover Letter</h4>
                <div className="cover-letter-controls">
                  <button 
                    onClick={() => handleEditCoverLetter(result.cover_letter)}
                    className="edit-button"
                  >
                    편집
                  </button>
                  <button 
                    onClick={() => copyToClipboard(result.cover_letter)}
                    className="copy-button"
                  >
                    복사
                  </button>
                </div>
              </div>
              <div className="cover-letter-content">
                {result.cover_letter.split('\n').map((line, i) => (
                  <p key={i}>{line}</p>
                ))}
              </div>
            </div>
          )}

          <div className="generation-info">
            <h4>생성 정보</h4>
            <p><strong>모델:</strong> {result.generation_info?.model}</p>
            <p><strong>생성 시간:</strong> {new Date(result.generation_info?.generated_at).toLocaleString()}</p>
            <p><strong>사용된 컨텍스트:</strong> {result.context_info?.job_postings_found || 0}개 Job Posting, {result.context_info?.pdf_documents_found || 0}개 PDF 문서</p>
          </div>

          <div className="version-management">
            <div className="version-header">
              <h4>저장된 버전</h4>
              <div className="version-controls">
                <button onClick={loadSavedVersions} className="refresh-button">
                  새로고침
                </button>
                <button onClick={() => setShowVersions(!showVersions)} className="toggle-button">
                  {showVersions ? '숨기기' : '보기'}
                </button>
              </div>
            </div>
            
            {showVersions && (
              <div className="saved-versions">
                {savedVersions.length === 0 ? (
                  <p className="no-versions">저장된 버전이 없습니다.</p>
                ) : (
                  savedVersions.map((version) => (
                    <div key={version.version_id} className="version-item">
                      <div className="version-info">
                        <h5>{version.job_title} - {version.company_name}</h5>
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
                        <p className="version-id">ID: {version.version_id.substring(0, 8)}...</p>
                      </div>
                      <div className="version-actions">
                        <button onClick={() => loadVersion(version.version_id)} className="load-button">
                          불러오기
                        </button>
                        <button onClick={() => deleteVersion(version.version_id)} className="delete-button">
                          삭제
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {showEditor && editedCoverLetter && (
        <CoverLetterEditor
          coverLetter={editedCoverLetter}
          onSave={handleSaveEditedCoverLetter}
          onCancel={handleCancelEdit}
          jobTitle={formData.jobTitle}
          companyName={formData.companyName}
          userBackground={formData.userBackground}
          userQuestion={formData.userQuestion}
        />
      )}

      {debugInfo && showDebugInfo && (
        <div className="debug-info" style={{ 
          marginTop: '20px', 
          padding: '15px', 
          backgroundColor: '#f8f9fa', 
          border: '1px solid #dee2e6',
          borderRadius: '5px'
        }}>
          <h4>📊 PDF 참조 상태</h4>
          <p><strong>업로드된 PDF 수:</strong> {debugInfo.pdf_documents_found || 0}</p>
          <p><strong>Job Posting 수:</strong> {debugInfo.job_postings_found || 0}</p>
          <p><strong>평균 PDF 유사도:</strong> {
            typeof debugInfo.avg_pdf_similarity === 'number' 
              ? debugInfo.avg_pdf_similarity.toFixed(3) 
              : 'N/A'
          }</p>
          
          {debugInfo.pdf_documents && Array.isArray(debugInfo.pdf_documents) && debugInfo.pdf_documents.length > 0 ? (
            <div>
              <h5>📄 참조된 PDF 문서:</h5>
              {debugInfo.pdf_documents.map((doc, index) => (
                <div key={index} style={{ 
                  marginBottom: '10px', 
                  padding: '10px', 
                  backgroundColor: 'white',
                  border: '1px solid #e9ecef',
                  borderRadius: '3px'
                }}>
                  <p><strong>유사도:</strong> {
                    typeof doc.similarity_score === 'number' 
                      ? doc.similarity_score.toFixed(3) 
                      : 'N/A'
                  }</p>
                  <p><strong>내용 미리보기:</strong></p>
                  <p style={{ fontSize: '0.9em', color: '#666' }}>
                    {typeof doc.content_preview === 'string' ? doc.content_preview : '내용 없음'}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: '#dc3545' }}>⚠️ 참조할 PDF 문서가 없습니다.</p>
          )}
          
          <button 
            onClick={() => setShowDebugInfo(false)}
            style={{ 
              marginTop: '10px', 
              padding: '5px 10px', 
              backgroundColor: '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '3px',
              cursor: 'pointer'
            }}
          >
            닫기
          </button>
        </div>
      )}
    </div>
  );
};

export default CoverLetterGenerator; 