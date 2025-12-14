"""
🧪 Teste Direto - Processamento de Extrato Itaú PJ
Testa o processamento do arquivo sem interação do usuário
"""
import asyncio
import sys
import os
from pathlib import Path

# Adiciona o diretório atual ao path para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.extratos import ExtratosModule

async def teste_direto_itau_pj():
    """Testa processamento direto do extrato Itaú PJ"""

    # Caminho do arquivo
    arquivo_path = r"c:\Users\gabri\Downloads\Extratos\Itau_Pj.pdf"

    print("🧪 TESTE DIRETO - EXTRATO ITAÚ PJ")
    print("=" * 50)
    print(f"📄 Arquivo: {arquivo_path}")
    print("🔓 Sem senha (conforme informado)")
    print()

    # Verifica se arquivo existe
    if not os.path.exists(arquivo_path):
        print(f"❌ Arquivo não encontrado: {arquivo_path}")
        return

    # Inicializa módulo
    extratos = ExtratosModule()

    # Simula anexo
    anexo_simulado = {
        'file_name': 'Itau_Pj.pdf',
        'file_path': arquivo_path,
        'tipo': 'PDF'
    }

    print("🔄 Processando extrato...")
    print("-" * 40)

    try:
        # Processa sem senha
        resultado = await extratos._processar_extrato_attachment(anexo_simulado, "teste_direto", senha=None)

        if resultado and resultado != "SENHA_NECESSARIA":
            print("✅ Extrato processado com sucesso!")
            print("\n📊 RESULTADO BÁSICO:")
            print(resultado)

            # Análise detalhada
            try:
                if extratos.extratos:
                    extrato_obj = extratos.extratos[-1]
                    print("\n" + "="*60)
                    print("📊 ANÁLISE DETALHADA DAS TRANSAÇÕES")
                    print("="*60)

                    # Converte dict para objeto temporário
                    class TempExtrato:
                        def __init__(self, data):
                            for key, value in data.items():
                                setattr(self, key, value)

                    extrato_temp = TempExtrato(extrato_obj)

                    # Análise das transações
                    transacoes = extrato_temp.transacoes
                    categorizadas = []
                    nao_categorizadas = []

                    for t in transacoes:
                        # Trata tanto objetos quanto dicionários
                        categoria = t.get('categoria_sugerida') if isinstance(t, dict) else getattr(t, 'categoria_sugerida', '')
                        if categoria and categoria != 'outros':
                            categorizadas.append(t)
                        else:
                            nao_categorizadas.append(t)

                    print(f"📄 Total de transações: {len(transacoes)}")
                    print(f"✅ Categorizadas automaticamente: {len(categorizadas)}")
                    print(f"❓ Precisam de categorização manual: {len(nao_categorizadas)}")
                    print()

                    # Mostra primeiras transações categorizadas
                    if categorizadas:
                        print("✅ TRANSAÇÕES CATEGORIZADAS:")
                        print("-" * 50)
                        for t in categorizadas[:10]:
                            # Trata dicionários
                            tipo = t.get('tipo') if isinstance(t, dict) else getattr(t, 'tipo', 'debito')
                            data = t.get('data') if isinstance(t, dict) else getattr(t, 'data', '')
                            descricao = t.get('descricao') if isinstance(t, dict) else getattr(t, 'descricao', '')
                            valor = t.get('valor', 0.0) if isinstance(t, dict) else getattr(t, 'valor', 0.0)
                            categoria = t.get('categoria_sugerida') if isinstance(t, dict) else getattr(t, 'categoria_sugerida', '')

                            emoji = "💚" if tipo == 'credito' else "❤️"
                            categoria = categoria.replace('_', ' ').title()
                            print(f"{emoji} {data} | {descricao[:35]:35} | R$ {valor:>8.2f} | {categoria}")

                    # Mostra primeiras não categorizadas
                    if nao_categorizadas:
                        print("\n❓ TRANSAÇÕES NÃO CATEGORIZADAS:")
                        print("-" * 50)
                        for t in nao_categorizadas[:10]:
                            # Trata dicionários
                            tipo = t.get('tipo') if isinstance(t, dict) else getattr(t, 'tipo', 'debito')
                            data = t.get('data') if isinstance(t, dict) else getattr(t, 'data', '')
                            descricao = t.get('descricao') if isinstance(t, dict) else getattr(t, 'descricao', '')
                            valor = t.get('valor', 0.0) if isinstance(t, dict) else getattr(t, 'valor', 0.0)

                            emoji = "💚" if tipo == 'credito' else "❤️"
                            print(f"{emoji} {data} | {descricao[:40]:40} | R$ {valor:>8.2f}")

                    # Resumo financeiro
                    print("\n💰 RESUMO FINANCEIRO:")
                    print("-" * 30)
                    entradas = sum(t.get('valor', 0.0) if isinstance(t, dict) else getattr(t, 'valor', 0.0)
                                 for t in transacoes if (t.get('tipo') if isinstance(t, dict) else getattr(t, 'tipo', '')) == 'credito')
                    saidas = sum(t.get('valor', 0.0) if isinstance(t, dict) else getattr(t, 'valor', 0.0)
                               for t in transacoes if (t.get('tipo') if isinstance(t, dict) else getattr(t, 'tipo', '')) == 'debito')
                    print(f"💚 Entradas: R$ {entradas:>10.2f}")
                    print(f"❤️ Saídas:   R$ {saidas:>10.2f}")
                    print(f"📊 Saldo:    R$ {(entradas - saidas):>10.2f}")

                else:
                    print("⚠️ Não foi possível obter dados detalhados")

            except Exception as e:
                print(f"⚠️ Erro na análise: {e}")
                import traceback
                traceback.print_exc()

        elif resultado == "SENHA_NECESSARIA":
            print("❌ PDF requer senha, mas foi informado que não tem senha")
        else:
            print(f"❌ Falha no processamento: {resultado}")

    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(teste_direto_itau_pj())