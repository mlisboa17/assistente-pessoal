#!/usr/bin/env python3
"""Debug detalhado da extração BB"""

import sys
import os
import re
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.extratos import ExtratosModule

def debug_extracao_bb():
    # Extrai texto do PDF
    extratos = ExtratosModule()

    # Simula o caminho do arquivo
    arquivo_path = "test_extratos/BancoBrasil_Real_Novembro2025.pdf"

    print("🔍 DEBUG DA EXTRAÇÃO BANCO DO BRASIL")
    print("=" * 60)

    # Extrai texto
    texto = extratos._extrair_texto_pdf(arquivo_path)
    print(f"📄 Texto extraído ({len(texto)} caracteres):")
    print("-" * 40)
    print(texto[:1000] + "..." if len(texto) > 1000 else texto)
    print("-" * 40)

    # Identifica banco
    banco = extratos._identificar_banco(texto, arquivo_path)
    print(f"🏦 Banco identificado: {banco}")

    # Testa extração
    print("\n🔄 Testando extração BB...")
    dados = extratos._extrair_bb(texto)

    print(f"📊 Dados extraídos:")
    print(f"  - Conta: {dados.get('conta', 'N/A')}")
    print(f"  - Agência: {dados.get('agencia', 'N/A')}")
    print(f"  - Período: {dados.get('periodo', 'N/A')}")
    print(f"  - Saldo Anterior: {dados.get('saldo_anterior', 'N/A')}")
    print(f"  - Saldo Atual: {dados.get('saldo_atual', 'N/A')}")
    print(f"  - Transações encontradas: {len(dados.get('transacoes', []))}")

    # Mostra primeiras linhas do texto para análise
    print("\n📝 Primeiras 20 linhas do texto:")
    linhas = texto.split('\n')
    for i, linha in enumerate(linhas[:20]):
        print("2")

    # Testa padrões de regex
    print("\n🔍 Testando padrões de regex:")

    # Padrão BB específico
    padrao_bb = r'^(\d{2}/\d{2}/\d{4})\s+\d+\s+\d+\s+(.+?)\s+([\d.,]+)\s*(\(\+\)|\(\-\))$'
    print(f"Padrão BB: {padrao_bb}")

    matches_bb = []
    for linha in linhas:
        linha = linha.strip()
        if re.search(padrao_bb, linha):
            matches_bb.append(linha)
            if len(matches_bb) >= 5:  # Mostra até 5 matches
                break

    print(f"Matches encontrados com padrão BB: {len(matches_bb)}")
    for i, match in enumerate(matches_bb[:5]):
        print(f"  {i+1}. {match}")

    # Outros padrões
    padroes = [
        (r'^(\d{2}/\d{2})\s+(.+?)\s+R\$\s*([\d.,-]+)$', "Padrão 1"),
        (r'^(\d{2}/\d{2})\s+(.+?)\s+([\d.,-]+)$', "Padrão 2"),
        (r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+R\$\s*([\d.,-]+)$', "Padrão 3"),
        (r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d.,-]+)$', "Padrão 4"),
    ]

    for padrao, nome in padroes:
        matches = []
        for linha in linhas:
            linha = linha.strip()
            if re.search(padrao, linha):
                matches.append(linha)
                if len(matches) >= 3:
                    break
        print(f"{nome}: {len(matches)} matches")
        for match in matches[:3]:
            print(f"  - {match}")

if __name__ == "__main__":
    debug_extracao_bb()