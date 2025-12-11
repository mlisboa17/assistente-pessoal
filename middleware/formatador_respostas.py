"""
💬 Formatador de Respostas Humanizadas
Transforma respostas técnicas/robotizadas em linguagem natural e amigável
"""
import re
from datetime import datetime
from typing import Dict, Any, List


class FormatadorRespostas:
    """
    Formata respostas para serem mais naturais e humanas
    Remove jargões técnicos e melhora a experiência do usuário
    """
    
    # Emojis por contexto
    EMOJIS = {
        'financeiro': '💰',
        'gasto': '💸',
        'receita': '💵',
        'tarefa': '✅',
        'agenda': '📅',
        'lembrete': '⏰',
        'sucesso': '✅',
        'erro': '❌',
        'aviso': '⚠️',
        'info': 'ℹ️',
        'pergunta': '❓',
        'dica': '💡',
        'celebracao': '🎉',
        'pensando': '🤔'
    }
    
    # Substituições para humanizar
    SUBSTITUICOES = {
        # Financeiro
        r'Gasto de R\$': 'Você gastou R$',
        r'Receita de R\$': 'Você recebeu R$',
        r'Valor: R\$': 'R$',
        r'Total depositado:': 'Total dos depósitos:',
        r'Número depósitos:': 'Quantidade:',
        r'caixa eletrônico SAA-MARIM DOS CABETES': 'caixa eletrônico',
        r'realizado no caixa eletrônico': 'no caixa eletrônico',
        r'depósitos realizados no': 'depósitos no',
        
        # Datas
        r'(\d{2})/(\d{2})/(\d{4})': lambda m: FormatadorRespostas._formatar_data(m),
        
        # Termos técnicos
        r'processamento concluído': 'pronto',
        r'operação executada': 'feito',
        r'registro inserido': 'registrado',
        r'dados armazenados': 'salvou',
        r'consulta realizada': 'verifiquei',
        
        # Confirmações robotizadas
        r'Confirmação recebida': 'Ok',
        r'Ação confirmada': 'Feito',
        r'Solicitação processada': 'Pronto',
    }
    
    @staticmethod
    def _formatar_data(match) -> str:
        """Formata data de DD/MM/YYYY para formato humanizado"""
        dia, mes, ano = match.groups()
        data = datetime.strptime(f'{dia}/{mes}/{ano}', '%d/%m/%Y')
        hoje = datetime.now()
        
        diff = (data.date() - hoje.date()).days
        
        if diff == 0:
            return 'hoje'
        elif diff == 1:
            return 'amanhã'
        elif diff == -1:
            return 'ontem'
        elif 1 < diff <= 7:
            dias_semana = ['segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo']
            return dias_semana[data.weekday()]
        else:
            meses = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 
                    'jul', 'ago', 'set', 'out', 'nov', 'dez']
            return f'{dia} de {meses[int(mes)-1]}'
    
    @staticmethod
    def humanizar(texto: str, contexto: str = None) -> str:
        """
        Humaniza um texto técnico/robotizado
        
        Args:
            texto: Texto a ser humanizado
            contexto: Contexto (financeiro, agenda, tarefa, etc)
        
        Returns:
            Texto humanizado
        """
        if not texto:
            return texto
        
        resultado = texto
        
        # Aplica substituições de padrões
        for padrao, substituicao in FormatadorRespostas.SUBSTITUICOES.items():
            if callable(substituicao):
                resultado = re.sub(padrao, substituicao, resultado)
            else:
                resultado = re.sub(padrao, substituicao, resultado, flags=re.IGNORECASE)
        
        # Remove excesso de emojis repetidos
        resultado = re.sub(r'([\U0001F300-\U0001F9FF])\1{2,}', r'\1', resultado)
        
        # Remove múltiplos espaços
        resultado = re.sub(r'\s{2,}', ' ', resultado)
        
        # Remove múltiplas quebras de linha
        resultado = re.sub(r'\n{3,}', '\n\n', resultado)
        
        # Capitaliza primeira letra de cada sentença
        resultado = FormatadorRespostas._capitalizar_sentencas(resultado)
        
        return resultado.strip()
    
    @staticmethod
    def _capitalizar_sentencas(texto: str) -> str:
        """Capitaliza primeira letra de cada sentença"""
        sentencas = re.split(r'([.!?]\s+)', texto)
        resultado = []
        
        for i, parte in enumerate(sentencas):
            if i % 2 == 0 and parte:  # É uma sentença, não um delimitador
                # Pula se começar com emoji ou número
                if parte[0].isalpha():
                    parte = parte[0].upper() + parte[1:]
            resultado.append(parte)
        
        return ''.join(resultado)
    
    @staticmethod
    def resumir_financeiro(dados: Dict[str, Any]) -> str:
        """
        Formata resumo financeiro de forma humanizada
        
        Args:
            dados: {
                'descricao': str,
                'valor': float,
                'tipo': 'deposito'|'saque'|'transferencia',
                'data': str,
                'quantidade': int (opcional)
            }
        
        Returns:
            Texto humanizado
        """
        valor = dados.get('valor', 0)
        tipo = dados.get('tipo', '').lower()
        descricao = dados.get('descricao', '')
        quantidade = dados.get('quantidade', 1)
        
        # Limpa descrição de jargões
        descricao_limpa = descricao
        descricao_limpa = re.sub(r'SAA-MARIM DOS CABETES.*', '', descricao_limpa, flags=re.IGNORECASE)
        descricao_limpa = re.sub(r'caixa eletrônico.*', 'caixa eletrônico', descricao_limpa, flags=re.IGNORECASE)
        descricao_limpa = re.sub(r'realizado(s)? no', 'no', descricao_limpa, flags=re.IGNORECASE)
        descricao_limpa = re.sub(r'\s{2,}', ' ', descricao_limpa).strip()
        
        # Monta resumo humanizado
        if tipo == 'deposito':
            if quantidade > 1:
                return f"💰 {quantidade} depósitos no caixa eletrônico\nTotal: R$ {valor:,.2f}"
            else:
                return f"💰 Depósito de R$ {valor:,.2f} no caixa eletrônico"
        
        elif tipo == 'saque':
            if quantidade > 1:
                return f"💸 {quantidade} saques\nTotal: R$ {valor:,.2f}"
            else:
                return f"💸 Saque de R$ {valor:,.2f}"
        
        elif tipo == 'transferencia':
            return f"💳 Transferência de R$ {valor:,.2f}"
        
        else:
            # Genérico
            if descricao_limpa:
                return f"💰 R$ {valor:,.2f} - {descricao_limpa}"
            else:
                return f"💰 R$ {valor:,.2f}"
    
    @staticmethod
    def formatar_lista_gastos(gastos: List[Dict], total: float = None) -> str:
        """
        Formata lista de gastos de forma humanizada
        
        Args:
            gastos: Lista de dicionários com gastos
            total: Total dos gastos (opcional)
        
        Returns:
            Texto formatado
        """
        if not gastos:
            return "Nenhum gasto registrado ainda 😊"
        
        linhas = ["💸 Seus gastos:\n"]
        
        for i, gasto in enumerate(gastos[:10], 1):  # Máximo 10
            valor = gasto.get('valor', 0)
            descricao = gasto.get('descricao', 'Sem descrição')
            categoria = gasto.get('categoria', '')
            
            # Emojis por categoria
            emoji_cat = {
                'alimentacao': '🍔',
                'transporte': '🚗',
                'saude': '💊',
                'lazer': '🎮',
                'moradia': '🏠',
                'outros': '📌'
            }.get(categoria.lower(), '•')
            
            linhas.append(f"{emoji_cat} R$ {valor:,.2f} - {descricao}")
        
        if len(gastos) > 10:
            linhas.append(f"\n... e mais {len(gastos) - 10} gastos")
        
        if total is not None:
            linhas.append(f"\n💰 Total: R$ {total:,.2f}")
        
        return '\n'.join(linhas)
    
    @staticmethod
    def formatar_pergunta_categoria() -> str:
        """Formata pergunta de categoria de forma amigável"""
        return """Em qual categoria fica esse gasto?

1️⃣ Alimentação (mercado, restaurante, etc)
2️⃣ Transporte (Uber, gasolina, ônibus)
3️⃣ Saúde (farmácia, médico, academia)
4️⃣ Lazer (cinema, jogos, diversão)
5️⃣ Moradia (aluguel, conta de luz, etc)
0️⃣ Outros

Digite o número da categoria:"""
    
    @staticmethod
    def formatar_confirmacao_gasto(valor: float, descricao: str, categoria: str) -> str:
        """Formata confirmação de gasto de forma humanizada"""
        emoji_cat = {
            'alimentacao': '🍔',
            'transporte': '🚗',
            'saude': '💊',
            'lazer': '🎮',
            'moradia': '🏠',
            'outros': '📌'
        }.get(categoria.lower(), '📌')
        
        return f"""Vou registrar:

{emoji_cat} R$ {valor:,.2f} - {descricao}
Categoria: {categoria.capitalize()}

Confirma?"""
    
    @staticmethod
    def formatar_sucesso(mensagem: str = None) -> str:
        """Formata mensagem de sucesso"""
        mensagens_default = [
            "Feito! ✅",
            "Pronto! 👍",
            "Salvou! ✅",
            "Ok, registrado! ✅",
            "Anotado! 📝"
        ]
        
        if mensagem:
            return FormatadorRespostas.humanizar(mensagem)
        
        import random
        return random.choice(mensagens_default)
    
    @staticmethod
    def formatar_erro(erro: str = None) -> str:
        """Formata mensagem de erro de forma amigável"""
        if not erro:
            return "Ops! Algo deu errado 😅"
        
        # Remove stack traces e detalhes técnicos
        erro_limpo = re.sub(r'Traceback.*', '', erro, flags=re.DOTALL)
        erro_limpo = re.sub(r'File ".*", line \d+.*', '', erro_limpo)
        erro_limpo = re.sub(r'^\s*at\s+.*', '', erro_limpo, flags=re.MULTILINE)
        
        return f"❌ {erro_limpo.strip()}"


# Função auxiliar para uso rápido
def humanizar(texto: str, contexto: str = None) -> str:
    """Atalho para humanizar texto"""
    return FormatadorRespostas.humanizar(texto, contexto)
