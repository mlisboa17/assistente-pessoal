"""
🧾 Módulo de Processamento de Comprovantes
Reconhece e categoriza despesas a partir de imagens de:
- Comprovantes de pagamento
- PIX
- Recibos
- Notas fiscais
"""
import json
import os
import re
import base64
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
import hashlib


@dataclass
class ComprovanteExtraido:
    """Dados extraídos de um comprovante"""
    id: str
    tipo: str  # 'pix', 'transferencia', 'boleto', 'cartao', 'recibo', 'nf'
    valor: float
    descricao: str
    data: str
    destinatario: str = ""
    origem: str = ""
    categoria_sugerida: str = "outros"
    confianca: float = 0.0  # 0 a 1
    texto_original: str = ""
    user_id: str = ""
    status: str = "pendente"  # pendente, confirmado, cancelado
    criado_em: str = ""
    
    def to_dict(self):
        return asdict(self)


class ComprovantesModule:
    """Processa e categoriza comprovantes de pagamento"""
    
    # Padrões para extração de dados
    PADROES_VALOR = [
        r'R\$\s*([\d.,]+)',
        r'Valor:?\s*R?\$?\s*([\d.,]+)',
        r'VALOR:?\s*R?\$?\s*([\d.,]+)',
        r'Total:?\s*R?\$?\s*([\d.,]+)',
        r'TOTAL:?\s*R?\$?\s*([\d.,]+)',
        r'Pagamento:?\s*R?\$?\s*([\d.,]+)',
        r'(\d{1,3}(?:\.\d{3})*,\d{2})',  # Formato brasileiro: 1.234,56
    ]
    
    PADROES_DATA = [
        r'(\d{2}/\d{2}/\d{4})',
        r'(\d{2}/\d{2}/\d{2})',
        r'(\d{2}-\d{2}-\d{4})',
        r'(\d{4}-\d{2}-\d{2})',
        r'Data:?\s*(\d{2}/\d{2}/\d{4})',
    ]
    
    PADROES_PIX = [
        r'PIX',
        r'Chave PIX',
        r'Pagamento instantâneo',
        r'Transferência PIX',
        r'Comprovante PIX',
    ]
    
    PADROES_DESTINATARIO = [
        r'Para:?\s*([^\n]+)',
        r'Destinatário:?\s*([^\n]+)',
        r'DESTINATÁRIO:?\s*([^\n]+)',
        r'Favorecido:?\s*([^\n]+)',
        r'Nome:?\s*([^\n]+)',
        r'Recebedor:?\s*([^\n]+)',
    ]
    
    # Palavras-chave para categorização
    CATEGORIAS_KEYWORDS = {
        'alimentacao': [
            'restaurante', 'lanchonete', 'padaria', 'mercado', 'supermercado',
            'ifood', 'uber eats', 'rappi', 'delivery', 'pizza', 'burger',
            'açougue', 'hortifruti', 'feira', 'bar', 'cafe', 'café',
            'mcdonald', 'subway', 'bk', 'atacadão', 'assaí', 'carrefour',
            'extra', 'pão de açúcar', 'big', 'mateus', 'gbarbosa'
        ],
        'combustivel': [
            'posto', 'gasolina', 'combustível', 'shell', 'br', 'ipiranga',
            'petrobras', 'ale', 'abastecimento', 'diesel', 'etanol', 'gnv'
        ],
        'transporte': [
            'uber', '99', 'taxi', 'estacionamento', 'pedágio', 'ônibus',
            'metro', 'metrô', 'passagem', 'cabify', '99pop', 'indriver'
        ],
        'moradia': [
            'aluguel', 'condomínio', 'luz', 'energia', 'celpe', 'enel',
            'água', 'compesa', 'saneamento', 'gás', 'internet', 'telefone',
            'tim', 'vivo', 'claro', 'oi', 'net', 'sky'
        ],
        'saude': [
            'farmácia', 'drogaria', 'hospital', 'clínica', 'médico',
            'consulta', 'exame', 'laboratório', 'dentista', 'plano de saúde',
            'unimed', 'hapvida', 'pague menos', 'drogasil', 'panvel'
        ],
        'lazer': [
            'cinema', 'teatro', 'show', 'netflix', 'spotify', 'amazon',
            'disney', 'hbo', 'streaming', 'ingresso', 'evento', 'academia',
            'smartfit', 'bluefit', 'gym'
        ],
        'educacao': [
            'escola', 'faculdade', 'curso', 'livro', 'udemy', 'alura',
            'mensalidade', 'matrícula', 'apostila'
        ],
        'vestuario': [
            'roupa', 'loja', 'shopping', 'renner', 'riachuelo', 'c&a',
            'marisa', 'hering', 'centauro', 'netshoes', 'zattini'
        ],
        'tecnologia': [
            'celular', 'computador', 'notebook', 'eletrônico', 'samsung',
            'apple', 'xiaomi', 'magazine', 'casas bahia', 'americanas'
        ]
    }
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.comprovantes_file = os.path.join(data_dir, "comprovantes.json")
        self.pendentes_file = os.path.join(data_dir, "comprovantes_pendentes.json")
        
        os.makedirs(data_dir, exist_ok=True)
        self._load_data()
    
    def _load_data(self):
        """Carrega dados do disco"""
        if os.path.exists(self.comprovantes_file):
            with open(self.comprovantes_file, 'r', encoding='utf-8') as f:
                self.comprovantes = json.load(f)
        else:
            self.comprovantes = []
        
        if os.path.exists(self.pendentes_file):
            with open(self.pendentes_file, 'r', encoding='utf-8') as f:
                self.pendentes = json.load(f)
        else:
            self.pendentes = {}
    
    def _save_data(self):
        """Salva dados no disco"""
        with open(self.comprovantes_file, 'w', encoding='utf-8') as f:
            json.dump(self.comprovantes, f, ensure_ascii=False, indent=2)
    
    def _save_pendentes(self):
        """Salva comprovantes pendentes"""
        with open(self.pendentes_file, 'w', encoding='utf-8') as f:
            json.dump(self.pendentes, f, ensure_ascii=False, indent=2)
    
    def _salvar_pendente(self, comprovante: Dict):
        """Salva um comprovante como pendente para confirmação"""
        user_id = comprovante.get('user_id', 'default')
        self.pendentes[user_id] = comprovante
        self._save_pendentes()
    
    def _gerar_id(self, texto: str) -> str:
        """Gera ID único baseado no conteúdo"""
        hash_obj = hashlib.md5(f"{texto}{datetime.now().isoformat()}".encode())
        return hash_obj.hexdigest()[:8]
    
    def _extrair_valor(self, texto: str) -> Optional[float]:
        """Extrai valor monetário do texto"""
        for padrao in self.PADROES_VALOR:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                valor_str = match.group(1)
                # Converte formato brasileiro para float
                valor_str = valor_str.replace('.', '').replace(',', '.')
                try:
                    valor = float(valor_str)
                    if 0.01 <= valor <= 1000000:  # Valores razoáveis
                        return valor
                except:
                    continue
        return None
    
    def _extrair_data(self, texto: str) -> str:
        """Extrai data do texto"""
        for padrao in self.PADROES_DATA:
            match = re.search(padrao, texto)
            if match:
                data_str = match.group(1)
                # Tenta converter para formato padrão
                for fmt in ['%d/%m/%Y', '%d/%m/%y', '%d-%m-%Y', '%Y-%m-%d']:
                    try:
                        dt = datetime.strptime(data_str, fmt)
                        return dt.strftime('%Y-%m-%d')
                    except:
                        continue
        return datetime.now().strftime('%Y-%m-%d')
    
    def _detectar_tipo(self, texto: str) -> str:
        """Detecta tipo de comprovante"""
        texto_lower = texto.lower()
        
        if any(re.search(p, texto, re.IGNORECASE) for p in self.PADROES_PIX):
            return 'pix'
        elif 'transferência' in texto_lower or 'ted' in texto_lower or 'doc' in texto_lower:
            return 'transferencia'
        elif 'boleto' in texto_lower or 'código de barras' in texto_lower:
            return 'boleto'
        elif 'cartão' in texto_lower or 'crédito' in texto_lower or 'débito' in texto_lower:
            return 'cartao'
        elif 'nota fiscal' in texto_lower or 'nf-e' in texto_lower or 'danfe' in texto_lower:
            return 'nf'
        elif 'recibo' in texto_lower:
            return 'recibo'
        else:
            return 'outros'
    
    def _extrair_destinatario(self, texto: str) -> str:
        """Extrai nome do destinatário/estabelecimento"""
        for padrao in self.PADROES_DESTINATARIO:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                dest = match.group(1).strip()
                # Limpa o nome
                dest = re.sub(r'\s+', ' ', dest)
                if len(dest) > 2 and len(dest) < 100:
                    return dest
        return ""
    
    def _sugerir_categoria(self, texto: str, destinatario: str) -> Tuple[str, float]:
        """Sugere categoria baseado no texto e destinatário"""
        texto_analise = f"{texto} {destinatario}".lower()
        
        melhor_categoria = 'outros'
        melhor_score = 0
        
        for categoria, keywords in self.CATEGORIAS_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in texto_analise:
                    score += 1
                    # Bonus se match exato no destinatário
                    if keyword.lower() in destinatario.lower():
                        score += 2
            
            if score > melhor_score:
                melhor_score = score
                melhor_categoria = categoria
        
        # Calcula confiança
        confianca = min(melhor_score / 5.0, 1.0) if melhor_score > 0 else 0.0
        
        return melhor_categoria, confianca
    
    def processar_texto_comprovante(self, texto: str, user_id: str) -> Dict[str, Any]:
        """
        Processa texto extraído de um comprovante (OCR)
        Retorna dados extraídos para confirmação
        """
        # Extrai informações
        valor = self._extrair_valor(texto)
        data = self._extrair_data(texto)
        tipo = self._detectar_tipo(texto)
        destinatario = self._extrair_destinatario(texto)
        categoria, confianca = self._sugerir_categoria(texto, destinatario)
        
        # Cria descrição automática
        if destinatario:
            descricao = f"Pagamento para {destinatario}"
        else:
            descricao = f"Pagamento via {tipo.upper()}"
        
        # Cria comprovante pendente
        comp_id = self._gerar_id(texto)
        comprovante = ComprovanteExtraido(
            id=comp_id,
            tipo=tipo,
            valor=valor or 0.0,
            descricao=descricao,
            data=data,
            destinatario=destinatario,
            categoria_sugerida=categoria,
            confianca=confianca,
            texto_original=texto[:500],  # Limita tamanho
            user_id=user_id,
            status='pendente',
            criado_em=datetime.now().isoformat()
        )
        
        # Salva como pendente
        self.pendentes[user_id] = comprovante.to_dict()
        self._save_pendentes()
        
        return comprovante.to_dict()
    
    def tem_pendente(self, user_id: str) -> bool:
        """Verifica se usuário tem comprovante pendente"""
        return user_id in self.pendentes
    
    def get_pendente(self, user_id: str) -> Optional[Dict]:
        """Obtém comprovante pendente do usuário"""
        return self.pendentes.get(user_id)
    
    def confirmar_comprovante(self, user_id: str, categoria: str = None, 
                              valor: float = None, descricao: str = None,
                              financas_module=None) -> Dict[str, Any]:
        """
        Confirma e salva comprovante
        Também registra como despesa no módulo de finanças
        """
        if user_id not in self.pendentes:
            return {'erro': 'Nenhum comprovante pendente'}
        
        comp = self.pendentes[user_id]
        
        # Atualiza com dados confirmados
        if categoria:
            comp['categoria_sugerida'] = categoria
        if valor:
            comp['valor'] = valor
        if descricao:
            comp['descricao'] = descricao
        
        comp['status'] = 'confirmado'
        
        # Move para lista de confirmados
        self.comprovantes.append(comp)
        self._save_data()
        
        # Remove dos pendentes
        del self.pendentes[user_id]
        self._save_pendentes()
        
        # 🆕 INTEGRAÇÃO COM FINANÇAS - Registra como despesa
        if financas_module and comp.get('valor', 0) > 0:
            try:
                self._registrar_despesa_financas(comp, financas_module)
                comp['despesa_registrada'] = True
            except Exception as e:
                comp['erro_financas'] = str(e)
        
        return comp
    
    def _registrar_despesa_financas(self, comp: Dict, financas_module):
        """Registra o comprovante como despesa no módulo de finanças"""
        from uuid import uuid4
        
        # Mapeia categorias do comprovante para o financas
        mapa_categorias = {
            'alimentacao': 'alimentacao',
            'combustivel': 'combustivel',
            'transporte': 'transporte',
            'moradia': 'moradia',
            'saude': 'saude',
            'lazer': 'lazer',
            'educacao': 'educacao',
            'vestuario': 'vestuario',
            'tecnologia': 'tecnologia',
            'outros': 'outros'
        }
        
        categoria = mapa_categorias.get(comp.get('categoria_sugerida', 'outros'), 'outros')
        
        # Cria descrição mais detalhada
        tipo = comp.get('tipo', 'pagamento').upper()
        destinatario = comp.get('destinatario', '')
        descricao_base = comp.get('descricao', 'Pagamento')
        
        if destinatario:
            descricao = f"[{tipo}] {descricao_base} - {destinatario}"
        else:
            descricao = f"[{tipo}] {descricao_base}"
        
        # Usa a estrutura do financas_module
        from dataclasses import asdict
        
        transacao_data = {
            'id': f"comp_{comp.get('id', str(uuid4())[:8])}",
            'tipo': 'saida',
            'valor': comp.get('valor', 0),
            'descricao': descricao[:100],  # Limita tamanho
            'categoria': categoria,
            'data': comp.get('data', datetime.now().strftime('%Y-%m-%d')),
            'user_id': comp.get('user_id', ''),
            'criado_em': datetime.now().isoformat(),
            'origem': 'comprovante'  # Marca origem
        }
        
        financas_module.transacoes.append(transacao_data)
        financas_module._save_data()
    
    def cancelar_pendente(self, user_id: str) -> bool:
        """Cancela comprovante pendente"""
        if user_id in self.pendentes:
            del self.pendentes[user_id]
            self._save_pendentes()
            return True
        return False
    
    def formatar_confirmacao(self, comp: Dict) -> str:
        """Formata mensagem de confirmação para o usuário"""
        tipo_emoji = {
            'pix': '📲',
            'transferencia': '🏦',
            'boleto': '📄',
            'cartao': '💳',
            'recibo': '🧾',
            'nf': '📋',
            'outros': '💰'
        }
        
        emoji = tipo_emoji.get(comp.get('tipo', 'outros'), '💰')
        valor = comp.get('valor', 0)
        categoria = comp.get('categoria_sugerida', 'outros')
        confianca = comp.get('confianca', 0)
        destinatario = comp.get('destinatario', '')
        data = comp.get('data', '')
        
        # Formata data
        try:
            dt = datetime.strptime(data, '%Y-%m-%d')
            data_fmt = dt.strftime('%d/%m/%Y')
        except:
            data_fmt = data
        
        # Indicador de confiança
        if confianca >= 0.7:
            conf_txt = "✅ Alta"
        elif confianca >= 0.4:
            conf_txt = "⚠️ Média"
        else:
            conf_txt = "❓ Baixa"
        
        # Nome da categoria
        categorias_nome = {
            'alimentacao': '🍔 Alimentação',
            'combustivel': '⛽ Combustível',
            'transporte': '🚗 Transporte',
            'moradia': '🏠 Moradia',
            'saude': '🏥 Saúde',
            'lazer': '🎮 Lazer',
            'educacao': '📚 Educação',
            'vestuario': '👕 Vestuário',
            'tecnologia': '📱 Tecnologia',
            'outros': '📦 Outros'
        }
        
        cat_nome = categorias_nome.get(categoria, f'📦 {categoria.title()}')
        
        return f"""🧾 *Comprovante Detectado!*

{emoji} *Tipo:* {comp.get('tipo', 'Pagamento').upper()}
💰 *Valor:* R$ {valor:.2f}
📅 *Data:* {data_fmt}
🏪 *Destinatário:* {destinatario or 'Não identificado'}

━━━━━━━━━━━━━━━━━━━━━

📊 *Categoria Sugerida:* {cat_nome}
🎯 *Confiança:* {conf_txt}

━━━━━━━━━━━━━━━━━━━━━

*Confirma esses dados?*

✅ Digite *SIM* para confirmar
✏️ Digite *EDITAR* para alterar
❌ Digite *NÃO* para cancelar

Ou digite a categoria correta:
1-Alimentação, 2-Combustível, 3-Transporte
4-Moradia, 5-Saúde, 6-Lazer
7-Educação, 8-Vestuário, 9-Tecnologia, 0-Outros"""
    
    async def handle(self, command: str, args: List[str], user_id: str, 
                     attachments: list = None, financas_module=None) -> str:
        """Processa comandos do módulo"""
        
        if command == 'comprovantes':
            return self._listar_comprovantes(user_id)
        
        return "Use: envie uma imagem de comprovante, PIX ou recibo"
    
    def processar_resposta_confirmacao(self, resposta: str, user_id: str, 
                                       financas_module=None) -> Optional[str]:
        """
        Processa resposta do usuário para confirmação de comprovante
        Retorna mensagem de resposta ou None se não era uma resposta válida
        """
        if not self.tem_pendente(user_id):
            return None
        
        resposta_lower = resposta.strip().lower()
        
        # Mapeamento de números para categorias
        categorias_num = {
            '1': 'alimentacao',
            '2': 'combustivel',
            '3': 'transporte',
            '4': 'moradia',
            '5': 'saude',
            '6': 'lazer',
            '7': 'educacao',
            '8': 'vestuario',
            '9': 'tecnologia',
            '0': 'outros'
        }
        
        # Verifica se é confirmação
        if resposta_lower in ['sim', 's', 'yes', 'y', 'confirma', 'ok', 'confirmar']:
            comp = self.confirmar_comprovante(user_id, financas_module=financas_module)
            return self._formatar_comprovante_salvo(comp)
        
        # Verifica se é cancelamento
        elif resposta_lower in ['não', 'nao', 'n', 'no', 'cancelar', 'cancela']:
            self.cancelar_pendente(user_id)
            return "❌ Comprovante cancelado. Nenhum registro foi salvo."
        
        # Verifica se é editar
        elif resposta_lower in ['editar', 'alterar', 'mudar', 'corrigir']:
            comp = self.get_pendente(user_id)
            return self._formatar_edicao(comp)
        
        # Verifica se é número de categoria
        elif resposta_lower in categorias_num:
            categoria = categorias_num[resposta_lower]
            comp = self.confirmar_comprovante(user_id, categoria=categoria, 
                                               financas_module=financas_module)
            return self._formatar_comprovante_salvo(comp)
        
        # Verifica se é nome de categoria
        elif resposta_lower in ['alimentacao', 'alimentação', 'comida']:
            comp = self.confirmar_comprovante(user_id, categoria='alimentacao',
                                               financas_module=financas_module)
            return self._formatar_comprovante_salvo(comp)
        elif resposta_lower in ['combustivel', 'combustível', 'gasolina']:
            comp = self.confirmar_comprovante(user_id, categoria='combustivel',
                                               financas_module=financas_module)
            return self._formatar_comprovante_salvo(comp)
        elif resposta_lower in ['transporte', 'uber', 'taxi']:
            comp = self.confirmar_comprovante(user_id, categoria='transporte',
                                               financas_module=financas_module)
            return self._formatar_comprovante_salvo(comp)
        elif resposta_lower in ['moradia', 'casa', 'aluguel']:
            comp = self.confirmar_comprovante(user_id, categoria='moradia',
                                               financas_module=financas_module)
            return self._formatar_comprovante_salvo(comp)
        elif resposta_lower in ['saude', 'saúde', 'farmacia', 'farmácia']:
            comp = self.confirmar_comprovante(user_id, categoria='saude',
                                               financas_module=financas_module)
            return self._formatar_comprovante_salvo(comp)
        elif resposta_lower in ['lazer', 'diversao', 'diversão']:
            comp = self.confirmar_comprovante(user_id, categoria='lazer',
                                               financas_module=financas_module)
            return self._formatar_comprovante_salvo(comp)
        elif resposta_lower in ['educacao', 'educação', 'curso', 'escola']:
            comp = self.confirmar_comprovante(user_id, categoria='educacao',
                                               financas_module=financas_module)
            return self._formatar_comprovante_salvo(comp)
        elif resposta_lower in ['vestuario', 'vestuário', 'roupa']:
            comp = self.confirmar_comprovante(user_id, categoria='vestuario',
                                               financas_module=financas_module)
            return self._formatar_comprovante_salvo(comp)
        elif resposta_lower in ['tecnologia', 'tech', 'eletrônicos']:
            comp = self.confirmar_comprovante(user_id, categoria='tecnologia',
                                               financas_module=financas_module)
            return self._formatar_comprovante_salvo(comp)
        elif resposta_lower in ['outros', 'outro']:
            comp = self.confirmar_comprovante(user_id, categoria='outros',
                                               financas_module=financas_module)
            return self._formatar_comprovante_salvo(comp)
        
        return None
    
    def _formatar_comprovante_salvo(self, comp: Dict) -> str:
        """Formata mensagem de sucesso ao salvar comprovante"""
        if 'erro' in comp:
            return f"❌ {comp['erro']}"
        
        categorias_emoji = {
            'alimentacao': '🍔',
            'combustivel': '⛽',
            'transporte': '🚗',
            'moradia': '🏠',
            'saude': '🏥',
            'lazer': '🎮',
            'educacao': '📚',
            'vestuario': '👕',
            'tecnologia': '📱',
            'outros': '📦'
        }
        
        categoria = comp.get('categoria_sugerida', 'outros')
        emoji = categorias_emoji.get(categoria, '📦')
        valor = comp.get('valor', 0)
        descricao = comp.get('descricao', '')
        
        msg = f"""✅ *Comprovante Salvo com Sucesso!*

{emoji} *Categoria:* {categoria.capitalize()}
💰 *Valor:* R$ {valor:.2f}
📝 *Descrição:* {descricao}"""

        if comp.get('despesa_registrada'):
            msg += """

💸 *Despesa registrada automaticamente!*
📊 Use /financas para ver seu resumo."""
        
        return msg
    
    def _formatar_edicao(self, comp: Dict) -> str:
        """Formata mensagem para edição"""
        return f"""✏️ *Editando Comprovante*

Valor atual: R$ {comp.get('valor', 0):.2f}
Categoria: {comp.get('categoria_sugerida', 'outros')}
Descrição: {comp.get('descricao', '')}

Para editar, envie no formato:
`valor:100.50` - Para alterar valor
`cat:alimentacao` - Para alterar categoria  
`desc:Nova descrição` - Para alterar descrição

Ou digite *SIM* para confirmar como está."""
    
    def _listar_comprovantes(self, user_id: str) -> str:
        """Lista comprovantes salvos do usuário"""
        comps_user = [c for c in self.comprovantes if c.get('user_id') == user_id]
        
        if not comps_user:
            return "📭 Nenhum comprovante salvo ainda.\n\nEnvie uma foto de um comprovante de pagamento!"
        
        # Últimos 10
        ultimos = sorted(comps_user, key=lambda x: x.get('criado_em', ''), reverse=True)[:10]
        
        resp = "🧾 *Últimos Comprovantes:*\n\n"
        
        total = 0
        for comp in ultimos:
            valor = comp.get('valor', 0)
            total += valor
            data = comp.get('data', '')[:10]
            dest = comp.get('destinatario', 'N/A')[:20]
            
            resp += f"• {data} - R$ {valor:.2f} - {dest}\n"
        
        resp += f"\n💰 *Total:* R$ {total:.2f}"
        
        return resp


# Instância global
_comprovantes_module = None

def get_comprovantes_module(data_dir: str = "data") -> ComprovantesModule:
    global _comprovantes_module
    if _comprovantes_module is None:
        _comprovantes_module = ComprovantesModule(data_dir)
    return _comprovantes_module
