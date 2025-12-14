#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Testes do Interpretador Inteligente v2.0
Validar confiança, processamento de arquivos e busca de emails
"""

import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from middleware.ia_interpreter import interpretar_mensagem, IAInterpreter


def teste_interpretador():
    """Executa testes do interpretador"""
    print("=" * 70)
    print("🧪 TESTES DO INTERPRETADOR INTELIGENTE V2.0")
    print("=" * 70)
    
    tests_passed = 0
    tests_total = 0
    
    # ===== TESTE 1: Saudações =====
    tests_total += 1
    print("\n📋 TESTE 1: Saudações")
    msg = "oi, tudo bem?"
    resultado = interpretar_mensagem(msg)
    print(f"   Mensagem: '{msg}'")
    print(f"   Intenção: {resultado['intencao']}")
    print(f"   Ação: {resultado['acao']}")
    print(f"   Confiança: {resultado['confianca']}")
    assert resultado['intencao'] == 'conversa', "Falha: deve ser conversa"
    assert resultado['confianca'] > 0.9, "Falha: confiança deve ser alta"
    print("   ✅ PASSOU")
    tests_passed += 1
    
    # ===== TESTE 2: Agenda com Data e Hora =====
    tests_total += 1
    print("\n📋 TESTE 2: Agenda com Data e Hora")
    msg = "tenho reunião amanhã às 14h30 com o cliente"
    resultado = interpretar_mensagem(msg)
    print(f"   Mensagem: '{msg}'")
    print(f"   Intenção: {resultado['intencao']}")
    print(f"   Ação: {resultado['acao']}")
    print(f"   Parâmetros: {resultado['parametros']}")
    print(f"   Confiança: {resultado['confianca']}")
    assert resultado['intencao'] == 'agenda', "Falha: deve ser agenda"
    assert resultado['acao'] == 'adicionar', "Falha: deve ser adicionar"
    assert 'horario' in resultado['parametros'], "Falha: deve extrair horário"
    assert resultado['parametros']['horario'] == '14:30', "Falha: horário incorreto"
    print("   ✅ PASSOU")
    tests_passed += 1
    
    # ===== TESTE 3: Tarefa =====
    tests_total += 1
    print("\n📋 TESTE 3: Tarefa")
    msg = "preciso comprar leite e pão no mercado"
    resultado = interpretar_mensagem(msg)
    print(f"   Mensagem: '{msg}'")
    print(f"   Intenção: {resultado['intencao']}")
    print(f"   Ação: {resultado['acao']}")
    print(f"   Confiança: {resultado['confianca']}")
    assert resultado['intencao'] == 'tarefa', "Falha: deve ser tarefa"
    assert resultado['acao'] == 'adicionar', "Falha: deve ser adicionar"
    print("   ✅ PASSOU")
    tests_passed += 1
    
    # ===== TESTE 4: Lembrete =====
    tests_total += 1
    print("\n📋 TESTE 4: Lembrete")
    msg = "me lembra em 30 minutos de ligar para o João"
    resultado = interpretar_mensagem(msg)
    print(f"   Mensagem: '{msg}'")
    print(f"   Intenção: {resultado['intencao']}")
    print(f"   Ação: {resultado['acao']}")
    print(f"   Parâmetros: {resultado['parametros']}")
    print(f"   Confiança: {resultado['confianca']}")
    assert resultado['intencao'] == 'lembrete', "Falha: deve ser lembrete"
    assert 'tempo' in resultado['parametros'], "Falha: deve extrair tempo"
    print("   ✅ PASSOU")
    tests_passed += 1
    
    # ===== TESTE 5: Finanças - Despesa =====
    tests_total += 1
    print("\n📋 TESTE 5: Finanças - Despesa")
    msg = "gastei 50 reais no almoço no restaurante"
    resultado = interpretar_mensagem(msg)
    print(f"   Mensagem: '{msg}'")
    print(f"   Intenção: {resultado['intencao']}")
    print(f"   Ação: {resultado['acao']}")
    print(f"   Parâmetros: {resultado['parametros']}")
    print(f"   Confiança: {resultado['confianca']}")
    assert resultado['intencao'] == 'financeiro', "Falha: deve ser financeiro"
    assert resultado['parametros']['valor'] == 50.0, "Falha: valor incorreto"
    print("   ✅ PASSOU")
    tests_passed += 1
    
    # ===== TESTE 6: Busca de Email - Remetente =====
    tests_total += 1
    print("\n📋 TESTE 6: Busca de Email - Remetente")
    msg = "buscar email de joão"
    resultado = interpretar_mensagem(msg)
    print(f"   Mensagem: '{msg}'")
    print(f"   Intenção: {resultado['intencao']}")
    print(f"   Ação: {resultado['acao']}")
    print(f"   Parâmetros: {resultado['parametros']}")
    print(f"   Confiança: {resultado['confianca']}")
    assert resultado['intencao'] == 'email', "Falha: deve ser email"
    assert resultado['acao'] == 'buscar', "Falha: ação deve ser buscar"
    assert 'remetente' in resultado['parametros'], "Falha: deve extrair remetente"
    print("   ✅ PASSOU")
    tests_passed += 1
    
    # ===== TESTE 7: Busca de Email - Assunto =====
    tests_total += 1
    print("\n📋 TESTE 7: Busca de Email - Assunto")
    msg = "pesquisar email com assunto reunião"
    resultado = interpretar_mensagem(msg)
    print(f"   Mensagem: '{msg}'")
    print(f"   Intenção: {resultado['intencao']}")
    print(f"   Parâmetros: {resultado['parametros']}")
    print(f"   Confiança: {resultado['confianca']}")
    assert resultado['intencao'] == 'email', "Falha: deve ser email"
    assert 'assunto' in resultado['parametros'], "Falha: deve extrair assunto"
    print("   ✅ PASSOU")
    tests_passed += 1
    
    # ===== TESTE 8: Processamento com Arquivo - Boleto =====
    tests_total += 1
    print("\n📋 TESTE 8: Processamento com Arquivo - Boleto")
    msg = "processa esse boleto"
    arquivo_dados = {
        'tipo': 'application/pdf',
        'nome': 'boleto_banco.pdf'
    }
    resultado = interpretar_mensagem(msg, arquivo_dados=arquivo_dados)
    print(f"   Mensagem: '{msg}'")
    print(f"   Arquivo: {arquivo_dados['nome']}")
    print(f"   Intenção: {resultado['intencao']}")
    print(f"   Ação: {resultado['acao']}")
    print(f"   Tipo: {resultado['parametros'].get('tipo')}")
    print(f"   Confiança: {resultado['confianca']}")
    assert resultado['intencao'] == 'sistema', "Falha: deve ser sistema"
    assert resultado['acao'] == 'processar_arquivo', "Falha: deve processar arquivo"
    assert resultado['parametros']['tipo'] == 'boleto', "Falha: deve detectar boleto"
    assert resultado['confianca'] > 0.9, "Falha: confiança deve ser alta"
    print("   ✅ PASSOU")
    tests_passed += 1
    
    # ===== TESTE 9: Processamento com Arquivo - Imagem =====
    tests_total += 1
    print("\n📋 TESTE 9: Processamento com Arquivo - Imagem")
    msg = "analisa esse comprovante"
    arquivo_dados = {
        'tipo': 'image/jpeg',
        'nome': 'comprovante_pix.jpg'
    }
    resultado = interpretar_mensagem(msg, arquivo_dados=arquivo_dados)
    print(f"   Mensagem: '{msg}'")
    print(f"   Arquivo: {arquivo_dados['nome']}")
    print(f"   Intenção: {resultado['intencao']}")
    print(f"   Tipo: {resultado['parametros'].get('tipo')}")
    print(f"   Confiança: {resultado['confianca']}")
    assert resultado['intencao'] == 'sistema', "Falha: deve ser sistema"
    assert resultado['parametros']['tipo'] == 'imagem', "Falha: deve detectar imagem"
    print("   ✅ PASSOU")
    tests_passed += 1
    
    # ===== TESTE 10: Processamento com Arquivo - Áudio =====
    tests_total += 1
    print("\n📋 TESTE 10: Processamento com Arquivo - Áudio")
    msg = "transcreve esse áudio"
    arquivo_dados = {
        'tipo': 'audio/ogg',
        'nome': 'mensagem.ogg'
    }
    resultado = interpretar_mensagem(msg, arquivo_dados=arquivo_dados)
    print(f"   Mensagem: '{msg}'")
    print(f"   Arquivo: {arquivo_dados['nome']}")
    print(f"   Intenção: {resultado['intencao']}")
    print(f"   Tipo: {resultado['parametros'].get('tipo')}")
    print(f"   Confiança: {resultado['confianca']}")
    assert resultado['intencao'] == 'sistema', "Falha: deve ser sistema"
    assert resultado['parametros']['tipo'] == 'audio', "Falha: deve detectar áudio"
    print("   ✅ PASSOU")
    tests_passed += 1
    
    # ===== TESTE 11: Ajuda =====
    tests_total += 1
    print("\n📋 TESTE 11: Ajuda")
    msg = "/ajuda"
    resultado = interpretar_mensagem(msg)
    print(f"   Mensagem: '{msg}'")
    print(f"   Intenção: {resultado['intencao']}")
    print(f"   Ação: {resultado['acao']}")
    print(f"   Tem resposta: {resultado['resposta_direta'] is not None}")
    assert resultado['intencao'] == 'sistema', "Falha: deve ser sistema"
    assert resultado['acao'] == 'ajuda', "Falha: ação deve ser ajuda"
    assert resultado['resposta_direta'] is not None, "Falha: deve ter resposta"
    print("   ✅ PASSOU")
    tests_passed += 1
    
    # ===== TESTE 12: Agradecimento =====
    tests_total += 1
    print("\n📋 TESTE 12: Agradecimento")
    msg = "obrigado pela ajuda!"
    resultado = interpretar_mensagem(msg)
    print(f"   Mensagem: '{msg}'")
    print(f"   Intenção: {resultado['intencao']}")
    print(f"   Confiança: {resultado['confianca']}")
    assert resultado['intencao'] == 'conversa', "Falha: deve ser conversa"
    assert resultado['confianca'] > 0.9, "Falha: confiança deve ser alta"
    print("   ✅ PASSOU")
    tests_passed += 1
    
    # Resumo
    print("\n" + "=" * 70)
    print(f"✅ RESULTADO: {tests_passed}/{tests_total} testes passaram")
    print("=" * 70)
    
    if tests_passed == tests_total:
        print("\n🎉 TODOS OS TESTES PASSARAM! Interpretador funcionando perfeitamente!")
        return 0
    else:
        print(f"\n❌ {tests_total - tests_passed} testes falharam")
        return 1


def demonstracao_interpretador():
    """Demonstração interativa do interpretador"""
    print("\n" + "=" * 70)
    print("🎯 DEMONSTRAÇÃO INTERATIVA DO INTERPRETADOR")
    print("=" * 70)
    print("\nDigite mensagens para testar o interpretador")
    print("Digite 'sair' para finalizar\n")
    
    while True:
        try:
            msg = input("📝 Sua mensagem: ").strip()
            
            if msg.lower() == 'sair':
                print("Até logo! 👋")
                break
            
            if not msg:
                continue
            
            # Processa a mensagem
            resultado = interpretar_mensagem(msg)
            
            # Exibe resultado
            print(f"\n📊 RESULTADO:")
            print(f"   Intenção: {resultado['intencao']}")
            print(f"   Ação: {resultado['acao']}")
            print(f"   Confiança: {resultado['confianca']:.0%}")
            
            if resultado['parametros']:
                print(f"   Parâmetros: {resultado['parametros']}")
            
            if resultado['resposta_direta']:
                print(f"   Resposta: {resultado['resposta_direta']}")
            
            print()
            
        except KeyboardInterrupt:
            print("\n\nFinalizado.")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")


if __name__ == '__main__':
    # Executa testes
    exit_code = teste_interpretador()
    
    # Pergunta se quer demonstração interativa
    if exit_code == 0:
        try:
            resp = input("\nDeseja testar interativamente? (s/n): ").lower()
            if resp == 's':
                demonstracao_interpretador()
        except KeyboardInterrupt:
            pass
    
    sys.exit(exit_code)

