#!/usr/bin/env python3
"""Teste simples de um arquivo de extrato"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Configura logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Adiciona o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.extratos import ExtratosModule

async def testar_arquivo(arquivo_path):
    """Testa um arquivo específico"""
    print(f"🧪 Testando: {arquivo_path}")
    print("=" * 60)

    extratos = ExtratosModule()

    # Simula anexo
    anexo_simulado = {
        'file_name': Path(arquivo_path).name,
        'file_path': arquivo_path,
        'mime_type': 'application/pdf'
    }

    try:
        resultado = await extratos._processar_extrato_attachment(anexo_simulado, "teste")
        print("📊 RESULTADO:")
        print(resultado)
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python teste_simples.py <caminho_do_arquivo>")
        sys.exit(1)

    arquivo = sys.argv[1]
    if not os.path.exists(arquivo):
        print(f"Arquivo não encontrado: {arquivo}")
        sys.exit(1)

    asyncio.run(testar_arquivo(arquivo))