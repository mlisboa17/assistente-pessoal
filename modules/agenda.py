"""
📅 Módulo de Agenda
Gerencia compromissos, lembretes e calendário
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class Evento:
    """Representa um evento/compromisso"""
    id: str
    titulo: str
    descricao: str = ""
    data: str = ""  # ISO format
    hora: str = ""
    duracao_min: int = 60
    lembrete_min: int = 30
    recorrente: bool = False
    user_id: str = ""
    criado_em: str = ""
    
    def to_dict(self):
        return asdict(self)


@dataclass
class Lembrete:
    """Representa um lembrete"""
    id: str
    texto: str
    data_hora: str  # ISO format
    user_id: str
    ativo: bool = True
    criado_em: str = ""
    
    def to_dict(self):
        return asdict(self)


class AgendaModule:
    """Gerenciador de Agenda"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.eventos_file = os.path.join(data_dir, "eventos.json")
        self.lembretes_file = os.path.join(data_dir, "lembretes.json")
        
        os.makedirs(data_dir, exist_ok=True)
        self._load_data()
    
    def _load_data(self):
        """Carrega dados do disco"""
        # Eventos
        if os.path.exists(self.eventos_file):
            with open(self.eventos_file, 'r', encoding='utf-8') as f:
                self.eventos = json.load(f)
        else:
            self.eventos = []
        
        # Lembretes
        if os.path.exists(self.lembretes_file):
            with open(self.lembretes_file, 'r', encoding='utf-8') as f:
                self.lembretes = json.load(f)
        else:
            self.lembretes = []
    
    def _save_data(self):
        """Salva dados no disco"""
        with open(self.eventos_file, 'w', encoding='utf-8') as f:
            json.dump(self.eventos, f, ensure_ascii=False, indent=2)
        
        with open(self.lembretes_file, 'w', encoding='utf-8') as f:
            json.dump(self.lembretes, f, ensure_ascii=False, indent=2)
    
    async def handle(self, command: str, args: List[str], 
                     user_id: str, attachments: list = None) -> str:
        """
        Processa comandos de agenda
        
        Args:
            command: Comando (agenda, lembrete, etc)
            args: Argumentos do comando
            user_id: ID do usuário
            attachments: Anexos (não usado)
            
        Returns:
            Resposta formatada
        """
        if command == 'agenda':
            return self._get_agenda(user_id)
        
        elif command == 'lembrete':
            if args:
                return self._criar_lembrete(user_id, ' '.join(args))
            return "📝 Use: /lembrete [texto] [hora]\nExemplo: /lembrete Reunião às 14h"
        
        elif command == 'compromissos':
            return self._get_compromissos(user_id)
        
        elif command == 'lembretes':
            return self._get_lembretes(user_id)
        
        return "📅 Comandos de agenda: /agenda, /lembrete, /compromissos"
    
    async def handle_natural(self, message: str, analysis: Any,
                              user_id: str, attachments: list = None) -> str:
        """Processa linguagem natural"""
        text_lower = message.lower()
        
        # Detecta ação
        if any(word in text_lower for word in ['lembrar', 'lembrete', 'avisar']):
            return self._criar_lembrete(user_id, message)
        
        if any(word in text_lower for word in ['marcar', 'agendar', 'reunião']):
            return self._criar_evento(user_id, message, analysis)
        
        if any(word in text_lower for word in ['compromisso', 'agenda', 'hoje']):
            return self._get_agenda(user_id)
        
        return self._get_agenda(user_id)
    
    def _get_agenda(self, user_id: str) -> str:
        """Retorna agenda do dia"""
        hoje = datetime.now().strftime('%Y-%m-%d')
        
        # Filtra eventos do usuário para hoje
        eventos_hoje = [
            e for e in self.eventos 
            if e.get('user_id') == user_id and e.get('data') == hoje
        ]
        
        # Filtra lembretes do usuário para hoje
        lembretes_hoje = [
            l for l in self.lembretes 
            if l.get('user_id') == user_id and l.get('ativo') 
            and l.get('data_hora', '').startswith(hoje)
        ]
        
        if not eventos_hoje and not lembretes_hoje:
            return f"""
📅 *Agenda de Hoje* ({datetime.now().strftime('%d/%m/%Y')})

📭 Nenhum compromisso para hoje.

_Use /lembrete para criar um lembrete._
"""
        
        response = f"📅 *Agenda de Hoje* ({datetime.now().strftime('%d/%m/%Y')})\n\n"
        
        if eventos_hoje:
            response += "*Compromissos:*\n"
            for evento in sorted(eventos_hoje, key=lambda x: x.get('hora', '')):
                hora = evento.get('hora', '--:--')
                titulo = evento.get('titulo', 'Sem título')
                response += f"  ⏰ {hora} - {titulo}\n"
        
        if lembretes_hoje:
            response += "\n*Lembretes:*\n"
            for lembrete in lembretes_hoje:
                texto = lembrete.get('texto', '')
                response += f"  🔔 {texto}\n"
        
        return response
    
    def _get_compromissos(self, user_id: str) -> str:
        """Lista próximos compromissos"""
        hoje = datetime.now()
        proximos = []
        
        for evento in self.eventos:
            if evento.get('user_id') != user_id:
                continue
            
            try:
                data = datetime.strptime(evento.get('data', ''), '%Y-%m-%d')
                if data >= hoje:
                    proximos.append(evento)
            except:
                pass
        
        if not proximos:
            return "📅 Nenhum compromisso agendado."
        
        response = "📅 *Próximos Compromissos:*\n\n"
        
        for evento in sorted(proximos, key=lambda x: x.get('data', ''))[:10]:
            data = evento.get('data', '')
            hora = evento.get('hora', '')
            titulo = evento.get('titulo', '')
            response += f"📌 {data} {hora} - {titulo}\n"
        
        return response
    
    def _get_lembretes(self, user_id: str) -> str:
        """Lista lembretes ativos"""
        ativos = [
            l for l in self.lembretes 
            if l.get('user_id') == user_id and l.get('ativo')
        ]
        
        if not ativos:
            return "🔔 Nenhum lembrete ativo."
        
        response = "🔔 *Lembretes Ativos:*\n\n"
        
        for lembrete in ativos:
            texto = lembrete.get('texto', '')
            data = lembrete.get('data_hora', '')[:10]
            response += f"  • {texto} ({data})\n"
        
        return response
    
    def _criar_lembrete(self, user_id: str, texto: str) -> str:
        """Cria um novo lembrete"""
        import re
        from uuid import uuid4
        
        # Extrai hora do texto
        hora_match = re.search(r'(\d{1,2})[h:](\d{2})?', texto)
        
        if hora_match:
            hora = int(hora_match.group(1))
            minuto = int(hora_match.group(2) or 0)
            data_hora = datetime.now().replace(hour=hora, minute=minuto)
            # Remove a hora do texto
            texto_limpo = re.sub(r'às?\s*\d{1,2}[h:]\d{0,2}', '', texto).strip()
        else:
            # Lembrete para daqui 1 hora
            data_hora = datetime.now() + timedelta(hours=1)
            texto_limpo = texto
        
        # Remove palavras de comando
        for word in ['lembrete', 'lembrar', 'me', 'de', 'para']:
            texto_limpo = re.sub(rf'\b{word}\b', '', texto_limpo, flags=re.IGNORECASE)
        texto_limpo = texto_limpo.strip()
        
        if not texto_limpo:
            return "❌ Por favor, informe o texto do lembrete."
        
        lembrete = Lembrete(
            id=str(uuid4())[:8],
            texto=texto_limpo,
            data_hora=data_hora.isoformat(),
            user_id=user_id,
            ativo=True,
            criado_em=datetime.now().isoformat()
        )
        
        self.lembretes.append(lembrete.to_dict())
        self._save_data()
        
        return f"""
✅ *Lembrete Criado!*

📝 {texto_limpo}
⏰ {data_hora.strftime('%d/%m/%Y às %H:%M')}

_Você será notificado no horário._
"""
    
    def _criar_evento(self, user_id: str, texto: str, analysis: Any) -> str:
        """Cria um novo evento"""
        from uuid import uuid4
        
        # Extrai informações do texto
        entities = analysis.entities if analysis else {}
        datetime_info = entities.get('datetime', {})
        
        # Data
        if datetime_info.get('relative_date') == 'tomorrow':
            data = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        else:
            data = datetime.now().strftime('%Y-%m-%d')
        
        hora = datetime_info.get('time', '09:00')
        
        evento = Evento(
            id=str(uuid4())[:8],
            titulo=texto[:50],
            descricao=texto,
            data=data,
            hora=hora,
            user_id=user_id,
            criado_em=datetime.now().isoformat()
        )
        
        self.eventos.append(evento.to_dict())
        self._save_data()
        
        return f"""
✅ *Evento Agendado!*

📌 {evento.titulo}
📅 {data}
⏰ {hora}
"""
