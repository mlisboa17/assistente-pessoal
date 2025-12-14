"""
🧪 Script de Teste - Módulo de Extratos Bancários
Testa o processamento de extratos sem precisar de interface
"""
import asyncio
import os
from modules.extratos import ExtratosModule


async def testar_extratos():
    """Testa o módulo de extratos"""
    print("🧪 Testando Módulo de Extratos Bancários")
    print("=" * 50)

    # Inicializa módulo
    extratos = ExtratosModule()

    # Testa identificação de bancos
    print("\n1. Testando identificação de bancos:")

    textos_teste = {
        "ITAÚ": "Extrato ITAÚ Unibanco - Conta Corrente",
        "BRADESCO": "Banco Bradesco S.A. - Extrato",
        "SANTANDER": "Santander Brasil - Conta",
        "NUBANK": "Nubank - Cartão de Crédito",
        "BANCO DO BRASIL": "Banco do Brasil - Extrato",
        "CAIXA": "Caixa Econômica Federal",
        "INTER": "Banco Inter - Extrato"
    }

    for banco, texto in textos_teste.items():
        identificado = extratos._identificar_banco(texto)
        status = "✅" if identificado == banco.lower().replace(' ', '_') else "❌"
        print(f"{status} {banco}: {identificado}")

    # Testa parsing de valores
    print("\n2. Testando parsing de valores:")

    valores_teste = [
        "1.234,56",
        "123,45",
        "1.234,56-",
        "R$ 1.234,56",
        "1234.56",
        "1,234.56"
    ]

    for valor_str in valores_teste:
        valor = extratos._parse_valor(valor_str)
        print(f"'{valor_str}' -> R$ {valor:.2f}")

    # Testa categorização
    print("\n3. Testando categorização:")

    descricoes_teste = [
        "Supermercado Extra",
        "Posto Shell",
        "Uber viagem",
        "Netflix mensal",
        "Farmácia Drogasil"
    ]

    for desc in descricoes_teste:
        categoria = extratos._categorizar_transacao(desc)
        print(f"'{desc}' -> {categoria}")

    print("\n4. Comandos disponíveis:")
    print("/extrato [anexo PDF] - Processar extrato bancário")
    print("/extratos - Listar extratos processados")

    print("\n5. Bancos suportados:")
    bancos = [
        "🏦 Itaú", "🏦 Bradesco", "🏦 Santander",
        "🏦 Nubank", "🏦 Banco do Brasil", "🏦 Caixa", "🏦 Inter"
    ]
    for banco in bancos:
        print(f"  {banco}")

    print("\n✅ Teste concluído!")
    print("\nPara usar: envie um PDF de extrato bancário com o comando /extrato")


if __name__ == "__main__":
    asyncio.run(testar_extratos())