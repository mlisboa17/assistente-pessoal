"""
Interpretador de IA - Entende linguagem natural e converte em ações
Usa Google Gemini (gratuito) ou OpenAI GPT
Versão 2.0: Interpretador Inteligente com Processamento de Arquivos
"""

import os
import re
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any

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
        
        # Dicionários de sinonímia para melhor entendimento
        self.sinonimos = {
            'agenda': ['agenda', 'compromisso', 'evento', 'reunião', 'encontro', 'marcação', 'agendamento'],
            'tarefa': ['tarefa', 'afazer', 'to-do', 'tarefa', 'dever', 'responsabilidade', 'obrigação'],
            'lembrete': ['lembrete', 'aviso', 'alerta', 'notificação', 'alerta'],
            'financeiro': ['gasto', 'despesa', 'receita', 'gastos', 'finanças', 'dinheiro', 'custo'],
            'email': ['email', 'e-mail', 'mail', 'mensagem', 'correspondência']
        }
        
        # Variações de verbos para melhor detecção
        self.verbos_acao = {
            'adicionar': ['adicionar', 'criar', 'fazer', 'agendar', 'marcar', 'registrar', 'anotar'],
            'listar': ['listar', 'mostrar', 'exibir', 'ver', 'quais', 'quantas', 'qual'],
            'remover': ['remover', 'deletar', 'apagar', 'excluir', 'tirar', 'cancelar'],
            'buscar': ['buscar', 'procurar', 'pesquisar', 'encontrar', 'qual']
        }
        
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
    
    def interpretar(self, mensagem: str, contexto: dict = None, arquivo_dados: dict = None) -> dict:
        """
        Interpreta uma mensagem e retorna a intenção e parâmetros
        
        Args:
            mensagem: Texto a ser interpretado
            contexto: Contexto adicional (histórico, preferências)
            arquivo_dados: Dados do arquivo se houver (para processamento de docs)
        
        Returns:
            {
                'intencao': 'agenda|tarefa|lembrete|financeiro|email|conversa',
                'acao': 'adicionar|listar|remover|processar|...',
                'parametros': {...},
                'resposta_direta': 'resposta se for conversa casual',
                'confianca': 0.0-1.0
            }
        """
        mensagem_lower = mensagem.lower().strip()
        
        # Se houver arquivo, tenta processar com contexto do arquivo
        if arquivo_dados:
            return self._interpretar_com_arquivo(mensagem_lower, arquivo_dados, contexto)
        
        # Primeiro tenta interpretação local (mais rápida)
        resultado_local = self._interpretar_local(mensagem_lower)
        
        # Se encontrou intenção clara com confiança alta, retorna
        if resultado_local.get('intencao') != 'desconhecido' and resultado_local.get('confianca', 0) > 0.7:
            return resultado_local
        
        # Se tem IA disponível e confiança é baixa, usa para interpretar
        if self.model or self.provider == 'openai':
            resultado_ia = self._interpretar_ia(mensagem, contexto)
            # Combina resultados se local teve alguma pista
            if resultado_local.get('intencao') != 'desconhecido':
                resultado_ia['confianca'] = max(resultado_local.get('confianca', 0), resultado_ia.get('confianca', 0.5))
            return resultado_ia
        
        # Fallback: resposta genérica
        return {
            'intencao': 'conversa',
            'acao': 'responder',
            'parametros': {},
            'resposta_direta': self._resposta_generica(mensagem),
            'confianca': 0.3
        }
    
    def _interpretar_com_arquivo(self, msg: str, arquivo_dados: dict, contexto: dict = None) -> dict:
        """Interpreta mensagem com contexto de arquivo enviado"""
        tipo_arquivo = arquivo_dados.get('tipo', 'desconhecido')
        nome_arquivo = arquivo_dados.get('nome', 'arquivo')
        
        # Se o arquivo é PDF de boleto
        if 'boleto' in nome_arquivo.lower() or 'pdf' in tipo_arquivo.lower():
            # Verifica se há menção ao arquivo
            if any(p in msg for p in ['boleto', 'processá', 'processa', 'lê', 'le', 'arquivo', 'pdf', 'documento']):
                return {
                    'intencao': 'sistema',
                    'acao': 'processar_arquivo',
                    'parametros': {
                        'tipo': 'boleto',
                        'nome': nome_arquivo,
                        'comando_usuario': msg
                    },
                    'resposta_direta': f"📄 Processando {nome_arquivo}...",
                    'confianca': 0.95
                }
        
        # Se é imagem (comprovante)
        if 'image' in tipo_arquivo.lower() or 'jpg' in tipo_arquivo.lower():
            if any(p in msg for p in ['comprovante', 'comprava', 'pix', 'pagamento', 'recibo', 'processa', 'lê', 'le']):
                return {
                    'intencao': 'sistema',
                    'acao': 'processar_arquivo',
                    'parametros': {
                        'tipo': 'imagem',
                        'nome': nome_arquivo,
                        'comando_usuario': msg
                    },
                    'resposta_direta': f"🖼️ Analisando imagem {nome_arquivo}...",
                    'confianca': 0.95
                }
        
        # Se é áudio
        if 'audio' in tipo_arquivo.lower() or 'mp3' in tipo_arquivo.lower():
            if any(p in msg for p in ['áudio', 'audio', 'áudio', 'transcreve', 'processa', 'lê']):
                return {
                    'intencao': 'sistema',
                    'acao': 'processar_arquivo',
                    'parametros': {
                        'tipo': 'audio',
                        'nome': nome_arquivo,
                        'comando_usuario': msg
                    },
                    'resposta_direta': f"🎤 Transcrevendo áudio...",
                    'confianca': 0.95
                }
        
        # Fallback: processa arquivo de forma genérica
        if msg:
            return {
                'intencao': 'sistema',
                'acao': 'processar_arquivo',
                'parametros': {
                    'tipo': tipo_arquivo,
                    'nome': nome_arquivo,
                    'comando_usuario': msg
                },
                'resposta_direta': f"📎 Processando {nome_arquivo}...",
                'confianca': 0.85
            }
        
        return {
            'intencao': 'sistema',
            'acao': 'processar_arquivo',
            'parametros': {
                'tipo': tipo_arquivo,
                'nome': nome_arquivo,
                'comando_usuario': 'Arquivo enviado'
            },
            'resposta_direta': f"📎 Arquivo {nome_arquivo} recebido. Processando...",
            'confianca': 0.8
        }
    
    def _interpretar_local(self, msg: str) -> dict:
        """Interpretação local baseada em padrões com scoring de confiança"""
        
        confianca = 0.0
        
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
                'resposta_direta': f"{saudacao}! 👋 Como posso te ajudar hoje?\n\nPosso ajudar com:\n📅 Agenda e compromissos\n✅ Tarefas\n⏰ Lembretes\n💰 Finanças\n\nÉ só me dizer o que precisa!",
                'confianca': 0.99
            }
        
        # === BUSCAR E-MAILS ===
        if any(p in msg for p in ['buscar email', 'pesquisar email', 'procura email', 'de:', 'assunto:', 'remetente']):
            # Tenta extrair critérios de busca
            de_match = re.search(r'de:\s*(\w+)', msg)
            assunto_match = re.search(r'assunto:\s*([^,]+)', msg)
            
            parametros = {}
            if de_match:
                parametros['remetente'] = de_match.group(1)
            if assunto_match:
                parametros['assunto'] = assunto_match.group(1).strip()
            
            # Se não tem critérios específicos, extrai do contexto
            if not parametros:
                # Remove palavras-chave
                texto_busca = msg
                for p in ['buscar', 'pesquisar', 'procura', 'email', 'de', 'assunto']:
                    texto_busca = texto_busca.replace(p, '')
                texto_busca = texto_busca.strip()
                
                if texto_busca:
                    # Tenta identificar se é remetente ou assunto
                    if len(texto_busca.split()) <= 2:
                        parametros['remetente'] = texto_busca
                    else:
                        parametros['assunto'] = texto_busca
            
            if parametros:
                return {
                    'intencao': 'email',
                    'acao': 'buscar',
                    'parametros': parametros,
                    'resposta_direta': None,
                    'confianca': 0.85
                }
        
        # === AGENDA ===
        # "tenho reunião amanhã às 14h"
        if any(p in msg for p in ['reunião', 'reuniao', 'compromisso', 'evento', 'encontro', 'consulta', 'dentista', 'médico', 'medico']):
            resultado = self._extrair_evento(msg)
            resultado['confianca'] = 0.90
            return resultado
        
        # "o que tenho hoje", "minha agenda", "compromissos de amanhã"
        if any(p in msg for p in ['agenda', 'compromissos', 'o que tenho', 'que tenho', 'meus eventos', 'minha agenda']):
            data = self._extrair_data_referencia(msg)
            return {
                'intencao': 'agenda',
                'acao': 'listar',
                'parametros': {'data': data},
                'resposta_direta': None,
                'confianca': 0.88
            }
        
        # === TAREFAS ===
        # "preciso comprar leite", "tenho que fazer relatório"
        if any(p in msg for p in ['preciso', 'tenho que', 'não esquecer', 'nao esquecer', 'lembrar de', 'fazer', 'pra fazer']):
            tarefa = self._extrair_tarefa(msg)
            if tarefa:
                return {
                    'intencao': 'tarefa',
                    'acao': 'adicionar',
                    'parametros': {'descricao': tarefa},
                    'resposta_direta': None,
                    'confianca': 0.85
                }
        
        # "minhas tarefas", "lista de tarefas"
        if any(p in msg for p in ['tarefas', 'afazeres', 'to do', 'todo', 'pendências', 'pendencias', 'o que tenho pra fazer']):
            return {
                'intencao': 'tarefa',
                'acao': 'listar',
                'parametros': {},
                'resposta_direta': None,
                'confianca': 0.87
            }
        
        # === LEMBRETES ===
        # "me lembra em 30 minutos", "lembrete para amanhã"
        if any(p in msg for p in ['lembr', 'me avisa', 'me avise', 'alarme', 'alerta', 'não esqueça']):
            lembrete = self._extrair_lembrete(msg)
            if lembrete:
                return {
                    'intencao': 'lembrete',
                    'acao': 'criar',
                    'parametros': lembrete,
                    'resposta_direta': None,
                    'confianca': 0.86
                }
        
        # === FINANÇAS ===
        # "gastei 50 reais no almoço" OU formato direto: "mercado 150 alimentação"
        if any(p in msg for p in ['gastei', 'paguei', 'comprei', 'despesa', 'gasto', 'custa']):
            financa = self._extrair_despesa(msg)
            if financa:
                return {
                    'intencao': 'financeiro',
                    'acao': 'adicionar_despesa',
                    'parametros': financa,
                    'resposta_direta': None,
                    'confianca': 0.82
                }
        
        # 🆕 FORMATO DIRETO: "mercado 150 alimentação" (sem precisar 'gastei')
        # Detecta se tem valor + possível local/categoria
        financa_direta = self._extrair_despesa_formato_direto(msg)
        if financa_direta:
            return {
                'intencao': 'financeiro',
                'acao': 'adicionar_despesa',
                'parametros': financa_direta,
                'resposta_direta': None,
                'confianca': 0.78
            }
        
        # "recebi 1000", "entrou dinheiro"
        if any(p in msg for p in ['recebi', 'ganhei', 'entrou', 'receita', 'salário', 'salario', 'deposito', 'depósito']):
            financa = self._extrair_receita(msg)
            if financa:
                return {
                    'intencao': 'financeiro',
                    'acao': 'adicionar_receita',
                    'parametros': financa,
                    'resposta_direta': None,
                    'confianca': 0.83
                }
        
        # "quanto tenho", "meu saldo", "minhas finanças"
        if any(p in msg for p in ['saldo', 'finanças', 'financas', 'quanto tenho', 'dinheiro', 'balanço', 'balanco']):
            return {
                'intencao': 'financeiro',
                'acao': 'resumo',
                'parametros': {},
                'resposta_direta': None,
                'confianca': 0.84
            }
        
        # === AJUDA ===
        if any(p in msg for p in ['ajuda', 'help', 'comandos', 'o que você faz', 'o que voce faz', 'como funciona']):
            return {
                'intencao': 'sistema',
                'acao': 'ajuda',
                'parametros': {},
                'resposta_direta': self._texto_ajuda(),
                'confianca': 0.92
            }
        
        # === AGRADECIMENTOS ===
        if any(p in msg for p in ['obrigado', 'obrigada', 'valeu', 'thanks', 'vlw', 'brigado']):
            return {
                'intencao': 'conversa',
                'acao': 'agradecimento',
                'parametros': {},
                'resposta_direta': "De nada! 😊 Estou sempre aqui para ajudar!",
                'confianca': 0.96
            }
        
        return {
            'intencao': 'desconhecido',
            'acao': None,
            'parametros': {},
            'resposta_direta': None,
            'confianca': 0.0
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
            'resposta_direta': None,
            'confianca': 0.88
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
    
    def _extrair_despesa_formato_direto(self, msg: str) -> dict:
        """Extrai despesa em formato direto: 'mercado 150 alimentação'"""
        # Só processa se não tem verbos de gasto (evita duplicação)
        if any(p in msg for p in ['gastei', 'paguei', 'comprei', 'recebi', 'ganhei']):
            return None
        
        # Encontrar valor (mais flexível)
        valor_match = re.search(r'(\d+(?:[.,]\d{1,2})?)', msg)
        if not valor_match:
            return None
        
        valor = float(valor_match.group(1).replace(',', '.'))
        
        # Se valor muito pequeno (<5) pode ser ID ou número, não gasto
        if valor < 5:
            return None
        
        # Pegar texto antes e depois do valor
        partes = msg.split(valor_match.group(0))
        texto_antes = partes[0].strip().lower() if len(partes) > 0 else ""
        texto_depois = partes[1].strip().lower() if len(partes) > 1 else ""
        
        # Descrição: texto antes do valor (geralmente é o local)
        descricao = texto_antes if texto_antes else "Gasto"
        
        # Categoria: tentar detectar do texto completo ou depois do valor
        categoria = self._detectar_categoria_texto(msg)
        
        # Se não tem descrição clara, tentar pegar do depois do valor
        if not descricao or descricao == "gasto":
            if texto_depois:
                # Remove palavras de ligação
                descricao_depois = texto_depois
                for palavra in ['na', 'no', 'de', 'em', 'para', 'com']:
                    descricao_depois = descricao_depois.replace(palavra, '')
                descricao_depois = ' '.join(descricao_depois.split()).capitalize()
                if descricao_depois:
                    descricao = descricao_depois
        
        return {
            'valor': valor,
            'descricao': descricao.capitalize(),
            'categoria': categoria
        }
    
    def _extrair_despesa(self, msg: str) -> dict:
        """Extrai valor e categoria da despesa (formato com verbo)"""
        # Encontrar valor
        valor_match = re.search(r'(\d+(?:[.,]\d{2})?)\s*(?:reais|r\$|$)?', msg)
        if not valor_match:
            return None
        
        valor = float(valor_match.group(1).replace(',', '.'))
        
        # Descrição: pegar contexto
        descricao = msg.replace(valor_match.group(0), '').strip()
        for palavra in ['gastei', 'paguei', 'comprei', 'no', 'na', 'com', 'de', 'em', 'reais', 'r$']:
            descricao = descricao.replace(palavra, '')
        descricao = ' '.join(descricao.split()).capitalize()
        if not descricao:
            descricao = "Gasto"
        
        # Detectar categoria
        categoria = self._detectar_categoria_texto(msg)
        
        return {
            'valor': valor,
            'descricao': descricao,
            'categoria': categoria
        }
    
    def _detectar_categoria_texto(self, msg: str) -> str:
        """Detecta categoria baseada em palavras-chave no texto"""
        msg_lower = msg.lower()
        
        # Categoria baseada em palavras-chave
        categorias = {
            'alimentação': ['almoço', 'almoco', 'jantar', 'café', 'cafe', 'lanche', 'comida', 'restaurante', 'mercado', 'supermercado', 'alimentação', 'alimentacao', 'food'],
            'transporte': ['uber', 'taxi', 'ônibus', 'onibus', 'metrô', 'metro', 'gasolina', 'combustível', 'combustivel', 'estacionamento', 'transporte', '99'],
            'lazer': ['cinema', 'netflix', 'spotify', 'show', 'festa', 'bar', 'cerveja', 'lazer', 'diversão', 'diversao'],
            'saúde': ['farmácia', 'farmacia', 'remédio', 'remedio', 'médico', 'medico', 'consulta', 'saúde', 'saude', 'hospital'],
            'moradia': ['aluguel', 'luz', 'água', 'agua', 'internet', 'condomínio', 'condominio', 'moradia', 'casa'],
            'educação': ['curso', 'livro', 'escola', 'faculdade', 'educação', 'educacao'],
            'combustível': ['gasolina', 'combustível', 'combustivel', 'álcool', 'alcool', 'diesel', 'posto'],
            'vestuário': ['roupa', 'vestuário', 'vestuario', 'calça', 'calca', 'camisa', 'sapato'],
            'beleza': ['beleza', 'cabeleireiro', 'salão', 'salao', 'manicure', 'barbeiro'],
            'tecnologia': ['tecnologia', 'celular', 'computador', 'notebook', 'fone', 'carregador']
        }
        
        categoria = 'outros'
        for cat, palavras in categorias.items():
            if any(p in msg_lower for p in palavras):
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
        """Usa IA para interpretar mensagens complexas com melhor compreensão"""
        
        # Preparar contexto para a IA
        historico = ""
        if contexto:
            historico = f"\nContexto anterior:\n{json.dumps(contexto, indent=2, ensure_ascii=False)}"
        
        prompt = f"""Você é um assistente pessoal inteligente e altamente funcional. Sua tarefa é analisar a mensagem do usuário e extrair:

1. **Intenção principal** (escolha uma):
   - agenda (agendar, listar eventos, compromissos)
   - tarefa (adicionar, listar tarefas)
   - lembrete (criar lembretes com tempo específico)
   - financeiro (gastos, receitas, análise)
   - email (buscar, ler, enviar emails)
   - sistema (ajuda, status, processamento)
   - conversa (resposta natural)

2. **Ação desejada** (exemplos: adicionar, listar, remover, processar, responder, buscar)

3. **Parâmetros relevantes** (extrair informações específicas)

4. **Nível de confiança** (0.0 a 1.0)

5. **Resposta amigável** (se for conversa casual)

REGRAS IMPORTANTES:
- Interprete linguagem natural com flexibilidade
- Reconheça variações semânticas (ex: "me lembra" = lembrete, "tenho que" = tarefa)
- Extraia datas com inteligência (hoje, amanhã, próxima segunda, 15/12, etc)
- Reconheça valores monetários (com ou sem símbolos)
- Identifique categorias de gasto automaticamente
- Para buscas, extraia critérios (remetente, assunto, palavra-chave)
- Mantenha conversas naturais quando apropriado

Mensagem do usuário: "{mensagem}"{historico}

Responda em JSON no formato:
{{
    "intencao": "agenda|tarefa|lembrete|financeiro|email|sistema|conversa",
    "acao": "adicionar|listar|remover|processar|buscar|responder",
    "parametros": {{}},
    "confianca": 0.0-1.0,
    "resposta_direta": "resposta se for conversa casual",
    "notas": "observações sobre a interpretação"
}}"""
        
        try:
            if self.provider == 'gemini':
                response = self.model.generate_content(prompt)
                texto = response.text
            elif self.provider == 'openai':
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=800,
                    temperature=0.7
                )
                texto = response.choices[0].message.content
            else:
                # Sem IA, usa fallback
                return {
                    'intencao': 'conversa',
                    'acao': 'responder',
                    'parametros': {},
                    'confianca': 0.3,
                    'resposta_direta': self._resposta_generica(mensagem)
                }
            
            # Limpar o JSON se estiver embrulhado em markdown
            texto = texto.replace('```json', '').replace('```', '').strip()
            
            # Extrair JSON da resposta
            json_match = re.search(r'\{.*\}', texto, re.DOTALL)
            if json_match:
                resultado = json.loads(json_match.group())
                # Validar campos obrigatórios
                if 'intencao' in resultado and 'acao' in resultado:
                    resultado.setdefault('confianca', 0.7)
                    resultado.setdefault('parametros', {})
                    resultado.setdefault('resposta_direta', None)
                    return resultado
            
        except json.JSONDecodeError as e:
            print(f"⚠️ Erro ao parsear JSON da IA: {e}")
        except Exception as e:
            print(f"⚠️ Erro na IA (Gemini/OpenAI): {e}")
        
        # Fallback para resposta genérica
        return {
            'intencao': 'conversa',
            'acao': 'responder',
            'parametros': {},
            'confianca': 0.3,
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


def interpretar_mensagem(mensagem: str, contexto: dict = None, arquivo_dados: dict = None) -> dict:
    """
    Função helper para interpretar mensagem
    
    Args:
        mensagem: Mensagem do usuário
        contexto: Contexto adicional (histórico, preferências)
        arquivo_dados: Dados do arquivo se houver (tipo, nome, etc)
    
    Returns:
        Dicionário com intenção, ação, parâmetros e confiança
    """
    return ia.interpretar(mensagem, contexto, arquivo_dados)

