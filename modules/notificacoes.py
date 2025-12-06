"""
🔔 Módulo de Notificações Proativas
Envia alertas automáticos para os usuários
"""
import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict


@dataclass
class ConfigNotificacao:
    """Configuração de notificações do usuário"""
    user_id: str
    ativo: bool = True
    # Horários de resumo diário (formato HH:MM)
    resumo_diario: str = "20:00"
    resumo_semanal: str = "dom-10:00"
    # Dias de antecedência para alertas de vencimento
    dias_alerta_boleto: int = 3
    # Limite de gastos para alertar
    limite_gastos_diario: float = 0.0
    limite_gastos_mensal: float = 0.0
    # Notificações ativas
    notificar_boletos: bool = True
    notificar_gastos: bool = True
    notificar_metas: bool = True
    notificar_lembretes: bool = True
    # Horário de não perturbe
    nao_perturbe_inicio: str = "22:00"
    nao_perturbe_fim: str = "08:00"
    
    def to_dict(self):
        return asdict(self)


class NotificacoesModule:
    """Sistema de Notificações Proativas"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.config_file = os.path.join(data_dir, "config_notificacoes.json")
        self.historico_file = os.path.join(data_dir, "historico_notificacoes.json")
        
        os.makedirs(data_dir, exist_ok=True)
        self._load_data()
        
        # Callbacks para enviar notificações (serão registrados pelo bot)
        self.send_callbacks: Dict[str, Callable] = {}  # user_id -> callback
        
        # Referências aos módulos
        self.financas_module = None
        self.agenda_module = None
        self.faturas_module = None
        self.metas_module = None
        
        # Flag para controle do loop
        self._running = False
    
    def _load_data(self):
        """Carrega configurações"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.configs = json.load(f)
        else:
            self.configs = {}
        
        if os.path.exists(self.historico_file):
            with open(self.historico_file, 'r', encoding='utf-8') as f:
                self.historico = json.load(f)
        else:
            self.historico = []
    
    def _save_configs(self):
        """Salva configurações"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.configs, f, ensure_ascii=False, indent=2)
    
    def _save_historico(self):
        """Salva histórico"""
        with open(self.historico_file, 'w', encoding='utf-8') as f:
            json.dump(self.historico[-1000:], f, ensure_ascii=False, indent=2)  # Últimas 1000
    
    def set_modules(self, financas=None, agenda=None, faturas=None, metas=None):
        """Define referências aos módulos"""
        self.financas_module = financas
        self.agenda_module = agenda
        self.faturas_module = faturas
        self.metas_module = metas
    
    def register_callback(self, user_id: str, callback: Callable):
        """Registra callback para enviar notificações ao usuário"""
        self.send_callbacks[user_id] = callback
    
    def get_config(self, user_id: str) -> Dict:
        """Obtém configuração do usuário"""
        if user_id not in self.configs:
            self.configs[user_id] = ConfigNotificacao(user_id=user_id).to_dict()
            self._save_configs()
        return self.configs[user_id]
    
    def update_config(self, user_id: str, **kwargs) -> Dict:
        """Atualiza configuração do usuário"""
        config = self.get_config(user_id)
        config.update(kwargs)
        self.configs[user_id] = config
        self._save_configs()
        return config
    
    def _is_horario_permitido(self, user_id: str) -> bool:
        """Verifica se está fora do horário de não perturbe"""
        config = self.get_config(user_id)
        
        if not config.get('ativo', True):
            return False
        
        agora = datetime.now()
        hora_atual = agora.strftime("%H:%M")
        
        inicio = config.get('nao_perturbe_inicio', '22:00')
        fim = config.get('nao_perturbe_fim', '08:00')
        
        # Lógica de não perturbe (pode cruzar meia-noite)
        if inicio > fim:  # Ex: 22:00 - 08:00
            if hora_atual >= inicio or hora_atual < fim:
                return False
        else:  # Ex: 02:00 - 06:00
            if inicio <= hora_atual < fim:
                return False
        
        return True
    
    async def _send_notification(self, user_id: str, message: str, force: bool = False):
        """Envia notificação para o usuário"""
        if not force and not self._is_horario_permitido(user_id):
            return False
        
        # Registra no histórico
        self.historico.append({
            'user_id': user_id,
            'message': message[:200],  # Resumo
            'timestamp': datetime.now().isoformat(),
            'enviado': user_id in self.send_callbacks
        })
        self._save_historico()
        
        # Envia via callback
        if user_id in self.send_callbacks:
            try:
                callback = self.send_callbacks[user_id]
                if asyncio.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)
                return True
            except Exception as e:
                print(f"Erro ao enviar notificação: {e}")
        
        return False
    
    # ========== VERIFICAÇÕES AUTOMÁTICAS ==========
    
    async def verificar_boletos_vencendo(self, user_id: str) -> List[str]:
        """Verifica boletos próximos do vencimento"""
        alertas = []
        
        if not self.faturas_module:
            return alertas
        
        config = self.get_config(user_id)
        if not config.get('notificar_boletos', True):
            return alertas
        
        dias_alerta = config.get('dias_alerta_boleto', 3)
        hoje = datetime.now().date()
        
        for boleto in self.faturas_module.boletos:
            if boleto.get('user_id') != user_id:
                continue
            if boleto.get('pago', False):
                continue
            
            try:
                vencimento = datetime.fromisoformat(boleto['vencimento']).date()
                dias_restantes = (vencimento - hoje).days
                
                if 0 <= dias_restantes <= dias_alerta:
                    emoji = "🔴" if dias_restantes <= 1 else "🟠" if dias_restantes <= 2 else "🟡"
                    alertas.append(f"""
{emoji} *BOLETO VENCENDO!*

📄 {boleto.get('beneficiario', 'Boleto')}
💰 R$ {boleto.get('valor', 0):.2f}
📅 Vencimento: {vencimento.strftime('%d/%m/%Y')}
⏰ Faltam {dias_restantes} dia(s)!

_Use /boletos para ver todos_
""")
            except:
                continue
        
        return alertas
    
    async def verificar_gastos_limite(self, user_id: str) -> Optional[str]:
        """Verifica se ultrapassou limite de gastos"""
        if not self.financas_module:
            return None
        
        config = self.get_config(user_id)
        if not config.get('notificar_gastos', True):
            return None
        
        limite_diario = config.get('limite_gastos_diario', 0)
        limite_mensal = config.get('limite_gastos_mensal', 0)
        
        if limite_diario <= 0 and limite_mensal <= 0:
            return None
        
        hoje = datetime.now().date()
        gastos_hoje = 0
        gastos_mes = 0
        
        for t in self.financas_module.transacoes:
            if t.get('user_id') != user_id or t.get('tipo') != 'saida':
                continue
            
            try:
                data = datetime.fromisoformat(t['data']).date()
                valor = t.get('valor', 0)
                
                if data == hoje:
                    gastos_hoje += valor
                if data.month == hoje.month and data.year == hoje.year:
                    gastos_mes += valor
            except:
                continue
        
        # Verifica limites
        if limite_diario > 0 and gastos_hoje > limite_diario:
            porcentagem = (gastos_hoje / limite_diario) * 100
            return f"""
⚠️ *ALERTA DE GASTOS DIÁRIOS!*

💸 Você gastou: R$ {gastos_hoje:.2f}
🎯 Limite diário: R$ {limite_diario:.2f}
📊 {porcentagem:.0f}% do limite

_Configure limites com /config gastos_
"""
        
        if limite_mensal > 0 and gastos_mes > limite_mensal:
            porcentagem = (gastos_mes / limite_mensal) * 100
            return f"""
🚨 *ALERTA DE GASTOS MENSAIS!*

💸 Gastos do mês: R$ {gastos_mes:.2f}
🎯 Limite mensal: R$ {limite_mensal:.2f}
📊 {porcentagem:.0f}% do limite

_Configure limites com /config gastos_
"""
        
        return None
    
    async def verificar_metas(self, user_id: str) -> List[str]:
        """Verifica progresso das metas"""
        alertas = []
        
        if not self.metas_module:
            return alertas
        
        config = self.get_config(user_id)
        if not config.get('notificar_metas', True):
            return alertas
        
        for meta in self.metas_module.metas:
            if meta.get('user_id') != user_id:
                continue
            if meta.get('concluida', False):
                continue
            
            progresso = meta.get('valor_atual', 0) / meta.get('valor_alvo', 1) * 100
            
            # Alerta em marcos importantes
            if progresso >= 100:
                alertas.append(f"""
🎉 *META ALCANÇADA!*

🎯 {meta.get('titulo', 'Meta')}
💰 R$ {meta.get('valor_atual', 0):.2f} / R$ {meta.get('valor_alvo', 0):.2f}

Parabéns! Você conseguiu! 🏆
""")
            elif progresso >= 75 and meta.get('ultimo_alerta', 0) < 75:
                alertas.append(f"""
📈 *75% DA META!*

🎯 {meta.get('titulo', 'Meta')}
💰 R$ {meta.get('valor_atual', 0):.2f} / R$ {meta.get('valor_alvo', 0):.2f}

Falta pouco! Continue assim! 💪
""")
                meta['ultimo_alerta'] = 75
                self.metas_module._save_data()
            elif progresso >= 50 and meta.get('ultimo_alerta', 0) < 50:
                alertas.append(f"""
📊 *50% DA META!*

🎯 {meta.get('titulo', 'Meta')}
💰 R$ {meta.get('valor_atual', 0):.2f} / R$ {meta.get('valor_alvo', 0):.2f}

Metade do caminho! 🚀
""")
                meta['ultimo_alerta'] = 50
                self.metas_module._save_data()
        
        return alertas
    
    async def gerar_resumo_diario(self, user_id: str) -> str:
        """Gera resumo diário para o usuário"""
        config = self.get_config(user_id)
        hoje = datetime.now()
        
        resumo = f"""
📊 *RESUMO DO DIA - {hoje.strftime('%d/%m/%Y')}*

"""
        
        # Gastos do dia
        if self.financas_module:
            gastos_hoje = 0
            entradas_hoje = 0
            
            for t in self.financas_module.transacoes:
                if t.get('user_id') != user_id:
                    continue
                try:
                    data = datetime.fromisoformat(t['data']).date()
                    if data == hoje.date():
                        if t.get('tipo') == 'saida':
                            gastos_hoje += t.get('valor', 0)
                        else:
                            entradas_hoje += t.get('valor', 0)
                except:
                    continue
            
            resumo += f"""💰 *Finanças:*
   📉 Gastos: R$ {gastos_hoje:.2f}
   📈 Entradas: R$ {entradas_hoje:.2f}
   💵 Saldo do dia: R$ {entradas_hoje - gastos_hoje:.2f}

"""
        
        # Boletos próximos
        if self.faturas_module:
            boletos_proximos = []
            for boleto in self.faturas_module.boletos:
                if boleto.get('user_id') != user_id or boleto.get('pago'):
                    continue
                try:
                    venc = datetime.fromisoformat(boleto['vencimento']).date()
                    dias = (venc - hoje.date()).days
                    if 0 <= dias <= 7:
                        boletos_proximos.append((boleto, dias))
                except:
                    continue
            
            if boletos_proximos:
                resumo += f"📄 *Boletos próximos:*\n"
                for boleto, dias in sorted(boletos_proximos, key=lambda x: x[1]):
                    emoji = "🔴" if dias <= 1 else "🟠" if dias <= 3 else "🟡"
                    resumo += f"   {emoji} {boleto.get('beneficiario', 'Boleto')[:20]} - R$ {boleto.get('valor', 0):.2f} ({dias}d)\n"
                resumo += "\n"
        
        # Metas
        if self.metas_module:
            metas_ativas = [m for m in self.metas_module.metas 
                          if m.get('user_id') == user_id and not m.get('concluida')]
            if metas_ativas:
                resumo += f"🎯 *Metas ativas:* {len(metas_ativas)}\n"
                for meta in metas_ativas[:3]:
                    progresso = meta.get('valor_atual', 0) / meta.get('valor_alvo', 1) * 100
                    barra = self._barra_progresso(progresso)
                    resumo += f"   {barra} {meta.get('titulo', 'Meta')[:15]}\n"
                resumo += "\n"
        
        # Compromissos de amanhã
        if self.agenda_module:
            amanha = (hoje + timedelta(days=1)).date()
            eventos_amanha = []
            for evento in self.agenda_module.eventos:
                if evento.get('user_id') != user_id:
                    continue
                try:
                    data_evento = datetime.fromisoformat(evento['data']).date()
                    if data_evento == amanha:
                        eventos_amanha.append(evento)
                except:
                    continue
            
            if eventos_amanha:
                resumo += f"📅 *Amanhã:*\n"
                for ev in eventos_amanha[:5]:
                    hora = ev.get('hora', '')
                    resumo += f"   • {hora} {ev.get('titulo', 'Evento')[:25]}\n"
                resumo += "\n"
        
        resumo += "_Boa noite! 🌙_"
        
        return resumo
    
    def _barra_progresso(self, porcentagem: float) -> str:
        """Gera barra de progresso visual"""
        total = 10
        preenchido = int(porcentagem / 100 * total)
        preenchido = min(preenchido, total)
        vazio = total - preenchido
        return f"[{'█' * preenchido}{'░' * vazio}] {porcentagem:.0f}%"
    
    # ========== LOOP DE VERIFICAÇÃO ==========
    
    async def start_notification_loop(self):
        """Inicia loop de verificações periódicas"""
        self._running = True
        print("🔔 Sistema de notificações iniciado!")
        
        while self._running:
            try:
                await self._check_and_notify()
            except Exception as e:
                print(f"Erro no loop de notificações: {e}")
            
            # Verifica a cada 5 minutos
            await asyncio.sleep(300)
    
    def stop_notification_loop(self):
        """Para o loop de verificações"""
        self._running = False
    
    async def _check_and_notify(self):
        """Executa todas as verificações"""
        agora = datetime.now()
        hora_atual = agora.strftime("%H:%M")
        
        for user_id, config in self.configs.items():
            if not config.get('ativo', True):
                continue
            
            # Resumo diário no horário configurado
            if hora_atual == config.get('resumo_diario', '20:00'):
                resumo = await self.gerar_resumo_diario(user_id)
                await self._send_notification(user_id, resumo)
            
            # Verificações contínuas
            
            # Boletos
            alertas_boletos = await self.verificar_boletos_vencendo(user_id)
            for alerta in alertas_boletos:
                await self._send_notification(user_id, alerta)
            
            # Gastos
            alerta_gastos = await self.verificar_gastos_limite(user_id)
            if alerta_gastos:
                await self._send_notification(user_id, alerta_gastos)
            
            # Metas
            alertas_metas = await self.verificar_metas(user_id)
            for alerta in alertas_metas:
                await self._send_notification(user_id, alerta)
    
    # ========== COMANDOS ==========
    
    async def handle(self, command: str, args: List[str], 
                     user_id: str, attachments: list = None) -> str:
        """Processa comandos de notificações"""
        
        if command == 'notificacoes':
            if args:
                if args[0] in ['on', 'ativar', 'ligar']:
                    self.update_config(user_id, ativo=True)
                    return "🔔 Notificações *ativadas*!"
                elif args[0] in ['off', 'desativar', 'desligar']:
                    self.update_config(user_id, ativo=False)
                    return "🔕 Notificações *desativadas*."
                elif args[0] == 'config':
                    return self._mostrar_config(user_id)
            return self._mostrar_status(user_id)
        
        elif command == 'silenciar':
            horas = 1
            if args and args[0].isdigit():
                horas = int(args[0])
            return self._silenciar(user_id, horas)
        
        elif command == 'config':
            if len(args) >= 2:
                return self._configurar(user_id, args[0], ' '.join(args[1:]))
            return self._mostrar_config(user_id)
        
        return self._mostrar_status(user_id)
    
    def _mostrar_status(self, user_id: str) -> str:
        """Mostra status das notificações"""
        config = self.get_config(user_id)
        status = "🟢 Ativas" if config.get('ativo') else "🔴 Desativadas"
        
        return f"""
🔔 *Notificações - {status}*

📊 Resumo diário: {config.get('resumo_diario', '20:00')}
📄 Alerta de boletos: {config.get('dias_alerta_boleto', 3)} dias antes
🌙 Não perturbe: {config.get('nao_perturbe_inicio')} - {config.get('nao_perturbe_fim')}

*Comandos:*
• `/notificacoes on/off` - Ativar/desativar
• `/notificacoes config` - Ver configurações
• `/silenciar [horas]` - Silenciar temporariamente
• `/config [opção] [valor]` - Configurar
"""
    
    def _mostrar_config(self, user_id: str) -> str:
        """Mostra configurações detalhadas"""
        config = self.get_config(user_id)
        
        return f"""
⚙️ *Configurações de Notificações*

*Horários:*
• Resumo diário: `{config.get('resumo_diario', '20:00')}`
• Não perturbe: `{config.get('nao_perturbe_inicio')}` - `{config.get('nao_perturbe_fim')}`

*Alertas:*
• Boletos: {config.get('dias_alerta_boleto', 3)} dias antes
• Limite diário: R$ {config.get('limite_gastos_diario', 0):.2f}
• Limite mensal: R$ {config.get('limite_gastos_mensal', 0):.2f}

*Tipos ativos:*
• 📄 Boletos: {'✅' if config.get('notificar_boletos') else '❌'}
• 💰 Gastos: {'✅' if config.get('notificar_gastos') else '❌'}
• 🎯 Metas: {'✅' if config.get('notificar_metas') else '❌'}
• ⏰ Lembretes: {'✅' if config.get('notificar_lembretes') else '❌'}

*Para configurar:*
`/config resumo 21:00`
`/config limite_diario 200`
`/config limite_mensal 3000`
`/config nao_perturbe 23:00-07:00`
"""
    
    def _configurar(self, user_id: str, opcao: str, valor: str) -> str:
        """Configura uma opção"""
        opcao = opcao.lower()
        
        if opcao == 'resumo':
            self.update_config(user_id, resumo_diario=valor)
            return f"✅ Resumo diário configurado para {valor}"
        
        elif opcao in ['limite_diario', 'limite-diario', 'limitediario']:
            try:
                limite = float(valor.replace('R$', '').replace(',', '.').strip())
                self.update_config(user_id, limite_gastos_diario=limite)
                return f"✅ Limite diário: R$ {limite:.2f}"
            except:
                return "❌ Valor inválido. Use: /config limite_diario 200"
        
        elif opcao in ['limite_mensal', 'limite-mensal', 'limitemensal']:
            try:
                limite = float(valor.replace('R$', '').replace(',', '.').strip())
                self.update_config(user_id, limite_gastos_mensal=limite)
                return f"✅ Limite mensal: R$ {limite:.2f}"
            except:
                return "❌ Valor inválido. Use: /config limite_mensal 3000"
        
        elif opcao in ['nao_perturbe', 'naoperturbe', 'silencio']:
            partes = valor.replace(' ', '').split('-')
            if len(partes) == 2:
                self.update_config(user_id, 
                                  nao_perturbe_inicio=partes[0],
                                  nao_perturbe_fim=partes[1])
                return f"✅ Não perturbe: {partes[0]} - {partes[1]}"
            return "❌ Formato inválido. Use: /config nao_perturbe 22:00-08:00"
        
        elif opcao in ['dias_boleto', 'diasboleto', 'boleto']:
            try:
                dias = int(valor)
                self.update_config(user_id, dias_alerta_boleto=dias)
                return f"✅ Alerta de boletos: {dias} dias antes"
            except:
                return "❌ Valor inválido. Use: /config dias_boleto 3"
        
        return f"❌ Opção `{opcao}` não reconhecida."
    
    def _silenciar(self, user_id: str, horas: int) -> str:
        """Silencia notificações temporariamente"""
        ate = datetime.now() + timedelta(hours=horas)
        self.update_config(user_id, silenciado_ate=ate.isoformat())
        return f"🔕 Notificações silenciadas por {horas} hora(s).\nAté: {ate.strftime('%H:%M')}"


# Singleton
_notificacoes_instance = None

def get_notificacoes(data_dir: str = "data") -> NotificacoesModule:
    """Retorna instância singleton do módulo de notificações"""
    global _notificacoes_instance
    if _notificacoes_instance is None:
        _notificacoes_instance = NotificacoesModule(data_dir)
    return _notificacoes_instance
