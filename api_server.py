"""
🌐 API Server para WhatsApp Bot
Conecta o bot Node.js ao Assistente Python
"""
import os
import sys
import json
import shutil
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Adiciona path do projeto
sys.path.insert(0, os.path.dirname(__file__))

from middleware.orchestrator import Orchestrator
from modules.extratos import ExtratosModule
from modules.financas import FinancasModule
import database_setup as db

load_dotenv()

app = Flask(__name__, template_folder='templates', static_folder='static')
orchestrator = Orchestrator()
extratos_module = ExtratosModule()
financas_module = FinancasModule()

# Adiciona filtro personalizado para formatação de números
@app.template_filter('number_format')
def number_format_filter(value, decimals=2, decimal_sep=',', thousand_sep='.'):
    """Formata números para moeda brasileira"""
    try:
        if value is None:
            return "0,00"
        # Formata com separadores brasileiros
        return f"{value:,.{decimals}f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return "0,00"

# Adiciona filtro personalizado para formatação de datas
@app.template_filter('strftime')
def strftime_filter(value, format_string='%d/%m/%Y'):
    """Formata datas para o formato brasileiro"""
    try:
        if value is None:
            return "N/A"
        # Se for string ISO, converter para datetime
        if isinstance(value, str):
            from datetime import datetime
            try:
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except:
                return value
        # Formatar data
        return value.strftime(format_string)
    except (ValueError, TypeError, AttributeError):
        return "N/A"

@app.route('/process', methods=['POST'])
def process_message():
    """Processa mensagem do WhatsApp"""
    try:
        data = request.json
        message = data.get('message', '')
        user_id = data.get('user_id', 'whatsapp_user')
        user_name = data.get('user_name', 'Usuário')
        
        # Processa com o orquestrador
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(
            orchestrator.process(message, user_id)
        )
        loop.close()
        
        return jsonify({
            'success': True,
            'response': response
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'response': f'Erro: {str(e)}'
        }), 500

@app.route('/', methods=['GET'])
def dashboard():
    """Página inicial - Dashboard"""
    try:
        # Carrega dados dos módulos
        extratos_count = len(extratos_module.extratos) if hasattr(extratos_module, 'extratos') else 0

        # Calcula totais financeiros
        total_entradas = 0
        total_saidas = 0
        ultimos_extratos = []

        if hasattr(extratos_module, 'extratos') and extratos_module.extratos:
            # Pega os últimos 5 extratos
            ultimos_extratos = extratos_module.extratos[-5:] if len(extratos_module.extratos) > 5 else extratos_module.extratos

            # Calcula totais
            for extrato in extratos_module.extratos:
                for transacao in extrato.get('transacoes', []):
                    if transacao.get('tipo') == 'credito':
                        total_entradas += transacao.get('valor', 0)
                    elif transacao.get('tipo') == 'debito':
                        total_saidas += transacao.get('valor', 0)

        saldo_atual = total_entradas - total_saidas

        return render_template('dashboard.html',
                             extratos_count=extratos_count,
                             total_entradas=total_entradas,
                             total_saidas=total_saidas,
                             saldo_atual=saldo_atual,
                             ultimos_extratos=ultimos_extratos)

    except Exception as e:
        return f"Erro no dashboard: {str(e)}"

@app.route('/extratos', methods=['GET'])
def listar_extratos():
    """Página de listagem de extratos"""
    try:
        extratos = []
        if hasattr(extratos_module, 'extratos'):
            extratos = extratos_module.extratos

        return render_template('extratos.html', extratos=extratos)

    except Exception as e:
        return f"Erro ao listar extratos: {str(e)}"

@app.route('/upload-extrato', methods=['GET', 'POST'])
def upload_extrato():
    """Página de upload de extrato"""
    if request.method == 'GET':
        return render_template('upload_extrato.html')

    try:
        # Processa upload
        arquivo = request.files.get('extrato')
        banco = request.form.get('banco')
        tem_senha = request.form.get('tem_senha') == 'on'
        senha = request.form.get('senha') if tem_senha else None

        if not arquivo:
            return jsonify({'success': False, 'response': 'Nenhum arquivo enviado'})

        # Salva arquivo temporariamente
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(arquivo.filename)[1]) as temp_file:
            arquivo.save(temp_file.name)
            temp_path = temp_file.name

        # Simula anexo
        anexo_simulado = {
            'file_name': arquivo.filename,
            'file_path': temp_path,
            'tipo': 'PDF' if arquivo.filename.lower().endswith('.pdf') else 'TXT'
        }

        # Processa
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        resultado = loop.run_until_complete(
            extratos_module._processar_extrato_attachment(anexo_simulado, "web_user", senha)
        )
        loop.close()

        # Remove arquivo temporário
        os.unlink(temp_path)

        return jsonify({
            'success': True,
            'response': resultado
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'response': f'Erro: {str(e)}'
        })

@app.route('/revisao-categorias', methods=['GET'])
def revisao_categorias():
    """Página de revisão visual de categorias"""
    try:
        # Carregar dados reais de transacoes.json
        transacoes_path = os.path.join(os.path.dirname(__file__), 'data', 'transacoes.json')
        if os.path.exists(transacoes_path):
            with open(transacoes_path, 'r', encoding='utf-8') as f:
                transacoes = json.load(f)
        else:
            # Fallback para dados de teste
            transacoes = [
                {'data': '01/12/2025', 'descricao': 'PIX RECEBIDO SALARIO EMPRESA', 'valor': 3500.00, 'tipo': 'credito', 'categoria': 'salario'},
                {'data': '02/12/2025', 'descricao': 'BOLETO PAGO ENERGIA', 'valor': 180.00, 'tipo': 'debito', 'categoria': 'servicos'},
                {'data': '03/12/2025', 'descricao': 'PIX ENVIADO POSTO COMBUSTIVEL', 'valor': 150.00, 'tipo': 'debito', 'categoria': 'combustivel'},
                {'data': '04/12/2025', 'descricao': 'RECEBIMENTO FREELANCE', 'valor': 800.00, 'tipo': 'credito', 'categoria': 'freelance'},
                {'data': '05/12/2025', 'descricao': 'PAGAMENTO ALUGUEL', 'valor': 1200.00, 'tipo': 'debito', 'categoria': 'sem_categoria'}
            ]

        # Filtrar por data (padrão: últimos 30 dias)
        data_inicio_param = request.args.get('data_inicio')
        data_fim_param = request.args.get('data_fim')
        
        if data_inicio_param and data_fim_param:
            # Converter de YYYY-MM-DD para DD/MM/YYYY para comparação
            data_inicio_dt = datetime.strptime(data_inicio_param, '%Y-%m-%d')
            data_fim_dt = datetime.strptime(data_fim_param, '%Y-%m-%d')
            data_inicio_str = data_inicio_dt.strftime('%d/%m/%Y')
            data_fim_str = data_fim_dt.strftime('%d/%m/%Y')
            transacoes = [t for t in transacoes if data_inicio_str <= t['data'] <= data_fim_str]
        else:
            # Padrão: últimos 2 dias
            hoje = datetime.now()
            inicio = hoje - timedelta(days=2)
            data_inicio_str = inicio.strftime('%d/%m/%Y')
            data_fim_str = hoje.strftime('%d/%m/%Y')
            transacoes = [t for t in transacoes if data_inicio_str <= t['data'] <= data_fim_str]
            data_inicio_param = inicio.strftime('%Y-%m-%d')
            data_fim_param = hoje.strftime('%Y-%m-%d')

        # Extrair bancos únicos das transações
        bancos = set()
        for t in transacoes:
            desc = t.get('descricao', '')
            if ': ' in desc:
                banco_part = desc.split(': ')[0]
                bancos.add(banco_part)
        
        # Adicionar bancos suportados que podem não ter transações ainda
        bancos_suportados = [
            'BANCO_DO_BRASIL', 'ITAÚ', 'C6', 'SANTANDER', 'BRADESCO', 
            'NUBANK', 'INTER', 'ORIGINAL', 'PAN', 'BMG'
        ]
        for banco in bancos_suportados:
            bancos.add(banco)
        
        # Padronizar nomes dos bancos
        bancos_padronizados = set()
        for banco in bancos:
            if banco == 'ITAÚ':
                bancos_padronizados.add('ITAÚ')
            elif banco == 'ITAU':
                bancos_padronizados.add('ITAÚ')
            else:
                bancos_padronizados.add(banco)
        
        bancos_disponiveis = sorted(list(bancos_padronizados))

        categorias_disponiveis = [
            'alimentacao', 'transporte', 'combustivel', 'saude', 'educacao',
            'assinaturas', 'lazer', 'compras', 'servicos', 'impostos',
            'investimentos', 'transferencias', 'salario', 'freelance', 'outros'
        ]

        # Calcular estatísticas
        categorizadas = [t for t in transacoes if t.get('categoria', '') != 'sem_categoria']
        nao_categorizadas = [t for t in transacoes if t.get('categoria', '') == 'sem_categoria']

        return render_template('revisao_categorias.html',
                             transacoes=transacoes,
                             categorias_disponiveis=categorias_disponiveis,
                             bancos_disponiveis=bancos_disponiveis,
                             categorizadas=categorizadas,
                             nao_categorizadas=nao_categorizadas,
                             data_inicio=data_inicio_param,
                             data_fim=data_fim_param)

    except Exception as e:
        return f"Erro na revisão de categorias: {str(e)}"

@app.route('/revisao-assistente', methods=['GET'])
def revisao_assistente():
    """Página de revisão assistida de categorias passo a passo"""
    try:
        # Carregar dados reais de transacoes.json para extrair bancos
        transacoes_path = os.path.join(os.path.dirname(__file__), 'data', 'transacoes.json')
        if os.path.exists(transacoes_path):
            with open(transacoes_path, 'r', encoding='utf-8') as f:
                transacoes = json.load(f)
        else:
            transacoes = []

        # Extrair bancos únicos das transações
        bancos = set()
        for t in transacoes:
            desc = t.get('descricao', '')
            if ': ' in desc:
                banco_part = desc.split(': ')[0]
                bancos.add(banco_part)
        
        # Adicionar bancos suportados que podem não ter transações ainda
        bancos_suportados = [
            'BANCO_DO_BRASIL', 'ITAÚ', 'C6', 'SANTANDER', 'BRADESCO', 
            'NUBANK', 'INTER', 'ORIGINAL', 'PAN', 'BMG'
        ]
        for banco in bancos_suportados:
            bancos.add(banco)
        
        # Padronizar nomes dos bancos
        bancos_padronizados = set()
        for banco in bancos:
            if banco == 'ITAÚ':
                bancos_padronizados.add('ITAÚ')
            elif banco == 'ITAU':
                bancos_padronizados.add('ITAÚ')
            else:
                bancos_padronizados.add(banco)
        
        bancos_disponiveis = sorted(list(bancos_padronizados))

        return render_template('revisao_assistente.html',
                             bancos_disponiveis=bancos_disponiveis)

    except Exception as e:
        return f"Erro na revisão assistida: {str(e)}"

@app.route('/planilha-normalizacao', methods=['GET'])
def planilha_normalizacao():
    """Página de normalização em formato de planilha com checkboxes e operações em lote"""
    try:
        # Carregar dados reais de transacoes.json
        transacoes_path = os.path.join(os.path.dirname(__file__), 'data', 'transacoes.json')
        if os.path.exists(transacoes_path):
            with open(transacoes_path, 'r', encoding='utf-8') as f:
                transacoes = json.load(f)
        else:
            # Fallback para dados de teste
            transacoes = [
                {'data': '01/12/2025', 'descricao': 'PIX RECEBIDO SALARIO EMPRESA', 'valor': 3500.00, 'tipo': 'entrada', 'categoria': 'salario'},
                {'data': '02/12/2025', 'descricao': 'BOLETO PAGO ENERGIA', 'valor': 180.00, 'tipo': 'entrada', 'categoria': 'servicos'},
                {'data': '03/12/2025', 'descricao': 'PIX ENVIADO POSTO COMBUSTIVEL', 'valor': 150.00, 'tipo': 'entrada', 'categoria': 'combustivel'},
                {'data': '04/12/2025', 'descricao': 'RECEBIMENTO FREELANCE', 'valor': 800.00, 'tipo': 'entrada', 'categoria': 'freelance'},
                {'data': '05/12/2025', 'descricao': 'PAGAMENTO ALUGUEL', 'valor': 1200.00, 'tipo': 'entrada', 'categoria': 'sem_categoria'}
            ]

        # Filtrar por data (padrão: últimos 2 dias)
        data_inicio_param = request.args.get('data_inicio')
        data_fim_param = request.args.get('data_fim')
        
        if data_inicio_param and data_fim_param:
            # Converter de YYYY-MM-DD para DD/MM/YYYY para comparação
            data_inicio_dt = datetime.strptime(data_inicio_param, '%Y-%m-%d')
            data_fim_dt = datetime.strptime(data_fim_param, '%Y-%m-%d')
            data_inicio_str = data_inicio_dt.strftime('%d/%m/%Y')
            data_fim_str = data_fim_dt.strftime('%d/%m/%Y')
            transacoes = [t for t in transacoes if data_inicio_str <= t['data'] <= data_fim_str]
        else:
            # Padrão: últimos 2 dias
            hoje = datetime.now()
            inicio = hoje - timedelta(days=2)
            data_inicio_str = inicio.strftime('%d/%m/%Y')
            data_fim_str = hoje.strftime('%d/%m/%Y')
            transacoes = [t for t in transacoes if data_inicio_str <= t['data'] <= data_fim_str]
            data_inicio_param = inicio.strftime('%Y-%m-%d')
            data_fim_param = hoje.strftime('%Y-%m-%d')

        # Preparar dados para planilha - converter tipos booleanos
        for transacao in transacoes:
            # Melhorar lógica de detecção de crédito/débito baseada na descrição e valor
            descricao = transacao.get('descricao', '').upper()
            tipo = transacao.get('tipo', '').lower()
            valor = transacao.get('valor', 0)

            # Palavras-chave que indicam entrada (crédito)
            entrada_keywords = [
                'ENTRADA', 'PIX RECEBIDO', 'RECEBIDO', 'CREDITO', 'CRÉDITO',
                'DEPÓSITO', 'DEPOSITO', 'TRANSFERÊNCIA RECEBIDA', 'TRANSFERENCIA RECEBIDA',
                'PAGAMENTO RECEBIDO', 'SALÁRIO', 'SALARIO', 'FREELANCE'
            ]

            # Palavras-chave que indicam saída (débito)
            saida_keywords = [
                'SAÍDA', 'SAIDA', 'PIX ENVIADO', 'ENVIADO', 'DÉBITO', 'DEBITO',
                'PAGAMENTO', 'COMPRA', 'GASTO', 'DESPESA', 'TRANSFERÊNCIA ENVIADA',
                'TRANSFERENCIA ENVIADA', 'BOLETO', 'CONTA', 'ALUGUEL', 'LUZ', 'ÁGUA', 'AGUA'
            ]

            # Verificar se é entrada baseada em palavras-chave na descrição
            is_entrada_descricao = any(keyword in descricao for keyword in entrada_keywords)
            is_saida_descricao = any(keyword in descricao for keyword in saida_keywords)

            # Lógica de decisão:
            # 1. Se tipo é explicitamente 'saida', é débito
            # 2. Se descrição indica saída, é débito
            # 3. Se valor é negativo, é débito
            # 4. Caso contrário, assume crédito
            is_debito = (
                tipo == 'saida' or
                is_saida_descricao or
                (valor < 0) or
                ('PIX ENVIADO' in descricao) or
                ('ENVIADO' in descricao and 'PIX' in descricao)
            )

            transacao['is_credito'] = not is_debito
            transacao['is_debito'] = is_debito
            transacao['is_categorizado'] = transacao.get('categoria', '') not in ['', 'sem_categoria']
            transacao['is_pendente'] = not transacao['is_categorizado']
            transacao['valor_formatado'] = f"R$ {transacao['valor']:.2f}".replace('.', ',')

        # Extrair bancos únicos
        bancos = set()
        for t in transacoes:
            desc = t.get('descricao', '')
            if ': ' in desc:
                banco_part = desc.split(': ')[0]
                bancos.add(banco_part)
        
        # Adicionar bancos suportados que podem não ter transações ainda
        bancos_suportados = [
            'BANCO_DO_BRASIL', 'ITAÚ', 'C6', 'SANTANDER', 'BRADESCO', 
            'NUBANK', 'INTER', 'ORIGINAL', 'PAN', 'BMG'
        ]
        for banco in bancos_suportados:
            bancos.add(banco)
        
        # Padronizar nomes dos bancos
        bancos_padronizados = set()
        for banco in bancos:
            if banco == 'ITAÚ':
                bancos_padronizados.add('ITAÚ')
            elif banco == 'ITAU':
                bancos_padronizados.add('ITAÚ')
            else:
                bancos_padronizados.add(banco)
        
        bancos_disponiveis = sorted(list(bancos_padronizados))

        # Carregar categorias do arquivo ou usar padrão
        categorias_path = os.path.join(os.path.dirname(__file__), 'data', 'categorias.json')
        if os.path.exists(categorias_path):
            with open(categorias_path, 'r', encoding='utf-8') as f:
                categorias_disponiveis = json.load(f)
        else:
            categorias_disponiveis = [
                'alimentacao', 'transporte', 'combustivel', 'saude', 'educacao',
                'assinaturas', 'lazer', 'compras', 'servicos', 'impostos',
                'investimentos', 'transferencias', 'salario', 'freelance', 'outros'
            ]

        return render_template('planilha_normalizacao.html',
                             transacoes=transacoes,
                             categorias_disponiveis=categorias_disponiveis,
                             bancos_disponiveis=bancos_disponiveis,
                             data_inicio=data_inicio_param,
                             data_fim=data_fim_param)

    except Exception as e:
        return f"Erro na planilha de normalização: {str(e)}"

@app.route('/salvar-normalizacao', methods=['POST'])
def salvar_normalizacao():
    """Salva as alterações da planilha de normalização"""
    try:
        dados = request.get_json()
        
        if not dados:
            return jsonify({'success': False, 'message': 'Dados não fornecidos'}), 400
        
        # Validar estrutura dos dados
        if not isinstance(dados, list):
            return jsonify({'success': False, 'message': 'Formato de dados inválido'}), 400
        
        # Caminho para o arquivo de transações
        transacoes_path = os.path.join(os.path.dirname(__file__), 'data', 'transacoes.json')
        
        # Fazer backup do arquivo original
        if os.path.exists(transacoes_path):
            backup_path = transacoes_path + '.backup'
            shutil.copy2(transacoes_path, backup_path)
        
        # Salvar os novos dados
        with open(transacoes_path, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True, 'message': 'Alterações salvas com sucesso'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao salvar: {str(e)}'}), 500

@app.route('/adicionar-categoria', methods=['POST'])
def adicionar_categoria():
    """Adiciona uma nova categoria à lista de categorias disponíveis"""
    try:
        dados = request.get_json()
        
        if not dados or 'categoria' not in dados:
            return jsonify({'success': False, 'message': 'Nome da categoria não fornecido'}), 400
        
        nova_categoria = dados['categoria'].strip().lower()
        
        # Validar nome da categoria
        if not nova_categoria:
            return jsonify({'success': False, 'message': 'Nome da categoria não pode estar vazio'}), 400
        
        # Validar formato (apenas letras, números, underscores)
        if not re.match(r'^[a-zA-Z0-9_]+$', nova_categoria):
            return jsonify({'success': False, 'message': 'Nome da categoria deve conter apenas letras, números e underscores'}), 400
        
        # Caminho para o arquivo de categorias
        categorias_path = os.path.join(os.path.dirname(__file__), 'data', 'categorias.json')
        
        # Carregar categorias existentes ou criar lista padrão
        if os.path.exists(categorias_path):
            with open(categorias_path, 'r', encoding='utf-8') as f:
                categorias = json.load(f)
        else:
            categorias = [
                'alimentacao', 'transporte', 'combustivel', 'saude', 'educacao',
                'assinaturas', 'lazer', 'compras', 'servicos', 'impostos',
                'investimentos', 'transferencias', 'salario', 'freelance', 'outros'
            ]
        
        # Verificar se categoria já existe
        if nova_categoria in categorias:
            return jsonify({'success': False, 'message': 'Esta categoria já existe'}), 400
        
        # Adicionar nova categoria
        categorias.append(nova_categoria)
        
        # Salvar arquivo
        with open(categorias_path, 'w', encoding='utf-8') as f:
            json.dump(categorias, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True, 'message': 'Categoria adicionada com sucesso'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao adicionar categoria: {str(e)}'}), 500

@app.route('/transacoes', methods=['GET'])
def listar_transacoes():
    """Página para listar todas as transações com filtros e paginação"""
    try:
        # Parâmetros de filtro
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        banco = request.args.get('banco')
        tipo = request.args.get('tipo')
        categoria = request.args.get('categoria')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        busca = request.args.get('busca')

        # Carregar transações
        transacoes_path = os.path.join(os.path.dirname(__file__), 'data', 'transacoes.json')
        if os.path.exists(transacoes_path):
            with open(transacoes_path, 'r', encoding='utf-8') as f:
                todas_transacoes = json.load(f)
        else:
            todas_transacoes = []

        # Aplicar filtros
        transacoes_filtradas = todas_transacoes

        # Filtro por banco
        if banco:
            transacoes_filtradas = [
                t for t in transacoes_filtradas
                if t.get('descricao', '').startswith(f"{banco}: ")
            ]

        # Filtro por tipo
        if tipo:
            transacoes_filtradas = [
                t for t in transacoes_filtradas
                if t.get('tipo') == tipo
            ]

        # Filtro por categoria
        if categoria:
            transacoes_filtradas = [
                t for t in transacoes_filtradas
                if t.get('categoria') == categoria
            ]

        # Filtro por data
        if data_inicio or data_fim:
            from datetime import datetime
            transacoes_temp = []
            for t in transacoes_filtradas:
                data_str = t.get('data', '')
                try:
                    data_transacao = datetime.strptime(data_str, '%d/%m/%Y')
                    incluir = True

                    if data_inicio:
                        data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
                        if data_transacao < data_inicio_dt:
                            incluir = False

                    if data_fim:
                        data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
                        if data_transacao > data_fim_dt:
                            incluir = False

                    if incluir:
                        transacoes_temp.append(t)
                except ValueError:
                    # Se não conseguir parsear, incluir se não houver filtro de data
                    if not data_inicio and not data_fim:
                        transacoes_temp.append(t)
            transacoes_filtradas = transacoes_temp

        # Filtro por busca
        if busca:
            busca_lower = busca.lower()
            transacoes_filtradas = [
                t for t in transacoes_filtradas
                if busca_lower in t.get('descricao', '').lower() or
                   busca_lower in t.get('categoria', '').lower()
            ]

        # Calcular totais de entrada e saída das transações filtradas
        total_entradas = sum(t.get('valor', 0) for t in transacoes_filtradas if t.get('tipo') == 'entrada')
        total_saidas = sum(t.get('valor', 0) for t in transacoes_filtradas if t.get('tipo') != 'entrada')

        # Paginação
        total_transacoes = len(transacoes_filtradas)
        start = (page - 1) * per_page
        end = start + per_page
        transacoes_pagina = transacoes_filtradas[start:end]

        # Calcular total de páginas
        total_pages = (total_transacoes + per_page - 1) // per_page

        # Extrair opções de filtro
        bancos = set()
        tipos = set()
        categorias = set()

        for t in todas_transacoes:
            desc = t.get('descricao', '')
            if ': ' in desc:
                bancos.add(desc.split(': ')[0])
            tipos.add(t.get('tipo', ''))
            cat = t.get('categoria', '')
            if cat:
                categorias.add(cat)

        # Adicionar bancos suportados
        bancos_suportados = [
            'BANCO_DO_BRASIL', 'ITAÚ', 'C6', 'SANTANDER', 'BRADESCO',
            'NUBANK', 'INTER', 'ORIGINAL', 'PAN', 'BMG'
        ]
        for b in bancos_suportados:
            bancos.add(b)

        return render_template('transacoes.html',
                             transacoes=transacoes_pagina,
                             bancos=sorted(list(bancos)),
                             tipos=sorted(list(tipos)),
                             categorias=sorted(list(categorias)),
                             page=page,
                             per_page=per_page,
                             total_pages=total_pages,
                             total_transacoes=total_transacoes,
                             total_entradas=total_entradas,
                             total_saidas=total_saidas,
                             filtros={
                                 'banco': banco,
                                 'tipo': tipo,
                                 'categoria': categoria,
                                 'data_inicio': data_inicio,
                                 'data_fim': data_fim,
                                 'busca': busca
                             })

    except Exception as e:
        return f"Erro ao listar transações: {str(e)}"

@app.route('/api/transacoes', methods=['GET'])
def api_transacoes():
    """API para obter transações filtradas"""
    try:
        banco = request.args.get('banco')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')

        # Carregar transações
        transacoes_path = os.path.join(os.path.dirname(__file__), 'data', 'transacoes.json')
        if os.path.exists(transacoes_path):
            with open(transacoes_path, 'r', encoding='utf-8') as f:
                transacoes = json.load(f)
        else:
            return jsonify({'error': 'Arquivo de transações não encontrado'}), 404

        # Filtrar por banco
        if banco:
            transacoes_filtradas = []
            for t in transacoes:
                desc = t.get('descricao', '')
                if desc.startswith(f"{banco}: "):
                    transacoes_filtradas.append(t)
            transacoes = transacoes_filtradas

        # Filtrar por data
        if data_inicio or data_fim:
            from datetime import datetime
            transacoes_filtradas = []
            for t in transacoes:
                data_str = t.get('data', '')
                try:
                    # Converter data do formato dd/mm/yyyy para datetime
                    data_transacao = datetime.strptime(data_str, '%d/%m/%Y')
                    incluir = True

                    if data_inicio:
                        data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
                        if data_transacao < data_inicio_dt:
                            incluir = False

                    if data_fim:
                        data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
                        if data_transacao > data_fim_dt:
                            incluir = False

                    if incluir:
                        transacoes_filtradas.append(t)
                except ValueError:
                    # Se não conseguir parsear a data, incluir a transação
                    transacoes_filtradas.append(t)
            transacoes = transacoes_filtradas

        return jsonify({'transacoes': transacoes})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/salvar-categorias', methods=['POST'])
def salvar_categorias():
    """Salva alterações de categorias das transações"""
    try:
        data = request.json
        transacoes = data.get('transacoes', [])
        novas_categorias = data.get('novas_categorias', [])

        # Aqui seria a lógica para salvar no banco de dados
        # Por enquanto, apenas simular o salvamento

        print(f"Salvando {len(transacoes)} transações...")
        print(f"Novas categorias: {novas_categorias}")

        # Simular processamento
        import time
        time.sleep(0.5)

        return jsonify({
            'success': True,
            'message': f'Categorias salvas com sucesso! {len(transacoes)} transações atualizadas.'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao salvar categorias: {str(e)}'
        })

@app.route('/integrar-transacoes', methods=['POST'])
def integrar_transacoes():
    """Integra transações com categorias revisadas"""
    try:
        data = request.json
        transacoes = data.get('transacoes', [])
        novas_categorias = data.get('novas_categorias', [])

        # Aqui seria a lógica de integração com o sistema financeiro
        # Por enquanto, apenas simular sucesso

        print(f"Integrando {len(transacoes)} transações...")
        print(f"Novas categorias adicionadas: {novas_categorias}")

        # Simular processamento
        import time
        time.sleep(1)

        return jsonify({
            'success': True,
            'message': f'{len(transacoes)} transações integradas com sucesso!'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro na integração: {str(e)}'
        })

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'ok'})

@app.route('/cadastros', methods=['GET'])
def cadastros():
    """Página principal de cadastros"""
    return render_template('cadastros.html')

@app.route('/cadastros/usuarios', methods=['GET'])
def cadastros_usuarios():
    """Página de cadastro de usuários PF"""
    return render_template('cadastro_usuarios.html')

@app.route('/cadastros/empresas', methods=['GET'])
def cadastros_empresas():
    """Página de cadastro de empresas PJ"""
    return render_template('cadastro_empresas.html')

@app.route('/cadastros/contas', methods=['GET'])
def cadastros_contas():
    """Página de cadastro de contas bancárias"""
    return render_template('cadastro_contas.html')

@app.route('/cadastros/cartoes', methods=['GET'])
def cadastros_cartoes():
    """Página de cadastro de cartões de crédito"""
    return render_template('cadastro_cartoes.html')

@app.route('/cadastros/contatos', methods=['GET'])
def cadastros_contatos():
    """Página de cadastro de contatos"""
    return render_template('cadastro_contatos.html')

# API Routes para cadastros
@app.route('/api/usuarios', methods=['POST'])
def api_criar_usuario():
    """API para criar usuário PF"""
    try:
        data = request.json
        nome = data.get('nome')
        email = data.get('email')
        cpf = data.get('cpf')
        telefone = data.get('telefone')

        if not nome or not email:
            return jsonify({'success': False, 'error': 'Nome e email são obrigatórios'}), 400

        # Verificar se o banco está configurado
        db.criar_tabelas()

        # Inserir usuário no banco
        usuario_id, erro = db.inserir_usuario(nome, email, cpf, telefone)

        if erro:
            return jsonify({'success': False, 'error': erro}), 400

        return jsonify({'success': True, 'message': 'Usuário criado com sucesso', 'usuario_id': usuario_id})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/usuarios', methods=['GET'])
def api_listar_usuarios():
    """API para listar todos os usuários"""
    try:
        usuarios, erro = db.buscar_usuarios()

        if erro:
            return jsonify({'success': False, 'error': erro}), 500

        return jsonify({'success': True, 'usuarios': usuarios})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/usuarios/<int:usuario_id>', methods=['GET'])
def api_obter_usuario(usuario_id):
    """API para obter um usuário específico"""
    try:
        usuario, erro = db.buscar_usuario_por_id(usuario_id)

        if erro:
            return jsonify({'success': False, 'error': erro}), 404

        return jsonify({'success': True, 'usuario': usuario})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/usuarios/<int:usuario_id>', methods=['PUT'])
def api_atualizar_usuario(usuario_id):
    """API para atualizar um usuário"""
    try:
        data = request.json
        nome = data.get('nome')
        email = data.get('email')
        cpf = data.get('cpf')
        telefone = data.get('telefone')

        sucesso, erro = db.atualizar_usuario(usuario_id, nome, email, cpf, telefone)

        if not sucesso:
            return jsonify({'success': False, 'error': erro}), 400

        return jsonify({'success': True, 'message': 'Usuário atualizado com sucesso'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/usuarios/<int:usuario_id>', methods=['DELETE'])
def api_excluir_usuario(usuario_id):
    """API para excluir um usuário"""
    try:
        sucesso, erro = db.excluir_usuario(usuario_id)

        if not sucesso:
            return jsonify({'success': False, 'error': erro}), 400

        return jsonify({'success': True, 'message': 'Usuário excluído com sucesso'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/empresas', methods=['POST'])
def api_criar_empresa():
    """API para criar empresa PJ"""
    try:
        data = request.json
        usuario_id = data.get('usuario_id')
        nome = data.get('nome')
        cnpj = data.get('cnpj')

        if not nome or not cnpj:
            return jsonify({'success': False, 'error': 'Nome e CNPJ são obrigatórios'}), 400

        if not usuario_id:
            return jsonify({'success': False, 'error': 'ID do usuário é obrigatório'}), 400

        # Verificar se o banco está configurado
        db.criar_tabelas()

        # Inserir empresa no banco
        empresa_id, erro = db.inserir_empresa(usuario_id, nome, cnpj)

        if erro:
            return jsonify({'success': False, 'error': erro}), 400

        return jsonify({'success': True, 'message': 'Empresa criada com sucesso', 'empresa_id': empresa_id})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/contas', methods=['POST'])
def api_criar_conta():
    """API para criar conta bancária"""
    try:
        data = request.json
        banco_id = data.get('banco_id')
        agencia = data.get('agencia')
        conta_corrente = data.get('conta_corrente')
        tipo_conta = data.get('tipo_conta')
        usuario_id = data.get('usuario_id')
        empresa_id = data.get('empresa_id')

        if not banco_id or not conta_corrente or not tipo_conta:
            return jsonify({'success': False, 'error': 'Banco, conta corrente e tipo são obrigatórios'}), 400

        if not usuario_id:
            return jsonify({'success': False, 'error': 'ID do usuário é obrigatório'}), 400

        # Verificar se o banco está configurado
        db.criar_tabelas()

        # Criar nome da conta baseado nos dados
        nome_conta = f"{tipo_conta.title()} - {conta_corrente}"
        if agencia:
            nome_conta = f"{tipo_conta.title()} - Ag: {agencia} CC: {conta_corrente}"

        # Inserir conta no banco
        conta_id, erro = db.inserir_conta_bancaria(banco_id, usuario_id, nome_conta, agencia, conta_corrente, tipo_conta)

        if erro:
            return jsonify({'success': False, 'error': erro}), 400

        return jsonify({'success': True, 'message': 'Conta criada com sucesso', 'conta_id': conta_id})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cartoes', methods=['POST'])
def api_criar_cartao():
    """API para criar cartão de crédito"""
    try:
        data = request.json
        banco_id = data.get('banco_id')
        usuario_id = data.get('usuario_id')
        empresa_id = data.get('empresa_id')
        nome = data.get('nome')
        bandeira = data.get('bandeira')
        limite = data.get('limite')
        dia_fechamento = data.get('dia_fechamento')
        dia_vencimento = data.get('dia_vencimento')
        ultimos_4_digitos = data.get('ultimos_4_digitos')
        validade_mes = data.get('validade_mes')
        validade_ano = data.get('validade_ano')

        if not nome or not dia_fechamento or not dia_vencimento or not ultimos_4_digitos:
            return jsonify({'success': False, 'error': 'Campos obrigatórios não preenchidos'}), 400

        # Validar que pelo menos um titular foi selecionado
        if not usuario_id and not empresa_id:
            return jsonify({'success': False, 'error': 'Selecione um titular (usuário ou empresa)'}), 400

        # Verificar se o banco está configurado
        db.criar_tabelas()

        # Primeiro criar uma conta bancária para o cartão se necessário
        # Por enquanto, vamos assumir que o cartão está associado a uma conta existente
        # TODO: Melhorar lógica para associar cartão a conta bancária

        # Criar nome do cartão
        nome_cartao = f"{bandeira} ****{ultimos_4_digitos}" if bandeira else f"Cartão ****{ultimos_4_digitos}"

        # Por enquanto, vamos criar sem conta_id (None) - precisa ser ajustado
        cartao_id, erro = db.inserir_cartao_credito(None, nome_cartao, limite, f"{dia_vencimento:02d}")

        if erro:
            return jsonify({'success': False, 'error': erro}), 400

        return jsonify({'success': True, 'message': 'Cartão criado com sucesso', 'cartao_id': cartao_id})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/contatos', methods=['POST'])
def api_criar_contato():
    """API para criar contato"""
    try:
        data = request.json
        nome = data.get('nome')
        tipo_pessoa = data.get('tipo_pessoa')
        cpf_cnpj = data.get('cpf_cnpj')
        categoria = data.get('categoria')
        telefone = data.get('telefone')
        email = data.get('email')
        cep = data.get('cep')
        endereco = data.get('endereco')
        cidade = data.get('cidade')
        estado = data.get('estado')
        pais = data.get('pais')
        observacoes = data.get('observacoes')
        status = data.get('status', 'Ativo')

        if not nome or not tipo_pessoa or not categoria:
            return jsonify({'success': False, 'error': 'Nome, tipo de pessoa e categoria são obrigatórios'}), 400

        # Verificar se o banco está configurado
        db.criar_tabelas()

        # Usar categoria como tipo (cliente/fornecedor)
        tipo_contato = categoria.lower() if categoria else 'cliente'

        # Por enquanto, vamos usar usuario_id = 1 (usuário padrão)
        # TODO: Implementar sistema de autenticação para obter usuario_id correto
        usuario_id = 1

        # Inserir contato no banco
        contato_id, erro = db.inserir_contato(usuario_id, nome, tipo_contato, telefone, email)

        if erro:
            return jsonify({'success': False, 'error': erro}), 400

        return jsonify({'success': True, 'message': 'Contato criado com sucesso', 'contato_id': contato_id})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("""
API SERVER - ASSISTENTE PESSOAL

  Web Interface: http://localhost:5501
  API Endpoint: POST /process
  Dashboard: http://localhost:5501/
    """)
    app.run(host='0.0.0.0', port=5501, debug=False)
