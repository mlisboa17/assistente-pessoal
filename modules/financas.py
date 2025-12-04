"""
💰 Módulo de Finanças
Gerencia gastos, despesas e relatórios financeiros
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class Transacao:
    """Representa uma transação financeira"""
    id: str
    tipo: str  # 'entrada' ou 'saida'
    valor: float
    descricao: str
    categoria: str = "outros"
    data: str = ""  # ISO format
    user_id: str = ""
    criado_em: str = ""
    
    def to_dict(self):
        return asdict(self)


class FinancasModule:
    """Gerenciador de Finanças"""
    
    CATEGORIAS = {
        'alimentacao': ['comida', 'restaurante', 'lanche', 'mercado', 'supermercado', 'ifood', 'uber eats'],
        'transporte': ['uber', '99', 'taxi', 'gasolina', 'combustível', 'estacionamento', 'ônibus', 'metrô'],
        'moradia': ['aluguel', 'condomínio', 'luz', 'água', 'gás', 'internet', 'iptu'],
        'saude': ['farmácia', 'remédio', 'médico', 'consulta', 'exame', 'plano de saúde'],
        'lazer': ['cinema', 'netflix', 'spotify', 'jogo', 'viagem', 'bar', 'festa'],
        'educacao': ['curso', 'livro', 'escola', 'faculdade', 'mensalidade'],
        'outros': []
    }
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.transacoes_file = os.path.join(data_dir, "transacoes.json")
        
        os.makedirs(data_dir, exist_ok=True)
        self._load_data()
    
    def _load_data(self):
        """Carrega dados do disco"""
        if os.path.exists(self.transacoes_file):
            with open(self.transacoes_file, 'r', encoding='utf-8') as f:
                self.transacoes = json.load(f)
        else:
            self.transacoes = []
    
    def _save_data(self):
        """Salva dados no disco"""
        with open(self.transacoes_file, 'w', encoding='utf-8') as f:
            json.dump(self.transacoes, f, ensure_ascii=False, indent=2)
    
    def _detectar_categoria(self, descricao: str) -> str:
        """Detecta categoria baseado na descrição"""
        descricao_lower = descricao.lower()
        
        for categoria, palavras in self.CATEGORIAS.items():
            for palavra in palavras:
                if palavra in descricao_lower:
                    return categoria
        
        return 'outros'
    
    async def handle(self, command: str, args: List[str], 
                     user_id: str, attachments: list = None) -> str:
        """Processa comandos de finanças"""
        
        if command == 'gastos':
            return self._resumo_gastos(user_id)
        
        elif command == 'despesas':
            if args:
                return self._registrar_despesa(user_id, args)
            return self._listar_despesas(user_id)
        
        elif command in ['saldo', 'financas']:
            return self._saldo_geral(user_id)
        
        elif command == 'entrada':
            if args:
                return self._registrar_entrada(user_id, args)
            return "💵 Use: /entrada [valor] [descrição]"
        
        return "💰 Comandos: /gastos, /despesas, /saldo"
    
    async def handle_natural(self, message: str, analysis: Any,
                              user_id: str, attachments: list = None) -> str:
        """Processa linguagem natural"""
        text_lower = message.lower()
        
        # Detecta valor
        valor = None
        if analysis and analysis.entities.get('money'):
            valor = analysis.entities['money'].get('value')
        
        # Detecta ação
        if any(word in text_lower for word in ['gastei', 'paguei', 'comprei', 'despesa']):
            if valor:
                return self._registrar_despesa(user_id, [str(valor), message])
            return "💸 Quanto você gastou? Informe o valor."
        
        if any(word in text_lower for word in ['recebi', 'ganhei', 'entrada', 'salário']):
            if valor:
                return self._registrar_entrada(user_id, [str(valor), message])
            return "💵 Quanto você recebeu? Informe o valor."
        
        if any(word in text_lower for word in ['gasto', 'quanto', 'despesas']):
            return self._resumo_gastos(user_id)
        
        return self._resumo_gastos(user_id)
    
    def _registrar_despesa(self, user_id: str, args: List[str]) -> str:
        """Registra uma despesa"""
        from uuid import uuid4
        
        if not args:
            return "❌ Informe o valor e descrição da despesa."
        
        # Primeiro argumento é o valor
        try:
            valor_str = args[0].replace('R$', '').replace(',', '.').strip()
            valor = float(valor_str)
        except:
            return "❌ Valor inválido. Use: /despesas 50.00 Almoço"
        
        # Resto é a descrição
        descricao = ' '.join(args[1:]) if len(args) > 1 else "Despesa"
        categoria = self._detectar_categoria(descricao)
        
        transacao = Transacao(
            id=str(uuid4())[:8],
            tipo='saida',
            valor=valor,
            descricao=descricao,
            categoria=categoria,
            data=datetime.now().strftime('%Y-%m-%d'),
            user_id=user_id,
            criado_em=datetime.now().isoformat()
        )
        
        self.transacoes.append(transacao.to_dict())
        self._save_data()
        
        return f"""
✅ *Despesa Registrada!*

💸 R$ {valor:.2f}
📝 {descricao}
🏷️ Categoria: {categoria.capitalize()}
📅 {datetime.now().strftime('%d/%m/%Y')}
"""
    
    def _registrar_entrada(self, user_id: str, args: List[str]) -> str:
        """Registra uma entrada"""
        from uuid import uuid4
        
        if not args:
            return "❌ Informe o valor e descrição."
        
        try:
            valor_str = args[0].replace('R$', '').replace(',', '.').strip()
            valor = float(valor_str)
        except:
            return "❌ Valor inválido."
        
        descricao = ' '.join(args[1:]) if len(args) > 1 else "Entrada"
        
        transacao = Transacao(
            id=str(uuid4())[:8],
            tipo='entrada',
            valor=valor,
            descricao=descricao,
            categoria='renda',
            data=datetime.now().strftime('%Y-%m-%d'),
            user_id=user_id,
            criado_em=datetime.now().isoformat()
        )
        
        self.transacoes.append(transacao.to_dict())
        self._save_data()
        
        return f"""
✅ *Entrada Registrada!*

💵 R$ {valor:.2f}
📝 {descricao}
📅 {datetime.now().strftime('%d/%m/%Y')}
"""
    
    def _resumo_gastos(self, user_id: str) -> str:
        """Retorna resumo de gastos do mês"""
        hoje = datetime.now()
        inicio_mes = hoje.replace(day=1).strftime('%Y-%m-%d')
        
        # Filtra transações do usuário no mês
        transacoes_mes = [
            t for t in self.transacoes
            if t.get('user_id') == user_id 
            and t.get('data', '') >= inicio_mes
            and t.get('tipo') == 'saida'
        ]
        
        if not transacoes_mes:
            return f"""
💰 *Resumo de Gastos* ({hoje.strftime('%B/%Y')})

📭 Nenhum gasto registrado este mês.

_Use /despesas [valor] [descrição] para registrar._
"""
        
        # Agrupa por categoria
        por_categoria = defaultdict(float)
        total = 0
        
        for t in transacoes_mes:
            categoria = t.get('categoria', 'outros')
            valor = t.get('valor', 0)
            por_categoria[categoria] += valor
            total += valor
        
        # Monta resposta
        response = f"💰 *Resumo de Gastos* ({hoje.strftime('%B/%Y')})\n\n"
        
        # Ordena por valor
        for categoria, valor in sorted(por_categoria.items(), key=lambda x: -x[1]):
            emoji = self._emoji_categoria(categoria)
            percent = (valor / total * 100) if total > 0 else 0
            response += f"{emoji} {categoria.capitalize()}: R$ {valor:.2f} ({percent:.0f}%)\n"
        
        response += f"\n💸 *Total: R$ {total:.2f}*"
        
        # Média diária
        dias = hoje.day
        media = total / dias if dias > 0 else 0
        response += f"\n📊 Média diária: R$ {media:.2f}"
        
        return response
    
    def _listar_despesas(self, user_id: str) -> str:
        """Lista últimas despesas"""
        despesas = [
            t for t in self.transacoes
            if t.get('user_id') == user_id and t.get('tipo') == 'saida'
        ][-10:]  # Últimas 10
        
        if not despesas:
            return "📭 Nenhuma despesa registrada."
        
        response = "💸 *Últimas Despesas:*\n\n"
        
        for d in reversed(despesas):
            data = d.get('data', '')
            valor = d.get('valor', 0)
            desc = d.get('descricao', '')[:30]
            response += f"• {data}: R$ {valor:.2f} - {desc}\n"
        
        return response
    
    def _saldo_geral(self, user_id: str) -> str:
        """Retorna saldo geral"""
        transacoes_user = [
            t for t in self.transacoes
            if t.get('user_id') == user_id
        ]
        
        entradas = sum(t.get('valor', 0) for t in transacoes_user if t.get('tipo') == 'entrada')
        saidas = sum(t.get('valor', 0) for t in transacoes_user if t.get('tipo') == 'saida')
        saldo = entradas - saidas
        
        emoji_saldo = "✅" if saldo >= 0 else "⚠️"
        
        return f"""
💰 *Resumo Financeiro*

💵 Entradas: R$ {entradas:.2f}
💸 Saídas: R$ {saidas:.2f}

{emoji_saldo} *Saldo: R$ {saldo:.2f}*
"""
    
    def _emoji_categoria(self, categoria: str) -> str:
        """Retorna emoji da categoria"""
        emojis = {
            'alimentacao': '🍔',
            'transporte': '🚗',
            'moradia': '🏠',
            'saude': '💊',
            'lazer': '🎮',
            'educacao': '📚',
            'renda': '💵',
            'outros': '📦'
        }
        return emojis.get(categoria, '📦')
