"""
🌐 API Server para WhatsApp Bot
Conecta o bot Node.js ao Assistente Python
"""
import os
import sys
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Adiciona path do projeto
sys.path.insert(0, os.path.dirname(__file__))

from middleware.orchestrator import Orchestrator

load_dotenv()

app = Flask(__name__)
orchestrator = Orchestrator()

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

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════╗
║     🌐 API SERVER - ASSISTENTE PESSOAL          ║
║                                                  ║
║  Porta: 5001                                    ║
║  Endpoint: POST /process                        ║
╚══════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=5001, debug=False)
