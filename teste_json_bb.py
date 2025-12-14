import asyncio
import json
from teste_normalizacao_etl import testar_normalizacao_banco
from json_etl_extratos import gerar_json_etl_extratos

async def testar_e_mostrar_json():
    print("🔄 Executando teste do Banco do Brasil...")
    from teste_normalizacao_etl import testar_normalizacao_banco

    # Executar teste e capturar resultado
    resultado = await testar_normalizacao_banco('Banco do Brasil', r'c:\Users\gabri\OneDrive\Área de Trabalho\Projetos\assistente-pessoal-main\test_extratos\BancoBrasil_Real_Novembro2025.pdf')

    print("\n🔍 Analisando resultado...")

    if resultado and 'dados' in resultado:
        dados = resultado['dados']

        # Mostrar estrutura geral
        print('\n📋 ESTRUTURA GERAL DOS DADOS NORMALIZADOS:')
        print(f'• Banco: {dados.get("banco")}')
        print(f'• Período: {dados.get("periodo", "N/A")}')
        print(f'• Total de transações: {len(dados.get("transacoes", []))}')
        print(f'• Transações finais: {len(dados.get("transacoes_finais", []))}')

        # Mostrar exemplo de transação normalizada
        if dados.get('transacoes'):
            print('\n🔍 EXEMPLO DE TRANSAÇÃO NORMALIZADA:')
            transacao = dados['transacoes'][0]
            print(f'• ID: {transacao.id}')
            print(f'• Data: {transacao.data}')
            print(f'• Descrição: {transacao.descricao[:50]}...')
            print(f'• Valor: R$ {transacao.valor:.2f}')
            print(f'• Tipo: {transacao.tipo}')
            print(f'• Categoria: {transacao.categoria}')

        # Mostrar exemplo do formato final
        if dados.get('transacoes_finais'):
            print('\n📊 EXEMPLO DO FORMATO FINAL (JSON-ready):')
            transacao_final = dados['transacoes_finais'][0]
            print(json.dumps(transacao_final, indent=2, ensure_ascii=False)[:800] + '...')

            # Salvar como JSON de exemplo (resultado normalizado)
            with open('exemplo_extrato_bb.json', 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=2, ensure_ascii=False, default=str)
            print('\n💾 Dados normalizados salvos em: exemplo_extrato_bb.json')

            # Também gerar JSON ETL no formato de entrada
            # Para isso, precisamos simular dados brutos
            transacoes_brutas = []
            for transacao in dados.get('transacoes', []):
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
                'metodo_extracao': 'regex_texto',
                'tempo_processamento_segundos': 1.2,
                'total_transacoes_extraidas': len(transacoes_brutas),
                'taxa_sucesso_extracao': 1.0
            }

            # Gerar JSON ETL
            json_etl_bb = gerar_json_etl_extratos(dados, transacoes_brutas, metadados_extracao)

            # Salvar JSON ETL
            with open('exemplo_etl_bb.json', 'w', encoding='utf-8') as f:
                f.write(json_etl_bb)
            print('💾 JSON ETL de entrada salvo em: exemplo_etl_bb.json')
    else:
        print("❌ Nenhum dado retornado do teste")
        print(f"Resultado: {resultado}")

if __name__ == "__main__":
    asyncio.run(testar_e_mostrar_json())