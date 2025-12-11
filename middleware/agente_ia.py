"""
🧠 Agente de IA Proativo
Sistema inteligente que entende contexto, aprende e toma iniciativas
Suporta múltiplas IAs GRATUITAS: Gemini, Groq, Cohere, HuggingFace, Ollama
"""
import os
import json
import re
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from middleware.formatador_respostas import FormatadorRespostas, humanizar

# Tentar importar Google Generative AI (Gemini - gratuito)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Tentar importar OpenAI (compatível com Groq)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Tentar importar Groq
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

# Tentar importar Cohere
try:
    import cohere
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False


@dataclass
class Contexto:
    """Contexto da conversa com o usuário"""
    user_id: str
    nome: str = ""
    ultima_interacao: str = ""
    historico: List[Dict] = None
    preferencias: Dict = None
    pendencias: List[Dict] = None
    humor: str = "neutro"
    
    def __post_init__(self):
        if self.historico is None:
            self.historico = []
        if self.preferencias is None:
            self.preferencias = {}
        if self.pendencias is None:
            self.pendencias = []


@dataclass
class Acao:
    """Ação que o agente deve executar"""
    tipo: str  # responder, criar_tarefa, agendar, registrar_gasto, etc.
    parametros: Dict
    resposta: str
    proativa: bool = False  # Se foi iniciativa do bot
    confianca: float = 1.0  # 0-1, quão confiante está na ação


class AgenteProativo:
    """
    Agente de IA que:
    - Entende linguagem natural complexa
    - Mantém contexto das conversas
    - Toma iniciativas baseadas em padrões
    - Sugere ações proativamente
    - Aprende com as interações
    """
    
    SYSTEM_PROMPT = """Você é um assistente pessoal inteligente e proativo chamado JARVIS.
Sua função é ajudar o usuário com:
- Agenda e compromissos
- Tarefas e lembretes
- Finanças pessoais (gastos, receitas, saldo)
- Organização geral

REGRAS IMPORTANTES:
1. Seja proativo: se perceber que o usuário precisa de algo, sugira
2. Mantenha contexto: lembre-se do que foi dito antes
3. Extraia informações: datas, valores, descrições
4. Confirme ações importantes antes de executar
5. Seja amigável mas objetivo
6. Use emojis moderadamente

FORMATO DE RESPOSTA (JSON):
{
    "entendi": "resumo do que entendeu",
    "acao": "criar_tarefa|agendar|registrar_gasto|registrar_receita|listar|responder|sugerir",
    "parametros": {
        "descricao": "texto",
        "valor": 0.0,
        "data": "YYYY-MM-DD",
        "hora": "HH:MM",
        "categoria": "categoria"
    },
    "resposta": "mensagem para o usuário",
    "sugestao": "sugestão proativa se houver",
    "pergunta": "pergunta se precisar de mais info"
}

Hoje é {data_atual}. O usuário se chama {nome_usuario}.
"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.contextos_file = os.path.join(data_dir, "contextos_ia.json")
        os.makedirs(data_dir, exist_ok=True)
        
        # Configurar IA
        self.provider = None
        self.model = None
        self.client = None
        self.api_key = None
        self._setup_ia()
        
        # Carregar contextos salvos
        self.contextos: Dict[str, Contexto] = {}
        self._load_contextos()
        
        # Callbacks para módulos
        self.modulos = {}
    
    def _setup_ia(self):
        """Configura provider de IA - Prioriza IAs GRATUITAS"""
        
        # 1. Google Gemini (GRATUITO - 60 req/min)
        gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if GEMINI_AVAILABLE and gemini_key:
            genai.configure(api_key=gemini_key)
            self.model = genai.GenerativeModel('gemini-pro')
            self.provider = 'gemini'
            print("🧠 Agente IA: Usando Google Gemini (GRATUITO)")
            return
        
        # 2. Groq (GRATUITO - 30 req/min, muito rápido)
        groq_key = os.getenv('GROQ_API_KEY')
        if GROQ_AVAILABLE and groq_key:
            self.client = Groq(api_key=groq_key)
            self.provider = 'groq'
            print("🧠 Agente IA: Usando Groq (GRATUITO)")
            return
        
        # 3. Cohere (GRATUITO - 100 req/min)
        cohere_key = os.getenv('COHERE_API_KEY')
        if COHERE_AVAILABLE and cohere_key:
            self.client = cohere.Client(cohere_key)
            self.provider = 'cohere'
            print("🧠 Agente IA: Usando Cohere (GRATUITO)")
            return
        
        # 4. HuggingFace Inference API (GRATUITO)
        hf_key = os.getenv('HUGGINGFACE_API_KEY') or os.getenv('HF_API_KEY')
        if hf_key:
            self.api_key = hf_key
            self.provider = 'huggingface'
            print("🧠 Agente IA: Usando HuggingFace (GRATUITO)")
            return
        
        # 5. Ollama Local (GRATUITO - roda local)
        ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        if self._check_ollama(ollama_url):
            self.api_key = ollama_url
            self.provider = 'ollama'
            print("🧠 Agente IA: Usando Ollama (LOCAL/GRATUITO)")
            return
        
        # 6. OpenAI (PAGO - último recurso)
        openai_key = os.getenv('OPENAI_API_KEY')
        if OPENAI_AVAILABLE and openai_key:
            self.client = OpenAI(api_key=openai_key)
            self.provider = 'openai'
            print("🧠 Agente IA: Usando OpenAI GPT (PAGO)")
            return
        
        # Fallback: Modo local (sem API)
        self.provider = 'local'
        print("🧠 Agente IA: Modo local (padrões)")
        print("   💡 Configure uma IA gratuita no .env:")
        print("      GEMINI_API_KEY=xxx (https://makersuite.google.com/app/apikey)")
        print("      GROQ_API_KEY=xxx (https://console.groq.com)")
        print("      COHERE_API_KEY=xxx (https://cohere.ai)")
    
    def _check_ollama(self, url: str) -> bool:
        """Verifica se Ollama está rodando"""
        try:
            import urllib.request
            urllib.request.urlopen(f"{url}/api/tags", timeout=1)
            return True
        except:
            return False
    
    def set_modulos(self, **modulos):
        """Define os módulos disponíveis"""
        self.modulos = modulos
    
    def _load_contextos(self):
        """Carrega contextos salvos"""
        if os.path.exists(self.contextos_file):
            try:
                with open(self.contextos_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for user_id, ctx in data.items():
                        self.contextos[user_id] = Contexto(**ctx)
            except:
                pass
    
    def _save_contextos(self):
        """Salva contextos"""
        data = {uid: asdict(ctx) for uid, ctx in self.contextos.items()}
        with open(self.contextos_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_contexto(self, user_id: str, nome: str = "") -> Contexto:
        """Obtém ou cria contexto do usuário"""
        if user_id not in self.contextos:
            self.contextos[user_id] = Contexto(user_id=user_id, nome=nome)
        elif nome and not self.contextos[user_id].nome:
            self.contextos[user_id].nome = nome
        return self.contextos[user_id]
    
    async def processar(self, mensagem: str, user_id: str, nome: str = "") -> Acao:
        """
        Processa uma mensagem e retorna a ação a ser tomada
        
        Este é o método principal que:
        1. Obtém contexto do usuário
        2. Analisa a mensagem
        3. Decide a ação
        4. Executa se apropriado
        5. Retorna resposta
        """
        contexto = self.get_contexto(user_id, nome)
        
        # Adiciona ao histórico
        contexto.historico.append({
            'tipo': 'usuario',
            'mensagem': mensagem,
            'timestamp': datetime.now().isoformat()
        })
        
        # Limita histórico a últimas 20 mensagens
        if len(contexto.historico) > 20:
            contexto.historico = contexto.historico[-20:]
        
        # Processa com IA ou localmente
        if self.provider in ['gemini', 'openai', 'groq', 'cohere', 'huggingface', 'ollama']:
            acao = await self._processar_com_ia(mensagem, contexto)
        else:
            acao = self._processar_local(mensagem, contexto)
        
        # Adiciona resposta ao histórico
        contexto.historico.append({
            'tipo': 'assistente',
            'mensagem': acao.resposta,
            'acao': acao.tipo,
            'timestamp': datetime.now().isoformat()
        })
        
        contexto.ultima_interacao = datetime.now().isoformat()
        self._save_contextos()
        
        return acao
    
    async def _processar_com_ia(self, mensagem: str, contexto: Contexto) -> Acao:
        """Processa usando IA (Gemini, Groq, Cohere, HuggingFace, Ollama ou OpenAI)"""
        try:
            # Monta prompt com contexto
            prompt = self._montar_prompt(mensagem, contexto)
            system_prompt = self.SYSTEM_PROMPT.format(
                data_atual=datetime.now().strftime("%d/%m/%Y %H:%M"),
                nome_usuario=contexto.nome or "usuário"
            )
            
            resposta_texto = ""
            
            # === GEMINI (GRATUITO) ===
            if self.provider == 'gemini':
                full_prompt = f"{system_prompt}\n\n{prompt}"
                response = self.model.generate_content(full_prompt)
                resposta_texto = response.text
            
            # === GROQ (GRATUITO - usa Llama/Mixtral) ===
            elif self.provider == 'groq':
                response = self.client.chat.completions.create(
                    model="llama-3.1-70b-versatile",  # Modelo gratuito e potente
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1024
                )
                resposta_texto = response.choices[0].message.content
            
            # === COHERE (GRATUITO) ===
            elif self.provider == 'cohere':
                response = self.client.chat(
                    model="command-r-plus",  # Modelo gratuito
                    message=prompt,
                    preamble=system_prompt,
                    temperature=0.7
                )
                resposta_texto = response.text
            
            # === HUGGINGFACE (GRATUITO) ===
            elif self.provider == 'huggingface':
                resposta_texto = await self._chamar_huggingface(system_prompt, prompt)
            
            # === OLLAMA (LOCAL/GRATUITO) ===
            elif self.provider == 'ollama':
                resposta_texto = await self._chamar_ollama(system_prompt, prompt)
            
            # === OPENAI (PAGO) ===
            elif self.provider == 'openai':
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7
                )
                resposta_texto = response.choices[0].message.content
            
            # Tenta parsear JSON
            return self._parsear_resposta_ia(resposta_texto, mensagem, contexto)
            
        except Exception as e:
            print(f"⚠️ Erro IA ({self.provider}): {e}")
            return self._processar_local(mensagem, contexto)
    
    async def _chamar_huggingface(self, system_prompt: str, prompt: str) -> str:
        """Chama HuggingFace Inference API"""
        import aiohttp
        
        # Usar modelo gratuito (Mistral ou Llama)
        model = "mistralai/Mistral-7B-Instruct-v0.2"
        url = f"https://api-inference.huggingface.co/models/{model}"
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {
            "inputs": f"[INST] {system_prompt}\n\n{prompt} [/INST]",
            "parameters": {
                "max_new_tokens": 1024,
                "temperature": 0.7
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=30) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if isinstance(result, list) and result:
                        return result[0].get('generated_text', '').split('[/INST]')[-1].strip()
                    return str(result)
                else:
                    raise Exception(f"HuggingFace API error: {resp.status}")
    
    async def _chamar_ollama(self, system_prompt: str, prompt: str) -> str:
        """Chama Ollama local"""
        import aiohttp
        
        url = f"{self.api_key}/api/generate"
        payload = {
            "model": "llama3.1",  # ou mistral, codellama, etc
            "prompt": f"{system_prompt}\n\nUsuário: {prompt}\n\nAssistente:",
            "stream": False
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=60) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result.get('response', '')
                else:
                    raise Exception(f"Ollama error: {resp.status}")
    
    def _montar_prompt(self, mensagem: str, contexto: Contexto) -> str:
        """Monta prompt com histórico e contexto"""
        historico_str = ""
        for h in contexto.historico[-5:]:  # Últimas 5 mensagens
            tipo = "Usuário" if h['tipo'] == 'usuario' else "Assistente"
            historico_str += f"{tipo}: {h['mensagem']}\n"
        
        pendencias_str = ""
        if contexto.pendencias:
            pendencias_str = "\nPendências do usuário:\n"
            for p in contexto.pendencias[:5]:
                pendencias_str += f"- {p.get('descricao', p)}\n"
        
        prompt = f"""
Data/Hora atual: {datetime.now().strftime("%d/%m/%Y %H:%M")}
Nome do usuário: {contexto.nome or 'Não informado'}

Histórico recente:
{historico_str}
{pendencias_str}

Mensagem atual do usuário: {mensagem}

Analise a mensagem e retorne um JSON com a ação apropriada.
"""
        return prompt
    
    def _parsear_resposta_ia(self, texto: str, mensagem: str, contexto: Contexto) -> Acao:
        """Parseia resposta da IA"""
        try:
            # Tenta extrair JSON
            json_match = re.search(r'\{[\s\S]*\}', texto)
            if json_match:
                data = json.loads(json_match.group())
                
                return Acao(
                    tipo=data.get('acao', 'responder'),
                    parametros=data.get('parametros', {}),
                    resposta=data.get('resposta', texto),
                    proativa=bool(data.get('sugestao')),
                    confianca=0.9
                )
        except:
            pass
        
        # Fallback: usa texto como resposta
        return Acao(
            tipo='responder',
            parametros={},
            resposta=texto,
            confianca=0.7
        )
    
    def _processar_local(self, mensagem: str, contexto: Contexto) -> Acao:
        """Processamento local sem IA externa - INTERPRETADOR INTELIGENTE"""
        msg = mensagem.lower().strip()
        msg_original = mensagem.strip()
        
        # === SAUDAÇÕES ===
        if self._eh_saudacao(msg):
            return self._responder_saudacao(contexto)
        
        # === DESPEDIDAS ===
        if self._eh_despedida(msg):
            return Acao(
                tipo='responder',
                parametros={},
                resposta="👋 Até logo! Foi um prazer ajudar.\n\nQuando precisar, é só chamar!"
            )
        
        # === AGRADECIMENTO ===
        if self._eh_agradecimento(msg):
            return Acao(
                tipo='responder',
                parametros={},
                resposta="😊 De nada! Fico feliz em ajudar!\n\nPrecisa de mais alguma coisa?"
            )
        
        # === CANCELAR/REMOVER ===
        cancelamento = self._detectar_cancelamento(msg)
        if cancelamento:
            return Acao(
                tipo='cancelar',
                parametros=cancelamento,
                resposta=f"🗑️ Cancelando: *{cancelamento.get('descricao', cancelamento.get('id', ''))}*"
            )
        
        # === MARCAR COMO CONCLUÍDO ===
        conclusao = self._detectar_conclusao(msg)
        if conclusao:
            return Acao(
                tipo='concluir',
                parametros=conclusao,
                resposta=f"✅ Marcando como concluído!"
            )
        
        # === CRIAR TAREFA ===
        tarefa = self._detectar_tarefa(msg, msg_original)
        if tarefa:
            descricao = tarefa['descricao']
            prioridade = tarefa.get('prioridade', 'normal')
            
            # Resposta humanizada
            resposta = f"✅ Anotado!\n📝 {descricao}"
            
            if prioridade == 'alta':
                resposta += "\n🔴 Prioridade alta"
            
            return Acao(
                tipo='criar_tarefa',
                parametros={'descricao': descricao, 'prioridade': prioridade},
                resposta=resposta
            )
        
        # === CRIAR LEMBRETE ===
        lembrete = self._detectar_lembrete(msg, msg_original)
        if lembrete:
            return Acao(
                tipo='criar_lembrete',
                parametros=lembrete,
                resposta=f"⏰ Lembrete criado!\n📝 *{lembrete['texto']}*"
                        + (f"\n📅 {lembrete.get('quando', '')}" if lembrete.get('quando') else "")
            )
        
        # === REGISTRAR GASTO ===
        gasto = self._detectar_gasto(msg, msg_original)
        if gasto:
            # Formata resposta humanizada
            descricao = gasto.get('descricao', '')
            categoria = gasto.get('categoria', 'outros')
            valor = gasto['valor']
            
            emoji_cat = {
                'alimentacao': '🍔',
                'transporte': '🚗',
                'saude': '💊',
                'lazer': '🎮',
                'moradia': '🏠',
                'outros': '💸'
            }.get(categoria.lower(), '💸')
            
            resposta = f"{emoji_cat} Anotado! Você gastou R$ {valor:.2f}"
            if descricao:
                resposta += f" em {descricao}"
            if categoria and categoria != 'outros':
                resposta += f"\n📊 Categoria: {categoria.capitalize()}"
            
            return Acao(
                tipo='registrar_gasto',
                parametros=gasto,
                resposta=resposta
            )
        
        # === REGISTRAR RECEITA ===
        receita = self._detectar_receita(msg, msg_original)
        if receita:
            return Acao(
                tipo='registrar_receita',
                parametros=receita,
                resposta=f"💰 Entrada registrada!\n💵 *R$ {receita['valor']:.2f}*"
                        + (f"\n📝 {receita['descricao']}" if receita.get('descricao') else "")
            )
        
        # === AGENDAR EVENTO ===
        evento = self._detectar_evento(msg, msg_original)
        if evento:
            return Acao(
                tipo='agendar',
                parametros=evento,
                resposta=f"📅 Evento agendado!\n📌 *{evento['titulo']}*"
                        + (f"\n📆 {evento['data']}" if evento.get('data') else "")
                        + (f" às {evento['hora']}" if evento.get('hora') else "")
            )
        
        # === REGISTRAR VENDA ===
        venda = self._detectar_venda(msg, msg_original)
        if venda:
            return Acao(
                tipo='registrar_venda',
                parametros=venda,
                resposta=f"🛒 Venda registrada!\n💰 *R$ {venda['valor']:.2f}*"
                        + (f"\n📦 {venda['descricao']}" if venda.get('descricao') else "")
            )
        
        # === CONSULTAS - TAREFAS ===
        if self._quer_ver_tarefas(msg):
            return Acao(tipo='listar_tarefas', parametros={}, resposta=None)
        
        # === CONSULTAS - AGENDA ===
        if self._quer_ver_agenda(msg):
            return Acao(tipo='listar_agenda', parametros={'data': self._extrair_data(msg)}, resposta=None)
        
        # === CONSULTAS - FINANÇAS ===
        if self._quer_ver_financas(msg):
            return Acao(tipo='ver_financas', parametros={}, resposta=None)
        
        # === CONSULTAS - VENDAS ===
        if self._quer_ver_vendas(msg):
            return Acao(tipo='ver_vendas', parametros={}, resposta=None)
        
        # === CONSULTAS - BOLETOS ===
        if self._quer_ver_boletos(msg):
            return Acao(tipo='ver_boletos', parametros={}, resposta=None)
        
        # === AJUDA ===
        if self._quer_ajuda(msg):
            return self._responder_ajuda()
        
        # === STATUS ===
        if self._quer_status(msg):
            return Acao(tipo='ver_status', parametros={}, resposta=None)
        
        # === NÃO ENTENDEU - SEJA PROATIVO ===
        return self._resposta_proativa(msg, contexto)
    
    # ========== DETECTORES APRIMORADOS ==========
    
    def _eh_saudacao(self, msg: str) -> bool:
        saudacoes = ['oi', 'olá', 'ola', 'hey', 'eai', 'e ai', 'e aí', 'bom dia', 'boa tarde', 
                     'boa noite', 'hello', 'hi', 'fala', 'salve', 'opa', 'oie', 'oii', 'oiii']
        return any(msg.startswith(s) or msg == s for s in saudacoes)
    
    def _eh_despedida(self, msg: str) -> bool:
        despedidas = ['tchau', 'até', 'ate', 'bye', 'adeus', 'flw', 'falou', 'vlw', 'valeu',
                      'até mais', 'ate mais', 'até logo', 'ate logo', 'fui']
        return any(d in msg for d in despedidas)
    
    def _eh_agradecimento(self, msg: str) -> bool:
        agradecimentos = ['obrigado', 'obrigada', 'obg', 'thanks', 'thank you', 'valeu', 
                          'vlw', 'tmj', 'muito obrigado', 'muito obrigada', 'brigadão', 'brigado']
        return any(a in msg for a in agradecimentos)
    
    def _detectar_cancelamento(self, msg: str) -> Optional[Dict]:
        """Detecta intenção de cancelar/remover algo"""
        palavras_cancelar = ['cancelar', 'cancela', 'remover', 'remove', 'deletar', 'deleta', 
                             'apagar', 'apaga', 'excluir', 'exclui', 'tirar', 'tira',
                             'desmarcar', 'desmarca', 'descartar', 'descarta']
        
        if not any(word in msg for word in palavras_cancelar):
            return None
        
        # Tenta extrair ID (códigos hexadecimais ou numéricos)
        id_match = re.search(r'\b([a-f0-9]{4,8})\b', msg)
        item_id = id_match.group(1) if id_match else None
        
        # Detecta tipo de item
        tipo = 'geral'
        if any(word in msg for word in ['tarefa', 'tarefas', 'todo']):
            tipo = 'tarefa'
        elif any(word in msg for word in ['evento', 'compromisso', 'reunião', 'reuniao', 'agenda']):
            tipo = 'evento'
        elif any(word in msg for word in ['lembrete', 'alarme', 'aviso']):
            tipo = 'lembrete'
        elif any(word in msg for word in ['gasto', 'despesa']):
            tipo = 'gasto'
        elif any(word in msg for word in ['venda']):
            tipo = 'venda'
        elif any(word in msg for word in ['boleto', 'fatura']):
            tipo = 'boleto'
        
        return {'tipo': tipo, 'id': item_id, 'descricao': ''}
    
    def _detectar_conclusao(self, msg: str) -> Optional[Dict]:
        """Detecta intenção de marcar algo como concluído"""
        palavras = ['concluir', 'concluí', 'conclui', 'terminei', 'terminado', 'feito', 'fiz',
                    'finalizar', 'finalizei', 'completar', 'completei', 'pronto', 'acabei', 'done']
        
        if not any(word in msg for word in palavras):
            return None
        
        # Tenta extrair ID
        id_match = re.search(r'\b([a-f0-9]{4,8})\b', msg)
        item_id = id_match.group(1) if id_match else None
        
        return {'id': item_id}
    
    def _detectar_tarefa(self, msg: str, original: str) -> Optional[Dict]:
        """Detecta intenção de criar tarefa - APRIMORADO"""
        patterns = [
            # "preciso fazer X", "tenho que fazer X"
            r'(?:preciso|tenho que|devo|vou ter que|necessito)\s+(?:de\s+)?(.+)',
            # "não posso esquecer de X", "não esquecer X"
            r'(?:não|nao)\s+(?:posso\s+)?(?:esquecer|esquece)\s+(?:de\s+)?(.+)',
            # "lembrar de X" (sem "me" = tarefa)
            r'(?:lembrar|anotar)\s+(?:de\s+)?(?:que\s+)?(.+)',
            # "adicionar tarefa X", "criar tarefa X"
            r'(?:adicionar?|criar?|nova?)\s+tarefa[:\s]+(.+)',
            # "tarefa: X"
            r'^tarefa[:\s]+(.+)',
            # "me lembra de X amanhã" pode ser lembrete ou tarefa
            r'(?:me\s+)?(?:lembra|lembre)\s+(?:de\s+)?(?:que\s+)?(.+?)(?:\s+(?:amanhã|depois|hoje|às|as|no dia))?$',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, msg, re.IGNORECASE)
            if match:
                tarefa = match.group(1).strip()
                # Remove palavras desnecessárias
                tarefa = re.sub(r'^(que|para|pra|de)\s+', '', tarefa)
                # Remove tempos verbais comuns
                tarefa = re.sub(r'\s+(amanhã|depois|hoje)$', '', tarefa, flags=re.IGNORECASE)
                
                if len(tarefa) > 2:
                    # Detecta prioridade
                    prioridade = 'normal'
                    if any(p in msg for p in ['urgente', 'importante', 'crítico', 'prioridade alta', 'asap']):
                        prioridade = 'alta'
                    elif any(p in msg for p in ['baixa prioridade', 'quando puder', 'sem pressa']):
                        prioridade = 'baixa'
                    
                    return {'descricao': tarefa, 'prioridade': prioridade}
        return None
    
    def _detectar_lembrete(self, msg: str, original: str) -> Optional[Dict]:
        """Detecta intenção de criar lembrete - NOVO"""
        patterns = [
            # "me lembra de X às 14h", "me avisa sobre X amanhã"
            r'(?:me\s+)?(?:lembra|lembre|avisa|avise)\s+(?:de\s+|sobre\s+)?(.+?)\s+(?:às|as|em|no dia|daqui)\s+(.+)',
            # "lembrete: X"
            r'(?:lembrete|alarme)[:\s]+(.+)',
            # "daqui X tempo me lembra de Y"
            r'daqui\s+(.+?)\s+(?:me\s+)?(?:lembra|avisa)\s+(?:de\s+)?(.+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, msg, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    texto = match.group(1).strip()
                    quando = match.group(2).strip()
                else:
                    texto = match.group(1).strip()
                    quando = ""
                
                if len(texto) > 2:
                    return {'texto': texto, 'quando': quando}
        return None
    
    def _detectar_gasto(self, msg: str, original: str) -> Optional[Dict]:
        """Detecta registro de gasto - APRIMORADO"""
        patterns = [
            # "gastei 50 com uber", "gastei R$ 50 no mercado"
            r'(?:gastei|paguei|comprei|despesa|pagar)\s+(?:de\s+)?(?:r\$?\s*)?(\d+[.,]?\d*)\s*(?:reais?)?\s*(?:com|em|no|na|de)?\s*(.+)?',
            # "50 reais de almoço", "R$ 100 no mercado"  
            r'(?:r\$?\s*)?(\d+[.,]?\d*)\s*(?:reais?)?\s+(?:de|com|em|no|na|para|pro)\s+(.+)',
            # "almoço 30 reais", "uber 25"
            r'(.+?)\s+(?:r\$?\s*)?(\d+[.,]?\d*)\s*(?:reais?)?$',
            # "comprei X por Y"
            r'comprei\s+(.+?)\s+(?:por\s+)?(?:r\$?\s*)?(\d+[.,]?\d*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, msg, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                # Determina qual grupo é valor e qual é descrição
                valor = None
                descricao = ""
                
                for g in groups:
                    if g:
                        # Tenta converter para número
                        try:
                            num = float(g.replace(',', '.').replace('r$', '').strip())
                            if num > 0 and num < 1000000:
                                valor = num
                        except:
                            if len(g.strip()) > 1:
                                descricao = g.strip()
                
                if valor:
                    categoria = self._detectar_categoria_gasto(msg)
                    return {
                        'valor': valor,
                        'descricao': descricao[:100] if descricao else "",
                        'categoria': categoria,
                        'tipo': 'saida'
                    }
        return None
    
    def _responder_saudacao(self, contexto: Contexto) -> Acao:
        hora = datetime.now().hour
        if hora < 12:
            saudacao = "Bom dia"
        elif hora < 18:
            saudacao = "Boa tarde"
        else:
            saudacao = "Boa noite"
        
        nome = f", {contexto.nome}" if contexto.nome else ""
        
        # Verifica se tem pendências para mencionar
        sugestao = ""
        if contexto.pendencias:
            sugestao = f"\n\n💡 Você tem {len(contexto.pendencias)} tarefa(s) pendente(s). Quer ver?"
        
        return Acao(
            tipo='responder',
            parametros={},
            resposta=f"{saudacao}{nome}! 👋\n\nComo posso te ajudar hoje?{sugestao}",
            proativa=bool(sugestao)
        )
    
    def _detectar_categoria_gasto(self, msg: str) -> str:
        """Detecta categoria do gasto - APRIMORADO"""
        categorias = {
            'alimentacao': ['almoço', 'almoco', 'janta', 'jantar', 'café', 'cafe', 'lanche', 'comida', 
                           'restaurante', 'mercado', 'supermercado', 'ifood', 'delivery', 'uber eats',
                           'rappi', 'pizzaria', 'padaria', 'açougue', 'feira', 'hortifruti', 'sushi',
                           'hamburguer', 'mcdonald', 'burger king', 'subway', 'starbucks'],
            'transporte': ['uber', '99', '99pop', 'cabify', 'gasolina', 'combustível', 'combustivel',
                          'estacionamento', 'onibus', 'ônibus', 'metro', 'metrô', 'passagem', 'trem',
                          'taxi', 'táxi', 'pedágio', 'pedagio', 'ipva', 'seguro carro', 'manutenção carro'],
            'moradia': ['aluguel', 'condomínio', 'condominio', 'luz', 'energia', 'água', 'agua', 
                       'gas', 'gás', 'internet', 'wifi', 'telefone', 'celular', 'iptu', 'conta de luz',
                       'conta de água', 'conta de gás', 'reforma', 'manutenção casa', 'móveis'],
            'saude': ['farmácia', 'farmacia', 'remédio', 'remedio', 'médico', 'medico', 'consulta',
                     'dentista', 'psicólogo', 'psicologo', 'exame', 'hospital', 'plano de saúde',
                     'academia', 'gym', 'suplemento', 'vitamina', 'ótica', 'otica', 'óculos'],
            'lazer': ['cinema', 'netflix', 'spotify', 'amazon prime', 'disney', 'hbo', 'bar', 
                     'festa', 'viagem', 'hotel', 'airbnb', 'show', 'teatro', 'museu', 'parque',
                     'ingresso', 'game', 'jogo', 'playstation', 'xbox', 'steam'],
            'educacao': ['curso', 'livro', 'escola', 'faculdade', 'universidade', 'mensalidade',
                        'material escolar', 'udemy', 'coursera', 'alura', 'apostila', 'aula'],
            'vestuario': ['roupa', 'sapato', 'tênis', 'tenis', 'camisa', 'calça', 'calca', 'vestido',
                         'blusa', 'shorts', 'jaqueta', 'casaco', 'meia', 'cueca', 'calcinha', 'sutiã'],
            'pets': ['ração', 'racao', 'pet', 'cachorro', 'gato', 'veterinário', 'veterinario', 
                    'petshop', 'pet shop'],
            'beleza': ['cabelo', 'salão', 'salao', 'barbearia', 'manicure', 'maquiagem', 'perfume',
                      'creme', 'shampoo', 'condicionador'],
            'assinaturas': ['assinatura', 'mensalidade', 'spotify', 'netflix', 'amazon', 'apple',
                           'icloud', 'google one', 'dropbox', 'adobe', 'microsoft'],
        }
        
        for categoria, keywords in categorias.items():
            if any(k in msg for k in keywords):
                return categoria
        return 'outros'
    
    def _detectar_receita(self, msg: str, original: str) -> Optional[Dict]:
        """Detecta registro de receita - APRIMORADO"""
        patterns = [
            # "recebi 1000 de salário", "ganhei 500 de freelance"
            r'(?:recebi|ganhei|entrou|entrada|depositaram|caiu)\s+(?:de\s+)?(?:r\$?\s*)?(\d+[.,]?\d*)\s*(?:reais?)?\s*(?:de|do|da)?\s*(.+)?',
            # "salário de 3000", "freelance de 500"
            r'(?:salário|salario|pagamento|freela|freelance|bico|extra|comissão|comissao|bonus|bônus)\s+(?:de\s+)?(?:r\$?\s*)?(\d+[.,]?\d*)',
            # "1000 reais do trabalho"
            r'(?:r\$?\s*)?(\d+[.,]?\d*)\s*(?:reais?)?\s+(?:de|do|da)\s+(?:salário|salario|trabalho|freela|venda)',
            # "pix de 200"
            r'(?:pix|transferência|transferencia|ted|doc)\s+(?:de\s+)?(?:r\$?\s*)?(\d+[.,]?\d*)\s+(?:recebido|que recebi|entrada)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, msg, re.IGNORECASE)
            if match:
                valor = float(match.group(1).replace(',', '.'))
                descricao = match.group(2).strip() if len(match.groups()) > 1 and match.group(2) else ""
                
                # Tenta identificar tipo de receita
                if any(p in msg for p in ['salário', 'salario', 'trabalho']):
                    descricao = descricao or "Salário"
                elif any(p in msg for p in ['freela', 'freelance', 'bico']):
                    descricao = descricao or "Freelance"
                elif any(p in msg for p in ['venda', 'vendi']):
                    descricao = descricao or "Venda"
                elif any(p in msg for p in ['aluguel']):
                    descricao = descricao or "Aluguel recebido"
                
                return {
                    'valor': valor,
                    'descricao': descricao[:100] if descricao else "",
                    'tipo': 'entrada'
                }
        return None
    
    def _detectar_evento(self, msg: str, original: str) -> Optional[Dict]:
        """Detecta agendamento de evento - APRIMORADO"""
        patterns = [
            # "agendar reunião com João amanhã às 14h"
            r'(?:agendar?|marcar?|tenho)\s+(.+?)\s+(?:para|no dia|em|dia)\s+(.+?)(?:\s+(?:às|as)\s+(\d{1,2}[h:]?\d{0,2}))?',
            # "reunião com cliente amanhã 15h"
            r'(?:reunião|reuniao|consulta|compromisso|encontro|call|meeting)\s+(?:com\s+)?(.+?)\s+(.+?)(?:\s+(\d{1,2}[h:]?\d{0,2}))?$',
            # "amanhã tenho dentista às 10h"
            r'(hoje|amanhã|amanha|segunda|terça|terca|quarta|quinta|sexta|sábado|sabado|domingo)\s+(?:tenho|tem)\s+(.+?)(?:\s+(?:às|as)\s+(\d{1,2}[h:]?\d{0,2}))?',
            # "marcar X para dia DD/MM"
            r'(?:marcar?|agendar?)\s+(.+?)\s+(?:para\s+)?(?:dia\s+)?(\d{1,2}/\d{1,2}(?:/\d{2,4})?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, msg, re.IGNORECASE)
            if match:
                groups = match.groups()
                titulo = groups[0].strip() if groups[0] else ""
                data_texto = groups[1].strip() if len(groups) > 1 and groups[1] else ""
                hora = groups[2] if len(groups) > 2 and groups[2] else ""
                
                # Limpa título
                titulo = re.sub(r'^(uma?|o)\s+', '', titulo)
                
                if len(titulo) > 2:
                    data = self._extrair_data(data_texto) or self._extrair_data(msg)
                    hora = self._extrair_hora(hora) or self._extrair_hora(msg)
                    
                    return {
                        'titulo': titulo[:100],
                        'data': data,
                        'hora': hora
                    }
        return None
    
    def _detectar_venda(self, msg: str, original: str) -> Optional[Dict]:
        """Detecta registro de venda - APRIMORADO"""
        patterns = [
            # "vendi por 100"
            r'(?:vendi|venda|vendido)\s+(?:por\s+)?(?:r\$?\s*)?(\d+[.,]?\d*)',
            # "vendi X por 100"
            r'(?:vendi|venda|vendido)\s+(.+?)\s+(?:por\s+)?(?:r\$?\s*)?(\d+[.,]?\d*)',
            # "cliente comprou X por Y"
            r'(?:cliente\s+)?(?:comprou|pagou)\s+(.+?)\s+(?:por\s+)?(?:r\$?\s*)?(\d+[.,]?\d*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, msg, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 1:
                    valor = float(groups[0].replace(',', '.'))
                    descricao = ""
                else:
                    descricao = groups[0].strip() if groups[0] else ""
                    valor = float(groups[1].replace(',', '.'))
                
                return {
                    'valor': valor,
                    'descricao': descricao[:100]
                }
        return None
    
    def _extrair_data(self, texto: str) -> Optional[str]:
        """Extrai data do texto"""
        hoje = datetime.now()
        
        if 'hoje' in texto:
            return hoje.strftime('%Y-%m-%d')
        if 'amanhã' in texto or 'amanha' in texto:
            return (hoje + timedelta(days=1)).strftime('%Y-%m-%d')
        if 'depois de amanhã' in texto or 'depois de amanha' in texto:
            return (hoje + timedelta(days=2)).strftime('%Y-%m-%d')
        
        # Dias da semana
        dias = {'segunda': 0, 'terça': 1, 'terca': 1, 'quarta': 2, 
                'quinta': 3, 'sexta': 4, 'sábado': 5, 'sabado': 5, 'domingo': 6}
        for dia, num in dias.items():
            if dia in texto:
                dias_ate = (num - hoje.weekday()) % 7
                if dias_ate == 0:
                    dias_ate = 7
                return (hoje + timedelta(days=dias_ate)).strftime('%Y-%m-%d')
        
        # Data explícita (DD/MM ou DD/MM/YYYY)
        match = re.search(r'(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?', texto)
        if match:
            dia = int(match.group(1))
            mes = int(match.group(2))
            ano = int(match.group(3)) if match.group(3) else hoje.year
            if ano < 100:
                ano += 2000
            return f"{ano}-{mes:02d}-{dia:02d}"
        
        return None
    
    def _extrair_hora(self, texto: str) -> Optional[str]:
        """Extrai hora do texto"""
        # "às 14h", "14:30", "2pm"
        match = re.search(r'(\d{1,2})[h:](\d{2})?', texto)
        if match:
            hora = int(match.group(1))
            minuto = int(match.group(2)) if match.group(2) else 0
            return f"{hora:02d}:{minuto:02d}"
        return None
    
    def _quer_ver_tarefas(self, msg: str) -> bool:
        return any(p in msg for p in ['minhas tarefas', 'lista de tarefas', 'ver tarefas', 
                                       'pendências', 'pendencias', 'to do', 'afazeres', 
                                       'o que tenho que fazer', 'mostrar tarefas', 'listar tarefas'])
    
    def _quer_ver_agenda(self, msg: str) -> bool:
        return any(p in msg for p in ['minha agenda', 'ver agenda', 'compromissos', 'eventos',
                                       'o que tenho hoje', 'o que tenho amanhã', 'mostrar agenda',
                                       'próximos compromissos', 'proximos compromissos'])
    
    def _quer_ver_financas(self, msg: str) -> bool:
        return any(p in msg for p in ['meu saldo', 'finanças', 'financas', 'quanto tenho',
                                       'meus gastos', 'resumo financeiro', 'dinheiro',
                                       'quanto gastei', 'balanço', 'balanco', 'extrato'])
    
    def _quer_ver_vendas(self, msg: str) -> bool:
        return any(p in msg for p in ['minhas vendas', 'ver vendas', 'relatório de vendas',
                                       'quanto vendi', 'faturamento', 'vendas de hoje',
                                       'vendas do mês', 'vendas do mes'])
    
    def _quer_ver_boletos(self, msg: str) -> bool:
        return any(p in msg for p in ['meus boletos', 'boletos', 'faturas', 'contas a pagar',
                                       'contas para pagar', 'ver boletos', 'listar boletos'])
    
    def _quer_status(self, msg: str) -> bool:
        return any(p in msg for p in ['status', 'como está', 'como esta', 'funcionando',
                                       'está online', 'esta online', 'tudo certo'])
    
    def _quer_ajuda(self, msg: str) -> bool:
        return any(p in msg for p in ['ajuda', 'help', 'comandos', 'o que você faz',
                                       'como funciona', 'o que sabe fazer', 'o que posso fazer',
                                       'me ajuda', 'não entendi', 'nao entendi', '?'])
    
    def _responder_ajuda(self) -> Acao:
        return Acao(
            tipo='responder',
            parametros={},
            resposta="""🤖 *Sou seu Assistente Pessoal Inteligente!*

Você pode falar comigo naturalmente. Exemplos:

📝 *Tarefas:*
• "Preciso comprar leite"
• "Não esquecer de ligar pro João"
• "Minhas tarefas" / "Concluir tarefa abc123"

💰 *Finanças:*
• "Gastei 50 no uber"
• "Recebi 3000 de salário"
• "Quanto gastei esse mês?"

📅 *Agenda:*
• "Tenho reunião amanhã às 14h"
• "Marcar dentista sexta às 10h"
• "Me lembra de pagar conta amanhã"

⏰ *Lembretes:*
• "Me lembra de X às 15h"
• "Daqui 30 minutos me avisa"

🛒 *Vendas:*
• "Vendi 150 reais"
• "Minhas vendas de hoje"

📄 *Boletos:*
• Envie foto ou PDF de boleto
• "Meus boletos"

🎤 *Voz:*
• Envie um áudio que eu transcrevo!

❌ *Cancelar:*
• "Cancelar tarefa abc123"
• "Remover lembrete xyz"

É só falar naturalmente! 😊"""
        )
    
    def _resposta_proativa(self, msg: str, contexto: Contexto) -> Acao:
        """Quando não entende, tenta ser proativo e dar sugestões úteis"""
        sugestoes = []
        
        # Analisa palavras-chave para sugerir ações
        palavras = msg.split()
        
        # Se parece com um valor monetário
        if re.search(r'\d+(?:[.,]\d+)?', msg) and not re.search(r'\d{2}/\d{2}', msg):
            sugestoes.append("💡 Parece um valor. Você quer registrar um *gasto* ou uma *entrada*?")
        
        # Se menciona tempo/data
        if any(p in msg for p in ['amanhã', 'amanha', 'hoje', 'semana', 'mês', 'mes']):
            sugestoes.append("💡 Quer *agendar* algo ou ver sua *agenda*?")
        
        # Se parece pergunta
        if '?' in msg or msg.startswith(('qual', 'quanto', 'quando', 'onde', 'como', 'quem')):
            if 'quanto' in msg and 'gast' in msg:
                return Acao(tipo='ver_financas', parametros={}, resposta=None)
            sugestoes.append("💡 Posso ajudar com informações sobre suas *tarefas*, *finanças* ou *agenda*.")
        
        # Verifica hora do dia para sugestões contextuais
        hora = datetime.now().hour
        if 8 <= hora <= 10 and not sugestoes:
            sugestoes.append("☀️ Bom dia! Quer ver sua *agenda de hoje* ou *tarefas pendentes*?")
        elif 12 <= hora <= 14 and not sugestoes:
            sugestoes.append("🍽️ Hora do almoço! Registrou algum gasto?")
        elif 17 <= hora <= 19 and not sugestoes:
            sugestoes.append("🌅 Final do dia! Quer ver um *resumo* de hoje?")
        
        # Resposta base quando não entende
        if sugestoes:
            resp = "🤔 Não entendi bem.\n\n" + "\n".join(sugestoes)
        else:
            resp = """🤔 Não entendi. Você pode:

• Registrar gastos: "Gastei 50 no almoço"
• Criar tarefas: "Preciso comprar leite"
• Agendar: "Reunião amanhã às 14h"
• Consultar: "Minhas tarefas", "Meu saldo"

Ou digite *ajuda* para ver mais opções."""
        
        return Acao(
            tipo='responder',
            parametros={},
            resposta=resp
        )
        hora = datetime.now().hour
        if 11 <= hora <= 13:
            sugestoes.append("Hora do almoço! Quer registrar o gasto?")
        elif hora >= 18:
            sugestoes.append("Final do dia! Quer ver um resumo de hoje?")
        
        # Verifica se falou algo que pode ser tarefa
        if len(msg.split()) > 2:
            sugestoes.append(f"Quer que eu anote isso como tarefa?\n📝 \"{msg[:50]}...\"")
        
        resposta = "🤔 Hmm, não tenho certeza do que você precisa.\n\n"
        
        if sugestoes:
            resposta += "💡 *Sugestão:* " + sugestoes[0] + "\n\n"
        
        resposta += "Você pode:\n"
        resposta += "• Registrar um gasto ou receita\n"
        resposta += "• Criar uma tarefa\n"
        resposta += "• Agendar um compromisso\n"
        resposta += "• Ver suas finanças ou tarefas\n\n"
        resposta += "Digite /ajuda para mais opções!"
        
        return Acao(
            tipo='responder',
            parametros={},
            resposta=resposta,
            proativa=True
        )
    
    # ========== AÇÕES PROATIVAS ==========
    
    async def verificar_lembretes(self, enviar_callback: Callable) -> List[Dict]:
        """Verifica e envia lembretes pendentes"""
        # TODO: Implementar sistema de lembretes com scheduler
        pass
    
    async def sugerir_acoes_diarias(self, user_id: str) -> Optional[str]:
        """Sugere ações baseadas no padrão do usuário"""
        contexto = self.contextos.get(user_id)
        if not contexto:
            return None
        
        sugestoes = []
        hora = datetime.now().hour
        
        # Manhã: lembrar de tarefas
        if 8 <= hora <= 10:
            if contexto.pendencias:
                sugestoes.append(f"☀️ Bom dia! Você tem {len(contexto.pendencias)} tarefa(s) pendente(s).")
        
        # Final do dia: resumo
        elif 17 <= hora <= 19:
            sugestoes.append("🌅 Fim do dia! Quer ver um resumo de hoje?")
        
        return sugestoes[0] if sugestoes else None
    
    def adicionar_pendencia(self, user_id: str, descricao: str):
        """Adiciona pendência ao contexto do usuário"""
        contexto = self.get_contexto(user_id)
        contexto.pendencias.append({
            'descricao': descricao,
            'criado_em': datetime.now().isoformat()
        })
        self._save_contextos()
    
    def remover_pendencia(self, user_id: str, indice: int):
        """Remove pendência do contexto"""
        contexto = self.get_contexto(user_id)
        if 0 <= indice < len(contexto.pendencias):
            contexto.pendencias.pop(indice)
            self._save_contextos()


# Singleton
_agente = None

def get_agente() -> AgenteProativo:
    """Retorna instância singleton do agente"""
    global _agente
    if _agente is None:
        _agente = AgenteProativo()
    return _agente
