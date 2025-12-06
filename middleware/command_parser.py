"""
📝 Parser de Comandos
Interpreta comandos do usuário
"""
import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ParsedCommand:
    """Comando parseado"""
    raw: str
    command: str
    args: List[str]
    flags: dict
    
    
class CommandParser:
    """Parser de comandos no formato /comando arg1 arg2"""
    
    def __init__(self):
        self.command_pattern = re.compile(r'^/(\w+)(?:\s+(.*))?$')
        self.flag_pattern = re.compile(r'--(\w+)(?:=([^\s]+))?')
        self.quote_pattern = re.compile(r'"([^"]*)"')
    
    def parse(self, message: str) -> ParsedCommand:
        """
        Parseia uma mensagem de comando
        
        Args:
            message: Mensagem no formato /comando args
            
        Returns:
            ParsedCommand com comando, argumentos e flags
        """
        message = message.strip()
        
        # Extrai comando
        match = self.command_pattern.match(message)
        
        if not match:
            return ParsedCommand(
                raw=message,
                command='unknown',
                args=[message],
                flags={}
            )
        
        command = match.group(1).lower()
        args_str = match.group(2) or ''
        
        # Extrai flags (--flag ou --flag=value)
        flags = {}
        for flag_match in self.flag_pattern.finditer(args_str):
            flag_name = flag_match.group(1)
            flag_value = flag_match.group(2) or True
            flags[flag_name] = flag_value
        
        # Remove flags do texto de args
        args_str = self.flag_pattern.sub('', args_str).strip()
        
        # Extrai argumentos entre aspas primeiro
        quoted_args = self.quote_pattern.findall(args_str)
        args_str = self.quote_pattern.sub('', args_str).strip()
        
        # Divide argumentos restantes por espaço
        args = [a for a in args_str.split() if a]
        args.extend(quoted_args)
        
        return ParsedCommand(
            raw=message,
            command=command,
            args=args,
            flags=flags
        )
    
    def extract_datetime(self, text: str) -> Optional[dict]:
        """
        Extrai data/hora de um texto
        
        Exemplos:
            "amanhã às 14h" -> {'date': 'tomorrow', 'time': '14:00'}
            "segunda 10:30" -> {'date': 'monday', 'time': '10:30'}
        """
        result = {}
        text_lower = text.lower()
        
        # Padrões de data
        if 'hoje' in text_lower:
            result['date'] = 'today'
        elif 'amanhã' in text_lower or 'amanha' in text_lower:
            result['date'] = 'tomorrow'
        elif 'segunda' in text_lower:
            result['date'] = 'monday'
        elif 'terça' in text_lower or 'terca' in text_lower:
            result['date'] = 'tuesday'
        elif 'quarta' in text_lower:
            result['date'] = 'wednesday'
        elif 'quinta' in text_lower:
            result['date'] = 'thursday'
        elif 'sexta' in text_lower:
            result['date'] = 'friday'
        elif 'sábado' in text_lower or 'sabado' in text_lower:
            result['date'] = 'saturday'
        elif 'domingo' in text_lower:
            result['date'] = 'sunday'
        
        # Padrões de hora
        time_patterns = [
            r'(\d{1,2}):(\d{2})',  # 14:30
            r'(\d{1,2})h(\d{2})?',  # 14h ou 14h30
            r'às?\s*(\d{1,2})',  # às 14 ou as 14
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text_lower)
            if match:
                hour = match.group(1)
                minute = match.group(2) if len(match.groups()) > 1 and match.group(2) else '00'
                result['time'] = f"{int(hour):02d}:{int(minute):02d}"
                break
        
        return result if result else None
    
    def extract_value(self, text: str) -> Optional[float]:
        """
        Extrai valor monetário do texto
        
        Exemplos:
            "R$ 150,00" -> 150.0
            "50 reais" -> 50.0
            "R$1.500,50" -> 1500.50
        """
        # Padrões de valor
        patterns = [
            r'R\$\s*([\d.,]+)',  # R$ 150,00
            r'(\d+(?:[.,]\d+)?)\s*reais',  # 150 reais
            r'(\d+(?:[.,]\d+)?)\s*(?:R\$|BRL)',  # 150 R$
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value_str = match.group(1)
                # Normaliza: remove pontos de milhar, troca vírgula por ponto
                value_str = value_str.replace('.', '').replace(',', '.')
                try:
                    return float(value_str)
                except ValueError:
                    continue
        
        # Tenta encontrar apenas número
        match = re.search(r'(\d+(?:[.,]\d+)?)', text)
        if match:
            value_str = match.group(1).replace(',', '.')
            try:
                return float(value_str)
            except ValueError:
                pass
        
        return None
