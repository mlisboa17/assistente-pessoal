"""
🧠 Motor NLP - Processamento de Linguagem Natural
"""
import re
import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Any


@dataclass
class NLPAnalysis:
    """Resultado da análise NLP"""
    text: str
    intent: Optional[str] = None
    confidence: float = 0.0
    entities: Dict[str, Any] = None
    sentiment: str = "neutral"
    keywords: List[str] = None
    
    def __post_init__(self):
        if self.entities is None:
            self.entities = {}
        if self.keywords is None:
            self.keywords = []


class NLPEngine:
    """
    Motor de NLP para entender linguagem natural
    
    Suporta:
    - Análise de intenção (intent)
    - Extração de entidades
    - Análise de sentimento básica
    - Keywords
    
    Pode usar:
    - Regras simples (default)
    - spaCy (se disponível)
    - OpenAI GPT (se configurado)
    """
    
    def __init__(self):
        self.use_spacy = False
        self.use_openai = False
        self.nlp = None
        
        # Tenta carregar spaCy
        try:
            import spacy
            self.nlp = spacy.load('pt_core_news_sm')
            self.use_spacy = True
        except:
            pass
        
        # Verifica OpenAI
        if os.getenv('OPENAI_API_KEY'):
            self.use_openai = True
        
        # Padrões de intenção
        self.intent_patterns = {
            'agenda': [
                r'agenda', r'compromisso', r'reunião', r'reuniao',
                r'marcar', r'agendar', r'lembrete', r'lembrar',
                r'horário', r'horario', r'calendário', r'calendario'
            ],
            'emails': [
                r'email', r'e-mail', r'mail', r'mensagem',
                r'inbox', r'caixa de entrada', r'enviar', r'ler'
            ],
            'financas': [
                r'gasto', r'despesa', r'dinheiro', r'saldo',
                r'conta', r'banco', r'pagar', r'pagamento',
                r'financ', r'valor', r'reais', r'R\$'
            ],
            'faturas': [
                r'fatura', r'boleto', r'extrato', r'conta de',
                r'luz', r'água', r'internet', r'telefone'
            ],
            'vendas': [
                r'venda', r'vendas', r'estoque', r'produto',
                r'cliente', r'pedido', r'relatório de venda'
            ],
            'tarefas': [
                r'tarefa', r'fazer', r'todo', r'pendente',
                r'lista', r'atividade', r'concluir'
            ],
            'saudacao': [
                r'olá', r'ola', r'oi', r'bom dia', r'boa tarde',
                r'boa noite', r'hey', r'hello', r'eai', r'e ai'
            ],
            'agradecimento': [
                r'obrigado', r'obrigada', r'valeu', r'thanks',
                r'agradeço', r'grato', r'grata'
            ]
        }
        
        # Palavras de sentimento
        self.positive_words = [
            'bom', 'ótimo', 'excelente', 'perfeito', 'legal',
            'adorei', 'gostei', 'maravilha', 'sucesso', 'consegui'
        ]
        self.negative_words = [
            'ruim', 'péssimo', 'horrível', 'problema', 'erro',
            'não consegui', 'falha', 'bug', 'travou', 'difícil'
        ]
    
    def analyze(self, text: str) -> NLPAnalysis:
        """
        Analisa um texto e retorna insights
        
        Args:
            text: Texto para analisar
            
        Returns:
            NLPAnalysis com intenção, entidades, etc.
        """
        text_lower = text.lower()
        
        # Detecta intenção
        intent, confidence = self._detect_intent(text_lower)
        
        # Extrai entidades
        entities = self._extract_entities(text)
        
        # Analisa sentimento
        sentiment = self._analyze_sentiment(text_lower)
        
        # Extrai keywords
        keywords = self._extract_keywords(text_lower)
        
        return NLPAnalysis(
            text=text,
            intent=intent,
            confidence=confidence,
            entities=entities,
            sentiment=sentiment,
            keywords=keywords
        )
    
    def _detect_intent(self, text: str) -> tuple:
        """Detecta a intenção do usuário"""
        best_intent = None
        best_score = 0
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            matches = 0
            
            for pattern in patterns:
                if re.search(pattern, text):
                    matches += 1
            
            if matches > 0:
                score = matches / len(patterns)
                if score > best_score:
                    best_score = score
                    best_intent = intent
        
        # Normaliza confiança
        confidence = min(best_score * 2, 1.0)  # Escala para 0-1
        
        return best_intent, confidence
    
    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Extrai entidades do texto"""
        entities = {}
        
        # Data/Hora
        datetime_info = self._extract_datetime(text)
        if datetime_info:
            entities['datetime'] = datetime_info
        
        # Valores monetários
        value = self._extract_money(text)
        if value:
            entities['money'] = value
        
        # E-mails
        emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        if emails:
            entities['emails'] = emails
        
        # Telefones
        phones = re.findall(r'\(?\d{2}\)?\s*\d{4,5}[-\s]?\d{4}', text)
        if phones:
            entities['phones'] = phones
        
        # URLs
        urls = re.findall(r'https?://[^\s]+', text)
        if urls:
            entities['urls'] = urls
        
        # Se tiver spaCy, extrai mais entidades
        if self.use_spacy and self.nlp:
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ not in entities:
                    entities[ent.label_] = []
                entities[ent.label_].append(ent.text)
        
        return entities
    
    def _extract_datetime(self, text: str) -> Optional[Dict]:
        """Extrai informações de data/hora"""
        result = {}
        text_lower = text.lower()
        
        # Datas relativas
        if 'hoje' in text_lower:
            result['relative_date'] = 'today'
        elif 'amanhã' in text_lower or 'amanha' in text_lower:
            result['relative_date'] = 'tomorrow'
        elif 'ontem' in text_lower:
            result['relative_date'] = 'yesterday'
        elif 'próxima semana' in text_lower or 'proxima semana' in text_lower:
            result['relative_date'] = 'next_week'
        
        # Dias da semana
        dias = {
            'segunda': 0, 'terça': 1, 'terca': 1, 'quarta': 2,
            'quinta': 3, 'sexta': 4, 'sábado': 5, 'sabado': 5, 'domingo': 6
        }
        for dia, num in dias.items():
            if dia in text_lower:
                result['weekday'] = num
                result['weekday_name'] = dia
                break
        
        # Horas
        time_match = re.search(r'(\d{1,2})[:\s]?h?(\d{2})?\s*(am|pm)?', text_lower)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            period = time_match.group(3)
            
            if period == 'pm' and hour < 12:
                hour += 12
            
            result['time'] = f"{hour:02d}:{minute:02d}"
        
        return result if result else None
    
    def _extract_money(self, text: str) -> Optional[Dict]:
        """Extrai valores monetários"""
        # Padrão: R$ 1.234,56 ou 1234.56 ou 1234,56
        pattern = r'R?\$?\s*(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)'
        match = re.search(pattern, text)
        
        if match:
            value_str = match.group(1)
            # Normaliza
            if ',' in value_str and '.' in value_str:
                # Formato brasileiro: 1.234,56
                value_str = value_str.replace('.', '').replace(',', '.')
            elif ',' in value_str:
                value_str = value_str.replace(',', '.')
            
            try:
                value = float(value_str)
                return {'value': value, 'currency': 'BRL'}
            except:
                pass
        
        return None
    
    def _analyze_sentiment(self, text: str) -> str:
        """Analisa sentimento do texto"""
        positive_count = sum(1 for word in self.positive_words if word in text)
        negative_count = sum(1 for word in self.negative_words if word in text)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        return 'neutral'
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extrai palavras-chave"""
        # Remove stopwords comuns
        stopwords = {
            'a', 'o', 'e', 'de', 'da', 'do', 'em', 'para', 'com',
            'que', 'um', 'uma', 'os', 'as', 'no', 'na', 'se', 'por',
            'mais', 'como', 'mas', 'foi', 'ao', 'ele', 'ela', 'entre',
            'depois', 'sem', 'mesmo', 'aos', 'ter', 'seus', 'quem',
            'nas', 'me', 'esse', 'eles', 'está', 'essa', 'num', 'nem',
            'suas', 'meu', 'às', 'minha', 'têm', 'numa', 'pelos', 'elas',
            'isso', 'eu', 'você', 'voce', 'nós', 'nos', 'já', 'ja'
        }
        
        # Tokeniza
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filtra
        keywords = [w for w in words if w not in stopwords and len(w) > 2]
        
        # Remove duplicatas mantendo ordem
        seen = set()
        unique = []
        for w in keywords:
            if w not in seen:
                seen.add(w)
                unique.append(w)
        
        return unique[:10]  # Top 10 keywords
