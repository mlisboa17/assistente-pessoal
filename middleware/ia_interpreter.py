"""
Interpretador de IA - Entende linguagem natural e converte em ações
Usa Google Gemini (gratuito) ou OpenAI GPT
"""

import os
import re
import json
from datetime import datetime, timedelta

# Tentar importar Google Generative AI (Gemini - gratuito)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Tentar importar OpenAI
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class IAInterpreter:
    """Interpreta mensagens em linguagem natural e extrai intenções"""
    
    def __init__(self):
        self.gemini_key = os.getenv('GEMINI_API_KEY')
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.model = None
        
        # Configurar Gemini (gratuito)
        if GEMINI_AVAILABLE and self.gemini_key:
            genai.configure(api_key=self.gemini_key)
            self.model = genai.GenerativeModel('gemini-pro')
            self.provider = 'gemini'
            print("✅ IA: Usando Google Gemini")
        # Configurar OpenAI
        elif OPENAI_AVAILABLE and self.openai_key:
            openai.api_key = self.openai_key
            self.provider = 'openai'
            print("✅ IA: Usando OpenAI GPT")
        else:
            self.provider = 'local'
            print("⚠️ IA: Usando interpretador local (sem API key)")
    
    def interpretar(self, mensagem: str, contexto: dict = None) -> dict:
        """
        Interpreta uma mensagem e retorna a intenção e parâmetros
        
        Returns:
            {
                'intencao': 'agenda|tarefa|lembrete|financeiro|email|conversa',
                'acao': 'adicionar|listar|remover|ver|...',
                'parametros': {...},
                'resposta_direta': 'resposta se for conversa casual'
            }
        """
        mensagem_lower = mensagem.lower().strip()
        
        # Primeiro tenta interpretação local (mais rápida)
        resultado_local = self._interpretar_local(mensagem_lower)
        
        # Se encontrou intenção clara, retorna
        if resultado_local['intencao'] != 'desconhecido':
            return resultado_local
        
        # Se tem IA disponível, usa para interpretar
        if self.model or self.provider == 'openai':
            return self._interpretar_ia(mensagem, contexto)
        
        # Fallback: resposta genérica
        return {
            'intencao': 'conversa',
            'acao': 'responder',
            'parametros': {},
            'resposta_direta': self._resposta_generica(mensagem)
        }
    
    def _interpretar_local(self, msg: str) -> dict:
        """Interpretação local baseada em padrões"""
        
        # === SAUDAÇÕES ===
        saudacoes = ['oi', 'olá', 'ola', 'hey', 'eai', 'e ai', 'bom dia', 'boa tarde', 'boa noite', 'hello', 'hi']
        if any(msg.startswith(s) or msg == s for s in saudacoes):
            hora = datetime.now().hour
            if hora < 12:
                saudacao = "Bom dia"
            elif hora < 18:
                saudacao = "Boa tarde"
            else:
                saudacao = "Boa noite"
            return {
                'intencao': 'conversa',
                'acao': 'saudacao',
                'parametros': {},
                'resposta_direta': f"{saudacao}! 👋 Como posso te ajudar hoje?\n\nPosso ajudar com:\n📅 Agenda e compromissos\n✅ Tarefas\n⏰ Lembretes\n💰 Finanças\n\nÉ só me dizer o que precisa!"
            }
        
        # === AGENDA ===
        # "tenho reunião amanhã às 14h"
        if any(p in msg for p in ['reunião', 'reuniao', 'compromisso', 'evento', 'encontro', 'consulta', 'dentista', 'médico', 'medico']):
            return self._extrair_evento(msg)
        
        # "o que tenho hoje", "minha agenda", "compromissos de amanhã"
        if any(p in msg for p in ['agenda', 'compromissos', 'o que tenho', 'que tenho', 'meus eventos']):
            data = self._extrair_data_referencia(msg)
            return {
                'intencao': 'agenda',
                'acao': 'listar',
                'parametros': {'data': data},
                'resposta_direta': None
            }
        
        # === TAREFAS ===
        # "preciso comprar leite", "tenho que fazer relatório"
        if any(p in msg for p in ['preciso', 'tenho que', 'não esquecer', 'nao esquecer', 'lembrar de', 'fazer']):
            tarefa = self._extrair_tarefa(msg)
            if tarefa:
                return {
                    'intencao': 'tarefa',
                    'acao': 'adicionar',
                    'parametros': {'descricao': tarefa},
                    'resposta_direta': None
                }
        
        # "minhas tarefas", "lista de tarefas"
        if any(p in msg for p in ['tarefas', 'afazeres', 'to do', 'todo', 'pendências', 'pendencias']):
            return {
                'intencao': 'tarefa',
                'acao': 'listar',
                'parametros': {},
                'resposta_direta': None
            }
        
        # === LEMBRETES ===
        # "me lembra em 30 minutos", "lembrete para amanhã"
        if any(p in msg for p in ['lembr', 'me avisa', 'me avise', 'alarme', 'alerta']):
            lembrete = self._extrair_lembrete(msg)
            if lembrete:
                return {
                    'intencao': 'lembrete',
                    'acao': 'criar',
                    'parametros': lembrete,
                    'resposta_direta': None
                }
        
        # === FINANÇAS ===
        # "gastei 50 reais no almoço"
        if any(p in msg for p in ['gastei', 'paguei', 'comprei', 'despesa', 'gasto']):
            financa = self._extrair_despesa(msg)
            if financa:
                return {
                    'intencao': 'financeiro',
                    'acao': 'adicionar_despesa',
                    'parametros': financa,
                    'resposta_direta': None
                }
        
        # "recebi 1000", "entrou dinheiro"
        if any(p in msg for p in ['recebi', 'ganhei', 'entrou', 'receita', 'salário', 'salario']):
            financa = self._extrair_receita(msg)
            if financa:
                return {
                    'intencao': 'financeiro',
                    'acao': 'adicionar_receita',
                    'parametros': financa,
                    'resposta_direta': None
                }
        
        # "quanto tenho", "meu saldo", "minhas finanças"
        if any(p in msg for p in ['saldo', 'finanças', 'financas', 'quanto tenho', 'dinheiro', 'balanço', 'balanco']):
            return {
                'intencao': 'financeiro',
                'acao': 'resumo',
                'parametros': {},
                'resposta_direta': None
            }
        
        # === AJUDA ===
        if any(p in msg for p in ['ajuda', 'help', 'comandos', 'o que você faz', 'o que voce faz', 'como funciona']):
            return {
                'intencao': 'sistema',
                'acao': 'ajuda',
                'parametros': {},
                'resposta_direta': self._texto_ajuda()
            }
        
        # === AGRADECIMENTOS ===
        if any(p in msg for p in ['obrigado', 'obrigada', 'valeu', 'thanks', 'vlw']):
            return {
                'intencao': 'conversa',
                'acao': 'agradecimento',
                'parametros': {},
                'resposta_direta': "De nada! 😊 Estou sempre aqui para ajudar!"
            }
        
        return {
            'intencao': 'desconhecido',
            'acao': None,
            'parametros': {},
            'resposta_direta': None
        }
    
    def _extrair_evento(self, msg: str) -> dict:
        """Extrai informações de um evento da mensagem"""
        # Encontrar horário (14h, 14:00, 2pm)
        horario = None
        hora_match = re.search(r'(\d{1,2})[h:](\d{2})?', msg)
        if hora_match:
            hora = int(hora_match.group(1))
            minuto = int(hora_match.group(2)) if hora_match.group(2) else 0
            horario = f"{hora:02d}:{minuto:02d}"
        
        # Encontrar data
        data = self._extrair_data_referencia(msg)
        
        # Descrição do evento (remover palavras de contexto)
        descricao = msg
        for palavra in ['tenho', 'vou ter', 'marquei', 'agendei', 'às', 'as', 'amanhã', 'amanha', 'hoje', 'segunda', 'terça', 'terca', 'quarta', 'quinta', 'sexta', 'sábado', 'sabado', 'domingo']:
            descricao = descricao.replace(palavra, '')
        descricao = re.sub(r'\d{1,2}[h:]\d{0,2}', '', descricao).strip()
        descricao = ' '.join(descricao.split())  # Remover espaços extras
        
        if not descricao:
            descricao = "Compromisso"
        
        return {
            'intencao': 'agenda',
            'acao': 'adicionar',
            'parametros': {
                'data': data,
                'horario': horario,
                'descricao': descricao.capitalize()
            },
            'resposta_direta': None
        }
    
    def _extrair_data_referencia(self, msg: str) -> str:
        """Extrai data da mensagem (hoje, amanhã, dia específico)"""
        hoje = datetime.now()
        
        if 'hoje' in msg:
            return hoje.strftime('%Y-%m-%d')
        elif 'amanhã' in msg or 'amanha' in msg:
            return (hoje + timedelta(days=1)).strftime('%Y-%m-%d')
        elif 'depois de amanhã' in msg or 'depois de amanha' in msg:
            return (hoje + timedelta(days=2)).strftime('%Y-%m-%d')
        
        # Dias da semana
        dias_semana = {
            'segunda': 0, 'terça': 1, 'terca': 1, 'quarta': 2,
            'quinta': 3, 'sexta': 4, 'sábado': 5, 'sabado': 5, 'domingo': 6
        }
        for dia, num in dias_semana.items():
            if dia in msg:
                dias_ate = (num - hoje.weekday()) % 7
                if dias_ate == 0:
                    dias_ate = 7  # Próxima semana
                return (hoje + timedelta(days=dias_ate)).strftime('%Y-%m-%d')
        
        # Data específica (15/12, 15-12)
        data_match = re.search(r'(\d{1,2})[/-](\d{1,2})', msg)
        if data_match:
            dia = int(data_match.group(1))
            mes = int(data_match.group(2))
            ano = hoje.year
            if mes < hoje.month or (mes == hoje.month and dia < hoje.day):
                ano += 1
            return f"{ano}-{mes:02d}-{dia:02d}"
        
        return hoje.strftime('%Y-%m-%d')
    
    def _extrair_tarefa(self, msg: str) -> str:
        """Extrai descrição da tarefa"""
        # Remover palavras de contexto
        tarefa = msg
        for palavra in ['preciso', 'tenho que', 'não esquecer de', 'nao esquecer de', 'lembrar de', 'fazer', 'de']:
            tarefa = tarefa.replace(palavra, '')
        tarefa = tarefa.strip()
        return tarefa.capitalize() if tarefa else None
    
    def _extrair_lembrete(self, msg: str) -> dict:
        """Extrai informações do lembrete"""
        # Tempo relativo
        tempo_match = re.search(r'(\d+)\s*(min|hora|h)', msg)
        if tempo_match:
            valor = int(tempo_match.group(1))
            unidade = tempo_match.group(2)
            if 'min' in unidade:
                tempo = f"{valor}min"
            else:
                tempo = f"{valor}h"
        else:
            tempo = "30min"  # Padrão
        
        # Mensagem do lembrete
        mensagem = msg
        for palavra in ['me lembra', 'me lembre', 'lembrete', 'me avisa', 'me avise', 'em', 'daqui', 'para', 'de', 'que']:
            mensagem = mensagem.replace(palavra, '')
        mensagem = re.sub(r'\d+\s*(min|hora|h)', '', mensagem).strip()
        mensagem = ' '.join(mensagem.split())
        
        if not mensagem:
            mensagem = "Lembrete"
        
        return {
            'tempo': tempo,
            'mensagem': mensagem.capitalize()
        }
    
    def _extrair_despesa(self, msg: str) -> dict:
        """Extrai valor e categoria da despesa"""
        # Encontrar valor
        valor_match = re.search(r'(\d+(?:[.,]\d{2})?)\s*(?:reais|r\$|$)?', msg)
        if not valor_match:
            return None
        
        valor = float(valor_match.group(1).replace(',', '.'))
        
        # Categoria baseada em palavras-chave
        categorias = {
            'alimentação': ['almoço', 'almoco', 'jantar', 'café', 'cafe', 'lanche', 'comida', 'restaurante', 'mercado', 'supermercado'],
            'transporte': ['uber', 'taxi', 'ônibus', 'onibus', 'metrô', 'metro', 'gasolina', 'combustível', 'combustivel', 'estacionamento'],
            'lazer': ['cinema', 'netflix', 'spotify', 'show', 'festa', 'bar', 'cerveja'],
            'saúde': ['farmácia', 'farmacia', 'remédio', 'remedio', 'médico', 'medico', 'consulta'],
            'moradia': ['aluguel', 'luz', 'água', 'agua', 'internet', 'condomínio', 'condominio'],
            'educação': ['curso', 'livro', 'escola', 'faculdade']
        }
        
        categoria = 'outros'
        for cat, palavras in categorias.items():
            if any(p in msg for p in palavras):
                categoria = cat
                break
        
        # Descrição
        descricao = msg
        for palavra in ['gastei', 'paguei', 'comprei', 'reais', 'r$']:
            descricao = descricao.replace(palavra, '')
        descricao = re.sub(r'\d+(?:[.,]\d{2})?', '', descricao).strip()
        descricao = ' '.join(descricao.split())
        
        return {
            'valor': valor,
            'categoria': categoria,
            'descricao': descricao.capitalize() if descricao else categoria.capitalize()
        }
    
    def _extrair_receita(self, msg: str) -> dict:
        """Extrai valor e categoria da receita"""
        # Encontrar valor
        valor_match = re.search(r'(\d+(?:[.,]\d{2})?)\s*(?:reais|r\$|$)?', msg)
        if not valor_match:
            return None
        
        valor = float(valor_match.group(1).replace(',', '.'))
        
        # Categoria
        if 'salário' in msg or 'salario' in msg:
            categoria = 'salário'
        elif 'freelance' in msg or 'freela' in msg:
            categoria = 'freelance'
        elif 'extra' in msg:
            categoria = 'extra'
        else:
            categoria = 'outros'
        
        return {
            'valor': valor,
            'categoria': categoria,
            'descricao': categoria.capitalize()
        }
    
    def _interpretar_ia(self, mensagem: str, contexto: dict = None) -> dict:
        """Usa IA para interpretar mensagens complexas"""
        prompt = f"""Você é um assistente pessoal inteligente. Analise a mensagem do usuário e extraia:
1. A intenção principal (agenda, tarefa, lembrete, financeiro, conversa)
2. A ação desejada (adicionar, listar, remover, etc)
3. Os parâmetros relevantes
4. Uma resposta amigável se for conversa casual

Mensagem: "{mensagem}"

Responda em JSON no formato:
{{
    "intencao": "agenda|tarefa|lembrete|financeiro|conversa",
    "acao": "adicionar|listar|remover|responder",
    "parametros": {{}},
    "resposta_direta": "resposta se for conversa"
}}"""
        
        try:
            if self.provider == 'gemini':
                response = self.model.generate_content(prompt)
                texto = response.text
            elif self.provider == 'openai':
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500
                )
                texto = response.choices[0].message.content
            
            # Extrair JSON da resposta
            json_match = re.search(r'\{.*\}', texto, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            print(f"Erro na IA: {e}")
        
        return {
            'intencao': 'conversa',
            'acao': 'responder',
            'parametros': {},
            'resposta_direta': self._resposta_generica(mensagem)
        }
    
    def _resposta_generica(self, msg: str) -> str:
        """Gera resposta genérica quando não entende"""
        return f"""Desculpa, não entendi bem o que você quer fazer 🤔

Você pode tentar dizer algo como:
• "Tenho reunião amanhã às 14h"
• "Preciso comprar leite"
• "Me lembra em 30 minutos de ligar para o João"
• "Gastei 50 reais no almoço"
• "Qual minha agenda de hoje?"

Ou digite /ajuda para ver todos os comandos! 📋"""
    
    def _texto_ajuda(self) -> str:
        """Retorna texto de ajuda"""
        return """🤖 *Assistente Pessoal Inteligente*

Você pode falar comigo naturalmente! Exemplos:

📅 *Agenda:*
• "Tenho reunião amanhã às 14h"
• "Qual minha agenda de hoje?"
• "Compromissos da semana"

✅ *Tarefas:*
• "Preciso comprar leite"
• "Tenho que enviar o relatório"
• "Minhas tarefas pendentes"

⏰ *Lembretes:*
• "Me lembra em 30 minutos"
• "Lembrete para amanhã: pagar conta"

💰 *Finanças:*
• "Gastei 50 reais no almoço"
• "Recebi o salário de 3000"
• "Qual meu saldo?"

É só me dizer o que precisa! 😊"""


# Instância global
ia = IAInterpreter()


def interpretar_mensagem(mensagem: str, contexto: dict = None) -> dict:
    """Função helper para interpretar mensagem"""
    return ia.interpretar(mensagem, contexto)
