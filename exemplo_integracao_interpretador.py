#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📱 Exemplo de Integração - Interpretador Inteligente v2.0 com WhatsApp Bot
Demonstra como o novo interpretador funciona com processamento de arquivos
"""

from middleware.ia_interpreter import interpretar_mensagem
import json


def exemplo_1_saudacao():
    """Exemplo 1: Saudação simples"""
    print("\n" + "=" * 70)
    print("📱 EXEMPLO 1: SAUDAÇÃO SIMPLES")
    print("=" * 70)
    
    msg = "oi, tudo bem?"
    print(f"\n👤 Usuário: {msg}")
    
    resultado = interpretar_mensagem(msg)
    
    print(f"\n🤖 Interpretador:")
    print(f"   Intenção: {resultado['intencao']}")
    print(f"   Ação: {resultado['acao']}")
    print(f"   Confiança: {resultado['confianca']:.0%}")
    print(f"\n💬 Resposta: {resultado['resposta_direta']}")


def exemplo_2_agenda():
    """Exemplo 2: Agendar reunião com data e hora"""
    print("\n" + "=" * 70)
    print("📱 EXEMPLO 2: AGENDAR REUNIÃO")
    print("=" * 70)
    
    msg = "tenho reunião com o cliente amanhã às 14h30"
    print(f"\n👤 Usuário: {msg}")
    
    resultado = interpretar_mensagem(msg)
    
    print(f"\n🤖 Interpretador:")
    print(f"   Intenção: {resultado['intencao']}")
    print(f"   Ação: {resultado['acao']}")
    print(f"   Confiança: {resultado['confianca']:.0%}")
    print(f"\n📋 Parâmetros extraídos:")
    for chave, valor in resultado['parametros'].items():
        print(f"   • {chave}: {valor}")


def exemplo_3_busca_email():
    """Exemplo 3: Buscar email incompleto (com fuzzy)"""
    print("\n" + "=" * 70)
    print("📱 EXEMPLO 3: BUSCAR EMAIL (FUZZY)")
    print("=" * 70)
    
    msg = "buscar email de joão"
    print(f"\n👤 Usuário: {msg}")
    
    resultado = interpretar_mensagem(msg)
    
    print(f"\n🤖 Interpretador:")
    print(f"   Intenção: {resultado['intencao']}")
    print(f"   Ação: {resultado['acao']}")
    print(f"   Confiança: {resultado['confianca']:.0%}")
    print(f"\n📧 Critérios de busca:")
    for chave, valor in resultado['parametros'].items():
        print(f"   • {chave}: '{valor}' (será usado fuzzy search)")


def exemplo_4_boleto():
    """Exemplo 4: Processamento de boleto PDF"""
    print("\n" + "=" * 70)
    print("📱 EXEMPLO 4: PROCESSAR BOLETO PDF")
    print("=" * 70)
    
    msg = "lê o código de barras desse boleto"
    arquivo_dados = {
        'tipo': 'application/pdf',
        'nome': 'boleto_banco_2024.pdf'
    }
    
    print(f"\n👤 Usuário: {msg}")
    print(f"📎 Arquivo: {arquivo_dados['nome']} ({arquivo_dados['tipo']})")
    
    resultado = interpretar_mensagem(msg, arquivo_dados=arquivo_dados)
    
    print(f"\n🤖 Interpretador:")
    print(f"   Intenção: {resultado['intencao']}")
    print(f"   Ação: {resultado['acao']}")
    print(f"   Confiança: {resultado['confianca']:.0%}")
    print(f"\n📋 Parâmetros:")
    print(f"   • Tipo de arquivo: {resultado['parametros']['tipo']}")
    print(f"   • Nome: {resultado['parametros']['nome']}")
    print(f"   • Comando: {resultado['parametros']['comando_usuario']}")
    print(f"\n💬 Feedback ao usuário: {resultado['resposta_direta']}")


def exemplo_5_comprovante():
    """Exemplo 5: Processamento de comprovante de PIX"""
    print("\n" + "=" * 70)
    print("📱 EXEMPLO 5: ANALISAR COMPROVANTE DE PIX")
    print("=" * 70)
    
    msg = "processa esse comprovante"
    arquivo_dados = {
        'tipo': 'image/jpeg',
        'nome': 'comprovante_pix_123.jpg'
    }
    
    print(f"\n👤 Usuário: {msg}")
    print(f"📎 Arquivo: {arquivo_dados['nome']} ({arquivo_dados['tipo']})")
    
    resultado = interpretar_mensagem(msg, arquivo_dados=arquivo_dados)
    
    print(f"\n🤖 Interpretador:")
    print(f"   Intenção: {resultado['intencao']}")
    print(f"   Ação: {resultado['acao']}")
    print(f"   Confiança: {resultado['confianca']:.0%}")
    print(f"\n📋 O que vai acontecer:")
    print(f"   1. Arquivo {arquivo_dados['nome']} será enviado para análise")
    print(f"   2. Será detectado como: {resultado['parametros']['tipo']}")
    print(f"   3. Módulo de comprovantes processará com IA")
    print(f"   4. Extrairá: valor, data, beneficiário")
    print(f"\n💬 Feedback ao usuário: {resultado['resposta_direta']}")


def exemplo_6_fluxo_completo():
    """Exemplo 6: Fluxo completo - Usuário envia boleto com mensagem"""
    print("\n" + "=" * 70)
    print("📱 EXEMPLO 6: FLUXO COMPLETO - BOLETO + MENSAGEM")
    print("=" * 70)
    
    print("""
    🔄 SIMULAÇÃO DO FLUXO:
    
    1️⃣ WhatsApp Bot recebe:
       - Arquivo: boleto.pdf (1.2 MB)
       - Mensagem: "extrai o vencimento desse boleto"
    
    2️⃣ Bot aguarda download (com timeout):
       - ⏳ Timeout de 45 segundos
       - 🔄 Retry automático até 3 vezes
       - ✅ Verifica se buffer foi completado
    
    3️⃣ Envia para API Server com:
       - Dados do arquivo (base64)
       - Mensagem do usuário
    
    4️⃣ API Server chama interpretador:
    """)
    
    msg = "extrai o vencimento desse boleto"
    arquivo_dados = {
        'tipo': 'application/pdf',
        'nome': 'boleto.pdf'
    }
    
    resultado = interpretar_mensagem(msg, arquivo_dados=arquivo_dados)
    
    print(f"       Resultado: {json.dumps(resultado, indent=6, ensure_ascii=False)}")
    
    print(f"""
    5️⃣ Orquestrador decide:
       - Intenção: {resultado['intencao']}
       - Ação: {resultado['acao']}
       - Tipo de arquivo: {resultado['parametros']['tipo']}
       
    6️⃣ FaturasModule processa:
       - Extrai código de barras
       - Lê data de vencimento
       - Retorna informações
    
    7️⃣ Resposta ao usuário:
       {resultado['resposta_direta']}
    """)


def exemplo_7_comparacao_confianca():
    """Exemplo 7: Mostrar score de confiança em diferentes mensagens"""
    print("\n" + "=" * 70)
    print("📊 EXEMPLO 7: SCORES DE CONFIANÇA")
    print("=" * 70)
    
    testes = [
        ("oi", "Saudação muito clara"),
        ("tenho reunião amanhã às 14h", "Agenda com informações completas"),
        ("alguma coisa aleatória", "Mensagem sem intenção clara"),
        ("me lembra em 1 hora", "Lembrete com tempo específico"),
        ("gastei 100 no almoço", "Despesa com valor claro"),
    ]
    
    print("\nMensagem | Intenção | Confiança")
    print("-" * 70)
    
    for msg, descricao in testes:
        resultado = interpretar_mensagem(msg)
        inten = resultado['intencao']
        confa = resultado['confianca']
        
        # Barra visual de confiança
        barra = "█" * int(confa * 20) + "░" * (20 - int(confa * 20))
        
        print(f"{msg:30} | {inten:12} | {confa:.0%} [{barra}]")


def main():
    """Executa todos os exemplos"""
    print("\n" + "=" * 70)
    print("🎯 EXEMPLOS DE INTEGRAÇÃO - INTERPRETADOR V2.0")
    print("=" * 70)
    
    exemplo_1_saudacao()
    exemplo_2_agenda()
    exemplo_3_busca_email()
    exemplo_4_boleto()
    exemplo_5_comprovante()
    exemplo_6_fluxo_completo()
    exemplo_7_comparacao_confianca()
    
    print("\n" + "=" * 70)
    print("✅ FIM DOS EXEMPLOS")
    print("=" * 70)
    print("""
    📚 PRÓXIMOS PASSOS:
    
    1. Integrar com orchestrator.py para usar arquivo_dados
    2. Atualizar API Server para passar dados de arquivo
    3. Testar com usuários reais no WhatsApp
    4. Monitorar scores de confiança
    5. Ajustar thresholds conforme necessário
    
    📖 Veja também:
    - MELHORIAS_INTERPRETADOR_V2.md
    - teste_interpretador_v2.py
    - middleware/ia_interpreter.py
    """)


if __name__ == '__main__':
    main()

