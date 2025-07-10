# MiniVault API

A local REST API for text generation with comprehensive logging capabilities. Built as a complete offline solution with no external dependencies.

## Overview

This project provides a FastAPI-based REST API that accepts text prompts and returns generated responses. It includes optional local LLM integration through Ollama or Hugging Face Transformers, with intelligent fallbacks to dummy responses when models aren't available.

## Features

- REST API with `/generate` endpoint
- Complete request/response logging in JSONL format
- Local LLM support (Ollama + Transformers)
- Web-based testing interface with Gradio
- Automatic fallback to contextual dummy responses
- Health monitoring and status endpoints

## Quick Start

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)

### Installation

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the API

```bash
# Start the FastAPI server
python app.py
```

API will be available at `http://localhost:8000`

### Running the UI (Optional)

```bash
# Start the Gradio interface
python app_ui.py
```

Web interface will be available at `http://localhost:7860`

## API Endpoints

### POST /generate

Generate text from a prompt.

**Request:**
```json
{
  "prompt": "Your text prompt here"
}
```

**Response:**
```json
{
  "response": "Generated response text"
}
```

### GET /health

Check API status and LLM availability.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.123456",
  "local_llm_available": false,
  "ollama_available": true
}
```

## Local LLM Setup

### Option 1: Ollama (Recommended)

1. Install Ollama from https://ollama.ai/
2. Pull a model: `ollama pull llama2:7b`
3. Run the model: `ollama run llama2:7b`
4. Restart the API (it will auto-detect Ollama)

### Option 2: Hugging Face Transformers

Install transformers: `pip install transformers torch`

The API will automatically use `microsoft/DialoGPT-small` if Ollama isn't available.

### Fallback Behavior

Without local LLMs, the API returns contextual dummy responses based on prompt patterns.

## Logging

All interactions are logged to `logs/log.jsonl`:

```json
{
  "timestamp": "2024-01-15T10:30:00.123456",
  "prompt": "Hello, how are you?",
  "response": "Generated response text",
  "processing_time_ms": 125,
  "method": "ollama",
  "error": null
}
```

## Project Structure

```
minivault-api/
├── app.py               # FastAPI application
├── app_ui.py            # Gradio UI interface
├── logs/                # Auto-created log directory
│   └── log.jsonl        # Interaction logs
├── requirements.txt     # Dependencies
└── README.md           # This file
```

## Configuration

The API can be configured through environment variables:

```bash
export API_HOST="0.0.0.0"
export API_PORT="8000"
export OLLAMA_URL="http://localhost:11434"
```

## Testing

```bash
# Test the API with curl
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, world!"}'

# Check health
curl "http://localhost:8000/health"
```

## Troubleshooting

**Cannot connect to API**
- Ensure the FastAPI server is running: `python app.py`
- Check that port 8000 isn't in use

**Module not found errors**
- Activate your virtual environment
- Install dependencies: `pip install -r requirements.txt`

**Ollama not detected**
- Verify Ollama is running: `ollama list`
- Check the service is accessible: `curl http://localhost:11434/api/tags`

## Development

The codebase is structured for easy extension:

- `app.py`: Main FastAPI application with generation logic
- `app_ui.py`: Gradio interface for testing and interaction
- Comprehensive error handling and logging throughout
- Modular design for adding new LLM backends

## Dependencies

Core dependencies (see `requirements.txt`):
- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `gradio`: Web UI
- `requests`: HTTP client
- `pydantic`: Data validation

Optional for enhanced LLM support:
- `transformers`: Hugging Face models
- `torch`: PyTorch backend
