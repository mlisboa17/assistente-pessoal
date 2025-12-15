#!/usr/bin/env python3
"""
Script para executar o servidor do Assistente Pessoal
"""

import os
import sys

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from api_server import app

    print("🚀 Iniciando Assistente Pessoal - Servidor Flask")
    print("📊 Web Interface: http://localhost:5501")
    print("📋 Planilha de Normalização: http://localhost:5501/planilha-normalizacao")
    print("🔄 API Endpoint: POST /process")
    print("📈 Dashboard: http://localhost:5501/")
    print("")

    # Executar o servidor
    app.run(host='0.0.0.0', port=5501, debug=False)

except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Erro ao iniciar servidor: {e}")
    sys.exit(1)