"""
📊 Módulo de Extratos Bancários
Processa PDFs de extratos bancários de múltiplos bancos brasileiros
"""
import os
import re
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, replace
from collections import defaultdict
from normalizador_extratos import normalizar_extrato_completo

logger = logging.getLogger(__name__)

# Para processar PDFs
try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import tabula
    TABULA_AVAILABLE = True
except ImportError:
    TABULA_AVAILABLE = False

try:
    import camelot
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import ofxparse
    OFXPARSE_AVAILABLE = True
except ImportError:
    OFXPARSE_AVAILABLE = False


@dataclass
class TransacaoExtrato:
    """Representa uma transação extraída de extrato bancário"""
    data: str
    descricao: str
    valor: float
    tipo: str  # 'credito' ou 'debito'
    saldo: float = 0.0
    documento: str = ""
    categoria_sugerida: str = ""


@dataclass
class ExtratoBancario:
    """Representa um extrato bancário processado"""
    id: str
    banco: str
    agencia: str
    conta: str
    periodo: str  # "MM/YYYY"
    saldo_anterior: float
    saldo_atual: float
    transacoes: List[TransacaoExtrato]
    arquivo_origem: str
    user_id: str
    processado_em: str


class ExtratosModule:
    """Processador de extratos bancários"""

    # Padrões de identificação de bancos
    BANCOS_PATTERNS = {
        'itau': [
            r'ITAÚ', r'Itaú', r'ITAÚ UNIBANCO', r'Banco Itaú',
            r'www\.itau\.com\.br', r'\b4004\b', r'\b341\b'
        ],
        'bradesco': [
            r'BRADESCO', r'Bradesco', r'Banco Bradesco',
            r'www\.bradesco\.com\.br', r'\b237\b'
        ],
        'santander': [
            r'SANTANDER', r'Santander', r'Banco Santander',
            r'www\.santander\.com\.br', r'\b033\b'
        ],
        'nubank': [
            r'NUBANK', r'Nubank', r'Nu Bank',
            r'www\.nubank\.com\.br', r'\b260\b'
        ],
        'banco_do_brasil': [
            r'BANCO DO BRASIL', r'Banco do Brasil', r'\bBB\b',
            r'www\.bb\.com\.br', r'\b001\b'
        ],
        'caixa': [
            r'CAIXA ECONÔMICA', r'Caixa Econômica', r'CEF',
            r'www\.caixa\.gov\.br', r'\b104\b'
        ],
        'inter': [
            r'BANCO INTER', r'Banco Inter', r'Inter',
            r'www\.bancointer\.com\.br', r'077'
        ],
        'c6': [
            r'C6 BANK', r'C6BANK', r'BANCO C6', r'C6 S\.A',
            r'www\.c6bank\.com\.br', r'336', r'C6 CONSIGNADO'
        ],
        'next': [
            r'NEXT', r'Banco Next', r'Next',
            r'www\.banco next\.com\.br', r'237'  # Mesmo código do Bradesco
        ],
        'original': [
            r'BANCO ORIGINAL', r'Banco Original', r'Original',
            r'www\.bancooriginal\.com\.br', r'212'
        ],
        'pan': [
            r'BANCO PAN', r'Banco Pan', r'Pan',
            r'www\.bancopan\.com\.br', r'623'
        ],
        'bmg': [
            r'BANCO BMG', r'Banco BMG', r'BMG',
            r'www\.bmgbank\.com\.br', r'318'
        ],
        'digio': [
            r'DIGIO', r'Digio', r'Banco Digio',
            r'www\.digio\.com\.br', r'335'
        ],
        'pagbank': [
            r'PAGBANK', r'PagBank', r'PagSeguro',
            r'www\.pagseguro\.com\.br', r'290'
        ],
        'mercadopago': [
            r'MERCADO PAGO', r'Mercado Pago', r'MercadoPago',
            r'www\.mercadopago\.com\.br', r'323'
        ]
    }

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.extratos_file = os.path.join(data_dir, "extratos.json")

        os.makedirs(data_dir, exist_ok=True)
        self._load_data()

    def _load_data(self):
        """Carrega dados do disco"""
        if os.path.exists(self.extratos_file):
            with open(self.extratos_file, 'r', encoding='utf-8') as f:
                self.extratos = json.load(f)
        else:
            self.extratos = []

    def _save_data(self):
        """Salva dados no disco"""
        with open(self.extratos_file, 'w', encoding='utf-8') as f:
            json.dump(self.extratos, f, ensure_ascii=False, indent=2)

    async def handle(self, command: str, args: List[str],
                     user_id: str, attachments: list = None) -> str:
        """Processa comandos de extratos"""

        if command == 'extrato':
            if attachments:
                return await self._processar_extrato_attachment(attachments[0], user_id)
            else:
                return self._listar_extratos(user_id)

        elif command == 'extratos':
            return self._listar_extratos(user_id)

        return """
📊 *Módulo de Extratos Bancários*

Envie um PDF de extrato bancário para processamento automático!

Bancos suportados:
• Itaú • Bradesco • Santander • Nubank
• Banco do Brasil • Caixa • Inter • C6 Bank
• Next • Original • Pan • BMG • Digio
• PagBank • Mercado Pago

Comandos:
/extrato - Processar extrato (anexe PDF)
/extratos - Ver extratos processados
"""

    async def handle_natural(self, message: str, analysis: Any,
                              user_id: str, attachments: list = None) -> str:
        """Processa linguagem natural sobre extratos"""
        text_lower = message.lower()

        # Verifica se é resposta de confirmação
        if hasattr(self, '_dados_temp') and self._dados_temp:
            if any(word in text_lower for word in ['sim', 'confirmar', 'ok', 'salvar', 'yes']):
                return await self._confirmar_e_salvar_extrato(user_id)
            elif any(word in text_lower for word in ['revisar', 'editar', 'ajustar', 'no', 'não']):
                # Redireciona para interface web de revisão
                return "🔄 Para revisar as categorias, acesse a interface web: http://localhost:5001/revisao-categorias"
            elif any(word in text_lower for word in ['cancelar', 'descartar']):
                self._dados_temp = None
                return "❌ Processamento cancelado. Os dados foram descartados."

        if any(word in text_lower for word in ['extrato', 'banco', 'conta']):
            if attachments:
                return await self._processar_extrato_attachment(attachments[0], user_id)
            else:
                return self._listar_extratos(user_id)

        return await self.handle('extrato', [], user_id, attachments)

    async def _processar_extrato_attachment(self, attachment: dict, user_id: str, senha: str = None) -> str:
        """Processa anexo de extrato bancário"""
        if not PDF_AVAILABLE:
            return "❌ pdfplumber não instalado. Instale: pip install pdfplumber"

        # Verifica se é PDF
        if not attachment.get('file_name', '').lower().endswith('.pdf'):
            return "❌ Envie um arquivo PDF de extrato bancário"

        arquivo_path = attachment.get('file_path')
        if not arquivo_path or not os.path.exists(arquivo_path):
            return "❌ Arquivo não encontrado"

        # Processa o PDF
        resultado = await self._processar_pdf_extrato(arquivo_path, user_id, senha)

        if resultado['sucesso']:
            if resultado.get('preview', False):
                # Retorna preview para confirmação
                dados = resultado['dados']
                preview = dados['preview_categorias']

                resposta = f"""
📄 *EXTRATO PROCESSADO - CONFIRMAÇÃO NECESSÁRIA*

🏦 *Banco:* {dados['banco'].upper()}
👤 *Titular:* {dados['titular']}
📊 *Período:* {dados['periodo'] or 'N/A'}

💰 *RESUMO FINANCEIRO:*
• Entradas: R$ {preview['totais']['entradas']:.2f}
• Saídas: R$ {preview['totais']['saidas']:.2f}
• Saldo: R$ {preview['totais']['saldo']:.2f}

📈 *RECEITAS IDENTIFICADAS:*
"""

                for categoria, dados_cat in preview['receitas'].items():
                    resposta += f"• {categoria.title()}: R$ {dados_cat['total']:.2f} ({len(dados_cat['transacoes'])} transações)\n"

                resposta += "\n💸 *DESPESAS IDENTIFICADAS:*\n"
                for categoria, dados_cat in preview['despesas'].items():
                    resposta += f"• {categoria.title()}: R$ {dados_cat['total']:.2f} ({len(dados_cat['transacoes'])} transações)\n"

                if preview['sem_categoria']:
                    resposta += f"\n⚠️ *SEM CATEGORIA:* {len(preview['sem_categoria'])} transações\n"

                resposta += "\n✅ *Deseja confirmar e salvar este extrato?*"

                # Armazena dados temporariamente para confirmação
                self._dados_temp = dados

                # Retorna dados estruturados para permitir botões no Telegram
                return {
                    'tipo': 'confirmacao_extrato',
                    'mensagem': resposta,
                    'dados': dados,
                    'opcoes': {
                        'sim': 'SIM',
                        'revisar': 'REVISAR'
                    }
                }
            else:
                # Processamento normal (já salvo)
                extrato = resultado['extrato']
                return self._formatar_resposta_extrato(extrato)
        else:
            erro = resultado['erro']
            # Se for erro de senha, indica que precisa de senha
            if "PDF_PROTEGIDO_POR_SENHA" in erro:
                return "SENHA_NECESSARIA"
            return f"❌ Erro ao processar extrato: {erro}"

    async def _confirmar_e_salvar_extrato(self, user_id: str) -> str:
        """Confirma e salva o extrato após preview"""
        if not hasattr(self, '_dados_temp') or not self._dados_temp:
            return "❌ Nenhum extrato pendente para confirmação."

        try:
            dados = self._dados_temp

            # Cria objeto extrato
            from uuid import uuid4
            extrato = ExtratoBancario(
                id=str(uuid4())[:8],
                banco=dados['banco'],
                agencia=dados['agencia'],
                conta=dados['conta'],
                periodo=dados['periodo'],
                saldo_anterior=dados['saldo_anterior'],
                saldo_atual=dados['saldo_atual'],
                transacoes=dados['transacoes'],
                arquivo_origem=dados['arquivo_path'],
                user_id=user_id,
                processado_em=datetime.now().isoformat()
            )

            # Salva
            self.extratos.append(asdict(extrato))
            self._save_data()

            # Integra com módulo de finanças
            await self._integrar_com_financas(extrato, user_id)

            # Limpa dados temporários
            self._dados_temp = None

            return f"""
✅ *EXTRATO CONFIRMADO E SALVO!*

🏦 {extrato.banco.upper()}
👤 Titular: {dados['titular']}
📊 Período: {extrato.periodo or 'N/A'}
💰 Saldo Atual: R$ {extrato.saldo_atual:.2f}

📈 {len(extrato.transacoes)} transações processadas e categorizadas.
💾 Dados salvos e integrados ao sistema financeiro.
"""

        except Exception as e:
            return f"❌ Erro ao salvar extrato: {str(e)}"

    def _extrair_dados_pdf_avancado(self, arquivo_path: str, banco: str, senha: str = None) -> dict:
        """Extrai dados de PDF usando bibliotecas avançadas (Camelot, PyMuPDF, Tabula)"""
        dados = {'transacoes': []}

        try:
            # Tenta usar Camelot primeiro (melhor para tabelas)
            if CAMELOT_AVAILABLE:
                try:
                    logger.info(f"Tentando extrair com Camelot: {arquivo_path}")
                    tables = camelot.read_pdf(arquivo_path, password=senha, pages='all')

                    if len(tables) > 0:
                        logger.info(f"Camelot encontrou {len(tables)} tabelas")

                        # Processa cada tabela encontrada
                        for table in tables:
                            df = table.df
                            transacoes_extraidas = self._processar_tabela_camelot(df, banco)
                            dados['transacoes'].extend(transacoes_extraidas)

                        if dados['transacoes']:
                            logger.info(f"Camelot extraiu {len(dados['transacoes'])} transações")
                            return dados

                except Exception as e:
                    logger.warning(f"Camelot falhou: {e}")

            # # Tenta usar Tabula como alternativa (desabilitado por problemas com jpype)
            # if TABULA_AVAILABLE:
            #     try:
            #         logger.info(f"Tentando extrair com Tabula: {arquivo_path}")
            #         dfs = tabula.read_pdf(arquivo_path, password=senha, pages='all', multiple_tables=True)

            #         if dfs and len(dfs) > 0:
            #             logger.info(f"Tabula encontrou {len(dfs)} tabelas")

            #             for df in dfs:
            #                 transacoes_extraidas = self._processar_tabela_tabula(df, banco)
            #                 dados['transacoes'].extend(transacoes_extraidas)

            #             if dados['transacoes']:
            #                 logger.info(f"Tabula extraiu {len(dados['transacoes'])} transações")
            #                 return dados

            #     except Exception as e:
            #         logger.warning(f"Tabula falhou: {e}")

            # Fallback para PyMuPDF (texto estruturado)
            if PYMUPDF_AVAILABLE:
                try:
                    logger.info(f"Tentando extrair com PyMuPDF: {arquivo_path}")
                    doc = fitz.open(arquivo_path)

                    texto_completo = ""
                    for page in doc:
                        texto_completo += page.get_text()

                    doc.close()

                    if texto_completo.strip():
                        # Usa o método de extração por banco com o texto do PyMuPDF
                        dados_banco = self._extrair_dados_banco(texto_completo, banco)
                        if dados_banco['transacoes']:
                            logger.info(f"PyMuPDF extraiu {len(dados_banco['transacoes'])} transações")
                            return dados_banco

                except Exception as e:
                    logger.warning(f"PyMuPDF falhou: {e}")

        except Exception as e:
            logger.error(f"Erro geral na extração avançada: {e}")

        # Se todas as tentativas falharam, retorna dados vazios
        logger.warning("Todas as bibliotecas avançadas falharam, retornando dados vazios")
        return dados

    def _processar_tabela_camelot(self, df, banco: str) -> list:
        """Processa DataFrame do Camelot e extrai transações"""
        transacoes = []

        try:
            # Remove linhas vazias
            df = df.dropna(how='all')

            for idx, row in df.iterrows():
                # Tenta identificar se é uma linha de transação
                valores = [str(val).strip() for val in row.values if str(val).strip()]

                if len(valores) >= 3:  # Pelo menos data, descrição, valor
                    transacao = self._tentar_extrair_transacao_linha(valores, banco)
                    if transacao:
                        transacoes.append(transacao)

        except Exception as e:
            logger.warning(f"Erro ao processar tabela Camelot: {e}")

        return transacoes

    def _processar_tabela_tabula(self, df, banco: str) -> list:
        """Processa DataFrame do Tabula e extrai transações"""
        transacoes = []

        try:
            # Remove linhas vazias
            df = df.dropna(how='all')

            for idx, row in df.iterrows():
                # Converte para lista de strings
                valores = [str(val).strip() for val in row.values if str(val).strip()]

                if len(valores) >= 3:
                    transacao = self._tentar_extrair_transacao_linha(valores, banco)
                    if transacao:
                        transacoes.append(transacao)

        except Exception as e:
            logger.warning(f"Erro ao processar tabela Tabula: {e}")

        return transacoes

    def _tentar_extrair_transacao_linha(self, valores: list, banco: str) -> TransacaoExtrato:
        """Tenta extrair uma transação de uma linha de valores"""
        try:
            # Procura por padrão data + descrição + valor
            for i, valor in enumerate(valores):
                # Verifica se é uma data
                if re.match(r'^\d{2}/\d{2}(/\d{4})?$', valor):
                    data = valor
                    if len(data) == 5:  # DD/MM
                        data = f"{data}/2024"

                    # Próximos valores são descrição
                    descricao_parts = []
                    valor_str = ""

                    for j in range(i + 1, len(valores)):
                        val = valores[j].strip()
                        if re.match(r'^[\d.,\-R$\s]+$', val):  # Parece valor
                            valor_str = val
                            break
                        else:
                            descricao_parts.append(val)

                    if valor_str and descricao_parts:
                        descricao = ' '.join(descricao_parts)
                        valor = self._parse_valor(valor_str)

                        if valor != 0:
                            tipo = 'credito' if valor > 0 else 'debito'
                            valor = abs(valor)

                            return TransacaoExtrato(
                                data=data,
                                descricao=descricao.strip(),
                                valor=valor,
                                tipo=tipo,
                                categoria_sugerida=self._categorizar_transacao(descricao)
                            )

        except Exception as e:
            logger.debug(f"Erro ao extrair transação da linha {valores}: {e}")

        return None

    async def _processar_pdf_extrato(self, arquivo_path: str, user_id: str, senha: str = None) -> dict:
        """Processa PDF de extrato bancário usando métodos avançados primeiro"""
        try:
            # Extrai texto do PDF (para identificação de banco)
            texto = self._extrair_texto_pdf(arquivo_path, senha)
            if not texto:
                return {'sucesso': False, 'erro': 'Não consegui ler o PDF'}

            # Identifica o banco
            banco = self._identificar_banco(texto, arquivo_path)
            if not banco:
                return {'sucesso': False, 'erro': 'Banco não identificado'}

            logger.info(f"Banco identificado: {banco}")

            # PARA C6 BANK: TENTA MÉTODO TRADICIONAL PRIMEIRO (RegEx no texto)
            if banco == 'c6':
                logger.info("C6 Bank detectado - tentando extração por RegEx primeiro")
                dados = self._extrair_dados_banco(texto, banco)

                # Se RegEx falhou, tenta métodos avançados
                if not dados['transacoes']:
                    logger.info("RegEx falhou para C6, tentando métodos avançados")
                    dados = self._extrair_dados_pdf_avancado(arquivo_path, banco, senha)
            else:
                # PARA OUTROS BANCOS: TENTA EXTRAÇÃO AVANÇADA PRIMEIRO
                dados = self._extrair_dados_pdf_avancado(arquivo_path, banco, senha)

                # Se não conseguiu extrair com métodos avançados, tenta o método tradicional
                if not dados['transacoes']:
                    logger.info("Extração avançada falhou, tentando método tradicional")
                    dados = self._extrair_dados_banco(texto, banco)

            # Se ainda não conseguiu, erro
            if not dados['transacoes']:
                return {'sucesso': False, 'erro': 'Nenhuma transação encontrada'}

            # Identifica o titular (do texto extraído)
            titular_nome, titular_documento = self._identificar_titular(texto, banco)

            # Extrai informações da empresa (nome, agência, conta)
            info_empresa = self._extrair_informacoes_empresa(texto, banco)

            # Adiciona informações do titular e empresa aos dados
            dados['titular'] = titular_nome
            dados['cpf_cnpj_titular'] = titular_documento
            dados['nome_empresa'] = info_empresa['nome_empresa']
            dados['agencia'] = info_empresa['agencia']
            dados['conta'] = info_empresa['conta']
            dados['banco'] = banco

            # Categoriza automaticamente as transações
            transacoes_categorizadas = self._categorizar_transacoes_automaticamente(dados['transacoes'])

            # Cria preview das categorias para confirmação
            preview_categorias = self._gerar_preview_categorias(transacoes_categorizadas)

            # NORMALIZAÇÃO - Segundo estágio do processamento
            dados_para_normalizacao = {
                'agencia': dados.get('agencia', ''),
                'conta': dados.get('conta', ''),
                'nome_empresa': dados.get('nome_empresa', ''),
                'titular': titular_nome,
                'cpf_cnpj_titular': titular_documento,
                'periodo': dados.get('periodo', ''),
                'saldo_anterior': dados.get('saldo_anterior', 0.0),
                'saldo_atual': dados.get('saldo_atual', 0.0),
                'transacoes': transacoes_categorizadas
            }

            dados_normalizados = normalizar_extrato_completo(dados_para_normalizacao, banco)

            # Retorna dados normalizados para preview (não salva ainda)
            return {
                'sucesso': True,
                'preview': True,
                'dados': dados_normalizados,
                'dados_originais': {
                    'banco': banco,
                    'titular': titular,
                    'transacoes_categorizadas': transacoes_categorizadas,
                    'preview_categorias': preview_categorias,
                    'arquivo_path': arquivo_path,
                    'user_id': user_id
                }
            }

        except Exception as e:
            logger.error(f"Erro ao processar PDF: {e}")
            return {'sucesso': False, 'erro': str(e)}

    def _categorizar_transacoes_automaticamente(self, transacoes: list) -> list:
        """Categoriza automaticamente as transações baseado em padrões"""
        categorias_padrao = {
            # Receitas
            'salario': [r'salario', r'salário', r'proventos', r'remuneracao', r'REMUNERAÇÃO'],
            'freelance': [r'freelance', r'freela', r'autonomo', r'autônomo', r'pj'],
            'investimentos': [r'dividendos', r'juros', r'rendimentos', r'aplicacao', r'aplicação'],
            'transferencias': [r'transf', r'ted', r'doc', r'pix.*receb', r'recebimento'],

            # Despesas
            'alimentacao': [r'restaurante', r'lanchonete', r'padaria', r'supermercado', r'ifood', r'rappi', r'uber.*eats'],
            'transporte': [r'uber', r'99', r'taxi', r'onibus', r'ônibus', r'metro', r'trem'],
            'combustivel': [r'posto', r'combustivel', r'gasolina', r'etanol', r'diesel', r'shell', r'petrobras'],
            'saude': [r'farmacia', r'hospital', r'medico', r'consulta', r'exame', r'odontologo'],
            'educacao': [r'escola', r'faculdade', r'curso', r'livraria', r'material'],
            'lazer': [r'cinema', r'teatro', r'show', r'netflix', r'spotify', r'bar', r'boate'],
            'compras': [r'shopping', r'loja', r'magazine', r'americanas', r'casas bahia', r'kabum'],
            'servicos': [r'luz', r'agua', r'água', r'gas', r'telefone', r'internet', r'celular'],
            'impostos': [r'imposto', r'irpf', r'ipva', r'iptu', r'tributo'],
            'assinaturas': [r'assinatura', r'streaming', r'plataforma', r'servico', r'service'],
            'outros': []
        }

        transacoes_categorizadas = []

        for transacao in transacoes:
            descricao = transacao.descricao.upper()
            categoria_encontrada = 'sem_categoria'

            # Procura por padrões nas descrições
            for categoria, padroes in categorias_padrao.items():
                for padrao in padroes:
                    if re.search(padrao.upper(), descricao):
                        categoria_encontrada = categoria
                        break
                if categoria_encontrada != 'sem_categoria':
                    break

            # Adiciona categoria à transação
            from dataclasses import replace
            transacao_categorizada = replace(transacao, categoria_sugerida=categoria_encontrada)
            transacoes_categorizadas.append(transacao_categorizada)

        return transacoes_categorizadas

    def _gerar_preview_categorias(self, transacoes: list) -> dict:
        """Gera preview das categorias identificadas para confirmação"""
        categorias_receitas = {}
        categorias_despesas = {}
        sem_categoria = []

        total_entradas = 0
        total_saidas = 0

        for transacao in transacoes:
            categoria = getattr(transacao, 'categoria_sugerida', 'sem_categoria')
            valor = transacao.valor
            tipo = transacao.tipo

            if categoria == 'sem_categoria':
                sem_categoria.append(transacao)
            elif tipo == 'credito':
                if categoria not in categorias_receitas:
                    categorias_receitas[categoria] = {'total': 0, 'transacoes': []}
                categorias_receitas[categoria]['total'] += valor
                categorias_receitas[categoria]['transacoes'].append(transacao)
                total_entradas += valor
            elif tipo == 'debito':
                if categoria not in categorias_despesas:
                    categorias_despesas[categoria] = {'total': 0, 'transacoes': []}
                categorias_despesas[categoria]['total'] += valor
                categorias_despesas[categoria]['transacoes'].append(transacao)
                total_saidas += valor

        return {
            'receitas': categorias_receitas,
            'despesas': categorias_despesas,
            'sem_categoria': sem_categoria,
            'totais': {
                'entradas': total_entradas,
                'saidas': total_saidas,
                'saldo': total_entradas - total_saidas
            }
        }

    def _extrair_texto_pdf(self, arquivo_path: str, senha: str = None) -> str:
        """Extrai texto do PDF, com suporte a senha"""
        texto = ""

        try:
            # Tenta abrir sem senha primeiro
            pdf = pdfplumber.open(arquivo_path, password=senha)
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    texto += page_text + "\n"
            pdf.close()
        except Exception as e:
            error_msg = str(e).lower()
            if "password" in error_msg or "encrypted" in error_msg or "crypt" in error_msg:
                # PDF protegido por senha
                raise Exception("PDF_PROTEGIDO_POR_SENHA")
            else:
                # Outro erro
                raise Exception(f"Erro ao ler PDF: {e}")

        return texto

    def _identificar_banco(self, texto: str, arquivo_path: str = None) -> Optional[str]:
        """Identifica o banco baseado no texto e nome do arquivo"""
        texto_upper = texto.upper()
        filename = arquivo_path.upper() if arquivo_path else ""

        # Primeiro, verifica o nome do arquivo para hints específicos
        filename_hints = {
            'C6': ['C6', 'C6BANK'],
            'BANCO_DO_BRASIL': ['BANCOBRASIL', 'BB', 'BANCO_DO_BRASIL'],
            'ITAÚ': ['ITAU', 'ITAÚ'],
            'BRADESCO': ['BRADESCO'],
            'SANTANDER': ['SANTANDER'],
            'NUBANK': ['NUBANK'],
            'CAIXA': ['CAIXA'],
            'INTER': ['INTER'],
        }

        for banco, hints in filename_hints.items():
            for hint in hints:
                if hint in filename:
                    return banco.lower().replace(' ', '_').replace('ú', 'u')

        # Se não encontrou no filename, usa os padrões no texto
        # Verifica bancos em ordem de especificidade (mais específicos primeiro)
        bancos_ordenados = ['c6', 'nubank', 'inter', 'banco_do_brasil', 'itau', 'bradesco', 'santander', 'caixa', 'next', 'original']

        for banco in bancos_ordenados:
            if banco in self.BANCOS_PATTERNS:
                for pattern in self.BANCOS_PATTERNS[banco]:
                    if re.search(pattern.upper(), texto_upper):
                        return banco

        return None

    def _identificar_titular(self, texto: str, banco: str) -> tuple[str, str]:
        """Identifica o titular da conta no extrato
        
        Returns:
            tuple: (nome_titular, documento_titular)
        """
        texto_upper = texto.upper()

        # Padrões comuns para identificar titular
        padroes_titular = [
            r'TITULAR:\s*([^\n\r]+)',
            r'CLIENTE:\s*([^\n\r]+)',
            r'NOME:\s*([^\n\r]+)',
            r'CORRENTISTA:\s*([^\n\r]+)',
            r'CONTA\s+DE:\s*([^\n\r]+)',
            r'EM\s+NOME\s+DE:\s*([^\n\r]+)',
        ]

        for padrao in padroes_titular:
            match = re.search(padrao, texto_upper)
            if match:
                linha_completa = match.group(1).strip()
                nome, documento = self._extrair_nome_e_documento(linha_completa)
                if len(nome) > 3:  # Nome deve ter pelo menos 3 caracteres
                    return nome.title(), documento

        # Padrões específicos por banco
        if banco == 'itau':
            # Itaú geralmente tem "Cliente:" ou "Titular:"
            match = re.search(r'(?:CLIENTE|TITULAR):\s*([^\n\r]+)', texto_upper)
            if match:
                linha_completa = match.group(1).strip()
                nome, documento = self._extrair_nome_e_documento(linha_completa)
                return nome.title(), documento

        elif banco == 'bradesco':
            # Bradesco geralmente tem "Cliente:" ou nome após "Extrato de Conta"
            match = re.search(r'EXTRATO\s+DE\s+CONTA[^:]*:\s*([^\n\r]+)', texto_upper)
            if match:
                linha_completa = match.group(1).strip()
                nome, documento = self._extrair_nome_e_documento(linha_completa)
                return nome.title(), documento

        elif banco == 'santander':
            # Santander geralmente tem "Cliente:" ou "Titular:"
            match = re.search(r'(?:CLIENTE|TITULAR):\s*([^\n\r]+)', texto_upper)
            if match:
                linha_completa = match.group(1).strip()
                nome, documento = self._extrair_nome_e_documento(linha_completa)
                return nome.title(), documento

        # Se não encontrou, tenta extrair nome de pessoa física (geralmente antes de CPF)
        linhas = texto.split('\n')
        for linha in linhas:
            linha = linha.strip()
            if len(linha) > 10 and len(linha) < 50:  # Nome típico
                # Verifica se parece um nome (letras, espaços, talvez alguns caracteres especiais)
                if re.match(r'^[A-Z\s\.\-\']+$', linha.upper()) and not any(palavra in linha.upper() for palavra in ['CONTA', 'AGENCIA', 'SALDO', 'DATA', 'VALOR', 'EXTRATO']):
                    # Verifica se não é um cabeçalho ou informação bancária
                    if not linha.upper().startswith(('EXTRATO', 'CONTA', 'AGENCIA', 'SALDO', 'DATA', 'VALOR', 'DEBITO', 'CREDITO')):
                        nome, documento = self._extrair_nome_e_documento(linha)
                        return nome.title(), documento

        return "Não identificado", ""

    def _extrair_informacoes_empresa(self, texto: str, banco: str) -> dict:
        """Extrai informações da empresa: nome, agência e conta
        
        Returns:
            dict: {'nome_empresa': str, 'agencia': str, 'conta': str}
        """
        info = {'nome_empresa': '', 'agencia': '', 'conta': ''}
        texto_upper = texto.upper()
        
        # Padrões para extrair nome da empresa
        padroes_empresa = [
            r'EMPRESA:\s*([^\n\r]+)',
            r'RAZÃO\s+SOCIAL:\s*([^\n\r]+)',
            r'NOME\s+DA\s+EMPRESA:\s*([^\n\r]+)',
            r'EM\s+NOME\s+DE:\s*([^\n\r]+)',
            r'CONTA\s+DE:\s*([^\n\r]+)',
        ]
        
        for padrao in padroes_empresa:
            match = re.search(padrao, texto_upper)
            if match:
                nome_empresa = match.group(1).strip()
                # Limpa caracteres especiais mantendo letras, números e espaços
                nome_empresa = re.sub(r'[^A-Z0-9\s]', '', nome_empresa).strip()
                if len(nome_empresa) > 3:
                    info['nome_empresa'] = nome_empresa.title()
                    break
        
        # Padrões para extrair agência
        padroes_agencia = [
            r'AGÊNCIA:\s*(\d+)',
            r'AGENCIA:\s*(\d+)',
            r'AG\.\s*(\d+)',
            r'AG\s*(\d+)',
            r'AGÊNCIA\s+(\d+)',  # Sem caracteres especiais
        ]
        
        for padrao in padroes_agencia:
            match = re.search(padrao, texto_upper)
            if match:
                info['agencia'] = match.group(1).strip()
                break
        
        # Padrões para extrair conta
        padroes_conta = [
            r'CONTA:\s*([\d\-\.]+)',
            r'CONTA\s+CORRENTE:\s*([\d\-\.]+)',
            r'CONTA\s*(\d+(?:[-\s]\d+)*)',
            r'CC:\s*([\d\-\.]+)',
        ]
        
        for padrao in padroes_conta:
            match = re.search(padrao, texto_upper)
            if match:
                conta = match.group(1).strip()
                # Normaliza formato da conta (remove espaços, substitui por hífen)
                conta = re.sub(r'\s+', '-', conta)
                info['conta'] = conta
                break
        
        # Padrões específicos por banco
        if banco == 'itau':
            # Itaú PJ geralmente tem agência e conta no cabeçalho
            agencia_match = re.search(r'AGÊNCIA\s+(\d+)', texto_upper)
            if agencia_match:
                info['agencia'] = agencia_match.group(1)
            
            conta_match = re.search(r'CONTA\s+([\d\-]+)', texto_upper)
            if conta_match:
                info['conta'] = conta_match.group(1)
                
        elif banco == 'banco_do_brasil':
            # BB geralmente tem "Agência:" e "Conta:"
            agencia_match = re.search(r'Agência:\s*(\d+)', texto)
            if agencia_match:
                info['agencia'] = agencia_match.group(1)
            
            conta_match = re.search(r'Conta:\s*(\d+(?:-\d+)?)', texto)
            if conta_match:
                info['conta'] = conta_match.group(1)
                
        elif banco == 'santander':
            # Santander geralmente tem "Agência:" e "Conta:"
            agencia_match = re.search(r'Agência\s*[:\-]?\s*(\d+)', texto)
            if agencia_match:
                info['agencia'] = agencia_match.group(1)
                
            conta_match = re.search(r'Conta\s*[:\-]?\s*(\d+(?:[-\s]\d+)*)', texto)
            if conta_match:
                info['conta'] = conta_match.group(1).replace(' ', '-')
        
        return info

    def _extrair_nome_e_documento(self, texto: str) -> tuple[str, str]:
        """Extrai nome e documento (CPF/CNPJ) de uma linha de texto
        
        Returns:
            tuple: (nome_limpo, documento)
        """
        # Primeiro tenta extrair CPF: 123.456.789-00
        cpf_match = re.search(r'\d{3}\.\d{3}\.\d{3}-\d{2}', texto)
        if cpf_match:
            documento = cpf_match.group(0)
            # Remove o documento e caracteres especiais do nome
            nome = re.sub(r'\d{3}\.\d{3}\.\d{3}-\d{2}', '', texto)
            nome = re.sub(r'[^A-Z\s]', '', nome).strip()
            return nome, documento
        
        # Depois tenta extrair CNPJ: 12.345.678/0001-23
        cnpj_match = re.search(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', texto)
        if cnpj_match:
            documento = cnpj_match.group(0)
            # Remove o documento e caracteres especiais do nome
            nome = re.sub(r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', '', texto)
            nome = re.sub(r'[^A-Z\s]', '', nome).strip()
            return nome, documento
        
        # Se não encontrou documento, retorna apenas o nome limpo
        nome = re.sub(r'[^A-Z\s]', '', texto).strip()
        return nome, ""

    def _extrair_dados_banco(self, texto: str, banco: str) -> dict:
        """Extrai dados específicos do banco"""
        if banco == 'itau':
            return self._extrair_itau(texto)
        elif banco == 'bradesco':
            return self._extrair_bradesco(texto)
        elif banco == 'santander':
            return self._extrair_santander(texto)
        elif banco == 'pagseguro':
            return self._extrair_pagseguro(texto)
        elif banco == 'nubank':
            return self._extrair_nubank(texto)
        elif banco == 'banco_do_brasil':
            return self._extrair_bb(texto)
        elif banco == 'caixa':
            return self._extrair_caixa(texto)
        elif banco == 'inter':
            return self._extrair_inter(texto)
        elif banco == 'c6':
            return self._extrair_c6(texto)
        elif banco == 'next':
            return self._extrair_padrao_generico(texto)
        elif banco == 'original':
            return self._extrair_padrao_generico(texto)
        elif banco == 'pan':
            return self._extrair_padrao_generico(texto)
        elif banco == 'bmg':
            return self._extrair_padrao_generico(texto)
        elif banco == 'digio':
            return self._extrair_padrao_generico(texto)
        elif banco == 'pagbank':
            return self._extrair_padrao_generico(texto)
        elif banco == 'mercadopago':
            return self._extrair_padrao_generico(texto)
        else:
            return {'transacoes': []}

    def _extrair_itau(self, texto: str) -> dict:
        """Extrai dados de extrato Itaú PJ"""
        dados = {'transacoes': []}

        # Extrai informações básicas - agência e conta
        agencia_match = re.search(r'AGÊNCIA\s+(\d+)', texto.upper())
        if agencia_match:
            dados['agencia'] = agencia_match.group(1)
        
        conta_match = re.search(r'CONTA\s+([\d\-]+)', texto.upper())
        if conta_match:
            dados['conta'] = conta_match.group(1)

        # Extrai período se disponível
        periodo_match = re.search(r'Lançamentos do período:\s*(\d{2}/\d{4})\s*até\s*(\d{2}/\d{4})', texto)
        if periodo_match:
            dados['periodo'] = f"{periodo_match.group(1)} - {periodo_match.group(2)}"

        # Junta linhas quebradas primeiro
        linhas_juntadas = []
        linhas = texto.split('\n')
        i = 0
        while i < len(linhas):
            linha = linhas[i].strip()
            i += 1

            # Pula linhas vazias
            if not linha:
                continue

            # Se não começa com data, é continuação da linha anterior
            if not re.match(r'^\d{2}/\d{2}', linha):
                if linhas_juntadas:
                    linhas_juntadas[-1] += ' ' + linha
                continue

            # Nova linha de transação
            linhas_juntadas.append(linha)

            # Verifica se há continuação
            while i < len(linhas) and linhas[i].strip() and not re.match(r'^\d{2}/\d{2}', linhas[i].strip()):
                linhas_juntadas[-1] += ' ' + linhas[i].strip()
                i += 1

        # Agora processa cada linha juntada
        for linha in linhas_juntadas:
            linha = linha.strip()

            # Pula cabeçalhos e linhas irrelevantes
            if ('Lançamentos do período' in linha or
                'Data Lançamentos' in linha or
                'Razão Social' in linha or
                'SALDO' in linha.upper() or
                'AGÊNCIA' in linha.upper()):
                continue

            # Para depósitos: DATA DEP DIN BCO24H NUMERO_DOCUMENTO VALOR
            # O valor deve ser um número monetário (até 15 dígitos antes da vírgula)
            match_dep = re.search(r'(\d{2}/\d{2}/?\d{4}?)\s+DEP DIN BCO24H\s+(\d{1,15})\s+([\d.,]{1,20}-?)', linha)
            if match_dep and len(match_dep.group(3)) <= 15:  # Valor monetário não deve ser muito longo
                data, doc_num, valor_str = match_dep.groups()
                desc = "DEP DIN BCO24H"
            else:
                # Para PIX/Boletos com CNPJ: DATA TIPO DESCRIÇÃO CNPJ VALOR
                match_pix = re.search(r'(\d{2}/\d{2}/?\d{4}?)\s+(PIX \w+|BOLETO \w+)\s+(.+?)\s+\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\s+([\d.,]+-?)', linha)
                if match_pix:
                    data, tipo, desc, valor_str = match_pix.groups()
                    desc = f"{tipo} {desc}"
                else:
                    # Para PIX/Boletos sem CNPJ completo: DATA TIPO DESCRIÇÃO VALOR (mais flexível)
                    match_pix_simples = re.search(r'(\d{2}/\d{2}/?\d{4}?)\s+(PIX \w+|BOLETO \w+)\s+(.+?)\s+([\d.,]+-?)', linha)
                    if match_pix_simples:
                        data, tipo, desc, valor_str = match_pix_simples.groups()
                        desc = f"{tipo} {desc}"
                    else:
                        # Para transferências: DATA TRANSFERÊNCIA RECEBIDA NUMERO VALOR
                        match_transf = re.search(r'(\d{2}/\d{2}/?\d{4}?)\s+TRANSFERÊNCIA RECEBIDA\s+\d+\.\d+\s+([\d.,]+)', linha)
                        if match_transf:
                            data, valor_str = match_transf.groups()
                            desc = "TRANSFERÊNCIA RECEBIDA"
                        else:
                            # Para outros casos: DATA DESCRIÇÃO VALOR
                            match_geral = re.search(r'(\d{2}/\d{2}/?\d{4}?)\s+(.+?)\s+([\d.,]+-?)$', linha)
                            if match_geral:
                                data, desc, valor_str = match_geral.groups()
                            else:
                                continue

            # Limpa a descrição
            desc = desc.strip()
            desc = re.sub(r'\s+', ' ', desc)  # Remove espaços múltiplos

            # Pula linhas que não são transações reais
            if any(skip in desc.upper() for skip in ['SALDO ANTERIOR', 'AGÊNCIA', 'CONTA', 'PERÍODO']):
                continue

            valor = self._parse_valor(valor_str)
            
            # Validação: valores maiores que 10 milhões são provavelmente erros de extração
            if valor > 10000000:
                continue
                
            tipo = 'credito' if valor >= 0 else 'debito'
            valor = abs(valor)

            transacao = TransacaoExtrato(
                data=data if len(data) > 5 else f"{data}/2025",
                descricao=desc,
                valor=valor,
                tipo=tipo,
                saldo=0.0,
                categoria_sugerida=self._categorizar_transacao(desc)
            )

            dados['transacoes'].append(transacao)

        return dados

    def _extrair_bradesco(self, texto: str) -> dict:
        """Extrai dados de extrato Bradesco"""
        dados = {'transacoes': []}

        # Extrai informações básicas - agência e conta
        agencia_match = re.search(r'AGÊNCIA\s*[:\-]?\s*(\d+)', texto.upper())
        if agencia_match:
            dados['agencia'] = agencia_match.group(1)
        
        conta_match = re.search(r'CONTA\s*[:\-]?\s*([\d\-\.]+)', texto.upper())
        if conta_match:
            dados['conta'] = conta_match.group(1)

        # Padrão Bradesco similar ao Itaú
        linhas = texto.split('\n')

        for linha in linhas:
            linha = linha.strip()
            if not linha:
                continue

            # Procura por data e valores
            match = re.search(r'(\d{2}/\d{2})\s+(.+?)\s+([\d.,-]+)', linha)
            if match:
                data, desc, valor_str = match.groups()

                valor = self._parse_valor(valor_str)
                tipo = 'credito' if valor >= 0 else 'debito'
                valor = abs(valor)

                transacao = TransacaoExtrato(
                    data=f"{data}/2024",
                    descricao=desc.strip(),
                    valor=valor,
                    tipo=tipo,
                    categoria_sugerida=self._categorizar_transacao(desc)
                )

                dados['transacoes'].append(transacao)

        return dados

    def _extrair_santander(self, texto: str) -> dict:
        """Extrai dados de extrato Santander"""
        dados = {'transacoes': []}

        # Extrai informações básicas
        # Procura por conta e agência
        conta_match = re.search(r'Conta\s*[:\-]?\s*(\d+(?:[-\s]\d+)*)', texto, re.IGNORECASE)
        if conta_match:
            dados['conta'] = conta_match.group(1).replace(' ', '-')

        agencia_match = re.search(r'Agência\s*[:\-]?\s*(\d+)', texto, re.IGNORECASE)
        if agencia_match:
            dados['agencia'] = agencia_match.group(1)

        # Extrai titular
        titular_match = re.search(r'(?:Cliente|Titular|Nome)\s*[:\-]?\s*([^\n\r]+)', texto, re.IGNORECASE)
        if titular_match:
            dados['titular'] = titular_match.group(1).strip()

        # Extrai período
        periodo_match = re.search(r'Período\s*[:\-]?\s*(\d{2}/\d{4})\s*(?:a|até|-)\s*(\d{2}/\d{4})', texto, re.IGNORECASE)
        if periodo_match:
            dados['periodo'] = f"{periodo_match.group(1)} - {periodo_match.group(2)}"

        # Extrai saldo anterior
        saldo_ant_match = re.search(r'Saldo\s+Anterior\s*[:\-]?\s*R\$\s*([\d.,]+)', texto, re.IGNORECASE)
        if saldo_ant_match:
            dados['saldo_anterior'] = self._parse_valor(saldo_ant_match.group(1))

        # Extrai saldo atual
        saldo_atual_match = re.search(r'Saldo\s+(?:Atual|Final)\s*[:\-]?\s*R\$\s*([\d.,]+)', texto, re.IGNORECASE)
        if saldo_atual_match:
            dados['saldo_atual'] = self._parse_valor(saldo_atual_match.group(1))

        # Processa transações - padrão Santander
        linhas = texto.split('\n')
        transacoes = []

        for linha in linhas:
            linha = linha.strip()
            if not linha:
                continue

            # Padrão Santander: Data Descrição Valor
            # Exemplo: "12/12 PIX ENVIADO PARA EMPRESA XYZ R$ 1.500,00"
            match = re.search(r'(\d{2}/\d{2})\s+(.+?)\s+R\$\s*([\d.,]+)', linha)
            if match:
                data, desc, valor_str = match.groups()

                valor = self._parse_valor(valor_str)

                # Determinar tipo baseado na descrição
                tipo = 'credito'  # Default
                if any(word in desc.upper() for word in ['PAGAMENTO', 'ENVIADO', 'SAQUE', 'COMPRA', 'DEBITO']):
                    tipo = 'debito'

                transacao = TransacaoExtrato(
                    data=f"{data}/2025",  # Assumindo ano atual
                    descricao=desc.strip(),
                    valor=valor,
                    tipo=tipo,
                    categoria_sugerida=self._categorizar_transacao(desc)
                )

                transacoes.append(transacao)

        dados['transacoes'] = transacoes
        return dados

    def _extrair_pagseguro(self, texto: str) -> dict:
        """Extrai dados de extrato PagSeguro"""
        dados = {'transacoes': []}

        # Extrai informações básicas
        # Procura por conta e agência
        conta_match = re.search(r'Conta\s*[:\-]?\s*(\d+(?:[-\s]\d+)*)', texto, re.IGNORECASE)
        if conta_match:
            dados['conta'] = conta_match.group(1).replace(' ', '-')

        agencia_match = re.search(r'Agência\s*[:\-]?\s*(\d+)', texto, re.IGNORECASE)
        if agencia_match:
            dados['agencia'] = agencia_match.group(1)

        # Extrai titular
        titular_match = re.search(r'(?:Cliente|Titular|Nome)\s*[:\-]?\s*([^\n\r]+)', texto, re.IGNORECASE)
        if titular_match:
            dados['titular'] = titular_match.group(1).strip()

        # Extrai período
        periodo_match = re.search(r'Período\s*[:\-]?\s*(\d{2}/\d{4})\s*(?:a|até|-)\s*(\d{2}/\d{4})', texto, re.IGNORECASE)
        if periodo_match:
            dados['periodo'] = f"{periodo_match.group(1)} - {periodo_match.group(2)}"

        # Extrai saldo anterior
        saldo_ant_match = re.search(r'Saldo\s+Anterior\s*[:\-]?\s*R\$\s*([\d.,]+)', texto, re.IGNORECASE)
        if saldo_ant_match:
            dados['saldo_anterior'] = self._parse_valor(saldo_ant_match.group(1))

        # Extrai saldo atual
        saldo_atual_match = re.search(r'Saldo\s+(?:Atual|Final)\s*[:\-]?\s*R\$\s*([\d.,]+)', texto, re.IGNORECASE)
        if saldo_atual_match:
            dados['saldo_atual'] = self._parse_valor(saldo_atual_match.group(1))

        # Processa transações - padrão PagSeguro
        linhas = texto.split('\n')
        transacoes = []

        for linha in linhas:
            linha = linha.strip()
            if not linha:
                continue

            # Padrão PagSeguro: Data Descrição Valor
            # Exemplo: "12/12/2025 RECEBIMENTO PIX DE EMPRESA XYZ R$ 1.500,00"
            match = re.search(r'(\d{2}/\d{2}/?\d{4}?)\s+(.+?)\s+R\$\s*([\d.,]+)', linha)
            if match:
                data, desc, valor_str = match.groups()

                valor = self._parse_valor(valor_str)

                # Determinar tipo baseado na descrição
                tipo = 'credito'  # Default
                if any(word in desc.upper() for word in ['PAGAMENTO', 'ENVIADO', 'SAQUE', 'COMPRA', 'DEBITO', 'PAGBANK']):
                    tipo = 'debito'

                transacao = TransacaoExtrato(
                    data=data,
                    descricao=desc.strip(),
                    valor=valor,
                    tipo=tipo,
                    categoria_sugerida=self._categorizar_transacao(desc)
                )

                transacoes.append(transacao)

        dados['transacoes'] = transacoes
        return dados

    def _extrair_nubank(self, texto: str) -> dict:
        """Extrai dados de extrato Nubank"""
        dados = {'transacoes': []}

        # Nubank geralmente tem formato diferente (cartão de crédito)
        linhas = texto.split('\n')

        for linha in linhas:
            linha = linha.strip()
            if not linha:
                continue

            # Procura por data e descrição
            match = re.search(r'(\d{2}/\d{2})\s+(.+?)\s+([\d.,-]+)', linha)
            if match:
                data, desc, valor_str = match.groups()

                valor = self._parse_valor(valor_str)
                tipo = 'debito'  # Cartão geralmente débito

                transacao = TransacaoExtrato(
                    data=f"{data}/2024",
                    descricao=desc.strip(),
                    valor=abs(valor),
                    tipo=tipo,
                    categoria_sugerida=self._categorizar_transacao(desc)
                )

                dados['transacoes'].append(transacao)

        return dados

    def _extrair_bb(self, texto: str) -> dict:
        """Extrai dados de extrato Banco do Brasil"""
        dados = {'transacoes': []}

        # Extrai informações básicas
        # Procura por conta e agência
        conta_match = re.search(r'Conta\s*:\s*(\d+(?:-\d+)?)', texto, re.IGNORECASE)
        if conta_match:
            dados['conta'] = conta_match.group(1)

        agencia_match = re.search(r'Agência\s*:\s*(\d+)', texto, re.IGNORECASE)
        if agencia_match:
            dados['agencia'] = agencia_match.group(1)

        # Extrai período
        periodo_match = re.search(r'Período\s*:\s*(\d{2}/\d{4})\s*a\s*(\d{2}/\d{4})', texto, re.IGNORECASE)
        if periodo_match:
            dados['periodo'] = f"{periodo_match.group(1)} - {periodo_match.group(2)}"

        # Extrai saldo anterior
        saldo_ant_match = re.search(r'Saldo\s+Anterior\s*[:\-]?\s*R\$\s*([\d.,]+)', texto, re.IGNORECASE)
        if saldo_ant_match:
            dados['saldo_anterior'] = self._parse_valor(saldo_ant_match.group(1))

        # Extrai saldo atual
        saldo_atual_match = re.search(r'Saldo\s+Atual\s*[:\-]?\s*R\$\s*([\d.,]+)', texto, re.IGNORECASE)
        if saldo_atual_match:
            dados['saldo_atual'] = self._parse_valor(saldo_atual_match.group(1))

        # Extrai transações - múltiplos padrões para BB
        linhas = texto.split('\n')
        transacoes_encontradas = []

        i = 0
        while i < len(linhas):
            linha = linhas[i].strip()
            i += 1

            if not linha:
                continue

            # Padrão BB: Data na linha anterior, detalhes na linha atual
            # Exemplo:
            # 03/11/2025
            # 99021 612365000056816 Transferência recebida 02/11 17:21 A POSTO CASA CAIADA LTDA 370,00 (+)

            # Verifica se é uma data
            data_match = re.match(r'^(\d{2}/\d{2}/\d{4})$', linha)
            if data_match:
                data = data_match.group(1)

                # Pega a próxima linha não vazia
                while i < len(linhas):
                    proxima_linha = linhas[i].strip()
                    i += 1
                    if proxima_linha:
                        break

                if proxima_linha:
                    # Padrão: Lote Documento Descrição Valor (+/-)
                    match_detalhes = re.match(r'^(\d+)\s+(\d+)\s+(.+?)\s+([\d.,]+)\s*(\(\+\)|\(\-\))$', proxima_linha)
                    if match_detalhes:
                        lote, documento, desc, valor_str, sinal = match_detalhes.groups()
                        valor = self._parse_valor(valor_str)
                        if sinal == '(-)':
                            valor = -valor
                    else:
                        # Tenta padrão alternativo sem lote/documento
                        match_alt = re.match(r'^(.+?)\s+([\d.,]+)\s*(\(\+\)|\(\-\))$', proxima_linha)
                        if match_alt:
                            desc, valor_str, sinal = match_alt.groups()
                            valor = self._parse_valor(valor_str)
                            if sinal == '(-)':
                                valor = -valor
                        else:
                            continue  # Não conseguiu extrair desta linha
                else:
                    continue  # Não há linha de detalhes
            else:
                # Tenta padrões tradicionais
                # Padrão BB específico: Data Lote Documento Descrição Valor (+/-)
                match_bb = re.search(r'^(\d{2}/\d{2}/\d{4})\s+\d+\s+\d+\s+(.+?)\s+([\d.,]+)\s*(\(\+\)|\(\-\))$', linha)

                if match_bb:
                    data, lote, documento, desc, valor_str, sinal = match_bb.groups()
                    valor = self._parse_valor(valor_str)
                    if sinal == '(-)':
                        valor = -valor
                else:
                    # Padrão 1: Data Descrição Valor (formato BB comum)
                    match1 = re.search(r'^(\d{2}/\d{2})\s+(.+?)\s+R\$\s*([\d.,-]+)$', linha)

                    # Padrão 2: Data Descrição Valor sem R$
                    match2 = re.search(r'^(\d{2}/\d{2})\s+(.+?)\s+([\d.,-]+)$', linha)

                    # Padrão 3: Data com ano completo
                    match3 = re.search(r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+R\$\s*([\d.,-]+)$', linha)

                    # Padrão 4: Data com ano completo sem R$
                    match4 = re.search(r'^(\d{2}/\d{2}/\d{4})\s+(.+?)\s+([\d.,-]+)$', linha)

                    match = match1 or match2 or match3 or match4

                    if match:
                        data, desc, valor_str = match.groups()
                        valor = self._parse_valor(valor_str)
                    else:
                        continue

            # Pula cabeçalhos e totais
            desc_lower = desc.lower()
            if any(skip in desc_lower for skip in ['data', 'histórico', 'valor', 'saldo', 'total', 'subtotal', 'lançamento', 'dia', 'lote', 'documento']):
                continue

            try:
                if valor == 0:
                    continue

                tipo = 'credito' if valor > 0 else 'debito'
                valor = abs(valor)

                # Cria data completa se necessário
                if len(data) == 5:  # DD/MM
                    data = f"{data}/2024"

                transacao = TransacaoExtrato(
                    data=data,
                    descricao=desc.strip(),
                    valor=valor,
                    tipo=tipo,
                    categoria_sugerida=self._categorizar_transacao(desc)
                )

                transacoes_encontradas.append(transacao)

            except Exception as e:
                logger.warning(f"Erro ao processar transação BB: {linha} - {e}")
                continue

        # Remove duplicatas (alguns extratos BB repetem linhas)
        transacoes_unicas = []
        descricoes_vistas = set()

        for transacao in transacoes_encontradas:
            chave = f"{transacao.data}_{transacao.descricao}_{transacao.valor}"
            if chave not in descricoes_vistas:
                transacoes_unicas.append(transacao)
                descricoes_vistas.add(chave)

        dados['transacoes'] = transacoes_unicas
        return dados

    def _extrair_caixa(self, texto: str) -> dict:
        """Extrai dados de extrato Caixa"""
        return self._extrair_padrao_generico(texto)

    def _extrair_inter(self, texto: str) -> dict:
        """Extrai dados de extrato Inter"""
        return self._extrair_padrao_generico(texto)

    def _extrair_c6(self, texto: str) -> dict:
        """Extrai dados de extrato C6 Bank com padrões mais flexíveis"""
        dados = {'transacoes': []}
        linhas = texto.split('\n')

        for linha in linhas:
            linha = linha.strip()
            if not linha:
                continue

            # Padrão C6 mais flexível:
            # "31/10 31/10 Saída PIX Recorrência Pix enviada para GA... -R$ 50,00"
            # "31/10 31/10 Entrada PIX Recebido de FULANO R$ 100,00"
            # "31/10 31/10 Saída TED Enviada R$ 500,00"
            match = re.search(r'(\d{2}/\d{2})\s+(\d{2}/\d{2})\s+(Entrada|Saída|Entrada|Saida)\s+(.+?)\s+(?:-?R\$\s*)?([\d.,-]+)', linha)

            if match:
                data1, data2, tipo_str, desc, valor_str = match.groups()

                # Usa a segunda data (data de lançamento)
                data = data2

                # Normaliza tipo
                tipo_str = tipo_str.lower()
                tipo = 'credito' if tipo_str in ['entrada'] else 'debito'

                # Parse valor - remove R$ e espaços
                valor_str = valor_str.replace('R$', '').replace('$', '').strip()
                valor = self._parse_valor(valor_str)

                # Para saídas, garante negativo; para entradas, garante positivo
                if tipo == 'debito':
                    valor = -abs(valor)
                else:
                    valor = abs(valor)

                # Pula cabeçalhos e totais
                desc_lower = desc.lower()
                if any(skip in desc_lower for skip in ['data', 'tipo', 'descrição', 'valor', 'saldo', 'total', 'subtotal', 'lançamento', 'extrato']):
                    continue

                # Pula se descrição for muito curta ou suspeita
                if len(desc.strip()) < 3:
                    continue

                transacao = TransacaoExtrato(
                    data=f"{data}/2024",  # Assume ano atual
                    descricao=desc.strip(),
                    valor=valor,
                    tipo=tipo,
                    categoria_sugerida=self._categorizar_transacao(desc)
                )

                dados['transacoes'].append(transacao)
                logger.debug(f"C6: Extraída transação - {data} | {desc[:30]}... | {valor}")

        logger.info(f"C6: Total de {len(dados['transacoes'])} transações extraídas")
        return dados

    def _extrair_padrao_generico(self, texto: str) -> dict:
        """Extração genérica para bancos não específicos"""
        dados = {'transacoes': []}
        linhas = texto.split('\n')

        for linha in linhas:
            linha = linha.strip()
            if not linha:
                continue

            # Procura por qualquer padrão data + descrição + valor
            match = re.search(r'(\d{2}/\d{2})\s+(.+?)\s+([\d.,-]+)', linha)
            if match:
                data, desc, valor_str = match.groups()

                valor = self._parse_valor(valor_str)
                tipo = 'credito' if valor >= 0 else 'debito'
                valor = abs(valor)

                transacao = TransacaoExtrato(
                    data=f"{data}/2024",
                    descricao=desc.strip(),
                    valor=valor,
                    tipo=tipo,
                    categoria_sugerida=self._categorizar_transacao(desc)
                )

                dados['transacoes'].append(transacao)

        return dados

    def _parse_valor(self, valor_str: str) -> float:
        """Converte string de valor para float"""
        try:
            # Remove espaços e símbolos
            valor_str = valor_str.replace(' ', '').replace('R$', '').strip()
            
            # Trata valores negativos (terminam com -)
            negativo = valor_str.endswith('-')
            if negativo:
                valor_str = valor_str[:-1]
            
            # Trata casos como "1.234,56" -> "1234.56"
            if '.' in valor_str and ',' in valor_str:
                # Formato brasileiro: 1.234,56
                valor_str = valor_str.replace('.', '').replace(',', '.')
            elif ',' in valor_str and '.' not in valor_str:
                # Formato simples brasileiro: 123,45
                valor_str = valor_str.replace(',', '.')
            elif '.' in valor_str and ',' not in valor_str:
                # Já está em formato americano: 1234.56
                pass
            
            valor = float(valor_str)
            return -valor if negativo else valor
            
        except:
            return 0.0

    def _categorizar_transacao(self, descricao: str) -> str:
        """Sugere categoria baseada na descrição"""
        desc_lower = descricao.lower()

        # Mapeamentos simples (pode ser expandido)
        if any(word in desc_lower for word in ['supermercado', 'mercado', 'atacadao', 'extra', 'carrefour', 'pao de acucar']):
            return 'alimentacao'
        elif any(word in desc_lower for word in ['posto', 'combustivel', 'shell', 'petrobras', 'ipiranga', 'texaco']):
            return 'combustivel'
        elif any(word in desc_lower for word in ['uber', '99', 'cabify', 'taxi', 'transporte']):
            return 'transporte'
        elif any(word in desc_lower for word in ['netflix', 'spotify', 'amazon', 'assinatura', 'prime']):
            return 'assinaturas'
        elif any(word in desc_lower for word in ['farmacia', 'drogasil', 'raia', 'drogaria', 'saude']):
            return 'saude'
        elif any(word in desc_lower for word in ['pix', 'ted', 'transferencia', 'transferência']):
            return 'transferencias'
        elif any(word in desc_lower for word in ['boleto', 'conta', 'luz', 'agua', 'gas', 'telefone']):
            return 'contas'
        elif any(word in desc_lower for word in ['salario', 'provento', 'rendimento', 'dividendo']):
            return 'receitas'
        elif any(word in desc_lower for word in ['deposito', 'deposito judicial', 'judicial']):
            return 'receitas'
        else:
            return 'outros'

    async def _integrar_com_financas(self, extrato: ExtratoBancario, user_id: str):
        """Integra transações com módulo de finanças"""
        try:
            from modules.financas import FinancasModule
            financas = FinancasModule()

            for transacao in extrato.transacoes:
                # Converte para formato do módulo finanças
                tipo_financas = 'entrada' if transacao.tipo == 'credito' else 'saida'

                transacao_financas = {
                    'id': f"{extrato.id}_{len(financas.transacoes)}",
                    'tipo': tipo_financas,
                    'valor': transacao.valor,
                    'descricao': f"{extrato.banco.upper()}: {transacao.historico_completo}",
                    'categoria': transacao.categoria_sugerida or 'outros',
                    'data': transacao.data,
                    'user_id': user_id,
                    'criado_em': datetime.now().isoformat()
                }

                financas.transacoes.append(transacao_financas)
                financas._save_data()

        except ImportError:
            pass  # Módulo finanças não disponível

    def _listar_extratos(self, user_id: str) -> str:
        """Lista extratos processados do usuário"""
        extratos_user = [e for e in self.extratos if e.get('user_id') == user_id]

        if not extratos_user:
            return """
📊 *Seus Extratos*

Nenhum extrato processado ainda.

Envie um PDF de extrato bancário para começar!
"""

        resposta = "📊 *Seus Extratos Processados*\n\n"

        for extrato in extratos_user[-5:]:  # Últimos 5
            resposta += f"""
🏦 *{extrato['banco'].upper()}*
📅 Período: {extrato.get('periodo', 'N/A')}
💰 Saldo: R$ {extrato.get('saldo_atual', 0):.2f}
📊 Transações: {len(extrato.get('transacoes', []))}
ID: `{extrato['id']}`
─────────────
"""

        return resposta

    def _formatar_resposta_extrato(self, extrato: ExtratoBancario) -> str:
        """Formata resposta de extrato processado"""
        resposta = f"""
✅ *Extrato Processado com Sucesso!*

🏦 *Banco:* {extrato.banco.upper()}
📅 *Período:* {extrato.periodo or 'N/A'}
🏢 *Agência:* {extrato.agencia or 'N/A'}
💳 *Conta:* {extrato.conta or 'N/A'}

💰 *Saldo Anterior:* R$ {extrato.saldo_anterior:.2f}
💰 *Saldo Atual:* R$ {extrato.saldo_atual:.2f}

📊 *Transações Encontradas:* {len(extrato.transacoes)}

─────────────
*Últimas 10 transações:*
"""

        for i, transacao in enumerate(extrato.transacoes[-10:]):
            emoji = "💚" if transacao.tipo == 'credito' else "❤️"
            resposta += f"""
{emoji} {transacao.data}
{transacao.descricao[:50]}...
R$ {transacao.valor:.2f}
"""

        resposta += f"""
─────────────
*Comandos:*
/extratos - Ver todos os extratos
/gastos - Ver resumo financeiro

📝 *As transações foram automaticamente importadas para seu controle financeiro!*
"""

        return resposta