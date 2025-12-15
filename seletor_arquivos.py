"""
🗂️ Seletor de Arquivos - Teste de Extratos
Permite selecionar e processar PDFs de extratos bancários
"""
import os
import sys
import asyncio
from pathlib import Path
from modules.extratos import ExtratosModule
import tkinter as tk
from tkinter import filedialog

# Para testar PDFs
try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


def testar_pdf(arquivo_path, senha=None):
    """Testa se o PDF pode ser aberto e se precisa de senha"""
    if not PDF_AVAILABLE:
        return "ERRO", "pdfplumber não instalado"

    try:
        # Tenta abrir com senha se fornecida
        pdf = pdfplumber.open(arquivo_path, password=senha)
        pdf.close()
        return "OK", None
    except Exception as e:
        error_msg = str(e).lower()
        if "password" in error_msg or "encrypted" in error_msg or "crypt" in error_msg:
            return "SENHA_NECESSARIA", None
        else:
            return "ERRO", str(e)


def pedir_senha():
    """Pede senha para PDF protegido"""
    print("\n🔒 PDF PROTEGIDO POR SENHA")
    print("Este arquivo requer uma senha para ser aberto.")
    senha = input("Digite a senha do PDF: ").strip()
    return senha if senha else None


def analisar_transacoes(extrato):
    """Analisa transações categorizadas vs não categorizadas"""
    categorizadas = []
    nao_categorizadas = []

    # Trata tanto objetos quanto dicionários
    transacoes = extrato.transacoes if hasattr(extrato, 'transacoes') else extrato.get('transacoes', [])

    for transacao in transacoes:
        # Se for dicionário, acessa como dict, senão como atributo
        categoria = transacao.get('categoria_sugerida') if isinstance(transacao, dict) else getattr(transacao, 'categoria_sugerida', '')

        if categoria and categoria != 'outros':
            categorizadas.append(transacao)
        else:
            nao_categorizadas.append(transacao)

    return categorizadas, nao_categorizadas


def revisar_categorias_transacoes(transacoes):
    """Permite ao usuário revisar e modificar categorias das transações"""
    print("📝 REVISÃO INTERATIVA DE CATEGORIAS")
    print("=" * 50)
    print("Para cada transação, você pode:")
    print("• Pressionar ENTER para manter a categoria sugerida")
    print("• Digitar uma nova categoria existente")
    print("• Digitar uma nova categoria personalizada (será adicionada à lista)")
    print("• Digitar 'pular' para deixar sem categoria")
    print("• Digitar 'lista' para ver categorias disponíveis")
    print()

    categorias_disponiveis = [
        'alimentacao', 'transporte', 'combustivel', 'saude', 'educacao',
        'assinaturas', 'lazer', 'compras', 'servicos', 'impostos',
        'investimentos', 'transferencias', 'salario', 'freelance', 'outros'
    ]

    transacoes_revisadas = []

    for i, transacao in enumerate(transacoes, 1):
        # Obtém dados da transação
        if isinstance(transacao, dict):
            data = transacao.get('data', 'N/A')
            descricao = transacao.get('descricao', 'N/A')
            valor = transacao.get('valor', 0.0)
            tipo = transacao.get('tipo', 'N/A')
            categoria_atual = transacao.get('categoria', 'sem_categoria')
        else:
            data = getattr(transacao, 'data', 'N/A')
            descricao = getattr(transacao, 'descricao', 'N/A')
            valor = getattr(transacao, 'valor', 0.0)
            tipo = getattr(transacao, 'tipo', 'N/A')
            categoria_atual = getattr(transacao, 'categoria', 'sem_categoria')

        # Mostra a transação
        emoji = "💚" if tipo == 'credito' else "❤️"
        print(f"{i:2d}. {emoji} {data} | {descricao[:40]:40} | R$ {valor:>10.2f}")
        print(f"    Categoria atual: '{categoria_atual}'")

        # Loop para obter nova categoria
        while True:
            resposta = input("    Nova categoria (ENTER para manter, 'lista' para ver opções): ").strip().lower()

            if resposta == '':
                # Mantém a categoria atual
                break
            elif resposta == 'lista':
                print(f"    Categorias disponíveis: {', '.join(categorias_disponiveis)}")
                continue
            elif resposta == 'pular':
                categoria_atual = 'sem_categoria'
                break
            elif resposta in categorias_disponiveis:
                categoria_atual = resposta
                break
            else:
                # Verifica se é uma nova categoria
                print(f"    📝 '{resposta}' não está na lista de categorias.")
                adicionar = input("    Deseja adicionar como nova categoria? (S/N): ").strip().upper()
                if adicionar == 'S':
                    categorias_disponiveis.append(resposta)
                    categoria_atual = resposta
                    print(f"    ✅ Nova categoria '{resposta}' adicionada!")
                    break
                else:
                    print("    ❌ Tente novamente ou digite 'lista' para ver opções.")
                    continue

        # Atualiza a transação com a nova categoria
        if isinstance(transacao, dict):
            transacao_copy = transacao.copy()
            transacao_copy['categoria'] = categoria_atual
        else:
            transacao_copy = transacao  # Para objetos dataclasses, modificar diretamente
            if hasattr(transacao, 'categoria'):
                transacao.categoria = categoria_atual

        transacoes_revisadas.append(transacao_copy)
        print(f"    ✅ Categoria definida: '{categoria_atual}'")
        print()

    print("🎉 Revisão de categorias concluída!")
    return transacoes_revisadas


def mostrar_analise_detalhada(extrato):
    """Mostra análise detalhada das transações"""
    categorizadas, nao_categorizadas = analisar_transacoes(extrato)

    print("\n" + "="*60)
    print("📊 ANÁLISE DETALHADA DAS TRANSAÇÕES")
    print("="*60)

    # Trata tanto objetos quanto dicionários
    transacoes = extrato.transacoes if hasattr(extrato, 'transacoes') else extrato.get('transacoes', [])
    saldo_anterior = extrato.saldo_anterior if hasattr(extrato, 'saldo_anterior') else extrato.get('saldo_anterior', 0.0)
    saldo_atual = extrato.saldo_atual if hasattr(extrato, 'saldo_atual') else extrato.get('saldo_atual', 0.0)

    # Resumo geral
    total_transacoes = len(transacoes)
    total_categorizadas = len(categorizadas)
    total_nao_categorizadas = len(nao_categorizadas)

    print(f"📄 Total de transações: {total_transacoes}")
    print(f"✅ Categorizadas automaticamente: {total_categorizadas}")
    print(f"❓ Precisam de categorização manual: {total_nao_categorizadas}")
    print()

    # Transações categorizadas
    if categorizadas:
        print("✅ TRANSAÇÕES CATEGORIZADAS AUTOMATICAMENTE:")
        print("-" * 50)
        for transacao in categorizadas[:15]:  # Mostra primeiras 15
            # Trata tanto objetos quanto dicionários
            tipo = transacao.get('tipo') if isinstance(transacao, dict) else getattr(transacao, 'tipo', 'debito')
            data = transacao.get('data') if isinstance(transacao, dict) else getattr(transacao, 'data', '')
            descricao = transacao.get('descricao') if isinstance(transacao, dict) else getattr(transacao, 'descricao', '')
            valor = transacao.get('valor', 0.0) if isinstance(transacao, dict) else getattr(transacao, 'valor', 0.0)
            categoria = transacao.get('categoria_sugerida') if isinstance(transacao, dict) else getattr(transacao, 'categoria_sugerida', '')

            emoji = "💚" if tipo == 'credito' else "❤️"
            categoria = categoria.replace('_', ' ').title()
            print(f"{emoji} {data} | {descricao[:35]:35} | R$ {valor:>8.2f} | {categoria}")

        if len(categorizadas) > 15:
            print(f"... e mais {len(categorizadas) - 15} transações categorizadas")
        print()

    # Transações não categorizadas
    if nao_categorizadas:
        print("❓ TRANSAÇÕES QUE PRECISAM DE CATEGORIZAÇÃO MANUAL:")
        print("-" * 50)
        for transacao in nao_categorizadas[:10]:  # Mostra primeiras 10
            # Trata tanto objetos quanto dicionários
            tipo = transacao.get('tipo') if isinstance(transacao, dict) else getattr(transacao, 'tipo', 'debito')
            data = transacao.get('data') if isinstance(transacao, dict) else getattr(transacao, 'data', '')
            descricao = transacao.get('descricao') if isinstance(transacao, dict) else getattr(transacao, 'descricao', '')
            valor = transacao.get('valor', 0.0) if isinstance(transacao, dict) else getattr(transacao, 'valor', 0.0)

            emoji = "💚" if tipo == 'credito' else "❤️"
            print(f"{emoji} {data} | {descricao[:40]:40} | R$ {valor:>8.2f}")

        if len(nao_categorizadas) > 10:
            print(f"... e mais {len(nao_categorizadas) - 10} transações")
        print()

        print("💡 DICAS PARA CATEGORIZAÇÃO:")
        print("   • Use /categoria [id] [categoria] para categorizar")
        print("   • Categorias disponíveis: alimentacao, transporte, saude, assinaturas, etc.")
        print()

    # Resumo financeiro
    print("💰 RESUMO FINANCEIRO:")
    print("-" * 30)

    entradas = sum(t.get('valor', 0.0) if isinstance(t, dict) else getattr(t, 'valor', 0.0)
                   for t in transacoes if (t.get('tipo') if isinstance(t, dict) else getattr(t, 'tipo', '')) == 'credito')
    saidas = sum(t.get('valor', 0.0) if isinstance(t, dict) else getattr(t, 'valor', 0.0)
                 for t in transacoes if (t.get('tipo') if isinstance(t, dict) else getattr(t, 'tipo', '')) == 'debito')

    print(f"💚 Entradas (créditos): R$ {entradas:>10.2f}")
    print(f"❤️ Saídas (débitos):   R$ {saidas:>10.2f}")
    print(f"📊 Saldo do período:   R$ {(entradas - saidas):>10.2f}")
    print()

    # Saldo da conta
    print("🏦 SALDO DA CONTA:")
    print("-" * 20)
    print(f"Saldo Anterior: R$ {saldo_anterior:>10.2f}")
    print(f"Saldo Atual:    R$ {saldo_atual:>10.2f}")
    print(f"Diferença:      R$ {(saldo_atual - saldo_anterior):>10.2f}")
    print()

    # Revisão de categorias via interface web
    print("🌐 REVISÃO DE CATEGORIAS:")
    print("-" * 30)
    print("📱 Abrindo interface web para revisão visual...")
    print("📝 Acesse: http://localhost:5001/revisao-categorias")
    print("💡 Use o navegador para revisar e confirmar as categorias")
    print()

    # Tentar abrir o navegador automaticamente
    try:
        import webbrowser
        webbrowser.open('http://localhost:5501/revisao-categorias')
        print("✅ Navegador aberto automaticamente!")
    except:
        print("ℹ️ Abra o navegador manualmente no endereço acima")

    print()
    input("Pressione ENTER quando terminar a revisão no navegador...")

    print()
    # Integração
    print("🔄 INTEGRAÇÃO COM SISTEMA:")
    print("-" * 30)
    print("✅ Transações importadas para controle financeiro")
    print("✅ Categorias revisadas e confirmadas pelo usuário")
    print("📝 Use /extratos para ver histórico completo")
    print("📊 Use /gastos para ver resumo financeiro")


def escolher_arquivo():
    """Interface gráfica para escolher arquivo PDF/TXT"""
    # Cria janela raiz (oculta)
    root = tk.Tk()
    root.withdraw()

    # Configura tipos de arquivo
    filetypes = [
        ('Arquivos PDF', '*.pdf'),
        ('Arquivos TXT', '*.txt'),
        ('Todos os arquivos', '*.*')
    ]

    # Abre diálogo de seleção
    arquivo_path = filedialog.askopenfilename(
        title="Selecione um arquivo de extrato bancário",
        filetypes=filetypes,
        initialdir=os.getcwd()
    )

    root.destroy()

    if not arquivo_path:
        return None

    # Determina o tipo baseado na extensão
    path_obj = Path(arquivo_path)
    if path_obj.suffix.lower() == '.pdf':
        tipo = 'PDF'
    elif path_obj.suffix.lower() == '.txt':
        tipo = 'TXT'
    else:
        tipo = 'DESCONHECIDO'

    return (tipo, path_obj)


async def simular_processamento_txt(extratos, texto, anexo, user_id):
    """Simula processamento de PDF para arquivos TXT"""
    try:
        # Identifica o banco
        banco = extratos._identificar_banco(texto)
        if not banco:
            return "❌ Banco não identificado no arquivo TXT"

        # Extrai dados específicos do banco
        dados = extratos._extrair_dados_banco(texto, banco)

        if not dados['transacoes']:
            return "⚠️ Nenhuma transação encontrada no arquivo"

        # Cria objeto extrato
        from uuid import uuid4
        from datetime import datetime

        extrato = {
            'id': str(uuid4())[:8],
            'banco': banco,
            'agencia': dados.get('agencia', ''),
            'conta': dados.get('conta', ''),
            'periodo': dados.get('periodo', ''),
            'saldo_anterior': dados.get('saldo_anterior', 0.0),
            'saldo_atual': dados.get('saldo_atual', 0.0),
            'transacoes': [t.__dict__ if hasattr(t, '__dict__') else t for t in dados['transacoes']],
            'arquivo_origem': anexo['file_path'],
            'user_id': user_id,
            'processado_em': datetime.now().isoformat()
        }

        # Salva
        extratos.extratos.append(extrato)
        extratos._save_data()

        # Integra com módulo de finanças
        await extratos._integrar_com_financas(type('Extrato', (), extrato)(), user_id)

        # Formata resposta
        return extratos._formatar_resposta_extrato(type('Extrato', (), extrato)())

    except Exception as e:
        return f"❌ Erro no processamento TXT: {e}"


async def processar_arquivo_por_caminho():
    """Processa arquivo informado diretamente pelo caminho"""

    print("📁 PROCESSAMENTO POR CAMINHO DIRETO")
    print("-" * 40)

    # Pede o caminho do arquivo
    caminho_str = input("Digite o caminho completo do arquivo: ").strip()

    if not caminho_str:
        print("❌ Caminho não informado.")
        return

    # Converte para Path
    arquivo = Path(caminho_str)

    if not arquivo.exists():
        print(f"❌ Arquivo não encontrado: {arquivo.absolute()}")
        return

    print(f"\n📄 Arquivo encontrado: {arquivo.name}")
    print(f"📂 Caminho: {arquivo.absolute()}")
    print()

    # Determina o tipo baseado na extensão
    if arquivo.suffix.lower() == '.pdf':
        tipo = 'PDF'
    elif arquivo.suffix.lower() == '.txt':
        tipo = 'TXT'
    else:
        tipo = 'DESCONHECIDO'
        print(f"❌ Tipo de arquivo não suportado: {arquivo.suffix}")
        return

    print(f"📋 Tipo: {tipo}")
    print()

    # Confirmação
    confirmar = input("Processar este arquivo? (S/N): ").strip().upper()
    if confirmar != "S":
        print("❌ Cancelado pelo usuário.")
        return

    print("\n🔄 Processando extrato...")
    print("-" * 40)

    # Inicializa módulo
    extratos = ExtratosModule()

    # Simula anexo (como seria no WhatsApp/Telegram)
    anexo_simulado = {
        'file_name': arquivo.name,
        'file_path': str(arquivo.absolute()),
        'tipo': tipo  # Adiciona tipo para processamento especial
    }

    # Processa
    try:
        senha = None

        # Para PDFs, pergunta se tem senha
        if tipo == "PDF":
            tem_senha = input("Este PDF está protegido por senha? (S/N): ").strip().upper()
            if tem_senha == "S":
                senha = pedir_senha()
                if not senha:
                    print("❌ Senha não fornecida.")
                    return

                # Testa se a senha funciona
                print("🔍 Testando senha...")
                status, erro = testar_pdf(str(arquivo.absolute()), senha)
                if status != "OK":
                    print(f"❌ Senha incorreta ou PDF inválido: {erro}")
                    return
                print("✅ Senha válida!")
            else:
                senha = None
                print("🔓 Tentando abrir PDF sem senha...")

        while True:
            # Se for TXT, processa diretamente
            if tipo == "TXT":
                print("📝 Lendo arquivo TXT...")
                with open(arquivo, 'r', encoding='utf-8') as f:
                    texto_simulado = f.read()

                # Simula processamento de PDF
                resultado = await simular_processamento_txt(extratos, texto_simulado, anexo_simulado, "teste_terminal")
                break
            else:
                # Processa PDF normalmente
                resultado = await extratos._processar_extrato_attachment(anexo_simulado, "teste_terminal", senha)

                # Se ainda precisa de senha (não deveria acontecer com o teste prévio)
                if resultado == "SENHA_NECESSARIA":
                    print("🔒 PDF protegido por senha. Digite a senha:")
                    senha = pedir_senha()
                    if senha:
                        resultado = await extratos._processar_extrato_attachment(anexo_simulado, "teste_terminal", senha)
                    else:
                        print("❌ Senha não fornecida.")
                        return
                else:
                    break

        if resultado:
            print("✅ Extrato processado com sucesso!")
            print("\n📊 RESULTADO BÁSICO:")
            print(resultado)

            # Análise detalhada - obtém o último extrato processado
            try:
                if extratos.extratos:  # Se há extratos salvos
                    extrato_obj = extratos.extratos[-1]  # Último processado
                    mostrar_analise_detalhada(type('Extrato', (), extrato_obj)())
                else:
                    print("⚠️ Não foi possível obter dados detalhados do extrato")
            except Exception as e:
                print(f"⚠️ Erro na análise detalhada: {e}")
                import traceback
                traceback.print_exc()

        else:
            print("❌ Falha no processamento!")

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()


async def processar_arquivo_selecionado():
    """Processa arquivo selecionado via diálogo do Windows"""

    print("🖱️ SELEÇÃO VIA DIÁLOGO DO WINDOWS")
    print("-" * 40)

    # Abre diálogo para selecionar arquivo
    try:
        from tkinter import Tk
        from tkinter.filedialog import askopenfilename

        # Cria janela raiz (oculta)
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)  # Mantém na frente

        # Abre diálogo
        caminho_arquivo = askopenfilename(
            title="Selecione o arquivo de extrato",
            filetypes=[
                ("Arquivos PDF", "*.pdf"),
                ("Arquivos TXT", "*.txt"),
                ("Todos os arquivos", "*.*")
            ]
        )

        root.destroy()

        if not caminho_arquivo:
            print("❌ Nenhum arquivo selecionado.")
            return

    except ImportError:
        print("❌ Tkinter não disponível. Use a opção de caminho direto.")
        return
    except Exception as e:
        print(f"❌ Erro no diálogo: {e}")
        return

    # Converte para Path
    arquivo = Path(caminho_arquivo)

    print(f"\n📄 Arquivo selecionado: {arquivo.name}")
    print(f"📂 Caminho: {arquivo.absolute()}")
    print()

    # Determina o tipo baseado na extensão
    if arquivo.suffix.lower() == '.pdf':
        tipo = 'PDF'
    elif arquivo.suffix.lower() == '.txt':
        tipo = 'TXT'
    else:
        tipo = 'DESCONHECIDO'
        print(f"❌ Tipo de arquivo não suportado: {arquivo.suffix}")
        return

    print(f"📋 Tipo: {tipo}")
    print()

    # Confirmação
    confirmar = input("Processar este arquivo? (S/N): ").strip().upper()
    if confirmar != "S":
        print("❌ Cancelado pelo usuário.")
        return

    print("\n🔄 Processando extrato...")
    print("-" * 40)

    # Inicializa módulo
    extratos = ExtratosModule()

    # Simula anexo (como seria no WhatsApp/Telegram)
    anexo_simulado = {
        'file_name': arquivo.name,
        'file_path': str(arquivo.absolute()),
        'tipo': tipo  # Adiciona tipo para processamento especial
    }

    # Processa
    try:
        senha = None

        # Para PDFs, pergunta se tem senha
        if tipo == "PDF":
            tem_senha = input("Este PDF está protegido por senha? (S/N): ").strip().upper()
            if tem_senha == "S":
                senha = pedir_senha()
                if not senha:
                    print("❌ Senha não fornecida.")
                    return

                # Testa se a senha funciona
                print("🔍 Testando senha...")
                status, erro = testar_pdf(str(arquivo.absolute()), senha)
                if status != "OK":
                    print(f"❌ Senha incorreta ou PDF inválido: {erro}")
                    return
                print("✅ Senha válida!")
            else:
                senha = None
                print("🔓 Tentando abrir PDF sem senha...")

        while True:
            # Se for TXT, processa diretamente
            if tipo == "TXT":
                print("📝 Lendo arquivo TXT...")
                with open(arquivo, 'r', encoding='utf-8') as f:
                    texto_simulado = f.read()

                # Simula processamento de PDF
                resultado = await simular_processamento_txt(extratos, texto_simulado, anexo_simulado, "teste_terminal")
                break
            else:
                # Processa PDF normalmente
                resultado = await extratos._processar_extrato_attachment(anexo_simulado, "teste_terminal", senha)

                # Se ainda precisa de senha (não deveria acontecer com o teste prévio)
                if resultado == "SENHA_NECESSARIA":
                    print("🔒 PDF protegido por senha. Digite a senha:")
                    senha = pedir_senha()
                    if senha:
                        resultado = await extratos._processar_extrato_attachment(anexo_simulado, "teste_terminal", senha)
                    else:
                        print("❌ Senha não fornecida.")
                        return
                else:
                    break

        if resultado:
            print("✅ Extrato processado com sucesso!")
            print("\n📊 RESULTADO BÁSICO:")
            print(resultado)

            # Mensagem de integração
            print("\n✅ Transações importadas para controle financeiro")

            # Análise detalhada - obtém o último extrato processado
            try:
                if extratos.extratos:  # Se há extratos salvos
                    extrato_obj = extratos.extratos[-1]  # Último processado
                    mostrar_analise_detalhada(type('Extrato', (), extrato_obj)())
                else:
                    print("⚠️ Não foi possível obter dados detalhados do extrato")
            except Exception as e:
                print(f"⚠️ Erro na análise detalhada: {e}")
                import traceback
                traceback.print_exc()

        else:
            print("❌ Falha no processamento!")

    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()


def menu_principal():
    """Menu principal do seletor"""
    while True:
        print("\n" + "=" * 50)
        print("🗂️ TESTADOR DE EXTRATOS BANCÁRIOS")
        print("=" * 50)
        print("1. Selecionar e processar arquivo (diálogo Windows)")
        print("2. Informar caminho direto do arquivo")
        print("3. Executar teste automático")
        print("0. Sair")
        print()

        escolha = input("Escolha uma opção: ").strip()

        if escolha == "0":
            print("👋 Até logo!")
            break

        elif escolha == "1":
            asyncio.run(processar_arquivo_selecionado())

        elif escolha == "2":
            asyncio.run(processar_arquivo_por_caminho())

        elif escolha == "3":
            print("🔄 Executando teste automático...")
            os.system("python teste_real_extratos.py")

        else:
            print("❌ Opção inválida!")

        input("\nPressione ENTER para continuar...")


if __name__ == "__main__":
    print("🚀 Iniciando Seletor de Arquivos para Extratos Bancários")
    print("💡 Opções disponíveis:")
    print("   • Diálogo do Windows para selecionar arquivos")
    print("   • Informar caminho direto do arquivo")
    print("🔒 Para PDFs: será perguntado se está protegido por senha")
    menu_principal()
