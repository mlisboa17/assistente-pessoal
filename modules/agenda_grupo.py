"""
👥 Módulo de Agenda de Grupo
Gerencia eventos e compromissos compartilhados para grupos do WhatsApp
Armazenamento local (sem custos)
"""
import json
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from uuid import uuid4


@dataclass
class EventoGrupo:
    """Evento compartilhado do grupo"""
    id: str
    titulo: str
    descricao: str = ""
    data: str = ""          # YYYY-MM-DD
    hora: str = ""          # HH:MM
    duracao_min: int = 60
    local: str = ""
    criado_por: str = ""    # user_id
    criado_por_nome: str = ""
    grupo_id: str = ""
    grupo_nome: str = ""
    participantes: List[str] = None  # Lista de user_ids confirmados
    lembrete_enviado: bool = False
    criado_em: str = ""
    
    def __post_init__(self):
        if self.participantes is None:
            self.participantes = []
    
    def to_dict(self):
        d = asdict(self)
        d['participantes'] = list(self.participantes) if self.participantes else []
        return d


@dataclass
class TarefaGrupo:
    """Tarefa compartilhada do grupo"""
    id: str
    titulo: str
    descricao: str = ""
    responsavel: str = ""        # user_id responsável
    responsavel_nome: str = ""
    prazo: str = ""              # YYYY-MM-DD
    status: str = "pendente"     # pendente, em_andamento, concluida
    prioridade: str = "normal"   # baixa, normal, alta, urgente
    criado_por: str = ""
    criado_por_nome: str = ""
    grupo_id: str = ""
    grupo_nome: str = ""
    criado_em: str = ""
    concluido_em: str = ""
    
    def to_dict(self):
        return asdict(self)


class AgendaGrupoModule:
    """Gerenciador de Agenda de Grupos"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.grupos_agenda_dir = os.path.join(data_dir, "grupos_agenda")
        
        os.makedirs(self.grupos_agenda_dir, exist_ok=True)
        
        # Pendências de configuração de grupo
        self._pendencias_config: Dict[str, Dict] = {}
    
    def _get_grupo_file(self, grupo_id: str) -> str:
        """Retorna caminho do arquivo de agenda do grupo"""
        safe_id = re.sub(r'[^\w\-]', '_', grupo_id)
        return os.path.join(self.grupos_agenda_dir, f"agenda_{safe_id}.json")
    
    def _load_grupo_data(self, grupo_id: str) -> Dict:
        """Carrega dados do grupo"""
        filepath = self._get_grupo_file(grupo_id)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None  # Retorna None se não existe
    
    def _criar_grupo_data(self, grupo_id: str, grupo_nome: str, admin_id: str, admin_nome: str) -> Dict:
        """Cria dados iniciais do grupo"""
        return {
            "grupo_id": grupo_id,
            "grupo_nome": grupo_nome,
            "admin_master": admin_id,
            "admin_master_nome": admin_nome,
            "eventos": [],
            "tarefas": [],
            "configuracoes": {
                "ativo": True,
                "lembrete_antecedencia_min": 30,
                "admins": [admin_id],
                "todos_podem_criar": True,
                "compartilhar_agenda_pessoal": False  # Por padrão NÃO compartilha
            },
            "criado_em": datetime.now().isoformat()
        }
    
    def grupo_existe(self, grupo_id: str) -> bool:
        """Verifica se grupo já foi configurado"""
        return self._load_grupo_data(grupo_id) is not None
    
    def is_admin(self, grupo_id: str, user_id: str) -> bool:
        """Verifica se usuário é admin do grupo"""
        data = self._load_grupo_data(grupo_id)
        if not data:
            return False
        return user_id in data.get('configuracoes', {}).get('admins', [])
    
    def get_admin_master(self, grupo_id: str) -> Optional[str]:
        """Retorna o admin master do grupo"""
        data = self._load_grupo_data(grupo_id)
        if data:
            return data.get('admin_master')
        return None
    
    def _save_grupo_data(self, grupo_id: str, data: Dict):
        """Salva dados do grupo"""
        filepath = self._get_grupo_file(grupo_id)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _gerar_id(self) -> str:
        """Gera ID único"""
        return str(uuid4())[:8]
    
    def _parse_data(self, texto: str) -> Optional[str]:
        """Extrai data do texto"""
        hoje = datetime.now()
        texto_lower = texto.lower()
        
        # Datas relativas
        if 'hoje' in texto_lower:
            return hoje.strftime('%Y-%m-%d')
        if 'amanha' in texto_lower or 'amanhã' in texto_lower:
            return (hoje + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Dias da semana
        dias_semana = {
            'segunda': 0, 'terça': 1, 'terca': 1, 'quarta': 2,
            'quinta': 3, 'sexta': 4, 'sábado': 5, 'sabado': 5, 'domingo': 6
        }
        for dia, num in dias_semana.items():
            if dia in texto_lower:
                dias_ate = (num - hoje.weekday()) % 7
                if dias_ate == 0:
                    dias_ate = 7
                return (hoje + timedelta(days=dias_ate)).strftime('%Y-%m-%d')
        
        # Formato DD/MM ou DD/MM/YYYY
        match = re.search(r'(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?', texto)
        if match:
            dia = int(match.group(1))
            mes = int(match.group(2))
            ano = int(match.group(3)) if match.group(3) else hoje.year
            if ano < 100:
                ano += 2000
            try:
                return datetime(ano, mes, dia).strftime('%Y-%m-%d')
            except:
                pass
        
        return None
    
    def _parse_hora(self, texto: str) -> Optional[str]:
        """Extrai hora do texto"""
        # Formato HH:MM ou HHh ou HH horas
        match = re.search(r'(\d{1,2})(?::(\d{2})|\s*h(?:oras?)?)', texto.lower())
        if match:
            hora = int(match.group(1))
            minuto = int(match.group(2)) if match.group(2) else 0
            if 0 <= hora <= 23 and 0 <= minuto <= 59:
                return f"{hora:02d}:{minuto:02d}"
        
        return None
    
    # ==================== EVENTOS ====================
    
    def criar_evento(self, grupo_id: str, grupo_nome: str, titulo: str,
                     data: str = None, hora: str = None, descricao: str = "",
                     local: str = "", criado_por: str = "", criado_por_nome: str = "") -> Dict:
        """Cria novo evento no grupo"""
        evento = EventoGrupo(
            id=self._gerar_id(),
            titulo=titulo,
            descricao=descricao,
            data=data or "",
            hora=hora or "",
            local=local,
            criado_por=criado_por,
            criado_por_nome=criado_por_nome,
            grupo_id=grupo_id,
            grupo_nome=grupo_nome,
            participantes=[criado_por] if criado_por else [],
            criado_em=datetime.now().isoformat()
        )
        
        data_grupo = self._load_grupo_data(grupo_id)
        if not data_grupo:
            return None  # Grupo não existe
        data_grupo['grupo_nome'] = grupo_nome
        data_grupo['eventos'].append(evento.to_dict())
        self._save_grupo_data(grupo_id, data_grupo)
        
        return evento.to_dict()
    
    def listar_eventos(self, grupo_id: str, apenas_futuros: bool = True) -> List[Dict]:
        """Lista eventos do grupo"""
        data = self._load_grupo_data(grupo_id)
        if not data:
            return []
        eventos = data.get('eventos', [])
        
        if apenas_futuros:
            hoje = datetime.now().strftime('%Y-%m-%d')
            eventos = [e for e in eventos if e.get('data', '') >= hoje or not e.get('data')]
        
        # Ordena por data
        eventos.sort(key=lambda e: (e.get('data', '9999-99-99'), e.get('hora', '99:99')))
        return eventos
    
    def confirmar_participacao(self, grupo_id: str, evento_id: str, user_id: str) -> bool:
        """Confirma participação em evento"""
        data = self._load_grupo_data(grupo_id)
        if not data:
            return False
        
        for evento in data.get('eventos', []):
            if evento['id'] == evento_id:
                if user_id not in evento.get('participantes', []):
                    evento.setdefault('participantes', []).append(user_id)
                    self._save_grupo_data(grupo_id, data)
                return True
        
        return False
    
    def cancelar_evento(self, grupo_id: str, evento_id: str, user_id: str) -> bool:
        """Cancela evento (apenas criador)"""
        data = self._load_grupo_data(grupo_id)
        if not data:
            return False
        
        for i, evento in enumerate(data.get('eventos', [])):
            if evento['id'] == evento_id:
                if evento.get('criado_por') == user_id:
                    data['eventos'].pop(i)
                    self._save_grupo_data(grupo_id, data)
                    return True
        
        return False
    
    # ==================== TAREFAS ====================
    
    def criar_tarefa(self, grupo_id: str, grupo_nome: str, titulo: str,
                     prazo: str = None, responsavel: str = "", responsavel_nome: str = "",
                     descricao: str = "", prioridade: str = "normal",
                     criado_por: str = "", criado_por_nome: str = "") -> Dict:
        """Cria nova tarefa no grupo"""
        tarefa = TarefaGrupo(
            id=self._gerar_id(),
            titulo=titulo,
            descricao=descricao,
            responsavel=responsavel,
            responsavel_nome=responsavel_nome,
            prazo=prazo or "",
            prioridade=prioridade,
            criado_por=criado_por,
            criado_por_nome=criado_por_nome,
            grupo_id=grupo_id,
            grupo_nome=grupo_nome,
            criado_em=datetime.now().isoformat()
        )
        
        data = self._load_grupo_data(grupo_id)
        if not data:
            return None  # Grupo não existe
        data['grupo_nome'] = grupo_nome
        data['tarefas'].append(tarefa.to_dict())
        self._save_grupo_data(grupo_id, data)
        
        return tarefa.to_dict()
    
    def listar_tarefas(self, grupo_id: str, apenas_pendentes: bool = True) -> List[Dict]:
        """Lista tarefas do grupo"""
        data = self._load_grupo_data(grupo_id)
        if data is None:
            return []
        
        tarefas = data.get('tarefas', [])
        
        if apenas_pendentes:
            tarefas = [t for t in tarefas if t.get('status') != 'concluida']
        
        # Ordena por prazo e prioridade
        prioridades = {'urgente': 0, 'alta': 1, 'normal': 2, 'baixa': 3}
        tarefas.sort(key=lambda t: (
            t.get('prazo', '9999-99-99'),
            prioridades.get(t.get('prioridade', 'normal'), 2)
        ))
        return tarefas
    
    def concluir_tarefa(self, grupo_id: str, tarefa_id: str, user_id: str) -> bool:
        """Marca tarefa como concluída"""
        data = self._load_grupo_data(grupo_id)
        if data is None:
            return False
        
        for tarefa in data.get('tarefas', []):
            if tarefa['id'] == tarefa_id:
                tarefa['status'] = 'concluida'
                tarefa['concluido_em'] = datetime.now().isoformat()
                self._save_grupo_data(grupo_id, data)
                return True
        
        return False
    
    # ==================== COMANDOS ====================
    
    async def handle(self, command: str, args: List[str], 
                     user_id: str, user_name: str,
                     grupo_id: str, grupo_nome: str) -> str:
        """Processa comandos de agenda de grupo"""
        
        # Verifica se há pendência de configuração
        resposta_pendencia = self._processar_pendencia(grupo_id, user_id, user_name, command, args)
        if resposta_pendencia:
            return resposta_pendencia
        
        # Se grupo não está configurado, pergunta se quer criar
        if not self.grupo_existe(grupo_id):
            return self._perguntar_criar_agenda(grupo_id, grupo_nome, user_id, user_name)
        
        # Comandos normais
        if command in ['agenda', 'eventos']:
            return self._formatar_eventos(grupo_id, grupo_nome)
        
        elif command in ['tarefas', 'tasks']:
            return self._formatar_tarefas(grupo_id, grupo_nome)
        
        elif command in ['criar_evento', 'evento', 'agendar']:
            if args:
                texto = ' '.join(args)
                return self._criar_evento_natural(grupo_id, grupo_nome, texto, user_id, user_name)
            return "❌ Use: *evento [título] [data] [hora]*\n\nEx: evento Reunião sexta 15h"
        
        elif command in ['criar_tarefa', 'tarefa', 'task']:
            if args:
                texto = ' '.join(args)
                return self._criar_tarefa_natural(grupo_id, grupo_nome, texto, user_id, user_name)
            return "❌ Use: *tarefa [título] [prazo]*\n\nEx: tarefa Enviar relatório até sexta"
        
        elif command in ['concluir', 'feito', 'done']:
            if args:
                tarefa_id = args[0]
                if self.concluir_tarefa(grupo_id, tarefa_id, user_id):
                    return f"✅ Tarefa *{tarefa_id}* concluída!"
                return "❌ Tarefa não encontrada."
            return "❌ Use: *concluir [id_tarefa]*"
        
        elif command in ['confirmar', 'vou']:
            if args:
                evento_id = args[0]
                if self.confirmar_participacao(grupo_id, evento_id, user_id):
                    return f"✅ Participação confirmada!"
                return "❌ Evento não encontrado."
            return "❌ Use: *confirmar [id_evento]*"
        
        elif command == 'grupo':
            return self._menu_grupo(grupo_nome)
        
        return self._menu_grupo(grupo_nome)
    
    # ==================== CONFIGURAÇÃO DE GRUPO ====================
    
    def _perguntar_criar_agenda(self, grupo_id: str, grupo_nome: str, 
                                 user_id: str, user_name: str) -> str:
        """Pergunta se quer criar agenda para o grupo"""
        # Salva pendência
        self._pendencias_config[grupo_id] = {
            'etapa': 'criar_agenda',
            'grupo_nome': grupo_nome,
            'iniciado_por': user_id,
            'iniciado_por_nome': user_name,
            'criado_em': datetime.now().isoformat()
        }
        
        return f"""👥 *Olá! Sou o Assistente do Grupo*
_{grupo_nome}_

━━━━━━━━━━━━━━━━━━━━━

📌 Este grupo ainda não tem uma agenda configurada.

Posso criar uma *agenda exclusiva* para este grupo com:
• 📅 Eventos compartilhados
• ✅ Tarefas do grupo
• 🔔 Lembretes para todos

━━━━━━━━━━━━━━━━━━━━━

⚠️ *Importante:*
• A agenda do grupo é *separada* das agendas pessoais
• Não tenho acesso a emails ou dados pessoais
• Apenas eventos criados aqui ficam visíveis

━━━━━━━━━━━━━━━━━━━━━

*Deseja criar a agenda do grupo?*

✅ Digite *SIM* para criar
❌ Digite *NÃO* para cancelar"""
    
    def _processar_pendencia(self, grupo_id: str, user_id: str, user_name: str,
                              command: str, args: List[str]) -> Optional[str]:
        """Processa pendências de configuração do grupo"""
        if grupo_id not in self._pendencias_config:
            return None
        
        pendencia = self._pendencias_config[grupo_id]
        etapa = pendencia.get('etapa')
        resposta_lower = command.lower().strip()
        
        # Etapa 1: Criar agenda
        if etapa == 'criar_agenda':
            if resposta_lower in ['sim', 's', 'yes', 'y', 'ok', 'criar']:
                # Passa para próxima etapa: escolher admin
                self._pendencias_config[grupo_id]['etapa'] = 'escolher_admin'
                self._pendencias_config[grupo_id]['criador'] = user_id
                self._pendencias_config[grupo_id]['criador_nome'] = user_name
                
                return f"""✅ *Ótimo! Vamos configurar a agenda.*

━━━━━━━━━━━━━━━━━━━━━

👑 *Quem será o Administrador Master?*

O Admin Master pode:
• Editar/excluir qualquer evento
• Adicionar outros admins
• Alterar configurações do grupo

━━━━━━━━━━━━━━━━━━━━━

*Opções:*

1️⃣ Digite *EU* para ser você ({user_name})
2️⃣ Digite *@nome* de outro membro
3️⃣ Digite *TODOS* para todos serem admins"""
            
            elif resposta_lower in ['nao', 'não', 'n', 'no', 'cancelar']:
                del self._pendencias_config[grupo_id]
                return "👍 Ok, não criei a agenda. Digite *grupo* quando quiser configurar."
            
            return None  # Não era resposta válida
        
        # Etapa 2: Escolher admin
        elif etapa == 'escolher_admin':
            admin_id = user_id
            admin_nome = user_name
            todos_admin = False
            
            if resposta_lower in ['eu', 'eu mesmo', 'me', '1']:
                admin_id = user_id
                admin_nome = user_name
            elif resposta_lower in ['todos', 'all', '3']:
                todos_admin = True
            elif resposta_lower.startswith('@'):
                # Usa o nome mencionado (simplificado)
                admin_nome = resposta_lower[1:]
                # Em produção, validaria se o usuário existe no grupo
            
            # Cria o grupo
            grupo_nome = pendencia.get('grupo_nome', 'Grupo')
            data = self._criar_grupo_data(grupo_id, grupo_nome, admin_id, admin_nome)
            
            if todos_admin:
                data['configuracoes']['todos_podem_criar'] = True
                data['configuracoes']['admins'] = []  # Vazio = todos
            
            self._save_grupo_data(grupo_id, data)
            del self._pendencias_config[grupo_id]
            
            admin_info = "todos os membros" if todos_admin else f"*{admin_nome}*"
            
            return f"""🎉 *Agenda do Grupo Criada!*
_{grupo_nome}_

━━━━━━━━━━━━━━━━━━━━━

👑 *Admin Master:* {admin_info}

━━━━━━━━━━━━━━━━━━━━━

📌 *Comandos disponíveis:*

📅 *agenda* → Ver eventos
📝 *evento [título] [data]* → Criar evento
✅ *tarefas* → Ver tarefas
📋 *tarefa [título]* → Criar tarefa

━━━━━━━━━━━━━━━━━━━━━

💡 _Exemplo: evento Reunião sexta 15h_"""
        
        return None
    
    def _menu_grupo(self, grupo_nome: str) -> str:
        """Menu de comandos do grupo"""
        return f"""👥 *Agenda do Grupo*
_{grupo_nome}_

━━━━━━━━━━━━━━━━━━━━━

📅 *Eventos:*
• *agenda* → Ver eventos
• *evento [título] [data] [hora]* → Criar
• *confirmar [id]* → Confirmar presença

✅ *Tarefas:*
• *tarefas* → Ver tarefas pendentes
• *tarefa [título] [prazo]* → Criar
• *concluir [id]* → Marcar como feita

━━━━━━━━━━━━━━━━━━━━━

💡 _Exemplos:_
• evento Reunião sexta 15h
• tarefa Enviar relatório amanhã"""
    
    def _formatar_eventos(self, grupo_id: str, grupo_nome: str) -> str:
        """Formata lista de eventos"""
        eventos = self.listar_eventos(grupo_id)
        
        if not eventos:
            return f"""📅 *Agenda do Grupo*
_{grupo_nome}_

Nenhum evento agendado.

💡 Crie um: *evento [título] [data] [hora]*"""
        
        texto = f"📅 *Próximos Eventos*\n_{grupo_nome}_\n\n"
        
        for e in eventos[:10]:
            data = e.get('data', '')
            hora = e.get('hora', '')
            
            if data:
                try:
                    dt = datetime.strptime(data, '%Y-%m-%d')
                    data_fmt = dt.strftime('%d/%m')
                except:
                    data_fmt = data
            else:
                data_fmt = "A definir"
            
            texto += f"🔹 *{e['titulo']}*\n"
            texto += f"   📆 {data_fmt}"
            if hora:
                texto += f" às {hora}"
            texto += f"\n   ID: `{e['id']}`\n"
            
            num_participantes = len(e.get('participantes', []))
            if num_participantes:
                texto += f"   👥 {num_participantes} confirmado(s)\n"
            texto += "\n"
        
        texto += "━━━━━━━━━━━━━━━━━━━━━\n"
        texto += "💡 _confirmar [id]_ para participar"
        return texto
    
    def _formatar_tarefas(self, grupo_id: str, grupo_nome: str) -> str:
        """Formata lista de tarefas"""
        tarefas = self.listar_tarefas(grupo_id)
        
        if not tarefas:
            return f"""✅ *Tarefas do Grupo*
_{grupo_nome}_

Nenhuma tarefa pendente! 🎉

💡 Crie uma: *tarefa [título] [prazo]*"""
        
        texto = f"✅ *Tarefas Pendentes*\n_{grupo_nome}_\n\n"
        
        icones_prioridade = {'urgente': '🔴', 'alta': '🟠', 'normal': '🟡', 'baixa': '🟢'}
        
        for t in tarefas[:10]:
            icone = icones_prioridade.get(t.get('prioridade', 'normal'), '🟡')
            texto += f"{icone} *{t['titulo']}*\n"
            
            if t.get('prazo'):
                try:
                    dt = datetime.strptime(t['prazo'], '%Y-%m-%d')
                    prazo_fmt = dt.strftime('%d/%m')
                except:
                    prazo_fmt = t['prazo']
                texto += f"   📅 Prazo: {prazo_fmt}\n"
            
            if t.get('responsavel_nome'):
                texto += f"   👤 {t['responsavel_nome']}\n"
            
            texto += f"   ID: `{t['id']}`\n\n"
        
        texto += "━━━━━━━━━━━━━━━━━━━━━\n"
        texto += "💡 _concluir [id]_ para finalizar"
        return texto
    
    def _criar_evento_natural(self, grupo_id: str, grupo_nome: str, texto: str,
                               user_id: str, user_name: str) -> str:
        """Cria evento a partir de texto natural"""
        data = self._parse_data(texto)
        hora = self._parse_hora(texto)
        
        # Remove data/hora do título
        titulo = texto
        if data:
            titulo = re.sub(r'\d{1,2}/\d{1,2}(?:/\d{2,4})?', '', titulo)
            titulo = re.sub(r'(hoje|amanha|amanhã|segunda|terça|terca|quarta|quinta|sexta|sábado|sabado|domingo)', '', titulo, flags=re.IGNORECASE)
        if hora:
            titulo = re.sub(r'\d{1,2}(?::\d{2})?\s*h(?:oras?)?', '', titulo, flags=re.IGNORECASE)
        
        titulo = titulo.strip()
        if not titulo:
            titulo = "Evento"
        
        evento = self.criar_evento(
            grupo_id=grupo_id,
            grupo_nome=grupo_nome,
            titulo=titulo,
            data=data,
            hora=hora,
            criado_por=user_id,
            criado_por_nome=user_name
        )
        
        resposta = f"✅ *Evento criado!*\n\n"
        resposta += f"📌 *{titulo}*\n"
        if data:
            try:
                dt = datetime.strptime(data, '%Y-%m-%d')
                resposta += f"📆 {dt.strftime('%d/%m/%Y')}"
            except:
                resposta += f"📆 {data}"
        if hora:
            resposta += f" às {hora}"
        resposta += f"\n\n👤 Criado por {user_name}"
        resposta += f"\n🆔 ID: `{evento['id']}`"
        resposta += f"\n\n💡 Participantes podem digitar: *confirmar {evento['id']}*"
        
        return resposta
    
    def _criar_tarefa_natural(self, grupo_id: str, grupo_nome: str, texto: str,
                               user_id: str, user_name: str) -> str:
        """Cria tarefa a partir de texto natural"""
        prazo = self._parse_data(texto)
        
        # Remove prazo do título
        titulo = texto
        if prazo:
            titulo = re.sub(r'\d{1,2}/\d{1,2}(?:/\d{2,4})?', '', titulo)
            titulo = re.sub(r'(ate|até|para|prazo)', '', titulo, flags=re.IGNORECASE)
            titulo = re.sub(r'(hoje|amanha|amanhã|segunda|terça|terca|quarta|quinta|sexta|sábado|sabado|domingo)', '', titulo, flags=re.IGNORECASE)
        
        titulo = titulo.strip()
        if not titulo:
            titulo = "Tarefa"
        
        tarefa = self.criar_tarefa(
            grupo_id=grupo_id,
            grupo_nome=grupo_nome,
            titulo=titulo,
            prazo=prazo,
            criado_por=user_id,
            criado_por_nome=user_name
        )
        
        resposta = f"✅ *Tarefa criada!*\n\n"
        resposta += f"📌 *{titulo}*\n"
        if prazo:
            try:
                dt = datetime.strptime(prazo, '%Y-%m-%d')
                resposta += f"📆 Prazo: {dt.strftime('%d/%m/%Y')}\n"
            except:
                resposta += f"📆 Prazo: {prazo}\n"
        resposta += f"\n👤 Criado por {user_name}"
        resposta += f"\n🆔 ID: `{tarefa['id']}`"
        resposta += f"\n\n💡 Para concluir: *concluir {tarefa['id']}*"
        
        return resposta


# Singleton
_agenda_grupo: Optional[AgendaGrupoModule] = None

def get_agenda_grupo(data_dir: str = "data") -> AgendaGrupoModule:
    """Retorna instância singleton"""
    global _agenda_grupo
    if _agenda_grupo is None:
        _agenda_grupo = AgendaGrupoModule(data_dir)
    return _agenda_grupo
