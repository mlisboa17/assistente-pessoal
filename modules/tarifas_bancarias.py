"""
Base de Dados de Classificação de Tarifas Bancárias - Banco do Brasil
"""

import json
import sqlite3
import os
from datetime import datetime

# Base de conhecimento de tarifas do BB
TARIFAS_BB = {
    "9903": {
        "nome": "Pacote de Serviços",
        "descricao": "Tarifa mensal do pacote de serviços contratado",
        "categoria": "Manutenção de Conta",
        "tipo": "Recorrente Mensal",
        "inclui": [
            "Saques em caixa eletrônico",
            "Consultas em caixa eletrônico",
            "Extratos impressos",
            "Transferências DOC/TED (conforme franquia)",
            "Segunda via de cartão",
            "Talão de cheques (se aplicável)"
        ],
        "nao_inclui": [
            "PIX (sempre gratuito para PF)",
            "Tarifas específicas de cartão de crédito",
            "IOF",
            "Taxas judiciais"
        ],
        "observacoes": "PIX é sempre gratuito para pessoa física e não consome franquia do pacote"
    },
    "13013": {
        "nome": "Tarifa de Pacote - Pessoa Jurídica",
        "descricao": "Tarifa de pacote de serviços para conta empresarial (PJ)",
        "categoria": "Manutenção de Conta PJ",
        "tipo": "Recorrente Mensal",
        "inclui": [
            "Saques em caixa eletrônico (conforme franquia)",
            "Consultas",
            "Extratos",
            "Transferências DOC/TED (conforme franquia)",
            "Outros serviços do pacote PJ"
        ],
        "nao_inclui": [
            "PIX (pode ter cobrança específica para PJ dependendo do contrato)",
            "Tarifas de boletos além da franquia",
            "IOF"
        ],
        "observacoes": "Para PJ, PIX pode ter tarifa específica dependendo do contrato, mas não está incluído no código 13013"
    },
    "13373": {
        "nome": "Taxa de Transferência Judicial/Especial",
        "descricao": "Taxa para transferências judiciais, depósitos judiciais ou transferências especiais",
        "categoria": "Taxas Judiciais",
        "tipo": "Por Operação",
        "inclui": [
            "Depósitos judiciais",
            "Transferências para contas judiciais",
            "Outras operações especiais determinadas por ordem judicial"
        ],
        "observacoes": "Geralmente acompanhado de número de processo ou identificador judicial"
    },
    "PIX_PF": {
        "nome": "PIX - Pessoa Física",
        "descricao": "Transferências via PIX para pessoa física",
        "categoria": "Transferências",
        "tipo": "Por Operação",
        "tarifa": 0.00,
        "observacoes": "Totalmente gratuito e ilimitado para pessoa física. Não aparece como débito no extrato."
    },
    "PIX_PJ": {
        "nome": "PIX - Pessoa Jurídica",
        "descricao": "Transferências via PIX para pessoa jurídica (pode ter tarifa conforme contrato)",
        "categoria": "Transferências PJ",
        "tipo": "Por Operação",
        "tarifa": "Variável conforme contrato",
        "observacoes": "Para PJ pode haver cobrança específica, mas não está vinculada ao pacote 13013"
    }
}

class RepositorioTarifas:
    """Gerencia base de conhecimento de tarifas bancárias"""
    
    def __init__(self, db_path: str = "data/tarifas_bancarias.db"):
        self.db_path = db_path
        self._criar_tabelas()
        self._popular_tarifas_bb()
    
    def _criar_tabelas(self):
        """Cria estrutura do banco de tarifas"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # Tabela de códigos de tarifa
            conn.execute("""
                CREATE TABLE IF NOT EXISTS codigos_tarifa (
                    codigo TEXT PRIMARY KEY,
                    banco TEXT NOT NULL,
                    nome TEXT NOT NULL,
                    descricao TEXT,
                    categoria TEXT,
                    tipo TEXT,
                    tarifa_media REAL,
                    observacoes TEXT,
                    data_criacao TEXT NOT NULL,
                    data_atualizacao TEXT
                )
            """)
            
            # Tabela de itens incluídos/não incluídos
            conn.execute("""
                CREATE TABLE IF NOT EXISTS itens_tarifa (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo_tarifa TEXT NOT NULL,
                    item TEXT NOT NULL,
                    incluido BOOLEAN NOT NULL,
                    FOREIGN KEY (codigo_tarifa) REFERENCES codigos_tarifa(codigo)
                )
            """)
            
            # Tabela de histórico de tarifas identificadas
            conn.execute("""
                CREATE TABLE IF NOT EXISTS historico_tarifas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo_tarifa TEXT NOT NULL,
                    valor REAL NOT NULL,
                    data_transacao TEXT NOT NULL,
                    id_adicional TEXT,
                    linha_original TEXT,
                    data_processamento TEXT NOT NULL,
                    FOREIGN KEY (codigo_tarifa) REFERENCES codigos_tarifa(codigo)
                )
            """)
    
    def _popular_tarifas_bb(self):
        """Popula base com tarifas conhecidas do BB"""
        with sqlite3.connect(self.db_path) as conn:
            for codigo, info in TARIFAS_BB.items():
                # Verificar se já existe
                cursor = conn.execute(
                    "SELECT codigo FROM codigos_tarifa WHERE codigo = ? AND banco = 'Banco do Brasil'",
                    (codigo,)
                )
                
                if cursor.fetchone() is None:
                    # Inserir código de tarifa
                    conn.execute("""
                        INSERT INTO codigos_tarifa 
                        (codigo, banco, nome, descricao, categoria, tipo, tarifa_media, observacoes, data_criacao)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        codigo,
                        "Banco do Brasil",
                        info.get("nome", ""),
                        info.get("descricao", ""),
                        info.get("categoria", ""),
                        info.get("tipo", ""),
                        info.get("tarifa", None),
                        info.get("observacoes", ""),
                        datetime.now().isoformat()
                    ))
                    
                    # Inserir itens incluídos
                    for item in info.get("inclui", []):
                        conn.execute("""
                            INSERT INTO itens_tarifa (codigo_tarifa, item, incluido)
                            VALUES (?, ?, ?)
                        """, (codigo, item, True))
                    
                    # Inserir itens não incluídos
                    for item in info.get("nao_inclui", []):
                        conn.execute("""
                            INSERT INTO itens_tarifa (codigo_tarifa, item, incluido)
                            VALUES (?, ?, ?)
                        """, (codigo, item, False))
    
    def classificar_tarifa(self, codigo: str, banco: str = "Banco do Brasil"):
        """Retorna classificação de uma tarifa"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT nome, descricao, categoria, tipo, observacoes
                FROM codigos_tarifa
                WHERE codigo = ? AND banco = ?
            """, (codigo, banco))
            
            row = cursor.fetchone()
            if row:
                return {
                    "codigo": codigo,
                    "nome": row[0],
                    "descricao": row[1],
                    "categoria": row[2],
                    "tipo": row[3],
                    "observacoes": row[4]
                }
            return None
    
    def registrar_tarifa_historico(self, codigo: str, valor: float, 
                                   data_transacao: str, id_adicional: str = None,
                                   linha_original: str = None):
        """Registra uma tarifa identificada no histórico"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO historico_tarifas 
                (codigo_tarifa, valor, data_transacao, id_adicional, linha_original, data_processamento)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                codigo,
                valor,
                data_transacao,
                id_adicional,
                linha_original,
                datetime.now().isoformat()
            ))
    
    def listar_todas_tarifas(self, banco: str = "Banco do Brasil"):
        """Lista todas as tarifas conhecidas"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT codigo, nome, categoria, tipo, observacoes
                FROM codigos_tarifa
                WHERE banco = ?
                ORDER BY categoria, codigo
            """, (banco,))
            
            tarifas = []
            for row in cursor.fetchall():
                tarifas.append({
                    "codigo": row[0],
                    "nome": row[1],
                    "categoria": row[2],
                    "tipo": row[3],
                    "observacoes": row[4]
                })
            
            return tarifas

# Teste e exibição
if __name__ == "__main__":
    print("🗄️  CRIANDO BASE DE DADOS DE TARIFAS BANCÁRIAS")
    print("=" * 100)
    
    repo = RepositorioTarifas()
    
    print("\n✅ Base de dados criada com sucesso!")
    print(f"📂 Localização: {repo.db_path}")
    
    print("\n\n📋 TARIFAS CADASTRADAS - BANCO DO BRASIL:\n")
    print("-" * 100)
    
    tarifas = repo.listar_todas_tarifas()
    
    for tarifa in tarifas:
        print(f"\n🔹 Código: {tarifa['codigo']}")
        print(f"   Nome: {tarifa['nome']}")
        print(f"   Categoria: {tarifa['categoria']}")
        print(f"   Tipo: {tarifa['tipo']}")
        if tarifa['observacoes']:
            print(f"   📝 {tarifa['observacoes']}")
        print("-" * 100)
    
    print("\n\n💡 INFORMAÇÕES IMPORTANTES:\n")
    print("✅ PIX para Pessoa Física: GRATUITO e ilimitado (não aparece como débito)")
    print("⚠️  PIX para Pessoa Jurídica: Pode ter tarifa específica conforme contrato")
    print("📦 Código 9903: Pacote de serviços mensal (NÃO inclui PIX)")
    print("🏢 Código 13013: Pacote PJ (PIX não está vinculado a este código)")
    print("⚖️  Código 13373: Transferências judiciais/especiais")
    print("\n" + "=" * 100)
