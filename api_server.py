"""
🤖 Moga Bot - API Server
Conecta WhatsApp e Telegram ao Assistente Python
Suporta: Texto, Áudio, PDF e Comprovantes
"""
import os
import sys
import base64
import tempfile
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Adiciona path do projeto
sys.path.insert(0, os.path.dirname(__file__))

from middleware.orchestrator import Orchestrator

load_dotenv()

app = Flask(__name__)
orchestrator = Orchestrator()

# Módulo de voz (para transcrição)
voz_module = None
try:
    from modules.voz import VozModule
    voz_module = VozModule(data_dir="data")
    print("🎤 Módulo de Voz carregado!")
except ImportError as e:
    print(f"⚠️ Módulo de Voz não disponível: {e}")

# Módulo de faturas (para processar PDFs)
faturas_module = None
try:
    from modules.faturas import FaturasModule
    faturas_module = FaturasModule(data_dir="data")
    print("📄 Módulo de Faturas carregado!")
except ImportError as e:
    print(f"⚠️ Módulo de Faturas não disponível: {e}")

# Módulo de comprovantes (para processar imagens)
comprovantes_module = None
try:
    from modules.comprovantes import ComprovantesModule
    comprovantes_module = ComprovantesModule(data_dir="data")
    print("🧾 Módulo de Comprovantes carregado!")
except ImportError as e:
    print(f"⚠️ Módulo de Comprovantes não disponível: {e}")

# Módulo de extração de documentos (extratos, impostos, etc)
extrator_documentos = None
try:
    from modules.extrator_documentos import extrator_documentos as extrator_docs
    extrator_documentos = extrator_docs
    print("📊 Módulo Extrator de Documentos carregado!")
except ImportError as e:
    print(f"⚠️ Módulo Extrator de Documentos não disponível: {e}")


# Módulo de agenda de grupo
agenda_grupo_module = None
try:
    from modules.agenda_grupo import AgendaGrupoModule
    agenda_grupo_module = AgendaGrupoModule(data_dir="data")
    print("👥 Módulo de Agenda de Grupo carregado!")
except ImportError as e:
    print(f"⚠️ Módulo de Agenda de Grupo não disponível: {e}")

# Módulo de cadastros
cadastros_module = None
try:
    from modules.cadastros import CadastrosModule
    cadastros_module = CadastrosModule(data_dir="data")
    print("📋 Módulo de Cadastros carregado!")
except ImportError as e:
    print(f"⚠️ Módulo de Cadastros não disponível: {e}")

# Módulo de configurações
configuracoes_module = None
try:
    from modules.configuracoes import ConfiguracoesModule
    configuracoes_module = ConfiguracoesModule(data_dir="data")
    print("⚙️ Módulo de Configurações carregado!")
except ImportError as e:
    print(f"⚠️ Módulo de Configurações não disponível: {e}")

# Módulo de monitoramento de emails
email_monitor_module = None
try:
    from modules.email_monitor import EmailMonitorModule
    email_monitor_module = EmailMonitorModule(data_dir="data")
    print("📧 Módulo de Monitor de Emails carregado!")
except ImportError as e:
    print(f"⚠️ Módulo de Monitor de Emails não disponível: {e}")


@app.route('/process', methods=['POST'])
def process_message():
    """Processa mensagem de texto do WhatsApp"""
    try:
        data = request.json
        message = data.get('message', '')
        user_id = data.get('user_id', 'whatsapp_user')
        user_name = data.get('user_name', 'Usuário')
        is_group = data.get('is_group', False)
        group_name = data.get('group_name', '')
        participant_id = data.get('participant_id', user_id)  # ID de quem enviou (em grupos)
        
        # Se é grupo, user_id é o grupo_id, participant_id é quem enviou
        if is_group and agenda_grupo_module:
            grupo_id = user_id  # Em grupos, user_id é o ID do grupo
            response = process_group_command(message, participant_id, user_name, grupo_id, group_name)
            if response:
                return jsonify({
                    'success': True,
                    'response': response
                })
        
        # Processa com o orquestrador (usa participant_id em grupos)
        actual_user_id = participant_id if is_group else user_id
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(
            orchestrator.process(message, actual_user_id)
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


def process_group_command(message: str, user_id: str, user_name: str, 
                          grupo_id: str, grupo_nome: str):
    """Processa comandos específicos de grupo"""
    import asyncio
    
    text = message.lower().strip()
    first_word = text.split()[0].lstrip('/') if text else ''
    
    # BLOQUEIA comandos de email em grupos
    comandos_email_bloqueados = ['emails', 'email', 'ler', 'inbox', 'caixa', 
                                  'monitorar', 'monitor', 'alertar', 'palavras', 'keywords']
    if first_word in comandos_email_bloqueados:
        return """🔒 *Função não disponível em grupos*

Por questões de privacidade, o acesso a emails 
e monitoramento não funcionam em grupos.

_Use essa função em conversa privada comigo!_ 💬"""
    
    # Comandos de agenda de grupo
    comandos_grupo = ['agenda', 'eventos', 'evento', 'agendar', 'tarefas', 
                      'tarefa', 'concluir', 'feito', 'confirmar', 'vou', 'grupo',
                      'sim', 's', 'nao', 'não', 'n', 'eu', 'todos']  # Respostas de configuração
    
    # Verifica se é comando de grupo OU se o grupo tem pendência de configuração
    if first_word in comandos_grupo or agenda_grupo_module._pendencias_config.get(grupo_id):
        args = text.split()[1:] if len(text.split()) > 1 else []
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(
            agenda_grupo_module.handle(first_word, args, user_id, user_name, grupo_id, grupo_nome)
        )
        loop.close()
        return response
    
    return None


@app.route('/process-audio', methods=['POST'])
def process_audio():
    """Processa áudio do WhatsApp - Transcreve e executa comando"""
    try:
        data = request.json
        audio_base64 = data.get('audio', '')
        user_id = data.get('user_id', 'whatsapp_user')
        user_name = data.get('user_name', 'Usuário')
        mimetype = data.get('mimetype', 'audio/ogg')
        
        if not audio_base64:
            return jsonify({
                'success': False,
                'response': '❌ Nenhum áudio recebido.'
            }), 400
        
        if not voz_module:
            return jsonify({
                'success': False,
                'response': '❌ Módulo de voz não está disponível. Instale: pip install SpeechRecognition pydub'
            }), 500
        
        # Decodifica o áudio base64
        audio_bytes = base64.b64decode(audio_base64)
        
        # Determina extensão
        ext = 'ogg'
        if 'mp4' in mimetype or 'mp4a' in mimetype:
            ext = 'mp4'
        elif 'mpeg' in mimetype:
            ext = 'mp3'
        elif 'wav' in mimetype:
            ext = 'wav'
        
        # Salva temporariamente
        with tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False) as f:
            f.write(audio_bytes)
            audio_path = f.name
        
        try:
            # Transcreve o áudio
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                voz_module.transcrever_audio(audio_path, ext)
            )
            
            if not result['success']:
                return jsonify({
                    'success': False,
                    'response': f"🎤 {result.get('error', 'Erro ao transcrever áudio')}"
                })
            
            texto_transcrito = result['text']
            
            # Agora processa o texto transcrito como comando
            response = loop.run_until_complete(
                orchestrator.process(texto_transcrito, user_id)
            )
            loop.close()
            
            return jsonify({
                'success': True,
                'transcription': texto_transcrito,
                'response': f"🎤 *Você disse:* _{texto_transcrito}_\n\n{response}"
            })
            
        finally:
            # Remove arquivo temporário
            if os.path.exists(audio_path):
                os.remove(audio_path)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'response': f'❌ Erro ao processar áudio: {str(e)}'
        }), 500


@app.route('/process-file', methods=['POST'])
def process_file():
    """Processa arquivo do WhatsApp (PDF de boletos, etc.)"""
    try:
        data = request.json
        file_base64 = data.get('file', '')
        filename = data.get('filename', 'arquivo')
        mimetype = data.get('mimetype', '')
        user_id = data.get('user_id', 'whatsapp_user')
        user_name = data.get('user_name', 'Usuário')
        caption = data.get('caption', '')
        
        if not file_base64:
            return jsonify({
                'success': False,
                'response': '❌ Nenhum arquivo recebido.'
            }), 400
        
        # Verifica se é PDF
        is_pdf = 'pdf' in mimetype.lower() or filename.lower().endswith('.pdf')
        
        # Verifica se é arquivo OFX (extrato bancário)
        is_ofx = filename.lower().endswith('.ofx') or filename.lower().endswith('.qfx')
        
        # === EXTRATO OFX ===
        if is_ofx and extrator_documentos:
            file_bytes = base64.b64decode(file_base64)
            
            with tempfile.NamedTemporaryFile(suffix='.ofx', delete=False) as f:
                f.write(file_bytes)
                file_path = f.name
            
            try:
                resultado = extrator_documentos.extrair_extrato_ofx(file_path)
                if resultado:
                    return jsonify({
                        'success': True,
                        'response': _formatar_extrato(resultado)
                    })
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)
        
        if is_pdf:
            file_bytes = base64.b64decode(file_base64)
            
            # Salva temporariamente
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                f.write(file_bytes)
                file_path = f.name
            
            try:
                # === TENTA DETECTAR TIPO AUTOMATICAMENTE ===
                if extrator_documentos:
                    resultado = extrator_documentos.extrair_automatico(arquivo_path=file_path)
                    
                    if resultado.get('tipo') != 'desconhecido' and resultado.get('dados'):
                        # Formata resposta baseado no tipo
                        tipo = resultado['tipo']
                        dados = resultado['dados']
                        
                        if tipo == 'das':
                            return jsonify({
                                'success': True,
                                'response': _formatar_das(dados)
                            })
                        elif tipo == 'fgts':
                            return jsonify({
                                'success': True,
                                'response': _formatar_fgts(dados)
                            })
                        elif tipo == 'gps':
                            return jsonify({
                                'success': True,
                                'response': _formatar_gps(dados)
                            })
                        elif tipo == 'darf':
                            return jsonify({
                                'success': True,
                                'response': _formatar_darf(dados)
                            })
                        elif tipo == 'extrato_bancario':
                            from modules.extrator_documentos import ExtratoBancario, TransacaoExtrato
                            # Reconstrói objeto para formatação
                            transacoes = [TransacaoExtrato(**t) for t in dados.get('transacoes', [])]
                            dados['transacoes'] = transacoes
                            extrato = ExtratoBancario(**{k: v for k, v in dados.items()})
                            return jsonify({
                                'success': True,
                                'response': _formatar_extrato(extrato)
                            })
                        elif tipo == 'comprovante_boleto':
                            return jsonify({
                                'success': True,
                                'response': _formatar_comprovante_boleto(dados)
                            })
                
                # === FALLBACK: PROCESSA COMO FATURA/BOLETO ===
                if faturas_module:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    response = loop.run_until_complete(
                        faturas_module.processar_arquivo(file_path, user_id)
                    )
                    loop.close()
                    
                    return jsonify({
                        'success': True,
                        'response': response
                    })
                
            finally:
                # Remove arquivo temporário
                if os.path.exists(file_path):
                    os.remove(file_path)
        
        else:
            # Verifica se é imagem (possível comprovante)
            is_image = any(x in mimetype.lower() for x in ['image', 'jpeg', 'jpg', 'png'])
            
            if is_image:
                # === TENTA EXTRATOR DE DOCUMENTOS PRIMEIRO ===
                if extrator_documentos:
                    file_bytes = base64.b64decode(file_base64)
                    resultado = extrator_documentos.extrair_automatico(imagem_bytes=file_bytes)
                    
                    if resultado.get('tipo') != 'desconhecido' and resultado.get('dados'):
                        tipo = resultado['tipo']
                        dados = resultado['dados']
                        
                        if tipo == 'das':
                            return jsonify({
                                'success': True,
                                'response': _formatar_das(dados)
                            })
                        elif tipo == 'fgts':
                            return jsonify({
                                'success': True,
                                'response': _formatar_fgts(dados)
                            })
                        elif tipo == 'gps':
                            return jsonify({
                                'success': True,
                                'response': _formatar_gps(dados)
                            })
                        elif tipo == 'darf':
                            return jsonify({
                                'success': True,
                                'response': _formatar_darf(dados)
                            })
                        elif tipo == 'comprovante_boleto':
                            return jsonify({
                                'success': True,
                                'response': _formatar_comprovante_boleto(dados)
                            })
                
                # === FALLBACK: COMPROVANTE NORMAL ===
                if comprovantes_module:
                    return process_comprovante_image(file_base64, filename, user_id, user_name, caption)
            
            # Arquivo não suportado
            return jsonify({
                'success': True,
                'response': f"""📁 *Arquivo recebido:* {filename}

📸 *Envie comprovantes de pagamento* e eu vou:
• Identificar o valor
• Detectar o destinatário
• Sugerir a categoria
• Pedir sua confirmação antes de salvar

✅ *Tipos aceitos:*
• 📲 PIX
• 🧾 Recibos
• 💳 Comprovantes de cartão
• 📄 PDF de boletos
• 📊 Extratos bancários (PDF/OFX)
• 💼 Guias: DAS, FGTS, GPS, DARF"""
            })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'response': f'❌ Erro ao processar arquivo: {str(e)}'
        }), 500


# ========== FUNÇÕES DE FORMATAÇÃO DE DOCUMENTOS ==========

def _formatar_valor(valor: float) -> str:
    """Formata valor em Reais"""
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def _sugerir_categoria(tipo_doc: str, descricao: str = '') -> str:
    """Sugere categoria baseado no tipo de documento"""
    categorias = {
        'das': 'impostos',
        'fgts': 'folha_pagamento',
        'gps': 'folha_pagamento',
        'darf': 'impostos',
        'boleto': 'contas',
        'pix': 'outros',
        'energia': 'contas',
        'agua': 'contas',
        'internet': 'contas',
        'telefone': 'contas',
        'aluguel': 'moradia',
    }
    
    # Verifica palavras na descrição
    desc_lower = descricao.lower()
    for keyword, cat in categorias.items():
        if keyword in desc_lower:
            return cat
    
    return categorias.get(tipo_doc, 'outros')

def _formatar_extrato(extrato) -> str:
    """Formata extrato bancário para exibição"""
    msg = f"""📊 *EXTRATO BANCÁRIO*

🏦 *Banco:* {extrato.banco}
📍 *Agência:* {extrato.agencia}
💳 *Conta:* {extrato.conta}
👤 *Titular:* {extrato.titular or 'Não identificado'}

📅 *Período:* {extrato.periodo_inicio} a {extrato.periodo_fim}

💰 *Resumo:*
├ Saldo Inicial: {_formatar_valor(extrato.saldo_inicial)}
├ Total Créditos: {_formatar_valor(extrato.total_creditos)}
├ Total Débitos: {_formatar_valor(extrato.total_debitos)}
└ *Saldo Final:* {_formatar_valor(extrato.saldo_final)}

📋 *Últimas Transações:*
"""
    # Mostra até 10 transações
    for i, t in enumerate(extrato.transacoes[:10]):
        sinal = "➕" if t.tipo == 'credito' else "➖"
        msg += f"{sinal} {t.data} | {t.descricao[:25]} | {_formatar_valor(t.valor)}\n"
    
    if len(extrato.transacoes) > 10:
        msg += f"\n... e mais {len(extrato.transacoes) - 10} transações"
    
    msg += "\n━━━━━━━━━━━━━━━━━━━━"
    msg += "\n💡 Digite *extrato detalhado* para ver todas as transações"
    
    return msg

def _formatar_das(dados: dict) -> str:
    """Formata DAS para exibição"""
    valor = dados.get('valor_total', 0)
    linha = dados.get('linha_digitavel', '')
    categoria = _sugerir_categoria('das')
    
    return f"""💼 *DAS - SIMPLES NACIONAL*

📅 *Período:* {dados.get('periodo_apuracao', '-')}
🏢 *CNPJ:* {dados.get('cnpj', '-')}
📋 *Razão Social:* {dados.get('razao_social', '-')}

💰 *Valores:*
├ Principal: {_formatar_valor(dados.get('valor_principal', 0))}
└ *Total:* {_formatar_valor(valor)}

📆 *Vencimento:* {dados.get('data_vencimento', '-')}
📝 *Documento:* {dados.get('numero_documento', '-')}

📊 *Código para pagamento:*
```
{linha}
```

🏷️ *Categoria sugerida:* {categoria.upper()}

━━━━━━━━━━━━━━━━━━━━
*Escolha uma opção:*

1️⃣ *COPIAR* - Copiar código para pagar
2️⃣ *PAGO* - Marcar como pago e registrar despesa
3️⃣ *AGENDAR* - Salvar na agenda (lembrete)
4️⃣ *TUDO* - Marcar pago + Despesa + Agenda

💡 Ou digite: *pago {categoria}* para mudar categoria"""

def _formatar_fgts(dados: dict) -> str:
    """Formata guia FGTS para exibição"""
    valor = dados.get('valor_total', 0)
    linha = dados.get('linha_digitavel', '')
    categoria = _sugerir_categoria('fgts')
    
    return f"""👷 *GUIA FGTS*

📅 *Competência:* {dados.get('competencia', '-')}
🏢 *CNPJ:* {dados.get('cnpj', '-')}
📋 *Razão Social:* {dados.get('razao_social', '-')}
🔢 *Código Recolhimento:* {dados.get('codigo_recolhimento', '-')}

💰 *Valores:*
├ FGTS: {_formatar_valor(dados.get('valor_fgts', 0))}
└ *Total:* {_formatar_valor(valor)}

👥 *Funcionários:* {dados.get('numero_funcionarios', '-')}
📆 *Vencimento:* {dados.get('data_vencimento', '-')}

📊 *Código para pagamento:*
```
{linha}
```

🏷️ *Categoria sugerida:* {categoria.upper()}

━━━━━━━━━━━━━━━━━━━━
*Escolha uma opção:*

1️⃣ *COPIAR* - Copiar código para pagar
2️⃣ *PAGO* - Marcar como pago e registrar despesa
3️⃣ *AGENDAR* - Salvar na agenda (lembrete)
4️⃣ *TUDO* - Marcar pago + Despesa + Agenda

💡 Ou digite: *pago {categoria}* para mudar categoria"""

def _formatar_gps(dados: dict) -> str:
    """Formata GPS (INSS) para exibição"""
    tipo_map = {
        'empresa': '🏢 Empresa',
        'contribuinte_individual': '👤 Contribuinte Individual',
        'domestico': '🏠 Empregador Doméstico'
    }
    tipo = tipo_map.get(dados.get('tipo_identificador', ''), '📋')
    valor = dados.get('valor_total', 0)
    linha = dados.get('linha_digitavel', '')
    categoria = _sugerir_categoria('gps')
    
    return f"""🏛️ *GPS - PREVIDÊNCIA SOCIAL*

📅 *Competência:* {dados.get('competencia', '-')}
{tipo}
📋 *Identificador:* {dados.get('identificador', '-')}
🔢 *Código Pagamento:* {dados.get('codigo_pagamento', '-')}

💰 *Valores:*
├ INSS: {_formatar_valor(dados.get('valor_inss', 0))}
├ Outras Entidades: {_formatar_valor(dados.get('valor_outras_entidades', 0))}
├ Atualização: {_formatar_valor(dados.get('valor_atualizacao', 0))}
└ *Total:* {_formatar_valor(valor)}

📆 *Vencimento:* {dados.get('data_vencimento', '-')}

📊 *Código para pagamento:*
```
{linha}
```

🏷️ *Categoria sugerida:* {categoria.upper()}

━━━━━━━━━━━━━━━━━━━━
*Escolha uma opção:*

1️⃣ *COPIAR* - Copiar código para pagar
2️⃣ *PAGO* - Marcar como pago e registrar despesa
3️⃣ *AGENDAR* - Salvar na agenda (lembrete)
4️⃣ *TUDO* - Marcar pago + Despesa + Agenda

💡 Ou digite: *pago {categoria}* para mudar categoria"""

def _formatar_darf(dados: dict) -> str:
    """Formata DARF para exibição"""
    valor = dados.get('valor_total', 0)
    linha = dados.get('linha_digitavel', '')
    categoria = _sugerir_categoria('darf')
    
    return f"""🏛️ *DARF - RECEITA FEDERAL*

📅 *Período Apuração:* {dados.get('periodo_apuracao', '-')}
📋 *CNPJ/CPF:* {dados.get('cnpj_cpf', '-')}
🔢 *Código Receita:* {dados.get('codigo_receita', '-')}
📝 *Receita:* {dados.get('nome_receita', '-')}

💰 *Valores:*
├ Principal: {_formatar_valor(dados.get('valor_principal', 0))}
├ Multa: {_formatar_valor(dados.get('valor_multa', 0))}
├ Juros: {_formatar_valor(dados.get('valor_juros', 0))}
└ *Total:* {_formatar_valor(valor)}

📆 *Vencimento:* {dados.get('data_vencimento', '-')}

📊 *Código para pagamento:*
```
{linha}
```

🏷️ *Categoria sugerida:* {categoria.upper()}

━━━━━━━━━━━━━━━━━━━━
*Escolha uma opção:*

1️⃣ *COPIAR* - Copiar código para pagar
2️⃣ *PAGO* - Marcar como pago e registrar despesa
3️⃣ *AGENDAR* - Salvar na agenda (lembrete)
4️⃣ *TUDO* - Marcar pago + Despesa + Agenda

💡 Ou digite: *pago {categoria}* para mudar categoria"""

def _formatar_comprovante_boleto(dados: dict) -> str:
    """Formata comprovante de boleto pago para exibição"""
    valor = dados.get('valor_pago', 0)
    categoria = _sugerir_categoria('boleto', dados.get('beneficiario', ''))
    
    return f"""✅ *COMPROVANTE DE PAGAMENTO*

🏦 *Banco Pagador:* {dados.get('banco_pagador', '-')}
💳 *Ag/Conta:* {dados.get('agencia_conta', '-')}

📅 *Data Pagamento:* {dados.get('data_pagamento', '-')}

💰 *Valores:*
├ Documento: {_formatar_valor(dados.get('valor_documento', 0))}
├ Desconto: {_formatar_valor(dados.get('desconto', 0))}
├ Juros: {_formatar_valor(dados.get('juros', 0))}
├ Multa: {_formatar_valor(dados.get('multa', 0))}
└ *Pago:* {_formatar_valor(valor)}

🏪 *Beneficiário:* {dados.get('beneficiario', '-')}
📋 *CNPJ/CPF:* {dados.get('beneficiario_doc', '-')}

🔐 *Autenticação:* {dados.get('autenticacao', '-')}

🏷️ *Categoria sugerida:* {categoria.upper()}

━━━━━━━━━━━━━━━━━━━━
*Este é um comprovante de pagamento já realizado!*

1️⃣ *DESPESA* - Registrar como despesa
2️⃣ *AGENDA* - Salvar na agenda como evento
3️⃣ *TUDO* - Despesa + Agenda

💡 Ou digite: *despesa {categoria}* para mudar categoria"""


def _formatar_boleto(dados: dict) -> str:
    """Formata boleto para exibição"""
    valor = dados.get('valor', 0)
    linha = dados.get('linha_digitavel', '')
    categoria = _sugerir_categoria('boleto', dados.get('beneficiario', ''))
    
    return f"""🧾 *BOLETO DETECTADO*

🏪 *Beneficiário:* {dados.get('beneficiario', '-')}
📋 *CNPJ/CPF:* {dados.get('beneficiario_doc', '-')}
🏦 *Banco:* {dados.get('banco', '-')}

💰 *Valor:* {_formatar_valor(valor)}
📆 *Vencimento:* {dados.get('data_vencimento', '-')}

📊 *Código para pagamento:*
```
{linha}
```

🏷️ *Categoria sugerida:* {categoria.upper()}

━━━━━━━━━━━━━━━━━━━━
*Escolha uma opção:*

1️⃣ *COPIAR* - Copiar código para pagar
2️⃣ *PAGO* - Marcar como pago e registrar despesa
3️⃣ *AGENDAR* - Salvar lembrete do vencimento
4️⃣ *TUDO* - Marcar pago + Despesa + Agenda

💡 Ou digite: *pago {categoria}* para mudar categoria"""


def _formatar_pix(dados: dict) -> str:
    """Formata comprovante PIX para exibição"""
    valor = dados.get('valor', 0)
    chave = dados.get('chave_pix', dados.get('id_transacao', ''))
    categoria = _sugerir_categoria('pix', dados.get('destinatario', ''))
    
    # Detecta tipo de chave
    tipo_chave = dados.get('tipo_chave', 'chave')
    
    return f"""📲 *PIX DETECTADO*

👤 *Pagador:* {dados.get('pagador', '-')}
📋 *Doc:* {dados.get('pagador_doc', '-')}

🏪 *Destinatário:* {dados.get('destinatario', '-')}
📋 *Doc:* {dados.get('destinatario_doc', '-')}
🏦 *Banco:* {dados.get('banco', '-')}

💰 *Valor:* {_formatar_valor(valor)}
📅 *Data:* {dados.get('data', '-')}
⏰ *Hora:* {dados.get('hora', '-')}

🔑 *{tipo_chave.upper()}:*
```
{chave}
```

🏷️ *Categoria sugerida:* {categoria.upper()}

━━━━━━━━━━━━━━━━━━━━
*Escolha uma opção:*

1️⃣ *COPIAR* - Copiar chave PIX
2️⃣ *PAGO* - Marcar como pago e registrar despesa
3️⃣ *DESPESA* - Registrar como despesa
4️⃣ *TUDO* - Despesa + Agenda

💡 Ou digite: *despesa {categoria}* para mudar categoria"""


def _formatar_transferencia(dados: dict) -> str:
    """Formata comprovante de transferência TED/DOC"""
    valor = dados.get('valor', 0)
    categoria = _sugerir_categoria('transferencia', dados.get('destinatario', ''))
    
    return f"""💸 *TRANSFERÊNCIA {dados.get('tipo', 'TED/DOC').upper()}*

👤 *Pagador:* {dados.get('pagador', '-')}
📋 *Doc:* {dados.get('pagador_doc', '-')}

🏪 *Destinatário:* {dados.get('destinatario', '-')}
📋 *Doc:* {dados.get('destinatario_doc', '-')}
🏦 *Banco:* {dados.get('banco', '-')}
💳 *Ag/Conta:* {dados.get('agencia', '-')}/{dados.get('conta', '-')}

💰 *Valor:* {_formatar_valor(valor)}
📅 *Data:* {dados.get('data', '-')}
🔢 *Protocolo:* {dados.get('protocolo', '-')}

🏷️ *Categoria sugerida:* {categoria.upper()}

━━━━━━━━━━━━━━━━━━━━
*Escolha uma opção:*

1️⃣ *PAGO* - Marcar como pago e registrar despesa
2️⃣ *DESPESA* - Registrar como despesa
3️⃣ *AGENDA* - Salvar na agenda
4️⃣ *TUDO* - Despesa + Agenda

💡 Ou digite: *despesa {categoria}* para mudar categoria"""


def process_comprovante_image(file_base64: str, filename: str, user_id: str, 
                               user_name: str, caption: str) -> dict:
    """Processa imagem de comprovante usando Extrator Brasil, Gemini Vision ou OCR"""
    try:
        texto_extraido = ""
        dados_extraidos = None
        fonte_extracao = None
        
        # === MÉTODO 0: EXTRATOR BRASILEIRO (Gratuito, Offline) ===
        # Tenta primeiro com extrator especializado para boletos/PIX/TED brasileiros
        try:
            if comprovantes_module:
                image_bytes = base64.b64decode(file_base64)
                resultado_brasil = comprovantes_module.processar_imagem_brasil(image_bytes, user_id)
                
                if resultado_brasil and resultado_brasil.get('status') == 'sucesso':
                    print(f"[EXTRATOR BRASIL] Sucesso! Tipo: {resultado_brasil.get('tipo')}")
                    
                    # Extrai os dados do resultado
                    dados = resultado_brasil.get('dados', {})
                    
                    # Mapeia para formato padrão
                    dados_extraidos = {
                        'tipo': resultado_brasil.get('tipo', 'outro'),
                        'valor': dados.get('valor', 0),
                        'pagador': dados.get('pagador', ''),
                        'pagador_doc': dados.get('pagador_doc', ''),
                        'destinatario': dados.get('destinatario', dados.get('beneficiario', '')),
                        'destinatario_doc': dados.get('destinatario_doc', dados.get('beneficiario_doc', '')),
                        'destinatario_banco': dados.get('banco', ''),
                        'data': dados.get('data_vencimento', dados.get('data', '')),
                        'hora': dados.get('hora', ''),
                        'id_transacao': dados.get('id_transacao', dados.get('linha_digitavel', '')),
                        'descricao': dados.get('descricao', ''),
                        'categoria_sugerida': dados.get('categoria', 'outros')
                    }
                    
                    # Adiciona dados extras específicos do tipo
                    if 'boleto_dados' in resultado_brasil:
                        dados_extraidos['boleto_dados'] = resultado_brasil['boleto_dados']
                    if 'pix_dados' in resultado_brasil:
                        dados_extraidos['pix_dados'] = resultado_brasil['pix_dados']
                    if 'transferencia_dados' in resultado_brasil:
                        dados_extraidos['transferencia_dados'] = resultado_brasil['transferencia_dados']
                    
                    texto_extraido = f"Tipo: {dados_extraidos['tipo']} | Valor: R$ {dados_extraidos['valor']}"
                    fonte_extracao = 'extrator_brasil'
                    
        except Exception as e:
            print(f"[EXTRATOR BRASIL] Erro: {e}")
            import traceback
            traceback.print_exc()
        
        # Se extrator brasileiro não funcionou, tenta Gemini
        # Verifica se deve usar Gemini (configuração)
        usar_gemini = os.getenv('USAR_GEMINI', 'True').lower() == 'true'
        
        # === MÉTODO 1: GEMINI VISION (IA - Mais preciso) ===
        if not dados_extraidos and usar_gemini:
            try:
                import google.generativeai as genai
                from PIL import Image
                import io
                
                api_key = os.getenv('GEMINI_API_KEY')
                if api_key:
                    genai.configure(api_key=api_key)
                    
                    # Usa modelo com visão
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # Decodifica imagem
                    image_bytes = base64.b64decode(file_base64)
                    image = Image.open(io.BytesIO(image_bytes))
                    
                    # Prompt para extrair dados do comprovante
                    prompt = """Analise esta imagem de comprovante de pagamento/PIX e extraia as informações em formato JSON.

Retorne APENAS um JSON válido (sem markdown, sem ```json) com os seguintes campos:
{
    "tipo": "pix" ou "transferencia" ou "boleto" ou "recibo" ou "cartao" ou "outro",
    "valor": número decimal (apenas o número, ex: 150.00),
    "pagador": "nome de quem pagou",
    "pagador_doc": "CPF/CNPJ do pagador (se visível)",
    "destinatario": "nome de quem recebeu o pagamento",
    "destinatario_doc": "CPF/CNPJ do destinatário (se visível)",
    "destinatario_banco": "banco do destinatário (se visível)",
    "data": "data do pagamento no formato DD/MM/YYYY",
    "hora": "hora do pagamento (se visível)",
    "id_transacao": "código/ID da transação (se visível)",
    "descricao": "descrição ou mensagem do pagamento (se houver)",
    "categoria_sugerida": sugira uma categoria entre: alimentacao, transporte, moradia, saude, educacao, lazer, compras, servicos, contas, impostos, investimentos, outros
}

Se algum campo não estiver visível ou legível, use null.
IMPORTANTE: Retorne APENAS o JSON, sem explicações ou texto adicional."""

                    # Envia imagem para análise
                    response = model.generate_content([prompt, image])
                    
                    # Extrai JSON da resposta
                    resposta_texto = response.text.strip()
                    print(f"[GEMINI VISION] Resposta: {resposta_texto[:500]}")
                    
                    # Remove markdown se houver
                    if resposta_texto.startswith('```'):
                        resposta_texto = resposta_texto.split('```')[1]
                        if resposta_texto.startswith('json'):
                            resposta_texto = resposta_texto[4:]
                    
                    # Parse JSON
                    import json
                    dados_extraidos = json.loads(resposta_texto)
                    fonte_extracao = 'gemini_vision'
                    print(f"[GEMINI VISION] Dados extraídos: {dados_extraidos}")
                    
                    # Formata o texto para processamento
                    texto_extraido = f"""
                    Tipo: {dados_extraidos.get('tipo', '')}
                    Valor: R$ {dados_extraidos.get('valor', '')}
                    Pagador: {dados_extraidos.get('pagador', '')}
                    Destinatário: {dados_extraidos.get('destinatario', '')}
                    Data: {dados_extraidos.get('data', '')}
                    Descrição: {dados_extraidos.get('descricao', '')}
                    """
                    
            except ImportError:
                print("[GEMINI] google-generativeai não instalado")
            except Exception as e:
                print(f"[GEMINI VISION] Erro: {e}")
                import traceback
                traceback.print_exc()
        elif not dados_extraidos:
            print("[GEMINI] Desabilitado por configuração ou extrator brasileiro já funcionou")
        
        # === MÉTODO 2: OCR TRADICIONAL (Fallback) ===
        if not texto_extraido or len(texto_extraido) < 10:
            try:
                from PIL import Image
                import pytesseract
                import io
                
                image_bytes = base64.b64decode(file_base64)
                image = Image.open(io.BytesIO(image_bytes))
                texto_extraido = pytesseract.image_to_string(image, lang='por')
                print(f"[OCR] Texto extraído: {texto_extraido[:200]}...")
                
            except ImportError:
                print("[OCR] pytesseract não disponível")
            except Exception as e:
                print(f"[OCR] Erro: {e}")
        
        # Se não conseguiu extrair nada, pede ajuda
        if not texto_extraido or len(texto_extraido) < 10:
            return jsonify({
                'success': True,
                'response': f"""📸 *Imagem recebida:* {filename}

⚠️ Não consegui ler o texto da imagem.

Por favor, me diga os dados do comprovante:
• Qual o *valor*? (ex: 50,00)
• Para quem foi? (ex: Mercado X)
• Qual a *categoria*? (alimentação, transporte, etc.)

Exemplo: "Gastei 50 no mercado, categoria alimentação" """
            })
        
        # Se temos dados extraídos via Gemini, usa direto
        if dados_extraidos:
            # Cria comprovante com dados da IA
            comprovante = {
                'id': f"comp_{user_id}_{int(__import__('time').time())}",
                'user_id': user_id,
                'tipo': dados_extraidos.get('tipo', 'outro'),
                'valor': float(dados_extraidos.get('valor', 0)) if dados_extraidos.get('valor') else 0,
                'pagador': dados_extraidos.get('pagador', ''),
                'pagador_doc': dados_extraidos.get('pagador_doc', ''),
                'destinatario': dados_extraidos.get('destinatario', ''),
                'destinatario_doc': dados_extraidos.get('destinatario_doc', ''),
                'destinatario_banco': dados_extraidos.get('destinatario_banco', ''),
                'data': dados_extraidos.get('data', ''),
                'hora': dados_extraidos.get('hora', ''),
                'id_transacao': dados_extraidos.get('id_transacao', ''),
                'descricao': dados_extraidos.get('descricao', ''),
                'categoria': dados_extraidos.get('categoria_sugerida', 'outros'),
                'status': 'pendente',
                'confianca': 0.85 if fonte_extracao == 'extrator_brasil' else 0.9,
                'fonte': fonte_extracao or 'gemini_vision',
                'texto_original': texto_extraido,
                'imagem_base64': file_base64[:100] + '...'  # Guarda referência
            }
            
            # Salva como pendente
            comprovantes_module._salvar_pendente(comprovante)
            
            # Formata mensagem de confirmação bonita
            valor_fmt = f"R$ {comprovante['valor']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            categoria = comprovante['categoria']
            
            # Monta código para copiar (se disponível)
            codigo_copiar = comprovante.get('id_transacao', '')
            if not codigo_copiar and dados_extraidos.get('linha_digitavel'):
                codigo_copiar = dados_extraidos.get('linha_digitavel')
            elif not codigo_copiar and dados_extraidos.get('chave_pix'):
                codigo_copiar = dados_extraidos.get('chave_pix')
            
            msg = f"""🧾 *COMPROVANTE DETECTADO*

📋 *Tipo:* {comprovante['tipo'].upper()}
💰 *Valor:* {valor_fmt}

👤 *Pagador:* {comprovante['pagador'] or 'Não identificado'}
📄 *Doc:* {comprovante['pagador_doc'] or '-'}

🏪 *Destinatário:* {comprovante['destinatario'] or 'Não identificado'}
📄 *Doc:* {comprovante['destinatario_doc'] or '-'}
🏦 *Banco:* {comprovante['destinatario_banco'] or '-'}

📅 *Data:* {comprovante['data'] or '-'}
⏰ *Hora:* {comprovante['hora'] or '-'}
🔑 *ID:* {comprovante['id_transacao'] or '-'}

📝 *Descrição:* {comprovante['descricao'] or '-'}
🏷️ *Categoria sugerida:* {categoria.upper()}
"""
            
            # Adiciona código para copiar se existir
            if codigo_copiar:
                msg += f"""
📊 *Código/Chave:*
```
{codigo_copiar}
```
"""
            
            msg += f"""
━━━━━━━━━━━━━━━━━━━━
*Escolha uma opção:*
"""
            
            # Se tem código, mostra opção de copiar
            if codigo_copiar:
                msg += "1️⃣ *COPIAR* - Copiar código/chave\n"
            
            msg += f"""2️⃣ *PAGO* - Marcar como pago ✅
3️⃣ *DESPESA* - Registrar como despesa 💰
4️⃣ *AGENDA* - Salvar na agenda 📅
5️⃣ *TUDO* - Pago + Despesa + Agenda ⭐

💡 Para mudar categoria: *despesa {categoria}*
❌ Para descartar: *cancelar*"""

            return jsonify({
                'success': True,
                'response': msg
            })
        
        # Fallback: processa texto via módulo de comprovantes
        comprovante = comprovantes_module.processar_texto_comprovante(texto_extraido, user_id)
        msg_confirmacao = comprovantes_module.formatar_confirmacao(comprovante)
        
        return jsonify({
            'success': True,
            'response': msg_confirmacao
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'response': f'❌ Erro ao processar comprovante: {str(e)}'
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'ok',
        'modules': {
            'voz': voz_module is not None,
            'faturas': faturas_module is not None,
            'email_monitor': email_monitor_module is not None,
            'comprovantes': comprovantes_module is not None
        }
    })


def iniciar_monitor_emails():
    """Inicia o monitor de emails em background"""
    if not email_monitor_module:
        return
    
    def get_gmail_service(user_id: str):
        """Obtém serviço Gmail para um usuário"""
        try:
            # Usa o módulo de agenda que tem o gemini_auth
            from modules.gemini_auth import GeminiAuthManager
            auth = GeminiAuthManager(data_dir="data")
            return auth.get_gmail_service(user_id)
        except Exception as e:
            print(f"Erro ao obter Gmail service: {e}")
            return None
    
    def enviar_notificacao(user_id: str, mensagem: str):
        """Envia notificação via WhatsApp (placeholder)"""
        # Por enquanto, apenas loga. 
        # Para enviar via WhatsApp, precisaríamos de uma conexão inversa
        print(f"📧 [NOTIFICAÇÃO para {user_id}]:")
        print(mensagem)
        print("-" * 50)
        
        # Salva notificações pendentes para serem enviadas quando o usuário interagir
        try:
            import json
            notif_file = os.path.join("data", "notificacoes_pendentes.json")
            notificacoes = {}
            if os.path.exists(notif_file):
                with open(notif_file, 'r') as f:
                    notificacoes = json.load(f)
            
            if user_id not in notificacoes:
                notificacoes[user_id] = []
            notificacoes[user_id].append({
                'mensagem': mensagem,
                'timestamp': datetime.now().isoformat()
            })
            
            with open(notif_file, 'w') as f:
                json.dump(notificacoes, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    email_monitor_module.set_notificacao_callback(enviar_notificacao)
    email_monitor_module.iniciar_monitor(get_gmail_service)



@app.route('/test-oauth/<user_id>/<code>', methods=['GET'])
def test_oauth(user_id, code):
    """Testa OAuth manualmente (útil para debug)"""
    try:
        from modules.gemini_auth import GeminiAuthManager
        auth_manager = GeminiAuthManager(data_dir="data")
        
        print(f"\n[DEBUG-OAUTH] Testando OAuth para user: {user_id}")
        print(f"[DEBUG-OAUTH] Código: {code[:50]}...")
        
        sucesso, erro = auth_manager.complete_auth(user_id, code)
        
        if sucesso:
            return jsonify({
                'success': True,
                'message': 'Login realizado com sucesso!',
                'user_id': user_id
            })
        else:
            return jsonify({
                'success': False,
                'error': erro,
                'user_id': user_id
            }), 400
            
    except Exception as e:
        print(f"[DEBUG-OAUTH] Erro: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════╗
║     🤖 MOGA BOT - API SERVER                     ║
║                                                  ║
║  Porta: 8005                                    ║
║  Endpoint: POST /process                        ║
╚══════════════════════════════════════════════════╝
    """)
    
    # Inicia monitor de emails em background
    iniciar_monitor_emails()
    
    app.run(host='0.0.0.0', port=8005, debug=False)
