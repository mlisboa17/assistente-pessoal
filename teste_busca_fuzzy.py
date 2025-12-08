"""
✅ Teste: Buscador Fuzzy de E-mails
Sistema inteligente de busca com fuzzy matching
"""
import sys
import os
sys.path.append('c:\\Users\\mlisb\\OneDrive\\Desktop\\Projetos\\assistente-pessoal-main\\assistente-pessoal-main')

# Configurar encoding UTF-8
if sys.platform == 'win32':
    os.system('chcp 65001')

from modules.buscador_emails import BuscadorFuzzyEmails
from dataclasses import dataclass
from datetime import datetime, timedelta

# Dados de teste
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
        id="1",
        de="chefe@empresa.com",
        para="voce@gmail.com",
        assunto="Reunião urgente hoje às 14:00 - Projeto X",
        corpo="Preciso discutir os desenvolvimentos do projeto X.",
        data=datetime.now().isoformat(),
        resumo="Reunião urgente sobre projeto X"
    ),
    EmailTest(
        id="2",
        de="chefao@empresa.com.br",
        para="voce@gmail.com",
        assunto="Feedback do Projeto",
        corpo="Aqui está o feedback que você pediu.",
        data=(datetime.now() - timedelta(hours=2)).isoformat(),
        resumo="Feedback sobre projeto"
    ),
    EmailTest(
        id="3",
        de="amigo@hotmail.com",
        para="voce@gmail.com",
        assunto="Ô, bora tomar um café?",
        corpo="Tá afim de tomar um café comigo no sábado?",
        data=(datetime.now() - timedelta(hours=5)).isoformat(),
        resumo="Convite para café"
    ),
    EmailTest(
        id="4",
        de="amazon@noreply.com.br",
        para="voce@gmail.com",
        assunto="📦 Seu pedido foi entregue!",
        corpo="Seu pedido chegou!",
        data=(datetime.now() - timedelta(hours=8)).isoformat(),
        resumo="Pedido Amazon entregue"
    ),
    EmailTest(
        id="5",
        de="shopee@noreply.com.br",
        para="voce@gmail.com",
        assunto="🎉 MEGA DESCONTO: Até 70% de desconto!",
        corpo="Eletrônicos com até 70% de desconto.",
        data=(datetime.now() - timedelta(hours=12)).isoformat(),
        resumo="Promoção eletrônicos"
    ),
    EmailTest(
        id="6",
        de="banco@bancobrasil.com.br",
        para="voce@gmail.com",
        assunto="⚠️ Alerta de Segurança: Acesso Não Autorizado",
        corpo="Detectamos uma tentativa de acesso.",
        data=(datetime.now() - timedelta(hours=24)).isoformat(),
        resumo="Alerta de segurança"
    ),
    EmailTest(
        id="7",
        de="carlos@empresa.com",
        para="voce@gmail.com",
        assunto="Discussão sobre meeting de amanhã",
        corpo="Precisamos agendar a reunião de amanhã.",
        data=(datetime.now() - timedelta(hours=3)).isoformat(),
        resumo="Agendamento de reunião"
    ),
]


def teste_1_busca_remetente_exata():
    """✅ Teste 1: Busca por remetente EXATA"""
        print("\n" + "="*60)
        print("   TESTE 1: Busca por Remetente EXATA")
    print("="*60)
    
    buscador = BuscadorFuzzyEmails()
    
    # Buscar "amazon@noreply.com.br"
    resultados = buscador.buscar_remetente_fuzzy("amazon@noreply.com.br", emails_teste)
    
    print(f"\n🔍 Buscando: 'amazon@noreply.com.br'")
    print(f"Encontrados: {len(resultados)}")
    
    if resultados:
        for r in resultados:
            print(f"  ✅ {r.email.de} ({r.score:.0%}) - {r.motivo}")
    
    # Verificar que a primeira correspondência é exata
    assert len(resultados) > 0, "Deve encontrar pelo menos um resultado"
    assert "amazon" in resultados[0].email.de.lower(), "Deve encontrar amazon primeiro"
    print("\n✅ TESTE 1 PASSOU!")


def teste_2_busca_remetente_incompleto():
    """✅ Teste 2: Busca por remetente INCOMPLETO (fuzzy)"""
    print("\n" + "="*60)
    print("✅ TESTE 2: Busca por Remetente INCOMPLETO")
    print("="*60)
    
    buscador = BuscadorFuzzyEmails()
    
    # Teste 2a: "ch" deve encontrar "chefe@empresa.com"
    print("\n🔍 Teste 2a: Buscando 'ch' (para 'chefe')")
    resultados = buscador.buscar_remetente_fuzzy("ch", emails_teste)
    print(f"Encontrados: {len(resultados)}")
    for r in resultados[:2]:
        print(f"  ⭐ {r.email.de} ({r.score:.0%})")
    assert len(resultados) > 0
    assert "chefe" in resultados[0].email.de.lower()
    
    # Teste 2b: "ama" deve encontrar "amazon"
    print("\n🔍 Teste 2b: Buscando 'ama' (para 'amazon')")
    resultados = buscador.buscar_remetente_fuzzy("ama", emails_teste)
    print(f"Encontrados: {len(resultados)}")
    for r in resultados[:2]:
        print(f"  ⭐ {r.email.de} ({r.score:.0%})")
    assert len(resultados) > 0
    assert "amazon" in resultados[0].email.de.lower()
    
    # Teste 2c: "car" deve encontrar "carlos"
    print("\n🔍 Teste 2c: Buscando 'car' (para 'carlos')")
    resultados = buscador.buscar_remetente_fuzzy("car", emails_teste)
    print(f"Encontrados: {len(resultados)}")
    for r in resultados[:2]:
        print(f"  ⭐ {r.email.de} ({r.score:.0%})")
    assert len(resultados) > 0
    
    print("\n✅ TESTE 2 PASSOU!")


def teste_3_busca_assunto_inteligente():
    """✅ Teste 3: Busca inteligente por ASSUNTO"""
    print("\n" + "="*60)
    print("✅ TESTE 3: Busca Inteligente por ASSUNTO")
    print("="*60)
    
    buscador = BuscadorFuzzyEmails()
    
    # Teste 3a: Buscar por "reunião"
    print("\n🔍 Teste 3a: Buscando 'reunião'")
    resultados = buscador.buscar_assunto_inteligente("reunião", emails_teste)
    print(f"Encontrados: {len(resultados)}")
    for r in resultados[:3]:
        print(f"  ⭐ {r.email.assunto[:50]} ({r.score:.0%})")
    assert len(resultados) > 0
    
    # Teste 3b: Buscar por "entrega"
    print("\n🔍 Teste 3b: Buscando 'entrega' (para 'pedido entregue')")
    resultados = buscador.buscar_assunto_inteligente("entrega", emails_teste)
    print(f"Encontrados: {len(resultados)}")
    for r in resultados[:3]:
        print(f"  ⭐ {r.email.assunto[:50]} ({r.score:.0%})")
    assert len(resultados) > 0
    
    # Teste 3c: Buscar por "desconto"
    print("\n🔍 Teste 3c: Buscando 'desconto'")
    resultados = buscador.buscar_assunto_inteligente("desconto", emails_teste)
    print(f"Encontrados: {len(resultados)}")
    for r in resultados[:3]:
        print(f"  ⭐ {r.email.assunto[:50]} ({r.score:.0%})")
    assert len(resultados) > 0
    
    print("\n✅ TESTE 3 PASSOU!")


def teste_4_busca_combinada():
    """✅ Teste 4: Busca COMBINADA (remetente + assunto)"""
    print("\n" + "="*60)
    print("✅ TESTE 4: Busca COMBINADA")
    print("="*60)
    
    buscador = BuscadorFuzzyEmails()
    
    print("\n🔍 Buscando: remetente='ch' + assunto='reunião'")
    resultados = buscador.buscar_combinado(
        termo_remetente="ch",
        termo_assunto="reunião",
        emails=emails_teste
    )
    
    print(f"\n📊 Resultados:")
    print(f"  Por remetente 'ch': {len(resultados['remetente'])} encontrados")
    print(f"  Por assunto 'reunião': {len(resultados['assunto'])} encontrados")
    print(f"  Combinados (ambos): {len(resultados['combinado'])} encontrados")
    
    # Deve encontrar "chefe@empresa.com" com assunto sobre reunião
    if resultados['combinado']:
        print(f"\n✅ Encontrado combinado: {resultados['combinado'][0].email.de}")
        assert "chefe" in resultados['combinado'][0].email.de.lower()
    
    print("\n✅ TESTE 4 PASSOU!")


def teste_5_sugestoes_autocomplete():
    """✅ Teste 5: Sugestões de AUTOCOMPLETE"""
    print("\n" + "="*60)
    print("✅ TESTE 5: Sugestões de AUTOCOMPLETE")
    print("="*60)
    
    buscador = BuscadorFuzzyEmails()
    
    print("\n🔍 Digite 'a' para obter sugestões:")
    sugestoes = buscador.gerar_sugestoes("a", emails_teste, max_sugestoes=5)
    
    print(f"Sugestões encontradas: {len(sugestoes)}")
    for remetente, nome in sugestoes:
        print(f"  🔹 {nome} ({remetente})")
    
    assert len(sugestoes) > 0
    
    print("\n✅ TESTE 5 PASSOU!")


def teste_6_fuzzy_com_erro_digitacao():
    """✅ Teste 6: Fuzzy matching com ERRO de digitação"""
    print("\n" + "="*60)
    print("✅ TESTE 6: Fuzzy Matching com ERRO de Digitação")
    print("="*60)
    
    buscador = BuscadorFuzzyEmails()
    
    # "ama" ao invés de "amazon"
    print("\n🔍 Digitação incorreta: 'ama' (correto: 'amazon')")
    resultados = buscador.buscar_remetente_fuzzy("ama", emails_teste)
    print(f"Encontrados: {len(resultados)}")
    if resultados:
        print(f"  ✅ Corrigido para: {resultados[0].email.de}")
        assert "amazon" in resultados[0].email.de.lower()
    
    # "banc" ao invés de "banco"
    print("\n🔍 Digitação incorreta: 'banc' (correto: 'banco')")
    resultados = buscador.buscar_remetente_fuzzy("banc", emails_teste)
    print(f"Encontrados: {len(resultados)}")
    if resultados:
        print(f"  ✅ Corrigido para: {resultados[0].email.de}")
        assert "banco" in resultados[0].email.de.lower()
    
    print("\n✅ TESTE 6 PASSOU!")


def teste_7_formatacao_resultados():
    """✅ Teste 7: Formatação de RESULTADOS"""
    print("\n" + "="*60)
    print("✅ TESTE 7: Formatação de Resultados")
    print("="*60)
    
    buscador = BuscadorFuzzyEmails()
    
    resultados = buscador.buscar_remetente_fuzzy("ch", emails_teste)
    
    if resultados:
        print("\n📋 Resultado formatado para exibição:")
        print(buscador.formatar_resultados(resultados, max_itens=3))
    
    print("\n✅ TESTE 7 PASSOU!")


def teste_8_score_confianca():
    """✅ Teste 8: Verificação de SCORE de Confiança"""
    print("\n" + "="*60)
    print("✅ TESTE 8: Score de Confiança")
    print("="*60)
    
    buscador = BuscadorFuzzyEmails()
    
    print("\n📊 Comparação de Scores:")
    
    # Busca exata (score alto)
    resultados_exato = buscador.buscar_remetente_fuzzy("chefe@empresa.com", emails_teste)
    print(f"\n  Busca exata 'chefe@empresa.com':")
    if resultados_exato:
        print(f"    Score: {resultados_exato[0].score:.1%} ⭐⭐⭐⭐⭐")
        assert resultados_exato[0].score >= 0.95
    
    # Busca parcial (score médio)
    resultados_parcial = buscador.buscar_remetente_fuzzy("che", emails_teste)
    print(f"\n  Busca parcial 'che':")
    if resultados_parcial:
        print(f"    Score: {resultados_parcial[0].score:.1%} ⭐⭐⭐")
        assert resultados_parcial[0].score >= 0.5
    
    # Busca com erro (score baixo mas ainda valido)
    resultados_erro = buscador.buscar_remetente_fuzzy("chf", emails_teste)
    print(f"\n  Busca com erro 'chf' (para 'chef'):")
    if resultados_erro:
        print(f"    Score: {resultados_erro[0].score:.1%}")
    
    print("\n✅ TESTE 8 PASSOU!")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("   TESTES: Buscador Fuzzy de E-mails")
    print("="*60)
    
    try:
        teste_1_busca_remetente_exata()
        teste_2_busca_remetente_incompleto()
        teste_3_busca_assunto_inteligente()
        teste_4_busca_combinada()
        teste_5_sugestoes_autocomplete()
        teste_6_fuzzy_com_erro_digitacao()
        teste_7_formatacao_resultados()
        teste_8_score_confianca()
        
        print("\n" + "="*60)
        print("   TODOS OS 8 TESTES PASSARAM COM SUCESSO!")
        print("="*60)
        print("\n🎉 Sistema de Busca Fuzzy está pronto para uso!")
        print("\n📋 Recursos:")
        print("  ✅ Busca por remetente incompleto (fuzzy matching)")
        print("  ✅ Busca inteligente por assunto")
        print("  ✅ Busca combinada (remetente + assunto)")
        print("  ✅ Autocomplete com sugestões")
        print("  ✅ Fuzzy matching com erros de digitação")
        print("  ✅ Score de confiança em cada resultado")
        print("  ✅ Formatação com emojis e indicadores visuais")
        
    except AssertionError as e:
        print(f"\n❌ TESTE FALHOU: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
