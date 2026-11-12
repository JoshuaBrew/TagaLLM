# Run 10 on Windows

## Add the source library

1. Download the GGUF to a folder of your choice, such as `C:/Models/Run10`.
2. Inside that folder, create a `source-library` subfolder.
3. Copy your local `sources-regional-preview-v104.json` into `source-library`. The Hugging Face folder contains setup notes. The evaluated 156-note JSON remains private.
4. Set `-SourceLibrary` to the path of the JSON file itself.

```text
Run10/
  tagallm-Q4_K_M.gguf
  source-library/
    sources-regional-preview-v104.json
```

## Start the app

From the repository root, run the following in PowerShell. Install Python and obtain a Gemma 4-compatible llama.cpp server. Keep the runtime DLLs beside the server executable.

```powershell
& ./local/run10/start.ps1 -RuntimePath 'C:/path/to/llama-server.exe' -ModelPath 'C:/Models/Run10/tagallm-Q4_K_M.gguf' -SourceLibrary 'C:/Models/Run10/source-library/sources-regional-preview-v104.json'
```

Open [the local chat](http://127.0.0.1:7879/). Try “Kumusta ka?” for conversation or “/ask Ano ang trabaho ng barangay?” for reference lookup. Follow up with “Saan galing yan?” to see the source. Press Ctrl+C in the terminal to stop the local servers.

The model is a 3,416,114,240-byte GGUF with SHA-256 `32d707dc209b5dcc217add78c4940d5f051494fbf4235167597385786039a6f9`. The evaluated source library is the v104 JSON with 156 notes. Download the [Run 10 GGUF](https://huggingface.co/JoshBrew/TagaLLM-Run-10/resolve/main/tagallm-Q4_K_M.gguf) from Hugging Face. The source library is pending redistribution review. The lookup-enabled launcher above requires a local copy of that library.
