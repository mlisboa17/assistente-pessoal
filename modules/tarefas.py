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
        
        # Comando 'nova' ou 'tarefa' - cria tarefa
        if command in ['tarefa', 'nova', 'criar']:
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
        
        # Se chegou aqui, comando não reconhecido - retorna vazio ao invés de mostrar ajuda
        return ""
    
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
        """Cria uma nova tarefa com alarme automático"""
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
        
        # Extrai data limite se houver
        data_limite = ""
        import re
        
        # Procura por "até" ou "para"
        match_data = re.search(r'(até|para|antes de)\s+(\d{1,2}[/\-]\d{1,2}|amanhã|hoje|sexta|segunda|terça|quarta|quinta|sábado|domingo)', texto_lower)
        if match_data:
            data_texto = match_data.group(2)
            try:
                # Converte texto para data
                hoje = datetime.now()
                if data_texto == 'hoje':
                    data_limite = hoje.strftime('%Y-%m-%d')
                elif data_texto == 'amanhã':
                    data_limite = (hoje + timedelta(days=1)).strftime('%Y-%m-%d')
                else:
                    # Tenta parsear data
                    for fmt in ['%d/%m', '%d-%m']:
                        try:
                            data = datetime.strptime(data_texto, fmt)
                            data_limite = data.replace(year=hoje.year).strftime('%Y-%m-%d')
                            break
                        except:
                            pass
            except:
                pass
        
        tarefa = Tarefa(
            id=str(uuid4())[:6],
            titulo=texto[:100],
            descricao=texto,
            prioridade=prioridade,
            status='pendente',
            data_limite=data_limite,
            user_id=user_id,
            criado_em=datetime.now().isoformat()
        )
        
        self.tarefas.append(tarefa.to_dict())
        self._save_data()
        
        # Cria alarme automático se tem data limite
        if data_limite:
            self._criar_alarme_tarefa(user_id, texto, data_limite, tarefa.id, prioridade)
        
        emoji_prio = {'alta': '🔴', 'media': '🟡', 'baixa': '🟢'}
        
        resposta = f"""
✅ *Tarefa Criada!*
━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 *Descrição:*
{texto[:80]}

{emoji_prio[prioridade]} *Prioridade:* {prioridade.upper()}
🔖 *ID:* `{tarefa.id}`
"""
        
        if data_limite:
            data_formatada = datetime.strptime(data_limite, '%Y-%m-%d').strftime('%d/%m/%Y')
            resposta += f"📅 *Prazo:* {data_formatada}\n"
            resposta += f"⏰ *Alarme:* Criado automaticamente!\n"
        
        resposta += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        resposta += f"💡 Use `/concluir {tarefa.id}` quando terminar."
        
        return resposta
    
    def _criar_alarme_tarefa(self, user_id: str, texto: str, data_limite: str, tarefa_id: str, prioridade: str):
        """Cria alarme automático para tarefa com prazo"""
        try:
            from modules.alertas import AlertasModule, Alerta
            
            # Define quando disparar baseado na prioridade
            dt_limite = datetime.strptime(data_limite, '%Y-%m-%d')
            
            if prioridade == 'alta':
                # Alta: 1 dia antes
                dt_alarme = dt_limite - timedelta(days=1)
            else:
                # Média/Baixa: 2 dias antes
                dt_alarme = dt_limite - timedelta(days=2)
            
            # Define horário do alarme (9h da manhã)
            dt_alarme = dt_alarme.replace(hour=9, minute=0, second=0)
            
            if dt_alarme <= datetime.now():
                return
            
            alerta_id = f"task_{tarefa_id}"
            dias_faltam = (dt_limite.date() - datetime.now().date()).days
            
            mensagem = f"""📝 *LEMBRETE DE TAREFA!*

{texto[:80]}

📅 Prazo: {dt_limite.strftime('%d/%m/%Y')}
⏰ Faltam {dias_faltam} dia(s)!
"""
            
            prio_alerta = 3 if prioridade == 'alta' else 2
            
            alerta = Alerta(
                id=alerta_id,
                tipo='lembrete',
                titulo=f"Tarefa: {texto[:30]}",
                mensagem=mensagem,
                prioridade=prio_alerta,
                data_disparo=dt_alarme.isoformat(),
                ativo=True,
                user_id=user_id,
                dados_extra={'tarefa_id': tarefa_id, 'data_limite': data_limite},
                criado_em=datetime.now().isoformat()
            )
            
            alertas_module = AlertasModule(self.data_dir)
            alertas_module.alertas.append(alerta.to_dict())
            alertas_module._save_data()
            
            print(f"[ALARME] Criado para tarefa: {texto[:30]} (prazo: {data_limite})")
        except Exception as e:
            print(f"[ALARME] Erro ao criar alarme de tarefa: {e}")
    
    def _listar_tarefas(self, user_id: str) -> str:
        """Lista tarefas pendentes com prazos e alarmes"""
        pendentes = [
            t for t in self.tarefas
            if t.get('user_id') == user_id and t.get('status') != 'concluida'
        ]
        
        if not pendentes:
            return """
✅ *SUAS TAREFAS*
━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎉 *Nenhuma tarefa pendente!*

💡 *Crie uma nova:*
   • /tarefa comprar material
   • /tarefa ligar cliente até amanhã
   • /tarefa revisar projeto
"""
        
        response = """✅ *SUAS TAREFAS*
━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"""
        
        # Ordena: primeiro por prazo (vencendo), depois por prioridade
        hoje = datetime.now().date()
        
        def ordenar_tarefa(t):
            # Prioriza tarefas com prazo próximo
            data_limite = t.get('data_limite', '')
            if data_limite:
                try:
                    dt = datetime.strptime(data_limite, '%Y-%m-%d').date()
                    dias = (dt - hoje).days
                    return (0, dias)  # Tarefas com prazo primeiro
                except:
                    pass
            
            # Depois por prioridade
            ordem_prio = {'alta': (1, 0), 'media': (1, 1), 'baixa': (1, 2)}
            return ordem_prio.get(t.get('prioridade', 'media'), (1, 1))
        
        pendentes.sort(key=ordenar_tarefa)
        
        emoji_prio = {'alta': '🔴', 'media': '🟡', 'baixa': '🟢'}
        emoji_status = {'pendente': '⬜', 'em_andamento': '🔄'}
        
        for idx, t in enumerate(pendentes, 1):
            prio = t.get('prioridade', 'media')
            status = t.get('status', 'pendente')
            titulo = t.get('titulo', '')[:60]
            id_tarefa = t.get('id', '')
            data_limite = t.get('data_limite', '')
            
            response += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            response += f"{idx}. {emoji_status[status]} {emoji_prio[prio]} *{titulo}*\n"
            response += f"   🔖 ID: `{id_tarefa}`\n"
            
            # Exibe prazo se existir
            if data_limite:
                try:
                    dt_limite = datetime.strptime(data_limite, '%Y-%m-%d')
                    dias_faltam = (dt_limite.date() - hoje).days
                    
                    data_fmt = dt_limite.strftime('%d/%m/%Y')
                    
                    if dias_faltam < 0:
                        response += f"   🔴 *VENCIDA!* (prazo era {data_fmt})\n"
                    elif dias_faltam == 0:
                        response += f"   ⚡ *VENCE HOJE!* ({data_fmt})\n"
                    elif dias_faltam == 1:
                        response += f"   ⚠️ *Vence amanhã!* ({data_fmt})\n"
                    elif dias_faltam <= 3:
                        response += f"   📅 Prazo: {data_fmt} ({dias_faltam} dias)\n"
                    else:
                        response += f"   📅 Prazo: {data_fmt}\n"
                    
                    response += f"   ⏰ Alarme automático ativo\n"
                except:
                    pass
            
            response += "\n"
        
        response += "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        response += f"📊 *Total:* {len(pendentes)} tarefa(s) pendente(s)\n\n"
        response += "💡 Use `/concluir [id]` para marcar como feita."
        
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
