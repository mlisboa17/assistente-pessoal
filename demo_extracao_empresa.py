#!/usr/bin/env python3
"""
Demonstração da extração de informações da empresa (nome, agência, conta) de extratos bancários
"""

import sys
import os
import re
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.extratos import ExtratosModule

def demo_extracao_empresa():
    """Demonstra a extração de nome da empresa, agência e conta"""

    # Instancia o módulo de extratos
    extratos = ExtratosModule()

    # Texto de exemplo de extrato bancário com informações da empresa
    texto_exemplo = """
    EXTRATO ITAÚ PJ
    ITAÚ UNIBANCO S.A.

    AGÊNCIA 1234
    CONTA 56789-0

    EMPRESA: EMPRESA XYZ LTDA
    CNPJ: 12.345.678/0001-23

    PERÍODO: 01/11/2024 - 30/11/2024

    SALDO ANTERIOR: R$ 10.000,00

    DATA        DESCRIÇÃO                           VALOR
    15/11/2024  PIX RECEBIDO EMPRESA ABC          5.000,00
    20/11/2024  TED ENVIADA PARA FORNECEDOR       -2.500,00
    25/11/2024  DEPÓSITO EM DINHEIRO               1.000,00

    SALDO ATUAL: R$ 13.500,00
    """

    print("=== DEMONSTRAÇÃO - EXTRAÇÃO DE INFORMAÇÕES DA EMPRESA ===\n")

    print("Texto do extrato:")
    print("-" * 60)
    print(texto_exemplo)
    print("-" * 60)

    # Identifica o banco
    banco = extratos._identificar_banco(texto_exemplo)
    print(f"Banco identificado: {banco}")
    
    # Debug: testa padrões manualmente
    texto_upper = texto_exemplo.upper()
    print(f"Texto contém 'ITAÚ': {'ITAÚ' in texto_upper}")
    print(f"Texto contém 'BANCO DO BRASIL': {'BANCO DO BRASIL' in texto_upper}")
    
    # Testa padrões do BB
    bb_patterns = [r'BANCO DO BRASIL', r'Banco do Brasil', r'BB', r'www\.bb\.com\.br', r'001']
    for pattern in bb_patterns:
        if re.search(pattern.upper(), texto_upper):
            print(f"Padrão BB encontrado: {pattern}")
            break
    
    # Testa padrões do Itaú
    itau_patterns = [r'ITAÚ', r'Itaú', r'ITAÚ UNIBANCO', r'Banco Itaú', r'www\.itau\.com\.br', r'4004', r'341']
    for pattern in itau_patterns:
        if re.search(pattern.upper(), texto_upper):
            print(f"Padrão Itaú encontrado: {pattern}")
            break
    
    print()

    # Extrai informações do titular
    titular_nome, titular_documento = extratos._identificar_titular(texto_exemplo, banco)
    print(f"Titular identificado: {titular_nome}")
    print(f"Documento: {titular_documento}\n")

    # Extrai informações da empresa
    info_empresa = extratos._extrair_informacoes_empresa(texto_exemplo, banco)
    print("Informações da empresa extraídas:")
    print(f"  Nome da empresa: {info_empresa['nome_empresa']}")
    print(f"  Agência: {info_empresa['agencia']}")
    print(f"  Conta: {info_empresa['conta']}\n")

    # Extrai dados completos do banco
    dados_completos = extratos._extrair_dados_banco(texto_exemplo, banco)
    print("Dados completos extraídos:")
    for chave, valor in dados_completos.items():
        if chave != 'transacoes':
            print(f"  {chave}: {valor}")
        else:
            print(f"  {chave}: {len(valor)} transações encontradas")

    print("\n=== TESTE COM DIFERENTES FORMATOS ===\n")

    # Teste com diferentes formatos
    textos_teste = [
        {
            'nome': 'Santander',
            'texto': """
            EXTRATO SANTANDER PJ
            
            Agência: 5678
            Conta: 12345-6
            
            Razão Social: COMERCIO LTDA
            CNPJ: 98.765.432/0001-10
            
            Período: 01/11/2024 - 30/11/2024
            """
        },
        {
            'nome': 'Banco do Brasil',
            'texto': """
            BANCO DO BRASIL - EXTRATO PJ
            
            Agência: 4321
            Conta: 98765-4
            
            Empresa: INDUSTRIA XYZ S.A.
            CNPJ: 11.222.333/0001-44
            
            Período: 01/11/2024 - 30/11/2024
            """
        }
    ]

    for teste in textos_teste:
        print(f"--- Teste com {teste['nome']} ---")
        banco_teste = extratos._identificar_banco(teste['texto'])
        info_empresa_teste = extratos._extrair_informacoes_empresa(teste['texto'], banco_teste)

        print(f"Banco: {banco_teste}")
        print(f"Nome da empresa: {info_empresa_teste['nome_empresa']}")
        print(f"Agência: {info_empresa_teste['agencia']}")
        print(f"Conta: {info_empresa_teste['conta']}\n")

if __name__ == "__main__":
    demo_extracao_empresa()