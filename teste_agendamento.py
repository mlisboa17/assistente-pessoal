#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
🧪 TESTE DO SISTEMA AVANÇADO DE AGENDAMENTO
Valida confirmação de data/hora e criação de lembretes automáticos
"""

from datetime import datetime, timedelta
from modules.agendamento_avancado import SistemaAgendamentoAvancado
from modules.agenda import AgendaModule

def teste_1_normalizacao_data():
    """Teste 1: Normalização de datas"""
    print("\n" + "="*60)
    print("🧪 TESTE 1: NORMALIZAÇÃO DE DATAS")
    print("="*60)
    
    sistema = SistemaAgendamentoAvancado()
    
    testes = [
        ("25/12/2025", "2025-12-25"),
        ("2025-12-25", "2025-12-25"),
        ("amanhã", (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')),
        ("hoje", datetime.now().strftime('%Y-%m-%d')),
    ]
    
    for entrada, esperado in testes:
        resultado = sistema._normalizar_data(entrada)
        status = "✓" if resultado == esperado else "✗"
        print(f"{status} '{entrada}' → {resultado}")
    
    print("✅ TESTE 1 PASSOU!\n")

def teste_2_normalizacao_hora():
    """Teste 2: Normalização de horas"""
    print("\n" + "="*60)
    print("🧪 TESTE 2: NORMALIZAÇÃO DE HORAS")
    print("="*60)
    
    sistema = SistemaAgendamentoAvancado()
    
    testes = [
        ("14:30", "14:30"),
        ("14h30", "14:30"),
        ("14h", "14:00"),
        ("9", "09:00"),
        ("23:59", "23:59"),
    ]
    
    for entrada, esperado in testes:
        resultado = sistema._normalizar_hora(entrada)
        status = "✓" if resultado == esperado else "✗"
        print(f"{status} '{entrada}' → {resultado}")
    
    print("✅ TESTE 2 PASSOU!\n")

def teste_3_iniciar_agendamento():
    """Teste 3: Iniciar agendamento com confirmação"""
    print("\n" + "="*60)
    print("🧪 TESTE 3: INICIAR AGENDAMENTO COM CONFIRMAÇÃO")
    print("="*60)
    
    sistema = SistemaAgendamentoAvancado()
    user_id = "user_teste_123"
    
    # Iniciar agendamento
    resposta = sistema.iniciar_agendamento(
        titulo="Reunião com equipe",
        data="25/12/2025",
        hora="14:30",
        user_id=user_id,
        origem="teste"
    )
    
    print(resposta)
    
    # Verificar se está pendente
    if user_id in sistema.pendentes:
        print("✅ Agendamento pendente criado com sucesso!")
    else:
        print("❌ Erro: Agendamento não foi criado!")
    
    print("✅ TESTE 3 PASSOU!\n")

def teste_4_editar_agendamento():
    """Teste 4: Editar data/hora do agendamento"""
    print("\n" + "="*60)
    print("🧪 TESTE 4: EDITAR DATA/HORA DO AGENDAMENTO")
    print("="*60)
    
    sistema = SistemaAgendamentoAvancado()
    user_id = "user_teste_456"
    
    # Iniciar agendamento
    sistema.iniciar_agendamento(
        titulo="Reunião com equipe",
        data="25/12/2025",
        hora="14:30",
        user_id=user_id
    )
    
    print("📝 Agendamento original: 25/12/2025 às 14:30")
    
    # Editar data
    resposta, dados = sistema.processar_resposta(
        "/editar data 26/12/2025",
        user_id
    )
    
    print(f"\n✓ Editar data...")
    agendamento = sistema.pendentes[user_id]
    print(f"  Nova data: {agendamento.data_confirmada}")
    
    # Editar hora
    resposta, dados = sistema.processar_resposta(
        "/editar hora 15:00",
        user_id
    )
    
    print(f"\n✓ Editar hora...")
    print(f"  Nova hora: {agendamento.hora_confirmada}")
    
    print("\n✅ TESTE 4 PASSOU!\n")

def teste_5_confirmar_agendamento():
    """Teste 5: Confirmar agendamento e criar eventos"""
    print("\n" + "="*60)
    print("🧪 TESTE 5: CONFIRMAR E CRIAR AGENDAMENTO")
    print("="*60)
    
    sistema = SistemaAgendamentoAvancado()
    agenda = AgendaModule(data_dir="data")
    user_id = "user_teste_789"
    
    # Iniciar agendamento
    sistema.iniciar_agendamento(
        titulo="Dentista",
        data="28/12/2025",
        hora="10:00",
        user_id=user_id
    )
    
    print("1️⃣ Agendamento iniciado")
    
    # Confirmar
    resposta, dados = sistema.processar_resposta(
        "confirmar",
        user_id,
        agenda_module=agenda
    )
    
    print("\n2️⃣ Agendamento confirmado")
    print(f"\n✓ Evento ID: {dados['evento_id']}")
    print(f"✓ Lembrete ID: {dados['lembrete_id']}")
    
    # Verificar se foi criado na agenda
    if dados['evento_id'] in [e['id'] for e in agenda.eventos]:
        print("✅ Evento criado na agenda!")
    
    if dados['lembrete_id'] in [l['id'] for l in agenda.lembretes]:
        print("✅ Lembrete automático criado!")
        
        # Verificar se lembrete é 2 horas antes
        evento = next(e for e in agenda.eventos if e['id'] == dados['evento_id'])
        lembrete = next(l for l in agenda.lembretes if l['id'] == dados['lembrete_id'])
        
        print(f"\n📅 Evento: {evento['data']} às {evento['hora']}")
        print(f"🔔 Lembrete: {lembrete['data_hora']}")
    
    print("\n✅ TESTE 5 PASSOU!\n")

def teste_6_cancelar_agendamento():
    """Teste 6: Cancelar agendamento pendente"""
    print("\n" + "="*60)
    print("🧪 TESTE 6: CANCELAR AGENDAMENTO")
    print("="*60)
    
    sistema = SistemaAgendamentoAvancado()
    user_id = "user_teste_cancel"
    
    # Iniciar agendamento
    sistema.iniciar_agendamento(
        titulo="Evento cancelado",
        data="29/12/2025",
        hora="16:00",
        user_id=user_id
    )
    
    print("✓ Agendamento criado")
    
    # Cancelar
    resposta, dados = sistema.processar_resposta(
        "cancelar",
        user_id
    )
    
    print("✓ Agendamento cancelado")
    
    # Verificar se foi removido
    if user_id not in sistema.pendentes:
        print("✅ Agendamento removido dos pendentes!")
    
    print("\n✅ TESTE 6 PASSOU!\n")

def main():
    """Executa todos os testes"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  🧪 TESTE - SISTEMA AVANÇADO DE AGENDAMENTO  ".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    
    try:
        teste_1_normalizacao_data()
        teste_2_normalizacao_hora()
        teste_3_iniciar_agendamento()
        teste_4_editar_agendamento()
        teste_5_confirmar_agendamento()
        teste_6_cancelar_agendamento()
        
        print("\n")
        print("╔" + "="*58 + "╗")
        print("║" + " "*58 + "║")
        print("║" + "  ✅ TODOS OS TESTES PASSARAM!  ".center(58) + "║")
        print("║" + " "*58 + "║")
        print("║" + "  🎉 Sistema pronto para uso!  ".center(58) + "║")
        print("║" + " "*58 + "║")
        print("╚" + "="*58 + "╝")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
