import React, { useState } from 'react';
import './JobPostingForm.css';

const JobPostingForm = ({ onSubmit }) => {
  const [formData, setFormData] = useState({
    jobTitle: '',
    companyName: '',
    jobDescription: '',
    requirements: '',
    companyVision: '',
    inputMethod: 'text' // 'text' or 'file'
  });
  
  const [selectedFile, setSelectedFile] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.type === 'text/plain' || file.type === 'application/pdf') {
        setSelectedFile(file);
        setError(null);
      } else {
        setError('텍스트 파일(.txt) 또는 PDF 파일만 업로드 가능합니다.');
        setSelectedFile(null);
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      if (formData.inputMethod === 'file' && selectedFile) {
        // 파일 업로드 처리
        const formDataToSend = new FormData();
        formDataToSend.append('file', selectedFile);
        formDataToSend.append('jobTitle', formData.jobTitle);
        formDataToSend.append('companyName', formData.companyName);
        
        const response = await fetch('http://localhost:8000/upload-job-posting', {
          method: 'POST',
          body: formDataToSend,
        });

        if (response.ok) {
          const result = await response.json();
          onSubmit(result);
        } else {
          const errorData = await response.json();
          setError(errorData.detail || '업로드 중 오류가 발생했습니다.');
        }
      } else if (formData.inputMethod === 'text') {
        // 텍스트 입력 처리
        const response = await fetch('http://localhost:8000/submit-job-posting', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(formData),
        });

        if (response.ok) {
          const result = await response.json();
          onSubmit(result);
        } else {
          const errorData = await response.json();
          setError(errorData.detail || '제출 중 오류가 발생했습니다.');
        }
      }
    } catch (err) {
      setError('서버 연결에 실패했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="job-posting-form">
      <h2>Job Posting Input</h2>
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="inputMethod">입력 방법:</label>
          <select
            id="inputMethod"
            name="inputMethod"
            value={formData.inputMethod}
            onChange={handleInputChange}
            className="form-control"
          >
            <option value="text">텍스트 직접 입력</option>
            <option value="file">파일 업로드</option>
          </select>
        </div>

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

        {formData.inputMethod === 'text' ? (
          <>
            <div className="form-group">
              <label htmlFor="jobDescription">직무 설명 *</label>
              <textarea
                id="jobDescription"
                name="jobDescription"
                value={formData.jobDescription}
                onChange={handleInputChange}
                className="form-control"
                rows="6"
                required
                placeholder="직무에 대한 상세한 설명을 입력하세요..."
              />
            </div>

            <div className="form-group">
              <label htmlFor="requirements">요구사항</label>
              <textarea
                id="requirements"
                name="requirements"
                value={formData.requirements}
                onChange={handleInputChange}
                className="form-control"
                rows="4"
                placeholder="필요한 기술, 경험, 자격 등을 입력하세요..."
              />
            </div>

            <div className="form-group">
              <label htmlFor="companyVision">회사 비전</label>
              <textarea
                id="companyVision"
                name="companyVision"
                value={formData.companyVision}
                onChange={handleInputChange}
                className="form-control"
                rows="4"
                placeholder="회사의 미션, 비전, 문화 등을 입력하세요..."
              />
            </div>
          </>
        ) : (
          <div className="form-group">
            <label htmlFor="jobFile">Job Posting 파일 *</label>
            <input
              type="file"
              id="jobFile"
              accept=".txt,.pdf"
              onChange={handleFileSelect}
              className="form-control"
              required
            />
            <small className="form-text">
              텍스트 파일(.txt) 또는 PDF 파일을 업로드하세요.
            </small>
            {selectedFile && (
              <div className="file-info">
                <p>선택된 파일: {selectedFile.name}</p>
                <p>크기: {(selectedFile.size / 1024).toFixed(2)} KB</p>
              </div>
            )}
          </div>
        )}

        {error && (
          <div className="error-message">
            <p>{error}</p>
          </div>
        )}

        <button
          type="submit"
          disabled={isSubmitting || (formData.inputMethod === 'file' && !selectedFile)}
          className="submit-button"
        >
          {isSubmitting ? '처리 중...' : 'Job Posting 제출'}
        </button>
      </form>
    </div>
  );
};

export default JobPostingForm; 