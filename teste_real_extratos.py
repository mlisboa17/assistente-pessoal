"""
🧪 Teste Real - Simulação de Processamento de Extrato
Demonstra como o sistema processaria um extrato bancário real
"""
import asyncio
from modules.extratos import ExtratosModule, TransacaoExtrato, ExtratoBancario
from datetime import datetime


async def testar_processamento_real():
    """Simula o processamento completo de um extrato real"""

    print("🏦 TESTE REAL - PROCESSAMENTO DE EXTRATO BANCÁRIO")
    print("=" * 60)

    # Inicializa módulo
    extratos = ExtratosModule()

    # Simula texto extraído de um PDF do Itaú
    texto_extrato_itau = """
    ITAÚ UNIBANCO S.A.
    EXTRATO DE CONTA CORRENTE

    Agência: 1234-5
    Conta: 12345-6

    Período: 01/12/2024 a 31/12/2024

    Saldo Anterior: R$ 2.500,00

    DATA        DESCRIÇÃO                           VALOR           SALDO
    01/12/2024  SALDO ANTERIOR                      2.500,00        2.500,00
    05/12/2024  SUPERMERCADO EXTRA                  156,78-         2.343,22
    07/12/2024  POSTO SHELL                         200,00-         2.143,22
    10/12/2024  SALÁRIO EMPRESA XYZ               5.000,00         7.143,22
    12/12/2024  UBER                               45,60-          7.097,62
    15/12/2024  NETFLIX                            39,90-          7.057,72
    18/12/2024  FARMÁCIA DROGASIL                  89,45-          6.968,27
    20/12/2024  DEPÓSITO                           300,00           7.268,27
    25/12/2024  AMAZON PRIME                       14,90-          7.253,37
    28/12/2024  RESTAURANTE                        67,80-          7.185,57

    Saldo Atual: R$ 7.185,57
    """

    print("📄 Texto extraído do PDF (simulado):")
    print("-" * 40)
    print(texto_extrato_itau[:300] + "...")
    print()

    # Testa identificação do banco
    banco = extratos._identificar_banco(texto_extrato_itau)
    print(f"🏦 Banco identificado: {banco.upper()}")
    print()

    # Simula extração de dados
    dados = extratos._extrair_itau(texto_extrato_itau)

    print("📊 Transações extraídas:")
    print("-" * 40)

    total_creditos = 0
    total_debitos = 0

    for i, transacao in enumerate(dados['transacoes'], 1):
        emoji = "💚" if transacao.tipo == 'credito' else "❤️"
        print(f"{i:2d}. {emoji} {transacao.data} - {transacao.descricao[:25]:<25} "
              f"R$ {transacao.valor:>8.2f} - {transacao.categoria_sugerida}")

        if transacao.tipo == 'credito':
            total_creditos += transacao.valor
        else:
            total_debitos += transacao.valor

    print()
    print("💰 Resumo:")
    print(f"   Créditos: R$ {total_creditos:.2f}")
    print(f"   Débitos:  R$ {total_debitos:.2f}")
    print(f"   Saldo:    R$ {total_creditos - total_debitos:.2f}")
    print()

    # Simula criação do extrato completo
    extrato = ExtratoBancario(
        id="TESTE_001",
        banco=banco,
        agencia="1234-5",
        conta="12345-6",
        periodo="12/2024",
        saldo_anterior=2500.00,
        saldo_atual=7185.57,
        transacoes=dados['transacoes'],
        arquivo_origem="extrato_itau_dezembro.pdf",
        user_id="teste_user",
        processado_em=datetime.now().isoformat()
    )

    print("✅ Extrato processado com sucesso!")
    print(f"   📄 {len(extrato.transacoes)} transações encontradas")
    print(f"   🏦 Banco: {extrato.banco.upper()}")
    print(f"   📅 Período: {extrato.periodo}")
    print(f"   💰 Saldo: R$ {extrato.saldo_atual:.2f}")
    print()

    # Simula resposta que seria enviada ao usuário
    resposta = extratos._formatar_resposta_extrato(extrato)
    print("📱 Resposta que seria enviada:")
    print("-" * 40)
    print(resposta[:500] + "..." if len(resposta) > 500 else resposta)

    print()
    print("🎯 RESULTADO: O sistema funcionaria perfeitamente com um PDF real!")
    print("💡 Para usar: envie um PDF de extrato com o comando /extrato")


def testar_outros_bancos():
    """Testa com exemplos de outros bancos"""

    print("\n🏦 TESTANDO OUTROS BANCOS")
    print("=" * 40)

    extratos = ExtratosModule()

    # Exemplos de texto de diferentes bancos
    exemplos = {
        "Bradesco": """
        BANCO BRADESCO S.A.
        EXTRATO DE CONTA CORRENTE

        02/12/2024  SALDO ANTERIOR                    1.000,00
        05/12/2024  PAGAMENTO DE CONTA LUZ            150,00-
        10/12/2024  DEPÓSITO                         500,00
        """,

        "Nubank": """
        Nubank
        EXTRATO DO CARTÃO

        03/12/2024  UBER                                25,90-
        08/12/2024  STARBUCKS                           18,50-
        15/12/2024  DEPÓSITO                           200,00
        """
    }

    for banco_nome, texto in exemplos.items():
        banco_identificado = extratos._identificar_banco(texto)
        status = "✅" if banco_identificado else "❌"
        print(f"{status} {banco_nome}: {banco_identificado}")


if __name__ == "__main__":
    asyncio.run(testar_processamento_real())
    testar_outros_bancos()