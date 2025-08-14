import React, { useState, useEffect } from 'react';
import './CoverLetterEditor.css';

const CoverLetterEditor = ({ coverLetter, onSave, onCancel, jobTitle, companyName, userBackground, userQuestion }) => {
  const [editedSections, setEditedSections] = useState({});
  const [isEditing, setIsEditing] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [versionId, setVersionId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showHistory, setShowHistory] = useState({});
  const [sectionHistory, setSectionHistory] = useState({});
  const [changeDescription, setChangeDescription] = useState('');
  const [lastSaved, setLastSaved] = useState(null);
  const [autoSaveEnabled, setAutoSaveEnabled] = useState(true);
  const [saveInterval, setSaveInterval] = useState(null);

  // Parse cover letter into sections
  const parseCoverLetterSections = (coverLetter) => {
    const lines = coverLetter.split('\n');
    const sections = {
      header: '',
      introduction: '',
      body: '',
      conclusion: '',
      signature: ''
    };

    let currentSection = 'header';
    let sectionContent = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      
      // Detect section boundaries
      if (line.toLowerCase().includes('dear') && line.toLowerCase().includes('hiring manager')) {
        if (sectionContent.length > 0) {
          sections[currentSection] = sectionContent.join('\n');
          sectionContent = [];
        }
        currentSection = 'introduction';
      } else if (line.toLowerCase().includes('sincerely') || line.toLowerCase().includes('best regards')) {
        if (sectionContent.length > 0) {
          sections[currentSection] = sectionContent.join('\n');
          sectionContent = [];
        }
        currentSection = 'conclusion';
      } else if (line.toLowerCase().includes('thank you') && line.toLowerCase().includes('consideration')) {
        if (sectionContent.length > 0) {
          sections[currentSection] = sectionContent.join('\n');
          sectionContent = [];
        }
        currentSection = 'signature';
      }

      sectionContent.push(line);
    }

    // Add remaining content to current section
    if (sectionContent.length > 0) {
      sections[currentSection] = sectionContent.join('\n');
    }

    return sections;
  };

  useEffect(() => {
    if (coverLetter) {
      const sections = parseCoverLetterSections(coverLetter);
      setEditedSections(sections);
    }
  }, [coverLetter]);

  // 자동 저장 기능
  useEffect(() => {
    if (autoSaveEnabled && isEditing && versionId && hasChanges) {
      // 기존 인터벌 클리어
      if (saveInterval) {
        clearTimeout(saveInterval);
      }

      // 3초 후 자동 저장
      const interval = setTimeout(async () => {
        try {
          const sectionsData = {};
          Object.entries(editedSections).forEach(([sectionName, section]) => {
            sectionsData[sectionName] = section.content;
          });

          const response = await fetch(`http://localhost:8000/cover-letter/${versionId}/save-all`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              version_id: versionId,
              sections: sectionsData
            }),
          });

          if (response.ok) {
            setLastSaved(new Date());
            setHasChanges(false);
          }
        } catch (err) {
          console.error('자동 저장 실패:', err);
        }
      }, 3000);

      setSaveInterval(interval);
    }

    return () => {
      if (saveInterval) {
        clearTimeout(saveInterval);
      }
    };
  }, [editedSections, autoSaveEnabled, isEditing, versionId, hasChanges]);

  const handleSectionChange = async (sectionName, value) => {
    setEditedSections(prev => ({
      ...prev,
      [sectionName]: value
    }));
    setHasChanges(true);
    
    // 실시간으로 백엔드에 업데이트 (디바운싱 적용)
    if (versionId && isEditing) {
      try {
        await updateSectionInBackend(sectionName, value);
      } catch (err) {
        console.error('실시간 업데이트 실패:', err);
        // 실시간 업데이트 실패해도 로컬 편집은 계속 가능
      }
    }
  };

  const saveToBackend = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch('http://localhost:8000/cover-letter/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          cover_letter: coverLetter,
          job_title: jobTitle,
          company_name: companyName,
          user_background: userBackground,
          user_question: userQuestion
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setVersionId(data.version_id);
        return data.version_id;
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Cover Letter 저장 실패');
      }
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const updateSectionInBackend = async (sectionName, content) => {
    if (!versionId) return;
    
    try {
      const response = await fetch(`http://localhost:8000/cover-letter/${versionId}/section`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          version_id: versionId,
          section_name: sectionName,
          new_content: content
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '섹션 업데이트 실패');
      }
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  const loadSectionHistory = async (sectionName) => {
    if (!versionId) return;
    
    try {
      const response = await fetch(`http://localhost:8000/cover-letter/${versionId}/section/${sectionName}/history`);
      if (response.ok) {
        const data = await response.json();
        setSectionHistory(prev => ({
          ...prev,
          [sectionName]: data.history || []
        }));
      }
    } catch (err) {
      console.error('섹션 히스토리 로드 실패:', err);
    }
  };

  const createSectionVersion = async (sectionName, description) => {
    if (!versionId) return;
    
    try {
      const response = await fetch(`http://localhost:8000/cover-letter/${versionId}/section/${sectionName}/version`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          version_id: versionId,
          section_name: sectionName,
          change_description: description
        }),
      });

      if (response.ok) {
        await loadSectionHistory(sectionName);
        setChangeDescription('');
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const revertSection = async (sectionName, targetVersionId) => {
    if (!versionId) return;
    
    try {
      const response = await fetch(`http://localhost:8000/cover-letter/${versionId}/section/${sectionName}/revert`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          version_id: versionId,
          section_name: sectionName,
          target_version_id: targetVersionId
        }),
      });

      if (response.ok) {
        // 섹션 내용을 다시 로드
        const coverLetterResponse = await fetch(`http://localhost:8000/cover-letter/${versionId}`);
        if (coverLetterResponse.ok) {
          const data = await coverLetterResponse.json();
          const sections = parseCoverLetterSections(data.content);
          setEditedSections(sections);
          await loadSectionHistory(sectionName);
        }
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleEditToggle = async () => {
    if (!isEditing) {
      // 편집 모드 시작 시 백엔드에 저장
      try {
        await saveToBackend();
      } catch (err) {
        console.error('백엔드 저장 실패:', err);
        // 백엔드 저장 실패해도 로컬 편집은 계속 가능
      }
    }
    setIsEditing(!isEditing);
  };

  const handleSave = async () => {
    try {
      setIsLoading(true);
      
      if (versionId) {
        // 모든 섹션을 백엔드에 저장
        const sectionsData = {};
        Object.entries(editedSections).forEach(([sectionName, section]) => {
          sectionsData[sectionName] = section.content;
        });

        const response = await fetch(`http://localhost:8000/cover-letter/${versionId}/save-all`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            version_id: versionId,
            sections: sectionsData
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || '저장 실패');
        }
      }

      const fullCoverLetter = Object.values(editedSections).join('\n\n');
      onSave(fullCoverLetter);
      setIsEditing(false);
      setHasChanges(false);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    // Reset to original content
    const sections = parseCoverLetterSections(coverLetter);
    setEditedSections(sections);
    setIsEditing(false);
    setHasChanges(false);
    onCancel();
  };

  const sectionLabels = {
    header: '헤더 (날짜, 주소)',
    introduction: '도입부 (인사말 및 지원 동기)',
    body: '본문 (경험 및 역량)',
    conclusion: '결론 (감사 인사)',
    signature: '서명'
  };

  const renderSection = (sectionName, content) => {
    const label = sectionLabels[sectionName] || sectionName;
    const history = sectionHistory[sectionName] || [];
    const isHistoryVisible = showHistory[sectionName];
    
    return (
      <div key={sectionName} className="editor-section">
        <div className="section-header">
          <h4>{label}</h4>
          <div className="section-controls">
            {isEditing && (
              <>
                <button
                  className="history-button"
                  onClick={() => {
                    if (!isHistoryVisible) {
                      loadSectionHistory(sectionName);
                    }
                    setShowHistory(prev => ({
                      ...prev,
                      [sectionName]: !isHistoryVisible
                    }));
                  }}
                >
                  {isHistoryVisible ? '히스토리 숨기기' : '버전 히스토리'}
                </button>
                <button
                  className="save-version-button"
                  onClick={() => {
                    const description = prompt('버전 저장 설명을 입력하세요 (선택사항):');
                    if (description !== null) {
                      createSectionVersion(sectionName, description);
                    }
                  }}
                >
                  버전 저장
                </button>
              </>
            )}
            <button
              className="edit-toggle-button"
              onClick={() => handleEditToggle()}
            >
              {isEditing ? '미리보기' : '편집'}
            </button>
          </div>
        </div>
        
        {isEditing ? (
          <textarea
            className="section-editor"
            value={content}
            onChange={(e) => handleSectionChange(sectionName, e.target.value)}
            placeholder={`${label} 내용을 입력하세요...`}
            rows={Math.max(3, content.split('\n').length)}
          />
        ) : (
          <div className="section-preview">
            {content.split('\n').map((line, index) => (
              <p key={index}>{line}</p>
            ))}
          </div>
        )}

        {isHistoryVisible && history.length > 0 && (
          <div className="section-history">
            <h5>버전 히스토리</h5>
            <div className="history-list">
              {history.map((version, index) => (
                <div key={version.version_id} className="history-item">
                  <div className="history-info">
                    <span className="version-number">버전 {history.length - index}</span>
                    <span className="version-date">
                      {new Date(version.created_at).toLocaleString()}
                    </span>
                    {version.change_description && (
                      <span className="version-description">{version.change_description}</span>
                    )}
                  </div>
                  <div className="history-content">
                    <p>{version.content.substring(0, 100)}...</p>
                  </div>
                  <div className="history-actions">
                    <button
                      className="revert-button"
                      onClick={() => {
                        if (window.confirm('이 버전으로 되돌리시겠습니까?')) {
                          revertSection(sectionName, version.version_id);
                        }
                      }}
                    >
                      이 버전으로 되돌리기
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  if (!coverLetter) {
    return <div className="no-cover-letter">편집할 Cover Letter가 없습니다.</div>;
  }

  return (
    <div className="cover-letter-editor">
      <div className="editor-header">
        <h3>Cover Letter 편집</h3>
        <div className="editor-controls">
          {!isEditing ? (
            <button
              className="edit-button"
              onClick={handleEditToggle}
              disabled={isLoading}
            >
              {isLoading ? '저장 중...' : '편집 모드 시작'}
            </button>
          ) : (
            <div className="edit-controls">
              <button
                className="save-button"
                onClick={handleSave}
                disabled={!hasChanges || isLoading}
              >
                {isLoading ? '저장 중...' : '저장'}
              </button>
              <button
                className="cancel-button"
                onClick={handleCancel}
                disabled={isLoading}
              >
                취소
              </button>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="error-message">
          <p>오류: {error}</p>
        </div>
      )}

      {isEditing && (
        <div className="save-status">
          <div className="save-controls">
            <label>
              <input
                type="checkbox"
                checked={autoSaveEnabled}
                onChange={(e) => setAutoSaveEnabled(e.target.checked)}
              />
              자동 저장
            </label>
            {lastSaved && (
              <span className="last-saved">
                마지막 저장: {lastSaved.toLocaleTimeString()}
              </span>
            )}
            {hasChanges && (
              <span className="unsaved-changes">
                저장되지 않은 변경사항이 있습니다
              </span>
            )}
          </div>
        </div>
      )}

      <div className="editor-content">
        {Object.entries(editedSections).map(([sectionName, content]) =>
          renderSection(sectionName, content)
        )}
      </div>

      {isEditing && (
        <div className="editor-footer">
          <div className="edit-tips">
            <h4>편집 팁:</h4>
            <ul>
              <li>각 섹션을 개별적으로 편집할 수 있습니다.</li>
              <li>변경사항은 저장 버튼을 눌러야 적용됩니다.</li>
              <li>취소 버튼을 누르면 원래 내용으로 되돌아갑니다.</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default CoverLetterEditor;
