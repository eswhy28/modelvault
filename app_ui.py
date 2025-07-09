import gradio as gr
import requests
import json
import logging
from datetime import datetime
from typing import Dict, Any
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MiniVaultUI:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.app = None
        self._setup_interface()

    def _setup_interface(self):
        """Setup the Gradio interface"""

        # Custom CSS for better styling
        css = """
        .gradio-container {
            max-width: 800px !important;
            margin: auto !important;
        }

        .header {
            text-align: center;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 20px;
        }

        .status-indicator {
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 15px;
            font-weight: bold;
        }

        .status-healthy {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }

        .status-error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }

        .footer {
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 14px;
        }
        """

        # Create the interface
        with gr.Blocks(css=css, title="MiniVault API Interface") as self.app:
            # Header
            gr.HTML("""
            <div class="header">
                <h1>🔐 MiniVault API Interface</h1>
                <p>Local text generation with logging capabilities</p>
            </div>
            """)

            # Status indicator
            status_display = gr.HTML(self._get_status_html())

            # Main interface
            with gr.Row():
                with gr.Column(scale=2):
                    # Input section
                    gr.Markdown("### 💬 Input")
                    prompt_input = gr.Textbox(
                        label="Enter your prompt",
                        placeholder="Type your message here...",
                        lines=3,
                        max_lines=10
                    )

                    # Controls
                    with gr.Row():
                        submit_btn = gr.Button("🚀 Generate", variant="primary")
                        clear_btn = gr.Button("🗑️ Clear", variant="secondary")
                        refresh_status_btn = gr.Button("🔄 Refresh Status")

                with gr.Column(scale=2):
                    # Output section
                    gr.Markdown("### 🤖 Response")
                    response_output = gr.Textbox(
                        label="Generated response",
                        lines=5,
                        max_lines=15,
                        interactive=False
                    )

                    # Metrics
                    with gr.Row():
                        processing_time = gr.Textbox(
                            label="Processing Time",
                            value="Not processed yet",
                            interactive=False,
                            scale=1
                        )
                        generation_method = gr.Textbox(
                            label="Method",
                            value="Unknown",
                            interactive=False,
                            scale=1
                        )

            # Examples section
            gr.Markdown("### 📝 Example Prompts")
            examples = gr.Examples(
                examples=[
                    ["Hello, how are you today?"],
                    ["What is the meaning of life?"],
                    ["Write a short story about a robot."],
                    ["Explain quantum computing in simple terms."],
                    ["Create a recipe for chocolate chip cookies."]
                ],
                inputs=prompt_input,
                label="Click on any example to try it out"
            )

            # Logs section
            with gr.Accordion("📊 Recent Interactions", open=False):
                logs_display = gr.Textbox(
                    label="Recent logs",
                    lines=10,
                    max_lines=20,
                    interactive=False
                )
                refresh_logs_btn = gr.Button("🔄 Refresh Logs")

            # Footer
            gr.HTML("""
            <div class="footer">
                <p>MiniVault API - Local text generation with comprehensive logging</p>
                <p>🏠 <strong>Running locally</strong> | 🔒 <strong>No cloud APIs</strong> | 📝 <strong>Full logging</strong></p>
            </div>
            """)

            # Event handlers
            submit_btn.click(
                fn=self._generate_response,
                inputs=[prompt_input],
                outputs=[response_output, processing_time, generation_method]
            )

            clear_btn.click(
                fn=lambda: ("", "", "Not processed yet", "Unknown"),
                outputs=[prompt_input, response_output, processing_time, generation_method]
            )

            refresh_status_btn.click(
                fn=self._get_status_html,
                outputs=[status_display]
            )

            refresh_logs_btn.click(
                fn=self._get_recent_logs,
                outputs=[logs_display]
            )

            # Auto-refresh status on load
            self.app.load(
                fn=self._get_status_html,
                outputs=[status_display]
            )

    def _generate_response(self, prompt: str) -> tuple:
        """Generate response via API call"""

        if not prompt.strip():
            return "Please enter a prompt first.", "0ms", "None"

        try:
            start_time = time.time()

            # Make API call
            response = requests.post(
                f"{self.api_url}/generate",
                json={"prompt": prompt},
                timeout=30
            )

            processing_time = f"{int((time.time() - start_time) * 1000)}ms"

            if response.status_code == 200:
                result = response.json()
                generated_text = result.get("response", "No response generated")

                # Get method from health check
                method = self._get_generation_method()

                return generated_text, processing_time, method
            else:
                error_msg = f"API Error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return f"Error: {error_msg}", processing_time, "Error"

        except requests.exceptions.ConnectionError:
            return "❌ Cannot connect to API. Make sure the FastAPI server is running on http://localhost:8000", "0ms", "Error"
        except requests.exceptions.Timeout:
            return "⏱️ Request timed out. The API might be processing a complex request.", "30000ms+", "Timeout"
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return f"❌ Unexpected error: {str(e)}", "0ms", "Error"

    def _get_status_html(self) -> str:
        """Get API status and return HTML"""

        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)

            if response.status_code == 200:
                health_data = response.json()

                status_class = "status-healthy"
                status_text = "🟢 API is healthy and running"

                # Add LLM status
                llm_status = ""
                if health_data.get("ollama_available"):
                    llm_status = " | 🦙 Ollama available"
                elif health_data.get("local_llm_available"):
                    llm_status = " | 🤗 HuggingFace model loaded"
                else:
                    llm_status = " | 🔧 Using dummy responses"

                timestamp = health_data.get("timestamp", "Unknown")

                return f"""
                <div class="{status_class}">
                    {status_text}{llm_status}
                    <br><small>Last checked: {timestamp}</small>
                </div>
                """
            else:
                return f"""
                <div class="status-error">
                    🔴 API returned error: {response.status_code}
                </div>
                """

        except requests.exceptions.ConnectionError:
            return """
            <div class="status-error">
                🔴 Cannot connect to API (http://localhost:8000)
                <br><small>Make sure the FastAPI server is running: <code>python app.py</code></small>
            </div>
            """
        except Exception as e:
            return f"""
            <div class="status-error">
                🔴 Status check failed: {str(e)}
            </div>
            """

    def _get_generation_method(self) -> str:
        """Get the current generation method"""

        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()

                if health_data.get("ollama_available"):
                    return "🦙 Ollama"
                elif health_data.get("local_llm_available"):
                    return "🤗 HuggingFace"
                else:
                    return "🔧 Dummy"
            else:
                return "❓ Unknown"

        except Exception:
            return "❓ Unknown"

    def _get_recent_logs(self) -> str:
        """Get recent logs from the log file"""

        try:
            with open("logs/log.jsonl", "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Get last 10 entries
            recent_lines = lines[-10:] if len(lines) > 10 else lines

            if not recent_lines:
                return "No logs available yet. Make some requests to see logs here."

            # Format logs for display
            formatted_logs = []
            for line in recent_lines:
                try:
                    log_entry = json.loads(line.strip())
                    timestamp = log_entry.get("timestamp", "Unknown")
                    prompt = log_entry.get("prompt", "")[:50]
                    response = log_entry.get("response", "")[:50]
                    method = log_entry.get("method", "unknown")
                    processing_time = log_entry.get("processing_time_ms", 0)

                    formatted_logs.append(
                        f"[{timestamp}] {method} ({processing_time}ms)\n"
                        f"  Prompt: {prompt}...\n"
                        f"  Response: {response}...\n"
                    )
                except json.JSONDecodeError:
                    continue

            return "\n".join(formatted_logs)

        except FileNotFoundError:
            return "Log file not found. The API hasn't logged any interactions yet."
        except Exception as e:
            return f"Error reading logs: {str(e)}"

    def launch(self, **kwargs):
        """Launch the Gradio app"""

        default_kwargs = {
            "server_name": "0.0.0.0",
            "server_port": 7860,
            "share": False,
            "debug": False
        }

        # Merge with provided kwargs
        launch_kwargs = {**default_kwargs, **kwargs}

        logger.info(f"Launching Gradio interface on http://localhost:{launch_kwargs['server_port']}")

        return self.app.launch(**launch_kwargs)


# Main execution
if __name__ == "__main__":
    # Initialize and launch the UI
    ui = MiniVaultUI()

    print("🚀 Starting MiniVault UI...")
    print("📱 Open your browser to: http://localhost:7860")
    print("🔗 Make sure the FastAPI server is running on: http://localhost:8000")
    print("⚡ Press Ctrl+C to stop the server")

    # Launch with auto-reload for development
    ui.launch(
        share=False,
        debug=True,
        show_error=True,
        quiet=False
    )