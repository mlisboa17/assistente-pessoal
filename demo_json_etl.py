import asyncio
import json
from json_etl_extratos import normalizar_de_json

async def demonstrar_json_etl():
    print('🚀 DEMONSTRAÇÃO: Sistema JSON ETL para Extratos Bancários')
    print('=' * 60)

    # Primeiro, vamos criar um exemplo de JSON ETL
    exemplo_json = {
        'especificacao': 'ETL Extratos Bancários v1.0',
        'data_processamento': '2025-12-13T10:00:00Z',
        'fonte': 'pdf',
        'extrato': {
            'banco': 'BANCO_DO_BRASIL',
            'agencia': '1234',
            'conta': '56789-0',
            'titular': 'João Silva',
            'periodo': '01/11/2025 - 30/11/2025',
            'saldo_anterior': 1500.00,
            'saldo_atual': 1250.00
        },
        'transacoes_brutas': [
            {
                'linha_original': '31/10 31/10 Entrada PIX Recebido de MARIA S R$ 100,00',
                'data_lancamento': '31/10/2025',
                'data_movimento': '31/10/2025',
                'tipo_operacao': 'PIX',
                'tipo_movimento': 'CREDITO',
                'descricao_completa': 'PIX Recebido de MARIA S',
                'valor_bruto': 'R$ 100,00',
                'valor_numerico': 100.00,
                'categoria_sugerida': 'transferencias',
                'tags': ['pix', 'recebimento'],
                'historico_completo': '31/10 31/10 Entrada PIX Recebido de MARIA S R$ 100,00'
            },
            {
                'linha_original': '01/11 01/11 Saída TED Enviada R$ 350,00',
                'data_lancamento': '01/11/2025',
                'data_movimento': '01/11/2025',
                'tipo_operacao': 'TED',
                'tipo_movimento': 'DEBITO',
                'descricao_completa': 'TED Enviada',
                'valor_bruto': 'R$ 350,00',
                'valor_numerico': -350.00,
                'categoria_sugerida': 'transferencias',
                'tags': ['ted', 'pagamento'],
                'historico_completo': '01/11 01/11 Saída TED Enviada R$ 350,00'
            }
        ],
        'metadados_extracao': {
            'metodo_extracao': 'regex_texto',
            'tempo_processamento_segundos': 1.2,
            'total_transacoes_extraidas': 2,
            'taxa_sucesso_extracao': 1.0
        },
        'validacao_entrada': {
            'status': 'APTO_PARA_NORMALIZACAO'
        }
    }

    # Salvar exemplo
    with open('exemplo_json_etl.json', 'w', encoding='utf-8') as f:
        json.dump(exemplo_json, f, indent=2, ensure_ascii=False)

    print('✅ Exemplo de JSON ETL criado: exemplo_json_etl.json')
    print('📋 Estrutura do JSON ETL:')
    print('   • especificacao: Versão do formato')
    print('   • extrato: Informações básicas da conta')
    print('   • transacoes_brutas: Lista de transações extraídas')
    print('   • metadados_extracao: Informações sobre o processo de extração')
    print('   • validacao_entrada: Status para normalização')

    print('\n🔄 Agora vamos normalizar dados de um JSON real...')

    # Usar o JSON ETL do Santander que geramos
    try:
        dados_normalizados = await normalizar_de_json('exemplo_etl_santander.json')
        print('✅ Normalização de JSON ETL do Santander concluída!')
        print(f'   • {len(dados_normalizados.get("transacoes", []))} transações normalizadas')
        print(f'   • {len(dados_normalizados.get("transacoes_finais", []))} no formato final')
    except FileNotFoundError:
        print('⚠️ Arquivo exemplo_etl_santander.json não encontrado')
        print('💡 Execute primeiro: python teste_json_santander.py')
        print('🔄 Tentando usar o exemplo_etl_itau.json...')
        try:
            dados_normalizados = await normalizar_de_json('exemplo_etl_itau.json')
            print('✅ Normalização do exemplo JSON ETL do Itaú concluída!')
            print(f'   • {len(dados_normalizados.get("transacoes", []))} transações normalizadas')
            print(f'   • {len(dados_normalizados.get("transacoes_finais", []))} no formato final')
        except Exception as e:
            print(f'❌ Erro ao processar exemplo_etl_itau.json: {e}')

    # Testar PagSeguro
    print('\n🔄 Testando normalização do PagSeguro...')
    try:
        dados_pagseguro = await normalizar_de_json('teste_pagseguro_etl.json')
        print('✅ Normalização de JSON ETL do PagSeguro concluída!')
        print(f'   • {len(dados_pagseguro.get("transacoes", []))} transações normalizadas')
        print(f'   • {len(dados_pagseguro.get("transacoes_finais", []))} no formato final')
    except FileNotFoundError:
        print('⚠️ Arquivo teste_pagseguro_etl.json não encontrado')
        print('💡 Execute primeiro: python teste_json_pagseguro.py')
    except Exception as e:
        print(f'❌ Erro ao processar teste_pagseguro_etl.json: {e}')

if __name__ == "__main__":
    asyncio.run(demonstrar_json_etl())