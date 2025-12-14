"""
🔔 Módulo de Notificações Agendadas
Gerencia lembretes automáticos via WhatsApp/Telegram
"""
import os
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time


class NotificacoesAgendadas:
    """Gerencia notificações e lembretes agendados"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.notificacoes_file = os.path.join(data_dir, "notificacoes_agendadas.json")
        self.notificacoes: Dict[str, List[Dict]] = {}
        self._load_notificacoes()
        self.thread_monitor = None
        self.ativo = False
    
    def _load_notificacoes(self):
        """Carrega notificações do arquivo"""
        if os.path.exists(self.notificacoes_file):
            try:
                with open(self.notificacoes_file, 'r', encoding='utf-8') as f:
                    self.notificacoes = json.load(f)
            except:
                self.notificacoes = {}
        else:
            self.notificacoes = {}
    
    def _save_notificacoes(self):
        """Salva notificações no arquivo"""
        with open(self.notificacoes_file, 'w', encoding='utf-8') as f:
            json.dump(self.notificacoes, f, ensure_ascii=False, indent=2)
    
    def adicionar_lembrete(self, user_id: str, titulo: str, descricao: str, 
                           data_hora: str, tipo: str = 'evento') -> bool:
        """
        Adiciona um lembrete agendado
        
        Args:
            user_id: ID do usuário
            titulo: Título do lembrete
            descricao: Descrição do lembrete
            data_hora: Data e hora (formato ISO 8601: 2025-12-10T09:00:00)
            tipo: Tipo de lembrete (evento, tarefa, gasto, etc)
        """
        try:
            if user_id not in self.notificacoes:
                self.notificacoes[user_id] = []
            
            lembrete = {
                'id': len(self.notificacoes[user_id]) + 1,
                'titulo': titulo,
                'descricao': descricao,
                'data_hora': data_hora,
                'tipo': tipo,
                'enviado': False,
                'criado_em': datetime.utcnow().isoformat()
            }
            
            self.notificacoes[user_id].append(lembrete)
            self._save_notificacoes()
            return True
        except Exception as e:
            print(f"Erro ao adicionar lembrete: {e}")
            return False
    
    def remover_lembrete(self, user_id: str, lembrete_id: int) -> bool:
        """Remove um lembrete"""
        try:
            if user_id in self.notificacoes:
                self.notificacoes[user_id] = [
                    l for l in self.notificacoes[user_id] if l['id'] != lembrete_id
                ]
                self._save_notificacoes()
                return True
            return False
        except Exception as e:
            print(f"Erro ao remover lembrete: {e}")
            return False
    
    def listar_lembretes(self, user_id: str) -> List[Dict]:
        """Lista todos os lembretes do usuário"""
        return self.notificacoes.get(user_id, [])
    
    def listar_lembretes_proximos(self, user_id: str, dias: int = 7) -> List[Dict]:
        """Lista lembretes dos próximos X dias"""
        lembretes = self.notificacoes.get(user_id, [])
        agora = datetime.utcnow()
        limite = agora + timedelta(days=dias)
        
        proximos = []
        for lembrete in lembretes:
            if not lembrete['enviado']:
                try:
                    dt = datetime.fromisoformat(lembrete['data_hora'].replace('Z', '+00:00'))
                    if agora <= dt <= limite:
                        proximos.append(lembrete)
                except:
                    pass
        
        return sorted(proximos, key=lambda x: x['data_hora'])
    
    def obter_notificacoes_pendentes(self) -> Dict[str, List[Dict]]:
        """
        Obtém todas as notificações que devem ser enviadas agora
        
        Returns:
            Dict com user_id como chave e lista de notificações como valor
        """
        pendentes = {}
        agora = datetime.utcnow()
        
        for user_id, lembretes in self.notificacoes.items():
            for lembrete in lembretes:
                if not lembrete['enviado']:
                    try:
                        dt = datetime.fromisoformat(lembrete['data_hora'].replace('Z', '+00:00'))
                        # Se a hora é agora (±5 minutos)
                        diff = (dt - agora).total_seconds()
                        if -300 <= diff <= 300:  # ±5 minutos
                            if user_id not in pendentes:
                                pendentes[user_id] = []
                            pendentes[user_id].append(lembrete)
                    except:
                        pass
        
        return pendentes
    
    def marcar_enviado(self, user_id: str, lembrete_id: int):
        """Marca um lembrete como enviado"""
        if user_id in self.notificacoes:
            for lembrete in self.notificacoes[user_id]:
                if lembrete['id'] == lembrete_id:
                    lembrete['enviado'] = True
                    lembrete['enviado_em'] = datetime.utcnow().isoformat()
                    self._save_notificacoes()
                    break
    
    def iniciar_monitor(self, callback_notificar=None):
        """Inicia thread de monitoramento de notificações"""
        if self.ativo:
            return
        
        self.ativo = True
        self.thread_monitor = threading.Thread(
            target=self._monitor_notificacoes,
            args=(callback_notificar,),
            daemon=True
        )
        self.thread_monitor.start()
        print("🔔 Monitor de notificações iniciado")
    
    def parar_monitor(self):
        """Para o thread de monitoramento"""
        self.ativo = False
        print("🛑 Monitor de notificações parado")
    
    def _monitor_notificacoes(self, callback_notificar=None):
        """Thread que monitora notificações pendentes"""
        while self.ativo:
            try:
                pendentes = self.obter_notificacoes_pendentes()
                
                for user_id, lembretes in pendentes.items():
                    for lembrete in lembretes:
                        mensagem = self._formatar_notificacao(lembrete)
                        
                        if callback_notificar:
                            callback_notificar(user_id, mensagem)
                        
                        self.marcar_enviado(user_id, lembrete['id'])
                        print(f"📬 Notificação enviada para {user_id}: {lembrete['titulo']}")
                
                # Verifica a cada 30 segundos
                time.sleep(30)
            except Exception as e:
                print(f"Erro no monitor de notificações: {e}")
                time.sleep(30)
    
    def _formatar_notificacao(self, lembrete: Dict) -> str:
        """Formata notificação para envio"""
        emoji_tipo = {
            'evento': '📅',
            'tarefa': '✅',
            'gasto': '💸',
            'boleto': '📄',
            'lembrete': '🔔',
            'meta': '🎯'
        }
        
        emoji = emoji_tipo.get(lembrete['tipo'], '📬')
        return f"""{emoji} *{lembrete['titulo']}*

{lembrete['descricao']}

⏰ Agendado para: {lembrete['data_hora']}"""
    
    def formatar_listagem(self, user_id: str) -> str:
        """Formata listagem de lembretes para exibição"""
        lembretes = self.listar_lembretes_proximos(user_id, dias=30)
        
        if not lembretes:
            return "📭 Nenhum lembrete próximo"
        
        resposta = "🔔 *Seus lembretes agendados:*\n\n"
        
        for l in lembretes[:10]:  # Mostra no máximo 10
            data = datetime.fromisoformat(l['data_hora'].replace('Z', '+00:00'))
            resposta += f"• {l['titulo']} - {data.strftime('%d/%m %H:%M')}\n"
        
        return resposta


# Singleton
_notificacoes: Optional[NotificacoesAgendadas] = None

def get_notificacoes_agendadas(data_dir: str = "data") -> NotificacoesAgendadas:
    """Retorna instância singleton de NotificacoesAgendadas"""
    global _notificacoes
    if _notificacoes is None:
        _notificacoes = NotificacoesAgendadas(data_dir)
    return _notificacoes
