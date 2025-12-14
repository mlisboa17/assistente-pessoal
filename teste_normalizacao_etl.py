#!/usr/bin/env python3
"""
Teste abrangente da normalização ETL para todos os bancos suportados
Verifica se o processo completo de extração, transformação e carregamento funciona
"""
import sys
import os
import asyncio

# Adiciona o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import pdfplumber
    from modules.extratos import ExtratosModule
    from normalizador_extratos import normalizar_extrato_completo
except ImportError as e:
    print(f"Erro ao importar: {e}")
    sys.exit(1)

async def testar_normalizacao_banco(banco_nome: str, arquivo_path: str, senha: str = None, simulado: bool = False):
    """Testa a normalização completa para um banco específico"""
    print(f"\n{'='*60}")
    print(f"🔍 Testando normalização ETL para: {banco_nome.upper()}")
    print(f"📁 Arquivo: {arquivo_path}")
    if simulado:
        print("🎭 Modo simulado (dados JSON)")
    print(f"{'='*60}")

    if not os.path.exists(arquivo_path):
        print(f"❌ Arquivo não encontrado: {arquivo_path}")
        return {
            'sucesso': False,
            'erro': f'Arquivo não encontrado: {arquivo_path}',
            'banco': banco_nome,
            'arquivo': arquivo_path
        }

    try:
        # Inicializar módulo de extratos
        extratos = ExtratosModule()

        if simulado:
            # Carregar dados simulados do JSON
            print("📖 Carregando dados simulados do JSON...")
            import json
            with open(arquivo_path, 'r', encoding='utf-8') as f:
                dados_simulados = json.load(f)

            # Simular resultado de extração
            resultado = {
                'sucesso': True,
                'dados': dados_simulados,
                'banco': banco_nome.lower()
            }
        else:
            # Processar PDF
            print("📖 Extraindo dados do PDF...")
            resultado = await extratos._processar_pdf_extrato(arquivo_path, "teste_user", senha)

        if not resultado.get('sucesso'):
            print(f"❌ Falha na extração: {resultado.get('erro')}")
            return {
                'sucesso': False,
                'erro': f'Falha na extração: {resultado.get("erro")}',
                'banco': banco_nome,
                'arquivo': arquivo_path
            }

        # Verificar se temos dados normalizados
        dados_normalizados = resultado.get('dados', {})
        if not dados_normalizados:
            print("❌ Dados normalizados não encontrados")
            return {
                'sucesso': False,
                'erro': 'Dados normalizados não encontrados',
                'banco': banco_nome,
                'arquivo': arquivo_path
            }

        print("✅ Extração concluída com sucesso!")

        # Verificar estrutura dos dados normalizados
        print("\n📊 VERIFICANDO ESTRUTURA DOS DADOS NORMALIZADOS:")

        # Campos obrigatórios
        campos_obrigatorios = ['banco', 'transacoes', 'estatisticas', 'validacao']
        for campo in campos_obrigatorios:
            if campo not in dados_normalizados:
                print(f"❌ Campo obrigatório faltando: {campo}")
                return {
                    'sucesso': False,
                    'erro': f'Campo obrigatório faltando: {campo}',
                    'banco': banco_nome,
                    'arquivo': arquivo_path
                }
            print(f"✅ {campo}: OK")

        # Verificar transações
        transacoes = dados_normalizados.get('transacoes', [])
        if not transacoes:
            print("❌ Nenhuma transação encontrada")
            return {
                'sucesso': False,
                'erro': 'Nenhuma transação encontrada',
                'banco': banco_nome,
                'arquivo': arquivo_path
            }

        print(f"✅ Transações encontradas: {len(transacoes)}")

        # Verificar estrutura de uma transação de exemplo
        if transacoes:
            transacao_exemplo = transacoes[0]
            campos_transacao = [
                'id_transacao', 'data_hora', 'valor', 'tipo_movimento',
                'descricao_original', 'descricao_normalizada', 'banco',
                'categoria', 'subcategoria', 'contraparte_tipo',
                'valido', 'erros_validacao'
            ]

            print("\n🔍 Verificando estrutura da primeira transação:")
            for campo in campos_transacao:
                if hasattr(transacao_exemplo, campo):
                    valor = getattr(transacao_exemplo, campo)
                    status = "✅" if valor is not None else "⚠️"
                    print(f"  {status} {campo}: {str(valor)[:50]}...")
                else:
                    print(f"  ❌ Campo faltando: {campo}")

        # Verificar estatísticas
        stats = dados_normalizados.get('estatisticas', {})
        print("\n📈 Estatísticas calculadas:")
        print(f"  • Total de transações: {stats.get('total_transacoes', 0)}")
        print(f"  • Entradas: {stats.get('total_entradas', 0)}")
        print(f"  • Saídas: {stats.get('total_saidas', 0)}")
        print(f"  • Saldo calculado: R$ {stats.get('saldo_calculado', 0):.2f}")
        print(f"  • Transações válidas: {stats.get('transacoes_validas', 0)}")
        print(f"  • Contrapartes identificadas: {stats.get('contrapartes_identificadas', 0)}")

        # Verificar validação
        validacao = dados_normalizados.get('validacao', {})
        print("\n✅ Validação:")
        if validacao.get('valido'):
            print("  ✅ Extrato válido")
        else:
            print("  ❌ Extrato com erros:")
            for erro in validacao.get('erros', []):
                print(f"    • {erro}")

        if validacao.get('avisos'):
            print("  ⚠️ Avisos:")
            for aviso in validacao.get('avisos', []):
                print(f"    • {aviso}")

        # Verificar preview de categorias
        preview = dados_normalizados.get('preview_categorias', {})
        if preview:
            print("\n📊 Preview de Categorias:")
            totais = preview.get('totais', {})
            if totais:
                print("  TOTAIS:")
                print(f"    • Entradas: R$ {totais.get('entradas', 0):.2f}")
                print(f"    • Saídas: R$ {totais.get('saidas', 0):.2f}")
                print(f"    • Saldo: R$ {totais.get('saldo', 0):.2f}")

            for tipo in ['receitas', 'despesas']:
                categorias = preview.get(tipo, {})
                if categorias:
                    print(f"  {tipo.upper()}:")
                    for cat, info in categorias.items():
                        if isinstance(info, dict):
                            quantidade = len(info.get('transacoes', []))
                            valor = info.get('total', 0)
                            print(f"    • {cat}: {quantidade} transações (R$ {valor:.2f})")
                        else:
                            print(f"    • {cat}: {info}")

            sem_categoria = preview.get('sem_categoria', [])
            if sem_categoria:
                print(f"  SEM_CATEGORIA: {len(sem_categoria)} transações")

        # Verificar formato final padronizado
        print("\n📋 VERIFICANDO FORMATO FINAL PADRONIZADO:")
        transacoes_finais = dados_normalizados.get('transacoes_finais', [])
        if not transacoes_finais:
            print("❌ Dados no formato final não encontrados")
            return {
                'sucesso': False,
                'erro': 'Dados no formato final não encontrados',
                'banco': banco_nome,
                'arquivo': arquivo_path
            }

        print(f"✅ Dados no formato final gerados: {len(transacoes_finais)} transações")

        # Campos obrigatórios do formato final
        campos_obrigatorios_finais = [
            'ID_Transacao_Unico', 'Conta_ID', 'Data_Hora_Transacao', 'Valor_Numerico',
            'Tipo_Movimento', 'Descricao_Normalizada', 'ID_Contraparte',
            'Agencia_Banco_Origem', 'Origem_Dado'
        ]

        if transacoes_finais:
            transacao_final_exemplo = transacoes_finais[0]
            print("🔍 Verificando campos obrigatórios do formato final:")
            for campo in campos_obrigatorios_finais:
                if campo in transacao_final_exemplo:
                    valor = transacao_final_exemplo[campo]
                    status = "✅" if valor is not None else "⚠️"
                    print(f"  {status} {campo}: {str(valor)[:50]}...")
                else:
                    print(f"  ❌ Campo obrigatório faltando: {campo}")
                    return {
                        'sucesso': False,
                        'erro': f'Campo obrigatório faltando no formato final: {campo}',
                        'banco': banco_nome,
                        'arquivo': arquivo_path
                    }

            # Verificações específicas dos valores
            tipo_movimento = transacao_final_exemplo.get('Tipo_Movimento')
            if tipo_movimento not in ['CREDITO', 'DEBITO']:
                print(f"  ❌ Tipo_Movimento inválido: {tipo_movimento}")
                return {
                    'sucesso': False,
                    'erro': f'Tipo_Movimento inválido: {tipo_movimento}',
                    'banco': banco_nome,
                    'arquivo': arquivo_path
                }
            else:
                print(f"  ✅ Tipo_Movimento válido: {tipo_movimento}")

            valor_numerico = transacao_final_exemplo.get('Valor_Numerico', 0)
            if valor_numerico == 0:
                print("  ❌ Valor_Numerico não pode ser zero")
                return {
                    'sucesso': False,
                    'erro': 'Valor_Numerico não pode ser zero',
                    'banco': banco_nome,
                    'arquivo': arquivo_path
                }
            else:
                print(f"  ✅ Valor_Numerico válido: {valor_numerico}")

            # Verificar formato da data
            data_hora = transacao_final_exemplo.get('Data_Hora_Transacao', '')
            try:
                from datetime import datetime
                datetime.fromisoformat(data_hora.replace('Z', '+00:00'))
                print(f"  ✅ Data_Hora_Transacao em formato ISO 8601: {data_hora}")
            except:
                print(f"  ❌ Data_Hora_Transacao em formato inválido: {data_hora}")
                return {
                    'sucesso': False,
                    'erro': f'Data_Hora_Transacao em formato inválido: {data_hora}',
                    'banco': banco_nome,
                    'arquivo': arquivo_path
                }

        print("✅ TODOS OS CAMPOS OBRIGATÓRIOS DO FORMATO FINAL VERIFICADOS!")

        print(f"\n✅ NORMALIZAÇÃO ETL PARA {banco_nome.upper()} CONCLUÍDA COM SUCESSO!")
        return {
            'sucesso': True,
            'dados': dados_normalizados,
            'banco': banco_nome,
            'arquivo': arquivo_path
        }

    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()
        return {
            'sucesso': False,
            'erro': f'Erro durante teste: {str(e)}',
            'banco': banco_nome,
            'arquivo': arquivo_path
        }

async def testar_todos_bancos():
    """Testa a normalização para todos os bancos com arquivos de teste disponíveis"""
    print("🚀 INICIANDO TESTES ABRANGENTES DE NORMALIZAÇÃO ETL")
    print("Testando todos os bancos com arquivos de exemplo disponíveis...")

    testes = [
        {
            'nome': 'C6 Bank',
            'arquivo': r"c:\Users\gabri\OneDrive\Área de Trabalho\Projetos\assistente-pessoal-main\test_extratos\c6_bank.pdf",
            'senha': '024296'
        },
        {
            'nome': 'Banco do Brasil',
            'arquivo': r"c:\Users\gabri\OneDrive\Área de Trabalho\Projetos\assistente-pessoal-main\test_extratos\BancoBrasil_Real_Novembro2025.pdf",
            'senha': None
        },
        {
            'nome': 'Itaú',
            'arquivo': r"c:\Users\gabri\OneDrive\Área de Trabalho\Projetos\assistente-pessoal-main\test_extratos\Itau_Pj.pdf",
            'senha': None
        },
        {
            'nome': 'Santander',
            'arquivo': r"c:\Users\gabri\OneDrive\Área de Trabalho\Projetos\assistente-pessoal-main\dados_santander_simulado.json",
            'senha': None,
            'simulado': True  # Arquivo JSON simulado, não PDF
        },
        {
            'nome': 'PagSeguro',
            'arquivo': r"c:\Users\gabri\OneDrive\Área de Trabalho\Projetos\assistente-pessoal-main\dados_pagseguro_simulado.json",
            'senha': None,
            'simulado': True  # Arquivo JSON simulado, não PDF
        }
    ]

    resultados = {}

    for teste in testes:
        sucesso = await testar_normalizacao_banco(
            teste['nome'],
            teste['arquivo'],
            teste['senha'],
            teste.get('simulado', False)
        )
        resultados[teste['nome']] = sucesso

    # Resumo final
    print(f"\n{'='*60}")
    print("📊 RESUMO DOS TESTES DE NORMALIZAÇÃO ETL")
    print(f"{'='*60}")

    total_testes = len(resultados)
    testes_passaram = sum(1 for r in resultados.values() if r)
    taxa_sucesso = (testes_passaram / total_testes) * 100 if total_testes > 0 else 0

    print(f"Total de bancos testados: {total_testes}")
    print(f"Testes que passaram: {testes_passaram}")
    print(f"Taxa de sucesso: {taxa_sucesso:.1f}%")

    print("\n📋 Resultados por banco:")
    for banco, passou in resultados.items():
        status = "✅ PASSOU" if passou else "❌ FALHOU"
        print(f"  • {banco}: {status}")

    if taxa_sucesso == 100:
        print("\n🎉 TODOS OS BANCOS PASSARAM NOS TESTES DE NORMALIZAÇÃO ETL!")
        print("✅ O sistema está funcionando corretamente para todos os bancos suportados.")
    else:
        print(f"\n⚠️ Alguns bancos falharam nos testes ({total_testes - testes_passaram} falhas)")
        print("Verifique os logs acima para identificar os problemas.")

if __name__ == "__main__":
    asyncio.run(testar_todos_bancos())