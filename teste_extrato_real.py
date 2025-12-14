#!/usr/bin/env python3
"""Script para testar processamento de extrato real com todas as bibliotecas"""

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

async def testar_extrato_real():
    """Testa processamento de extrato real com todas as bibliotecas"""

    print("🧪 TESTANDO PROCESSAMENTO DE EXTRATO REAL")
    print("=" * 60)

    extratos = ExtratosModule()

    # Verifica bibliotecas disponíveis
    print("📚 Bibliotecas disponíveis:")
    try:
        import camelot
        print("  ✅ Camelot (extração de tabelas)")
    except ImportError:
        print("  ❌ Camelot")

    try:
        import fitz
        print("  ✅ PyMuPDF (processamento avançado)")
    except ImportError:
        print("  ❌ PyMuPDF")

    try:
        import tabula
        print("  ✅ Tabula (extração de tabelas)")
    except ImportError:
        print("  ❌ Tabula")

    try:
        import ofxparse
        print("  ✅ OFX Parse (arquivos bancários)")
    except ImportError:
        print("  ❌ OFX Parse")

    print()

    # Tenta encontrar arquivos PDF no diretório test_extratos
    test_dir = Path("test_extratos")
    pdf_files = list(test_dir.glob("*.pdf")) if test_dir.exists() else []

    if not pdf_files:
        print("❌ Nenhum arquivo PDF encontrado na pasta test_extratos")
        print("💡 Copie arquivos PDF de extrato para a pasta test_extratos")
        return

    print(f"📄 {len(pdf_files)} PDFs encontrados em test_extratos:")
    for i, pdf in enumerate(pdf_files, 1):
        print(f"  {i}. {pdf.name}")
    print()

    # Testa todos os arquivos automaticamente
    for arquivo_selecionado in pdf_files:
        print(f"\n🎯 Testando arquivo: {arquivo_selecionado.name}")
        print(f"   Caminho: {arquivo_selecionado.absolute()}")
        print(f"   Tamanho: {arquivo_selecionado.stat().st_size} bytes")
        print()

        # Testa processamento
        print("🔄 Processando extrato...")
        print("   Método: Extração avançada (Camelot → Tabula → PyMuPDF → Tradicional)")
        print()

        try:
            # Simula anexo como o WhatsApp faria
            anexo_simulado = {
                'file_name': arquivo_selecionado.name,
                'file_path': str(arquivo_selecionado.absolute()),
                'mime_type': 'application/pdf'
            }

            # Processa o extrato
            resultado = await extratos._processar_extrato_attachment(anexo_simulado, "teste_real")

            print("📊 RESULTADO DO PROCESSAMENTO:")
            print("-" * 40)

            if "Erro ao processar extrato" in resultado:
                print(f"❌ {resultado}")
            elif resultado.startswith("📄"):
                # É uma resposta de preview bem-sucedida
                print("✅ Processamento bem-sucedido!")
                print("📝 Preview gerado:")
                print(resultado[:500] + "..." if len(resultado) > 500 else resultado)
            else:
                print(f"📝 Resposta: {resultado}")

        except Exception as e:
            print(f"❌ Erro durante processamento: {e}")
            import traceback
            traceback.print_exc()

        print("\n" + "-" * 60)

    print("\n🏁 TODOS OS TESTES CONCLUÍDOS")

    print("\n💡 O sistema agora usa bibliotecas avançadas:")
    print("   • Camelot: Melhor para tabelas estruturadas")
    print("   • Tabula: Extração robusta de tabelas")
    print("   • PyMuPDF: Processamento de texto avançado")
    print("   • Método tradicional: Fallback confiável")

async def main():
    await testar_extrato_real()

if __name__ == "__main__":
    asyncio.run(main())