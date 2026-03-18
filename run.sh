#!/bin/bash
set -e

echo "──────────────────────────────────────────"
echo "  ArbiTrib — Calculadora Tributária MVP"
echo "──────────────────────────────────────────"

# Instala dependências se necessário
if ! python -c "import fastapi" 2>/dev/null; then
  echo "Instalando dependências..."
  pip install -q fastapi uvicorn[standard] pydantic
fi

echo "Iniciando servidor em http://localhost:8000"
echo "Pressione Ctrl+C para parar."
echo ""

cd "$(dirname "$0")/backend"
python main.py
