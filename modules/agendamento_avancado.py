"""
📅 Sistema Avançado de Agendamento com Confirmação e Lembretes

Fluxo:
1. Usuário inicia agendamento com data/hora
2. Sistema mostra dados e pede confirmação
3. Usuário confirma ou edita data/hora
4. Sistema cria evento + lembrete automático (2 horas antes)
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import json
import re


@dataclass
class AgendamentoConfirmacao:
    """Agendamento aguardando confirmação do usuário"""
    id: str
    titulo: str
    data_original: str
    hora_original: str
    data_confirmada: Optional[str] = None
    hora_confirmada: Optional[str] = None
    user_id: str = ""
    origem: str = "documento"  # documento, comando, natural
    extra: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.extra is None:
            self.extra = {}


class SistemaAgendamentoAvancado:
    """Gerencia agendamentos com confirmação interativa e lembretes automáticos"""
    
    def __init__(self):
        self.pendentes = {}  # user_id -> AgendamentoConfirmacao
    
    def iniciar_agendamento(
        self,
        titulo: str,
        data: str,
        hora: str,
        user_id: str,
        origem: str = "documento"
    ) -> str:
        """
        Inicia processo de agendamento
        
        Formatos aceitos:
        - Data: YYYY-MM-DD ou DD/MM/YYYY ou "amanhã", "próxima segunda"
        - Hora: HH:MM ou "09:00" ou "9h"
        
        Retorna mensagem de confirmação
        """
        
        # Normalizar data
        data_norm = self._normalizar_data(data)
        if not data_norm:
            return f"❌ Data inválida: {data}\n\nUse formato: 2025-12-25 ou 25/12/2025"
        
        # Normalizar hora
        hora_norm = self._normalizar_hora(hora)
        if not hora_norm:
            return f"❌ Hora inválida: {hora}\n\nUse formato: 14:30 ou 14h30"
        
        # Criar agendamento pendente
        agendamento = AgendamentoConfirmacao(
            id=f"agd_{int(datetime.now().timestamp())}",
            titulo=titulo,
            data_original=data_norm,
            hora_original=hora_norm,
            user_id=user_id,
            origem=origem
        )
        
        self.pendentes[user_id] = agendamento
        
        # Formatar resposta
        return self._formatar_confirmacao_inicial(agendamento)
    
    def _normalizar_data(self, data: str) -> Optional[str]:
        """Normaliza data para YYYY-MM-DD"""
        
        data_lower = data.lower().strip()
        hoje = datetime.now()
        
        # Palavras-chave
        if data_lower in ['hoje', 'agora']:
            return hoje.strftime('%Y-%m-%d')
        
        if data_lower in ['amanhã', 'amanha']:
            amanha = hoje + timedelta(days=1)
            return amanha.strftime('%Y-%m-%d')
        
        if data_lower in ['próxima segunda', 'proxima segunda']:
            dias_ate_segunda = (7 - hoje.weekday()) % 7
            if dias_ate_segunda == 0:
                dias_ate_segunda = 7
            segunda = hoje + timedelta(days=dias_ate_segunda)
            return segunda.strftime('%Y-%m-%d')
        
        # Formato DD/MM/YYYY
        match = re.match(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', data)
        if match:
            try:
                dia, mes, ano = int(match.group(1)), int(match.group(2)), int(match.group(3))
                data_obj = datetime(ano, mes, dia)
                return data_obj.strftime('%Y-%m-%d')
            except ValueError:
                return None
        
        # Formato YYYY-MM-DD
        match = re.match(r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', data)
        if match:
            try:
                ano, mes, dia = int(match.group(1)), int(match.group(2)), int(match.group(3))
                data_obj = datetime(ano, mes, dia)
                return data_obj.strftime('%Y-%m-%d')
            except ValueError:
                return None
        
        return None
    
    def _normalizar_hora(self, hora: str) -> Optional[str]:
        """Normaliza hora para HH:MM"""
        
        hora_clean = hora.lower().strip().replace('h', ':').replace('hs', ':')
        
        # Formato HH:MM ou HH
        match = re.match(r'(\d{1,2}):?(\d{0,2})', hora_clean)
        if match:
            try:
                h = int(match.group(1))
                m = int(match.group(2)) if match.group(2) else 0
                
                if 0 <= h <= 23 and 0 <= m <= 59:
                    return f"{h:02d}:{m:02d}"
            except ValueError:
                pass
        
        return None
    
    def _formatar_confirmacao_inicial(self, agendamento: AgendamentoConfirmacao) -> str:
        """Formata mensagem inicial de confirmação"""
        
        data_fmt = self._formatar_data_exibicao(agendamento.data_original)
        
        msg = f"""
📅 *AGENDAMENTO PARA CONFIRMAR*

{'═' * 50}
📌 *EVENTO:* {agendamento.titulo}

📆 *DATA:* {data_fmt}
⏰ *HORA:* {agendamento.hora_original}

🔔 *LEMBRETE:* Automático 2h antes

{'═' * 50}

*Confirme os dados:*

✅ `/confirmar` ou `/ok` - Agendar
✏️  `/editar data 25/12/2025` - Mudar data
✏️  `/editar hora 14:30` - Mudar hora
❌ `/cancelar` - Descartar
"""
        
        return msg
    
    def _formatar_data_exibicao(self, data: str) -> str:
        """Formata data para exibição amigável"""
        
        try:
            data_obj = datetime.strptime(data, '%Y-%m-%d')
            dia_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
            
            return f"{dia_semana[data_obj.weekday()]}, {data_obj.strftime('%d de %B de %Y')}"
        except:
            return data
    
    def processar_resposta(
        self,
        mensagem: str,
        user_id: str,
        agenda_module=None
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Processa resposta do usuário sobre agendamento
        
        Retorna: (mensagem, dados_processamento)
        dados_processamento = {
            'acao': 'agendar|editar|cancelar',
            'agendamento': AgendamentoConfirmacao,
            'evento_id': '...',  # se foi agendado
            'lembrete_id': '...',  # se foi criado
        }
        """
        
        if user_id not in self.pendentes:
            return "❌ Nenhum agendamento pendente para você.", None
        
        agendamento = self.pendentes[user_id]
        mensagem_lower = mensagem.lower().strip()
        
        # ✅ CONFIRMAÇÃO
        if mensagem_lower in ['confirmar', 'ok', 'sim', 'yes', 'confirmo', 'correto']:
            resposta, dados = self._executar_agendamento(agendamento, agenda_module, user_id)
            del self.pendentes[user_id]
            return resposta, dados
        
        # ❌ CANCELAMENTO
        if mensagem_lower in ['cancelar', 'nao', 'no', 'cancel']:
            del self.pendentes[user_id]
            return "❌ Agendamento cancelado.\n\nEnvie um novo para tentar de novo.", {
                'acao': 'cancelar',
                'agendamento': agendamento
            }
        
        # ✏️ EDIÇÃO
        if mensagem_lower.startswith('/editar') or mensagem_lower.startswith('editar'):
            return self._processar_edicao(mensagem, agendamento, user_id)
        
        # Se não entendeu
        return self._formatar_confirmacao_inicial(agendamento), None
    
    def _processar_edicao(
        self,
        mensagem: str,
        agendamento: AgendamentoConfirmacao,
        user_id: str
    ) -> Tuple[str, Optional[Dict]]:
        """Processa edição de data ou hora"""
        
        try:
            # Extrai campo e valor: /editar data 25/12/2025
            partes = mensagem.split(None, 2)
            
            if len(partes) < 3:
                return "❌ Formato: `/editar data 25/12/2025` ou `/editar hora 14:30`", None
            
            _, campo, valor = partes
            campo = campo.lower().strip()
            valor = valor.strip()
            
            if campo == 'data':
                data_norm = self._normalizar_data(valor)
                if not data_norm:
                    return f"❌ Data inválida: {valor}\n\nUse: 25/12/2025 ou 2025-12-25", None
                
                agendamento.data_confirmada = data_norm
                data_fmt = self._formatar_data_exibicao(data_norm)
                msg = f"✅ Data atualizada para: {data_fmt}\n\n"
                
            elif campo == 'hora':
                hora_norm = self._normalizar_hora(valor)
                if not hora_norm:
                    return f"❌ Hora inválida: {valor}\n\nUse: 14:30 ou 14h", None
                
                agendamento.hora_confirmada = hora_norm
                msg = f"✅ Hora atualizada para: {hora_norm}\n\n"
                
            else:
                return f"❌ Campo inválido: {campo}\n\nCampos válidos: data, hora", None
            
            # Mostrar confirmação novamente
            msg += self._formatar_confirmacao_inicial(agendamento)
            
            return msg, {
                'acao': 'editar',
                'campo': campo,
                'valor': valor,
                'agendamento': agendamento
            }
        
        except Exception as e:
            return f"❌ Erro ao processar edição: {e}", None
    
    def _executar_agendamento(
        self,
        agendamento: AgendamentoConfirmacao,
        agenda_module,
        user_id: str
    ) -> Tuple[str, Dict]:
        """Executa o agendamento (cria evento + lembrete)"""
        
        # Usar data/hora confirmada se existir
        data_final = agendamento.data_confirmada or agendamento.data_original
        hora_final = agendamento.hora_confirmada or agendamento.hora_original
        
        evento_id = None
        lembrete_id = None
        
        # Tentar criar evento no módulo de agenda
        try:
            if agenda_module:
                # Criar evento principal
                from uuid import uuid4
                evento_id = str(uuid4())[:8]
                
                evento = {
                    'id': evento_id,
                    'titulo': agendamento.titulo,
                    'data': data_final,
                    'hora': hora_final,
                    'user_id': user_id,
                    'criado_em': datetime.now().isoformat(),
                    'origem': agendamento.origem,
                    'extra': agendamento.extra
                }
                
                # Adicionar aos eventos
                if not hasattr(agenda_module, 'eventos'):
                    agenda_module.eventos = []
                
                agenda_module.eventos.append(evento)
                
                # Criar lembrete automático (2 horas antes)
                lembrete_id = self._criar_lembrete_automatico(
                    agenda_module,
                    agendamento,
                    data_final,
                    hora_final,
                    user_id
                )
                
                # Salvar dados
                if hasattr(agenda_module, '_save_data'):
                    agenda_module._save_data()
        
        except Exception as e:
            print(f"⚠️ Erro ao criar evento: {e}")
        
        # Formatar resposta
        data_fmt = self._formatar_data_exibicao(data_final)
        
        msg = f"""
✅ *AGENDAMENTO CONFIRMADO!*

{'═' * 50}
📌 {agendamento.titulo}
📆 {data_fmt}
⏰ {hora_final}

🔔 Lembrete automático: 2 horas antes
{'═' * 50}

ID do evento: `{evento_id}`
ID do lembrete: `{lembrete_id}`
"""
        
        return msg, {
            'acao': 'agendar',
            'agendamento': agendamento,
            'evento_id': evento_id,
            'lembrete_id': lembrete_id
        }
    
    def _criar_lembrete_automatico(
        self,
        agenda_module,
        agendamento: AgendamentoConfirmacao,
        data: str,
        hora: str,
        user_id: str
    ) -> Optional[str]:
        """Cria lembrete automático 2 horas antes do evento"""
        
        try:
            from uuid import uuid4
            
            # Calcular data_hora do lembrete (2 horas antes)
            data_hora_evento = f"{data}T{hora}:00"
            
            try:
                evento_dt = datetime.fromisoformat(data_hora_evento)
                lembrete_dt = evento_dt - timedelta(hours=2)
                data_hora_lembrete = lembrete_dt.isoformat()
            except:
                # Se erro, usar como está
                data_hora_lembrete = data_hora_evento
            
            lembrete_id = str(uuid4())[:8]
            
            lembrete = {
                'id': lembrete_id,
                'texto': f"⏰ Lembrete: {agendamento.titulo}",
                'data_hora': data_hora_lembrete,
                'user_id': user_id,
                'ativo': True,
                'criado_em': datetime.now().isoformat(),
                'origem': 'agendamento_automatico',
                'evento_id': agendamento.id
            }
            
            # Adicionar aos lembretes
            if not hasattr(agenda_module, 'lembretes'):
                agenda_module.lembretes = []
            
            agenda_module.lembretes.append(lembrete)
            
            return lembrete_id
        
        except Exception as e:
            print(f"⚠️ Erro ao criar lembrete: {e}")
            return None
    
    def listar_pendentes(self, user_id: str) -> str:
        """Lista agendamentos pendentes do usuário"""
        
        if user_id not in self.pendentes:
            return "✅ Nenhum agendamento pendente!"
        
        agendamento = self.pendentes[user_id]
        data_fmt = self._formatar_data_exibicao(agendamento.data_original)
        
        msg = f"""
📅 *AGENDAMENTO PENDENTE DE CONFIRMAÇÃO*

📌 {agendamento.titulo}
📆 {data_fmt}
⏰ {agendamento.hora_original}

Use `/confirmar` para agendar ou `/cancelar` para descartar
"""
        
        return msg
    
    def cancelar_agendamento(self, user_id: str) -> str:
        """Cancela agendamento pendente"""
        
        if user_id not in self.pendentes:
            return "Nenhum agendamento pendente para cancelar."
        
        del self.pendentes[user_id]
        return "❌ Agendamento cancelado."


# Singleton para facilitar uso
_sistema_agendamento = None

def get_sistema_agendamento() -> SistemaAgendamentoAvancado:
    """Retorna instância singleton"""
    global _sistema_agendamento
    if _sistema_agendamento is None:
        _sistema_agendamento = SistemaAgendamentoAvancado()
    return _sistema_agendamento
