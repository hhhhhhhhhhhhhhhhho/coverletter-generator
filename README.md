# 📝 AI 커버레터 생성기

채용공고와 이력서 PDF를 분석하여 맞춤형 커버레터를 생성하는 AI 웹 애플리케이션입니다.
![이미지](uploads/image.png)
## 🚀 주요 기능

- **📄 PDF 이력서 업로드**: 이력서 PDF 파일을 업로드하여 텍스트 추출
- **🤖 AI 커버레터 생성**: 채용공고와 이력서를 분석하여 맞춤형 커버레터 생성
- **✏️ 실시간 편집**: 생성된 커버레터를 실시간으로 편집 및 미리보기
- **💾 자동 저장**: 모든 내용이 자동으로 저장되어 브라우저 새로고침 시에도 유지
- **🔍 PDF 참조 분석**: 업로드된 PDF가 제대로 참조되는지 분석 및 확인

## 🛠️ 기술 스택

### Frontend 🎨
```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                             │
├─────────────────────────────────────────────────────────────┤
│  React.js ──→ CSS3 ──→ Responsive Design                    │
│      │                                                      │
│      └──→ JavaScript ES6+ ──→ Fetch API                     │
└─────────────────────────────────────────────────────────────┘
```

### Backend ⚙️
```
┌─────────────────────────────────────────────────────────────┐
│                         Backend                             │
├─────────────────────────────────────────────────────────────┤
│  FastAPI ──→ Python 3.11                                    │
│      │                                                      │
│      ├──→ PyMuPDF                                           │
│      ├──→ pdfplumber                                        │
│      ├──→ SentenceTransformers                              │
│      ├──→ ChromaDB                                          │
│      └──→ OpenAI API                                        │
└─────────────────────────────────────────────────────────────┘
```

### AI & ML 🤖
```
┌─────────────────────────────────────────────────────────────┐
│                       AI & ML                               │
├─────────────────────────────────────────────────────────────┤
│  LangChain ──→ RAG Pipeline                                 │
│      │                                                      │
│      └──→ Vector Embeddings ──→ Semantic Search             │
│                                    │                        │
│                                    └──→ LLM Generation      │
└─────────────────────────────────────────────────────────────┘
```

### Data Storage 💾
```
┌─────────────────────────────────────────────────────────────┐
│                     Data Storage                            │
├─────────────────────────────────────────────────────────────┤
│  Vector Database ──→ Document Embeddings                    │
│                                                             │
│  Local File Storage                                         │
│      ├──→ PDF Files                                         │
│      └──→ Job Postings                                      │
└─────────────────────────────────────────────────────────────┘
```

### Development Tools 🛠️
```
┌─────────────────────────────────────────────────────────────┐
│                  Development Tools                          │
├─────────────────────────────────────────────────────────────┤
│  Docker ──→ Containerization                                │
│  Git ──→ Version Control                                    │
│  ESLint ──→ Code Quality                                    │
└─────────────────────────────────────────────────────────────┘
```

## 🏗️ 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              System Architecture                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│  │   Client    │    │     API     │    │ Processing  │    │     AI      │   │
│  │   Layer     │    │   Layer     │    │   Layer     │    │   Layer     │   │
│  │             │    │             │    │             │    │             │   │
│  │ React       │───▶│ FastAPI     │───▶│ PDF Parser  │───▶│ Vector      │   │
│  │ Frontend    │    │             │    │ Text        │    │ Store       │   │
│  │             │    │ RESTful  API│    │ Extractor   │    │ Semantic    │   │
│  │             │    │             │    │ Embedding   │    │ Search      │   │
│  │             │    │             │    │ Generator   │    │ LLM         │   │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘   │
│                                                                             │
│                                    ┌─────────────┐                          │
│                                    │  Storage    │                          │
│                                    │   Layer     │                          │
│                                    │             │                          │
│                                    │ ChromaDB    │                          │
│                                    │ Local Files │                          │
│                                    └─────────────┘                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 데이터 흐름 🔄
```
1. 사용자 입력 (채용공고 + PDF) 
   ↓
2. PDF 파싱 및 텍스트 추출
   ↓
3. 텍스트 임베딩 생성
   ↓
4. 벡터 스토어에 저장
   ↓
5. 의미적 검색으로 관련 정보 검색
   ↓
6. LLM을 통한 커버레터 생성
   ↓
7. 결과 반환 및 편집 가능
```

## 📦 주요 라이브러리

### Frontend
| 라이브러리 | 버전 | 용도 |
|-----------|------|------|
| React | 18.x | UI 프레임워크 |
| CSS3 | - | 스타일링 |
| Fetch API | - | HTTP 통신 |

### Backend
| 라이브러리 | 버전 | 용도 |
|-----------|------|------|
| FastAPI | 0.104.x | 웹 프레임워크 |
| PyMuPDF | 1.23.x | PDF 파싱 |
| pdfplumber | 0.11.x | PDF 텍스트 추출 |
| SentenceTransformers | 3.2.x | 텍스트 임베딩 |
| ChromaDB | 0.5.x | 벡터 데이터베이스 |
| OpenAI | 1.57.x | LLM API |
| NumPy | ≥1.24.x | 수치 계산 |
| Pydantic | - | 데이터 검증 |

### AI & ML
| 라이브러리 | 용도 |
|-----------|------|
| LangChain | AI 파이프라인 |
| RAG | 검색 기반 생성 |
| Vector Embeddings | 의미적 검색 |

## 🚀 설치 및 실행

### 1. 저장소 클론
```bash
git clone <repository-url>
cd langchain_test
```

### 2. 백엔드 설정
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

```python
root 폴더에 models 폴더 만들어서 LLM 모델 가져다 놓아야 합니다.
```


### 3. 환경 변수 설정
```bash
# backend/.env 파일 생성
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. 백엔드 실행
```bash
cd backend
source venv/bin/activate
python main.py
```

### 5. 프론트엔드 실행
```bash
cd frontend
npm install
npm start
```

### 6. 접속
- 프론트엔드: http://localhost:3000
- 백엔드 API: http://localhost:8000

## 📋 API 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/upload-pdf` | POST | PDF 파일 업로드 및 텍스트 추출 |
| `/api/generate-cover-letter` | POST | AI 커버레터 생성 |
| `/api/debug-context` | POST | PDF 참조 상태 분석 |
| `/health` | GET | 서버 상태 확인 |

## 🎨 UI/UX 특징

- **📱 반응형 디자인**: 모바일, 태블릿, 데스크톱 모든 기기 지원
- **🎯 단일 페이지**: 모든 기능을 한 페이지에서 사용 가능
- **⚡ 실시간 피드백**: 즉시적인 사용자 피드백 제공
- **🎨 직관적 인터페이스**: 사용하기 쉬운 깔끔한 UI
- **💾 자동 저장**: 데이터 손실 방지를 위한 자동 저장 기능

## 🔧 개발 환경

- **OS**: macOS, Windows, Linux
- **Python**: 3.11+
- **Node.js**: 18+
- **npm**: 9+

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해주세요.

---

⭐ 이 프로젝트가 도움이 되었다면 스타를 눌러주세요!
