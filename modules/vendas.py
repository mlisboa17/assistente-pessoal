"""
📊 Módulo de Vendas/LOGOS
Gerencia relatórios de vendas, estoque e integração com sistemas
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class Produto:
    """Representa um produto"""
    id: str
    nome: str
    codigo: str = ""
    preco: float = 0.0
    estoque: int = 0
    estoque_minimo: int = 5
    categoria: str = "geral"
    user_id: str = ""
    criado_em: str = ""
    
    def to_dict(self):
        return asdict(self)


@dataclass
class Venda:
    """Representa uma venda"""
    id: str
    produtos: List[Dict]  # [{produto_id, quantidade, preco_unitario}]
    valor_total: float
    cliente: str = ""
    data: str = ""
    forma_pagamento: str = "dinheiro"
    status: str = "concluida"  # concluida, pendente, cancelada
    user_id: str = ""
    criado_em: str = ""
    
    def to_dict(self):
        return asdict(self)


class VendasModule:
    """Gerenciador de Vendas e Estoque"""
    
    FORMAS_PAGAMENTO = ['dinheiro', 'pix', 'credito', 'debito', 'boleto', 'fiado']
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.produtos_file = os.path.join(data_dir, "produtos.json")
        self.vendas_file = os.path.join(data_dir, "vendas.json")
        
        os.makedirs(data_dir, exist_ok=True)
        self._load_data()
    
    def _load_data(self):
        """Carrega dados do disco"""
        # Produtos
        if os.path.exists(self.produtos_file):
            with open(self.produtos_file, 'r', encoding='utf-8') as f:
                self.produtos = json.load(f)
        else:
            self.produtos = []
        
        # Vendas
        if os.path.exists(self.vendas_file):
            with open(self.vendas_file, 'r', encoding='utf-8') as f:
                self.vendas = json.load(f)
        else:
            self.vendas = []
    
    def _save_data(self):
        """Salva dados no disco"""
        with open(self.produtos_file, 'w', encoding='utf-8') as f:
            json.dump(self.produtos, f, ensure_ascii=False, indent=2)
        
        with open(self.vendas_file, 'w', encoding='utf-8') as f:
            json.dump(self.vendas, f, ensure_ascii=False, indent=2)
    
    async def handle(self, command: str, args: List[str], 
                     user_id: str, attachments: list = None) -> str:
        """Processa comandos de vendas"""
        
        if command == 'vendas':
            if args:
                subcommand = args[0].lower()
                if subcommand == 'hoje':
                    return self._relatorio_hoje(user_id)
                elif subcommand == 'semana':
                    return self._relatorio_semana(user_id)
                elif subcommand == 'mes':
                    return self._relatorio_mes(user_id)
            return self._relatorio_hoje(user_id)
        
        elif command == 'venda':
            if args:
                return self._registrar_venda_rapida(user_id, ' '.join(args))
            return self._ajuda_venda()
        
        elif command == 'estoque':
            if args:
                return self._buscar_produto(user_id, ' '.join(args))
            return self._relatorio_estoque(user_id)
        
        elif command == 'produto':
            if args:
                return self._cadastrar_produto(user_id, ' '.join(args))
            return "📦 Use: /produto [nome] [preço] [estoque]"
        
        elif command == 'produtos':
            return self._listar_produtos(user_id)
        
        return "📊 Comandos: /vendas, /venda, /estoque, /produto, /produtos"
    
    async def handle_natural(self, message: str, analysis: Any,
                              user_id: str, attachments: list = None) -> str:
        """Processa linguagem natural"""
        text_lower = message.lower()
        
        if any(word in text_lower for word in ['estoque', 'tem', 'quantidade']):
            # Busca produto mencionado
            return self._relatorio_estoque(user_id)
        
        if any(word in text_lower for word in ['vendas hoje', 'vendi', 'vendemos']):
            return self._relatorio_hoje(user_id)
        
        if any(word in text_lower for word in ['relatório', 'relatorio', 'resumo']):
            return self._relatorio_mes(user_id)
        
        return self._relatorio_hoje(user_id)
    
    def _ajuda_venda(self) -> str:
        """Retorna ajuda sobre registro de vendas"""
        return """
📊 *Módulo de Vendas*

*Registrar venda:*
/venda [produto] [quantidade] [valor]
Exemplo: /venda Camiseta 2 79.90

*Relatórios:*
/vendas hoje - Vendas do dia
/vendas semana - Vendas da semana
/vendas mes - Vendas do mês

*Estoque:*
/estoque - Ver estoque geral
/estoque [produto] - Buscar produto
/produto [nome] [preço] [qtd] - Cadastrar

*Exemplos:*
• "vendi 3 camisetas por 150"
• "quanto tem de calça no estoque?"
• "relatório de vendas da semana"
"""
    
    def _registrar_venda_rapida(self, user_id: str, texto: str) -> str:
        """Registra uma venda rápida pelo texto"""
        import re
        from uuid import uuid4
        
        # Tenta extrair valor
        valor_match = re.search(r'(\d+[.,]?\d*)', texto)
        if not valor_match:
            return "❌ Não consegui identificar o valor. Use: /venda [produto] [qtd] [valor]"
        
        valor = float(valor_match.group(1).replace(',', '.'))
        
        # Cria venda
        venda = Venda(
            id=str(uuid4())[:8],
            produtos=[{"descricao": texto, "valor": valor}],
            valor_total=valor,
            data=datetime.now().strftime("%Y-%m-%d"),
            user_id=user_id,
            criado_em=datetime.now().isoformat()
        )
        
        self.vendas.append(venda.to_dict())
        self._save_data()
        
        # Calcula total do dia
        hoje = datetime.now().strftime("%Y-%m-%d")
        vendas_hoje = [v for v in self.vendas if v.get('data') == hoje]
        total_hoje = sum(v.get('valor_total', 0) for v in vendas_hoje)
        
        return f"""
✅ *Venda Registrada!*

💰 Valor: R$ {valor:,.2f}
📝 {texto}
📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}

📊 *Total do dia:* R$ {total_hoje:,.2f} ({len(vendas_hoje)} vendas)
"""
    
    def _relatorio_hoje(self, user_id: str) -> str:
        """Relatório de vendas do dia"""
        hoje = datetime.now().strftime("%Y-%m-%d")
        vendas_hoje = [v for v in self.vendas if v.get('data') == hoje]
        
        if not vendas_hoje:
            return f"""
📊 *Vendas de Hoje* ({datetime.now().strftime('%d/%m/%Y')})

Nenhuma venda registrada ainda.

💡 Use /venda [produto] [valor] para registrar
"""
        
        total = sum(v.get('valor_total', 0) for v in vendas_hoje)
        
        linhas = [f"📊 *Vendas de Hoje* ({datetime.now().strftime('%d/%m/%Y')})\n"]
        
        for i, v in enumerate(vendas_hoje[-10:], 1):  # Últimas 10
            desc = v.get('produtos', [{}])[0].get('descricao', 'Venda')[:30]
            valor = v.get('valor_total', 0)
            linhas.append(f"{i}. {desc} - R$ {valor:,.2f}")
        
        linhas.append(f"\n💰 *Total:* R$ {total:,.2f}")
        linhas.append(f"📈 *Quantidade:* {len(vendas_hoje)} vendas")
        
        return '\n'.join(linhas)
    
    def _relatorio_semana(self, user_id: str) -> str:
        """Relatório de vendas da semana"""
        hoje = datetime.now()
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        
        vendas_semana = []
        for v in self.vendas:
            try:
                data_venda = datetime.strptime(v.get('data', ''), "%Y-%m-%d")
                if data_venda >= inicio_semana:
                    vendas_semana.append(v)
            except:
                pass
        
        if not vendas_semana:
            return "📊 Nenhuma venda registrada esta semana."
        
        total = sum(v.get('valor_total', 0) for v in vendas_semana)
        
        # Agrupa por dia
        por_dia = defaultdict(float)
        for v in vendas_semana:
            por_dia[v.get('data', '')] += v.get('valor_total', 0)
        
        linhas = ["📊 *Vendas da Semana*\n"]
        
        dias_semana = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
        for data, valor in sorted(por_dia.items()):
            try:
                dt = datetime.strptime(data, "%Y-%m-%d")
                dia_nome = dias_semana[dt.weekday()]
                linhas.append(f"📅 {dia_nome} ({dt.strftime('%d/%m')}): R$ {valor:,.2f}")
            except:
                pass
        
        linhas.append(f"\n💰 *Total:* R$ {total:,.2f}")
        linhas.append(f"📈 *Quantidade:* {len(vendas_semana)} vendas")
        linhas.append(f"📊 *Média/dia:* R$ {total/7:,.2f}")
        
        return '\n'.join(linhas)
    
    def _relatorio_mes(self, user_id: str) -> str:
        """Relatório de vendas do mês"""
        hoje = datetime.now()
        mes_atual = hoje.strftime("%Y-%m")
        
        vendas_mes = [v for v in self.vendas if v.get('data', '').startswith(mes_atual)]
        
        if not vendas_mes:
            return f"📊 Nenhuma venda registrada em {hoje.strftime('%B/%Y')}."
        
        total = sum(v.get('valor_total', 0) for v in vendas_mes)
        dias_com_venda = len(set(v.get('data') for v in vendas_mes))
        
        return f"""
📊 *Relatório de {hoje.strftime('%B/%Y')}*

💰 *Total:* R$ {total:,.2f}
📈 *Vendas:* {len(vendas_mes)}
📅 *Dias ativos:* {dias_com_venda}
📊 *Média/venda:* R$ {total/len(vendas_mes):,.2f}
📊 *Média/dia:* R$ {total/max(dias_com_venda,1):,.2f}
"""
    
    def _relatorio_estoque(self, user_id: str) -> str:
        """Relatório geral de estoque"""
        if not self.produtos:
            return """
📦 *Estoque*

Nenhum produto cadastrado.

Use /produto [nome] [preço] [quantidade] para cadastrar.
Exemplo: /produto Camiseta 49.90 50
"""
        
        linhas = ["📦 *Estoque Atual*\n"]
        
        # Produtos com estoque baixo
        baixo_estoque = [p for p in self.produtos if p.get('estoque', 0) <= p.get('estoque_minimo', 5)]
        
        if baixo_estoque:
            linhas.append("⚠️ *ESTOQUE BAIXO:*")
            for p in baixo_estoque:
                linhas.append(f"  🔴 {p['nome']}: {p.get('estoque', 0)} unid.")
            linhas.append("")
        
        # Todos os produtos
        for p in self.produtos[:15]:  # Máximo 15
            qtd = p.get('estoque', 0)
            emoji = "🟢" if qtd > 10 else "🟡" if qtd > 5 else "🔴"
            linhas.append(f"{emoji} {p['nome']}: {qtd} unid. (R$ {p.get('preco', 0):,.2f})")
        
        if len(self.produtos) > 15:
            linhas.append(f"\n... e mais {len(self.produtos) - 15} produtos")
        
        return '\n'.join(linhas)
    
    def _listar_produtos(self, user_id: str) -> str:
        """Lista todos os produtos"""
        return self._relatorio_estoque(user_id)
    
    def _buscar_produto(self, user_id: str, termo: str) -> str:
        """Busca produto por nome"""
        termo_lower = termo.lower()
        encontrados = [p for p in self.produtos if termo_lower in p.get('nome', '').lower()]
        
        if not encontrados:
            return f"🔍 Nenhum produto encontrado para '{termo}'."
        
        linhas = [f"🔍 *Busca:* '{termo}'\n"]
        for p in encontrados:
            linhas.append(f"📦 *{p['nome']}*")
            linhas.append(f"   💰 Preço: R$ {p.get('preco', 0):,.2f}")
            linhas.append(f"   📊 Estoque: {p.get('estoque', 0)} unid.")
            linhas.append("")
        
        return '\n'.join(linhas)
    
    def _cadastrar_produto(self, user_id: str, texto: str) -> str:
        """Cadastra um novo produto"""
        import re
        from uuid import uuid4
        
        # Tenta extrair nome, preço e quantidade
        partes = texto.split()
        
        if len(partes) < 2:
            return "❌ Use: /produto [nome] [preço] [quantidade]"
        
        # Último número é quantidade, penúltimo é preço
        numeros = re.findall(r'(\d+[.,]?\d*)', texto)
        
        if len(numeros) < 1:
            return "❌ Informe pelo menos o preço do produto."
        
        preco = float(numeros[0].replace(',', '.'))
        estoque = int(float(numeros[1].replace(',', '.'))) if len(numeros) > 1 else 0
        
        # Nome é tudo antes dos números
        nome = re.sub(r'\d+[.,]?\d*', '', texto).strip()
        
        if not nome:
            nome = "Produto"
        
        produto = Produto(
            id=str(uuid4())[:8],
            nome=nome,
            preco=preco,
            estoque=estoque,
            user_id=user_id,
            criado_em=datetime.now().isoformat()
        )
        
        self.produtos.append(produto.to_dict())
        self._save_data()
        
        return f"""
✅ *Produto Cadastrado!*

📦 *{nome}*
💰 Preço: R$ {preco:,.2f}
📊 Estoque: {estoque} unid.
🆔 ID: {produto.id}
"""
    
    def atualizar_estoque(self, produto_id: str, quantidade: int, operacao: str = "subtrair") -> bool:
        """Atualiza estoque de um produto"""
        for p in self.produtos:
            if p.get('id') == produto_id:
                if operacao == "subtrair":
                    p['estoque'] = max(0, p.get('estoque', 0) - quantidade)
                else:
                    p['estoque'] = p.get('estoque', 0) + quantidade
                self._save_data()
                return True
        return False
    
    def verificar_estoque_baixo(self) -> List[Dict]:
        """Retorna produtos com estoque baixo"""
        return [p for p in self.produtos if p.get('estoque', 0) <= p.get('estoque_minimo', 5)]
