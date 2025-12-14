import asyncio
import json
from teste_normalizacao_etl import testar_normalizacao_banco
from json_etl_extratos import gerar_json_etl_extratos

async def testar_e_mostrar_json():
    print("🔄 Executando teste do Santander...")
    from teste_normalizacao_etl import testar_normalizacao_banco

    # Como não temos arquivo real do Santander, vamos criar dados simulados
    # para testar a implementação
    print("⚠️  Arquivo real do Santander não encontrado")
    print("💡 Criando dados simulados para teste...")

    # Criar dados simulados do Santander
    dados_simulados = {
        'banco': 'SANTANDER',
        'agencia': '1234',
        'conta': '56789-0',
        'titular': 'João Silva',
        'periodo': '01/12/2025 - 31/12/2025',
        'saldo_anterior': 5000.00,
        'saldo_atual': 3200.00,
        'transacoes': [
            {
                'data': '05/12/2025',
                'descricao': 'PIX ENVIADO PARA MARIA SANTOS',
                'valor': -500.00,
                'tipo': 'debito',
                'categoria_sugerida': 'transferencias'
            },
            {
                'data': '10/12/2025',
                'descricao': 'RECEBIMENTO SALARIO EMPRESA XYZ',
                'valor': 2500.00,
                'tipo': 'credito',
                'categoria_sugerida': 'salario'
            },
            {
                'data': '15/12/2025',
                'descricao': 'PAGAMENTO BOLETO LUZ',
                'valor': -150.00,
                'tipo': 'debito',
                'categoria_sugerida': 'contas_pagas'
            },
            {
                'data': '20/12/2025',
                'descricao': 'PIX RECEBIDO DE JOAO CARLOS',
                'valor': 800.00,
                'tipo': 'credito',
                'categoria_sugerida': 'transferencias'
            }
        ]
    }

    # Salvar dados simulados como JSON para teste
    with open('dados_santander_simulado.json', 'w', encoding='utf-8') as f:
        json.dump(dados_simulados, f, indent=2, ensure_ascii=False, default=str)
    print('💾 Dados simulados salvos em: dados_santander_simulado.json')

    # Tentar executar teste de normalização com dados simulados
    print("\n🔄 Testando normalização com dados simulados...")

    # Simular resultado de extração
    from normalizador_extratos import normalizar_extrato_completo

    try:
        resultado_normalizado = normalizar_extrato_completo(dados_simulados, 'santander')

        print("✅ Normalização concluída!")
        print(f"   • {len(resultado_normalizado.get('transacoes', []))} transações normalizadas")
        print(f"   • {len(resultado_normalizado.get('transacoes_finais', []))} no formato final")

        # Salvar resultado
        with open('exemplo_extrato_santander.json', 'w', encoding='utf-8') as f:
            json.dump(resultado_normalizado, f, indent=2, ensure_ascii=False, default=str)
        print('💾 Resultado salvo em: exemplo_extrato_santander.json')

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
        json_etl_santander = gerar_json_etl_extratos(resultado_normalizado, transacoes_brutas, metadados_extracao)

        # Salvar JSON ETL
        with open('exemplo_etl_santander.json', 'w', encoding='utf-8') as f:
            f.write(json_etl_santander)
        print('💾 JSON ETL salvo em: exemplo_etl_santander.json')

    except Exception as e:
        print(f"❌ Erro na normalização: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(testar_e_mostrar_json())