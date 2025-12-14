import asyncio
import json
from normalizador_extratos import normalizar_extrato_completo
from json_etl_extratos import gerar_json_etl_extratos

async def testar_e_mostrar_json():
    print("🔄 Executando teste do PagSeguro...")
    from normalizador_extratos import normalizar_extrato_completo

    # Como não temos arquivo real do PagSeguro, vamos criar dados simulados
    # para testar a implementação
    print("⚠️  Arquivo real do PagSeguro não encontrado")
    print("💡 Criando dados simulados para teste...")

    # Criar dados simulados do PagSeguro
    dados_simulados = {
        'banco': 'PAGSEGURO',
        'agencia': '0001',
        'conta': '123456-7',
        'titular': 'João Silva',
        'periodo': '01/11/2025 - 30/11/2025',
        'saldo_anterior': 2500.00,
        'saldo_atual': 1800.00,
        'transacoes': [
            {
                'data': '05/11/2025',
                'descricao': 'RECEBIMENTO PIX DE MARIA SANTOS',
                'valor': 500.00,
                'tipo': 'credito',
                'categoria_sugerida': 'transferencias'
            },
            {
                'data': '10/11/2025',
                'descricao': 'PAGAMENTO PAGBANK MERCADO XYZ',
                'valor': -200.00,
                'tipo': 'debito',
                'categoria_sugerida': 'compras'
            },
            {
                'data': '15/11/2025',
                'descricao': 'RECEBIMENTO VENDA PRODUTO ABC',
                'valor': 150.00,
                'tipo': 'credito',
                'categoria_sugerida': 'vendas'
            },
            {
                'data': '20/11/2025',
                'descricao': 'PAGAMENTO TAXA SERVICO',
                'valor': -50.00,
                'tipo': 'debito',
                'categoria_sugerida': 'taxas'
            }
        ]
    }

    print("📊 Dados simulados criados:")
    print(json.dumps(dados_simulados, indent=2, ensure_ascii=False))

    # Salvar dados simulados como JSON para teste
    with open('dados_pagseguro_simulado.json', 'w', encoding='utf-8') as f:
        json.dump(dados_simulados, f, indent=2, ensure_ascii=False, default=str)
    print('💾 Dados simulados salvos em: dados_pagseguro_simulado.json')

    # Tentar executar teste de normalização com dados simulados
    print("\n🔄 Testando normalização com dados simulados...")

    try:
        resultado_normalizado = normalizar_extrato_completo(dados_simulados, 'pagseguro')

        print("✅ Normalização concluída!")
        print(f"   • {len(resultado_normalizado.get('transacoes', []))} transações normalizadas")
        print(f"   • {len(resultado_normalizado.get('transacoes_finais', []))} no formato final")

        # Salvar resultado
        with open('exemplo_extrato_pagseguro.json', 'w', encoding='utf-8') as f:
            json.dump(resultado_normalizado, f, indent=2, ensure_ascii=False, default=str)
        print('💾 Resultado salvo em: exemplo_extrato_pagseguro.json')

        # Gerar JSON ETL
        transacoes_brutas = []
        for transacao in resultado_normalizado.get('transacoes', []):
            transacao_bruta = {
                'linha_original': getattr(transacao, 'descricao_original', ''),
                'data_lancamento': getattr(transacao, 'data', ''),
                'data_movimento': getattr(transacao, 'data', ''),
                'tipo_operacao': getattr(transacao, 'categoria', ''),
                'tipo_movimento': 'CREDITO' if getattr(transacao, 'tipo', '') == 'ENTRADA' else 'DEBITO',
                'descricao_completa': getattr(transacao, 'descricao', ''),
                'valor_bruto': f"R$ {abs(getattr(transacao, 'valor', 0)):.2f}",
                'valor_numerico': getattr(transacao, 'valor', 0),
                'categoria_sugerida': getattr(transacao, 'categoria', ''),
                'tags': [],
                'historico_completo': getattr(transacao, 'descricao', '')
            }
            transacoes_brutas.append(transacao_bruta)

        metadados_extracao = {
            'metodo_extracao': 'simulado',
            'tempo_processamento_segundos': 0.1,
            'total_transacoes_extraidas': len(transacoes_brutas),
            'taxa_sucesso_extracao': 1.0
        }

        # Gerar JSON ETL
        json_etl = gerar_json_etl_extratos(resultado_normalizado, transacoes_brutas, metadados_extracao)

        if json_etl:
            print("✅ JSON ETL gerado com sucesso!")
            print("\n📄 JSON ETL gerado:")
            print(json_etl)

            # Salvar arquivo de teste
            arquivo_saida = 'teste_pagseguro_etl.json'
            with open(arquivo_saida, 'w', encoding='utf-8') as f:
                f.write(json_etl)
            print(f"\n💾 Arquivo salvo: {arquivo_saida}")

        else:
            print("❌ Falha ao gerar JSON ETL")

    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(testar_e_mostrar_json())