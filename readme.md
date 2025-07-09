# 🔐 MiniVault API

A local REST API for text generation with comprehensive logging capabilities, built for the ModelVault Take-Home assessment.

## 🚀 Features

- **FastAPI REST API** with `/generate` endpoint
- **Comprehensive logging** of all interactions in JSON Lines format
- **Optional local LLM integration** (Hugging Face Transformers or Ollama)
- **Modern Gradio UI** for easy testing and interaction
- **Graceful fallbacks** to dummy responses when LLM unavailable
- **Production-ready** with proper error handling and validation

## 📁 Project Structure

```
minivault-api/
├── app.py               # FastAPI application
├── app_ui.py            # Gradio UI interface
├── logs/                # Auto-created directory
│   └── log.jsonl        # Interaction logs
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## 🛠️ Quick Setup

### 1. Create Virtual Environment

```bash
# Create virtual environment
python -m venv minivault-env

# Activate virtual environment
# On Windows:
minivault-env\Scripts\activate
# On macOS/Linux:
source minivault-env/bin/activate
```

### 2. Install Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Or install minimal dependencies (dummy responses only)
pip install fastapi uvicorn gradio requests python-multipart
```

### 3. Run the API Server

```bash
# Start the FastAPI server
python app.py

# Or use uvicorn directly
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at: **http://localhost:8000**

### 4. Run the Gradio UI (Optional)

```bash
# In a new terminal (with virtual environment activated)
python app_ui.py
```

The UI will be available at: **http://localhost:7860**

## 📡 API Usage

### POST /generate

Generate text based on a prompt.

**Request:**
```json
{
  "prompt": "Hello, how are you?"
}
```

**Response:**
```json
{
  "response": "This is a stubbed response from MiniVault API. How can I help you today?"
}
```

### GET /health

Check API health and LLM availability.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.123456",
  "local_llm_available": false,
  "ollama_available": false
}
```

### API Testing Examples

```bash
# Test with curl
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, world!"}'

# Test health endpoint
curl "http://localhost:8000/health"
```

## 🤖 Local LLM Integration

The API supports two methods for local LLM integration:

### Option 1: Ollama (Recommended)

1. Install Ollama: https://ollama.ai/
2. Pull a model: `ollama pull llama2`
3. Start Ollama: `ollama serve`
4. Restart the API - it will auto-detect Ollama

### Option 2: Hugging Face Transformers

The API will automatically use `microsoft/DialoGPT-small` if:
- Transformers is installed (`pip install transformers torch`)
- Ollama is not available
- Sufficient system resources are available

### Fallback Behavior

If neither LLM option is available, the API uses intelligent dummy responses based on prompt keywords.

## 📊 Logging System

All interactions are logged to `logs/log.jsonl` in JSON Lines format:

```json
{
  "timestamp": "2024-01-15T10:30:00.123456",
  "prompt": "Hello, how are you?",
  "response": "This is a stubbed response...",
  "processing_time_ms": 125,
  "method": "dummy",
  "error": null
}
```

### Log Analysis

```bash
# View recent logs
tail -f logs/log.jsonl

# Count total interactions
wc -l logs/log.jsonl

# Extract prompts only
jq -r '.prompt' logs/log.jsonl
```

## 🎨 Gradio UI Features

The web interface provides:

- **Real-time API testing** with prompt input and response display
- **API health monitoring** with LLM availability status
- **Example prompts** for quick testing
- **Recent logs viewer** for debugging
- **Processing metrics** (time, method used)
- **Responsive design** that works on desktop and mobile

## 🔧 Configuration Options

### Environment Variables

```bash
# API Configuration
export API_HOST="0.0.0.0"
export API_PORT="8000"

# UI Configuration
export UI_HOST="0.0.0.0"
export UI_PORT="7860"

# LLM Configuration
export OLLAMA_URL="http://localhost:11434"
export HF_MODEL="microsoft/DialoGPT-small"
```

### Customization

- **Change dummy responses:** Edit `_generate_dummy_response()` in `app.py`
- **Adjust LLM model:** Modify `model_name` in `_initialize_local_llm()`
- **Customize UI:** Edit CSS and components in `app_ui.py`
- **Add new endpoints:** Extend the FastAPI routes in `app.py`

## 🚨 Troubleshooting

### Common Issues

1. **"Cannot connect to API"**
   - Ensure FastAPI server is running: `python app.py`
   - Check port 8000 is not in use: `netstat -an | grep 8000`

2. **"Module not found" errors**
   - Activate virtual environment
   - Install dependencies: `pip install -r requirements.txt`

3. **LLM not loading**
   - Check available memory (>2GB recommended)
   - Verify transformers installation: `pip install transformers torch`

4. **Slow responses**
   - LLM loading takes time on first request
   - Use dummy responses for fastest testing

### Performance Tips

- Use Ollama for production deployments
- Increase `max_length` in transformers for longer responses
- Monitor system resources when using local LLMs
- Consider GPU acceleration for larger models

## 🔒 Security & Privacy

- **Local-only:** No external API calls or data transmission
- **Privacy-first:** All data stays on your machine
- **Logged interactions:** Review `logs/log.jsonl` for audit trail
- **No authentication:** Add auth middleware for production use

## 📈 Trade-offs Analysis

### Local LLM vs. Dummy Responses