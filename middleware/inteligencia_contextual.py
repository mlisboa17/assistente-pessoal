"""
🧠 INTELIGÊNCIA CONTEXTUAL
Sistema que deduz intenções do usuário e confirma com Sim/Não/Alterar
"""
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
import json

class InteligenciaContextual:
    """
    Interpreta comandos vagos e deduz intenções
    Sempre confirma com o usuário antes de executar
    """
    
    def __init__(self):
        # Contextos de conversa ativa
        self.contextos_ativos = {}
        
        # Padrões de intenção
        self.padroes_intencao = {
            'emails': {
                'palavras': ['email', 'e-mail', 'inbox', 'mensagem', 'ler', 'verificar'],
                'acao': 'ler_emails',
                'perguntas': ['quantos', 'filtro']
            },
            'agenda': {
                'palavras': ['agendar', 'compromisso', 'reunião', 'médico', 'dentista', 'evento', 'marcar'],
                'acao': 'criar_evento',
                'perguntas': ['quando', 'hora']
            },
            'lembrete': {
                'palavras': ['lembrar', 'lembre', 'avise', 'alerta', 'notifique'],
                'acao': 'criar_lembrete',
                'perguntas': ['quando']
            },
            'gasto': {
                'palavras': ['gastei', 'paguei', 'comprei', 'despesa', 'gasto', 'valor', 'reais', 'r$'],
                'acao': 'registrar_gasto',
                'perguntas': ['valor', 'categoria']
            },
            'tarefa': {
                'palavras': ['tarefa', 'fazer', 'pendente', 'todo'],
                'acao': 'criar_tarefa',
                'perguntas': []
            }
        }
    
    def interpretar(self, mensagem: str, user_id: str) -> Dict:
        """
        Interpreta a mensagem e retorna ação + dados deduzidos
        """
        mensagem_lower = mensagem.lower()
        
        # Verifica se é resposta a contexto ativo
        if user_id in self.contextos_ativos:
            return self._processar_resposta_contexto(mensagem, user_id)
        
        # Detecta intenção
        intencao = self._detectar_intencao(mensagem_lower)
        
        if not intencao:
            return {'tipo': 'desconhecido', 'mensagem': mensagem}
        
        # Extrai dados da mensagem
        dados = self._extrair_dados(mensagem, intencao)
        
        # Gera confirmação inteligente
        return self._gerar_confirmacao(intencao, dados, mensagem, user_id)
    
    def _detectar_intencao(self, mensagem: str) -> Optional[str]:
        """Detecta a intenção do usuário"""
        # 🆕 PALAVRAS QUE INDICAM QUE NÃO É GASTO
        palavras_exclusao_gasto = [
            'sugestao', 'sugestoes', 'sugestão', 'sugestões',
            'listar', 'lista', 'extrato', 'gastos', 'despesas',
            'relatorio', 'relatório', 'ver', 'mostrar', 'exibir',
            'historico', 'histórico', 'mes', 'mês', 'resumo',
            'ajuda', 'help', 'menu', 'opcoes', 'opções',
            'status', 'saldo', 'total'
        ]
        
        # 🆕 DETECÇÃO INTELIGENTE: Se tem valor numérico + texto, pode ser gasto
        # Exemplo: "mercado 150" ou "uber 25 transporte"
        if re.search(r'\d+[.,]?\d*', mensagem):
            # Verifica se NÃO é palavra de exclusão
            tem_exclusao = any(palavra in mensagem for palavra in palavras_exclusao_gasto)
            if tem_exclusao:
                # Não é gasto, continua detecção normal
                pass
            else:
                # Tem número - pode ser gasto
                # Verifica se NÃO é outra intenção clara
                tem_outra_intencao = False
                for intencao, config in self.padroes_intencao.items():
                    if intencao != 'gasto':
                        if any(palavra in mensagem for palavra in config['palavras']):
                            tem_outra_intencao = True
                            break
                
                # Se não tem outra intenção clara, assume gasto
                if not tem_outra_intencao:
                    return 'gasto'
        
        # Detecção normal por palavras-chave
        for intencao, config in self.padroes_intencao.items():
            if any(palavra in mensagem for palavra in config['palavras']):
                return intencao
        return None
    
    def _extrair_dados(self, mensagem: str, intencao: str) -> Dict:
        """Extrai dados relevantes da mensagem"""
        dados = {}
        
        if intencao == 'emails':
            # Extrai quantidade
            match_qtd = re.search(r'(\d+)\s*(email|e-mail|mensagem)', mensagem, re.IGNORECASE)
            if match_qtd:
                dados['quantidade'] = int(match_qtd.group(1))
            
            # Extrai filtro/remetente
            match_de = re.search(r'de\s+([a-zA-Z0-9@.\s]+)', mensagem, re.IGNORECASE)
            if match_de:
                dados['filtro'] = match_de.group(1).strip()
        
        elif intencao == 'agenda':
            # Extrai descrição
            dados['descricao'] = self._limpar_descricao(mensagem)
            
            # Extrai data/hora
            data_hora = self._extrair_data_hora(mensagem)
            if data_hora:
                dados.update(data_hora)
        
        elif intencao == 'lembrete':
            # Extrai o que lembrar
            dados['descricao'] = self._limpar_descricao(mensagem)
            
            # Extrai quando
            data_hora = self._extrair_data_hora(mensagem)
            if data_hora:
                dados.update(data_hora)
        
        elif intencao == 'gasto':
            # Extrai valor
            match_valor = re.search(r'R?\$?\s*(\d+[.,]?\d*)', mensagem)
            if match_valor:
                valor_str = match_valor.group(1).replace(',', '.')
                dados['valor'] = float(valor_str)
            
            # Extrai descrição
            dados['descricao'] = self._limpar_descricao(mensagem)
            
            # Deduz categoria
            dados['categoria'] = self._deduzir_categoria(mensagem)
        
        elif intencao == 'tarefa':
            dados['descricao'] = self._limpar_descricao(mensagem)
        
        return dados
    
    def _extrair_data_hora(self, mensagem: str) -> Optional[Dict]:
        """Extrai data e hora da mensagem"""
        resultado = {}
        
        # Palavras-chave temporais
        agora = datetime.now()
        
        # "amanhã"
        if 'amanha' in mensagem.lower() or 'amanhã' in mensagem.lower():
            resultado['data'] = (agora + timedelta(days=1)).strftime('%d/%m/%Y')
        
        # "hoje"
        elif 'hoje' in mensagem.lower():
            resultado['data'] = agora.strftime('%d/%m/%Y')
        
        # "segunda", "terça", etc
        dias_semana = {
            'segunda': 0, 'terca': 1, 'terça': 1, 'quarta': 2,
            'quinta': 3, 'sexta': 4, 'sabado': 5, 'sábado': 5, 'domingo': 6
        }
        for dia_nome, dia_num in dias_semana.items():
            if dia_nome in mensagem.lower():
                dias_ate = (dia_num - agora.weekday()) % 7
                if dias_ate == 0:
                    dias_ate = 7  # Próxima semana
                data_futura = agora + timedelta(days=dias_ate)
                resultado['data'] = data_futura.strftime('%d/%m/%Y')
                break
        
        # Extrai hora
        match_hora = re.search(r'(\d{1,2}):?(\d{2})?\s*(h|hs|horas?)?', mensagem, re.IGNORECASE)
        if match_hora:
            hora = int(match_hora.group(1))
            minuto = int(match_hora.group(2)) if match_hora.group(2) else 0
            resultado['hora'] = f"{hora:02d}:{minuto:02d}"
        
        # Data específica dd/mm ou dd/mm/yyyy
        match_data = re.search(r'(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?', mensagem)
        if match_data:
            dia = int(match_data.group(1))
            mes = int(match_data.group(2))
            ano = int(match_data.group(3)) if match_data.group(3) else agora.year
            if ano < 100:
                ano += 2000
            resultado['data'] = f"{dia:02d}/{mes:02d}/{ano}"
        
        return resultado if resultado else None
    
    def _limpar_descricao(self, mensagem: str) -> str:
        """Remove palavras de comando e retorna descrição limpa"""
        # Remove palavras comuns de comando
        palavras_remover = [
            'lembrar', 'lembre', 'agendar', 'marcar', 'criar', 'adicionar',
            'registrar', 'anotar', 'de', 'que', 'eu', 'tenho', 'vou',
            'amanhã', 'amanha', 'hoje', 'às', 'as', 'para'
        ]
        
        palavras = mensagem.split()
        descricao = []
        
        for palavra in palavras:
            palavra_limpa = re.sub(r'[^\w\s]', '', palavra.lower())
            if palavra_limpa not in palavras_remover:
                descricao.append(palavra)
        
        return ' '.join(descricao).strip()
    
    def _deduzir_categoria(self, mensagem: str) -> str:
        """Deduz categoria de gasto baseado na descrição"""
        categorias = {
            'alimentacao': ['comida', 'restaurante', 'lanche', 'pizza', 'ifood', 'mercado', 'supermercado'],
            'transporte': ['uber', 'taxi', '99', 'gasolina', 'combustivel', 'onibus', 'metro'],
            'saude': ['farmacia', 'remedio', 'medico', 'consulta', 'exame'],
            'lazer': ['cinema', 'show', 'jogo', 'ingresso', 'diversao'],
            'educacao': ['curso', 'livro', 'escola', 'faculdade'],
            'moradia': ['aluguel', 'condominio', 'luz', 'agua', 'internet']
        }
        
        mensagem_lower = mensagem.lower()
        for categoria, palavras in categorias.items():
            if any(p in mensagem_lower for p in palavras):
                return categoria
        
        return 'outros'
    
    def _gerar_confirmacao(self, intencao: str, dados: Dict, mensagem_original: str, user_id: str) -> Dict:
        """Gera mensagem de confirmação com dados deduzidos"""
        
        if intencao == 'emails':
            # Se não tem quantidade, pergunta
            if 'quantidade' not in dados:
                self.contextos_ativos[user_id] = {
                    'intencao': 'emails',
                    'dados': dados,
                    'aguardando': 'quantidade'
                }
                return {
                    'tipo': 'pergunta',
                    'mensagem': '📧 Quantos e-mails você quer ver?',
                    'sugestoes': ['5', '10', '20', 'todos']
                }
            
            # Se tem quantidade, confirma
            filtro_txt = f" de {dados['filtro']}" if 'filtro' in dados else ""
            self.contextos_ativos[user_id] = {
                'intencao': 'emails',
                'dados': dados,
                'aguardando': 'confirmacao'
            }
            return {
                'tipo': 'confirmacao',
                'mensagem': f"📧 Vou buscar os últimos {dados.get('quantidade', 10)} e-mails{filtro_txt}.\n\nConfirma?",
                'dados': dados,
                'botoes': ['✅ Sim', '✏️ Alterar', '❌ Não']
            }
        
        elif intencao == 'agenda':
            # Verifica dados faltantes
            if 'data' not in dados or 'hora' not in dados:
                self.contextos_ativos[user_id] = {
                    'intencao': 'agenda',
                    'dados': dados,
                    'aguardando': 'data_hora'
                }
                return {
                    'tipo': 'pergunta',
                    'mensagem': f"📅 Quando será: {dados.get('descricao', 'este compromisso')}?",
                    'sugestoes': ['Hoje', 'Amanhã', 'Segunda-feira']
                }
            
            # Confirma com todos os dados
            self.contextos_ativos[user_id] = {
                'intencao': 'agenda',
                'dados': dados,
                'aguardando': 'confirmacao'
            }
            return {
                'tipo': 'confirmacao',
                'mensagem': f"📅 **Novo compromisso:**\n\n• {dados['descricao']}\n• {dados['data']} às {dados['hora']}\n\nConfirma?",
                'dados': dados,
                'botoes': ['✅ Sim', '✏️ Alterar', '❌ Não']
            }
        
        elif intencao == 'lembrete':
            if 'data' not in dados or 'hora' not in dados:
                self.contextos_ativos[user_id] = {
                    'intencao': 'lembrete',
                    'dados': dados,
                    'aguardando': 'data_hora'
                }
                return {
                    'tipo': 'pergunta',
                    'mensagem': f"⏰ Quando devo lembrar: {dados.get('descricao', 'isso')}?",
                    'sugestoes': ['Amanhã 8h', 'Hoje 18h', 'Segunda 9h']
                }
            
            self.contextos_ativos[user_id] = {
                'intencao': 'lembrete',
                'dados': dados,
                'aguardando': 'confirmacao'
            }
            return {
                'tipo': 'confirmacao',
                'mensagem': f"⏰ **Lembrete:**\n\n• {dados['descricao']}\n• {dados['data']} às {dados['hora']}\n\nConfirma?",
                'dados': dados,
                'botoes': ['✅ Sim', '✏️ Alterar', '❌ Não']
            }
        
        elif intencao == 'gasto':
            # 🆕 VERIFICAÇÃO INTELIGENTE DE DADOS FALTANTES
            
            # Se não tem valor, pede
            if 'valor' not in dados:
                self.contextos_ativos[user_id] = {
                    'intencao': 'gasto',
                    'dados': dados,
                    'aguardando': 'valor'
                }
                return {
                    'tipo': 'pergunta',
                    'mensagem': '💰 Qual foi o valor do gasto?'
                }
            
            # Se não tem descrição ou local, pede
            if not dados.get('descricao') or dados.get('descricao') == 'Despesa':
                self.contextos_ativos[user_id] = {
                    'intencao': 'gasto',
                    'dados': dados,
                    'aguardando': 'descricao'
                }
                return {
                    'tipo': 'pergunta',
                    'mensagem': f'💰 R$ {dados["valor"]:.2f} em qual local/estabelecimento?',
                    'sugestoes': ['Mercado', 'Restaurante', 'Farmácia', 'Uber']
                }
            
            # Se categoria é "outros", pergunta se quer especificar
            categoria_atual = dados.get('categoria', 'outros')
            emoji_cat = self._emoji_categoria(categoria_atual)
            
            if categoria_atual == 'outros':
                self.contextos_ativos[user_id] = {
                    'intencao': 'gasto',
                    'dados': dados,
                    'aguardando': 'categoria'
                }
                
                valor = dados["valor"]
                descricao = dados.get("descricao", "")
                
                mensagem = f"💰 R$ {valor:.2f}"
                if descricao:
                    mensagem += f" - {descricao}"
                
                mensagem += "\n\n❓ Em qual categoria?\n\n"
                mensagem += "1️⃣ Alimentação (mercado, restaurante...)\n"
                mensagem += "2️⃣ Transporte (Uber, gasolina...)\n"
                mensagem += "3️⃣ Saúde (farmácia, médico...)\n"
                mensagem += "4️⃣ Lazer (cinema, jogos...)\n"
                mensagem += "5️⃣ Moradia (aluguel, contas...)\n"
                mensagem += "0️⃣ Outros (deixar sem categoria)"
                
                return {
                    'tipo': 'pergunta',
                    'mensagem': mensagem,
                    'sugestoes': ['1', '2', '3', '4', '5', '0']
                }
            
            # Se tem tudo, confirma
            self.contextos_ativos[user_id] = {
                'intencao': 'gasto',
                'dados': dados,
                'aguardando': 'confirmacao'
            }
            return {
                'tipo': 'confirmacao',
                'mensagem': f"{emoji_cat} **Novo gasto:**\n\n• Valor: R$ {dados['valor']:.2f}\n• Local: {dados.get('descricao', 'Sem descrição')}\n• Categoria: {categoria_atual.capitalize()}\n\nTá ok?",
                'dados': dados,
                'botoes': ['✅ Sim', '✏️ Alterar', '❌ Não']
            }
        
        elif intencao == 'tarefa':
            self.contextos_ativos[user_id] = {
                'intencao': 'tarefa',
                'dados': dados,
                'aguardando': 'confirmacao'
            }
            return {
                'tipo': 'confirmacao',
                'mensagem': f"✅ Vou anotar:\n\n📝 {dados['descricao']}\n\nConfirma?",
                'dados': dados,
                'botoes': ['✅ Sim', '✏️ Alterar', '❌ Não']
            }
        
        return {'tipo': 'desconhecido'}
    
    def _processar_resposta_contexto(self, mensagem: str, user_id: str) -> Dict:
        """Processa resposta do usuário a um contexto ativo - ANÁLISE SEMÂNTICA FLEXÍVEL"""
        contexto = self.contextos_ativos[user_id]
        mensagem_lower = mensagem.lower().strip()
        
        # Remove pontuação e espaços extras
        mensagem_clean = re.sub(r'[,.!?;]+', '', mensagem_lower).strip()
        
        # ============================================
        # ANÁLISE SEMÂNTICA - Não depende de palavras exatas
        # ============================================
        
        # Detecta SENTIMENTO POSITIVO (SIM)
        # Qualquer coisa que pareça concordância ou confirmação
        sinais_positivos = 0
        sinais_negativos = 0
        sinais_alteracao = 0
        
        # Palavras/frases que indicam SIM (peso: +1 cada)
        indicadores_sim = [
            'sim', 'yes', 'ok', 'okay', 'beleza', 'blz', 's',
            'confirma', 'confirmar', 'confirmado', 'confirme', 'confirm',
            'tá', 'ta', 'pode', 'vai', 'isso', 'correto', 'exato', 
            'perfeito', 'certinho', 'certo', 'claro', 'certeza',
            'dale', 'faz', 'manda', 'bora', 'vamo', 'vamos',
            '✅', '👍', '👌', 'show', 'massa', 'top',
            'é', 'eh', 'uhum', 'uh', 'hum', 'afirma', 'positivo',
            'aceito', 'concordo', 'aceita', 'boa', 'isso ai',
            'segue', 'continua', 'vai fundo', 'manda ver',
            'quero', 'quero sim', 'quero isso'
        ]
        
        # Palavras/frases que indicam NÃO (peso: +1 cada)
        indicadores_nao = [
            'não', 'nao', 'no', 'nope', 'nop', 'nem', 'n',
            'cancela', 'cancel', 'aborta', 'para', 'pare', 'stop',
            'deixa', 'esquece', 'desiste', 'negativo',
            '❌', '🚫', '👎', 'nada', 'errado', 'incorreto',
            'volta', 'voltar', 'sai', 'sair', 'fecha',
            'não quero', 'nao quero', 'nem pensar',
            'não foi', 'nao foi', 'não é', 'nao e', 
            'não era', 'nao era', 'não era isso', 'nao era isso'
        ]
        
        # Palavras/frases que indicam ALTERAÇÃO (peso: +1 cada)
        indicadores_alterar = [
            'alterar', 'altera', 'mudar', 'muda', 'trocar', 'troca',
            'modificar', 'modifica', 'corrigir', 'corrige', 'editar', 'edita',
            '✏️', 'refazer', 'refaz', 'outro', 'outra', 'diferente',
            'errei', 'ops', 'enganei', 'errado', 'muda isso', 'troca isso'
        ]
        
        # Conta sinais positivos
        for palavra in indicadores_sim:
            if palavra in mensagem_lower or palavra == mensagem_clean:
                sinais_positivos += 1
        
        # Conta sinais negativos
        for palavra in indicadores_nao:
            if palavra in mensagem_lower or palavra == mensagem_clean:
                sinais_negativos += 1
        
        # 🆕 PRIORIDADE: Detecta cancelamento explícito (não foi, não é)
        cancelamento_explicito = any(frase in mensagem_lower for frase in [
            'não foi', 'nao foi', 'não é', 'nao e',
            'não era', 'nao era', 'não quero', 'nao quero',
            'não era isso', 'nao era isso', 'engano'
        ])
        
        # Conta sinais de alteração (APENAS se está aguardando confirmação)
        aguardando = contexto.get('aguardando', '')
        if aguardando == 'confirmacao':
            for palavra in indicadores_alterar:
                if palavra in mensagem_lower:
                    sinais_alteracao += 1
        
        # ============================================
        # DECISÃO BASEADA EM ANÁLISE SEMÂNTICA
        # ============================================
        
        # 🔴 PRIORIDADE MÁXIMA: Cancelamento explícito
        if cancelamento_explicito:
            del self.contextos_ativos[user_id]
            return {
                'tipo': 'cancelado',
                'mensagem': '❌ Ok, cancelado! Não era isso mesmo.'
            }
        
        # Se tem sinais claros de alteração E está em confirmação
        if sinais_alteracao > 0 and aguardando == 'confirmacao':
            return {
                'tipo': 'alterar',
                'mensagem': '✏️ O que você quer mudar? Digite o novo valor.',
                'contexto': contexto
            }
        
        # Se tem mais sinais positivos que negativos → EXECUTA
        if sinais_positivos > sinais_negativos:
            dados_finais = contexto['dados']
            intencao = contexto['intencao']
            del self.contextos_ativos[user_id]
            
            return {
                'tipo': 'executar',
                'acao': intencao,
                'dados': dados_finais
            }
        
        # Se tem mais sinais negativos → CANCELA
        if sinais_negativos > sinais_positivos:
            del self.contextos_ativos[user_id]
            return {
                'tipo': 'cancelado',
                'mensagem': '❌ Ok, cancelado!'
            }
        
        # ============================================
        # ANÁLISE HEURÍSTICA (quando não há sinais claros)
        # ============================================
        
        # Se mensagem é muito curta (1-2 caracteres)
        if len(mensagem_clean) <= 2:
            # Provavelmente é uma confirmação rápida
            if mensagem_clean in ['s', 'y', 'k', '1', 'v']:
                dados_finais = contexto['dados']
                intencao = contexto['intencao']
                del self.contextos_ativos[user_id]
                return {
                    'tipo': 'executar',
                    'acao': intencao,
                    'dados': dados_finais
                }
            # Provavelmente é negação
            elif mensagem_clean in ['n', 'x', '0']:
                del self.contextos_ativos[user_id]
                return {
                    'tipo': 'cancelado',
                    'mensagem': '❌ Ok, cancelado!'
                }
        
        # Se não foi confirmação/negação/alteração, processa como dados complementares
        return self._processar_resposta_dados(mensagem, user_id, contexto)
    
    def _emoji_categoria(self, categoria: str) -> str:
        """Retorna emoji para cada categoria"""
        emojis = {
            'alimentacao': '🍽️',
            'alimentação': '🍽️',
            'transporte': '🚗',
            'combustivel': '⛽',
            'combustível': '⛽',
            'saude': '🏥',
            'saúde': '🏥',
            'lazer': '🎉',
            'educacao': '📚',
            'educação': '📚',
            'moradia': '🏠',
            'vestuario': '👕',
            'vestuário': '👕',
            'beleza': '💅',
            'tecnologia': '💻',
            'outros': '💰'
        }
        return emojis.get(categoria.lower(), '💰')
    
    def _processar_resposta_dados(self, mensagem: str, user_id: str, contexto: Dict) -> Dict:
        """Processa resposta com dados complementares"""
        mensagem_lower = mensagem.lower()
        aguardando = contexto.get('aguardando')
        
        # Se está aguardando CONFIRMAÇÃO mas chegou aqui, não entendeu
        if aguardando == 'confirmacao':
            return {
                'tipo': 'nao_entendido',
                'mensagem': '❓ Não entendi. Responda:\n\n✅ *Sim* / *Ok* / *Blz*\n✏️ *Alterar*\n❌ *Não* / *Cancela*'
            }
        
        # Processa respostas de dados (não confirmação)
        if aguardando == 'quantidade':
            # Extrai número
            match = re.search(r'\d+', mensagem)
            if match:
                contexto['dados']['quantidade'] = int(match.group())
            elif 'todos' in mensagem_lower:
                contexto['dados']['quantidade'] = 999
            
            return self._gerar_confirmacao(contexto['intencao'], contexto['dados'], mensagem, user_id)
        
        elif aguardando == 'data_hora':
            # Extrai data/hora da resposta
            data_hora = self._extrair_data_hora(mensagem)
            if data_hora:
                contexto['dados'].update(data_hora)
            
            return self._gerar_confirmacao(contexto['intencao'], contexto['dados'], mensagem, user_id)
        
        elif aguardando == 'valor':
            match = re.search(r'(\d+[.,]?\d*)', mensagem)
            if match:
                valor_str = match.group(1).replace(',', '.')
                contexto['dados']['valor'] = float(valor_str)
            
            return self._gerar_confirmacao(contexto['intencao'], contexto['dados'], mensagem, user_id)
        
        elif aguardando == 'descricao':
            # Usuário informou o local/descrição
            contexto['dados']['descricao'] = mensagem.strip().capitalize()
            # Tenta detectar categoria da nova descrição
            categoria = self._deduzir_categoria(mensagem)
            if categoria != 'outros':
                contexto['dados']['categoria'] = categoria
            
            return self._gerar_confirmacao(contexto['intencao'], contexto['dados'], mensagem, user_id)
        
        elif aguardando == 'categoria':
            # Mapeamento de números para categorias
            mapa_categorias = {
                '1': 'alimentação',
                '2': 'transporte',
                '3': 'saúde',
                '4': 'lazer',
                '5': 'moradia',
                '0': 'outros'
            }
            
            # Verifica se é número
            if mensagem.strip() in mapa_categorias:
                contexto['dados']['categoria'] = mapa_categorias[mensagem.strip()]
            else:
                # Tenta detectar por nome
                categoria = self._deduzir_categoria(mensagem)
                contexto['dados']['categoria'] = categoria
            
            return self._gerar_confirmacao(contexto['intencao'], contexto['dados'], mensagem, user_id)
        
        return {'tipo': 'nao_entendido'}


# Instância global
_inteligencia = None

def get_inteligencia() -> InteligenciaContextual:
    """Retorna instância singleton"""
    global _inteligencia
    if _inteligencia is None:
        _inteligencia = InteligenciaContextual()
    return _inteligencia
