"""
🔄 Conversation Flow Manager
Gerencia contexto de conversas multi-turn baseado no padrão Microsoft BotBuilder
"""
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json
import os


@dataclass
class ConversationStep:
    """Representa um passo em uma conversa multi-turn"""
    question: str  # 'none', 'name', 'valor', 'descricao', 'categoria', etc
    asked_at: str = ""
    attempts: int = 0
    max_attempts: int = 3
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversationFlow:
    """Gerencia o fluxo de uma conversa"""
    user_id: str
    flow_type: str = "none"  # 'expense', 'income', 'transfer', 'event', etc
    current_step: str = "none"
    started_at: str = ""
    expires_at: str = ""
    
    # Dados coletados durante a conversa
    collected_data: Dict[str, Any] = field(default_factory=dict)
    
    # Histórico de passos
    steps_history: List[ConversationStep] = field(default_factory=list)
    
    # Flags de estado
    is_active: bool = False
    is_completed: bool = False
    requires_confirmation: bool = False
    
    # Contexto adicional
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConversationFlowManager:
    """Gerenciador de fluxos de conversação"""
    
    def __init__(self, storage_path: str = "data/conversation_flows.json"):
        self.storage_path = storage_path
        self.active_flows: Dict[str, ConversationFlow] = {}
        self._load_flows()
    
    def _load_flows(self):
        """Carrega fluxos salvos"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for user_id, flow_data in data.items():
                        flow = ConversationFlow(**flow_data)
                        # Apenas carrega fluxos ativos e não expirados
                        if flow.is_active and not self._is_expired(flow):
                            self.active_flows[user_id] = flow
        except Exception as e:
            print(f"⚠️ Erro ao carregar fluxos: {e}")
    
    def _save_flows(self):
        """Salva fluxos ativos"""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            data = {uid: asdict(flow) for uid, flow in self.active_flows.items()}
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Erro ao salvar fluxos: {e}")
    
    def _is_expired(self, flow: ConversationFlow) -> bool:
        """Verifica se o fluxo expirou (30 minutos de inatividade)"""
        if not flow.expires_at:
            return False
        try:
            expires = datetime.fromisoformat(flow.expires_at)
            return datetime.now() > expires
        except:
            return False
    
    def start_flow(self, user_id: str, flow_type: str, initial_data: Dict[str, Any] = None) -> ConversationFlow:
        """Inicia um novo fluxo de conversa"""
        now = datetime.now()
        expires = now + timedelta(minutes=30)
        
        flow = ConversationFlow(
            user_id=user_id,
            flow_type=flow_type,
            started_at=now.isoformat(),
            expires_at=expires.isoformat(),
            is_active=True,
            collected_data=initial_data or {},
            metadata={'created_at': now.isoformat()}
        )
        
        self.active_flows[user_id] = flow
        self._save_flows()
        return flow
    
    def get_active_flow(self, user_id: str) -> Optional[ConversationFlow]:
        """Retorna o fluxo ativo do usuário"""
        flow = self.active_flows.get(user_id)
        if flow and self._is_expired(flow):
            self.cancel_flow(user_id)
            return None
        return flow
    
    def update_step(self, user_id: str, step: str, data: Any = None):
        """Atualiza o passo atual da conversa"""
        flow = self.get_active_flow(user_id)
        if not flow:
            return
        
        # Adiciona ao histórico
        step_obj = ConversationStep(
            question=step,
            asked_at=datetime.now().isoformat(),
            context={'data': data} if data else {}
        )
        flow.steps_history.append(step_obj)
        
        # Atualiza passo atual
        flow.current_step = step
        
        # Renova expiração
        flow.expires_at = (datetime.now() + timedelta(minutes=30)).isoformat()
        
        self._save_flows()
    
    def collect_data(self, user_id: str, key: str, value: Any):
        """Coleta um dado durante a conversa"""
        flow = self.get_active_flow(user_id)
        if flow:
            flow.collected_data[key] = value
            self._save_flows()
    
    def get_collected_data(self, user_id: str) -> Dict[str, Any]:
        """Retorna todos os dados coletados"""
        flow = self.get_active_flow(user_id)
        return flow.collected_data if flow else {}
    
    def complete_flow(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Completa o fluxo e retorna os dados coletados"""
        flow = self.get_active_flow(user_id)
        if not flow:
            return None
        
        flow.is_active = False
        flow.is_completed = True
        data = flow.collected_data.copy()
        
        # Remove do cache ativo
        self.active_flows.pop(user_id, None)
        self._save_flows()
        
        return data
    
    def cancel_flow(self, user_id: str):
        """Cancela o fluxo atual"""
        if user_id in self.active_flows:
            self.active_flows.pop(user_id)
            self._save_flows()
    
    def is_in_flow(self, user_id: str, flow_type: str = None) -> bool:
        """Verifica se usuário está em um fluxo"""
        flow = self.get_active_flow(user_id)
        if not flow:
            return False
        if flow_type:
            return flow.flow_type == flow_type
        return True
    
    def get_current_step(self, user_id: str) -> str:
        """Retorna o passo atual"""
        flow = self.get_active_flow(user_id)
        return flow.current_step if flow else "none"
    
    def increment_attempts(self, user_id: str) -> int:
        """Incrementa tentativas do passo atual"""
        flow = self.get_active_flow(user_id)
        if not flow or not flow.steps_history:
            return 0
        
        current_step = flow.steps_history[-1]
        current_step.attempts += 1
        self._save_flows()
        return current_step.attempts


# Instância global
_flow_manager = None

def get_flow_manager() -> ConversationFlowManager:
    """Retorna instância única do gerenciador"""
    global _flow_manager
    if _flow_manager is None:
        _flow_manager = ConversationFlowManager()
    return _flow_manager
