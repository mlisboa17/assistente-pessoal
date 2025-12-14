"""
📄 Módulo de Faturas e Boletos
Processa PDFs de boletos e extrai informações automaticamente
"""
import os
import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# Para processar PDFs
try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from PyPDF2 import PdfReader
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

# Para OCR em PDFs com imagem
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


@dataclass
class Boleto:
    """Representa um boleto ou guia de imposto"""
    id: str
    valor: float
    codigo_barras: str
    linha_digitavel: str
    vencimento: str
    beneficiario: str  # Quem vai receber (credor)
    pagador: str       # Quem vai pagar
    descricao: str
    arquivo_origem: str
    user_id: str
    extraido_em: str
    pago: bool = False
    agendado: bool = False
    # Campos de imposto
    tipo: str = "boleto"  # boleto, darf, gps, das, iptu, ipva, guia
    periodo_apuracao: str = ""
    codigo_receita: str = ""
    numero_referencia: str = ""
    cnpj_cpf: str = ""
    
    def to_dict(self):
        return asdict(self)


class FaturasModule:
    """Gerenciador de Faturas e Boletos"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.boletos_file = os.path.join(data_dir, "boletos.json")
        
        os.makedirs(data_dir, exist_ok=True)
        self._load_data()
        
        # Referência ao módulo de agenda (será injetado)
        self.agenda_module = None
    
    def set_agenda_module(self, agenda):
        """Define o módulo de agenda para criar lembretes"""
        self.agenda_module = agenda
    
    def _load_data(self):
        """Carrega dados do disco"""
        if os.path.exists(self.boletos_file):
            with open(self.boletos_file, 'r', encoding='utf-8') as f:
                self.boletos = json.load(f)
        else:
            self.boletos = []
    
    def _save_data(self):
        """Salva dados no disco"""
        with open(self.boletos_file, 'w', encoding='utf-8') as f:
            json.dump(self.boletos, f, ensure_ascii=False, indent=2)
    
    async def handle(self, command: str, args: List[str], 
                     user_id: str, attachments: list = None) -> str:
        """Processa comandos de faturas"""
        
        if command in ['fatura', 'boleto']:
            if attachments:
                return await self.processar_arquivo(attachments[0], user_id)
            return """
📄 *Módulo de Faturas e Boletos*

Envie um arquivo PDF de boleto e eu vou extrair:
• 💰 Valor
• 📊 Código de barras / Linha digitável  
• 📅 Data de vencimento
• 🏢 Beneficiário

E posso agendar automaticamente na sua agenda!

*Comandos:*
/boletos - Ver boletos pendentes
/pago [id] - Marcar como pago
"""
        
        elif command == 'boletos':
            return self._listar_boletos(user_id)
        
        elif command == 'pago':
            if args:
                return self._marcar_pago(user_id, args[0])
            return "❌ Use: /pago [id do boleto]"
        
        return "📄 Comandos: /fatura, /boletos, /pago [id]"
    
    async def handle_natural(self, message: str, analysis: Any,
                              user_id: str, attachments: list = None) -> str:
        """Processa linguagem natural"""
        if attachments:
            return await self.processar_arquivo(attachments[0], user_id)
        return await self.handle('fatura', [], user_id, attachments)
    
    async def processar_arquivo(self, arquivo: str, user_id: str) -> str:
        """
        Processa um arquivo de boleto (PDF)
        Extrai informações e agenda automaticamente
        """
        if not os.path.exists(arquivo):
            return "❌ Arquivo não encontrado."
        
        ext = os.path.splitext(arquivo)[1].lower()
        
        if ext == '.pdf':
            return await self._processar_pdf(arquivo, user_id)
        elif ext in ['.jpg', '.jpeg', '.png']:
            return await self._processar_imagem(arquivo, user_id)
        else:
            return f"❌ Formato não suportado: {ext}\nEnvie um PDF ou imagem."
    
    async def _processar_pdf(self, arquivo: str, user_id: str) -> str:
        """Processa PDF de boleto"""
        texto = ""
        
        # Tenta com pdfplumber primeiro (melhor para boletos)
        if PDF_AVAILABLE:
            try:
                with pdfplumber.open(arquivo) as pdf:
                    for page in pdf.pages:
                        texto += page.extract_text() or ""
            except Exception as e:
                print(f"Erro pdfplumber: {e}")
        
        # Fallback para PyPDF2
        if not texto and PYPDF2_AVAILABLE:
            try:
                reader = PdfReader(arquivo)
                for page in reader.pages:
                    texto += page.extract_text() or ""
            except Exception as e:
                print(f"Erro PyPDF2: {e}")
        
        if not texto:
            return """
❌ Não consegui ler o PDF.

Possíveis motivos:
• PDF é uma imagem (escaneado)
• PDF está protegido
• Arquivo corrompido

Tente enviar como imagem (foto do boleto).
"""
        
        # Extrai informações do boleto
        dados = self._extrair_dados_boleto(texto)
        
        if not dados['valor'] and not dados['linha_digitavel']:
            return f"""
⚠️ *PDF lido, mas não encontrei dados de boleto*

Texto extraído (primeiros 500 caracteres):
```
{texto[:500]}...
```

Se for um boleto, tente enviar uma foto mais nítida.
"""
        
        # Salva o boleto/imposto
        from uuid import uuid4
        boleto = Boleto(
            id=str(uuid4())[:8],
            valor=dados['valor'] or 0,
            codigo_barras=dados.get('codigo_barras') or "",
            linha_digitavel=dados.get('linha_digitavel') or "",
            vencimento=dados.get('vencimento') or "",
            beneficiario=dados.get('beneficiario') or "Não identificado",
            pagador=dados.get('pagador') or "Não identificado",
            descricao=dados.get('descricao') or "Boleto",
            arquivo_origem=os.path.basename(arquivo),
            user_id=user_id,
            extraido_em=datetime.now().isoformat(),
            pago=False,
            agendado=False,
            tipo=dados.get('tipo', 'boleto'),
            periodo_apuracao=dados.get('periodo_apuracao') or "",
            codigo_receita=dados.get('codigo_receita') or "",
            numero_referencia=dados.get('numero_referencia') or "",
            cnpj_cpf=dados.get('cnpj_cpf') or "",
        )
        
        self.boletos.append(boleto.to_dict())
        self._save_data()
        
        # Lista de tipos que são impostos/guias
        tipos_impostos = [
            'darf', 'irpf', 'irpj', 'pis', 'cofins', 'csll', 'gps', 
            'das', 'das_mei', 'itr', 'fgts', 'fgts_digital',
            'ipva', 'icms', 'icms_st', 'icms_difal', 'itcmd', 
            'licenciamento', 'multa_transito',
            'iptu', 'iss', 'itbi', 'guia'
        ]
        
        # Monta resposta baseada no tipo
        if boleto.tipo in tipos_impostos:
            resposta = self._formatar_resposta_imposto(boleto)
        else:
            resposta = self._formatar_resposta_boleto(boleto)
        
        # Agenda automaticamente se tiver data de vencimento
        if boleto.vencimento and self.agenda_module:
            try:
                await self._agendar_boleto(boleto, user_id)
                resposta += f"""
✅ *Agendado automaticamente!*
Você receberá um lembrete antes do vencimento.
"""
                # Atualiza status
                for b in self.boletos:
                    if b['id'] == boleto.id:
                        b['agendado'] = True
                self._save_data()
            except Exception as e:
                resposta += f"\n⚠️ Não consegui agendar: {e}"
        
        resposta += f"""
─────────────────────
*Comandos:*
/boletos - Ver todos os boletos
/pago {boleto.id} - Marcar como pago
"""
        
        return resposta
    
    def _formatar_resposta_boleto(self, boleto: Boleto) -> str:
        """Formata resposta para boleto comum"""
        return f"""
✅ *Boleto Processado com Sucesso!*

📋 *ID:* `{boleto.id}`
📝 *Descrição:* {boleto.descricao}
💰 *Valor:* R$ {boleto.valor:.2f}
📅 *Vencimento:* {self._formatar_data(boleto.vencimento)}

👤 *Pagador:* {boleto.pagador}
🏢 *Credor:* {boleto.beneficiario}

📊 *Linha Digitável:*
`{boleto.linha_digitavel}`
"""
    
    def _formatar_resposta_imposto(self, boleto: Boleto) -> str:
        """Formata resposta para guias de impostos"""
        
        # Ícone baseado no tipo
        icones = {
            # Federais
            'darf': '🏛️',
            'irpf': '🧾',
            'irpj': '🏢',
            'pis': '🏛️',
            'cofins': '🏛️',
            'csll': '🏛️',
            'gps': '👷',
            'das': '📊',
            'das_mei': '🧑‍💼',
            'itr': '🌾',
            # FGTS
            'fgts': '💼',
            'fgts_digital': '💼',
            # Estaduais
            'ipva': '🚗',
            'icms': '🏪',
            'icms_st': '🏪',
            'icms_difal': '🏪',
            'itcmd': '📜',
            'licenciamento': '🚗',
            'multa_transito': '🚦',
            # Municipais
            'iptu': '🏠',
            'iss': '🔧',
            'itbi': '🏘️',
            # Genéricos
            'guia': '📋',
        }
        icone = icones.get(boleto.tipo, '📄')
        
        # Tipo por extenso
        tipos_extenso = {
            'fgts_digital': 'FGTS DIGITAL',
            'fgts': 'FGTS',
            'das_mei': 'DAS-MEI',
            'icms_st': 'ICMS-ST',
            'icms_difal': 'ICMS-DIFAL',
        }
        tipo_display = tipos_extenso.get(boleto.tipo, boleto.tipo.upper())
        
        resposta = f"""
{icone} *{tipo_display} Processado com Sucesso!*

📋 *ID:* `{boleto.id}`
📝 *Tipo:* {boleto.descricao}
💰 *Valor:* R$ {boleto.valor:.2f}
📅 *Vencimento:* {self._formatar_data(boleto.vencimento)}
"""
        
        # Campos específicos de impostos
        if boleto.periodo_apuracao:
            resposta += f"📆 *Período/Competência:* {boleto.periodo_apuracao}\n"
        
        if boleto.codigo_receita:
            resposta += f"🔢 *Cód. Receita:* {boleto.codigo_receita}\n"
        
        if boleto.cnpj_cpf:
            resposta += f"🪪 *CPF/CNPJ:* {boleto.cnpj_cpf}\n"
        
        resposta += f"""
👤 *Contribuinte:* {boleto.pagador}
🏛️ *Órgão:* {boleto.beneficiario}

📊 *Código para Pagamento:*
`{boleto.linha_digitavel}`
"""
        
        return resposta
    
    def _extrair_dados_boleto(self, texto: str) -> Dict[str, Any]:
        """Extrai dados do boleto do texto"""
        dados = {
            'valor': None,
            'codigo_barras': None,
            'linha_digitavel': None,
            'vencimento': None,
            'beneficiario': None,  # Credor (quem recebe)
            'pagador': None,       # Quem paga
            'descricao': None,
            'tipo': 'boleto',      # boleto, imposto, darf, gps, das, iptu, ipva
            # Campos específicos de impostos
            'periodo_apuracao': None,
            'codigo_receita': None,
            'numero_referencia': None,
            'cnpj_cpf': None,
        }
        
        texto_upper = texto.upper()
        texto_limpo = re.sub(r'\s+', ' ', texto)
        
        # === DETECTA TIPO DE DOCUMENTO ===
        dados['tipo'] = self._detectar_tipo_documento(texto_upper)
        
        # Lista de tipos que são impostos/guias
        tipos_impostos = [
            'darf', 'irpf', 'irpj', 'pis', 'cofins', 'csll', 'gps', 
            'das', 'das_mei', 'itr', 'fgts', 'fgts_digital',
            'ipva', 'icms', 'icms_st', 'icms_difal', 'itcmd', 
            'licenciamento', 'multa_transito',
            'iptu', 'iss', 'itbi', 'guia'
        ]
        
        # Se for imposto, usa extração específica
        if dados['tipo'] in tipos_impostos:
            dados = self._extrair_dados_imposto(texto, texto_upper, dados)
            return dados
        
        # === LINHA DIGITÁVEL (47 ou 48 dígitos) ===
        # Formato: XXXXX.XXXXX XXXXX.XXXXXX XXXXX.XXXXXX X XXXXXXXXXXXXXXXX
        linha_pattern = r'(\d{5}\.?\d{5}\s*\d{5}\.?\d{6}\s*\d{5}\.?\d{6}\s*\d\s*\d{14})'
        linha_match = re.search(linha_pattern, texto)
        if linha_match:
            linha = re.sub(r'[^\d]', '', linha_match.group(1))
            dados['linha_digitavel'] = linha
        
        # Formato alternativo (só números separados)
        if not dados['linha_digitavel']:
            numeros = re.findall(r'\d{5,}', texto)
            for num in numeros:
                if len(num) >= 44 and len(num) <= 48:
                    dados['linha_digitavel'] = num
                    break
        
        # === CÓDIGO DE BARRAS (44 dígitos) ===
        codigo_pattern = r'\b(\d{44})\b'
        codigo_match = re.search(codigo_pattern, texto)
        if codigo_match:
            dados['codigo_barras'] = codigo_match.group(1)
        
        # === VALOR ===
        # Padrões comuns de valor em boletos
        valor_patterns = [
            r'VALOR\s*(?:DO\s*)?(?:DOCUMENTO|COBRAN[ÇC]A|BOLETO)?\s*:?\s*R?\$?\s*([\d.,]+)',
            r'R\$\s*([\d.,]+)',
            r'TOTAL\s*:?\s*R?\$?\s*([\d.,]+)',
            r'VALOR\s*:?\s*R?\$?\s*([\d.,]+)',
            r'(\d{1,3}(?:\.\d{3})*,\d{2})',  # 1.234,56
        ]
        
        for pattern in valor_patterns:
            match = re.search(pattern, texto_upper)
            if match:
                valor_str = match.group(1)
                # Limpa e converte
                valor_str = valor_str.replace('.', '').replace(',', '.')
                try:
                    valor = float(valor_str)
                    if valor > 0 and valor < 1000000:  # Valor razoável
                        dados['valor'] = valor
                        break
                except:
                    pass
        
        # === DATA DE VENCIMENTO ===
        venc_patterns = [
            r'VENCIMENTO\s*:?\s*(\d{2}[/.-]\d{2}[/.-]\d{2,4})',
            r'VENC\.?\s*:?\s*(\d{2}[/.-]\d{2}[/.-]\d{2,4})',
            r'DATA\s*VENC\w*\s*:?\s*(\d{2}[/.-]\d{2}[/.-]\d{2,4})',
            r'(\d{2}/\d{2}/\d{4})',  # Qualquer data
        ]
        
        for pattern in venc_patterns:
            match = re.search(pattern, texto_upper)
            if match:
                data_str = match.group(1)
                dados['vencimento'] = self._parse_data(data_str)
                if dados['vencimento']:
                    break
        
        # === BENEFICIÁRIO (CREDOR - quem recebe) ===
        benef_patterns = [
            r'BENEFICI[ÁA]RIO\s*[:/]?\s*([A-ZÀ-Ú][A-ZÀ-Ú\s.,&-]+?)(?:\n|CNPJ|CPF|AGÊNCIA|AGENCIA|$)',
            r'CEDENTE\s*[:/]?\s*([A-ZÀ-Ú][A-ZÀ-Ú\s.,&-]+?)(?:\n|CNPJ|CPF|$)',
            r'FAVORECIDO\s*[:/]?\s*([A-ZÀ-Ú][A-ZÀ-Ú\s.,&-]+?)(?:\n|CNPJ|CPF|$)',
            r'CREDOR\s*[:/]?\s*([A-ZÀ-Ú][A-ZÀ-Ú\s.,&-]+?)(?:\n|CNPJ|CPF|$)',
            r'RECEBEDOR\s*[:/]?\s*([A-ZÀ-Ú][A-ZÀ-Ú\s.,&-]+?)(?:\n|CNPJ|CPF|$)',
        ]
        
        for pattern in benef_patterns:
            match = re.search(pattern, texto_upper)
            if match:
                benef = match.group(1).strip()
                # Limpa caracteres estranhos no final
                benef = re.sub(r'[\s,.-]+$', '', benef)
                if len(benef) > 3 and len(benef) < 100:
                    dados['beneficiario'] = benef.title()
                    break
        
        # === PAGADOR (SACADO - quem paga) ===
        pagador_patterns = [
            r'PAGADOR\s*[:/]?\s*([A-ZÀ-Ú][A-ZÀ-Ú\s.,&-]+?)(?:\n|CNPJ|CPF|END|RUA|AV|$)',
            r'SACADO\s*[:/]?\s*([A-ZÀ-Ú][A-ZÀ-Ú\s.,&-]+?)(?:\n|CNPJ|CPF|END|RUA|AV|$)',
            r'DEVEDOR\s*[:/]?\s*([A-ZÀ-Ú][A-ZÀ-Ú\s.,&-]+?)(?:\n|CNPJ|CPF|$)',
            r'CLIENTE\s*[:/]?\s*([A-ZÀ-Ú][A-ZÀ-Ú\s.,&-]+?)(?:\n|CNPJ|CPF|$)',
            r'NOME\s*[:/]?\s*([A-ZÀ-Ú][A-ZÀ-Ú\s.,&-]+?)(?:\n|CNPJ|CPF|END|$)',
        ]
        
        for pattern in pagador_patterns:
            match = re.search(pattern, texto_upper)
            if match:
                pagador = match.group(1).strip()
                # Limpa caracteres estranhos no final
                pagador = re.sub(r'[\s,.-]+$', '', pagador)
                if len(pagador) > 3 and len(pagador) < 100:
                    dados['pagador'] = pagador.title()
                    break
        
        # === DESCRIÇÃO ===
        desc_patterns = [
            r'(?:DESCRI[ÇC][ÃA]O|REFER[ÊE]NCIA|HIST[ÓO]RICO)\s*:?\s*(.+?)(?:\n|$)',
            r'MENSALIDADE\s+(.+?)(?:\n|$)',
        ]
        
        for pattern in desc_patterns:
            match = re.search(pattern, texto_upper)
            if match:
                desc = match.group(1).strip()
                if len(desc) > 2:
                    dados['descricao'] = desc.title()
                    break
        
        # Tenta identificar tipo de conta pela descrição
        if not dados['descricao']:
            if 'LUZ' in texto_upper or 'ENERGIA' in texto_upper or 'CPFL' in texto_upper or 'ELETROPAULO' in texto_upper:
                dados['descricao'] = 'Conta de Luz'
            elif 'ÁGUA' in texto_upper or 'AGUA' in texto_upper or 'SABESP' in texto_upper:
                dados['descricao'] = 'Conta de Água'
            elif 'INTERNET' in texto_upper or 'TELEFONE' in texto_upper or 'VIVO' in texto_upper or 'CLARO' in texto_upper:
                dados['descricao'] = 'Internet/Telefone'
            elif 'GÁS' in texto_upper or 'GAS' in texto_upper or 'COMGAS' in texto_upper:
                dados['descricao'] = 'Conta de Gás'
            elif 'CONDOMÍNIO' in texto_upper or 'CONDOMINIO' in texto_upper:
                dados['descricao'] = 'Condomínio'
            elif 'ALUGUEL' in texto_upper:
                dados['descricao'] = 'Aluguel'
        
        return dados
    
    def _detectar_tipo_documento(self, texto_upper: str) -> str:
        """Detecta se é boleto comum ou imposto"""
        
        # === FGTS DIGITAL ===
        if 'FGTS' in texto_upper:
            if 'DIGITAL' in texto_upper or 'GUIA FGTS' in texto_upper:
                return 'fgts_digital'
            return 'fgts'
        
        # === DARF - Documento de Arrecadação de Receitas Federais ===
        if 'DARF' in texto_upper:
            if 'SIMPLES' in texto_upper:
                return 'das'
            return 'darf'
        
        # Receita Federal (vários tipos)
        if 'RECEITA FEDERAL' in texto_upper:
            if 'SIMPLES' in texto_upper:
                return 'das'
            if 'IRPF' in texto_upper or 'PESSOA FÍSICA' in texto_upper or 'PESSOA FISICA' in texto_upper:
                return 'irpf'
            if 'IRPJ' in texto_upper or 'PESSOA JURÍDICA' in texto_upper or 'PESSOA JURIDICA' in texto_upper:
                return 'irpj'
            return 'darf'
        
        # === GPS - Guia da Previdência Social (INSS) ===
        if 'GPS' in texto_upper or 'PREVIDÊNCIA SOCIAL' in texto_upper or 'PREVIDENCIA SOCIAL' in texto_upper or 'INSS' in texto_upper:
            return 'gps'
        
        # === DAS - Documento de Arrecadação do Simples Nacional ===
        if 'DAS' in texto_upper and ('SIMPLES' in texto_upper or 'MEI' in texto_upper):
            return 'das'
        if 'SIMPLES NACIONAL' in texto_upper:
            return 'das'
        if 'MEI' in texto_upper and 'MICROEMPREENDEDOR' in texto_upper:
            return 'das_mei'
        
        # === IPTU - Imposto Predial e Territorial Urbano ===
        if 'IPTU' in texto_upper or 'IMPOSTO PREDIAL' in texto_upper or 'TERRITORIAL URBANO' in texto_upper:
            return 'iptu'
        
        # === IPVA - Imposto sobre Veículos ===
        if 'IPVA' in texto_upper or 'IMPOSTO SOBRE VEÍCULO' in texto_upper or 'IMPOSTO SOBRE VEICULO' in texto_upper:
            return 'ipva'
        
        # === ICMS ===
        if 'ICMS' in texto_upper:
            if 'DIFAL' in texto_upper:
                return 'icms_difal'
            if 'ST' in texto_upper or 'SUBSTITUIÇÃO' in texto_upper:
                return 'icms_st'
            return 'icms'
        
        # === ISS - Imposto sobre Serviços ===
        if 'ISS' in texto_upper or 'IMPOSTO SOBRE SERVIÇO' in texto_upper:
            return 'iss'
        
        # === ITR - Imposto Territorial Rural ===
        if 'ITR' in texto_upper or 'TERRITORIAL RURAL' in texto_upper:
            return 'itr'
        
        # === ITBI - Imposto sobre Transmissão de Bens Imóveis ===
        if 'ITBI' in texto_upper or 'TRANSMISSÃO DE BENS' in texto_upper:
            return 'itbi'
        
        # === ITCMD - Imposto sobre Transmissão Causa Mortis ===
        if 'ITCMD' in texto_upper or 'CAUSA MORTIS' in texto_upper or 'DOAÇÃO' in texto_upper:
            return 'itcmd'
        
        # === Taxas específicas ===
        if 'TAXA DE LICENCIAMENTO' in texto_upper or 'LICENCIAMENTO' in texto_upper:
            return 'licenciamento'
        
        if 'MULTA' in texto_upper and ('TRÂNSITO' in texto_upper or 'TRANSITO' in texto_upper or 'DETRAN' in texto_upper):
            return 'multa_transito'
        
        # === Guias estaduais/municipais genéricas ===
        if 'GUIA DE RECOLHIMENTO' in texto_upper or 'DARE' in texto_upper or 'GARE' in texto_upper:
            return 'guia'
        
        # === Outros impostos federais ===
        if 'CONTRIBUIÇÃO' in texto_upper or 'CONTRIBUICAO' in texto_upper:
            if 'PIS' in texto_upper:
                return 'pis'
            if 'COFINS' in texto_upper:
                return 'cofins'
            if 'CSLL' in texto_upper:
                return 'csll'
            return 'darf'
        
        return 'boleto'
    
    def _extrair_dados_imposto(self, texto: str, texto_upper: str, dados: Dict) -> Dict:
        """Extrai dados específicos de guias de impostos"""
        
        tipo = dados['tipo']
        
        # === PERÍODO DE APURAÇÃO ===
        periodo_patterns = [
            r'PER[ÍI]ODO\s*(?:DE\s*)?APURA[ÇC][ÃA]O\s*[:/]?\s*(\d{2}[/.-]\d{4})',
            r'COMPET[ÊE]NCIA\s*[:/]?\s*(\d{2}[/.-]\d{4})',
            r'M[ÊE]S[/\s]*ANO\s*[:/]?\s*(\d{2}[/.-]\d{4})',
            r'REF(?:ER[ÊE]NCIA)?\s*[:/]?\s*(\d{2}[/.-]\d{4})',
        ]
        
        for pattern in periodo_patterns:
            match = re.search(pattern, texto_upper)
            if match:
                dados['periodo_apuracao'] = match.group(1)
                break
        
        # === CÓDIGO DA RECEITA ===
        codigo_patterns = [
            r'C[ÓO]D(?:IGO)?\s*(?:DA\s*)?RECEITA\s*[:/]?\s*(\d{4,6})',
            r'RECEITA\s*[:/]?\s*(\d{4,6})',
            r'C[ÓO]DIGO\s*[:/]?\s*(\d{4,6})',
        ]
        
        for pattern in codigo_patterns:
            match = re.search(pattern, texto_upper)
            if match:
                dados['codigo_receita'] = match.group(1)
                break
        
        # === NÚMERO DE REFERÊNCIA ===
        ref_patterns = [
            r'N[ÚU]MERO\s*(?:DE\s*)?REFER[ÊE]NCIA\s*[:/]?\s*(\d+)',
            r'REFER[ÊE]NCIA\s*[:/]?\s*(\d{10,20})',
        ]
        
        for pattern in ref_patterns:
            match = re.search(pattern, texto_upper)
            if match:
                dados['numero_referencia'] = match.group(1)
                break
        
        # === CPF/CNPJ DO CONTRIBUINTE ===
        cpf_pattern = r'CPF\s*[:/]?\s*(\d{3}\.?\d{3}\.?\d{3}-?\d{2})'
        cnpj_pattern = r'CNPJ\s*[:/]?\s*(\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2})'
        
        cnpj_match = re.search(cnpj_pattern, texto_upper)
        cpf_match = re.search(cpf_pattern, texto_upper)
        
        if cnpj_match:
            dados['cnpj_cpf'] = cnpj_match.group(1)
        elif cpf_match:
            dados['cnpj_cpf'] = cpf_match.group(1)
        
        # === VALOR ===
        valor_patterns = [
            r'VALOR\s*(?:TOTAL|PRINCIPAL|DO\s*DOCUMENTO)?\s*[:/]?\s*R?\$?\s*([\d.,]+)',
            r'TOTAL\s*A\s*RECOLHER\s*[:/]?\s*R?\$?\s*([\d.,]+)',
            r'R\$\s*([\d.,]+)',
            r'(\d{1,3}(?:\.\d{3})*,\d{2})',
        ]
        
        for pattern in valor_patterns:
            match = re.search(pattern, texto_upper)
            if match:
                valor_str = match.group(1).replace('.', '').replace(',', '.')
                try:
                    valor = float(valor_str)
                    if valor > 0 and valor < 10000000:
                        dados['valor'] = valor
                        break
                except:
                    pass
        
        # === DATA DE VENCIMENTO ===
        venc_patterns = [
            r'VENCIMENTO\s*[:/]?\s*(\d{2}[/.-]\d{2}[/.-]\d{2,4})',
            r'DATA\s*(?:DE\s*)?VENC\w*\s*[:/]?\s*(\d{2}[/.-]\d{2}[/.-]\d{2,4})',
            r'PAGAR\s*AT[ÉE]\s*[:/]?\s*(\d{2}[/.-]\d{2}[/.-]\d{2,4})',
        ]
        
        for pattern in venc_patterns:
            match = re.search(pattern, texto_upper)
            if match:
                dados['vencimento'] = self._parse_data(match.group(1))
                if dados['vencimento']:
                    break
        
        # === NOME DO CONTRIBUINTE (PAGADOR) ===
        nome_patterns = [
            r'CONTRIBUINTE\s*[:/]?\s*([A-ZÀ-Ú][A-ZÀ-Ú\s.,&-]+?)(?:\n|CPF|CNPJ|$)',
            r'NOME\s*[:/]?\s*([A-ZÀ-Ú][A-ZÀ-Ú\s.,&-]+?)(?:\n|CPF|CNPJ|END|$)',
            r'RAZ[ÃA]O\s*SOCIAL\s*[:/]?\s*([A-ZÀ-Ú][A-ZÀ-Ú\s.,&-]+?)(?:\n|CNPJ|$)',
        ]
        
        for pattern in nome_patterns:
            match = re.search(pattern, texto_upper)
            if match:
                nome = match.group(1).strip()
                nome = re.sub(r'[\s,.-]+$', '', nome)
                if len(nome) > 3 and len(nome) < 100:
                    dados['pagador'] = nome.title()
                    break
        
        # === CÓDIGO DE BARRAS / LINHA DIGITÁVEL ===
        # Guias de impostos usam formato diferente (44 ou 48 dígitos)
        linha_patterns = [
            r'(\d{11,12}[\s.-]?\d{11,12}[\s.-]?\d{11,12}[\s.-]?\d{11,12})',  # Formato convênio
            r'(\d{44,48})',  # Sequência contínua
        ]
        
        for pattern in linha_patterns:
            match = re.search(pattern, texto)
            if match:
                linha = re.sub(r'[^\d]', '', match.group(1))
                if len(linha) >= 44:
                    dados['linha_digitavel'] = linha
                    break
        
        # === DESCRIÇÃO BASEADA NO TIPO ===
        descricoes = {
            'darf': 'DARF - Imposto Federal',
            'gps': 'GPS - INSS/Previdência',
            'das': 'DAS - Simples Nacional',
            'iptu': 'IPTU - Imposto Predial',
            'ipva': 'IPVA - Imposto Veicular',
            'guia': 'Guia de Recolhimento',
        }
        
        # === DESCRIÇÃO BASEADA NO TIPO ===
        descricoes = {
            # Federais
            'darf': 'DARF - Imposto Federal',
            'irpf': 'IRPF - Imposto de Renda PF',
            'irpj': 'IRPJ - Imposto de Renda PJ',
            'pis': 'PIS - Programa Integração Social',
            'cofins': 'COFINS - Contrib. Financiamento Seg. Social',
            'csll': 'CSLL - Contrib. Social s/ Lucro Líquido',
            'gps': 'GPS - INSS/Previdência',
            'das': 'DAS - Simples Nacional',
            'das_mei': 'DAS-MEI - Microempreendedor Individual',
            'itr': 'ITR - Imposto Territorial Rural',
            # FGTS
            'fgts': 'FGTS - Fundo de Garantia',
            'fgts_digital': 'FGTS Digital',
            # Estaduais
            'ipva': 'IPVA - Imposto Veicular',
            'icms': 'ICMS - Imposto s/ Circulação',
            'icms_st': 'ICMS-ST - Substituição Tributária',
            'icms_difal': 'ICMS-DIFAL - Diferencial Alíquota',
            'itcmd': 'ITCMD - Transm. Causa Mortis/Doação',
            'licenciamento': 'Taxa de Licenciamento Veicular',
            'multa_transito': 'Multa de Trânsito',
            # Municipais
            'iptu': 'IPTU - Imposto Predial',
            'iss': 'ISS - Imposto sobre Serviços',
            'itbi': 'ITBI - Transm. Bens Imóveis',
            # Genéricos
            'guia': 'Guia de Recolhimento',
        }
        
        dados['descricao'] = descricoes.get(tipo, 'Imposto')
        
        # Adiciona código da receita à descrição se existir
        if dados['codigo_receita']:
            dados['descricao'] += f" (Cód: {dados['codigo_receita']})"
        
        # Beneficiário para impostos
        beneficiarios = {
            # Federais
            'darf': 'Receita Federal do Brasil',
            'irpf': 'Receita Federal do Brasil',
            'irpj': 'Receita Federal do Brasil',
            'pis': 'Receita Federal do Brasil',
            'cofins': 'Receita Federal do Brasil',
            'csll': 'Receita Federal do Brasil',
            'gps': 'INSS - Previdência Social',
            'das': 'Receita Federal - Simples Nacional',
            'das_mei': 'Receita Federal - MEI',
            'itr': 'Receita Federal do Brasil',
            # FGTS
            'fgts': 'Caixa Econômica Federal - FGTS',
            'fgts_digital': 'Caixa Econômica Federal - FGTS Digital',
            # Estaduais
            'ipva': 'Secretaria da Fazenda Estadual',
            'icms': 'Secretaria da Fazenda Estadual',
            'icms_st': 'Secretaria da Fazenda Estadual',
            'icms_difal': 'Secretaria da Fazenda Estadual',
            'itcmd': 'Secretaria da Fazenda Estadual',
            'licenciamento': 'DETRAN',
            'multa_transito': 'DETRAN / Órgão de Trânsito',
            # Municipais
            'iptu': 'Prefeitura Municipal',
            'iss': 'Prefeitura Municipal',
            'itbi': 'Prefeitura Municipal',
            # Genéricos
            'guia': 'Governo',
        }
        
        dados['beneficiario'] = beneficiarios.get(tipo, 'Governo')
        
        return dados
    
    def _parse_data(self, data_str: str) -> Optional[str]:
        """Converte string de data para ISO format"""
        # Remove caracteres extras
        data_str = re.sub(r'[^\d/.-]', '', data_str)
        
        formatos = ['%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y', '%d/%m/%y', '%d-%m-%y']
        
        for fmt in formatos:
            try:
                data = datetime.strptime(data_str, fmt)
                # Ajusta século se necessário
                if data.year < 100:
                    data = data.replace(year=data.year + 2000)
                return data.strftime('%Y-%m-%d')
            except:
                pass
        
        return None
    
    def _formatar_data(self, data_iso: str) -> str:
        """Formata data ISO para exibição"""
        if not data_iso:
            return "Não identificada"
        try:
            data = datetime.strptime(data_iso, '%Y-%m-%d')
            return data.strftime('%d/%m/%Y')
        except:
            return data_iso
    
    async def _agendar_boleto(self, boleto: Boleto, user_id: str):
        """Agenda o boleto na agenda do usuário"""
        if not self.agenda_module:
            return
        
        # Cria lembrete 2 dias antes do vencimento
        from datetime import timedelta
        venc = datetime.strptime(boleto.vencimento, '%Y-%m-%d')
        lembrete_data = venc - timedelta(days=2)
        
        texto_lembrete = f"💰 PAGAR: {boleto.descricao or 'Boleto'} - R$ {boleto.valor:.2f}"
        
        # Usa o método do módulo de agenda
        if hasattr(self.agenda_module, '_criar_lembrete_interno'):
            await self.agenda_module._criar_lembrete_interno(
                user_id=user_id,
                texto=texto_lembrete,
                data_hora=lembrete_data.isoformat(),
                extra={
                    'tipo': 'boleto',
                    'boleto_id': boleto.id,
                    'linha_digitavel': boleto.linha_digitavel,
                    'valor': boleto.valor
                }
            )
    
    def _listar_boletos(self, user_id: str) -> str:
        """Lista boletos pendentes do usuário"""
        boletos_user = [b for b in self.boletos if b['user_id'] == user_id and not b['pago']]
        
        if not boletos_user:
            return """
📄 *Seus Boletos*

Nenhum boleto pendente! 🎉

Envie um PDF de boleto para processá-lo.
"""
        
        # Ordena por vencimento
        boletos_user.sort(key=lambda x: x.get('vencimento') or '9999-99-99')
        
        linhas = ["📄 *Boletos Pendentes*\n"]
        total = 0
        
        for b in boletos_user:
            venc = self._formatar_data(b.get('vencimento'))
            valor = b.get('valor', 0)
            total += valor
            
            # Verifica se está vencido
            vencido = ""
            if b.get('vencimento'):
                try:
                    data_venc = datetime.strptime(b['vencimento'], '%Y-%m-%d')
                    if data_venc < datetime.now():
                        vencido = "⚠️ VENCIDO "
                except:
                    pass
            
            linhas.append(f"""
{vencido}📋 *ID:* `{b['id']}`
📝 {b.get('descricao', 'Boleto')}
💰 R$ {valor:.2f} | 📅 {venc}
👤 Pagador: {b.get('pagador', 'N/I')}
🏢 Credor: {b.get('beneficiario', 'N/I')}
""")
        
        linhas.append(f"""
─────────────────────
💵 *Total Pendente:* R$ {total:.2f}

Para ver detalhes: /boleto [id]
Para marcar pago: /pago [id]
""")
        
        return "\n".join(linhas)
    
    def _marcar_pago(self, user_id: str, boleto_id: str) -> str:
        """Marca boleto como pago"""
        for boleto in self.boletos:
            if boleto['id'] == boleto_id and boleto['user_id'] == user_id:
                boleto['pago'] = True
                boleto['pago_em'] = datetime.now().isoformat()
                self._save_data()
                
                return f"""
✅ *Boleto Marcado como Pago!*

📋 ID: `{boleto_id}`
💰 Valor: R$ {boleto.get('valor', 0):.2f}
🏢 {boleto.get('beneficiario', 'N/I')}
📅 Pago em: {datetime.now().strftime('%d/%m/%Y %H:%M')}
"""
        
        return f"❌ Boleto `{boleto_id}` não encontrado."
    
    async def _processar_imagem(self, arquivo: str, user_id: str) -> str:
        """Processa imagem de boleto com OCR"""
        if not OCR_AVAILABLE:
            return """
❌ OCR não disponível.

Instale as dependências:
```
pip install pytesseract pillow
```

E instale o Tesseract OCR no sistema.
"""
        
        try:
            img = Image.open(arquivo)
            texto = pytesseract.image_to_string(img, lang='por')
            
            if not texto.strip():
                return "❌ Não consegui ler a imagem. Tente uma foto mais nítida."
            
            # Usa a mesma lógica de extração
            dados = self._extrair_dados_boleto(texto)
            
            # Mesmo fluxo do PDF...
            # (código similar ao _processar_pdf)
            
            return f"🔍 Texto extraído da imagem (em desenvolvimento):\n\n{texto[:500]}"
            
        except Exception as e:
            return f"❌ Erro ao processar imagem: {e}"
