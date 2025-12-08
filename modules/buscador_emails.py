"""
🔍 Buscador Fuzzy de E-mails
Sistema inteligente de busca por:
- Remetente incompleto (fuzzy matching)
- Assunto com interpretação natural
- Múltiplos critérios combinados
- Sugestões de e-mails relacionados
"""
import re
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from difflib import SequenceMatcher


@dataclass
class ResultadoBusca:
    """Resultado de uma busca de email"""
    email: any  # Email object
    score: float  # Confiança da busca (0-1)
    tipo_match: str  # "remetente", "assunto", "corpo", "combinado"
    motivo: str  # Por que foi encontrado


class BuscadorFuzzyEmails:
    """
    Buscador inteligente de e-mails com:
    - Fuzzy matching para remetentes incompletos
    - Interpretação de linguagem natural para assuntos
    - Autocorreção de erros de digitação
    - Sugestões baseadas em contexto
    """
    
    def __init__(self):
        # Sinônimos comuns para melhorar busca
        self.sinonimos = {
            'chefe': ['chefe', 'boss', 'gerente', 'diretor', 'supervisor'],
            'amigo': ['amigo', 'colega', 'amiga', 'colega', 'friend'],
            'banco': ['banco', 'santander', 'itaú', 'bradesco', 'bb', 'caixa'],
            'loja': ['loja', 'shop', 'compra', 'amazon', 'shopee', 'mercado'],
            'email': ['email', 'e-mail', 'mensagem', 'mail', 'correio'],
            'reunião': ['reunião', 'meeting', 'conferência', 'encontro', 'call'],
            'urgente': ['urgente', 'urgent', 'imediato', 'prioridade', 'importante'],
            'confirmação': ['confirmação', 'confirm', 'confirmar', 'approved', 'ok'],
            'delivery': ['delivery', 'entrega', 'entregue', 'shipped', 'delivered'],
            'fatura': ['fatura', 'invoice', 'nota', 'cobrança', 'boleto'],
            'desconto': ['desconto', 'promoção', 'desconto', 'sale', 'offer'],
        }
        
        # Padrões de interpretação
        self.padroes_assunto = {
            'urgente': r'(urgente|imediato|prioridade|atenção)',
            'reuniao': r'(reunião|meeting|call|conferência|encontro)',
            'confirmacao': r'(confirmação|confirmar|confirmed|ok|aprovado)',
            'entrega': r'(entrega|delivered|shipped|chegou|recebeu)',
            'fatura': r'(fatura|invoice|nota|cobrança|boleto)',
            'desconto': r'(desconto|promoção|sale|offer|promocao)',
            'ticket': r'(ticket|suporte|help|problema|erro)',
            'recibo': r'(recibo|receipt|comprovante|nota fiscal)',
        }
    
    def buscar_remetente_fuzzy(self, termo_incompleto: str, 
                               emails: List, 
                               limiar_confianca: float = 0.6) -> List[ResultadoBusca]:
        """
        Busca por remetente com matching fuzzy
        
        Exemplos:
        - "ch" encontra "chefe@empresa.com"
        - "ama" encontra "amazon@noreply.com"
        - "amg" (erro) encontra "amigo@hotmail.com"
        
        Args:
            termo_incompleto: O que o usuário digitou (pode estar incompleto)
            emails: Lista de emails para buscar
            limiar_confianca: Score mínimo (0-1)
        
        Returns:
            Lista de ResultadoBusca ordenados por confiança
        """
        resultados = []
        termo_lower = termo_incompleto.lower().strip()
        
        if not termo_lower:
            return resultados
        
        for email in emails:
            remetente = email.de.lower()
            nome_remetente = remetente.split('@')[0] if '@' in remetente else remetente
            dominio = remetente.split('@')[1] if '@' in remetente else ''
            
            # 🔍 Tentativa 1: Correspondência exata (score = 1.0)
            if termo_lower == remetente or termo_lower == nome_remetente:
                resultados.append(ResultadoBusca(
                    email=email,
                    score=1.0,
                    tipo_match='remetente',
                    motivo=f'Correspondência exata: {remetente}'
                ))
                continue
            
            # 🔍 Tentativa 2: Contém exatamente (score = 0.95)
            if termo_lower in remetente or termo_lower in nome_remetente:
                resultados.append(ResultadoBusca(
                    email=email,
                    score=0.95,
                    tipo_match='remetente',
                    motivo=f'Contém: {remetente}'
                ))
                continue
            
            # 🔍 Tentativa 3: Fuzzy matching no nome (score = sequence matcher)
            score_nome = self._calcular_similaridade(termo_lower, nome_remetente)
            if score_nome >= limiar_confianca:
                resultados.append(ResultadoBusca(
                    email=email,
                    score=score_nome,
                    tipo_match='remetente',
                    motivo=f'Fuzzy match no nome: {nome_remetente} (score: {score_nome:.0%})'
                ))
                continue
            
            # 🔍 Tentativa 4: Fuzzy matching no domínio
            score_dominio = self._calcular_similaridade(termo_lower, dominio)
            if score_dominio >= limiar_confianca:
                resultados.append(ResultadoBusca(
                    email=email,
                    score=score_dominio * 0.8,  # Score menor para domínio
                    tipo_match='remetente',
                    motivo=f'Fuzzy match no domínio: {dominio} (score: {score_dominio:.0%})'
                ))
                continue
            
            # 🔍 Tentativa 5: Buscar por sinônimos
            score_sinonimo = self._buscar_sinonimos(termo_lower, remetente)
            if score_sinonimo > 0:
                resultados.append(ResultadoBusca(
                    email=email,
                    score=score_sinonimo,
                    tipo_match='remetente',
                    motivo=f'Encontrado por sinônimo (score: {score_sinonimo:.0%})'
                ))
                continue
        
        # Ordenar por confiança (maior primeiro)
        resultados.sort(key=lambda x: x.score, reverse=True)
        return resultados
    
    def buscar_assunto_inteligente(self, termo_busca: str, 
                                    emails: List,
                                    limiar_confianca: float = 0.5) -> List[ResultadoBusca]:
        """
        Busca por assunto com interpretação de linguagem natural
        
        Exemplos:
        - "reunião amanhã" encontra "Reunião urgente hoje às 14:00"
        - "pedido entregue" encontra "📦 Seu pedido foi entregue!"
        - "desconto eletrônicos" encontra "MEGA DESCONTO: eletrônicos"
        
        Args:
            termo_busca: O que o usuário está procurando
            emails: Lista de emails para buscar
            limiar_confianca: Score mínimo
        
        Returns:
            Lista de ResultadoBusca ordenados por confiança
        """
        resultados = []
        termo_lower = termo_busca.lower().strip()
        
        if not termo_lower:
            return resultados
        
        # Interpretar o termo (detectar intenção)
        palavras_chave = termo_lower.split()
        categorias_detectadas = self._detectar_categorias(termo_lower)
        
        for email in emails:
            texto_completo = f"{email.assunto} {email.corpo}".lower()
            assunto_lower = email.assunto.lower()
            
            scores = []
            motivos = []
            
            # 🎯 Estratégia 1: Correspondência exata (100%)
            if termo_lower == assunto_lower:
                scores.append(1.0)
                motivos.append("Correspondência exata no assunto")
            
            # 🎯 Estratégia 2: Todas as palavras estão presentes
            elif all(palavra in texto_completo for palavra in palavras_chave):
                peso = len(palavras_chave) / max(1, len(texto_completo.split()))
                scores.append(min(0.95, 0.7 + peso * 0.25))
                motivos.append(f"Contém todas as palavras: {', '.join(palavras_chave)}")
            
            # 🎯 Estratégia 3: Fuzzy match no assunto
            else:
                for palavra in palavras_chave:
                    if len(palavra) >= 3:  # Apenas palavras com 3+ caracteres
                        score = self._calcular_similaridade(palavra, assunto_lower)
                        if score >= 0.6:
                            scores.append(score * 0.8)
                            motivos.append(f"Fuzzy: '{palavra}' similiar ao assunto")
            
            # 🎯 Estratégia 4: Buscar por categoria/intenção
            for categoria, score_cat in categorias_detectadas.items():
                if self._verificar_categoria_email(email, categoria):
                    scores.append(score_cat)
                    motivos.append(f"Categoria detectada: {categoria}")
            
            # Se achou algo, adicionar resultado
            if scores:
                score_final = max(scores)
                if score_final >= limiar_confianca:
                    resultados.append(ResultadoBusca(
                        email=email,
                        score=score_final,
                        tipo_match='assunto',
                        motivo=' | '.join(motivos[:2])  # Primeiros 2 motivos
                    ))
        
        # Ordenar por confiança
        resultados.sort(key=lambda x: x.score, reverse=True)
        return resultados
    
    def buscar_combinado(self, termo_remetente: str = "", 
                        termo_assunto: str = "",
                        emails: List = None) -> Dict[str, List[ResultadoBusca]]:
        """
        Busca combinada por remetente E assunto
        
        Exemplo:
        - Remetente: "ch" + Assunto: "reunião"
        - Encontra: emails do chefe que mencionam reunião
        
        Returns:
            {
                'remetente': [...],
                'assunto': [...],
                'combinado': [...]  # Resultados que combinam ambos
            }
        """
        resultados = {
            'remetente': [],
            'assunto': [],
            'combinado': []
        }
        
        if not emails:
            return resultados
        
        # Buscar por remetente
        if termo_remetente:
            resultados['remetente'] = self.buscar_remetente_fuzzy(
                termo_remetente, emails, limiar_confianca=0.5
            )
        
        # Buscar por assunto
        if termo_assunto:
            resultados['assunto'] = self.buscar_assunto_inteligente(
                termo_assunto, emails, limiar_confianca=0.5
            )
        
        # Buscar combinado (apareça em ambos)
        if termo_remetente and termo_assunto:
            emails_remetente = {r.email.id for r in resultados['remetente']}
            emails_assunto = {r.email.id for r in resultados['assunto']}
            emails_combinados_ids = emails_remetente & emails_assunto
            
            resultados['combinado'] = [
                r for r in resultados['remetente'] 
                if r.email.id in emails_combinados_ids
            ]
        
        return resultados
    
    def gerar_sugestoes(self, termo_incompleto: str, 
                        emails: List,
                        max_sugestoes: int = 5) -> List[Tuple[str, str]]:
        """
        Gera sugestões de autocomplete para o usuário
        
        Exemplos:
        - Usuário digita: "ch" → Sugestões: 
          ["chefe@empresa.com", "chefao@gmail.com", ...]
        
        Returns:
            Lista de tuples: (remetente, nome_amigavel)
        """
        sugestoes = []
        remetentes_vistos = set()
        
        resultados = self.buscar_remetente_fuzzy(
            termo_incompleto, emails, limiar_confianca=0.5
        )
        
        for resultado in resultados[:max_sugestoes]:
            remetente = resultado.email.de
            if remetente not in remetentes_vistos:
                nome_amigavel = self._gerar_nome_amigavel(resultado.email)
                sugestoes.append((remetente, nome_amigavel))
                remetentes_vistos.add(remetente)
        
        return sugestoes
    
    # ============= Métodos auxiliares =============
    
    def _calcular_similaridade(self, termo1: str, termo2: str) -> float:
        """
        Calcula similaridade entre dois termos (0-1)
        Usa SequenceMatcher para fuzzy matching
        """
        # Normalizar
        t1 = termo1.lower().strip()
        t2 = termo2.lower().strip()
        
        # Se é prefixo, dar score alto
        if t2.startswith(t1):
            return 0.5 + (len(t1) / len(t2)) * 0.5
        
        # Se está contido, dar score médio
        if t1 in t2:
            return 0.4 + (len(t1) / len(t2)) * 0.4
        
        # Usar SequenceMatcher
        matcher = SequenceMatcher(None, t1, t2)
        return matcher.ratio()
    
    def _buscar_sinonimos(self, termo: str, remetente: str) -> float:
        """
        Verifica se o termo combina com sinônimos conhecidos
        Retorna score (0 ou 0.3-0.7)
        """
        remetente_lower = remetente.lower()
        termo_lower = termo.lower()
        
        for categoria, sinonimos_lista in self.sinonimos.items():
            # Se o termo é um sinônimo
            if any(sin in termo_lower for sin in sinonimos_lista):
                # Se o remetente também está relacionado
                if any(sin in remetente_lower for sin in sinonimos_lista):
                    return 0.7
        
        return 0
    
    def _detectar_categorias(self, termo: str) -> Dict[str, float]:
        """
        Detecta categorias/intenções no termo
        Retorna dict com categoria -> score
        """
        categorias = {}
        termo_lower = termo.lower()
        
        for categoria, padrao in self.padroes_assunto.items():
            if re.search(padrao, termo_lower):
                # Score baseado em quantas palavras-chave aparecem
                matches = re.findall(padrao, termo_lower)
                categorias[categoria] = min(0.9, 0.5 + len(matches) * 0.1)
        
        return categorias
    
    def _verificar_categoria_email(self, email: any, categoria: str) -> bool:
        """Verifica se um email pertence a uma categoria"""
        texto = f"{email.assunto} {email.corpo}".lower()
        padrao = self.padroes_assunto.get(categoria, "")
        return bool(re.search(padrao, texto)) if padrao else False
    
    def _gerar_nome_amigavel(self, email: any) -> str:
        """Gera um nome amigável para exibir ao usuário"""
        remetente = email.de
        
        # Se tem nome antes do @
        if '<' in remetente:
            nome = remetente.split('<')[0].strip()
            return nome if nome else remetente
        
        # Se tem domínio conhecido
        dominio = remetente.split('@')[1] if '@' in remetente else ''
        nomes_conhecidos = {
            'gmail.com': '📧 Gmail',
            'amazon.com.br': '📦 Amazon',
            'shopee.com.br': '🛍️ Shopee',
            'bancoxx.com.br': '🏦 Banco',
            'empresa.com': '💼 Empresa',
        }
        
        for dom, nome in nomes_conhecidos.items():
            if dom in dominio:
                return nome
        
        # Padrão: nome@dominio
        nome = remetente.split('@')[0]
        return nome.capitalize()
    
    def formatar_resultado(self, resultado: ResultadoBusca) -> str:
        """Formata um resultado para exibição"""
        score_str = f"{'⭐' * int(resultado.score * 5)}"
        return f"""
{score_str}
De: {resultado.email.de}
Assunto: {resultado.email.assunto}
Motivo: {resultado.motivo}
Confiança: {resultado.score:.0%}
"""
    
    def formatar_resultados(self, resultados: List[ResultadoBusca], 
                            max_itens: int = 5) -> str:
        """Formata múltiplos resultados para exibição"""
        if not resultados:
            return "❌ Nenhum e-mail encontrado"
        
        texto = f"🔍 Encontrados {len(resultados)} e-mail(is)\n"
        texto += "─" * 40 + "\n\n"
        
        for i, resultado in enumerate(resultados[:max_itens], 1):
            score_str = f"{'⭐' * int(resultado.score * 5)}"
            texto += f"{i}. {score_str}\n"
            texto += f"   De: {resultado.email.de}\n"
            texto += f"   Assunto: {resultado.email.assunto[:60]}\n"
            if resultado.email.resumo:
                texto += f"   📝 {resultado.email.resumo[:50]}...\n"
            texto += f"   ✅ Confiança: {resultado.score:.0%}\n"
            texto += "\n"
        
        if len(resultados) > max_itens:
            texto += f"... e mais {len(resultados) - max_itens} e-mail(is)"
        
        return texto
