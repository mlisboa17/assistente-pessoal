"""
🏦 SISTEMA ZERO - Importação Universal de Extratos Bancários
Implementação completa seguindo a planilha estratégica de 10 etapas

Fluxo:
1. CONFIGURAÇÃO: Padrão Interno de Dados
2. CONFIGURAÇÃO: Repositório de Layouts (Fingerprints)
3. EXTRAÇÃO (M1): Script de Extração → DataFrame Bruto
4. EXTRAÇÃO (M1): Impressão Digital (Hash único)
5. NORMALIZAÇÃO (M2/M3): Reconhecimento de Layout
6. NORMALIZAÇÃO (M2/M3): Interface de Mapeamento (1ª vez)
7. NORMALIZAÇÃO (M2/M3): Aplicar Regras de Transformação
8. CARREGAMENTO (M4): Verificação de Duplicidade
9. CARREGAMENTO (M4): Persistência no BD
10. CARREGAMENTO: Exportação OFX (Opcional)
"""

import hashlib
import json
import os
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import re


# ==========================================
# ETAPA 1: CONTRATO DE DADOS PADRONIZADO
# ==========================================

@dataclass
class TransactionRecord:
    """
    🎯 Contrato de Dados: Padrão de Transação (JSON Schema)
    Estrutura final para conciliação bancária e contabilidade gerencial
    """
    id_hash_unico: str              # SHA-256 (Hash de Data + Valor + Descrição) - OBRIGATÓRIO
    data_movimento: str             # ISO 8601: YYYY-MM-DD - OBRIGATÓRIO  
    valor: float                    # Valor sempre positivo (Ex: 100.50) - OBRIGATÓRIO
    tipo_movimento: str             # "C" (Crédito) ou "D" (Débito) - OBRIGATÓRIO
    descricao_original: str         # Texto bruto do extrato - OBRIGATÓRIO
    codigo_historico: Optional[str] = None      # Código de transação do banco (Ex: PIX, TED, DOC)
    saldo_final_linha: Optional[float] = None   # Saldo após esta transação
    identificador_banco: Optional[str] = None   # ID único do banco (FITID do OFX)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário (JSON)"""
        return asdict(self)
    
    def to_json_example(self) -> Dict[str, Any]:
        """Retorna exemplo no formato JSON padrão"""
        return {
            "id_hash_unico": self.id_hash_unico,
            "data_movimento": self.data_movimento,
            "valor": self.valor,
            "tipo_movimento": self.tipo_movimento,
            "descricao_original": self.descricao_original,
            "codigo_historico": self.codigo_historico,
            "saldo_final_linha": self.saldo_final_linha,
            "identificador_banco": self.identificador_banco
        }


class StatusProcessamento(Enum):
    SUCESSO = "sucesso"
    ERRO_EXTRACAO = "erro_extracao"
    ERRO_FINGERPRINT = "erro_fingerprint"
    LAYOUT_DESCONHECIDO = "layout_desconhecido"
    MAPEAMENTO_PENDENTE = "mapeamento_pendente"
    ERRO_NORMALIZACAO = "erro_normalizacao"
    DUPLICIDADE_DETECTADA = "duplicidade_detectada"
    ERRO_PERSISTENCIA = "erro_persistencia"


# ==========================================
# ETAPA 2: REPOSITÓRIO DE LAYOUTS
# ==========================================

class RepositorioLayouts:
    """Gerencia fingerprints e mapeamentos de layouts"""
    
    def __init__(self, db_path: str = "data/layouts_extratos.db"):
        self.db_path = db_path
        self._criar_tabelas()
    
    def _criar_tabelas(self):
        """Cria estrutura do banco de layouts"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS layouts_aprendidos (
                    fingerprint TEXT PRIMARY KEY,
                    nome_layout TEXT NOT NULL,
                    banco_detectado TEXT,
                    colunas_originais TEXT NOT NULL,
                    mapeamento_json TEXT NOT NULL,
                    data_criacao TEXT NOT NULL,
                    ultima_utilizacao TEXT,
                    contador_uso INTEGER DEFAULT 1
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transacoes_processadas (
                    id_hash_unico TEXT PRIMARY KEY,
                    data_movimento TEXT NOT NULL,
                    valor REAL NOT NULL,
                    tipo_movimento TEXT NOT NULL,
                    descricao_original TEXT NOT NULL,
                    codigo_historico TEXT,
                    saldo_final_linha REAL,
                    identificador_banco TEXT,
                    data_processamento TEXT NOT NULL
                )
            """)
    
    def salvar_layout(self, fingerprint: str, nome: str, banco: str, 
                     colunas: List[str], mapeamento: Dict[str, str]):
        """Salva um novo layout aprendido"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO layouts_aprendidos 
                (fingerprint, nome_layout, banco_detectado, colunas_originais, 
                 mapeamento_json, data_criacao, ultima_utilizacao)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                fingerprint,
                nome,
                banco,
                json.dumps(colunas),
                json.dumps(mapeamento),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
    
    def buscar_layout(self, fingerprint: str) -> Optional[Dict[str, Any]]:
        """Busca layout pelo fingerprint"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM layouts_aprendidos WHERE fingerprint = ?
            """, (fingerprint,))
            
            row = cursor.fetchone()
            if row:
                # Atualiza contador de uso
                conn.execute("""
                    UPDATE layouts_aprendidos 
                    SET ultima_utilizacao = ?, contador_uso = contador_uso + 1
                    WHERE fingerprint = ?
                """, (datetime.now().isoformat(), fingerprint))
                
                return {
                    'fingerprint': row[0],
                    'nome_layout': row[1],
                    'banco_detectado': row[2],
                    'colunas_originais': json.loads(row[3]),
                    'mapeamento_json': json.loads(row[4]),
                    'data_criacao': row[5],
                    'ultima_utilizacao': row[6],
                    'contador_uso': row[7]
                }
        return None

    def buscar_layout_por_banco(self, banco: str) -> Optional[Dict[str, Any]]:
        """Busca um layout pelo banco detectado, preferindo mapeamentos com meta 'aplicar_para_fornecedor'=True."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM layouts_aprendidos WHERE banco_detectado = ?
            """, (banco,))
            rows = cursor.fetchall()
            if not rows:
                return None

            # Prefer mappings whose meta has aplicar_para_fornecedor true
            for row in rows:
                try:
                    mjson = json.loads(row[4])
                    meta = mjson.get('meta', {}) if isinstance(mjson, dict) else {}
                    if meta.get('aplicar_para_fornecedor', False):
                        # update utilization
                        conn.execute("""
                            UPDATE layouts_aprendidos 
                            SET ultima_utilizacao = ?, contador_uso = contador_uso + 1
                            WHERE fingerprint = ?
                        """, (datetime.now().isoformat(), row[0]))
                        return {
                            'fingerprint': row[0],
                            'nome_layout': row[1],
                            'banco_detectado': row[2],
                            'colunas_originais': json.loads(row[3]),
                            'mapeamento_json': json.loads(row[4]),
                            'data_criacao': row[5],
                            'ultima_utilizacao': row[6],
                            'contador_uso': row[7]
                        }
                except Exception:
                    continue

            # If none had meta True, return first row
            row = rows[0]
            conn.execute("""
                UPDATE layouts_aprendidos 
                SET ultima_utilizacao = ?, contador_uso = contador_uso + 1
                WHERE fingerprint = ?
            """, (datetime.now().isoformat(), row[0]))
            return {
                'fingerprint': row[0],
                'nome_layout': row[1],
                'banco_detectado': row[2],
                'colunas_originais': json.loads(row[3]),
                'mapeamento_json': json.loads(row[4]),
                'data_criacao': row[5],
                'ultima_utilizacao': row[6],
                'contador_uso': row[7]
            }
    
    def verificar_duplicidade(self, id_hash: str) -> bool:
        """Verifica se transação já foi processada"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 1 FROM transacoes_processadas WHERE id_hash_unico = ?
            """, (id_hash,))
            return cursor.fetchone() is not None
    
    def registrar_transacao(self, transacao: TransactionRecord):
        """Registra transação como processada"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR IGNORE INTO transacoes_processadas 
                (id_hash_unico, data_movimento, valor, tipo_movimento, descricao_original,
                 codigo_historico, saldo_final_linha, identificador_banco, data_processamento)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transacao.id_hash_unico,
                transacao.data_movimento,
                transacao.valor,
                transacao.tipo_movimento,
                transacao.descricao_original,
                transacao.codigo_historico,
                transacao.saldo_final_linha,
                transacao.identificador_banco,
                datetime.now().isoformat()
            ))


# ==========================================
# ETAPA 3 e 4: EXTRAÇÃO + FINGERPRINT
# ==========================================

class ExtratorUniversal:
    """Extrai dados de diferentes formatos e gera fingerprint"""
    
    @staticmethod
    def extrair_de_arquivo(caminho: str, senha: str = None) -> pd.DataFrame:
        """Extrai dados do arquivo para DataFrame bruto"""
        extensao = os.path.splitext(caminho)[1].lower()
        
        try:
            if extensao == '.csv':
                # Tenta diferentes delimitadores
                for delim in [',', ';', '\t', '|']:
                    try:
                        df = pd.read_csv(caminho, delimiter=delim, encoding='utf-8')
                        if len(df.columns) > 1:
                            return df
                    except:
                        continue
                        
                # Fallback com encoding
                return pd.read_csv(caminho, delimiter=';', encoding='latin-1')
                
            elif extensao == '.xlsx':
                return pd.read_excel(caminho)
                
            elif extensao == '.ofx':
                # Implementação futura com ofxparse
                raise NotImplementedError("Formato OFX em desenvolvimento")
                
            elif extensao == '.pdf':
                df_bruto = ExtratorUniversal._extrair_pdf_como_texto(caminho, senha)
                
                # Se o Tabula retornou muitas colunas (layout quebrado), tenta parsing automático
                if len(df_bruto.columns) > 10 and 'Unnamed:' in str(df_bruto.columns):
                    print("🔧 Detectado layout fragmentado do Tabula, tentando parsing automático...")
                    df_parsed = ExtratorUniversal._tentar_parsing_automatico(df_bruto)
                    return df_parsed
                
                # Se PDF do Bradesco com poucas linhas (pode indicar extração problemática), tenta parser específico
                if ('bradesco' in caminho.lower() or 'Data' in df_bruto.columns) and len(df_bruto) <= 5:
                    print("🏦 PDF suspeito do Bradesco com poucos dados, tentando parser específico...")
                    df_bradesco = ExtratorUniversal._parser_bradesco_especifico(caminho, senha)
                    if not df_bradesco.empty:
                        return df_bradesco
                
                return df_bruto
                
            else:
                raise ValueError(f"Formato não suportado: {extensao}")
                
        except Exception as e:
            raise Exception(f"Erro na extração: {str(e)}")
    
    @staticmethod
    def _extrair_pdf_como_texto(caminho: str, senha: str = None) -> pd.DataFrame:
        """
        MÓDULO 1 - EXTRAÇÃO AVANÇADA DE PDFs
        Implementa múltiplas estratégias para extrair dados tabulares de PDFs bancários
        """
        
        # Estratégia 1: Tabula-py (Melhor para tabelas bem estruturadas)
        try:
            return ExtratorUniversal._extrair_pdf_tabula(caminho, senha)
        except Exception as e:
            print(f"⚠️ Tabula-py falhou: {e}")
        
        # Estratégia 2: Camelot (Para PDFs mais complexos) 
        try:
            return ExtratorUniversal._extrair_pdf_camelot(caminho, senha)
        except Exception as e:
            print(f"⚠️ Camelot falhou: {e}")
        
        # Estratégia 3: pdfplumber (Para estruturas de texto)
        try:
            return ExtratorUniversal._extrair_pdf_pdfplumber(caminho, senha)
        except Exception as e:
            print(f"⚠️ pdfplumber falhou: {e}")
        
        # Estratégia 4: Fallback - Análise de texto bruto
        return ExtratorUniversal._extrair_pdf_texto_bruto(caminho, senha)
    
    @staticmethod
    def _extrair_pdf_tabula(caminho: str, senha: str = None) -> pd.DataFrame:
        """Estratégia 1: Extrai tabelas usando Tabula-py"""
        try:
            import tabula
        except ImportError:
            raise Exception("tabula-py não instalado. Execute: pip install tabula-py")
        
        print("📊 Usando Tabula-py para extração tabular...")
        
        # Extrai todas as tabelas de todas as páginas
        dfs_list = tabula.read_pdf(
            caminho, 
            pages='all',
            password=senha,
            multiple_tables=True,
            pandas_options={'header': 0}
        )
        
        if not dfs_list:
            raise Exception("Nenhuma tabela detectada pelo Tabula-py")
        
        # Combina todas as tabelas encontradas
        df_combinado = pd.concat(dfs_list, ignore_index=True)
        
        if df_combinado.empty:
            raise Exception("Tabelas extraídas estão vazias")
        
        print(f"✅ Tabula-py: {len(df_combinado)} linhas extraídas")
        return df_combinado
    
    @staticmethod
    def _extrair_pdf_camelot(caminho: str, senha: str = None) -> pd.DataFrame:
        """Estratégia 2: Extrai tabelas usando Camelot"""
        try:
            import camelot
        except ImportError:
            raise Exception("camelot-py não instalado. Execute: pip install camelot-py[cv]")
        
        print("📊 Usando Camelot para extração avançada...")
        
        # Camelot não suporta senha diretamente, precisa descriptografar primeiro
        if senha:
            raise Exception("Camelot não suporta PDFs com senha diretamente")
        
        # Extrai tabelas com Camelot (melhor para layouts complexos)
        tables = camelot.read_pdf(caminho, pages='all', flavor='stream')
        
        if not tables:
            raise Exception("Nenhuma tabela detectada pelo Camelot")
        
        # Combina todas as tabelas
        dfs_list = [table.df for table in tables if not table.df.empty]
        
        if not dfs_list:
            raise Exception("Todas as tabelas extraídas estão vazias")
        
        df_combinado = pd.concat(dfs_list, ignore_index=True)
        
        print(f"✅ Camelot: {len(df_combinado)} linhas extraídas")
        return df_combinado
    
    @staticmethod
    def _extrair_pdf_pdfplumber(caminho: str, senha: str = None) -> pd.DataFrame:
        """Estratégia 3: Extrai tabelas usando pdfplumber"""
        try:
            import pdfplumber
        except ImportError:
            raise Exception("pdfplumber não instalado. Execute: pip install pdfplumber")
        
        print("📊 Usando pdfplumber para extração de tabelas...")
        all_tables = []

        with pdfplumber.open(caminho, password=senha) as pdf:
            for page_num, page in enumerate(pdf.pages):
                # 1) Tenta extract_tables (automático)
                try:
                    tables = page.extract_tables()
                except Exception:
                    tables = []

                if tables:
                    for table in tables:
                        if table and len(table) > 1:
                            df_table = pd.DataFrame(table[1:], columns=table[0])
                            df_table = df_table.dropna(how='all')
                            if not df_table.empty:
                                all_tables.append(df_table)
                    continue

                # 2) Tenta extract_table com estratégias alternativas
                alt_settings = [
                    {'vertical_strategy': 'lines', 'horizontal_strategy': 'text'},
                    {'vertical_strategy': 'text', 'horizontal_strategy': 'lines'},
                    {'vertical_strategy': 'lines', 'horizontal_strategy': 'lines'}
                ]

                for settings in alt_settings:
                    try:
                        table = page.extract_table(table_settings=settings)
                        if table and len(table) > 1:
                            df_table = pd.DataFrame(table[1:], columns=table[0])
                            df_table = df_table.dropna(how='all')
                            if not df_table.empty:
                                all_tables.append(df_table)
                                break
                    except Exception:
                        continue

                if any(settings for settings in alt_settings if page.extract_table(table_settings=settings)):
                    continue

                # 3) Tenta construir tabela a partir de palavras agrupando por posição vertical (y)
                try:
                    words = page.extract_words()
                    if words:
                        # Agrupa palavras por posição y aproximada para formar linhas
                        lines = {}
                        for w in words:
                            y = round(float(w.get('top', 0)))
                            lines.setdefault(y, []).append((float(w.get('x0', 0)), w.get('text', '')))

                        # Ordena por y desc (topo->baixo) e por x0 para formar colunas
                        sorted_lines = []
                        for y in sorted(lines.keys()):
                            row = [t[1] for t in sorted(lines[y], key=lambda x: x[0])]
                            sorted_lines.append(' '.join(row))

                        # Tenta extrair colunas por regex (data + descrição + valor)
                        regex_rows = []
                        for rl in sorted_lines:
                            if re.search(r'\d{1,2}/\d{1,2}/\d{2,4}.*\d+[\.,]\d{2}', rl):
                                regex_rows.append(rl)

                        if regex_rows:
                            df_table = pd.DataFrame({'linha_bruta': regex_rows, 'necessita_parsing': ['SIM'] * len(regex_rows)})
                            all_tables.append(df_table)
                except Exception:
                    pass

        # Se chegou aqui sem extrair tabelas estruturadas, tenta parsing específico por banco
        if not all_tables:
            # Detecta se é PDF do Bradesco baseado no nome do arquivo ou conteúdo
            if 'bradesco' in caminho.lower() or any('bradesco' in str(page.extract_text()).lower() for page in pdf.pages):
                print("🏦 Detectado PDF do Bradesco, aplicando parser específico...")
                df_bradesco = ExtratorUniversal._parser_bradesco_especifico(caminho, senha)
                if not df_bradesco.empty:
                    return df_bradesco

        if not all_tables:
            raise Exception("Nenhuma tabela estruturada encontrada pelo pdfplumber")

        df_combinado = pd.concat(all_tables, ignore_index=True)

        print(f"✅ pdfplumber: {len(df_combinado)} linhas extraídas")
        return df_combinado
    
    @staticmethod
    def _extrair_pdf_texto_bruto(caminho: str, senha: str = None) -> pd.DataFrame:
        """Estratégia 4: Fallback - Análise de texto bruto"""
        try:
            import pdfplumber
        except ImportError:
            raise Exception("pdfplumber não instalado. Execute: pip install pdfplumber")
        
        print("📊 Fallback: Análise de texto bruto...")
        
        # Extrai texto do PDF
        texto_completo = ""
        with pdfplumber.open(caminho, password=senha) as pdf:
            for page in pdf.pages:
                texto_pagina = page.extract_text()
                if texto_pagina:
                    texto_completo += texto_pagina + "\n"
        
        if not texto_completo.strip():
            raise Exception("Nenhum texto extraído do PDF")
        
        # Analisa o texto para identificar padrões tabulares
        linhas = texto_completo.split('\n')
        linhas_validas = [linha.strip() for linha in linhas if linha.strip()]

        # Padrões mais abrangentes para data e valor
        padrao_data = r'\d{1,2}/\d{1,2}/(?:\d{2}|\d{4})'
        padrao_valor = r'(?:R\$\s*)?[-\(]?\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d{2})[-\)]?'

        linhas_dados = []
        for linha in linhas_validas:
            if re.search(padrao_data, linha) and re.search(padrao_valor, linha):
                linhas_dados.append(linha)

        if linhas_dados:
            parsed = []
            for linha in linhas_dados:
                # Tenta extrair data
                m_data = re.search(padrao_data, linha)
                data = m_data.group(0) if m_data else ''

                # Tenta extrair último valor na linha
                valores = re.findall(padrao_valor, linha)
                valor_raw = valores[-1] if valores else ''

                # Normaliza valor para forma numérica
                valor_norm = 0.0
                if valor_raw:
                    vr = valor_raw.replace('R$', '').replace('(', '-').replace(')', '')
                    vr = vr.replace('.', '').replace(',', '.')
                    vr = re.sub(r'[^0-9\-\.]', '', vr)
                    try:
                        valor_norm = float(vr)
                    except:
                        valor_norm = 0.0

                # Descrição: parte do texto entre data e valor
                desc = linha
                if m_data:
                    desc = desc.split(m_data.group(0), 1)[-1].strip()
                if valor_raw:
                    desc = desc.rsplit(valor_raw, 1)[0].strip()

                tipo = 'C' if valor_norm >= 0 else 'D'

                parsed.append({'data_movimento': data, 'descricao_original': desc, 'valor': valor_norm, 'tipo_movimento': tipo, 'linha_bruta': linha})

            df = pd.DataFrame(parsed)
            print(f"✅ Texto bruto (parseado): {len(df)} linhas com data+valor")
            return df

        # Se nenhum padrão encontrado, retorna amostra para análise manual
        dados_basicos = {
            'texto_extraido': linhas_validas[:20],
            'total_linhas': len(linhas_validas)
        }
        print(f"⚠️ Texto bruto: {len(linhas_validas)} linhas gerais (sem padrões extraíveis)")
        return pd.DataFrame([dados_basicos])
    
    @staticmethod
    def _parser_bradesco_especifico(caminho: str, senha: str = None) -> pd.DataFrame:
        """Parser específico para PDFs do Bradesco que têm estrutura multilinhas complexa"""
        try:
            import pdfplumber
        except ImportError:
            return pd.DataFrame()
        
        print("🏦 Aplicando parser específico do Bradesco...")
        
        transacoes = []
        
        with pdfplumber.open(caminho, password=senha) as pdf:
            for page in pdf.pages:
                # Extrai texto completo da página
                texto = page.extract_text()
                if not texto:
                    continue
                
                # Divide em linhas e procura por padrões específicos do Bradesco
                linhas = texto.split('\n')
                
                for i, linha in enumerate(linhas):
                    # Procura linhas com datas (formato dd/mm)
                    data_match = re.search(r'(\d{1,2}/\d{1,2})', linha)
                    if data_match:
                        data = data_match.group(1)
                        
                        # Procura valores na mesma linha ou linhas próximas
                        contexto = ' '.join(linhas[max(0, i-2):i+3])  # Linha atual + 2 antes/depois
                        
                        # Busca valores monetários no contexto
                        valores = re.findall(r'\d{1,3}(?:\.\d{3})*,\d{2}', contexto)
                        if valores:
                            for valor_str in valores:
                                if valor_str != '0,00':  # Ignora valores zero
                                    # Extrai descrição (texto entre data e valor)
                                    desc_raw = linha.split(data)[-1] if data in linha else linha
                                    desc = re.sub(r'[^a-zA-Z\s]', ' ', desc_raw)  # Remove símbolos
                                    desc = ' '.join(desc.split())[:50]  # Limpa espaços e limita
                                    
                                    # Infere tipo baseado em palavras-chave
                                    contexto_lower = contexto.lower()
                                    if any(word in contexto_lower for word in ['pagt', 'debito', 'saque', 'pagamento']):
                                        tipo = 'D'
                                    else:
                                        tipo = 'C'
                                    
                                    # Converte valor para float
                                    try:
                                        valor_num = float(valor_str.replace('.', '').replace(',', '.'))
                                    except:
                                        valor_num = 0.0
                                    
                                    if valor_num > 0:
                                        transacoes.append({
                                            'data_movimento': f"2024-{data.replace('/', '-')}",  # Assume ano atual
                                            'descricao_original': desc or 'Movimento Bradesco',
                                            'valor': valor_num,
                                            'tipo_movimento': tipo,
                                            'linha_original': linha[:100]
                                        })
        
        if transacoes:
            df = pd.DataFrame(transacoes)
            print(f"✅ Bradesco: {len(df)} transações extraídas")
            return df
        else:
            print("⚠️ Bradesco: Nenhuma transação identificada")
            return pd.DataFrame()
    
    @staticmethod
    def _tentar_parsing_automatico(df: pd.DataFrame) -> pd.DataFrame:
        """Tenta parsing automático juntando colunas do Tabula em linhas e extraindo transações"""
        print("🤖 Tentando parsing automático das colunas extraídas...")
        
        linhas_reconstruidas = []
        
        for _, row in df.iterrows():
            # Junta todas as células não-nulas da linha em texto único
            valores = [str(val).strip() for val in row.values if pd.notna(val) and str(val).strip()]
            linha_completa = ' '.join(valores)
            
            if linha_completa:
                linhas_reconstruidas.append(linha_completa)
        
        if not linhas_reconstruidas:
            return df  # Retorna original se não conseguir reconstruir
        
        # Aplica parsing das linhas reconstruídas
        padrao_data = r'\d{1,2}/\d{1,2}/(?:\d{2}|\d{4})'
        padrao_valor = r'(?:R\$\s*)?[-\(]?\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d{2})[-\)]?'
        
        transacoes_parsed = []
        
        for linha in linhas_reconstruidas:
            # Busca padrões de data e valor
            match_data = re.search(padrao_data, linha)
            matches_valor = re.findall(padrao_valor, linha)
            
            if match_data and matches_valor:
                data = match_data.group(0)
                valor_raw = matches_valor[-1]  # Último valor (geralmente o principal)
                
                # Normaliza valor
                valor_norm = 0.0
                if valor_raw:
                    vr = valor_raw.replace('R$', '').replace('(', '-').replace(')', '')
                    vr = vr.replace('.', '').replace(',', '.')
                    vr = re.sub(r'[^0-9\-\.]', '', vr)
                    try:
                        valor_norm = float(vr)
                    except:
                        valor_norm = 0.0
                
                # Extrai descrição (texto entre data e último valor)
                desc = linha
                if match_data:
                    desc = desc.split(match_data.group(0), 1)[-1].strip()
                if valor_raw:
                    desc = desc.rsplit(valor_raw, 1)[0].strip()
                
                # Infere tipo (C/D) baseado no valor e palavras-chave
                tipo = 'D' if valor_norm < 0 or any(word in desc.lower() for word in ['pix enviado', 'pagamento', 'saque', 'debito', 'taxa', 'transferencia']) else 'C'
                
                transacoes_parsed.append({
                    'data_movimento': data,
                    'descricao_original': desc[:100],  # Limita descrição
                    'valor': abs(valor_norm),
                    'tipo_movimento': tipo,
                    'linha_original': linha
                })
        
        if transacoes_parsed:
            df_parsed = pd.DataFrame(transacoes_parsed)
            print(f"✅ Parsing automático: {len(df_parsed)} transações identificadas")
            return df_parsed
        else:
            print("⚠️ Parsing automático não encontrou transações válidas")
            return df  # Retorna original
    
    @staticmethod
    def gerar_fingerprint(df: pd.DataFrame) -> str:
        """Gera hash único baseado na estrutura do DataFrame"""
        try:
            # Combina nomes das colunas + tipos + primeiras linhas
            colunas = "|".join(sorted([str(col) for col in df.columns]))
            
            # Tipos de dados (com tratamento seguro)
            tipos = []
            for col in df.columns:
                try:
                    tipos.append(str(df[col].dtype))
                except:
                    tipos.append('object')
            tipos = "|".join(tipos)
            
            # Sample das primeiras linhas para detectar padrões
            sample = ""
            if len(df) > 0:
                try:
                    primeira_linha = "|".join([str(val) for val in df.iloc[0].values])
                    sample = primeira_linha[:100]  # Primeiros 100 chars
                except:
                    sample = f"rows_{len(df)}_cols_{len(df.columns)}"
            
            # Gera hash
            dados_fingerprint = f"{colunas}#{tipos}#{sample}"
            return hashlib.md5(dados_fingerprint.encode()).hexdigest()
            
        except Exception as e:
            # Fallback simples se houver problemas
            fallback = f"cols_{len(df.columns)}_rows_{len(df)}_error"
            return hashlib.md5(fallback.encode()).hexdigest()


# ==========================================
# ETAPA 5-7: NORMALIZAÇÃO E MAPEAMENTO
# ==========================================

class NormalizadorExtratos:
    """Aplica regras de normalização baseadas em mapeamentos"""
    
    def __init__(self, repositorio: RepositorioLayouts):
        self.repo = repositorio
    
    def normalizar(self, df: pd.DataFrame, fingerprint: str) -> Tuple[List[TransactionRecord], StatusProcessamento]:
        """Normaliza DataFrame usando mapeamento conhecido ou solicitando novo"""
        
        # Busca layout conhecido
        layout = self.repo.buscar_layout(fingerprint)
        
        if layout is None:
            return [], StatusProcessamento.LAYOUT_DESCONHECIDO
        
        # Aplica mapeamento
        mapeamento = layout['mapeamento_json']
        return self._aplicar_mapeamento(df, mapeamento)
    
    def _aplicar_mapeamento(self, df: pd.DataFrame, mapeamento: Dict[str, str]) -> Tuple[List[TransactionRecord], StatusProcessamento]:
        """Aplica regras de mapeamento ao DataFrame"""
        transacoes = []
        
        try:
            # Se o mapeamento for um wrapper com metadata, extrai o dicionário real
            if isinstance(mapeamento, dict) and 'mapping' in mapeamento:
                real_mapping = mapeamento['mapping']
            else:
                real_mapping = mapeamento

            # Renomeia colunas
            df_mapeado = df.rename(columns=real_mapping)
            
            for _, row in df_mapeado.iterrows():
                # Extrai dados OBRIGATÓRIOS do contrato
                # Defensive: ensure scalars (handle cases where row values are Series due to duplicate columns)
                def _scalar(v):
                    try:
                        if v is None:
                            return ''
                        if isinstance(v, pd.Series) or hasattr(v, '__iter__') and not isinstance(v, str):
                            # pick first non-null
                            for item in v:
                                if pd.notna(item) and str(item).strip():
                                    return item
                            return ''
                        return v
                    except Exception:
                        return v

                data_mov = self._normalizar_data(_scalar(row.get('data_movimento', '')))
                descricao_orig = str(_scalar(row.get('descricao_original', ''))).strip()
                valor = self._normalizar_valor(_scalar(row.get('valor', 0)))
                tipo = self._normalizar_tipo_movimento(_scalar(row.get('tipo_movimento', '')), valor, descricao_orig)
                
                # Valida campos obrigatórios
                if not data_mov or not descricao_orig or valor == 0:
                    continue  # Pula linhas inválidas
                
                # Gera hash SHA-256 único (Data + Valor + Descrição)
                id_hash = self._gerar_hash_sha256(data_mov, valor, descricao_orig)
                
                # Extrai dados OPCIONAIS do contrato
                codigo_hist = str(row.get('codigo_historico', '')).strip() or None
                saldo_final = self._normalizar_valor(row.get('saldo_final_linha'))
                id_banco = str(row.get('identificador_banco', '')).strip() or None
                
                # Cria registro seguindo o contrato padronizado
                transacao = TransactionRecord(
                    id_hash_unico=id_hash,
                    data_movimento=data_mov,
                    valor=abs(valor),  # Sempre positivo conforme contrato
                    tipo_movimento=tipo,  # "C" ou "D" conforme contrato
                    descricao_original=descricao_orig,
                    codigo_historico=codigo_hist,
                    saldo_final_linha=saldo_final if saldo_final != 0 else None,
                    identificador_banco=id_banco
                )
                
                transacoes.append(transacao)
            
            return transacoes, StatusProcessamento.SUCESSO
            
        except Exception as e:
            print(f"Erro na normalização: {e}")
            return [], StatusProcessamento.ERRO_NORMALIZACAO
    
    def _normalizar_data(self, data_raw: Any) -> str:
        """Normaliza data para formato YYYY-MM-DD"""
        if pd.isna(data_raw) or not data_raw:
            return ""
        
        data_str = str(data_raw).strip()
        
        # Padrões comuns
        padroes = [
            r'(\d{4})-(\d{2})-(\d{2})',  # 2024-12-09
            r'(\d{2})/(\d{2})/(\d{4})',  # 09/12/2024
            r'(\d{2})/(\d{2})/(\d{2})',  # 09/12/24
            r'(\d{2})-(\d{2})-(\d{4})',  # 09-12-2024
        ]
        
        for padrao in padroes:
            match = re.search(padrao, data_str)
            if match:
                if len(match.group(1)) == 4:  # Ano primeiro
                    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
                else:  # Dia primeiro
                    ano = match.group(3)
                    if len(ano) == 2:
                        ano = f"20{ano}"
                    return f"{ano}-{match.group(2)}-{match.group(1)}"
        
        return ""
    
    def _normalizar_valor(self, valor_raw: Any) -> float:
        """Normaliza valor para float"""
        if pd.isna(valor_raw) or valor_raw == "":
            return 0.0
        
        # Remove símbolos e converte
        valor_str = str(valor_raw).replace('R$', '').replace(',', '.').replace(' ', '')
        valor_str = re.sub(r'[^\d\.\-]', '', valor_str)
        
        try:
            return float(valor_str)
        except:
            return 0.0
    
    def _normalizar_tipo_movimento(self, tipo_raw: Any, valor: float, descricao: str) -> str:
        """
        Normaliza tipo de movimento para o CONTRATO PADRONIZADO:
        "C" (Crédito) ou "D" (Débito)
        """
        if pd.notna(tipo_raw) and tipo_raw:
            tipo_str = str(tipo_raw).lower()
            # Mapeia variações para o padrão C/D
            if any(word in tipo_str for word in ['credito', 'entrada', 'deposito', 'receita', 'c', 'credit']):
                return "C"
            elif any(word in tipo_str for word in ['debito', 'saida', 'pagamento', 'despesa', 'd', 'debit']):
                return "D"
        
        # Inferir pelo valor (valor negativo = débito)
        if valor < 0:
            return "D"
        elif valor > 0:
            return "C"
        
        # Inferir pela descrição (palavras-chave de débito)
        desc_lower = descricao.lower()
        if any(word in desc_lower for word in ['pagamento', 'compra', 'saque', 'debito', 'taxa', 'tarifa']):
            return "D"
        else:
            return "C"
    
    def _gerar_hash_sha256(self, data: str, valor: float, descricao: str) -> str:
        """
        Gera hash SHA-256 único seguindo o CONTRATO PADRONIZADO:
        Hash de Data + Valor + Descrição
        """
        dados = f"{data}|{valor}|{descricao}"
        return hashlib.sha256(dados.encode('utf-8')).hexdigest()


# ==========================================
# CLASSE PRINCIPAL DO SISTEMA
# ==========================================

class SistemaExtratoZero:
    """Sistema principal que orquestra todo o processo"""
    
    def __init__(self):
        self.repositorio = RepositorioLayouts()
        self.extrator = ExtratorUniversal()
        self.normalizador = NormalizadorExtratos(self.repositorio)
        
    def processar_extrato(self, caminho_arquivo: str, senha: str = None) -> Dict[str, Any]:
        """Pipeline completo de processamento"""
        
        resultado = {
            'status': StatusProcessamento.SUCESSO.value,
            'arquivo': caminho_arquivo,
            'fingerprint': '',
            'layout_conhecido': False,
            'transacoes_encontradas': 0,
            'transacoes_novas': 0,
            'transacoes_duplicadas': 0,
            'mensagem': '',
            'dados': []
        }
        
        try:
            # ETAPA 3: Extração
            print(f"📥 Extraindo dados de: {os.path.basename(caminho_arquivo)}")
            df_bruto = self.extrator.extrair_de_arquivo(caminho_arquivo, senha)
            
            if df_bruto.empty:
                resultado['status'] = StatusProcessamento.ERRO_EXTRACAO.value
                resultado['mensagem'] = "Nenhum dado extraído do arquivo"
                return resultado
            
            # ETAPA 4: Fingerprint
            print("🔍 Gerando impressão digital do layout...")
            fingerprint = self.extrator.gerar_fingerprint(df_bruto)
            resultado['fingerprint'] = fingerprint
            
            # ETAPA 5: Reconhecimento
            print("🧠 Verificando layout conhecido...")
            layout = self.repositorio.buscar_layout(fingerprint)
            # Se não encontrou layout por fingerprint, tenta detectar pelo nome do banco no arquivo
            if layout is None:
                banco_detectado = None
                # Heurística simples de detecção de banco
                nome_arquivo = os.path.basename(caminho_arquivo).lower()
                if 'c6' in nome_arquivo:
                    banco_detectado = 'C6'
                elif 'bradesco' in nome_arquivo:
                    banco_detectado = 'Bradesco'
                elif 'santander' in nome_arquivo:
                    banco_detectado = 'Santander'
                elif 'itau' in nome_arquivo:
                    banco_detectado = 'Itaú'
                # se detectou banco por heuristica, tenta buscar por banco
                if banco_detectado:
                    layout = self.repositorio.buscar_layout_por_banco(banco_detectado)
            
            if layout is None:
                # Tenta parsing automático para layouts desconhecidos
                if 'data_movimento' in df_bruto.columns:
                    print("✅ Colunas padronizadas detectadas, aplicando normalização direta...")
                    # Cria mapeamento automático para colunas já padronizadas
                    mapeamento_auto = {col: col for col in df_bruto.columns if col in [
                        'data_movimento', 'descricao_original', 'valor', 'tipo_movimento', 
                        'codigo_historico', 'saldo_final_linha', 'identificador_banco'
                    ]}
                    transacoes, status_norm = self.normalizador._aplicar_mapeamento(df_bruto, mapeamento_auto)
                    
                    if status_norm == StatusProcessamento.SUCESSO and transacoes:
                        # Validação das transações extraídas automaticamente
                        validacao = self.validar_transacoes_automaticas(transacoes)
                        
                        if validacao['valido']:
                            resultado['status'] = 'parsing_automatico_pendente_confirmacao'
                            resultado['transacoes_extraidas'] = [t.to_dict() for t in transacoes]
                            resultado['mensagem'] = f"✅ {len(transacoes)} transações extraídas automaticamente. Confirme se estão corretas."
                            resultado['fingerprint'] = fingerprint
                            resultado['validacao'] = validacao
                            return resultado
                
                resultado['status'] = StatusProcessamento.LAYOUT_DESCONHECIDO.value
                resultado['mensagem'] = f"Layout desconhecido. Fingerprint: {fingerprint[:8]}..."
                resultado['colunas_encontradas'] = list(df_bruto.columns)
                return resultado
            
            resultado['layout_conhecido'] = True
            print(f"✅ Layout reconhecido: {layout['nome_layout']}")
            
            # ETAPA 7: Normalização
            print("🔄 Aplicando normalização...")
            transacoes, status_norm = self.normalizador.normalizar(df_bruto, fingerprint)
            
            if status_norm != StatusProcessamento.SUCESSO:
                resultado['status'] = status_norm.value
                resultado['mensagem'] = "Erro na normalização dos dados"
                return resultado
            
            # ETAPA 8: Verificação de duplicidade
            print("🔍 Verificando duplicidade...")
            transacoes_novas = []
            duplicadas = 0
            
            for transacao in transacoes:
                if not self.repositorio.verificar_duplicidade(transacao.id_hash_unico):
                    transacoes_novas.append(transacao)
                else:
                    duplicadas += 1
            
            # ETAPA 9: Persistência
            print("💾 Registrando transações...")
            for transacao in transacoes_novas:
                self.repositorio.registrar_transacao(transacao)
            
            # Resultado final
            resultado['transacoes_encontradas'] = len(transacoes)
            resultado['transacoes_novas'] = len(transacoes_novas)
            resultado['transacoes_duplicadas'] = duplicadas
            resultado['dados'] = [t.to_dict() for t in transacoes_novas]
            resultado['mensagem'] = f"✅ Processado com sucesso! {len(transacoes_novas)} transações novas"
            
            print(f"🎉 Concluído! {len(transacoes_novas)} transações importadas")
            
            return resultado
            
        except Exception as e:
            resultado['status'] = StatusProcessamento.ERRO_EXTRACAO.value
            resultado['mensagem'] = f"Erro no processamento: {str(e)}"
            return resultado
    
    def criar_mapeamento_interativo(self, caminho_arquivo: str) -> Dict[str, Any]:
        """Interface para criar mapeamento de layout desconhecido"""
        
        try:
            # Extrai dados para análise
            df_bruto = self.extrator.extrair_de_arquivo(caminho_arquivo)
            fingerprint = self.extrator.gerar_fingerprint(df_bruto)
            
            print(f"🆕 Criando mapeamento para novo layout")
            print(f"Fingerprint: {fingerprint}")
            print(f"Colunas encontradas: {list(df_bruto.columns)}")
            print()
            
            # Mostra preview dos dados
            print("📋 Preview dos dados:")
            print(df_bruto.head(3).to_string())
            print()
            
            # Campos do CONTRATO PADRONIZADO
            campos_obrigatorios = [
                'data_movimento',        # ISO 8601: YYYY-MM-DD
                'descricao_original',    # Texto bruto do extrato
                'valor',                # Valor sempre positivo
                'tipo_movimento'        # "C" (Crédito) ou "D" (Débito)
            ]
            
            campos_opcionais = [
                'codigo_historico',      # Código de transação do banco (PIX, TED, DOC)
                'saldo_final_linha',    # Saldo após esta transação
                'identificador_banco'   # ID único do banco (FITID do OFX)
            ]
            
            print("🎯 Mapeamento necessário:")
            print("Campos OBRIGATÓRIOS:", campos_obrigatorios)
            print("Campos OPCIONAIS:", campos_opcionais)
            print()
            
            return {
                'fingerprint': fingerprint,
                'colunas_originais': list(df_bruto.columns),
                'preview_dados': df_bruto.head(5).to_dict('records'),
                'campos_obrigatorios': campos_obrigatorios,
                'campos_opcionais': campos_opcionais
            }
            
        except Exception as e:
            return {'erro': f"Erro na análise: {str(e)}"}
    
    def validar_transacoes_automaticas(self, transacoes: List[TransactionRecord]) -> Dict[str, Any]:
        """Mostra preview das transações extraídas automaticamente e pede confirmação"""
        print("\n🔍 VALIDAÇÃO - Transações extraídas automaticamente:")
        print("=" * 60)
        
        if not transacoes:
            return {'valido': False, 'erro': 'Nenhuma transação extraída'}
        
        # Mostra primeiras 5 transações para validação
        for i, t in enumerate(transacoes[:5]):
            print(f"\n[{i+1}] Data: {t.data_movimento}")
            print(f"    Valor: R$ {t.valor:.2f} ({t.tipo_movimento})")
            print(f"    Descrição: {t.descricao_original}")
        
        if len(transacoes) > 5:
            print(f"\n... e mais {len(transacoes) - 5} transações")
        
        print(f"\n📊 RESUMO: {len(transacoes)} transações extraídas")
        
        return {
            'valido': True,
            'total_transacoes': len(transacoes),
            'preview_mostrado': True,
            'confirmacao_pendente': True
        }
    
    def confirmar_e_salvar_transacoes(self, fingerprint: str, transacoes: List[TransactionRecord]) -> Dict[str, Any]:
        """Confirma e salva transações extraídas automaticamente"""
        resultado = {
            'status': StatusProcessamento.SUCESSO.value,
            'transacoes_salvas': 0,
            'transacoes_duplicadas': 0,
            'mensagem': ''
        }
        
        try:
            # Salva layout automático (para reconhecer futuramente)
            mapeamento_auto = {
                'data_movimento': 'data_movimento',
                'descricao_original': 'descricao_original', 
                'valor': 'valor',
                'tipo_movimento': 'tipo_movimento'
            }
            
            self.repositorio.salvar_layout(
                fingerprint, 
                f"Layout_Auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}", 
                "Detectado_Automaticamente",
                list(mapeamento_auto.keys()), 
                mapeamento_auto
            )
            
            # Verifica duplicidade e persiste transações novas
            transacoes_novas = []
            duplicadas = 0
            
            for transacao in transacoes:
                if not self.repositorio.verificar_duplicidade(transacao.id_hash_unico):
                    self.repositorio.registrar_transacao(transacao)
                    transacoes_novas.append(transacao)
                else:
                    duplicadas += 1
            
            resultado['transacoes_salvas'] = len(transacoes_novas)
            resultado['transacoes_duplicadas'] = duplicadas
            resultado['mensagem'] = f"✅ {len(transacoes_novas)} transações salvas, {duplicadas} duplicadas ignoradas"
            
            print(f"🎉 Processamento concluído! {len(transacoes_novas)} transações importadas")
            
            return resultado
            
        except Exception as e:
            resultado['status'] = StatusProcessamento.ERRO_PERSISTENCIA.value
            resultado['mensagem'] = f"Erro ao salvar: {str(e)}"
            return resultado

    def salvar_mapeamento(self, fingerprint: str, nome_layout: str, 
                         banco: str, mapeamento: Dict[str, str]) -> bool:
        """Salva mapeamento criado pelo usuário"""
        try:
            # Busca layout original para obter colunas
            df_temp = pd.DataFrame(columns=list(mapeamento.keys()))
            self.repositorio.salvar_layout(
                fingerprint, nome_layout, banco,
                list(mapeamento.keys()), mapeamento
            )
            print(f"✅ Mapeamento '{nome_layout}' salvo com sucesso!")
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar mapeamento: {e}")
            return False


# ==========================================
# FUNÇÃO DE TESTE E DEMONSTRAÇÃO
# ==========================================

def testar_sistema():
    """Função de teste do sistema completo"""
    sistema = SistemaExtratoZero()
    
    print("🚀 SISTEMA ZERO - Importação de Extratos")
    print("=" * 50)
    
    # Exemplo de uso
    arquivo_teste = "extrato_teste.csv"
    
    if os.path.exists(arquivo_teste):
        resultado = sistema.processar_extrato(arquivo_teste)
        
        print("\n📊 RESULTADO:")
        print(f"Status: {resultado['status']}")
        print(f"Mensagem: {resultado['mensagem']}")
        print(f"Layout conhecido: {resultado['layout_conhecido']}")
        print(f"Transações encontradas: {resultado['transacoes_encontradas']}")
        print(f"Transações novas: {resultado['transacoes_novas']}")
        
    else:
        print("⚠️ Arquivo de teste não encontrado")
        print("Crie um arquivo CSV com colunas: Data,Descricao,Tipo,Valor,Saldo")


if __name__ == "__main__":
    testar_sistema()