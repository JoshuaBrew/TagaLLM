# Run TagaLLM locally

The [public chat page](https://joshuabrew.github.io/TagaLLM/) is a visual preview only. It has no model backend and cannot reply. The [GitHub ZIP](https://github.com/JoshuaBrew/TagaLLM/archive/refs/heads/main.zip) includes the same chat interface and the local Python services. Extract it and open a terminal in the extracted TagaLLM-main folder, or clone the repository with Git:

    git clone https://github.com/JoshuaBrew/TagaLLM.git
    cd TagaLLM

Install Python 3 and run this from the repository root to browse the research pages and chatbot interface.

    python -m http.server 8000 --bind 127.0.0.1

Open http://127.0.0.1:8000/. On Linux or macOS, use python3 if python is unavailable. Live local chat needs the services below.

## Run the local chatbot

Download the [evaluated Gemma 4 E2B Q4_K_M GGUF](https://huggingface.co/JoshBrew/TagaLLM-Gemma-4-E2B/resolve/main/TagaLLM-Gemma-4-E2B-Q4_K_M.gguf). The 3.43 GB file includes its tokenizer. Its SHA-256 is `1b71213c391f309cd3775c2fb489591d5806d2f2e59eccf6400d2b96f42fed47`.

Install a Gemma 4 compatible [llama.cpp build](https://github.com/ggml-org/llama.cpp/releases). The Windows CPU commands below were tested with build b12224. Run each command in a separate terminal from the extracted or cloned repository folder, and leave all three running. On Linux or macOS, substitute python3 if needed. Replace the GGUF path with your downloaded file. On Windows, use the full path to llama-server.exe if it is not on PATH.

    llama-server --model "PATH-TO-GEMMA.gguf" --host 127.0.0.1 --port 19468 --ctx-size 4096 --parallel 1 --threads 4 --n-gpu-layers 0 --reasoning off --alias TagaLLM
    python -X utf8 local/tagallm_local_chat.py --port 7864 --backend-port 19468 --system-prompt local/system-prompt.txt --culture-references local/tagallm-culture-references.json
    python -X utf8 local/serve.py

Open http://127.0.0.1:7866/ for the working local UI and try “Sino si Alex Eala?” If the model is unavailable, check http://127.0.0.1:19468/health and confirm both Python services are running.

The research evaluation used a separate SEA-LION classifier for language and scope checks. The setup above runs the UI with Gemma alone, so it does not reproduce those checks. See the [evaluation evidence](../evidence.html) for details.
