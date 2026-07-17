#!/bin/bash
set -e

echo "============================================"
echo "  AEGIS Lite — Environment Setup"
echo "============================================"

# 1. Install Python dependencies
echo "[1/4] Installing Python packages..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo "      ✓ Python packages installed"

# 2. Install Ollama
echo "[2/4] Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh > /dev/null 2>&1
echo "      ✓ Ollama installed"

# 3. Start Ollama server in background
echo "[3/4] Starting Ollama server..."
ollama serve &>/tmp/ollama.log &
sleep 5
echo "      ✓ Ollama server running"

# 4. Pull the LLM model
# NOTE: In Codespaces, we use a small model (phi3:mini ~2.3GB) for speed.
# For demo/finale you can swap to llama3:8b if you have a larger machine.
echo "[4/4] Pulling LLM model (phi3:mini — ~2.3GB, wait ~3 min)..."
ollama pull phi3:mini
echo "      ✓ Model ready"

# 5. Create data directories
mkdir -p data/db data/vectors

# 6. Create sample data
python demo/create_sample_data.py

echo ""
echo "============================================"
echo "  ✓ AEGIS Lite is ready!"
echo "  Run:  streamlit run ui/app.py"
echo "  Or:   python demo/demo.py"
echo "============================================"
