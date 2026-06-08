#!/bin/bash
# Startup script for the Agentic AI Intelligent Loan Approval System

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo " Agentic AI Intelligent Loan Approval System"
echo "========================================"
echo ""

if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found. Creating template..."
    echo "ANTHROPIC_API_KEY=your_anthropic_api_key_here" > .env
fi

if grep -q "your_anthropic_api_key_here" .env; then
    echo "WARNING: ANTHROPIC_API_KEY is not set in .env file."
    echo "Please edit .env and add your Anthropic API key."
    echo ""
fi

source .env 2>/dev/null || true

echo "[1/2] Starting FastAPI microservice on http://localhost:8000 ..."
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
FASTAPI_PID=$!
echo "FastAPI PID: $FASTAPI_PID"

sleep 3

echo ""
echo "[2/2] Starting Streamlit UI on http://localhost:8501 ..."
~/.local/bin/streamlit run ui/app.py --server.port 8501 --server.address 0.0.0.0 &
STREAMLIT_PID=$!
echo "Streamlit PID: $STREAMLIT_PID"

echo ""
echo "========================================"
echo " System is running!"
echo "========================================"
echo " FastAPI:   http://localhost:8000"
echo " API Docs:  http://localhost:8000/docs"
echo " Streamlit: http://localhost:8501"
echo "========================================"
echo ""
echo "Press Ctrl+C to stop all services."
echo ""

trap "echo 'Shutting down...'; kill $FASTAPI_PID $STREAMLIT_PID 2>/dev/null; exit 0" INT TERM

wait
