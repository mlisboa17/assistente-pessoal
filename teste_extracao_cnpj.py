#!/usr/bin/env python3
"""
Teste da extração de CNPJ do titular da conta
"""

import re

def _extrair_nome_e_documento(texto: str) -> tuple[str, str]:
    """Extrai nome e documento (CPF/CNPJ) de uma linha de texto

    Returns:
        tuple: (nome_limpo, documento)
    """
    # Primeiro tenta extrair CPF: 123.456.789-00
    cpf_match = re.search(r'\d{3}\.\d{3}\.\d{3}-\d{2}', texto)
    if cpf_match:
        documento = cpf_match.group(0)
        # Remove o documento e caracteres especiais do nome
        nome = re.sub(r'\d{3}\.\d{3}\.\d{3}-\d{2}', '', texto)
        nome = re.sub(r'[^A-Z\s]', '', nome).strip()
        return nome, documento

    # Depois tenta extrair CNPJ: 12.345.678/0001-23
    cnpj_match = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', texto)
    if cnpj_match:
        documento = cnpj_match.group(0)
        # Remove o documento e caracteres especiais do nome
        nome = re.sub(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', '', texto)
        nome = re.sub(r'[^A-Z\s]', '', nome).strip()
        return nome, documento

    # Se não encontrou documento, retorna apenas o nome limpo
    nome = re.sub(r'[^A-Z\s]', '', texto).strip()
    return nome, ""

# Testes
testes = [
    "EMPRESA XYZ LTDA 12.345.678/0001-23",
    "JOÃO SILVA 123.456.789-00",
    "MARIA EMPRESA S.A. 98.765.432/0001-10",
    "APENAS NOME SEM DOCUMENTO",
    "EMPRESA COM CPF 111.222.333-44 E OUTRAS INFO",
]

print("🧪 Teste da extração de CNPJ do titular:")
print("=" * 50)

for teste in testes:
    nome, documento = _extrair_nome_e_documento(teste)
    print(f"Texto: {teste}")
    print(f"Nome: '{nome}'")
    print(f"Documento: '{documento}'")
    print("-" * 30)