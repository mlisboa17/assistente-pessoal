"""
 Assistente Pessoal Inteligente
Ponto de entrada principal do sistema
"""
import os
import sys
import asyncio
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

sys.path.insert(0, os.path.dirname(__file__))

from config.settings import Settings
from middleware.orchestrator import Orchestrator
from interfaces.telegram_bot import TelegramInterface

console = Console()

def print_banner():
    banner = """
    
            ASSISTENTE PESSOAL INTELIGENTE                 
                                                              
        Telegram  WhatsApp                                
        E-mails   Finanças   Agenda                  
        Comandos de Voz   Dashboards                    
    
    """
    console.print(Panel(banner, style="bold blue"))


class AssistentePessoal:
    def __init__(self):
        load_dotenv()
        self.settings = Settings()
        self.orchestrator = Orchestrator()
        self.interfaces = []
        self.voz_module = None

    def setup_voz_module(self):
        try:
            from modules.voz import VozModule
            self.voz_module = VozModule(data_dir="data")
            console.print("[green][/green] Módulo de Voz configurado")
            return True
        except ImportError as e:
            console.print(f"[yellow]![/yellow] Módulo de Voz: {e}")
            console.print("[dim]   Instale: pip install SpeechRecognition pydub[/dim]")
            return False

    def setup_interfaces(self):
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if telegram_token and telegram_token != 'seu_token_aqui':
            telegram = TelegramInterface(telegram_token, self.orchestrator)
            if self.voz_module:
                telegram.set_voz_module(self.voz_module)
            self.interfaces.append(('Telegram', telegram))
            console.print("[green][/green] Telegram Bot configurado")
        else:
            console.print("[yellow]![/yellow] Telegram: Token não configurado")

    async def start(self):
        print_banner()
        console.print("\n[bold] Inicializando módulos...[/bold]\n")
        self.setup_voz_module()
        self.setup_interfaces()

        if not self.interfaces:
            console.print("[red] Nenhuma interface configurada![/red]")
            return

        console.print(f"\n[green] {len(self.interfaces)} interface(s) ativa(s)[/green]")
        console.print("[bold cyan] Assistente iniciado! Aguardando mensagens...[/bold cyan]\n")

        tasks = [interface.start() for name, interface in self.interfaces if hasattr(interface, 'start')]
        if tasks:
            await asyncio.gather(*tasks)


def main():
    try:
        assistente = AssistentePessoal()
        asyncio.run(assistente.start())
    except KeyboardInterrupt:
        console.print("\n[yellow] Assistente encerrado[/yellow]")
    except Exception as e:
        console.print(f"\n[red] Erro: {e}[/red]")
        raise


if __name__ == "__main__":
    main()
