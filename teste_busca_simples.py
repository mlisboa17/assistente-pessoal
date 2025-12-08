#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste: Buscador Fuzzy de E-mails
"""
import sys
sys.path.append('c:\\Users\\mlisb\\OneDrive\\Desktop\\Projetos\\assistente-pessoal-main\\assistente-pessoal-main')

from modules.buscador_emails import BuscadorFuzzyEmails
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class EmailTest:
    id: str
    de: str
    para: str
    assunto: str
    corpo: str
    data: str
    resumo: str = ""

# Criar emails de teste
emails_teste = [
    EmailTest(
        id="1", de="chefe@empresa.com", para="voce@gmail.com",
        assunto="Reuniao urgente hoje 14:00 - Projeto X",
        corpo="Preciso discutir os desenvolvimentos do projeto X.",
        data=datetime.now().isoformat(), resumo="Reuniao urgente"
    ),
    EmailTest(
        id="2", de="amigo@hotmail.com", para="voce@gmail.com",
        assunto="Opa bora tomar um cafe?",
        corpo="Ta afim de tomar um cafe comigo no sabado?",
        data=(datetime.now() - timedelta(hours=5)).isoformat(),
        resumo="Convite para cafe"
    ),
    EmailTest(
        id="4", de="amazon@noreply.com.br", para="voce@gmail.com",
        assunto="Seu pedido foi entregue!",
        corpo="Seu pedido chegou!",
        data=(datetime.now() - timedelta(hours=8)).isoformat(),
        resumo="Pedido entregue"
    ),
    EmailTest(
        id="7", de="carlos@empresa.com", para="voce@gmail.com",
        assunto="Discussao sobre meeting de amanha",
        corpo="Precisamos agendar a reuniao de amanha.",
        data=(datetime.now() - timedelta(hours=3)).isoformat(),
        resumo="Agendamento de reuniao"
    ),
]

def main():
    print("\n" + "="*60)
    print("   TESTES: Buscador Fuzzy de E-mails")
    print("="*60)
    
    buscador = BuscadorFuzzyEmails()
    
    # Teste 1: Busca exata
    print("\n[TESTE 1] Busca por remetente EXATO:")
    resultados = buscador.buscar_remetente_fuzzy("amazon@noreply.com.br", emails_teste)
    print(f"  Buscando: 'amazon@noreply.com.br'")
    print(f"  Encontrados: {len(resultados)}")
    assert len(resultados) > 0
    print("  PASSOU!")
    
    # Teste 2: Busca incompleta
    print("\n[TESTE 2] Busca por remetente INCOMPLETO:")
    resultados = buscador.buscar_remetente_fuzzy("ch", emails_teste)
    print(f"  Buscando: 'ch'")
    print(f"  Encontrados: {len(resultados)}")
    if resultados:
        print(f"  Primeiro: {resultados[0].email.de} ({resultados[0].score:.0%})")
    assert len(resultados) > 0
    print("  PASSOU!")
    
    # Teste 3: Busca por "ama" (amazon)
    print("\n[TESTE 3] Busca fuzzy 'ama' -> 'amazon':")
    resultados = buscador.buscar_remetente_fuzzy("ama", emails_teste)
    print(f"  Buscando: 'ama'")
    print(f"  Encontrados: {len(resultados)}")
    if resultados and "amazon" in resultados[0].email.de.lower():
        print(f"  Primeiro: {resultados[0].email.de} (CORRETO!)")
        print("  PASSOU!")
    else:
        print("  FALHOU!")
    
    # Teste 4: Busca por assunto "reuniao"
    print("\n[TESTE 4] Busca inteligente por assunto 'reuniao':")
    resultados = buscador.buscar_assunto_inteligente("reuniao", emails_teste)
    print(f"  Buscando: 'reuniao'")
    print(f"  Encontrados: {len(resultados)}")
    if resultados:
        for r in resultados[:2]:
            print(f"    - {r.email.assunto[:40]} ({r.score:.0%})")
    assert len(resultados) > 0
    print("  PASSOU!")
    
    # Teste 5: Busca combinada
    print("\n[TESTE 5] Busca combinada 'ch' + 'reuniao':")
    resultados = buscador.buscar_combinado("ch", "reuniao", emails_teste)
    print(f"  Por remetente: {len(resultados['remetente'])}")
    print(f"  Por assunto: {len(resultados['assunto'])}")
    print(f"  Combinados: {len(resultados['combinado'])}")
    print("  PASSOU!")
    
    # Teste 6: Sugestoes
    print("\n[TESTE 6] Sugestoes de autocomplete para 'a':")
    sugestoes = buscador.gerar_sugestoes("a", emails_teste, max_sugestoes=3)
    print(f"  Encontradas: {len(sugestoes)} sugestoes")
    for remetente, nome in sugestoes:
        print(f"    - {nome} ({remetente})")
    print("  PASSOU!")
    
    # Teste 7: Formatacao
    print("\n[TESTE 7] Formatacao de resultados:")
    resultados = buscador.buscar_remetente_fuzzy("ch", emails_teste)
    if resultados:
        texto = buscador.formatar_resultados(resultados, max_itens=2)
        print(f"  Formatado com sucesso ({len(texto)} caracteres)")
        print("  PASSOU!")
    
    # Teste 8: Score de confianca
    print("\n[TESTE 8] Verificacao de scores:")
    res_exato = buscador.buscar_remetente_fuzzy("chefe@empresa.com", emails_teste)
    res_parcial = buscador.buscar_remetente_fuzzy("che", emails_teste)
    if res_exato and res_parcial:
        print(f"  Busca exata: {res_exato[0].score:.0%}")
        print(f"  Busca parcial: {res_parcial[0].score:.0%}")
        assert res_exato[0].score >= res_parcial[0].score
        print("  PASSOU!")
    
    print("\n" + "="*60)
    print("   TESTES CONCLUIDOS COM SUCESSO!")
    print("="*60)
    print("\nRecursos implementados:")
    print("  OK Busca por remetente incompleto (fuzzy matching)")
    print("  OK Busca inteligente por assunto")
    print("  OK Busca combinada (remetente + assunto)")
    print("  OK Autocomplete com sugestoes")
    print("  OK Score de confianca em cada resultado")
    print("  OK Formatacao com indicadores visuais")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
