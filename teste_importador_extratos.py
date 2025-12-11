"""
🧪 TESTES - Importador de Extratos Bancários e Cartão de Crédito

Como executar:
    python teste_importador_extratos.py

Exemplos de teste:
    - CSV genérico
    - Formato Itaú
    - Formato Cartão de Crédito
    - Detecção automática de tipo
    - Sugestão de categorias
"""
import json
from modules.importador_extratos import ImportadorExtratos, TipoExtrato


def print_header(titulo):
    """Imprime header de teste"""
    print("\n" + "=" * 60)
    print(f"  {titulo}")
    print("=" * 60)


def test_csv_generico():
    """Teste: Importar CSV genérico"""
    print_header("TESTE 1: CSV Genérico")
    
    importador = ImportadorExtratos()
    
    csv_content = """data,descricao,valor,saldo
01/12/2024,Salário,5000.00,15000.00
02/12/2024,Mercado Carrefour,250.50,14749.50
03/12/2024,Farmácia Drogasil,85.30,14664.20
04/12/2024,Uber para casa,45.00,14619.20
05/12/2024,Conta de Água,120.00,14499.20
06/12/2024,Netflix,49.90,14449.30
07/12/2024,Restaurante XYZ,180.00,14269.30
"""
    
    resultado = importador.importar(
        csv_content,
        tipo=TipoExtrato.CSV_GENERICO,
        nome_arquivo="extrato_dezembro.csv",
        user_id="user_123"
    )
    
    print(f"Status: {resultado['status']}")
    print(f"Movimentos importados: {resultado['movimentos']}")
    print(f"Valor total: R$ {resultado['total_valor']:.2f}")
    
    print("\n📋 Movimentos Importados:")
    importacao = importador.obter_movimentos(resultado['id_importacao'])
    for mov in importacao['movimentos']:
        print(f"  • {mov['data']} | {mov['descricao']:<30} | R$ {mov['valor']:>8.2f} | {mov['tipo']} | Categoria: {mov.get('categoria_sugerida', 'N/A')}")


def test_csv_com_ponto_separador():
    """Teste: CSV com ponto como separador decimal"""
    print_header("TESTE 2: CSV com Ponto (padrão internacional)")
    
    importador = ImportadorExtratos()
    
    csv_content = """data;descricao;valor
01/12/2024;Gasolina Posto Shell;150.75
02/12/2024;Almoço Restaurante;95.50
03/12/2024;Compra Livraria Cultura;320.00
"""
    
    resultado = importador.importar(
        csv_content,
        tipo=TipoExtrato.CSV_GENERICO,
        nome_arquivo="extrato_importado.csv",
        user_id="user_456"
    )
    
    print(f"Status: {resultado['status']}")
    print(f"Movimentos: {resultado['movimentos']}")
    
    importacao = importador.obter_movimentos(resultado['id_importacao'])
    print("\n📋 Movimentos:")
    for mov in importacao['movimentos']:
        cat = mov.get('categoria_sugerida', '?')
        print(f"  • {mov['data']} | {mov['descricao']:<40} | R$ {mov['valor']:>8.2f} | [{cat}]")


def test_detectar_tipo():
    """Teste: Detecção automática de tipo"""
    print_header("TESTE 3: Detecção Automática de Tipo")
    
    importador = ImportadorExtratos()
    
    # Simula conteúdo com assinatura Itaú
    conteudo_itau = """
    BANCO ITAU - EXTRATO DE CONTA
    AG. 0001 CC: 123456-7
    
    DATA        HISTORICO                      DEBITO          CREDITO        SALDO
    01/12/2024  SAQUE BANCO 24H            1.500,00                        5.234,56
    02/12/2024  DEP. SALÁRIO                           3.000,00            8.234,56
    """
    
    tipo_detectado = importador.detectar_tipo(conteudo_itau, "extrato.txt")
    print(f"Tipo detectado: {tipo_detectado.value}")
    
    # Simula conteúdo de cartão de crédito
    conteudo_cartao = """
    EXTRATO DE CARTÃO DE CRÉDITO
    Cartão terminado em 4521
    
    DATA        ESTABELECIMENTO                VALOR
    01/12/2024  MERCADO CARREFOUR            250,50
    02/12/2024  RESTAURANTE ITALIA           180,00
    """
    
    tipo_detectado = importador.detectar_tipo(conteudo_cartao, "cartao.txt")
    print(f"Tipo detectado (cartão): {tipo_detectado.value}")


def test_itau():
    """Teste: Formato Itaú"""
    print_header("TESTE 4: Formato Itaú")
    
    importador = ImportadorExtratos()
    
    extrato_itau = """
BANCO ITAU UNIBANCO S/A
AG. 1234 CC: 567890-1

EXTRATO CORRENTE
Per. de 01 a 05 de dez de 2024

DATA        HISTORICO                             DEBITO        CREDITO       SALDO
01/12/2024  SALDO ANTERIOR                                                   10.000,00
01/12/2024  DEP. SALÁRIO                                       5.000,00      15.000,00
02/12/2024  SAQUE 24H                            1.000,00                    14.000,00
03/12/2024  TRANSF ENVIADA BANCO 001-2          2.500,00                    11.500,00
04/12/2024  DEP. PESSOA FISICA                                   500,00      12.000,00
05/12/2024  TARIFA MENSAL                           50,00                    11.950,00
"""
    
    resultado = importador.importar(
        extrato_itau,
        tipo=TipoExtrato.BANCO_ITAU,
        nome_arquivo="extrato_itau.txt",
        user_id="user_itau"
    )
    
    print(f"Status: {resultado['status']}")
    print(f"Movimentos: {resultado['movimentos']}")
    
    if resultado['movimentos'] > 0:
        importacao = importador.obter_movimentos(resultado['id_importacao'])
        print("\n📋 Movimentos Itaú:")
        for mov in importacao['movimentos']:
            tipo_emoji = "📤" if mov['tipo'] == 'saida' else "📥"
            print(f"  {tipo_emoji} {mov['data']} | {mov['descricao']:<35} | R$ {mov['valor']:>8.2f} | Saldo: R$ {mov.get('saldo', 0):.2f}")


def test_cartao():
    """Teste: Cartão de Crédito"""
    print_header("TESTE 5: Cartão de Crédito")
    
    importador = ImportadorExtratos()
    
    extrato_cartao = """
BANCO ABC - CARTÃO DE CRÉDITO
Cartão terminado em 4567
Período: 01 a 30 de dezembro de 2024

DATA        ESTABELECIMENTO                    VALOR
01/12/2024  MERCADO EXTRA                      235,50
02/12/2024  RESTAURANTE ITALIA                 185,00
03/12/2024  UBER TECHNOLOGIES                   45,00
04/12/2024  SHELL GASOLINA                     120,00
05/12/2024  FARMACIA DROGASIL                  95,30
06/12/2024  NETFLIX BRASIL                      49,90
07/12/2024  SPOTIFY BRASIL                      14,90
08/12/2024  LOJA SHOPEE                        156,00
09/12/2024  PAGTO FACULDADE                  1.500,00
"""
    
    resultado = importador.importar(
        extrato_cartao,
        tipo=TipoExtrato.CARTAO_CREDITO,
        nome_arquivo="cartao_credito.txt",
        user_id="user_card"
    )
    
    print(f"Status: {resultado['status']}")
    print(f"Movimentos: {resultado['movimentos']}")
    print(f"Total gasto: R$ {resultado['total_valor']:.2f}")
    
    if resultado['movimentos'] > 0:
        importacao = importador.obter_movimentos(resultado['id_importacao'])
        print("\n🛍️ Transações do Cartão:")
        for mov in importacao['movimentos']:
            cat = mov.get('categoria_sugerida', 'outros')
            cat_emoji = {
                'alimentacao': '🍔',
                'combustivel': '⛽',
                'transporte': '🚗',
                'saude': '💊',
                'lazer': '🎮',
                'educacao': '📚',
                'tecnologia': '📱',
                'beleza': '💇',
                'vestuario': '👕',
                'outros': '📦'
            }.get(cat, '📦')
            
            print(f"  {cat_emoji} {mov['data']} | {mov['descricao']:<35} | R$ {mov['valor']:>8.2f}")


def test_sugestoes_categoria():
    """Teste: Sugestão automática de categorias"""
    print_header("TESTE 6: Sugestão Automática de Categorias")
    
    importador = ImportadorExtratos()
    
    csv_content = """data,descricao,valor
01/12/2024,Mercado Carrefour,250.50
02/12/2024,Consulta Dr. Silva,150.00
03/12/2024,Gasolina Ipiranga,120.00
04/12/2024,Netflix Streaming,49.90
05/12/2024,Amazon Livro,89.90
06/12/2024,Salão de Beleza,150.00
07/12/2024,Loja Renner,320.00
08/12/2024,Smartfit Academia,79.90
09/12/2024,Cinema Ingresso,60.00
10/12/2024,iPhone 15 Apple,6000.00
"""
    
    resultado = importador.importar(
        csv_content,
        tipo=TipoExtrato.CSV_GENERICO,
        nome_arquivo="teste_categorias.csv",
        user_id="user_cat"
    )
    
    print("📊 Sugestões de Categorias Automáticas:\n")
    importacao = importador.obter_movimentos(resultado['id_importacao'])
    
    categorias = {}
    for mov in importacao['movimentos']:
        cat = mov.get('categoria_sugerida', 'outros')
        if cat not in categorias:
            categorias[cat] = []
        categorias[cat].append(mov)
    
    for categoria, movimentos in sorted(categorias.items()):
        total_cat = sum(m['valor'] for m in movimentos)
        print(f"\n{categoria.upper()}:")
        for mov in movimentos:
            print(f"  • {mov['descricao']:<40} R$ {mov['valor']:>8.2f}")
        print(f"  💰 Subtotal: R$ {total_cat:.2f}")


def test_listar_importacoes():
    """Teste: Listar importações"""
    print_header("TESTE 7: Listar Importações")
    
    importador = ImportadorExtratos()
    
    # Faz várias importações
    extratos = [
        ("extrato_nov.csv", TipoExtrato.CSV_GENERICO, "data,desc,valor\n01/11/2024,Compra,100"),
        ("extrato_dez.csv", TipoExtrato.CSV_GENERICO, "data,desc,valor\n01/12/2024,Compra,200"),
        ("cartao_dez.csv", TipoExtrato.CARTAO_CREDITO, "data,desc,valor\n01/12/2024,Shop,300"),
    ]
    
    for nome, tipo, conteudo in extratos:
        importador.importar(conteudo, tipo=tipo, nome_arquivo=nome, user_id="user_123")
    
    importacoes = importador.listar_importacoes(user_id="user_123", limit=5)
    
    print(f"Total de importações encontradas: {len(importacoes)}\n")
    for imp in importacoes:
        print(f"📄 {imp['nome_arquivo']}")
        print(f"   Tipo: {imp['tipo']}")
        print(f"   Data: {imp['data_importacao'][:10]}")
        print(f"   Movimentos: {imp['metadata'].get('total_movimentos', 0)}")
        print()


def test_resumo_completo():
    """Teste: Resumo completo com todas as funcionalidades"""
    print_header("TESTE 8: RESUMO COMPLETO")
    
    importador = ImportadorExtratos()
    
    csv_content = """data,descricao,valor
01/12/2024,Salário Dezembro,5000.00
02/12/2024,Mercado Carrefour,-250.50
03/12/2024,Gasolina Ipiranga,-120.00
04/12/2024,Água e Luz,-200.00
05/12/2024,Restaurante XYZ,-180.00
06/12/2024,Netflix,-49.90
07/12/2024,Consultório Médico,-150.00
08/12/2024,Academia Smartfit,-79.90
09/12/2024,Presença Freelance,800.00
10/12/2024,Uber,-45.00
"""
    
    resultado = importador.importar(
        csv_content,
        tipo=TipoExtrato.CSV_GENERICO,
        nome_arquivo="extrato_completo_dezembro.csv",
        user_id="user_final"
    )
    
    print(f"""
📊 RESULTADO DA IMPORTAÇÃO
{'=' * 40}
✅ Status: {resultado['status'].upper()}
📈 Movimentos: {resultado['movimentos']}
💰 Valor Total: R$ {abs(resultado['total_valor']):.2f}

📅 Período: {resultado['metadata'].get('periodo_inicio')} a {resultado['metadata'].get('periodo_fim')}
💵 Entradas: R$ {resultado['metadata'].get('total_entradas', 0):.2f}
💸 Saídas: R$ {resultado['metadata'].get('total_saidas', 0):.2f}
""")
    
    importacao = importador.obter_movimentos(resultado['id_importacao'])
    
    print("📋 MOVIMENTOS DETALHADOS:\n")
    print(f"{'Data':<12} {'Descrição':<30} {'Valor':>10} {'Tipo':<8} {'Categoria':<15}")
    print("-" * 80)
    
    for mov in importacao['movimentos']:
        tipo_emoji = "📤" if mov['tipo'] == 'saida' else "📥"
        cat = mov.get('categoria_sugerida', 'outros')
        valor_str = f"R$ {mov['valor']:.2f}"
        
        if mov['tipo'] == 'saida':
            valor_str = f"-R$ {mov['valor']:.2f}"
        
        print(f"{mov['data']} {tipo_emoji} {mov['descricao']:<26} {valor_str:>10} {mov['tipo']:<8} {cat:<15}")


def main():
    """Executa todos os testes"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  🧪 TESTES - IMPORTADOR DE EXTRATOS BANCÁRIOS".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    
    try:
        test_csv_generico()
        test_csv_com_ponto_separador()
        test_detectar_tipo()
        test_itau()
        test_cartao()
        test_sugestoes_categoria()
        test_listar_importacoes()
        test_resumo_completo()
        
        print("\n")
        print("╔" + "=" * 58 + "╗")
        print("║" + "✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!".center(58) + "║")
        print("╚" + "=" * 58 + "╝")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE OS TESTES: {str(e)}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
