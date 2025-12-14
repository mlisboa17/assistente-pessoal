"""
🧾 Módulo de Processamento de Comprovantes
Reconhece e categoriza despesas a partir de imagens de:
- Comprovantes de pagamento (PIX, Transferências)
- Boletos pagos
- Recibos
- Notas fiscais
Usa extractores brasileiros e OCR (gratuito) para extração
"""
import json
import os
import re
import base64
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
import hashlib

# Sinônimos para extração melhorada
from modules.sinonimos_documentos import (
    criar_prompt_extracao_melhorado,
    identificar_tipo_documento,
    extrair_com_sinonimos,
    SINONIMOS_VALOR,
    SINONIMOS_BENEFICIARIO,
    SINONIMOS_PAGADOR,
)

# Extractores e OCR
try:
    from modules.extrator_brasil import ExtratorDocumentosBrasil
    EXTRATOR_BRASIL_AVAILABLE = True
except ImportError:
    EXTRATOR_BRASIL_AVAILABLE = False

try:
    from modules.ocr_engine import OCREngine
    OCR_ENGINE_AVAILABLE = True
except ImportError:
    OCR_ENGINE_AVAILABLE = False


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
        
        # Tenta carregar extrator brasileiro especializado
        self._extrator_brasil = None
        try:
            from modules.extrator_brasil import ExtratorDocumentosBrasil
            self._extrator_brasil = ExtratorDocumentosBrasil()
            print("🇧🇷 Extrator de documentos brasileiros carregado!")
        except ImportError as e:
            print(f"⚠️ Extrator brasileiro não disponível: {e}")
        
        # 🆕 Sistema de confirmação de documentos
        try:
            from modules.confirmacao_documentos import get_confirmacao_documentos
            self.confirmacao = get_confirmacao_documentos()
        except ImportError:
            self.confirmacao = None
        
        # Módulos relacionados
        self.financas_module = None
        
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
        """Extrai valor monetário do texto (última ocorrência)"""
        # Usa padrões locais com findall para última ocorrência
        for padrao in self.PADROES_VALOR:
            matches = re.findall(padrao, texto, re.IGNORECASE)
            if matches:
                valor_str = matches[-1]  # Última ocorrência
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
        elif 'transferência' in texto_lower or 'ted' in texto_lower:
            return 'transferencia'
        elif 'boleto' in texto_lower or 'código de barras' in texto_lower or 'comprovante de pagamento' in texto_lower or 'titulo' in texto_lower:
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
    
    def processar_imagem_brasil(self, image_data: bytes, user_id: str) -> Dict[str, Any]:
        """
        Processa imagem usando extrator brasileiro especializado
        Detecta automaticamente: Boleto, PIX, TED/DOC
        """
        if not self._extrator_brasil:
            return {'erro': 'Extrator brasileiro não disponível'}
        
        resultado = self._extrator_brasil.extrair_automatico(image_data=image_data)
        
        tipo = resultado.get('tipo', 'desconhecido')
        dados = resultado.get('dados', {})
        
        # Converte para formato padrão de comprovante
        if tipo == 'boleto':
            return self._converter_boleto(dados, user_id)
        elif tipo == 'pix':
            return self._converter_pix(dados, user_id)
        elif tipo == 'transferencia':
            return self._converter_transferencia(dados, user_id)
        else:
            # Usa processamento genérico
            texto = resultado.get('texto_extraido', '')
            return self.processar_texto_comprovante(texto, user_id)
    
    def _converter_boleto(self, dados: Dict, user_id: str) -> Dict[str, Any]:
        """Converte dados de boleto para comprovante"""
        comp_id = self._gerar_id(dados.get('linha_digitavel', ''))
        
        descricao = f"Boleto - {dados.get('beneficiario', 'Não identificado')}"
        if dados.get('documento'):
            descricao += f" (Doc: {dados['documento']})"
        
        comprovante = ComprovanteExtraido(
            id=comp_id,
            tipo='boleto',
            valor=dados.get('valor', 0.0),
            descricao=descricao,
            data=dados.get('vencimento', datetime.now().strftime('%Y-%m-%d')),
            destinatario=dados.get('beneficiario', ''),
            categoria_sugerida='outros',
            confianca=dados.get('confianca', 0.0) / 100,
            texto_original=dados.get('linha_digitavel', ''),
            user_id=user_id,
            status='pendente',
            criado_em=datetime.now().isoformat()
        )
        
        # Adiciona dados extras do boleto
        comp_dict = comprovante.to_dict()
        comp_dict['boleto_dados'] = {
            'linha_digitavel': dados.get('linha_digitavel', ''),
            'codigo_barras': dados.get('codigo_barras', ''),
            'banco': dados.get('banco', ''),
            'beneficiario_cnpj': dados.get('beneficiario_cnpj', ''),
            'nosso_numero': dados.get('nosso_numero', '')
        }
        
        self.pendentes[user_id] = comp_dict
        self._save_pendentes()
        
        return comp_dict
    
    def _converter_pix(self, dados: Dict, user_id: str) -> Dict[str, Any]:
        """Converte dados de PIX para comprovante"""
        comp_id = self._gerar_id(dados.get('id_transacao', str(datetime.now())))
        
        if dados.get('tipo_transacao') == 'enviado':
            descricao = f"PIX enviado para {dados.get('destino_nome', 'Não identificado')}"
            destinatario = dados.get('destino_nome', '')
        else:
            descricao = f"PIX recebido de {dados.get('origem_nome', 'Não identificado')}"
            destinatario = dados.get('origem_nome', '')
        
        # Tenta categorizar pelo destinatário
        categoria, confianca = self._sugerir_categoria(descricao, destinatario)
        
        comprovante = ComprovanteExtraido(
            id=comp_id,
            tipo='pix',
            valor=dados.get('valor', 0.0),
            descricao=descricao,
            data=dados.get('data_hora', datetime.now().strftime('%Y-%m-%d'))[:10],
            destinatario=destinatario,
            categoria_sugerida=categoria,
            confianca=max(confianca, dados.get('confianca', 0.0) / 100),
            texto_original=dados.get('id_transacao', ''),
            user_id=user_id,
            status='pendente',
            criado_em=datetime.now().isoformat()
        )
        
        # Adiciona dados extras do PIX
        comp_dict = comprovante.to_dict()
        comp_dict['pix_dados'] = {
            'chave_pix': dados.get('chave_pix', ''),
            'tipo_chave': dados.get('tipo_chave', ''),
            'id_transacao': dados.get('id_transacao', ''),
            'origem_banco': dados.get('origem_banco', ''),
            'destino_banco': dados.get('destino_banco', ''),
            'origem_documento': dados.get('origem_documento', ''),
            'destino_documento': dados.get('destino_documento', '')
        }
        
        self.pendentes[user_id] = comp_dict
        self._save_pendentes()
        
        return comp_dict
    
    def _converter_transferencia(self, dados: Dict, user_id: str) -> Dict[str, Any]:
        """Converte dados de TED/DOC para comprovante"""
        comp_id = self._gerar_id(dados.get('id_transacao', str(datetime.now())))
        
        tipo_trans = dados.get('tipo', 'Transferência')
        descricao = f"{tipo_trans} para {dados.get('destino_nome', 'Não identificado')}"
        
        comprovante = ComprovanteExtraido(
            id=comp_id,
            tipo='transferencia',
            valor=dados.get('valor', 0.0),
            descricao=descricao,
            data=dados.get('data_hora', datetime.now().strftime('%Y-%m-%d'))[:10],
            destinatario=dados.get('destino_nome', ''),
            categoria_sugerida='outros',
            confianca=dados.get('confianca', 0.0) / 100,
            texto_original=dados.get('id_transacao', ''),
            user_id=user_id,
            status='pendente',
            criado_em=datetime.now().isoformat()
        )
        
        # Adiciona dados extras
        comp_dict = comprovante.to_dict()
        comp_dict['transferencia_dados'] = {
            'tipo': dados.get('tipo', ''),
            'origem_banco': dados.get('origem_banco', ''),
            'destino_banco': dados.get('destino_banco', ''),
            'destino_agencia': dados.get('destino_agencia', ''),
            'destino_conta': dados.get('destino_conta', '')
        }
        
        self.pendentes[user_id] = comp_dict
        self._save_pendentes()
        
        return comp_dict
    
    def tem_pendente(self, user_id: str) -> bool:
        """Verifica se usuário tem comprovante pendente (válido por 5 min)"""
        if user_id not in self.pendentes:
            return False
        
        # Verifica se o comprovante pendente não expirou (5 minutos)
        pendente = self.pendentes[user_id]
        criado_em = pendente.get('criado_em', '')
        if criado_em:
            try:
                data_criacao = datetime.fromisoformat(criado_em)
                agora = datetime.now()
                diferenca = (agora - data_criacao).total_seconds()
                
                # Se passou mais de 5 minutos, remove o pendente
                if diferenca > 300:  # 5 minutos em segundos
                    del self.pendentes[user_id]
                    self._save_pendentes()
                    return False
            except:
                pass
        
        return True
    
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
    
    def processar_imagem_com_gemini_vision(self, image_data: bytes, user_id: str) -> Dict[str, Any]:
        """
        Processa comprovante usando extractores brasileiros e OCR (gratuito)
        
        Extrai com alta precisão:
        - BENEFICIÁRIO: quem recebe o pagamento
        - PAGADOR: quem paga  
        - VALOR: montante
        - TODO O DOCUMENTO: tipo, data, dados bancários, etc
        
        Usa bibliotecas open-source em vez de APIs pagas
        """
        try:
            # === MÉTODO 1: EXTRATOR BRASIL (PIX, Transferências, Boletos) ===
            if EXTRATOR_BRASIL_AVAILABLE:
                try:
                    extrator = ExtratorDocumentosBrasil()
                    
                    # Tenta extrair PIX
                    resultado_pix = extrator.extrair_pix_imagem(image_data)
                    if resultado_pix and resultado_pix.valor > 0:
                        print(f"[EXTRATOR] PIX identificado: {resultado_pix.valor}")
                        return self._converter_pix_extrator(resultado_pix, user_id)
                    
                    # Tenta extrair transferência
                    resultado_transf = extrator.extrair_transferencia_imagem(image_data)
                    if resultado_transf and resultado_transf.valor > 0:
                        print(f"[EXTRATOR] Transferência identificada: {resultado_transf.valor}")
                        return self._converter_transferencia_extrator(resultado_transf, user_id)
                    
                    # Tenta extrair boleto
                    resultado_boleto = extrator.extrair_boleto_imagem(image_data)
                    if resultado_boleto and resultado_boleto.valor > 0:
                        print(f"[EXTRATOR] Boleto identificado: {resultado_boleto.valor}")
                        return self._converter_boleto_extrator(resultado_boleto, user_id)
                        
                except Exception as e:
                    print(f"[EXTRATOR-BRASIL] Erro: {e}")
            
            # === MÉTODO 2: OCR + SINÔNIMOS (Fallback) ===
            if OCR_ENGINE_AVAILABLE:
                try:
                    ocr = OCREngine()
                    texto = ocr.extrair_texto_imagem(image_data)
                    
                    if texto:
                        print(f"[OCR] Texto extraído ({len(texto)} caracteres)")
                        
                        # Identifica tipo de documento
                        tipo_doc = identificar_tipo_documento(texto)
                        
                        # Extrai informações usando sinônimos
                        dados = self._extrair_com_sinonimos_ocr(texto, tipo_doc)
                        
                        if dados.get('valor', 0) > 0:
                            return self._converter_dados_ocr(dados, user_id)
                            
                except Exception as e:
                    print(f"[OCR] Erro: {e}")
            
            return {'erro': 'Não foi possível processar a imagem'}
            
        except Exception as e:
            print(f"[PROCESSAMENTO] Erro geral: {e}")
            return {'erro': f'Erro ao processar: {str(e)[:50]}'}
    
    def _extrair_com_sinonimos_ocr(self, texto: str, tipo_doc: str) -> Dict[str, Any]:
        """Extrai dados do texto OCR usando sinônimos"""
        dados = {
            'tipo': tipo_doc,
            'valor': 0.0,
            'beneficiario': '',
            'pagador': '',
            'descricao': '',
        }
        
        # Extrai valor
        valor_matches = extrair_com_sinonimos(texto, 'valor')
        if valor_matches:
            for match in valor_matches:
                # Procura número após a palavra-chave
                padrao = f"{re.escape(match)}[\\s:]*R?\\$?[\\s]*([\\d.,]+)"
                encontro = re.search(padrao, texto, re.IGNORECASE)
                if encontro:
                    valor_str = encontro.group(1).replace(',', '.')
                    try:
                        dados['valor'] = float(valor_str)
                        break
                    except:
                        pass
        
        # Extrai beneficiário
        ben_matches = extrair_com_sinonimos(texto, 'beneficiario')
        if ben_matches:
            for match in ben_matches:
                padrao = f"{re.escape(match)}[:\\s]*([^\\n]+)"
                encontro = re.search(padrao, texto, re.IGNORECASE)
                if encontro:
                    nome = encontro.group(1).strip()
                    if len(nome) > 3 and len(nome) < 100:
                        dados['beneficiario'] = nome[:50]
                        break
        
        # Extrai pagador
        pag_matches = extrair_com_sinonimos(texto, 'pagador')
        if pag_matches:
            for match in pag_matches:
                padrao = f"{re.escape(match)}[:\\s]*([^\\n]+)"
                encontro = re.search(padrao, texto, re.IGNORECASE)
                if encontro:
                    nome = encontro.group(1).strip()
                    if len(nome) > 3 and len(nome) < 100:
                        dados['pagador'] = nome[:50]
                        break
        
        # Cria descrição
        dados['descricao'] = f"{tipo_doc.upper()} - {dados.get('beneficiario', 'Não identificado')}"
        
        return dados
    
    def _converter_dados_ocr(self, dados: Dict, user_id: str) -> Dict[str, Any]:
        """Converte dados do OCR para comprovante"""
        comp_id = self._gerar_id(f"{dados.get('beneficiario')}_{datetime.now().isoformat()}")
        
        tipo = dados.get('tipo', 'outro')
        categoria, confianca = self._sugerir_categoria(dados.get('descricao', ''), dados.get('beneficiario', ''))
        
        comprovante = ComprovanteExtraido(
            id=comp_id,
            tipo=tipo,
            valor=dados.get('valor', 0),
            descricao=dados.get('descricao', ''),
            data=datetime.now().strftime('%Y-%m-%d'),
            destinatario=dados.get('beneficiario', ''),
            origem=dados.get('pagador', ''),
            categoria_sugerida=categoria,
            confianca=confianca * 0.8,  # OCR é menos confiável
            texto_original=json.dumps(dados),
            user_id=user_id,
            status='pendente',
            criado_em=datetime.now().isoformat()
        )
        
        comp_dict = comprovante.to_dict()
        self.pendentes[user_id] = comp_dict
        self._save_pendentes()
        
        return comp_dict
    
    def _converter_pix_extrator(self, resultado: Any, user_id: str) -> Dict[str, Any]:
        """Converte dados do extrator PIX para comprovante"""
        comp_id = self._gerar_id(resultado.id_transacao or str(datetime.now()))
        
        if resultado.tipo_transacao == 'enviado':
            descricao = f"PIX enviado para {resultado.destino_nome}"
            destinatario = resultado.destino_nome
        else:
            descricao = f"PIX recebido de {resultado.origem_nome}"
            destinatario = resultado.origem_nome
        
        categoria, confianca = self._sugerir_categoria(descricao, destinatario)
        
        comprovante = ComprovanteExtraido(
            id=comp_id,
            tipo='pix',
            valor=resultado.valor,
            descricao=descricao,
            data=resultado.data_hora[:10] if resultado.data_hora else datetime.now().strftime('%Y-%m-%d'),
            destinatario=destinatario,
            categoria_sugerida=categoria,
            confianca=confianca,
            texto_original=resultado.id_transacao or '',
            user_id=user_id,
            status='pendente',
            criado_em=datetime.now().isoformat()
        )
        
        comp_dict = comprovante.to_dict()
        comp_dict['pix_dados'] = {
            'chave_pix': resultado.chave_pix or '',
            'tipo_chave': resultado.tipo_chave or '',
            'id_transacao': resultado.id_transacao or '',
        }
        
        self.pendentes[user_id] = comp_dict
        self._save_pendentes()
        
        return comp_dict
    
    def _converter_transferencia_extrator(self, resultado: Any, user_id: str) -> Dict[str, Any]:
        """Converte dados do extrator de transferência para comprovante"""
        comp_id = self._gerar_id(resultado.id_transacao or str(datetime.now()))
        
        descricao = f"{resultado.tipo} para {resultado.destino_nome}"
        
        comprovante = ComprovanteExtraido(
            id=comp_id,
            tipo='transferencia',
            valor=resultado.valor,
            descricao=descricao,
            data=resultado.data_hora[:10] if resultado.data_hora else datetime.now().strftime('%Y-%m-%d'),
            destinatario=resultado.destino_nome,
            categoria_sugerida='outros',
            confianca=resultado.confianca / 100 if resultado.confianca else 0.8,
            texto_original=resultado.id_transacao or '',
            user_id=user_id,
            status='pendente',
            criado_em=datetime.now().isoformat()
        )
        
        comp_dict = comprovante.to_dict()
        comp_dict['transferencia_dados'] = {
            'banco_destino': resultado.destino_banco or '',
            'agencia_destino': resultado.destino_agencia or '',
            'conta_destino': resultado.destino_conta or '',
        }
        
        self.pendentes[user_id] = comp_dict
        self._save_pendentes()
        
        return comp_dict
    
    def _converter_boleto_extrator(self, resultado: Any, user_id: str) -> Dict[str, Any]:
        """Converte dados do extrator de boleto para comprovante"""
        comp_id = self._gerar_id(resultado.linha_digitavel or str(datetime.now()))
        
        descricao = f"Boleto - {resultado.beneficiario}"
        
        comprovante = ComprovanteExtraido(
            id=comp_id,
            tipo='boleto',
            valor=resultado.valor,
            descricao=descricao,
            data=resultado.vencimento[:10] if resultado.vencimento else datetime.now().strftime('%Y-%m-%d'),
            destinatario=resultado.beneficiario,
            categoria_sugerida='outros',
            confianca=resultado.confianca / 100 if resultado.confianca else 0.85,
            texto_original=resultado.linha_digitavel or '',
            user_id=user_id,
            status='pendente',
            criado_em=datetime.now().isoformat()
        )
        
        comp_dict = comprovante.to_dict()
        comp_dict['boleto_dados'] = {
            'linha_digitavel': resultado.linha_digitavel or '',
            'codigo_barras': resultado.codigo_barras or '',
            'banco': resultado.banco or '',
            'vencimento': resultado.vencimento or '',
        }
        
        self.pendentes[user_id] = comp_dict
        self._save_pendentes()
        
        return comp_dict
    
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
