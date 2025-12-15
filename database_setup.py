import sqlite3
import os
import json

DATABASE_PATH = 'data/financeiro.db'

def criar_tabelas():
    """Cria todas as tabelas do banco de dados."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Tabela de usuários (PF)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            cpf TEXT UNIQUE,
            telefone TEXT,
            data_criacao TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabela de empresas (PJ)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            nome TEXT NOT NULL,
            cnpj TEXT UNIQUE,
            data_criacao TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')

    # Tabela de bancos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bancos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            codigo TEXT UNIQUE,
            ativo INTEGER DEFAULT 1
        )
    ''')

    # Tabela de contas bancárias
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contas_bancarias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            banco_id INTEGER NOT NULL,
            agencia TEXT,
            conta_corrente TEXT NOT NULL,
            tipo_conta TEXT NOT NULL, -- 'PF' ou 'PJ'
            usuario_id INTEGER, -- Para contas PF
            empresa_id INTEGER, -- Para contas PJ
            saldo REAL DEFAULT 0,
            ativo INTEGER DEFAULT 1,
            data_criacao TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (banco_id) REFERENCES bancos (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
            FOREIGN KEY (empresa_id) REFERENCES empresas (id)
        )
    ''')

    # Tabela de cartões de crédito
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cartoes_credito (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            banco_id INTEGER NOT NULL,
            usuario_id INTEGER, -- Dono PF
            empresa_id INTEGER, -- Dono PJ
            nome TEXT NOT NULL,
            bandeira TEXT,
            limite REAL,
            dia_fechamento INTEGER NOT NULL,
            dia_vencimento INTEGER NOT NULL,
            ultimos_4_digitos TEXT NOT NULL,
            validade_mes_ano TEXT NOT NULL,
            ativo INTEGER DEFAULT 1,
            data_criacao TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (banco_id) REFERENCES bancos (id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
            FOREIGN KEY (empresa_id) REFERENCES empresas (id)
        )
    ''')

    # Tabela de contatos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contatos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL, -- 'cliente', 'fornecedor', 'pessoal'
            cpf_cnpj TEXT,
            empresa_id INTEGER, -- Opcional para contatos globais/PF
            telefone TEXT,
            email TEXT,
            endereco TEXT,
            data_criacao TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (empresa_id) REFERENCES empresas (id)
        )
    ''')

    # Tabela de categorias
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            tipo TEXT NOT NULL, -- 'entrada' ou 'saida'
            empresa_id INTEGER, -- Opcional para categorias globais/PF
            cor TEXT,
            icone TEXT,
            data_criacao TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (empresa_id) REFERENCES empresas (id),
            UNIQUE(nome, tipo, empresa_id)
        )
    ''')

    # Tabela de transações (atualizada)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            tipo TEXT NOT NULL, -- 'entrada' ou 'saida'
            valor REAL NOT NULL,
            descricao TEXT,
            categoria_id INTEGER,
            conta_bancaria_id INTEGER,
            cartao_credito_id INTEGER,
            contato_id INTEGER, -- Cliente/fornecedor relacionado
            empresa_id INTEGER, -- Para transações PJ
            banco_origem TEXT, -- Mantido para compatibilidade
            fonte TEXT DEFAULT 'manual', -- 'extrato', 'manual', 'cartao'
            data_criacao TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (categoria_id) REFERENCES categorias (id),
            FOREIGN KEY (conta_bancaria_id) REFERENCES contas_bancarias (id),
            FOREIGN KEY (cartao_credito_id) REFERENCES cartoes_credito (id),
            FOREIGN KEY (contato_id) REFERENCES contatos (id),
            FOREIGN KEY (empresa_id) REFERENCES empresas (id)
        )
    ''')

    # Tabela de extratos (atualizada)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS extratos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            banco_id INTEGER,
            conta_bancaria_id INTEGER,
            arquivo_nome TEXT,
            data_upload TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'processado',
            total_transacoes INTEGER DEFAULT 0,
            total_entradas REAL DEFAULT 0,
            total_saidas REAL DEFAULT 0,
            FOREIGN KEY (banco_id) REFERENCES bancos (id),
            FOREIGN KEY (conta_bancaria_id) REFERENCES contas_bancarias (id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Todas as tabelas criadas com sucesso!")

def verificar_banco_e_tabelas():
    """Verifica se o banco e tabelas existem."""
    if not os.path.exists(DATABASE_PATH):
        return False, "Banco de dados não existe"

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        tabelas_necessarias = [
            'usuarios', 'empresas', 'bancos', 'contas_bancarias',
            'cartoes_credito', 'contatos', 'categorias', 'transacoes', 'extratos'
        ]

        tabelas_faltando = []
        for tabela in tabelas_necessarias:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tabela,))
            if not cursor.fetchone():
                tabelas_faltando.append(tabela)

        conn.close()

        if tabelas_faltando:
            return False, f"Tabelas faltando: {', '.join(tabelas_faltando)}"

        return True, "Banco e todas as tabelas existem"

    except sqlite3.Error as e:
        return False, f"Erro ao verificar banco: {e}"

def inserir_dados_iniciais():
    """Insere dados iniciais (bancos suportados e categorias básicas)."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Inserir bancos suportados
    bancos = [
        ('BANCO_DO_BRASIL', '001'),
        ('ITAÚ', '341'),
        ('C6', '336'),
        ('SANTANDER', '033'),
        ('BRADESCO', '237'),
        ('NUBANK', '260'),
        ('INTER', '077'),
        ('ORIGINAL', '212'),
        ('PAN', '623'),
        ('BMG', '318')
    ]

    cursor.executemany('''
        INSERT OR IGNORE INTO bancos (nome, codigo) VALUES (?, ?)
    ''', bancos)

    # Inserir categorias básicas
    categorias_entrada = [
        'Salário', 'Freelance', 'Investimentos', 'Aluguel', 'Dividendos',
        'Reembolso', 'Prêmio', 'Outros Créditos'
    ]

    categorias_saida = [
        'Alimentação', 'Transporte', 'Moradia', 'Saúde', 'Educação',
        'Lazer', 'Vestuário', 'Contas', 'Impostos', 'Outros Débitos'
    ]

    for cat in categorias_entrada:
        cursor.execute('''
            INSERT OR IGNORE INTO categorias (nome, tipo) VALUES (?, 'entrada')
        ''', (cat,))

    for cat in categorias_saida:
        cursor.execute('''
            INSERT OR IGNORE INTO categorias (nome, tipo) VALUES (?, 'saida')
        ''', (cat,))

    conn.commit()
    conn.close()
    print("✅ Dados iniciais inseridos!")

# ===== FUNÇÕES DE INSERÇÃO =====

def inserir_usuario(nome, email, cpf=None, telefone=None):
    """Insere um novo usuário no banco de dados."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO usuarios (nome, email, cpf, telefone)
            VALUES (?, ?, ?, ?)
        ''', (nome, email, cpf, telefone))

        usuario_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return usuario_id, None  # Retorna ID e erro (None se sucesso)

    except sqlite3.IntegrityError as e:
        return None, f"Erro de integridade: {str(e)}"
    except Exception as e:
        return None, str(e)

def buscar_usuarios():
    """Busca todos os usuários do banco de dados."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, nome, email, cpf, telefone, data_criacao
            FROM usuarios
            ORDER BY nome
        ''')

        usuarios = cursor.fetchall()
        conn.close()

        # Converte para lista de dicionários
        usuarios_dict = []
        for usuario in usuarios:
            usuarios_dict.append({
                'id': usuario[0],
                'nome': usuario[1],
                'email': usuario[2],
                'cpf': usuario[3],
                'telefone': usuario[4],
                'data_criacao': usuario[5]
            })

        return usuarios_dict, None

    except Exception as e:
        return None, str(e)

def buscar_usuario_por_id(usuario_id):
    """Busca um usuário específico pelo ID."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, nome, email, cpf, telefone, data_criacao
            FROM usuarios
            WHERE id = ?
        ''', (usuario_id,))

        usuario = cursor.fetchone()
        conn.close()

        if usuario:
            return {
                'id': usuario[0],
                'nome': usuario[1],
                'email': usuario[2],
                'cpf': usuario[3],
                'telefone': usuario[4],
                'data_criacao': usuario[5]
            }, None
        else:
            return None, "Usuário não encontrado"

    except Exception as e:
        return None, str(e)

def atualizar_usuario(usuario_id, nome=None, email=None, cpf=None, telefone=None):
    """Atualiza os dados de um usuário."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Verifica se o usuário existe
        cursor.execute('SELECT id FROM usuarios WHERE id = ?', (usuario_id,))
        if not cursor.fetchone():
            conn.close()
            return False, "Usuário não encontrado"

        # Monta a query dinamicamente apenas com campos fornecidos
        campos = []
        valores = []

        if nome is not None:
            campos.append('nome = ?')
            valores.append(nome)
        if email is not None:
            campos.append('email = ?')
            valores.append(email)
        if cpf is not None:
            campos.append('cpf = ?')
            valores.append(cpf)
        if telefone is not None:
            campos.append('telefone = ?')
            valores.append(telefone)

        if not campos:
            conn.close()
            return False, "Nenhum campo para atualizar"

        valores.append(usuario_id)  # Para o WHERE

        query = f'UPDATE usuarios SET {", ".join(campos)} WHERE id = ?'
        cursor.execute(query, valores)

        conn.commit()
        conn.close()

        return True, None

    except sqlite3.IntegrityError as e:
        return False, f"Erro de integridade: {str(e)}"
    except Exception as e:
        return False, str(e)

def excluir_usuario(usuario_id):
    """Exclui um usuário do banco de dados."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Verifica se o usuário existe
        cursor.execute('SELECT id FROM usuarios WHERE id = ?', (usuario_id,))
        if not cursor.fetchone():
            conn.close()
            return False, "Usuário não encontrado"

        # Exclui o usuário
        cursor.execute('DELETE FROM usuarios WHERE id = ?', (usuario_id,))

        conn.commit()
        conn.close()

        return True, None

    except Exception as e:
        return False, str(e)

def inserir_empresa(usuario_id, nome, cnpj=None):
    """Insere uma nova empresa no banco de dados."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO empresas (usuario_id, nome, cnpj)
            VALUES (?, ?, ?)
        ''', (usuario_id, nome, cnpj))

        empresa_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return empresa_id, None

    except sqlite3.IntegrityError as e:
        return None, f"Erro de integridade: {str(e)}"
    except Exception as e:
        return None, str(e)

def inserir_banco(nome, codigo=None):
    """Insere um novo banco no banco de dados."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO bancos (nome, codigo)
            VALUES (?, ?)
        ''', (nome, codigo))

        banco_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return banco_id, None

    except sqlite3.IntegrityError as e:
        return None, f"Erro de integridade: {str(e)}"
    except Exception as e:
        return None, str(e)

def inserir_conta_bancaria(banco_id, usuario_id, nome, agencia=None, conta=None, tipo='corrente'):
    """Insere uma nova conta bancária no banco de dados."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO contas_bancarias (banco_id, usuario_id, nome, agencia, conta, tipo)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (banco_id, usuario_id, nome, agencia, conta, tipo))

        conta_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return conta_id, None

    except Exception as e:
        return None, str(e)

def inserir_cartao_credito(conta_id, nome, limite=None, vencimento=None):
    """Insere um novo cartão de crédito no banco de dados."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO cartoes_credito (conta_bancaria_id, nome, limite, vencimento)
            VALUES (?, ?, ?, ?)
        ''', (conta_id, nome, limite, vencimento))

        cartao_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return cartao_id, None

    except Exception as e:
        return None, str(e)

def inserir_contato(usuario_id, nome, tipo='cliente', telefone=None, email=None):
    """Insere um novo contato (cliente/fornecedor) no banco de dados."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO contatos (usuario_id, nome, tipo, telefone, email)
            VALUES (?, ?, ?, ?, ?)
        ''', (usuario_id, nome, tipo, telefone, email))

        contato_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return contato_id, None

    except Exception as e:
        return None, str(e)

def inserir_categoria(nome, tipo, empresa_id=None, cor=None, icone=None):
    """Insere uma nova categoria no banco de dados."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO categorias (nome, tipo, empresa_id, cor, icone)
            VALUES (?, ?, ?, ?, ?)
        ''', (nome, tipo, empresa_id, cor, icone))

        categoria_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return categoria_id, None

    except sqlite3.IntegrityError as e:
        return None, f"Erro de integridade: {str(e)}"
    except Exception as e:
        return None, str(e)

def inserir_transacao(data, tipo, valor, descricao=None, categoria_id=None, conta_bancaria_id=None,
                     cartao_credito_id=None, contato_id=None, empresa_id=None, fonte='manual'):
    """Insere uma nova transação no banco de dados."""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO transacoes (data, tipo, valor, descricao, categoria_id, conta_bancaria_id,
                                  cartao_credito_id, contato_id, empresa_id, fonte)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data, tipo, valor, descricao, categoria_id, conta_bancaria_id,
              cartao_credito_id, contato_id, empresa_id, fonte))

        transacao_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return transacao_id, None

    except Exception as e:
        return None, str(e)

def migrar_transacoes_json():
    """Migra transações do JSON para o banco."""
    json_path = 'data/transacoes.json'
    if not os.path.exists(json_path):
        print("❌ Arquivo JSON não encontrado.")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        transacoes_json = json.load(f)

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    migradas = 0
    saidas_detectadas = 0
    
    for transacao in transacoes_json:
        # Determinar tipo baseado na descrição e valor
        tipo = transacao.get('tipo', 'entrada')
        descricao = transacao.get('descricao', '').lower()
        valor = transacao.get('valor', 0)
        
        # Detectar saídas pela descrição
        if any(palavra in descricao for palavra in ['saída', 'saida', 'débito', 'debito', 'pix enviado', 'transferência enviada']):
            tipo = 'saida'
            saidas_detectadas += 1
        elif valor < 0:  # Valores negativos são saídas
            tipo = 'saida'
            saidas_detectadas += 1
        else:
            tipo = 'entrada'

        # Buscar categoria_id
        categoria_nome = transacao.get('categoria')
        categoria_id = None
        if categoria_nome:
            cursor.execute('''
                SELECT id FROM categorias WHERE nome = ? AND tipo = ?
            ''', (categoria_nome, tipo))
            result = cursor.fetchone()
            categoria_id = result[0] if result else None

        # Extrair banco da descrição
        banco_nome = None
        desc_original = transacao.get('descricao', '')
        if ': ' in desc_original:
            banco_nome = desc_original.split(': ')[0]

        # Inserir transação
        cursor.execute('''
            INSERT OR IGNORE INTO transacoes
            (data, tipo, valor, descricao, categoria_id, banco_origem, fonte)
            VALUES (?, ?, ?, ?, ?, ?, 'extrato')
        ''', (
            transacao.get('data'),
            tipo,
            abs(valor),  # Garantir valor positivo
            transacao.get('descricao'),
            categoria_id,
            banco_nome
        ))
        migradas += 1

    conn.commit()
    conn.close()
    print(f"✅ Migradas {migradas} transações do JSON para o banco!")
    print(f"   📊 Detectadas {saidas_detectadas} saídas automaticamente")

if __name__ == "__main__":
    print("🔍 Verificando banco e tabelas...")
    existe, mensagem = verificar_banco_e_tabelas()
    print(f"Resultado: {mensagem}")

    if not existe:
        print("📦 Criando tabelas...")
        criar_tabelas()

        print("📝 Inserindo dados iniciais...")
        inserir_dados_iniciais()

        print("🔄 Migrando dados do JSON...")
        migrar_transacoes_json()

    print("✅ Setup do banco de dados concluído!")