"""
🎯 Módulo de Metas Financeiras
Gerencia metas de economia, investimento e gastos
"""
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from uuid import uuid4


@dataclass
class Meta:
    """Representa uma meta financeira"""
    id: str
    titulo: str
    tipo: str  # economia, investimento, limite_gasto, quitacao
    valor_alvo: float
    valor_atual: float = 0.0
    prazo: str = ""  # Data limite ISO format
    descricao: str = ""
    categoria: str = ""  # Categoria relacionada (para limite de gastos)
    recorrente: bool = False  # Mensal, semanal, etc.
    periodicidade: str = ""  # mensal, semanal, anual
    concluida: bool = False
    user_id: str = ""
    criado_em: str = ""
    concluido_em: str = ""
    ultimo_alerta: float = 0.0  # Último percentual alertado
    historico: List[Dict] = None  # Histórico de contribuições
    
    def __post_init__(self):
        if self.historico is None:
            self.historico = []
    
    def to_dict(self):
        return asdict(self)


class MetasModule:
    """Gerenciador de Metas Financeiras"""
    
    TIPOS_META = {
        'economia': '💰 Economia',
        'investimento': '📈 Investimento',
        'limite_gasto': '🎯 Limite de Gasto',
        'quitacao': '💳 Quitação de Dívida',
        'emergencia': '🆘 Fundo de Emergência',
        'viagem': '✈️ Viagem',
        'compra': '🛒 Compra',
        'outro': '📌 Outro'
    }
    
    EMOJIS_PROGRESSO = ['🔴', '🟠', '🟡', '🟢', '🎉']
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.metas_file = os.path.join(data_dir, "metas.json")
        
        os.makedirs(data_dir, exist_ok=True)
        self._load_data()
        
        # Referência ao módulo de finanças (para limite de gastos)
        self.financas_module = None
    
    def set_financas_module(self, financas):
        """Define referência ao módulo de finanças"""
        self.financas_module = financas
    
    def _load_data(self):
        """Carrega dados do disco"""
        if os.path.exists(self.metas_file):
            with open(self.metas_file, 'r', encoding='utf-8') as f:
                self.metas = json.load(f)
        else:
            self.metas = []
    
    def _save_data(self):
        """Salva dados no disco"""
        with open(self.metas_file, 'w', encoding='utf-8') as f:
            json.dump(self.metas, f, ensure_ascii=False, indent=2)
    
    def _gerar_id(self) -> str:
        """Gera ID único para meta"""
        return f"m{len(self.metas) + 1}"
    
    def _barra_progresso(self, porcentagem: float) -> str:
        """Gera barra de progresso visual"""
        total = 10
        preenchido = int(porcentagem / 100 * total)
        preenchido = min(preenchido, total)
        vazio = total - preenchido
        
        # Emoji baseado no progresso
        if porcentagem >= 100:
            emoji = '🎉'
        elif porcentagem >= 75:
            emoji = '🟢'
        elif porcentagem >= 50:
            emoji = '🟡'
        elif porcentagem >= 25:
            emoji = '🟠'
        else:
            emoji = '🔴'
        
        return f"{emoji} [{'█' * preenchido}{'░' * vazio}] {porcentagem:.1f}%"
    
    def _calcular_progresso(self, meta: Dict) -> float:
        """Calcula o progresso de uma meta"""
        valor_alvo = meta.get('valor_alvo', 1)
        valor_atual = meta.get('valor_atual', 0)
        
        if valor_alvo <= 0:
            return 0
        
        return min((valor_atual / valor_alvo) * 100, 100)
    
    async def handle(self, command: str, args: List[str], 
                     user_id: str, attachments: list = None) -> str:
        """Processa comandos de metas"""
        
        if command == 'metas':
            return self._listar_metas(user_id)
        
        elif command == 'meta':
            if not args:
                return self._ajuda_metas()
            
            subcommand = args[0].lower()
            
            if subcommand == 'criar' or subcommand == 'nova':
                return self._criar_meta_interativo(user_id, args[1:])
            
            elif subcommand == 'depositar' or subcommand == 'add':
                return self._depositar_meta(user_id, args[1:])
            
            elif subcommand == 'retirar' or subcommand == 'sacar':
                return self._retirar_meta(user_id, args[1:])
            
            elif subcommand == 'ver' or subcommand == 'detalhes':
                return self._detalhes_meta(user_id, args[1:])
            
            elif subcommand == 'concluir':
                return self._concluir_meta(user_id, args[1:])
            
            elif subcommand == 'excluir' or subcommand == 'deletar':
                return self._excluir_meta(user_id, args[1:])
            
            else:
                # Assume que é criação rápida: /meta [titulo] [valor]
                return self._criar_meta_rapida(user_id, args)
        
        return self._ajuda_metas()
    
    async def handle_natural(self, message: str, analysis: Any,
                              user_id: str, attachments: list = None) -> str:
        """Processa linguagem natural sobre metas"""
        text_lower = message.lower()
        
        # Criar meta
        if any(word in text_lower for word in ['criar meta', 'nova meta', 'quero economizar', 'quero juntar']):
            return self._criar_meta_interativo(user_id, [])
        
        # Ver metas
        if any(word in text_lower for word in ['minhas metas', 'ver metas', 'metas']):
            return self._listar_metas(user_id)
        
        # Depositar
        if any(word in text_lower for word in ['depositar', 'guardar', 'poupar']):
            # Tenta extrair valor
            import re
            match = re.search(r'(\d+(?:[.,]\d{2})?)', message)
            if match:
                valor = match.group(1).replace(',', '.')
                return self._depositar_meta(user_id, [valor])
        
        return self._listar_metas(user_id)
    
    def _ajuda_metas(self) -> str:
        """Retorna ajuda sobre metas"""
        return """
🎯 *Metas Financeiras*

*Comandos:*
• `/meta criar` - Criar nova meta (interativo)
• `/meta [título] [valor]` - Criar meta rápida
• `/metas` - Ver todas as metas
• `/meta depositar [id] [valor]` - Depositar na meta
• `/meta retirar [id] [valor]` - Retirar da meta
• `/meta ver [id]` - Ver detalhes
• `/meta concluir [id]` - Marcar como concluída
• `/meta excluir [id]` - Excluir meta

*Tipos de Meta:*
💰 Economia - Juntar dinheiro
📈 Investimento - Para investir
🎯 Limite de Gasto - Controlar gastos
💳 Quitação - Pagar dívidas
🆘 Emergência - Fundo de reserva
✈️ Viagem - Juntar para viagem
🛒 Compra - Comprar algo específico

*Exemplos:*
`/meta Viagem 5000`
`/meta depositar m1 500`
"""
    
    def _listar_metas(self, user_id: str) -> str:
        """Lista todas as metas do usuário"""
        metas_usuario = [m for m in self.metas if m.get('user_id') == user_id]
        
        if not metas_usuario:
            return """
🎯 *Suas Metas*

_Você ainda não tem metas._

Crie sua primeira meta:
• `/meta criar` - Modo interativo
• `/meta Viagem 5000` - Modo rápido

💡 Metas ajudam você a economizar!
"""
        
        # Separa ativas e concluídas
        ativas = [m for m in metas_usuario if not m.get('concluida')]
        concluidas = [m for m in metas_usuario if m.get('concluida')]
        
        resposta = "🎯 *Suas Metas*\n\n"
        
        if ativas:
            resposta += "*📌 Ativas:*\n"
            for meta in ativas:
                progresso = self._calcular_progresso(meta)
                barra = self._barra_progresso(progresso)
                tipo_emoji = self.TIPOS_META.get(meta.get('tipo', 'outro'), '📌').split()[0]
                
                resposta += f"""
{tipo_emoji} *{meta.get('titulo', 'Meta')}* `[{meta.get('id')}]`
{barra}
💵 R$ {meta.get('valor_atual', 0):,.2f} / R$ {meta.get('valor_alvo', 0):,.2f}
"""
                # Prazo
                prazo = meta.get('prazo', '')
                if prazo:
                    try:
                        data_prazo = datetime.fromisoformat(prazo).date()
                        dias = (data_prazo - datetime.now().date()).days
                        if dias > 0:
                            resposta += f"⏰ {dias} dias restantes\n"
                        elif dias == 0:
                            resposta += f"⏰ Prazo é HOJE!\n"
                        else:
                            resposta += f"⏰ Prazo expirado há {-dias} dias\n"
                    except:
                        pass
        
        if concluidas:
            resposta += f"\n*✅ Concluídas:* {len(concluidas)}\n"
            for meta in concluidas[-3:]:  # Últimas 3
                resposta += f"  🏆 {meta.get('titulo', 'Meta')}\n"
        
        resposta += "\n_Use `/meta ver [id]` para detalhes_"
        
        return resposta
    
    def _criar_meta_rapida(self, user_id: str, args: List[str]) -> str:
        """Cria meta de forma rápida: /meta [titulo] [valor]"""
        if len(args) < 2:
            return "❌ Use: `/meta [título] [valor]`\nExemplo: `/meta Viagem 5000`"
        
        # Última parte é o valor
        try:
            valor_str = args[-1].replace('R$', '').replace('.', '').replace(',', '.').strip()
            valor = float(valor_str)
            titulo = ' '.join(args[:-1])
        except:
            return "❌ Valor inválido. Use: `/meta [título] [valor]`"
        
        if valor <= 0:
            return "❌ O valor deve ser maior que zero."
        
        # Cria a meta
        meta_id = self._gerar_id()
        nova_meta = Meta(
            id=meta_id,
            titulo=titulo,
            tipo='economia',
            valor_alvo=valor,
            valor_atual=0,
            user_id=user_id,
            criado_em=datetime.now().isoformat()
        )
        
        self.metas.append(nova_meta.to_dict())
        self._save_data()
        
        return f"""
✅ *Meta Criada!*

🎯 {titulo}
💰 Valor: R$ {valor:,.2f}
📋 ID: `{meta_id}`

*Próximos passos:*
• `/meta depositar {meta_id} [valor]` - Adicionar dinheiro
• `/meta ver {meta_id}` - Ver detalhes
• `/metas` - Ver todas as metas
"""
    
    def _criar_meta_interativo(self, user_id: str, args: List[str]) -> str:
        """Inicia criação interativa de meta"""
        # Por enquanto, retorna instruções
        return """
🎯 *Criar Nova Meta*

Para criar uma meta, use:
`/meta [título] [valor]`

*Exemplos:*
• `/meta Viagem para praia 3000`
• `/meta Fundo de emergência 10000`
• `/meta iPhone 15 5000`
• `/meta Quitar cartão 2500`

*Opções avançadas:*
Após criar, você pode:
• Definir prazo
• Configurar depósitos automáticos
• Categorizar a meta

💡 Dica: Comece com uma meta simples!
"""
    
    def _depositar_meta(self, user_id: str, args: List[str]) -> str:
        """Deposita valor em uma meta"""
        if len(args) < 1:
            # Lista metas para o usuário escolher
            metas_usuario = [m for m in self.metas 
                           if m.get('user_id') == user_id and not m.get('concluida')]
            
            if not metas_usuario:
                return "❌ Você não tem metas ativas."
            
            resposta = "💰 *Depositar em qual meta?*\n\n"
            for meta in metas_usuario:
                resposta += f"• `{meta.get('id')}` - {meta.get('titulo')}\n"
            resposta += "\nUse: `/meta depositar [id] [valor]`"
            return resposta
        
        # Se só tem 1 argumento, pode ser valor (assume última meta) ou ID
        if len(args) == 1:
            # Tenta como valor na última meta
            try:
                valor = float(args[0].replace('R$', '').replace(',', '.').strip())
                metas_usuario = [m for m in self.metas 
                               if m.get('user_id') == user_id and not m.get('concluida')]
                if metas_usuario:
                    meta_id = metas_usuario[-1].get('id')
                    return self._depositar_meta(user_id, [meta_id, str(valor)])
            except:
                pass
            return "❌ Use: `/meta depositar [id] [valor]`"
        
        meta_id = args[0]
        try:
            valor = float(args[1].replace('R$', '').replace(',', '.').strip())
        except:
            return "❌ Valor inválido."
        
        if valor <= 0:
            return "❌ O valor deve ser maior que zero."
        
        # Encontra a meta
        for meta in self.metas:
            if meta.get('id') == meta_id and meta.get('user_id') == user_id:
                if meta.get('concluida'):
                    return "❌ Esta meta já foi concluída."
                
                valor_anterior = meta.get('valor_atual', 0)
                meta['valor_atual'] = valor_anterior + valor
                
                # Adiciona ao histórico
                if 'historico' not in meta:
                    meta['historico'] = []
                meta['historico'].append({
                    'tipo': 'deposito',
                    'valor': valor,
                    'data': datetime.now().isoformat(),
                    'saldo_apos': meta['valor_atual']
                })
                
                self._save_data()
                
                progresso = self._calcular_progresso(meta)
                barra = self._barra_progresso(progresso)
                
                resposta = f"""
✅ *Depósito Realizado!*

🎯 {meta.get('titulo')}
💵 + R$ {valor:,.2f}

{barra}
💰 Total: R$ {meta['valor_atual']:,.2f} / R$ {meta.get('valor_alvo', 0):,.2f}
"""
                
                # Verifica se atingiu a meta
                if meta['valor_atual'] >= meta.get('valor_alvo', 0):
                    resposta += """

🎉 *PARABÉNS! META ALCANÇADA!* 🎉

Use `/meta concluir {meta_id}` para marcar como concluída!
"""
                else:
                    falta = meta.get('valor_alvo', 0) - meta['valor_atual']
                    resposta += f"\n📊 Faltam: R$ {falta:,.2f}"
                
                return resposta
        
        return f"❌ Meta `{meta_id}` não encontrada."
    
    def _retirar_meta(self, user_id: str, args: List[str]) -> str:
        """Retira valor de uma meta"""
        if len(args) < 2:
            return "❌ Use: `/meta retirar [id] [valor]`"
        
        meta_id = args[0]
        try:
            valor = float(args[1].replace('R$', '').replace(',', '.').strip())
        except:
            return "❌ Valor inválido."
        
        if valor <= 0:
            return "❌ O valor deve ser maior que zero."
        
        for meta in self.metas:
            if meta.get('id') == meta_id and meta.get('user_id') == user_id:
                valor_atual = meta.get('valor_atual', 0)
                
                if valor > valor_atual:
                    return f"❌ Saldo insuficiente. Disponível: R$ {valor_atual:,.2f}"
                
                meta['valor_atual'] = valor_atual - valor
                
                # Adiciona ao histórico
                if 'historico' not in meta:
                    meta['historico'] = []
                meta['historico'].append({
                    'tipo': 'retirada',
                    'valor': valor,
                    'data': datetime.now().isoformat(),
                    'saldo_apos': meta['valor_atual']
                })
                
                self._save_data()
                
                progresso = self._calcular_progresso(meta)
                barra = self._barra_progresso(progresso)
                
                return f"""
💸 *Retirada Realizada*

🎯 {meta.get('titulo')}
💵 - R$ {valor:,.2f}

{barra}
💰 Saldo: R$ {meta['valor_atual']:,.2f} / R$ {meta.get('valor_alvo', 0):,.2f}
"""
        
        return f"❌ Meta `{meta_id}` não encontrada."
    
    def _detalhes_meta(self, user_id: str, args: List[str]) -> str:
        """Mostra detalhes de uma meta"""
        if not args:
            return "❌ Use: `/meta ver [id]`"
        
        meta_id = args[0]
        
        for meta in self.metas:
            if meta.get('id') == meta_id and meta.get('user_id') == user_id:
                progresso = self._calcular_progresso(meta)
                barra = self._barra_progresso(progresso)
                tipo_nome = self.TIPOS_META.get(meta.get('tipo', 'outro'), '📌 Outro')
                
                resposta = f"""
🎯 *{meta.get('titulo')}*

📋 ID: `{meta_id}`
📌 Tipo: {tipo_nome}
💰 Valor atual: R$ {meta.get('valor_atual', 0):,.2f}
🎯 Meta: R$ {meta.get('valor_alvo', 0):,.2f}

{barra}

"""
                # Prazo
                prazo = meta.get('prazo', '')
                if prazo:
                    try:
                        data_prazo = datetime.fromisoformat(prazo).date()
                        dias = (data_prazo - datetime.now().date()).days
                        resposta += f"📅 Prazo: {data_prazo.strftime('%d/%m/%Y')} ({dias} dias)\n"
                    except:
                        pass
                
                # Descrição
                if meta.get('descricao'):
                    resposta += f"📝 {meta.get('descricao')}\n"
                
                # Histórico recente
                historico = meta.get('historico', [])
                if historico:
                    resposta += "\n*📜 Últimas movimentações:*\n"
                    for mov in historico[-5:]:
                        emoji = "💵" if mov.get('tipo') == 'deposito' else "💸"
                        sinal = "+" if mov.get('tipo') == 'deposito' else "-"
                        try:
                            data = datetime.fromisoformat(mov.get('data', '')).strftime('%d/%m')
                        except:
                            data = "?"
                        resposta += f"  {emoji} {sinal}R$ {mov.get('valor', 0):,.2f} ({data})\n"
                
                resposta += f"\n📅 Criada em: {meta.get('criado_em', '')[:10]}"
                
                return resposta
        
        return f"❌ Meta `{meta_id}` não encontrada."
    
    def _concluir_meta(self, user_id: str, args: List[str]) -> str:
        """Marca uma meta como concluída"""
        if not args:
            return "❌ Use: `/meta concluir [id]`"
        
        meta_id = args[0]
        
        for meta in self.metas:
            if meta.get('id') == meta_id and meta.get('user_id') == user_id:
                if meta.get('concluida'):
                    return "❌ Esta meta já foi concluída."
                
                meta['concluida'] = True
                meta['concluido_em'] = datetime.now().isoformat()
                self._save_data()
                
                return f"""
🎉🎉🎉 *META CONCLUÍDA!* 🎉🎉🎉

🏆 {meta.get('titulo')}
💰 Total guardado: R$ {meta.get('valor_atual', 0):,.2f}

Parabéns pela conquista! 🥳

_Use `/metas` para ver suas outras metas_
"""
        
        return f"❌ Meta `{meta_id}` não encontrada."
    
    def _excluir_meta(self, user_id: str, args: List[str]) -> str:
        """Exclui uma meta"""
        if not args:
            return "❌ Use: `/meta excluir [id]`"
        
        meta_id = args[0]
        
        for i, meta in enumerate(self.metas):
            if meta.get('id') == meta_id and meta.get('user_id') == user_id:
                titulo = meta.get('titulo')
                del self.metas[i]
                self._save_data()
                
                return f"🗑️ Meta *{titulo}* excluída."
        
        return f"❌ Meta `{meta_id}` não encontrada."
    
    # ========== INTEGRAÇÕES ==========
    
    def verificar_limite_gastos(self, user_id: str, categoria: str, valor: float) -> Optional[str]:
        """Verifica se um gasto excede o limite definido em uma meta"""
        for meta in self.metas:
            if (meta.get('user_id') == user_id and 
                meta.get('tipo') == 'limite_gasto' and
                meta.get('categoria', '').lower() == categoria.lower() and
                not meta.get('concluida')):
                
                # Calcula gastos do mês na categoria
                if self.financas_module:
                    hoje = datetime.now()
                    gastos_mes = 0
                    for t in self.financas_module.transacoes:
                        if (t.get('user_id') == user_id and 
                            t.get('tipo') == 'saida' and
                            t.get('categoria', '').lower() == categoria.lower()):
                            try:
                                data = datetime.fromisoformat(t['data'])
                                if data.month == hoje.month and data.year == hoje.year:
                                    gastos_mes += t.get('valor', 0)
                            except:
                                continue
                    
                    limite = meta.get('valor_alvo', 0)
                    if gastos_mes + valor > limite:
                        return f"""
⚠️ *ALERTA DE LIMITE!*

🎯 Meta: {meta.get('titulo')}
💰 Limite: R$ {limite:,.2f}
💸 Já gastou: R$ {gastos_mes:,.2f}
❌ Este gasto: R$ {valor:,.2f}

Você vai ultrapassar o limite em R$ {(gastos_mes + valor - limite):,.2f}!
"""
        
        return None


# Singleton
_metas_instance = None

def get_metas(data_dir: str = "data") -> MetasModule:
    """Retorna instância singleton do módulo de metas"""
    global _metas_instance
    if _metas_instance is None:
        _metas_instance = MetasModule(data_dir)
    return _metas_instance
