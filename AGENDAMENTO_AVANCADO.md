# 📅 Sistema Avançado de Agendamento - Guia Completo

## Visão Geral

O novo sistema de agendamento implementa um fluxo interativo com:

1. ✨ **Confirmação de dados** - Usuário vê data/hora antes de confirmar
2. ✏️ **Edição em tempo real** - Pode mudar data ou hora sem recomeçar
3. 🔔 **Lembrete automático** - Cria lembrete 2 horas antes do evento
4. 📱 **Suporte a múltiplos formatos** - Aceita diferentes formatos de data e hora

---

## Arquitetura

### Novo Módulo: `modules/agendamento_avancado.py`

```
SistemaAgendamentoAvancado
├── iniciar_agendamento()      # Inicia fluxo
├── processar_resposta()        # Processa ações do usuário
├── _normalizar_data()          # Converte formatos de data
├── _normalizar_hora()          # Converte formatos de hora
├── _formatar_confirmacao_inicial()  # Mostra menu
├── _processar_edicao()         # Edita data/hora
├── _executar_agendamento()     # Cria evento + lembrete
├── _criar_lembrete_automatico() # Cria lembrete 2h antes
└── listar_pendentes()          # Lista agendamentos pendentes
```

### Integração em `modules/agenda.py`

```python
class AgendaModule:
    def __init__(self):
        self.agendamento_avancado = get_sistema_agendamento()
    
    async def _criar_evento_interativo(self, user_id, texto, analysis):
        # Novo método que usa o sistema avançado
        # Chama iniciar_agendamento() do sistema
```

---

## Fluxo de Uso

### 1️⃣ Usuário inicia o agendamento

```
Usuário: "Agendar reunião amanhã às 14:30"
```

### 2️⃣ Sistema extrai dados e mostra confirmação

```
📅 AGENDAMENTO PARA CONFIRMAR

═══════════════════════════════════
📌 EVENTO: reunião
📆 DATA: Terça, 09 de Dezembro de 2025
⏰ HORA: 14:30
🔔 LEMBRETE: Automático 2h antes
═══════════════════════════════════

Confirme os dados:

✅ /confirmar ou /ok - Agendar
✏️  /editar data 25/12/2025 - Mudar data
✏️  /editar hora 14:30 - Mudar hora
❌ /cancelar - Descartar
```

### 3️⃣ Usuário pode editar antes de confirmar

```
Usuário: "/editar data 26/12/2025"

Sistema: ✅ Data atualizada para Quinta, 26 de Dezembro de 2025

[mostra confirmação novamente com nova data]
```

### 4️⃣ Usuário confirma agendamento

```
Usuário: "/confirmar"

Sistema: ✅ AGENDAMENTO CONFIRMADO!

═══════════════════════════════════
📌 reunião
📆 Quinta, 26 de Dezembro de 2025
⏰ 14:30
🔔 Lembrete automático: 2 horas antes
═══════════════════════════════════

ID do evento: 268a8a04
ID do lembrete: 84dab4af
```

### 5️⃣ Sistema cria automaticamente:

- **Evento**: Agendado para a data/hora confirmada
- **Lembrete**: Criado para 2 horas antes do evento

---

## Formatos Suportados

### Datas

| Formato | Exemplo | Resultado |
|---------|---------|-----------|
| DD/MM/YYYY | 25/12/2025 | 2025-12-25 |
| YYYY-MM-DD | 2025-12-25 | 2025-12-25 |
| Palavra-chave | amanhã | [dia seguinte] |
| Palavra-chave | hoje | [data de hoje] |
| Palavra-chave | próxima segunda | [próxima segunda-feira] |

### Horas

| Formato | Exemplo | Resultado |
|---------|---------|-----------|
| HH:MM | 14:30 | 14:30 |
| HHhMM | 14h30 | 14:30 |
| HHh | 14h | 14:00 |
| H | 9 | 09:00 |

---

## Comandos Disponíveis

### Durante a Confirmação

```
/confirmar      # Confirma agendamento
/ok             # Alias para confirmar
/sim            # Alias para confirmar
/yes            # Alias para confirmar

/editar data DATA       # Muda data (ex: /editar data 26/12/2025)
/editar hora HORA       # Muda hora (ex: /editar hora 15:00)

/cancelar       # Cancela agendamento
/nao            # Alias para cancelar
/no             # Alias para cancelar
/cancel         # Alias para cancelar
```

---

## Estrutura de Dados

### AgendamentoConfirmacao

```python
@dataclass
class AgendamentoConfirmacao:
    id: str                           # ID único
    titulo: str                       # Título do evento
    data_original: str                # Data extraída (YYYY-MM-DD)
    hora_original: str                # Hora extraída (HH:MM)
    data_confirmada: Optional[str]    # Data confirmada (se editada)
    hora_confirmada: Optional[str]    # Hora confirmada (se editada)
    user_id: str                      # ID do usuário
    origem: str                       # 'documento', 'comando', 'natural'
    extra: Dict[str, Any]             # Dados extras
```

### Evento (criado na agenda)

```json
{
  "id": "268a8a04",
  "titulo": "reunião",
  "data": "2025-12-26",
  "hora": "14:30",
  "user_id": "user123",
  "criado_em": "2025-12-08T10:45:30.123456",
  "origem": "natural",
  "extra": {}
}
```

### Lembrete Automático (criado 2h antes)

```json
{
  "id": "84dab4af",
  "texto": "⏰ Lembrete: reunião",
  "data_hora": "2025-12-26T12:30:00",
  "user_id": "user123",
  "ativo": true,
  "criado_em": "2025-12-08T10:45:30.123456",
  "origem": "agendamento_automatico",
  "evento_id": "268a8a04"
}
```

---

## Exemplos de Uso

### Exemplo 1: Agendamento Simples

```python
sistema = SistemaAgendamentoAvancado()

# Iniciar
resposta = sistema.iniciar_agendamento(
    titulo="Dentista",
    data="25/12/2025",
    hora="10:00",
    user_id="user123"
)
print(resposta)  # Mostra menu de confirmação

# Usuário responde
resposta, dados = sistema.processar_resposta("/confirmar", "user123")
print(resposta)  # Confirmação com IDs
print(dados['evento_id'])    # ID do evento
print(dados['lembrete_id'])  # ID do lembrete
```

### Exemplo 2: Editar Antes de Confirmar

```python
# Iniciar
sistema.iniciar_agendamento(
    titulo="Reunião",
    data="25/12/2025",
    hora="14:30",
    user_id="user123"
)

# Editar data
resposta, dados = sistema.processar_resposta(
    "/editar data 26/12/2025",
    "user123"
)

# Editar hora
resposta, dados = sistema.processar_resposta(
    "/editar hora 15:00",
    "user123"
)

# Confirmar com valores editados
resposta, dados = sistema.processar_resposta(
    "/confirmar",
    "user123"
)
```

### Exemplo 3: Cancelar Agendamento

```python
# Iniciar
sistema.iniciar_agendamento(
    titulo="Evento",
    data="25/12/2025",
    hora="16:00",
    user_id="user123"
)

# Cancelar
resposta, dados = sistema.processar_resposta(
    "/cancelar",
    "user123"
)

print(resposta)  # "❌ Agendamento cancelado."
print(datos['acao'])  # 'cancelar'
```

---

## Integração com Módulo Agenda

### Fluxo Automático em handle_natural()

```python
# Em modules/agenda.py

async def handle_natural(self, message, analysis, user_id):
    text_lower = message.lower()
    
    # Se tem agendamento pendente e usuário responde
    if self.agendamento_avancado and user_id in self.agendamento_avancado.pendentes:
        if any(word in text_lower for word in ['confirmar', 'ok', 'sim', 'cancelar', 'editar']):
            resposta, dados = self.agendamento_avancado.processar_resposta(
                message,
                user_id,
                agenda_module=self  # Passa self para criar evento/lembrete
            )
            return resposta
    
    # Se usuário pede para agendar
    if any(word in text_lower for word in ['marcar', 'agendar', 'reuniao']):
        return await self._criar_evento_interativo(user_id, message, analysis)
```

---

## Testes

Execute os testes com:

```bash
python teste_agendamento.py
```

### Testes Inclusos

1. ✅ Normalização de datas
2. ✅ Normalização de horas
3. ✅ Iniciar agendamento com confirmação
4. ✅ Editar data/hora
5. ✅ Confirmar e criar evento + lembrete
6. ✅ Cancelar agendamento

---

## Recursos Futuros

- [ ] Recorrência (semanal, mensal, etc.)
- [ ] Sincronização com Google Calendar
- [ ] Múltiplos lembretes (15min, 1h, 2h)
- [ ] Notificações push em tempo real
- [ ] Calendário visual em Telegram
- [ ] Busca de horários disponíveis
- [ ] Convites para participantes

---

## Troubleshooting

### Problema: Data não é reconhecida

**Solução**: Verifique o formato. Use DD/MM/YYYY ou YYYY-MM-DD

```
Correto: 25/12/2025
Errado:  25-12-2025
```

### Problema: Hora com minutos não funciona

**Solução**: Use HH:MM ou HHhMM

```
Correto: 14:30 ou 14h30
Errado:  14.30
```

### Problema: "Nenhum agendamento pendente"

**Solução**: Inicie um novo agendamento primeiro

```
Usuário: "Agendar reunião amanhã às 14:30"
```

---

## Exemplo de Conversa Completa

```
Usuário: Agendar dentista sexta às 10h

Sistema: 📅 AGENDAMENTO PARA CONFIRMAR
         📌 dentista
         📆 Sexta, 12 de Dezembro de 2025
         ⏰ 10:00
         🔔 LEMBRETE: Automático 2h antes
         
         ✅ /confirmar - Agendar
         ✏️  /editar data 25/12/2025
         ✏️  /editar hora 14:30

Usuário: /editar hora 10:30

Sistema: ✅ Hora atualizada para 10:30
         [mostra confirmação novamente]

Usuário: /confirmar

Sistema: ✅ AGENDAMENTO CONFIRMADO!
         📌 dentista
         📆 Sexta, 12 de Dezembro de 2025
         ⏰ 10:30
         🔔 Lembrete: 08:30
         ID: 268a8a04
```

---

## Referências

- `modules/agendamento_avancado.py` - Implementação completa
- `modules/agenda.py` - Integração com AgendaModule
- `teste_agendamento.py` - Suite de testes
