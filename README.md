# JobNova - AI Career Agent

JobNova is an enterprise-grade AI assistant that helps job seekers manage recruiter communications directly within LinkedIn.

## Features
- **Smart Analysis**: Detects recruiter intent (Blast vs. Personal).
- **Company Research**: Automatically fetches funding, news, and red flags (via Tavily/Search).
- **One-Click Reply**: Drafts professional replies tailored to your resume and desired tone.

## Architecture
- **Backend**: FastAPI (Python), Modular Architecture (`app/api`, `app/services`, `app/core`).
- **Frontend**: Chrome Extension (Manifest V3), LinkedIn DOM Injection.
- **Security**: API Key Authentication, Strict CORS, Pydantic Validation.

## Setup

### Backend
1.  Navigate to `backend/`.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Configure environment:
    - Edit `.env` to set your `OPENAI_API_KEY` and `TAVILY_API_KEY`.
    - Keep `HUNTFLOW_API_KEY` secret (will be used as `JobNova API Key`).
4.  Run server:
    ```bash
    uvicorn app.main:app --reload
    ```
    API will be available at `http://localhost:8000`.

### Extension
1.  Open Chrome and go to `chrome://extensions/`.
2.  Enable "Developer mode".
3.  Click "Load unpacked" and select the `extension/` folder.
4.  Copy the `HUNTFLOW_API_KEY` from `backend/.env`.
5.  Right-click the extension icon -> Options, and paste the key.
6.  Open LinkedIn Messages to see the "✨ AI Reply" button.

## Directory Structure
```
backend/
  app/
    api/v1/         # API Endpoints (REST)
    core/           # Config, Security, Logging
    services/       # Business Logic (LLM, Research)
    schemas/        # Data Models (Pydantic)
extension/          # Chrome Extension Source
```
