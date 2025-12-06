"""
🌐 API Server para WhatsApp Bot
Conecta o bot Node.js ao Assistente Python
Suporta: Texto, Áudio e Arquivos (PDF)
"""
import os
import sys
import base64
import tempfile
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


@app.route('/process', methods=['POST'])
def process_message():
    """Processa mensagem de texto do WhatsApp"""
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
        
        if is_pdf and faturas_module:
            # Decodifica o arquivo
            file_bytes = base64.b64decode(file_base64)
            
            # Salva temporariamente
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                f.write(file_bytes)
                file_path = f.name
            
            try:
                # Processa o PDF como fatura/boleto
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
            
            if is_image and comprovantes_module:
                # Processa imagem como comprovante
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
• 📄 PDF de boletos"""
            })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'response': f'❌ Erro ao processar arquivo: {str(e)}'
        }), 500


def process_comprovante_image(file_base64: str, filename: str, user_id: str, 
                               user_name: str, caption: str) -> dict:
    """Processa imagem de comprovante usando Gemini Vision (IA) ou OCR"""
    try:
        texto_extraido = ""
        dados_extraidos = None
        
        # Verifica se deve usar Gemini (configuração)
        usar_gemini = os.getenv('USAR_GEMINI', 'True').lower() == 'true'
        
        # === MÉTODO 1: GEMINI VISION (IA - Mais preciso) ===
        if usar_gemini:
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
        else:
            print("[GEMINI] Desabilitado por configuração (USAR_GEMINI=False)")
        
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
                'confianca': 0.9,  # Alta confiança com Gemini
                'fonte': 'gemini_vision',
                'texto_original': texto_extraido,
                'imagem_base64': file_base64[:100] + '...'  # Guarda referência
            }
            
            # Salva como pendente
            comprovantes_module._salvar_pendente(comprovante)
            
            # Formata mensagem de confirmação bonita
            valor_fmt = f"R$ {comprovante['valor']:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            
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
🏷️ *Categoria sugerida:* {comprovante['categoria']}

━━━━━━━━━━━━━━━━━━━━
✅ Responda *SIM* para salvar esta despesa
❌ Responda *NÃO* para descartar
✏️ Ou envie correções (ex: "valor 150" ou "categoria alimentacao")"""

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
            'faturas': faturas_module is not None
        }
    })

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════╗
║     🌐 API SERVER - ASSISTENTE PESSOAL          ║
║                                                  ║
║  Porta: 8010                                    ║
║  Endpoint: POST /process                        ║
╚══════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=8010, debug=False)
