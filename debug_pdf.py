#!/usr/bin/env python3
"""Extrai texto de PDF para debug usando pdfplumber"""

import pdfplumber

def extrair_texto_pdf(arquivo_path):
    with pdfplumber.open(arquivo_path) as pdf:
        texto = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                texto += page_text + "\n"
    return texto

if __name__ == "__main__":
    arquivo = "test_extratos/BancoBrasil_Real_Novembro2025.pdf"
    texto = extrair_texto_pdf(arquivo)
    print("TEXTO EXTRAÍDO DO PDF (pdfplumber):")
    print("=" * 50)
    print(texto[:2000])
    print("=" * 50)
    print(f"Total de caracteres: {len(texto)}")

    # Verifica padrões
    import re
    bb_patterns = [
        r'BANCO DO BRASIL', r'Banco do Brasil', r'BB',
        r'www\.bb\.com\.br', r'001'
    ]
    print("\nVERIFICANDO PADRÕES BANCO DO BRASIL:")
    for pattern in bb_patterns:
        if re.search(pattern.upper(), texto.upper()):
            print(f"Encontrado: {pattern}")
        else:
            print(f"Nao encontrado: {pattern}")

    # Check for transaction lines
    print("\nPROCURANDO LINHAS DE TRANSAÇÃO:")
    linhas = texto.split('\n')
    for i, linha in enumerate(linhas[:30]):
        if re.search(r'\d{2}/\d{2}/\d{4}', linha):
            print(f"Linha {i}: {linha.strip()}")