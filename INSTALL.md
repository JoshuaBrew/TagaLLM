# Run TagaLLM locally

The UI is static HTML, CSS and JavaScript. Download the repository ZIP from GitHub's Code menu or clone it with Git.

    git clone https://github.com/JoshuaBrew/TagaLLM.git
    cd TagaLLM

Install Python 3 and run this from the repository root to browse the research pages and chatbot interface.

    python -m http.server 8000 --bind 127.0.0.1

Open http://127.0.0.1:8000/. On Linux or macOS, use python3 if python is unavailable. Live local chat needs the services below.

## Exact evaluated chatbot

The evaluated app uses the base Google Gemma 4 E2B instruction model converted to GGUF and quantized as Q4_K_M. The exact file has SHA-256 1b71213c391f309cd3775c2fb489591d5806d2f2e59eccf6400d2b96f42fed47. SEA-LION v4.5 E2B IT Q4_K_M is used internally, with SHA-256 624a18a8cfc3d8ee29752200f73dc02f5007eaac408d94309e8d8da27b2a7ed9. Obtain the classifier from its publisher. The GGUF files embed their tokenizers. The exact Gemma conversion must be obtained or reproduced before this setup can match the evaluated artifacts.

Install a Gemma 4 compatible llama.cpp build. Use the commands below in separate terminals with the verified file paths. On Windows, invoke llama-server.exe by its full path if it is not on PATH. Keep the services bound to loopback.

    llama-server --model "PATH-TO-SEA-LION.gguf" --host 127.0.0.1 --port 19462 --ctx-size 4096 --parallel 1 --threads 6 --n-gpu-layers 0 --reasoning off --alias TagaLLM
    llama-server --model "PATH-TO-GEMMA.gguf" --host 127.0.0.1 --port 19468 --ctx-size 4096 --parallel 1 --threads 4 --n-gpu-layers 0 --reasoning off --alias TagaLLM
    python -X utf8 local/tagallm_local_chat.py --port 7864 --backend-port 19468 --scope-port 19462 --scope-guard --language-guard --system-prompt local/system-prompt.txt --culture-references local/tagallm-culture-references.json
    python -X utf8 local/serve.py

Open http://127.0.0.1:7866/ and try “Sino si Alex Eala?” Check ports 19462 and 19468 at /health if the model is unavailable. Close conflicting local services or reuse the existing evaluated processes. The two GGUF files need about 6.9 GB of storage combined. Both model processes used about 3.8 GiB combined resident memory in a local Windows snapshot. Allow additional memory for runtime buffers, other applications and the OS.

Model and runtime sources: [Google Gemma 4 E2B](https://huggingface.co/google/gemma-4-E2B-it), [AI Singapore classifier](https://huggingface.co/aisingapore/Gemma-SEA-LION-v4.5-E2B-IT-GGUF), [llama.cpp](https://github.com/ggml-org/llama.cpp).
