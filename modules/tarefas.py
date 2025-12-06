"""
✅ Módulo de Tarefas
Gerencia lista de tarefas e afazeres
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class Tarefa:
    """Representa uma tarefa"""
    id: str
    titulo: str
    descricao: str = ""
    prioridade: str = "media"  # baixa, media, alta
    status: str = "pendente"  # pendente, em_andamento, concluida
    data_limite: str = ""
    user_id: str = ""
    criado_em: str = ""
    concluido_em: str = ""
    
    def to_dict(self):
        return asdict(self)


class TarefasModule:
    """Gerenciador de Tarefas"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.tarefas_file = os.path.join(data_dir, "tarefas.json")
        
        os.makedirs(data_dir, exist_ok=True)
        self._load_data()
    
    def _load_data(self):
        """Carrega dados do disco"""
        if os.path.exists(self.tarefas_file):
            with open(self.tarefas_file, 'r', encoding='utf-8') as f:
                self.tarefas = json.load(f)
        else:
            self.tarefas = []
    
    def _save_data(self):
        """Salva dados no disco"""
        with open(self.tarefas_file, 'w', encoding='utf-8') as f:
            json.dump(self.tarefas, f, ensure_ascii=False, indent=2)
    
    async def handle(self, command: str, args: List[str], 
                     user_id: str, attachments: list = None) -> str:
        """Processa comandos de tarefas"""
        
        if command == 'tarefa':
            if args:
                return self._criar_tarefa(user_id, ' '.join(args))
            return "✅ Use: /tarefa [descrição da tarefa]"
        
        elif command == 'tarefas':
            return self._listar_tarefas(user_id)
        
        elif command == 'concluir':
            if args:
                return self._concluir_tarefa(user_id, args[0])
            return "✅ Use: /concluir [id da tarefa]"
        
        elif command == 'cancelar':
            if args:
                return self._cancelar_tarefa(user_id, args[0])
            return "❌ Use: /cancelar [id da tarefa]"
        
        elif command == 'remover':
            if args:
                return self._cancelar_tarefa(user_id, args[0])
            return "❌ Use: /remover [id da tarefa]"
        
        elif command == 'todo':
            return self._listar_tarefas(user_id)
        
        return "✅ Comandos: /tarefa, /tarefas, /concluir, /cancelar"
    
    async def handle_natural(self, message: str, analysis: Any,
                              user_id: str, attachments: list = None) -> str:
        """Processa linguagem natural"""
        text_lower = message.lower()
        
        if any(word in text_lower for word in ['criar', 'nova', 'adicionar', 'fazer']):
            # Remove palavras de comando
            texto = message
            for word in ['criar', 'nova', 'adicionar', 'tarefa', 'preciso', 'tenho que']:
                texto = texto.replace(word, '').replace(word.capitalize(), '')
            return self._criar_tarefa(user_id, texto.strip())
        
        if any(word in text_lower for word in ['lista', 'pendente', 'tarefas', 'mostrar']):
            return self._listar_tarefas(user_id)
        
        if any(word in text_lower for word in ['concluí', 'terminei', 'fiz', 'pronto']):
            return self._listar_para_concluir(user_id)
        
        return self._listar_tarefas(user_id)
    
    def _criar_tarefa(self, user_id: str, texto: str) -> str:
        """Cria uma nova tarefa"""
        from uuid import uuid4
        
        if not texto or len(texto) < 3:
            return "❌ Descrição muito curta. Informe o que precisa fazer."
        
        # Detecta prioridade
        prioridade = 'media'
        texto_lower = texto.lower()
        
        if any(word in texto_lower for word in ['urgente', 'importante', 'crítico', 'hoje']):
            prioridade = 'alta'
        elif any(word in texto_lower for word in ['depois', 'quando puder', 'baixa']):
            prioridade = 'baixa'
        
        tarefa = Tarefa(
            id=str(uuid4())[:6],
            titulo=texto[:100],
            descricao=texto,
            prioridade=prioridade,
            status='pendente',
            user_id=user_id,
            criado_em=datetime.now().isoformat()
        )
        
        self.tarefas.append(tarefa.to_dict())
        self._save_data()
        
        emoji_prio = {'alta': '🔴', 'media': '🟡', 'baixa': '🟢'}
        
        return f"""
✅ *Tarefa Criada!*

📝 {texto[:50]}
{emoji_prio[prioridade]} Prioridade: {prioridade.capitalize()}
🔖 ID: `{tarefa.id}`

_Use /concluir {tarefa.id} quando terminar._
"""
    
    def _listar_tarefas(self, user_id: str) -> str:
        """Lista tarefas pendentes"""
        pendentes = [
            t for t in self.tarefas
            if t.get('user_id') == user_id and t.get('status') != 'concluida'
        ]
        
        if not pendentes:
            return """
✅ *Suas Tarefas*

🎉 Nenhuma tarefa pendente!

_Use /tarefa [texto] para criar uma nova._
"""
        
        response = "✅ *Suas Tarefas*\n\n"
        
        # Ordena por prioridade
        ordem = {'alta': 0, 'media': 1, 'baixa': 2}
        pendentes.sort(key=lambda x: ordem.get(x.get('prioridade', 'media'), 1))
        
        emoji_prio = {'alta': '🔴', 'media': '🟡', 'baixa': '🟢'}
        emoji_status = {'pendente': '⬜', 'em_andamento': '🔄'}
        
        for t in pendentes:
            prio = t.get('prioridade', 'media')
            status = t.get('status', 'pendente')
            titulo = t.get('titulo', '')[:40]
            id_tarefa = t.get('id', '')
            
            response += f"{emoji_status[status]} {emoji_prio[prio]} {titulo}\n"
            response += f"   _ID: {id_tarefa}_\n"
        
        response += f"\n📊 Total: {len(pendentes)} tarefa(s)\n"
        response += "\n_Use /concluir [id] para marcar como feita._"
        
        return response
    
    def _concluir_tarefa(self, user_id: str, tarefa_id: str) -> str:
        """Marca tarefa como concluída"""
        for tarefa in self.tarefas:
            if tarefa.get('id') == tarefa_id and tarefa.get('user_id') == user_id:
                tarefa['status'] = 'concluida'
                tarefa['concluido_em'] = datetime.now().isoformat()
                self._save_data()
                
                return f"""
🎉 *Tarefa Concluída!*

✅ {tarefa.get('titulo', '')[:50]}

_Bom trabalho! Continue assim!_ 💪
"""
        
        return f"❌ Tarefa `{tarefa_id}` não encontrada."
    
    def _cancelar_tarefa(self, user_id: str, tarefa_id: str) -> str:
        """Remove/cancela uma tarefa"""
        for i, tarefa in enumerate(self.tarefas):
            if tarefa.get('id') == tarefa_id and tarefa.get('user_id') == user_id:
                titulo = tarefa.get('titulo', '')[:50]
                self.tarefas.pop(i)
                self._save_data()
                
                return f"""
🗑️ *Tarefa Cancelada!*

❌ {titulo}

_A tarefa foi removida da sua lista._
"""
        
        return f"❌ Tarefa `{tarefa_id}` não encontrada."
    
    def _listar_para_concluir(self, user_id: str) -> str:
        """Lista tarefas para marcar como concluídas"""
        pendentes = [
            t for t in self.tarefas
            if t.get('user_id') == user_id and t.get('status') != 'concluida'
        ]
        
        if not pendentes:
            return "🎉 Todas as tarefas já foram concluídas!"
        
        response = "📋 *Qual tarefa você concluiu?*\n\n"
        
        for t in pendentes[:5]:
            response += f"• `{t.get('id')}` - {t.get('titulo', '')[:30]}\n"
        
        response += "\n_Responda com /concluir [id]_"
        
        return response
