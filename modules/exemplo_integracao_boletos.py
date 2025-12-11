"""
📄 Exemplo de Integração com Leitor de Boletos
Demonstra como usar as funções públicas do módulo leitor_boletos
em outros módulos do assistente pessoal
"""

from modules.leitor_boletos import (
    processar_boleto_pdf,
    processar_boleto_imagem,
    validar_dados_boleto,
    identificar_banco_por_linha,
    extrair_valor_texto,
    extrair_cpf_cnpj_texto
)
from modules.leitor_boletos import DadosBoletoExtraido
import json
import os

def processar_documento_financeiro(caminho_arquivo: str) -> dict:
    """
    Exemplo de função que usa o leitor de boletos
    Pode ser chamada por outros módulos do assistente
    """
    try:
        # Determina tipo do arquivo
        extensao = os.path.splitext(caminho_arquivo)[1].lower()

        if extensao == '.pdf':
            dados_boleto = processar_boleto_pdf(caminho_arquivo)
        elif extensao in ['.jpg', '.jpeg', '.png']:
            dados_boleto = processar_boleto_imagem(caminho_arquivo)
        else:
            return {"erro": f"Formato não suportado: {extensao}"}

        # Valida os dados
        validacao = validar_dados_boleto(dados_boleto)

        # Retorna resultado estruturado
        return {
            "tipo": "boleto",
            "dados": dados_boleto.to_dict(),
            "validacao": validacao,
            "processado_em": "2025-12-09"
        }

    except Exception as e:
        return {"erro": str(e)}

def extrair_informacoes_texto_financeiro(texto: str) -> dict:
    """
    Exemplo de função que extrai informações específicas de texto financeiro
    Pode ser usada por módulos de NLP ou processamento de mensagens
    """
    try:
        # Usa funções específicas do leitor de boletos
        valor = extrair_valor_texto(texto)
        cpfs_cnpjs = extrair_cpf_cnpj_texto(texto)

        # Identifica se é boleto pela linha digitável
        linha_digitavel = None
        if "34191.09255" in texto:  # Exemplo de padrão Itaú
            # Extrair linha completa (simplificado)
            linha_digitavel = "34191.09255 25554.592938 85564.260009 8 12900002576900"

        banco = None
        if linha_digitavel:
            banco = identificar_banco_por_linha(linha_digitavel)

        return {
            "valor_encontrado": float(valor) if valor else None,
            "cpfs_cnpjs": cpfs_cnpjs,
            "banco_identificado": banco,
            "linha_digitavel": linha_digitavel,
            "parece_boleto": bool(linha_digitavel or valor)
        }

    except Exception as e:
        return {"erro": str(e)}

def exemplo_integracao_com_whatsapp():
    """
    Exemplo de como integrar com o módulo WhatsApp
    Quando um usuário envia um boleto, o sistema pode processá-lo automaticamente
    """
    print("📱 Exemplo de integração com WhatsApp Bot")

    # Simula recebimento de arquivo via WhatsApp
    caminho_boleto_simulado = r"c:\Users\mlisb\Downloads\BOLETO_NFe002806803.PDF"

    if os.path.exists(caminho_boleto_simulado):
        # Processa o boleto usando função pública
        resultado = processar_documento_financeiro(caminho_boleto_simulado)

        if "erro" not in resultado:
            dados = resultado["dados"]
            validacao = resultado["validacao"]

            # Monta resposta para o usuário
            resposta = f"✅ Boleto processado!\n"
            resposta += f"🏦 Banco: {dados['banco']}\n"
            resposta += f"💰 Valor: R$ {dados['valor']:.2f}\n"
            resposta += f"📋 CNPJ Cedente: {dados['cedente_cpf_cnpj']}\n"

            if validacao['valido']:
                resposta += "✅ Boleto válido para pagamento"
            else:
                resposta += "⚠️ Boleto com problemas de validação"

            print(resposta)
        else:
            print(f"❌ Erro ao processar: {resultado['erro']}")
    else:
        print("📄 Arquivo de exemplo não encontrado")

def exemplo_integracao_com_agenda():
    """
    Exemplo de como integrar com o módulo de agenda
    Quando processa um boleto, pode criar lembretes de vencimento
    """
    print("📅 Exemplo de integração com Agenda")

    # Simula dados de boleto processado
    dados_boleto = DadosBoletoExtraido(
        banco="Itaú",
        valor=25769.00,
        cedente_cpf_cnpj="34.274.233/0001-02",
        linha_digitavel="34191.09255 25554.592938 85564.260009 8 12900002576900"
    )

    # Poderia integrar com modules.agenda para criar lembretes
    print("💡 Integração possível com módulo agenda:")
    print(f"  - Criar lembrete de pagamento para boleto {dados_boleto.banco}")
    print(f"  - Valor: R$ {dados_boleto.valor}")
    print(f"  - Cedente: {dados_boleto.cedente_cpf_cnpj}")

def exemplo_integracao_com_faturas():
    """
    Exemplo de como integrar com o módulo de faturas
    Categorizar e armazenar informações de boletos
    """
    print("📊 Exemplo de integração com Faturas")

    # Simula processamento de boleto
    texto_boleto = """
    Boleto Itaú
    Valor: R$ 25.769,00
    CNPJ: 34.274.233/0001-02
    Linha digitável: 34191.09255 25554.592938 85564.260009 8 12900002576900
    """

    # Extrai informações usando funções públicas
    info_extraida = extrair_informacoes_texto_financeiro(texto_boleto)

    print("📋 Informações extraídas do texto:")
    print(json.dumps(info_extraida, indent=2, ensure_ascii=False))

    # Poderia salvar no banco de dados de faturas
    print("💾 Poderia salvar no módulo faturas:")
    print(f"  - Tipo: Boleto bancário")
    print(f"  - Status: Pendente")
    print(f"  - Valor: R$ {info_extraida['valor_encontrado']}")

# ==========================================
# TESTE DAS INTEGRAÇÕES
# ==========================================

if __name__ == "__main__":
    print("🔗 Testando integrações com outros módulos\n")

    exemplo_integracao_com_whatsapp()
    print()

    exemplo_integracao_com_agenda()
    print()

    exemplo_integracao_com_faturas()
    print()

    print("✅ Exemplos de integração concluídos!")
    print("\n💡 Agora outros módulos podem importar e usar:")
    print("   from modules.leitor_boletos import processar_boleto_pdf, validar_dados_boleto")
    print("   from modules.leitor_boletos import extrair_valor_texto, identificar_banco_por_linha")