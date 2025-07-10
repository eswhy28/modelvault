import os
import json
import logging
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Optional imports for local LLM integration
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM

    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

try:
    import requests

    HAS_OLLAMA = True
except ImportError:
    HAS_OLLAMA = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Pydantic models for request/response validation
class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10000, description="Input prompt for generation")


class GenerateResponse(BaseModel):
    response: str = Field(..., description="Generated response")


class MiniVaultAPI:
    def __init__(self):
        self.app = FastAPI(
            title="MiniVault API",
            description="A local REST API for text generation with logging capabilities",
            version="1.0.0"
        )

        # Setup CORS for Gradio integration
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Initialize logs directory
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        self.log_file = self.logs_dir / "log.jsonl"

        # Initialize local LLM (optional)
        self.local_llm = None
        self.ollama_available = False
        self._initialize_local_llm()

        # Setup routes
        self._setup_routes()

        logger.info("MiniVault API initialized successfully")

    def _initialize_local_llm(self):
        """Initialize local LLM if available (Hugging Face Transformers or Ollama)"""

        # Try to initialize Ollama first (more efficient for local deployment)
        if HAS_OLLAMA:
            try:
                # Check if Ollama is running
                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                if response.status_code == 200:
                    self.ollama_available = True
                    logger.info("Ollama detected and available")
                    return
            except Exception as e:
                logger.info(f"Ollama not available: {e}")

        # Fallback to Hugging Face Transformers
        if HAS_TRANSFORMERS:
            try:
                # Use a lightweight model for demonstration
                model_name = "microsoft/DialoGPT-small"
                logger.info(f"Loading Hugging Face model: {model_name}")

                # Initialize the text generation pipeline
                self.local_llm = pipeline(
                    "text-generation",
                    model=model_name,
                    tokenizer=model_name,
                    max_length=100,
                    do_sample=True,
                    temperature=0.7,
                    pad_token_id=50256  # GPT-2 pad token
                )
                logger.info("Local LLM initialized successfully")

            except Exception as e:
                logger.warning(f"Failed to initialize local LLM: {e}")
                self.local_llm = None
        else:
            logger.info("Transformers not available, using dummy responses only")

    def _setup_routes(self):
        """Setup FastAPI routes"""

        @self.app.get("/")
        async def root():
            return {
                "message": "MiniVault API",
                "version": "1.0.0",
                "endpoints": {
                    "generate": "/generate",
                    "health": "/health"
                }
            }

        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "local_llm_available": self.local_llm is not None,
                "ollama_available": self.ollama_available
            }

        @self.app.post("/generate", response_model=GenerateResponse)
        async def generate(request: GenerateRequest):
            return await self._generate_response(request)

    async def _generate_response(self, request: GenerateRequest) -> GenerateResponse:
        """Main generation logic with logging"""

        start_time = datetime.now()
        prompt = request.prompt.strip()

        try:
            # Generate response using available method
            if self.ollama_available:
                response_text = await self._generate_with_ollama(prompt)
            elif self.local_llm:
                response_text = await self._generate_with_transformers(prompt)
            else:
                response_text = self._generate_dummy_response(prompt)

            # Log the interaction
            await self._log_interaction(prompt, response_text, start_time)

            return GenerateResponse(response=response_text)

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            # Fallback to dummy response
            response_text = self._generate_dummy_response(prompt)
            await self._log_interaction(prompt, response_text, start_time, error=str(e))
            return GenerateResponse(response=response_text)

    async def _generate_with_ollama(self, prompt: str) -> str:
        """Generate response using Ollama"""
        try:
            payload = {
                "model": "llama2:7b",  # Default model, can be configured
                "prompt": prompt,
                "stream": False
            }

            response = requests.post(
                "http://localhost:11434/api/generate",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "No response generated")
            else:
                raise Exception(f"Ollama API error: {response.status_code}")

        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise

    async def _generate_with_transformers(self, prompt: str) -> str:
        """Generate response using Hugging Face Transformers"""
        try:
            # Generate response
            outputs = self.local_llm(
                prompt,
                max_length=len(prompt.split()) + 50,  # Adaptive length
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=50256
            )

            generated_text = outputs[0]['generated_text']

            # Extract only the new generated part
            response_text = generated_text[len(prompt):].strip()

            if not response_text:
                response_text = "I understand your prompt, but I couldn't generate a meaningful response."

            return response_text

        except Exception as e:
            logger.error(f"Transformers generation failed: {e}")
            raise

    def _generate_dummy_response(self, prompt: str) -> str:
        """Generate a contextual dummy response"""

        # Simple keyword-based responses for better demo experience
        prompt_lower = prompt.lower()

        if any(word in prompt_lower for word in ['hello', 'hi', 'hey']):
            return "Hello! This is a stubbed response from MiniVault API. How can I help you today?"
        elif any(word in prompt_lower for word in ['what', 'how', 'why', 'when', 'where']):
            return f"This is a stubbed response to your question: '{prompt[:50]}...'. In a real implementation, I would provide a detailed answer."
        elif any(word in prompt_lower for word in ['write', 'create', 'generate']):
            return f"This is a stubbed creative response. In a real implementation, I would generate content based on: '{prompt[:50]}...'"
        else:
            return f"This is a stubbed response from MiniVault API. Your prompt was: '{prompt[:50]}...'"

    async def _log_interaction(self, prompt: str, response: str, start_time: datetime, error: str = None):
        """Log interaction to JSONL file"""

        log_entry = {
            "timestamp": start_time.isoformat(),
            "prompt": prompt,
            "response": response,
            "processing_time_ms": int((datetime.now() - start_time).total_seconds() * 1000),
            "method": "ollama" if self.ollama_available else "transformers" if self.local_llm else "dummy",
            "error": error
        }

        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

            logger.info(f"Logged interaction: {len(prompt)} chars -> {len(response)} chars")

        except Exception as e:
            logger.error(f"Failed to log interaction: {e}")


# Initialize the API
api = MiniVaultAPI()
app = api.app

# Main execution
if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )