# XBot - X.com Automation System

## Quick Start

### 1. Install Python Dependencies
```bash
cd active
pip install -r requirements.txt
```

### 2. Set Groq API Key
```bash
set GROQ_API_KEY=your_api_key_here
```

### 3. Start the Brain Server
```bash
cd active
python server.py
# Or: uvicorn server:app --reload --port 8000
```

### 4. Install Tampermonkey Script
1. Install Tampermonkey extension in Chrome
2. Create new script
3. Copy contents of `xbot_client.js`
4. Save and enable

### 5. Run the Bot
1. Open x.com in Chrome
2. Click "Start Bot" in the XBot Control panel (bottom-right)

## Architecture
- **`server.py`**: Python Brain (FastAPI + Groq + SQLite)
- **`xbot_client.js`**: Browser Body (Tampermonkey)
- **`intelligence.md`**: Complete operational blueprint

## API Endpoints
- `GET /schedule`: Current target region & keywords
- `POST /analyze`: Analyze tweet & generate reply
- `POST /update-trends`: Update regional trends
- `GET /stats`: Bot statistics
