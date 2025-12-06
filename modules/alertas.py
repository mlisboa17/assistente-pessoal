"""
🔔 Módulo de Alertas Inteligentes
Sistema de alertas automáticos e notificações
"""
import json
import os
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum


class TipoAlerta(Enum):
    """Tipos de alerta disponíveis"""
    LEMBRETE = "lembrete"
    VENCIMENTO = "vencimento"
    ESTOQUE_BAIXO = "estoque_baixo"
    META_FINANCEIRA = "meta_financeira"
    EMAIL_IMPORTANTE = "email_importante"
    COMPROMISSO = "compromisso"
    PERSONALIZADO = "personalizado"


class Prioridade(Enum):
    """Níveis de prioridade"""
    BAIXA = 1
    MEDIA = 2
    ALTA = 3
    URGENTE = 4


@dataclass
class Alerta:
    """Representa um alerta"""
    id: str
    tipo: str
    titulo: str
    mensagem: str
    prioridade: int = 2
    data_disparo: str = ""  # ISO format - quando disparar
    recorrente: bool = False
    intervalo_horas: int = 0  # Para alertas recorrentes
    ativo: bool = True
    disparado: bool = False
    user_id: str = ""
    dados_extra: Dict = None  # Dados adicionais do alerta
    criado_em: str = ""
    
    def __post_init__(self):
        if self.dados_extra is None:
            self.dados_extra = {}
    
    def to_dict(self):
        return asdict(self)


@dataclass
class Gatilho:
    """Representa um gatilho automático"""
    id: str
    nome: str
    condicao: str  # Condição em formato string
    acao: str  # Ação a executar
    modulo: str  # Módulo relacionado
    ativo: bool = True
    user_id: str = ""
    criado_em: str = ""
    ultima_execucao: str = ""
    
    def to_dict(self):
        return asdict(self)


class AlertasModule:
    """Gerenciador de Alertas Inteligentes"""
    
    # Emojis por tipo de alerta
    EMOJIS = {
        'lembrete': '📝',
        'vencimento': '⚠️',
        'estoque_baixo': '📦',
        'meta_financeira': '🎯',
        'email_importante': '📧',
        'compromisso': '📅',
        'personalizado': '🔔'
    }
    
    # Emojis por prioridade
    PRIORIDADE_EMOJI = {
        1: '🟢',  # Baixa
        2: '🟡',  # Média
        3: '🟠',  # Alta
        4: '🔴'   # Urgente
    }
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.alertas_file = os.path.join(data_dir, "alertas.json")
        self.gatilhos_file = os.path.join(data_dir, "gatilhos.json")
        
        os.makedirs(data_dir, exist_ok=True)
        self._load_data()
        
        # Callbacks para notificação
        self.notificacao_callbacks: List[Callable] = []
        
        # Referências aos outros módulos (serão injetados)
        self.financas_module = None
        self.vendas_module = None
        self.agenda_module = None
    
    def set_modules(self, financas=None, vendas=None, agenda=None):
        """Define referências aos outros módulos"""
        self.financas_module = financas
        self.vendas_module = vendas
        self.agenda_module = agenda
    
    def add_notificacao_callback(self, callback: Callable):
        """Adiciona callback para enviar notificações"""
        self.notificacao_callbacks.append(callback)
    
    def _load_data(self):
        """Carrega dados do disco"""
        # Alertas
        if os.path.exists(self.alertas_file):
            with open(self.alertas_file, 'r', encoding='utf-8') as f:
                self.alertas = json.load(f)
        else:
            self.alertas = []
        
        # Gatilhos
        if os.path.exists(self.gatilhos_file):
            with open(self.gatilhos_file, 'r', encoding='utf-8') as f:
                self.gatilhos = json.load(f)
        else:
            self.gatilhos = self._criar_gatilhos_padrao()
    
    def _save_data(self):
        """Salva dados no disco"""
        with open(self.alertas_file, 'w', encoding='utf-8') as f:
            json.dump(self.alertas, f, ensure_ascii=False, indent=2)
        
        with open(self.gatilhos_file, 'w', encoding='utf-8') as f:
            json.dump(self.gatilhos, f, ensure_ascii=False, indent=2)
    
    def _criar_gatilhos_padrao(self) -> List[Dict]:
        """Cria gatilhos padrão do sistema"""
        gatilhos = [
            {
                "id": "g1",
                "nome": "Alerta de Estoque Baixo",
                "condicao": "estoque <= estoque_minimo",
                "acao": "notificar_estoque_baixo",
                "modulo": "vendas",
                "ativo": True,
                "criado_em": datetime.now().isoformat()
            },
            {
                "id": "g2", 
                "nome": "Lembrete de Vencimento",
                "condicao": "dias_ate_vencimento <= 3",
                "acao": "notificar_vencimento",
                "modulo": "faturas",
                "ativo": True,
                "criado_em": datetime.now().isoformat()
            },
            {
                "id": "g3",
                "nome": "Compromisso Próximo",
                "condicao": "minutos_ate_evento <= 30",
                "acao": "notificar_compromisso",
                "modulo": "agenda",
                "ativo": True,
                "criado_em": datetime.now().isoformat()
            },
            {
                "id": "g4",
                "nome": "Meta de Gastos",
                "condicao": "gastos_mes >= limite_mes",
                "acao": "notificar_meta_gastos",
                "modulo": "financas",
                "ativo": True,
                "criado_em": datetime.now().isoformat()
            }
        ]
        self._save_gatilhos(gatilhos)
        return gatilhos
    
    def _save_gatilhos(self, gatilhos: List[Dict]):
        """Salva gatilhos no disco"""
        with open(self.gatilhos_file, 'w', encoding='utf-8') as f:
            json.dump(gatilhos, f, ensure_ascii=False, indent=2)
    
    async def handle(self, command: str, args: List[str], 
                     user_id: str, attachments: list = None) -> str:
        """Processa comandos de alertas"""
        
        if command == 'alertas':
            return self._listar_alertas(user_id)
        
        elif command == 'alerta':
            if args:
                return self._criar_alerta_rapido(user_id, ' '.join(args))
            return self._ajuda_alertas()
        
        elif command == 'gatilhos':
            return self._listar_gatilhos(user_id)
        
        elif command == 'silenciar':
            if args:
                return self._silenciar_alerta(user_id, args[0])
            return "❌ Use: /silenciar [id do alerta]"
        
        return "🔔 Comandos: /alertas, /alerta, /gatilhos, /silenciar"
    
    async def handle_natural(self, message: str, analysis: Any,
                              user_id: str, attachments: list = None) -> str:
        """Processa linguagem natural"""
        text_lower = message.lower()
        
        if any(word in text_lower for word in ['criar alerta', 'me avise', 'lembre-me', 'notifique']):
            return self._criar_alerta_rapido(user_id, message)
        
        if any(word in text_lower for word in ['alertas', 'notificações', 'avisos']):
            return self._listar_alertas(user_id)
        
        return self._ajuda_alertas()
    
    def _ajuda_alertas(self) -> str:
        """Retorna ajuda sobre alertas"""
        return """
🔔 *Módulo de Alertas Inteligentes*

*Criar alerta:*
/alerta [descrição] [quando]
Exemplo: /alerta Pagar conta de luz amanhã

*Ver alertas:*
/alertas - Lista alertas pendentes

*Gatilhos automáticos:*
/gatilhos - Ver gatilhos ativos

Os alertas são disparados automaticamente quando:
• 📦 Estoque de produto fica baixo
• ⚠️ Boleto perto do vencimento
• 📅 Compromisso se aproxima
• 💰 Gastos atingem limite

*Exemplos:*
• "me avise sobre reunião às 14h"
• "criar alerta para pagar conta dia 10"
"""
    
    def _listar_alertas(self, user_id: str) -> str:
        """Lista alertas do usuário"""
        alertas_user = [a for a in self.alertas if a.get('user_id') == user_id and a.get('ativo')]
        
        if not alertas_user:
            return """
🔔 *Seus Alertas*

Nenhum alerta ativo.

Use /alerta [descrição] para criar um novo.
"""
        
        linhas = ["🔔 *Seus Alertas*\n"]
        
        # Agrupa por tipo
        por_tipo = {}
        for a in alertas_user:
            tipo = a.get('tipo', 'personalizado')
            if tipo not in por_tipo:
                por_tipo[tipo] = []
            por_tipo[tipo].append(a)
        
        for tipo, alertas in por_tipo.items():
            emoji = self.EMOJIS.get(tipo, '🔔')
            linhas.append(f"{emoji} *{tipo.replace('_', ' ').title()}*")
            
            for a in alertas[:5]:  # Máximo 5 por tipo
                prioridade = self.PRIORIDADE_EMOJI.get(a.get('prioridade', 2), '🟡')
                linhas.append(f"  {prioridade} {a.get('titulo', 'Alerta')}")
                if a.get('data_disparo'):
                    try:
                        dt = datetime.fromisoformat(a['data_disparo'])
                        linhas.append(f"      📅 {dt.strftime('%d/%m %H:%M')}")
                    except:
                        pass
            linhas.append("")
        
        return '\n'.join(linhas)
    
    def _criar_alerta_rapido(self, user_id: str, texto: str) -> str:
        """Cria um alerta a partir de texto livre"""
        import re
        from uuid import uuid4
        
        # Detecta data/hora mencionada
        data_disparo = self._extrair_data_hora(texto)
        
        # Detecta prioridade
        prioridade = 2  # Média por padrão
        if any(word in texto.lower() for word in ['urgente', 'importante', 'crítico']):
            prioridade = 4
        elif any(word in texto.lower() for word in ['alta prioridade', 'prioridade alta']):
            prioridade = 3
        
        alerta = Alerta(
            id=str(uuid4())[:8],
            tipo='personalizado',
            titulo=texto[:50],
            mensagem=texto,
            prioridade=prioridade,
            data_disparo=data_disparo.isoformat() if data_disparo else "",
            user_id=user_id,
            criado_em=datetime.now().isoformat()
        )
        
        self.alertas.append(alerta.to_dict())
        self._save_data()
        
        resposta = f"""
✅ *Alerta Criado!*

🔔 {texto[:50]}
{self.PRIORIDADE_EMOJI[prioridade]} Prioridade: {'Urgente' if prioridade == 4 else 'Alta' if prioridade == 3 else 'Média' if prioridade == 2 else 'Baixa'}
"""
        
        if data_disparo:
            resposta += f"📅 Disparo: {data_disparo.strftime('%d/%m/%Y %H:%M')}\n"
        
        resposta += f"🆔 ID: {alerta.id}"
        
        return resposta
    
    def _extrair_data_hora(self, texto: str) -> Optional[datetime]:
        """Extrai data/hora de um texto"""
        import re
        
        texto_lower = texto.lower()
        agora = datetime.now()
        
        # Padrões relativos
        if 'amanhã' in texto_lower or 'amanha' in texto_lower:
            data = agora + timedelta(days=1)
            return data.replace(hour=9, minute=0, second=0, microsecond=0)
        
        if 'hoje' in texto_lower:
            return agora.replace(second=0, microsecond=0)
        
        if 'semana que vem' in texto_lower or 'próxima semana' in texto_lower:
            data = agora + timedelta(days=7)
            return data.replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Extrai hora (ex: "às 14h", "14:30")
        hora_match = re.search(r'(\d{1,2})[h:](\d{2})?', texto_lower)
        if hora_match:
            hora = int(hora_match.group(1))
            minuto = int(hora_match.group(2)) if hora_match.group(2) else 0
            return agora.replace(hour=hora, minute=minuto, second=0, microsecond=0)
        
        # Extrai dia do mês (ex: "dia 15", "15/12")
        dia_match = re.search(r'dia (\d{1,2})|(\d{1,2})/(\d{1,2})', texto_lower)
        if dia_match:
            if dia_match.group(1):
                dia = int(dia_match.group(1))
                return agora.replace(day=dia, hour=9, minute=0, second=0, microsecond=0)
            else:
                dia = int(dia_match.group(2))
                mes = int(dia_match.group(3))
                return agora.replace(month=mes, day=dia, hour=9, minute=0, second=0, microsecond=0)
        
        return None
    
    def _listar_gatilhos(self, user_id: str) -> str:
        """Lista gatilhos automáticos"""
        linhas = ["⚡ *Gatilhos Automáticos*\n"]
        
        for g in self.gatilhos:
            status = "✅" if g.get('ativo') else "❌"
            linhas.append(f"{status} *{g.get('nome')}*")
            linhas.append(f"   📋 Módulo: {g.get('modulo')}")
            linhas.append(f"   🎯 Condição: {g.get('condicao')}")
            linhas.append("")
        
        linhas.append("💡 Gatilhos disparam alertas automaticamente!")
        
        return '\n'.join(linhas)
    
    def _silenciar_alerta(self, user_id: str, alerta_id: str) -> str:
        """Silencia/desativa um alerta"""
        for a in self.alertas:
            if a.get('id') == alerta_id and a.get('user_id') == user_id:
                a['ativo'] = False
                self._save_data()
                return f"🔕 Alerta '{a.get('titulo', alerta_id)}' silenciado."
        
        return f"❌ Alerta '{alerta_id}' não encontrado."
    
    # ========== MÉTODOS DE VERIFICAÇÃO AUTOMÁTICA ==========
    
    async def verificar_alertas_pendentes(self) -> List[Dict]:
        """Verifica alertas que precisam ser disparados"""
        agora = datetime.now()
        alertas_disparar = []
        
        for a in self.alertas:
            if not a.get('ativo') or a.get('disparado'):
                continue
            
            if a.get('data_disparo'):
                try:
                    data_disparo = datetime.fromisoformat(a['data_disparo'])
                    if data_disparo <= agora:
                        alertas_disparar.append(a)
                        a['disparado'] = True
                except:
                    pass
        
        if alertas_disparar:
            self._save_data()
        
        return alertas_disparar
    
    async def verificar_gatilhos(self) -> List[Dict]:
        """Verifica gatilhos e cria alertas se necessário"""
        alertas_novos = []
        
        for g in self.gatilhos:
            if not g.get('ativo'):
                continue
            
            # Verifica cada tipo de gatilho
            if g.get('modulo') == 'vendas' and self.vendas_module:
                produtos_baixos = self.vendas_module.verificar_estoque_baixo()
                for p in produtos_baixos:
                    alerta = self._criar_alerta_estoque_baixo(p)
                    if alerta:
                        alertas_novos.append(alerta)
        
        return alertas_novos
    
    def _criar_alerta_estoque_baixo(self, produto: Dict) -> Optional[Dict]:
        """Cria alerta de estoque baixo"""
        from uuid import uuid4
        
        # Verifica se já existe alerta para este produto
        for a in self.alertas:
            if (a.get('tipo') == 'estoque_baixo' and 
                a.get('dados_extra', {}).get('produto_id') == produto.get('id') and
                a.get('ativo')):
                return None
        
        alerta = Alerta(
            id=str(uuid4())[:8],
            tipo='estoque_baixo',
            titulo=f"Estoque baixo: {produto.get('nome')}",
            mensagem=f"O produto {produto.get('nome')} está com apenas {produto.get('estoque')} unidades.",
            prioridade=3,
            dados_extra={'produto_id': produto.get('id')},
            criado_em=datetime.now().isoformat()
        )
        
        self.alertas.append(alerta.to_dict())
        self._save_data()
        
        return alerta.to_dict()
    
    def criar_alerta_vencimento(self, boleto: Dict, user_id: str) -> Dict:
        """Cria alerta de vencimento de boleto"""
        from uuid import uuid4
        
        alerta = Alerta(
            id=str(uuid4())[:8],
            tipo='vencimento',
            titulo=f"Vencimento: {boleto.get('beneficiario', 'Boleto')[:30]}",
            mensagem=f"Boleto de R$ {boleto.get('valor', 0):,.2f} vence em {boleto.get('vencimento')}",
            prioridade=3,
            data_disparo=boleto.get('vencimento'),
            user_id=user_id,
            dados_extra={'boleto_id': boleto.get('id')},
            criado_em=datetime.now().isoformat()
        )
        
        self.alertas.append(alerta.to_dict())
        self._save_data()
        
        return alerta.to_dict()
    
    def criar_alerta_compromisso(self, evento: Dict, user_id: str, minutos_antes: int = 30) -> Dict:
        """Cria alerta para compromisso"""
        from uuid import uuid4
        
        try:
            data_evento = datetime.fromisoformat(evento.get('data', ''))
            data_alerta = data_evento - timedelta(minutes=minutos_antes)
        except:
            data_alerta = datetime.now()
        
        alerta = Alerta(
            id=str(uuid4())[:8],
            tipo='compromisso',
            titulo=f"📅 {evento.get('titulo', 'Compromisso')}",
            mensagem=f"Seu compromisso começa em {minutos_antes} minutos!",
            prioridade=3,
            data_disparo=data_alerta.isoformat(),
            user_id=user_id,
            dados_extra={'evento_id': evento.get('id')},
            criado_em=datetime.now().isoformat()
        )
        
        self.alertas.append(alerta.to_dict())
        self._save_data()
        
        return alerta.to_dict()
