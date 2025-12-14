#!/usr/bin/env python3
"""Script de teste das bibliotecas avançadas de processamento de PDFs"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.extratos import ExtratosModule

def testar_bibliotecas_avancadas():
    """Testa as bibliotecas avançadas de processamento de PDFs"""

    print("🧪 TESTANDO BIBLIOTECAS AVANÇADAS")
    print("=" * 50)

    extratos = ExtratosModule()

    # Verifica disponibilidade das bibliotecas
    print("📚 Verificando bibliotecas:")
    try:
        import camelot
        print("  Camelot: ✅")
    except ImportError:
        print("  Camelot: ❌")

    try:
        import fitz
        print("  PyMuPDF: ✅")
    except ImportError:
        print("  PyMuPDF: ❌")

    try:
        import ofxparse
        print("  OFX Parse: ✅")
    except ImportError:
        print("  OFX Parse: ❌")

    try:
        import tabula
        print("  Tabula: ✅")
    except ImportError:
        print("  Tabula: ❌")
    print()

    # Testa método de extração avançada com arquivo inexistente (deve falhar graciosamente)
    print("🔧 Testando método de extração avançada...")

    try:
        dados = extratos._extrair_dados_pdf_avancado("arquivo_inexistente.pdf", "banco_do_brasil")
        print(f"✅ Método executado sem erro. Transações encontradas: {len(dados['transacoes'])}")
    except Exception as e:
        print(f"❌ Erro no método: {e}")

    print("\n" + "=" * 50)
    print("🏁 TESTE CONCLUÍDO")

    print("\n💡 As bibliotecas avançadas foram integradas ao sistema!")
    print("   Agora o processamento tenta usar:")
    print("   1. Camelot (extração de tabelas)")
    print("   2. Tabula (extração de tabelas)")
    print("   3. PyMuPDF (texto estruturado)")
    print("   4. Método tradicional (fallback)")

if __name__ == "__main__":
    testar_bibliotecas_avancadas()