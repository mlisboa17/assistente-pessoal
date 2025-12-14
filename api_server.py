"""
🌐 API Server para WhatsApp Bot
Conecta o bot Node.js ao Assistente Python
"""
import os
import sys
import json
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

# Adiciona path do projeto
sys.path.insert(0, os.path.dirname(__file__))

from middleware.orchestrator import Orchestrator
from modules.extratos import ExtratosModule
from modules.financas import FinancasModule

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
                             nao_categorizadas=nao_categorizadas)

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

        # TODO: Implementar inserção no banco
        return jsonify({'success': True, 'message': 'Usuário criado com sucesso'})

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

        # TODO: Implementar inserção no banco
        return jsonify({'success': True, 'message': 'Empresa criada com sucesso'})

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

        # TODO: Implementar inserção no banco
        return jsonify({'success': True, 'message': 'Conta criada com sucesso'})

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

        # TODO: Implementar inserção no banco
        return jsonify({'success': True, 'message': 'Cartão criado com sucesso'})

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

        # TODO: Implementar inserção no banco
        return jsonify({'success': True, 'message': 'Contato criado com sucesso'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════╗
║     🌐 API SERVER - ASSISTENTE PESSOAL          ║
║                                                  ║
║  Web Interface: http://localhost:5001           ║
║  API Endpoint: POST /process                    ║
║  Dashboard: http://localhost:5001/              ║
╚══════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=5001, debug=True)
