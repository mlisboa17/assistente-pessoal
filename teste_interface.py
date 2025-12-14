#!/usr/bin/env python3
"""
Interface Web para Teste de Processamento de Extratos Bancários
Interface agradável para testar arquivos de extrato
"""

import os
import sys
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import asyncio
import json
from pathlib import Path

# Adiciona o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.extratos import ExtratosModule

app = Flask(__name__)

# Configurações
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'csv', 'ofx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Cria pasta de uploads se não existir
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Inicializa o módulo de extratos
extratos = ExtratosModule()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Página principal da interface de teste"""
    return render_template('teste_extratos.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Processa upload de arquivo de extrato"""
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Processa o arquivo
        result = asyncio.run(processar_arquivo(filepath, filename))

        # Remove o arquivo após processamento
        os.remove(filepath)

        return jsonify(result)

    return jsonify({'error': 'Tipo de arquivo não permitido'}), 400

@app.route('/upload_with_password', methods=['POST'])
def upload_with_password():
    """Processa upload de arquivo de extrato com senha"""
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400

    password = request.form.get('password', '')

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Processa o arquivo com senha
        result = asyncio.run(processar_arquivo_com_senha(filepath, filename, password))

        # Remove o arquivo após processamento
        os.remove(filepath)

        return jsonify(result)

    return jsonify({'error': 'Tipo de arquivo não permitido'}), 400

async def processar_arquivo(filepath, filename):
    """Processa um arquivo de extrato"""
    try:
        # Simula anexo como o WhatsApp faria
        anexo_simulado = {
            'file_name': filename,
            'file_path': filepath,
            'mime_type': 'application/pdf' if filename.endswith('.pdf') else 'text/csv'
        }

        # Processa o extrato
        resultado = await extratos._processar_extrato_attachment(anexo_simulado, "teste_web")

        if "Erro ao processar extrato" in resultado:
            # Verificar se é erro de senha
            if "PDF_PROTEGIDO_POR_SENHA" in resultado or "SENHA_NECESSARIA" in resultado:
                return {
                    'success': False,
                    'password_required': True,
                    'error': 'Este PDF está protegido por senha. Digite a senha para continuar.',
                    'filename': filename
                }
            else:
                return {
                    'success': False,
                    'error': resultado,
                    'filename': filename
                }
        elif resultado.get('preview', False):
            # É uma resposta de preview bem-sucedida com dados normalizados
            dados = resultado.get('dados', {})

            # Formatar preview com dados normalizados
            preview = "📄 *EXTRATO PROCESSADO E NORMALIZADO*\n\n"
            preview += f"🏦 *Banco:* {dados.get('banco', 'N/A')}\n"
            preview += f"👤 *Titular:* {dados.get('titular', 'N/A')}\n"
            preview += f"📅 *Período:* {dados.get('periodo', 'N/A')}\n\n"

            # Estatísticas normalizadas
            stats = dados.get('estatisticas', {})
            preview += "💰 *RESUMO FINANCEIRO:*\n"
            preview += f"• Entradas: R$ {stats.get('valor_total_creditos', 0):.2f}\n"
            preview += f"• Saídas: R$ {stats.get('valor_total_debitos', 0):.2f}\n"
            preview += f"• Saldo Calculado: R$ {stats.get('saldo_calculado', 0):.2f}\n"
            preview += f"• Saldo Informado: R$ {dados.get('saldo_atual', 0):.2f}\n\n"

            preview += f"📊 *Transações:* {stats.get('total_transacoes', 0)}\n"
            preview += f"• Créditos: {stats.get('total_creditos', 0)}\n"
            preview += f"• Débitos: {stats.get('total_debitos', 0)}\n"
            preview += f"• Dias com movimento: {stats.get('dias_com_movimento', 0)}\n\n"

            # Categorias
            categorias = stats.get('categorias', {})
            if categorias:
                preview += "🏷️ *CATEGORIAS IDENTIFICADAS:*\n"
                for categoria, count in categorias.items():
                    if categoria != 'sem_categoria':
                        preview += f"• {categoria.title()}: {count}\n"

                sem_cat = categorias.get('sem_categoria', 0)
                if sem_cat > 0:
                    preview += f"• Sem Categoria: {sem_cat}\n"

            # Validação
            validacao = dados.get('validacao', {})
            if not validacao.get('valido', True):
                preview += "\n⚠️ *AVISOS DE VALIDAÇÃO:*\n"
                for erro in validacao.get('erros', []):
                    preview += f"• ❌ {erro}\n"
                for aviso in validacao.get('avisos', []):
                    preview += f"• ⚠️ {aviso}\n"

            preview += "\n✅ *Deseja confirmar e salvar este extrato?*\n"
            preview += "Responda 'SIM' para confirmar ou 'REVISAR' para ajustar as categorias."

            return {
                'success': True,
                'preview': preview,
                'dados_normalizados': dados,
                'filename': filename
            }
        else:
            return {
                'success': True,
                'message': str(resultado),
                'filename': filename
            }
    except Exception as e:
        return {
            'success': False,
            'error': f'Erro interno: {str(e)}',
            'filename': filename
        }

async def processar_arquivo_com_senha(filepath, filename, password):
    """Processa um arquivo de extrato com senha fornecida"""
    try:
        # Simula anexo como o WhatsApp faria
        anexo_simulado = {
            'file_name': filename,
            'file_path': filepath,
            'mime_type': 'application/pdf' if filename.endswith('.pdf') else 'text/csv'
        }

        # Processa o extrato com senha
        resultado = await extratos._processar_extrato_attachment(anexo_simulado, "teste_web", password)

        if "Erro ao processar extrato" in resultado:
            return {
                'success': False,
                'error': resultado,
                'filename': filename
            }
        elif resultado.get('preview', False):
            # É uma resposta de preview bem-sucedida com dados normalizados
            dados = resultado.get('dados', {})

            # Formatar preview com dados normalizados
            preview = "📄 *EXTRATO PROCESSADO E NORMALIZADO*\n\n"
            preview += f"🏦 *Banco:* {dados.get('banco', 'N/A')}\n"
            preview += f"👤 *Titular:* {dados.get('titular', 'N/A')}\n"
            preview += f"📅 *Período:* {dados.get('periodo', 'N/A')}\n\n"

            # Estatísticas normalizadas
            stats = dados.get('estatisticas', {})
            preview += "💰 *RESUMO FINANCEIRO:*\n"
            preview += f"• Entradas: R$ {stats.get('valor_total_creditos', 0):.2f}\n"
            preview += f"• Saídas: R$ {stats.get('valor_total_debitos', 0):.2f}\n"
            preview += f"• Saldo Calculado: R$ {stats.get('saldo_calculado', 0):.2f}\n"
            preview += f"• Saldo Informado: R$ {dados.get('saldo_atual', 0):.2f}\n\n"

            preview += f"📊 *Transações:* {stats.get('total_transacoes', 0)}\n"
            preview += f"• Créditos: {stats.get('total_creditos', 0)}\n"
            preview += f"• Débitos: {stats.get('total_debitos', 0)}\n"
            preview += f"• Dias com movimento: {stats.get('dias_com_movimento', 0)}\n\n"

            # Categorias
            categorias = stats.get('categorias', {})
            if categorias:
                preview += "🏷️ *CATEGORIAS IDENTIFICADAS:*\n"
                for categoria, count in categorias.items():
                    if categoria != 'sem_categoria':
                        preview += f"• {categoria.title()}: {count}\n"

                sem_cat = categorias.get('sem_categoria', 0)
                if sem_cat > 0:
                    preview += f"• Sem Categoria: {sem_cat}\n"

            # Validação
            validacao = dados.get('validacao', {})
            if not validacao.get('valido', True):
                preview += "\n⚠️ *AVISOS DE VALIDAÇÃO:*\n"
                for erro in validacao.get('erros', []):
                    preview += f"• ❌ {erro}\n"
                for aviso in validacao.get('avisos', []):
                    preview += f"• ⚠️ {aviso}\n"

            preview += "\n✅ *Deseja confirmar e salvar este extrato?*\n"
            preview += "Responda 'SIM' para confirmar ou 'REVISAR' para ajustar as categorias."

            return {
                'success': True,
                'preview': preview,
                'dados_normalizados': dados,
                'filename': filename
            }
        else:
            return {
                'success': True,
                'message': str(resultado),
                'filename': filename
            }
    except Exception as e:
        return {
            'success': False,
            'error': f'Erro interno: {str(e)}',
            'filename': filename
        }

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve arquivos estáticos"""
    return send_from_directory('static', filename)

@app.route('/templates/<path:filename>')
def template_files(filename):
    """Serve templates"""
    return send_from_directory('templates', filename)

if __name__ == '__main__':
    print("🚀 Iniciando Interface de Teste de Extratos")
    print("📱 Acesse: http://localhost:5002")
    print("📁 Faça upload de arquivos PDF, CSV ou OFX de extratos bancários")
    app.run(debug=True, host='0.0.0.0', port=5002)