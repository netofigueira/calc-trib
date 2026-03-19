#!/bin/bash
set -e

echo "──────────────────────────────────────────"
echo "  ArbiTrib — Compartilhar via ngrok"
echo "──────────────────────────────────────────"

# Verifica se ngrok está instalado
if ! command -v ngrok &> /dev/null; then
  echo "ngrok não encontrado. Instale com: brew install ngrok"
  exit 1
fi

# Inicia o servidor em background
echo "Iniciando servidor local na porta 8000..."
cd "$(dirname "$0")/backend"
python main.py &
SERVER_PID=$!

# Espera o servidor subir
sleep 5

echo "Abrindo túnel ngrok..."
echo "Pressione Ctrl+C para parar tudo."
echo ""

# Ao sair, mata o servidor
trap "kill $SERVER_PID 2>/dev/null; echo ''; echo 'Servidor parado.'" EXIT

ngrok http 8001
