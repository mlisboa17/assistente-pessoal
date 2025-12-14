#!/usr/bin/env python3
"""
Teste da extração completa com arquivo de exemplo real
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.extratos import ExtratosModule

def teste_extracao_completa():
    """Testa a extração completa com arquivo de exemplo"""

    # Instancia o módulo de extratos
    extratos = ExtratosModule()

    # Lê o arquivo de exemplo
    arquivo_exemplo = "extrato_itau_exemplo.txt"

    with open(arquivo_exemplo, 'r', encoding='utf-8') as f:
        texto_exemplo = f.read()

    print("=== TESTE COM ARQUIVO REAL - EXTRATO ITAÚ ===\n")

    print("Conteúdo do arquivo:")
    print("-" * 60)
    print(texto_exemplo)
    print("-" * 60)

    # Identifica o banco
    banco = extratos._identificar_banco(texto_exemplo)
    print(f"Banco identificado: {banco}\n")

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
        if chave == 'transacoes':
            print(f"  {chave}: {len(valor)} transações encontradas")
            if valor:
                print("  Primeiras 3 transações:")
                for i, transacao in enumerate(valor[:3]):
                    print(f"    {i+1}. {transacao.data} - {transacao.descricao} - R$ {transacao.valor}")
        else:
            print(f"  {chave}: {valor}")

    print("\n=== EXTRAÇÃO COMPLETA CONCLUÍDA ===")

if __name__ == "__main__":
    teste_extracao_completa()