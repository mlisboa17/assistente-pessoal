#!/usr/bin/env python3
"""
Demonstração da extração de CNPJ do titular da conta
"""

# Simula um texto de extrato bancário com CNPJ
texto_exemplo = """
EXTRATO BANCÁRIO - BANCO DO BRASIL

TITULAR: EMPRESA XYZ LTDA 12.345.678/0001-23
CONTA: 12345-6
AGÊNCIA: 1234

DATA       HISTÓRICO                                      VALOR
01/12      SALDO ANTERIOR                               1000.00
02/12      PIX RECEBIDO EMPRESA ABC                    500.00
03/12      TED ENVIADO FORNECEDOR                      -200.00
"""

# Importa a lógica do módulo
import sys
import os
sys.path.append(os.path.dirname(__file__))

# Simula a chamada do método
def _extrair_nome_e_documento(texto: str):
    import re
    # Primeiro tenta extrair CPF: 123.456.789-00
    cpf_match = re.search(r'\d{3}\.\d{3}\.\d{3}-\d{2}', texto)
    if cpf_match:
        documento = cpf_match.group(0)
        nome = re.sub(r'\d{3}\.\d{3}\.\d{3}-\d{2}', '', texto)
        nome = re.sub(r'[^A-Z\s]', '', nome).strip()
        return nome, documento

    # Depois tenta extrair CNPJ: 12.345.678/0001-23
    cnpj_match = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', texto)
    if cnpj_match:
        documento = cnpj_match.group(0)
        nome = re.sub(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', '', texto)
        nome = re.sub(r'[^A-Z\s]', '', nome).strip()
        return nome, documento

    nome = re.sub(r'[^A-Z\s]', '', texto).strip()
    return nome, ""

print("📄 Exemplo de Extrato Bancário:")
print("=" * 50)
print(texto_exemplo)

# Extrai o titular
linha_titular = ""
for linha in texto_exemplo.split('\n'):
    if 'TITULAR:' in linha.upper():
        linha_titular = linha.split(':', 1)[1].strip()
        break

if linha_titular:
    nome, documento = _extrair_nome_e_documento(linha_titular)
    print("✅ Extração realizada:")
    print(f"   Nome da Empresa: '{nome}'")
    print(f"   CNPJ: '{documento}'")
else:
    print("❌ Não encontrou linha do titular")

print("\n💡 Agora o sistema extrairá automaticamente o CNPJ da empresa titular da conta!")