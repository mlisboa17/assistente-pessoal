"""
🏢 Módulo de Condomínio/Grupos
Gerencia finanças de grupos (condomínio, empresas, etc.)
Monitora mensagens automaticamente e extrai valores
"""
import json
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class TransacaoGrupo:
    """Representa uma transação do grupo"""
    id: str
    tipo: str  # 'entrada' ou 'saida'
    valor: float
    descricao: str
    categoria: str = "outros"
    data: str = ""
    grupo_id: str = ""
    grupo_nome: str = ""
    registrado_por: str = ""
    registrado_por_nome: str = ""
    mensagem_original: str = ""
    criado_em: str = ""
    
    def to_dict(self):
        return asdict(self)


class CondominioModule:
    """Gerenciador de Finanças de Grupos/Condomínio"""
    
    # Palavras que indicam ENTRADA de dinheiro
    PALAVRAS_ENTRADA = [
        'recebemos', 'recebido', 'entrada', 'entrou', 'pagou', 'pagaram',
        'depositou', 'depositaram', 'transferiu', 'transferiram',
        'taxa', 'mensalidade', 'condomínio pago', 'cota', 'rateio',
        'apt', 'apartamento', 'morador', 'inquilino'
    ]
    
    # Palavras que indicam SAÍDA de dinheiro
    PALAVRAS_SAIDA = [
        'pagamos', 'pago', 'gastamos', 'despesa', 'conta', 'boleto',
        'manutenção', 'reparo', 'conserto', 'limpeza', 'porteiro',
        'luz', 'água', 'gás', 'energia', 'elevador', 'interfone',
        'jardinagem', 'pintura', 'obra', 'material', 'compra'
    ]
    
    # Categorias de despesas de condomínio
    CATEGORIAS = {
        'taxa_condominio': ['taxa', 'condomínio', 'mensalidade', 'cota', 'rateio'],
        'energia': ['luz', 'energia', 'eletricidade', 'cemig', 'enel', 'cpfl'],
        'agua': ['água', 'agua', 'saneamento', 'copasa', 'sabesp'],
        'gas': ['gás', 'gas'],
        'manutencao': ['manutenção', 'reparo', 'conserto', 'obra'],
        'limpeza': ['limpeza', 'faxina', 'higienização'],
        'seguranca': ['porteiro', 'portaria', 'vigilância', 'segurança', 'câmera'],
        'elevador': ['elevador'],
        'jardim': ['jardim', 'jardinagem', 'paisagismo', 'poda'],
        'funcionarios': ['funcionário', 'salário', 'folha', 'sindico', 'zelador'],
        'outros': []
    }
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.grupos_dir = os.path.join(data_dir, "grupos")
        
        os.makedirs(self.grupos_dir, exist_ok=True)
    
    def _get_grupo_file(self, grupo_id: str) -> str:
        """Retorna caminho do arquivo de um grupo"""
        # Limpa o ID do grupo para usar como nome de arquivo
        safe_id = re.sub(r'[^\w\-]', '_', grupo_id)
        return os.path.join(self.grupos_dir, f"{safe_id}.json")
    
    def _load_grupo_data(self, grupo_id: str) -> Dict:
        """Carrega dados de um grupo"""
        filepath = self._get_grupo_file(grupo_id)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "grupo_id": grupo_id,
            "grupo_nome": "",
            "transacoes": [],
            "configuracoes": {
                "ativo": True,
                "notificar_registros": True,
                "admins": []
            },
            "criado_em": datetime.now().isoformat()
        }
    
    def _save_grupo_data(self, grupo_id: str, data: Dict):
        """Salva dados de um grupo"""
        filepath = self._get_grupo_file(grupo_id)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _extrair_valor(self, texto: str) -> Optional[float]:
        """Extrai valor monetário do texto"""
        # Padrões: R$ 1.234,56 | R$1234.56 | 1234,56 | 1234.56
        padroes = [
            r'R\$\s*([\d.,]+)',
            r'(\d{1,3}(?:\.\d{3})*,\d{2})',  # 1.234,56
            r'(\d+,\d{2})',  # 1234,56
            r'(\d+\.\d{2})',  # 1234.56
            r'(\d+)\s*(?:reais|real)',
        ]
        
        for padrao in padroes:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                valor_str = match.group(1)
                # Normaliza formato
                valor_str = valor_str.replace('.', '').replace(',', '.')
                try:
                    return float(valor_str)
                except:
                    pass
        
        return None
    
    def _detectar_tipo(self, texto: str) -> Optional[str]:
        """Detecta se é entrada ou saída"""
        texto_lower = texto.lower()
        
        # Conta palavras de cada tipo
        score_entrada = sum(1 for p in self.PALAVRAS_ENTRADA if p in texto_lower)
        score_saida = sum(1 for p in self.PALAVRAS_SAIDA if p in texto_lower)
        
        if score_entrada > score_saida:
            return 'entrada'
        elif score_saida > score_entrada:
            return 'saida'
        
        return None
    
    def _detectar_categoria(self, texto: str) -> str:
        """Detecta categoria baseado no texto"""
        texto_lower = texto.lower()
        
        for categoria, palavras in self.CATEGORIAS.items():
            for palavra in palavras:
                if palavra in texto_lower:
                    return categoria
        
        return 'outros'
    
    def analisar_mensagem_grupo(self, mensagem: str, grupo_id: str, grupo_nome: str,
                                 user_id: str, user_name: str) -> Optional[Dict]:
        """
        Analisa uma mensagem do grupo e retorna transação se detectada
        
        Returns:
            Dict com transação ou None se não for relevante
        """
        # Extrai valor
        valor = self._extrair_valor(mensagem)
        if not valor or valor <= 0:
            return None
        
        # Detecta tipo (entrada/saída)
        tipo = self._detectar_tipo(mensagem)
        if not tipo:
            return None
        
        # Detecta categoria
        categoria = self._detectar_categoria(mensagem)
        
        # Cria transação
        from uuid import uuid4
        transacao = TransacaoGrupo(
            id=str(uuid4())[:8],
            tipo=tipo,
            valor=valor,
            descricao=mensagem[:200],  # Limita descrição
            categoria=categoria,
            data=datetime.now().strftime('%Y-%m-%d'),
            grupo_id=grupo_id,
            grupo_nome=grupo_nome,
            registrado_por=user_id,
            registrado_por_nome=user_name,
            mensagem_original=mensagem,
            criado_em=datetime.now().isoformat()
        )
        
        return transacao.to_dict()
    
    def registrar_transacao_grupo(self, transacao: Dict) -> str:
        """Registra transação de um grupo"""
        grupo_id = transacao.get('grupo_id')
        
        # Carrega dados do grupo
        grupo_data = self._load_grupo_data(grupo_id)
        
        # Atualiza nome do grupo se fornecido
        if transacao.get('grupo_nome'):
            grupo_data['grupo_nome'] = transacao['grupo_nome']
        
        # Adiciona transação
        grupo_data['transacoes'].append(transacao)
        
        # Salva
        self._save_grupo_data(grupo_id, grupo_data)
        
        # Formata resposta
        emoji = "💵" if transacao['tipo'] == 'entrada' else "💸"
        tipo_texto = "Entrada" if transacao['tipo'] == 'entrada' else "Despesa"
        
        return f"""
{emoji} *{tipo_texto} Registrada!*

💰 R$ {transacao['valor']:.2f}
🏷️ {transacao['categoria'].replace('_', ' ').capitalize()}
📝 {transacao['descricao'][:50]}...
👤 Por: {transacao['registrado_por_nome']}
📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}

_Registrado automaticamente_
"""
    
    def get_resumo_grupo(self, grupo_id: str, periodo: str = "mes") -> str:
        """Retorna resumo financeiro do grupo"""
        grupo_data = self._load_grupo_data(grupo_id)
        transacoes = grupo_data.get('transacoes', [])
        
        if not transacoes:
            return "📭 Nenhuma transação registrada neste grupo."
        
        # Filtra por período
        hoje = datetime.now()
        if periodo == "mes":
            data_inicio = hoje.replace(day=1).strftime('%Y-%m-%d')
            titulo = f"Resumo de {hoje.strftime('%B/%Y')}"
        elif periodo == "ano":
            data_inicio = hoje.replace(month=1, day=1).strftime('%Y-%m-%d')
            titulo = f"Resumo de {hoje.year}"
        else:
            data_inicio = "2000-01-01"
            titulo = "Resumo Geral"
        
        transacoes_periodo = [
            t for t in transacoes
            if t.get('data', '') >= data_inicio
        ]
        
        if not transacoes_periodo:
            return f"📭 Nenhuma transação em {titulo.lower()}."
        
        # Calcula totais
        entradas = sum(t['valor'] for t in transacoes_periodo if t['tipo'] == 'entrada')
        saidas = sum(t['valor'] for t in transacoes_periodo if t['tipo'] == 'saida')
        saldo = entradas - saidas
        
        # Agrupa despesas por categoria
        por_categoria = defaultdict(float)
        for t in transacoes_periodo:
            if t['tipo'] == 'saida':
                por_categoria[t.get('categoria', 'outros')] += t['valor']
        
        # Monta resposta
        emoji_saldo = "✅" if saldo >= 0 else "⚠️"
        grupo_nome = grupo_data.get('grupo_nome', 'Grupo')
        
        response = f"""
🏢 *{grupo_nome}*
📊 *{titulo}*

💵 *Entradas:* R$ {entradas:,.2f}
💸 *Saídas:* R$ {saidas:,.2f}
{emoji_saldo} *Saldo:* R$ {saldo:,.2f}

"""
        
        if por_categoria:
            response += "*Despesas por categoria:*\n"
            for cat, valor in sorted(por_categoria.items(), key=lambda x: -x[1]):
                cat_nome = cat.replace('_', ' ').capitalize()
                response += f"  • {cat_nome}: R$ {valor:,.2f}\n"
        
        response += f"\n📝 Total de registros: {len(transacoes_periodo)}"
        
        return response
    
    def get_ultimas_transacoes(self, grupo_id: str, limite: int = 10) -> str:
        """Lista últimas transações do grupo"""
        grupo_data = self._load_grupo_data(grupo_id)
        transacoes = grupo_data.get('transacoes', [])[-limite:]
        
        if not transacoes:
            return "📭 Nenhuma transação registrada."
        
        grupo_nome = grupo_data.get('grupo_nome', 'Grupo')
        response = f"🏢 *{grupo_nome}*\n📋 *Últimas Transações:*\n\n"
        
        for t in reversed(transacoes):
            emoji = "💵" if t['tipo'] == 'entrada' else "💸"
            response += f"{emoji} {t['data']} - R$ {t['valor']:.2f}\n"
            response += f"   _{t['descricao'][:40]}_\n"
        
        return response
    
    async def handle(self, command: str, args: List[str], 
                     user_id: str, attachments: list = None,
                     grupo_id: str = None) -> str:
        """Processa comandos do módulo"""
        
        if command in ['resumo', 'relatorio', 'caixa']:
            if grupo_id:
                return self.get_resumo_grupo(grupo_id)
            return "❌ Este comando só funciona em grupos."
        
        if command in ['transacoes', 'historico']:
            if grupo_id:
                return self.get_ultimas_transacoes(grupo_id)
            return "❌ Este comando só funciona em grupos."
        
        return "🏢 Comandos: resumo, transacoes"
    
    async def handle_natural(self, message: str, analysis: Any,
                              user_id: str, attachments: list = None,
                              grupo_id: str = None, grupo_nome: str = None,
                              user_name: str = None) -> Optional[str]:
        """
        Processa mensagem natural do grupo
        Retorna resposta se detectou transação, None se ignorar
        """
        if not grupo_id:
            return None
        
        # Analisa mensagem
        transacao = self.analisar_mensagem_grupo(
            message, grupo_id, grupo_nome or "Grupo",
            user_id, user_name or "Usuário"
        )
        
        if transacao:
            return self.registrar_transacao_grupo(transacao)
        
        return None
