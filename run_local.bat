@echo off
set AI_ENABLED=1
set AI_BASE_URL=http://127.0.0.1:11434
set AI_MODEL=hf.co/mradermacher/Qwen3.5-4B-Kazakh-GGUF:Q4_K_M
set SEED_DEMO=1
python app.py
pause
