"""
🗄️ Database Manager - Versão Completa
Gerenciador de banco de dados SQLite com suporte futuro a PostgreSQL
Preparado para integração com Flutter App
"""
import os
import json
from datetime import datetime, date
from typing import List, Dict, Optional, Any, Union
from contextlib import contextmanager
from decimal import Decimal

# SQLAlchemy para SQL
try:
    from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Date, Index, Enum as SQLEnum, JSON
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, relationship
    from sqlalchemy.sql import func
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

# MongoDB (opcional - futuro)
try:
    from pymongo import MongoClient
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False


Base = declarative_base() if SQLALCHEMY_AVAILABLE else None


# ========== MODELOS SQL ==========
if SQLALCHEMY_AVAILABLE:
    
    # ----- USUÁRIO -----
    class Usuario(Base):
        """Modelo de usuário"""
        __tablename__ = 'usuarios'
        
        id = Column(Integer, primary_key=True)
        telegram_id = Column(String(50), unique=True, nullable=True, index=True)
        whatsapp_id = Column(String(50), unique=True, nullable=True, index=True)
        nome = Column(String(100))
        email = Column(String(100))
        telefone = Column(String(20))
        cpf = Column(String(14))
        criado_em = Column(DateTime, default=datetime.utcnow)
        atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        ativo = Column(Boolean, default=True)
        configuracoes = Column(JSON, default={})  # Preferências do usuário
        
        # Relacionamentos
        transacoes = relationship("Transacao", back_populates="usuario", cascade="all, delete-orphan")
        tarefas = relationship("Tarefa", back_populates="usuario", cascade="all, delete-orphan")
        eventos = relationship("Evento", back_populates="usuario", cascade="all, delete-orphan")
        boletos = relationship("Boleto", back_populates="usuario", cascade="all, delete-orphan")
        lembretes = relationship("Lembrete", back_populates="usuario", cascade="all, delete-orphan")
        comprovantes = relationship("Comprovante", back_populates="usuario", cascade="all, delete-orphan")
        cadastros = relationship("Cadastro", back_populates="usuario", cascade="all, delete-orphan")
        categorias = relationship("Categoria", back_populates="usuario", cascade="all, delete-orphan")
        contas_bancarias = relationship("ContaBancaria", back_populates="usuario", cascade="all, delete-orphan")
        metas = relationship("Meta", back_populates="usuario", cascade="all, delete-orphan")
    
    
    class Transacao(Base):
        """Modelo de transação financeira"""
        __tablename__ = 'transacoes'
        
        id = Column(Integer, primary_key=True)
        usuario_id = Column(Integer, ForeignKey('usuarios.id'), index=True)
        tipo = Column(String(20), index=True)  # entrada, saida
        valor = Column(Float)
        descricao = Column(String(200))
        categoria_id = Column(Integer, ForeignKey('categorias.id'), nullable=True)
        categoria_nome = Column(String(50))  # Para retrocompatibilidade
        conta_id = Column(Integer, ForeignKey('contas_bancarias.id'), nullable=True)
        data = Column(DateTime, index=True)
        data_competencia = Column(Date)  # Mês de referência
        recorrente = Column(Boolean, default=False)
        parcela_atual = Column(Integer, nullable=True)
        total_parcelas = Column(Integer, nullable=True)
        comprovante_id = Column(Integer, ForeignKey('comprovantes.id'), nullable=True)
        observacao = Column(Text)
        criado_em = Column(DateTime, default=datetime.utcnow)
        atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        usuario = relationship("Usuario", back_populates="transacoes")
        categoria = relationship("Categoria")
        conta = relationship("ContaBancaria")
        comprovante = relationship("Comprovante")
        
        __table_args__ = (
            Index('idx_transacao_usuario_data', 'usuario_id', 'data'),
            Index('idx_transacao_categoria', 'usuario_id', 'categoria_nome'),
        )
    
    
    # ----- CATEGORIA -----
    class Categoria(Base):
        """Categorias de transações"""
        __tablename__ = 'categorias'
        
        id = Column(Integer, primary_key=True)
        usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=True)  # NULL = categoria global
        nome = Column(String(50))
        tipo = Column(String(20))  # entrada, saida, ambos
        icone = Column(String(10))  # Emoji
        cor = Column(String(7))  # #RRGGBB
        ativo = Column(Boolean, default=True)
        ordem = Column(Integer, default=0)
        criado_em = Column(DateTime, default=datetime.utcnow)
        
        usuario = relationship("Usuario", back_populates="categorias")
    
    
    # ----- CONTA BANCÁRIA -----
    class ContaBancaria(Base):
        """Contas bancárias do usuário"""
        __tablename__ = 'contas_bancarias'
        
        id = Column(Integer, primary_key=True)
        usuario_id = Column(Integer, ForeignKey('usuarios.id'), index=True)
        nome = Column(String(100))  # "Nubank", "BB Conta Corrente"
        banco_codigo = Column(String(10))  # 001, 341, etc
        banco_nome = Column(String(50))
        agencia = Column(String(10))
        conta = Column(String(20))
        tipo = Column(String(30))  # corrente, poupanca, cartao_credito, investimento
        saldo_inicial = Column(Float, default=0)
        saldo_atual = Column(Float, default=0)
        limite = Column(Float, nullable=True)  # Para cartão de crédito
        dia_fechamento = Column(Integer, nullable=True)  # Para cartão
        dia_vencimento = Column(Integer, nullable=True)  # Para cartão
        cor = Column(String(7))
        ativo = Column(Boolean, default=True)
        principal = Column(Boolean, default=False)
        criado_em = Column(DateTime, default=datetime.utcnow)
        atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        usuario = relationship("Usuario", back_populates="contas_bancarias")
    
    
    class Tarefa(Base):
        """Modelo de tarefa"""
        __tablename__ = 'tarefas'
        
        id = Column(Integer, primary_key=True)
        usuario_id = Column(Integer, ForeignKey('usuarios.id'), index=True)
        titulo = Column(String(200))
        descricao = Column(Text)
        prioridade = Column(String(20), default='media')  # baixa, media, alta, urgente
        status = Column(String(20), default='pendente', index=True)  # pendente, em_andamento, concluida, cancelada
        data_limite = Column(DateTime, nullable=True, index=True)
        data_lembrete = Column(DateTime, nullable=True)
        concluido_em = Column(DateTime, nullable=True)
        categoria = Column(String(50))
        tags = Column(JSON, default=[])  # Lista de tags
        recorrente = Column(Boolean, default=False)
        recorrencia = Column(String(20))  # diaria, semanal, mensal, anual
        criado_em = Column(DateTime, default=datetime.utcnow)
        atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        usuario = relationship("Usuario", back_populates="tarefas")
        
        __table_args__ = (
            Index('idx_tarefa_usuario_status', 'usuario_id', 'status'),
        )
    
    
    class Evento(Base):
        """Modelo de evento/compromisso"""
        __tablename__ = 'eventos'
        
        id = Column(Integer, primary_key=True)
        usuario_id = Column(Integer, ForeignKey('usuarios.id'), index=True)
        titulo = Column(String(200))
        descricao = Column(Text)
        local = Column(String(200))
        data = Column(DateTime, index=True)
        data_fim = Column(DateTime, nullable=True)
        hora = Column(String(10))
        hora_fim = Column(String(10))
        duracao_min = Column(Integer, default=60)
        dia_todo = Column(Boolean, default=False)
        lembrete_min = Column(Integer, default=30)
        lembrete_enviado = Column(Boolean, default=False)
        recorrente = Column(Boolean, default=False)
        recorrencia = Column(String(20))  # diaria, semanal, mensal, anual
        google_event_id = Column(String(100))  # ID do Google Calendar
        categoria = Column(String(50))
        cor = Column(String(7))
        participantes = Column(JSON, default=[])  # Lista de emails/telefones
        criado_em = Column(DateTime, default=datetime.utcnow)
        atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        usuario = relationship("Usuario", back_populates="eventos")
        
        __table_args__ = (
            Index('idx_evento_usuario_data', 'usuario_id', 'data'),
        )
    
    
    # ----- LEMBRETE -----
    class Lembrete(Base):
        """Lembretes e notificações"""
        __tablename__ = 'lembretes'
        
        id = Column(Integer, primary_key=True)
        usuario_id = Column(Integer, ForeignKey('usuarios.id'), index=True)
        titulo = Column(String(200))
        mensagem = Column(Text)
        data_hora = Column(DateTime, index=True)
        enviado = Column(Boolean, default=False)
        tipo = Column(String(30))  # unico, diario, semanal, mensal
        dias_semana = Column(JSON, default=[])  # [0,1,2,3,4,5,6] = dom a sab
        ativo = Column(Boolean, default=True)
        canal = Column(String(20))  # whatsapp, telegram, email
        referencia_tipo = Column(String(30))  # boleto, evento, tarefa
        referencia_id = Column(Integer)
        criado_em = Column(DateTime, default=datetime.utcnow)
        
        usuario = relationship("Usuario", back_populates="lembretes")
    
    
    class Produto(Base):
        """Modelo de produto"""
        __tablename__ = 'produtos'
        
        id = Column(Integer, primary_key=True)
        nome = Column(String(100), index=True)
        codigo = Column(String(50), index=True)
        codigo_barras = Column(String(50))
        descricao = Column(Text)
        preco_custo = Column(Float, default=0)
        preco = Column(Float)
        estoque = Column(Integer, default=0)
        estoque_minimo = Column(Integer, default=5)
        unidade = Column(String(10), default='un')  # un, kg, l, m
        categoria = Column(String(50))
        fornecedor = Column(String(100))
        localizacao = Column(String(50))  # Localização no estoque
        ativo = Column(Boolean, default=True)
        imagem_url = Column(String(500))
        criado_em = Column(DateTime, default=datetime.utcnow)
        atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        itens_venda = relationship("ItemVenda", back_populates="produto")
    
    
    class Venda(Base):
        """Modelo de venda"""
        __tablename__ = 'vendas'
        
        id = Column(Integer, primary_key=True)
        numero = Column(String(20), unique=True)  # Número sequencial
        valor_total = Column(Float)
        valor_desconto = Column(Float, default=0)
        valor_final = Column(Float)
        cliente = Column(String(100))
        cliente_id = Column(Integer, ForeignKey('cadastros.id'), nullable=True)
        forma_pagamento = Column(String(50))  # dinheiro, pix, cartao_credito, cartao_debito
        parcelas = Column(Integer, default=1)
        status = Column(String(20), default='concluida', index=True)  # concluida, pendente, cancelada
        observacao = Column(Text)
        data = Column(DateTime, default=datetime.utcnow, index=True)
        criado_em = Column(DateTime, default=datetime.utcnow)
        
        itens = relationship("ItemVenda", back_populates="venda", cascade="all, delete-orphan")
        cliente_rel = relationship("Cadastro")
    
    
    class ItemVenda(Base):
        """Itens de uma venda"""
        __tablename__ = 'itens_venda'
        
        id = Column(Integer, primary_key=True)
        venda_id = Column(Integer, ForeignKey('vendas.id'), index=True)
        produto_id = Column(Integer, ForeignKey('produtos.id'))
        quantidade = Column(Float)
        preco_unitario = Column(Float)
        desconto = Column(Float, default=0)
        subtotal = Column(Float)
        
        venda = relationship("Venda", back_populates="itens")
        produto = relationship("Produto", back_populates="itens_venda")
    
    
    class Boleto(Base):
        """Modelo de boleto/conta a pagar"""
        __tablename__ = 'boletos'
        
        id = Column(Integer, primary_key=True)
        usuario_id = Column(Integer, ForeignKey('usuarios.id'), index=True)
        tipo = Column(String(30), default='boleto')  # boleto, pix, fatura, mensalidade
        valor = Column(Float)
        codigo_barras = Column(String(100))
        linha_digitavel = Column(String(100))
        pix_copia_cola = Column(Text)  # Código PIX copia e cola
        pix_chave = Column(String(100))
        vencimento = Column(Date, index=True)
        beneficiario = Column(String(100))
        beneficiario_cnpj = Column(String(20))
        pagador = Column(String(100))
        descricao = Column(Text)
        categoria_id = Column(Integer, ForeignKey('categorias.id'), nullable=True)
        categoria_nome = Column(String(50))
        pago = Column(Boolean, default=False, index=True)
        data_pagamento = Column(DateTime)
        valor_pago = Column(Float)
        comprovante_id = Column(Integer, ForeignKey('comprovantes.id'), nullable=True)
        recorrente = Column(Boolean, default=False)
        recorrencia = Column(String(20))  # mensal, anual
        lembrete_dias = Column(Integer, default=3)  # Dias antes do vencimento
        observacao = Column(Text)
        arquivo_original = Column(String(500))  # Path do PDF/imagem original
        criado_em = Column(DateTime, default=datetime.utcnow)
        atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        usuario = relationship("Usuario", back_populates="boletos")
        categoria = relationship("Categoria")
        comprovante = relationship("Comprovante")
        
        __table_args__ = (
            Index('idx_boleto_usuario_vencimento', 'usuario_id', 'vencimento'),
            Index('idx_boleto_pendente', 'usuario_id', 'pago', 'vencimento'),
        )
    
    
    # ----- COMPROVANTE -----
    class Comprovante(Base):
        """Comprovantes de pagamento"""
        __tablename__ = 'comprovantes'
        
        id = Column(Integer, primary_key=True)
        usuario_id = Column(Integer, ForeignKey('usuarios.id'), index=True)
        tipo = Column(String(30))  # pix, ted, doc, boleto, debito, credito
        valor = Column(Float)
        data_pagamento = Column(DateTime, index=True)
        origem = Column(String(100))  # Conta/banco de origem
        destino = Column(String(100))  # Favorecido
        destino_documento = Column(String(20))  # CPF/CNPJ do favorecido
        identificador = Column(String(100))  # ID da transação, autenticação
        descricao = Column(Text)
        categoria_nome = Column(String(50))
        banco_codigo = Column(String(10))
        banco_nome = Column(String(50))
        arquivo_path = Column(String(500))  # Caminho do arquivo original
        arquivo_tipo = Column(String(10))  # pdf, jpg, png
        dados_extraidos = Column(JSON)  # Dados brutos extraídos
        validado = Column(Boolean, default=False)
        criado_em = Column(DateTime, default=datetime.utcnow)
        
        usuario = relationship("Usuario", back_populates="comprovantes")
    
    
    # ----- CADASTRO (Contatos/Clientes/Fornecedores) -----
    class Cadastro(Base):
        """Cadastro de pessoas/empresas"""
        __tablename__ = 'cadastros'
        
        id = Column(Integer, primary_key=True)
        usuario_id = Column(Integer, ForeignKey('usuarios.id'), index=True)
        tipo = Column(String(20))  # pessoa, empresa
        papel = Column(String(30))  # cliente, fornecedor, contato, funcionario
        nome = Column(String(100), index=True)
        nome_fantasia = Column(String(100))
        documento = Column(String(20), index=True)  # CPF ou CNPJ
        email = Column(String(100))
        telefone = Column(String(20))
        telefone2 = Column(String(20))
        whatsapp = Column(String(20))
        endereco = Column(String(200))
        numero = Column(String(10))
        complemento = Column(String(50))
        bairro = Column(String(50))
        cidade = Column(String(50))
        estado = Column(String(2))
        cep = Column(String(10))
        observacao = Column(Text)
        data_nascimento = Column(Date)
        ativo = Column(Boolean, default=True)
        tags = Column(JSON, default=[])
        dados_extras = Column(JSON, default={})  # Campos customizados
        criado_em = Column(DateTime, default=datetime.utcnow)
        atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        usuario = relationship("Usuario", back_populates="cadastros")
    
    
    # ----- META FINANCEIRA -----
    class Meta(Base):
        """Metas financeiras"""
        __tablename__ = 'metas'
        
        id = Column(Integer, primary_key=True)
        usuario_id = Column(Integer, ForeignKey('usuarios.id'), index=True)
        titulo = Column(String(100))
        descricao = Column(Text)
        tipo = Column(String(30))  # economia, limite_gasto, receita
        categoria_nome = Column(String(50))  # Se for limite por categoria
        valor_meta = Column(Float)
        valor_atual = Column(Float, default=0)
        data_inicio = Column(Date)
        data_fim = Column(Date)
        periodo = Column(String(20))  # mensal, anual, unico
        ativo = Column(Boolean, default=True)
        concluida = Column(Boolean, default=False)
        criado_em = Column(DateTime, default=datetime.utcnow)
        
        usuario = relationship("Usuario", back_populates="metas")
    
    
    # ----- EXTRATO IMPORTADO -----
    class ExtratoImportado(Base):
        """Extratos bancários importados"""
        __tablename__ = 'extratos_importados'
        
        id = Column(Integer, primary_key=True)
        usuario_id = Column(Integer, ForeignKey('usuarios.id'), index=True)
        conta_id = Column(Integer, ForeignKey('contas_bancarias.id'))
        arquivo_nome = Column(String(200))
        arquivo_tipo = Column(String(10))  # ofx, pdf, csv
        data_importacao = Column(DateTime, default=datetime.utcnow)
        data_inicio = Column(Date)
        data_fim = Column(Date)
        saldo_inicial = Column(Float)
        saldo_final = Column(Float)
        total_transacoes = Column(Integer)
        transacoes_importadas = Column(Integer)
        status = Column(String(20))  # processando, concluido, erro
        erro_mensagem = Column(Text)
        
        conta = relationship("ContaBancaria")
    
    
    # ----- DOCUMENTO FISCAL (DAS, GPS, DARF, etc) -----
    class DocumentoFiscal(Base):
        """Documentos fiscais e impostos"""
        __tablename__ = 'documentos_fiscais'
        
        id = Column(Integer, primary_key=True)
        usuario_id = Column(Integer, ForeignKey('usuarios.id'), index=True)
        tipo = Column(String(30), index=True)  # das, gps, darf, fgts, grf
        competencia = Column(Date)  # Mês/ano de competência
        vencimento = Column(Date, index=True)
        valor_principal = Column(Float)
        valor_multa = Column(Float, default=0)
        valor_juros = Column(Float, default=0)
        valor_total = Column(Float)
        codigo_receita = Column(String(20))
        numero_documento = Column(String(50))
        codigo_barras = Column(String(100))
        linha_digitavel = Column(String(100))
        cnpj = Column(String(20))
        razao_social = Column(String(100))
        pago = Column(Boolean, default=False)
        data_pagamento = Column(DateTime)
        comprovante_id = Column(Integer, ForeignKey('comprovantes.id'), nullable=True)
        arquivo_original = Column(String(500))
        dados_extraidos = Column(JSON)
        criado_em = Column(DateTime, default=datetime.utcnow)
        
        comprovante = relationship("Comprovante")
        
        __table_args__ = (
            Index('idx_docfiscal_tipo_venc', 'usuario_id', 'tipo', 'vencimento'),
        )
    
    
    # ----- GATILHO/AUTOMAÇÃO -----
    class Gatilho(Base):
        """Gatilhos de automação"""
        __tablename__ = 'gatilhos'
        
        id = Column(Integer, primary_key=True)
        usuario_id = Column(Integer, ForeignKey('usuarios.id'), index=True)
        nome = Column(String(100))
        descricao = Column(Text)
        tipo = Column(String(30))  # horario, evento, condicao
        condicao = Column(JSON)  # Condições para disparo
        acao = Column(JSON)  # Ações a executar
        ativo = Column(Boolean, default=True)
        ultima_execucao = Column(DateTime)
        proxima_execucao = Column(DateTime)
        total_execucoes = Column(Integer, default=0)
        criado_em = Column(DateTime, default=datetime.utcnow)
    
    
    # ----- CONTEXTO IA -----
    class ContextoIA(Base):
        """Contextos e histórico de conversas com IA"""
        __tablename__ = 'contextos_ia'
        
        id = Column(Integer, primary_key=True)
        usuario_id = Column(Integer, ForeignKey('usuarios.id'), index=True)
        sessao_id = Column(String(50), index=True)
        mensagem = Column(Text)
        resposta = Column(Text)
        intencao = Column(String(50))  # Intenção detectada
        entidades = Column(JSON)  # Entidades extraídas
        contexto = Column(JSON)  # Estado da conversa
        modelo_usado = Column(String(30))  # gemini, groq, etc
        tokens_entrada = Column(Integer)
        tokens_saida = Column(Integer)
        tempo_resposta_ms = Column(Integer)
        criado_em = Column(DateTime, default=datetime.utcnow)
        
        __table_args__ = (
            Index('idx_contexto_usuario_sessao', 'usuario_id', 'sessao_id'),
        )


class DatabaseManager:
    """Gerenciador principal de banco de dados"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv('DATABASE_URL', 'sqlite:///data/assistente.db')
        self.engine = None
        self.Session = None
        self.mongo_client = None
        self.mongo_db = None
        
        self._setup_database()
    
    def _setup_database(self):
        """Configura conexão com banco de dados"""
        if self.database_url.startswith('mongodb'):
            self._setup_mongodb()
        else:
            self._setup_sql()
    
    def _setup_sql(self):
        """Configura banco SQL (SQLite/PostgreSQL)"""
        if not SQLALCHEMY_AVAILABLE:
            print("⚠️ SQLAlchemy não instalado. Use: pip install sqlalchemy")
            return
        
        # Cria diretório se for SQLite
        if 'sqlite' in self.database_url:
            db_path = self.database_url.replace('sqlite:///', '')
            os.makedirs(os.path.dirname(db_path) or '.', exist_ok=True)
        
        self.engine = create_engine(self.database_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
        
        # Cria tabelas
        Base.metadata.create_all(self.engine)
        print(f"✅ Banco de dados configurado: {self.database_url}")
    
    def _setup_mongodb(self):
        """Configura MongoDB"""
        if not MONGODB_AVAILABLE:
            print("⚠️ PyMongo não instalado. Use: pip install pymongo")
            return
        
        self.mongo_client = MongoClient(self.database_url)
        self.mongo_db = self.mongo_client.get_database()
        print(f"✅ MongoDB configurado")
    
    @contextmanager
    def get_session(self):
        """Context manager para sessão do banco"""
        if not self.Session:
            raise Exception("Banco de dados não configurado")
        
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    # ========== OPERAÇÕES CRUD ==========
    
    # ----- USUÁRIOS -----
    def criar_usuario(self, telegram_id: str = None, whatsapp_id: str = None, 
                      nome: str = "", email: str = "") -> Optional[int]:
        """Cria um novo usuário"""
        with self.get_session() as session:
            usuario = Usuario(
                telegram_id=telegram_id,
                whatsapp_id=whatsapp_id,
                nome=nome,
                email=email
            )
            session.add(usuario)
            session.flush()
            return usuario.id
    
    def buscar_usuario(self, telegram_id: str = None, whatsapp_id: str = None) -> Optional[Dict]:
        """Busca usuário por ID do Telegram ou WhatsApp"""
        with self.get_session() as session:
            query = session.query(Usuario)
            
            if telegram_id:
                query = query.filter(Usuario.telegram_id == telegram_id)
            elif whatsapp_id:
                query = query.filter(Usuario.whatsapp_id == whatsapp_id)
            else:
                return None
            
            usuario = query.first()
            if usuario:
                return {
                    'id': usuario.id,
                    'telegram_id': usuario.telegram_id,
                    'whatsapp_id': usuario.whatsapp_id,
                    'nome': usuario.nome,
                    'email': usuario.email,
                    'criado_em': usuario.criado_em.isoformat() if usuario.criado_em else None
                }
            return None
    
    def get_ou_criar_usuario(self, telegram_id: str = None, whatsapp_id: str = None, 
                              nome: str = "") -> int:
        """Busca ou cria usuário"""
        usuario = self.buscar_usuario(telegram_id=telegram_id, whatsapp_id=whatsapp_id)
        if usuario:
            return usuario['id']
        return self.criar_usuario(telegram_id=telegram_id, whatsapp_id=whatsapp_id, nome=nome)
    
    # ----- TRANSAÇÕES -----
    def adicionar_transacao(self, usuario_id: int, tipo: str, valor: float,
                            descricao: str, categoria: str = "outros") -> int:
        """Adiciona uma transação financeira"""
        with self.get_session() as session:
            transacao = Transacao(
                usuario_id=usuario_id,
                tipo=tipo,
                valor=valor,
                descricao=descricao,
                categoria=categoria,
                data=datetime.now()
            )
            session.add(transacao)
            session.flush()
            return transacao.id
    
    def listar_transacoes(self, usuario_id: int, limite: int = 50) -> List[Dict]:
        """Lista transações do usuário"""
        with self.get_session() as session:
            transacoes = session.query(Transacao)\
                .filter(Transacao.usuario_id == usuario_id)\
                .order_by(Transacao.data.desc())\
                .limit(limite)\
                .all()
            
            return [{
                'id': t.id,
                'tipo': t.tipo,
                'valor': t.valor,
                'descricao': t.descricao,
                'categoria': t.categoria,
                'data': t.data.isoformat() if t.data else None
            } for t in transacoes]
    
    def saldo_usuario(self, usuario_id: int) -> Dict:
        """Calcula saldo do usuário"""
        with self.get_session() as session:
            from sqlalchemy import func
            
            entradas = session.query(func.sum(Transacao.valor))\
                .filter(Transacao.usuario_id == usuario_id, Transacao.tipo == 'entrada')\
                .scalar() or 0
            
            saidas = session.query(func.sum(Transacao.valor))\
                .filter(Transacao.usuario_id == usuario_id, Transacao.tipo == 'saida')\
                .scalar() or 0
            
            return {
                'entradas': float(entradas),
                'saidas': float(saidas),
                'saldo': float(entradas - saidas)
            }
    
    # ----- TAREFAS -----
    def adicionar_tarefa(self, usuario_id: int, titulo: str, descricao: str = "",
                         prioridade: str = "media") -> int:
        """Adiciona uma tarefa"""
        with self.get_session() as session:
            tarefa = Tarefa(
                usuario_id=usuario_id,
                titulo=titulo,
                descricao=descricao,
                prioridade=prioridade
            )
            session.add(tarefa)
            session.flush()
            return tarefa.id
    
    def listar_tarefas(self, usuario_id: int, status: str = None) -> List[Dict]:
        """Lista tarefas do usuário"""
        with self.get_session() as session:
            query = session.query(Tarefa).filter(Tarefa.usuario_id == usuario_id)
            
            if status:
                query = query.filter(Tarefa.status == status)
            
            tarefas = query.order_by(Tarefa.criado_em.desc()).all()
            
            return [{
                'id': t.id,
                'titulo': t.titulo,
                'descricao': t.descricao,
                'prioridade': t.prioridade,
                'status': t.status,
                'data_limite': t.data_limite.isoformat() if t.data_limite else None,
                'criado_em': t.criado_em.isoformat() if t.criado_em else None
            } for t in tarefas]
    
    def concluir_tarefa(self, tarefa_id: int) -> bool:
        """Marca tarefa como concluída"""
        with self.get_session() as session:
            tarefa = session.query(Tarefa).get(tarefa_id)
            if tarefa:
                tarefa.status = 'concluida'
                tarefa.concluido_em = datetime.now()
                return True
            return False
    
    # ----- EVENTOS -----
    def adicionar_evento(self, usuario_id: int, titulo: str, data: datetime,
                         descricao: str = "", hora: str = "") -> int:
        """Adiciona um evento"""
        with self.get_session() as session:
            evento = Evento(
                usuario_id=usuario_id,
                titulo=titulo,
                descricao=descricao,
                data=data,
                hora=hora
            )
            session.add(evento)
            session.flush()
            return evento.id
    
    def listar_eventos(self, usuario_id: int, a_partir_de: datetime = None) -> List[Dict]:
        """Lista eventos do usuário"""
        with self.get_session() as session:
            query = session.query(Evento).filter(Evento.usuario_id == usuario_id)
            
            if a_partir_de:
                query = query.filter(Evento.data >= a_partir_de)
            
            eventos = query.order_by(Evento.data).all()
            
            return [{
                'id': e.id,
                'titulo': e.titulo,
                'descricao': e.descricao,
                'data': e.data.isoformat() if e.data else None,
                'hora': e.hora,
                'duracao_min': e.duracao_min
            } for e in eventos]
    
    # ----- PRODUTOS -----
    def adicionar_produto(self, nome: str, preco: float, estoque: int = 0,
                          codigo: str = "", categoria: str = "geral") -> int:
        """Adiciona um produto"""
        with self.get_session() as session:
            produto = Produto(
                nome=nome,
                codigo=codigo,
                preco=preco,
                estoque=estoque,
                categoria=categoria
            )
            session.add(produto)
            session.flush()
            return produto.id
    
    def atualizar_estoque(self, produto_id: int, quantidade: int, operacao: str = "subtrair") -> bool:
        """Atualiza estoque de produto"""
        with self.get_session() as session:
            produto = session.query(Produto).get(produto_id)
            if produto:
                if operacao == "subtrair":
                    produto.estoque = max(0, produto.estoque - quantidade)
                else:
                    produto.estoque += quantidade
                return True
            return False
    
    def listar_produtos(self, estoque_baixo: bool = False) -> List[Dict]:
        """Lista produtos"""
        with self.get_session() as session:
            query = session.query(Produto)
            
            if estoque_baixo:
                query = query.filter(Produto.estoque <= Produto.estoque_minimo)
            
            produtos = query.all()
            
            return [{
                'id': p.id,
                'nome': p.nome,
                'codigo': p.codigo,
                'preco': p.preco,
                'estoque': p.estoque,
                'estoque_minimo': p.estoque_minimo,
                'categoria': p.categoria
            } for p in produtos]
    
    # ----- VENDAS -----
    def registrar_venda(self, valor_total: float, cliente: str = "",
                        forma_pagamento: str = "dinheiro") -> int:
        """Registra uma venda"""
        with self.get_session() as session:
            venda = Venda(
                valor_total=valor_total,
                cliente=cliente,
                forma_pagamento=forma_pagamento
            )
            session.add(venda)
            session.flush()
            return venda.id
    
    def relatorio_vendas(self, data_inicio: datetime = None, data_fim: datetime = None) -> Dict:
        """Gera relatório de vendas"""
        with self.get_session() as session:
            from sqlalchemy import func
            
            query = session.query(Venda)
            
            if data_inicio:
                query = query.filter(Venda.data >= data_inicio)
            if data_fim:
                query = query.filter(Venda.data <= data_fim)
            
            vendas = query.all()
            total = sum(v.valor_total for v in vendas)
            
            return {
                'quantidade': len(vendas),
                'total': total,
                'media': total / len(vendas) if vendas else 0,
                'vendas': [{
                    'id': v.id,
                    'valor': v.valor_total,
                    'cliente': v.cliente,
                    'data': v.data.isoformat() if v.data else None
                } for v in vendas[-10:]]  # Últimas 10
            }
    
    # ----- BOLETOS -----
    def adicionar_boleto(self, usuario_id: int, valor: float, vencimento: datetime,
                         beneficiario: str, codigo_barras: str = "", **kwargs) -> int:
        """Adiciona um boleto"""
        with self.get_session() as session:
            boleto = Boleto(
                usuario_id=usuario_id,
                valor=valor,
                vencimento=vencimento,
                beneficiario=beneficiario,
                codigo_barras=codigo_barras,
                linha_digitavel=kwargs.get('linha_digitavel', ''),
                pix_copia_cola=kwargs.get('pix_copia_cola', ''),
                pix_chave=kwargs.get('pix_chave', ''),
                tipo=kwargs.get('tipo', 'boleto'),
                descricao=kwargs.get('descricao', ''),
                categoria_nome=kwargs.get('categoria', ''),
                recorrente=kwargs.get('recorrente', False)
            )
            session.add(boleto)
            session.flush()
            return boleto.id
    
    def boletos_pendentes(self, usuario_id: int, dias_vencer: int = None) -> List[Dict]:
        """Lista boletos pendentes"""
        with self.get_session() as session:
            query = session.query(Boleto)\
                .filter(Boleto.usuario_id == usuario_id, Boleto.pago == False)
            
            if dias_vencer:
                data_limite = datetime.now() + timedelta(days=dias_vencer)
                query = query.filter(Boleto.vencimento <= data_limite)
            
            boletos = query.order_by(Boleto.vencimento).all()
            
            return [{
                'id': b.id,
                'tipo': b.tipo,
                'valor': b.valor,
                'vencimento': b.vencimento.isoformat() if b.vencimento else None,
                'beneficiario': b.beneficiario,
                'codigo_barras': b.codigo_barras,
                'linha_digitavel': b.linha_digitavel,
                'pix_copia_cola': b.pix_copia_cola,
                'categoria': b.categoria_nome,
                'descricao': b.descricao
            } for b in boletos]
    
    def marcar_boleto_pago(self, boleto_id: int, valor_pago: float = None, 
                          comprovante_id: int = None) -> bool:
        """Marca boleto como pago"""
        with self.get_session() as session:
            boleto = session.query(Boleto).get(boleto_id)
            if boleto:
                boleto.pago = True
                boleto.data_pagamento = datetime.now()
                boleto.valor_pago = valor_pago or boleto.valor
                if comprovante_id:
                    boleto.comprovante_id = comprovante_id
                return True
            return False
    
    # ----- COMPROVANTES -----
    def adicionar_comprovante(self, usuario_id: int, tipo: str, valor: float,
                              destino: str, **kwargs) -> int:
        """Adiciona um comprovante"""
        with self.get_session() as session:
            comprovante = Comprovante(
                usuario_id=usuario_id,
                tipo=tipo,
                valor=valor,
                destino=destino,
                data_pagamento=kwargs.get('data_pagamento', datetime.now()),
                origem=kwargs.get('origem', ''),
                destino_documento=kwargs.get('destino_documento', ''),
                identificador=kwargs.get('identificador', ''),
                descricao=kwargs.get('descricao', ''),
                categoria_nome=kwargs.get('categoria', ''),
                banco_codigo=kwargs.get('banco_codigo', ''),
                banco_nome=kwargs.get('banco_nome', ''),
                arquivo_path=kwargs.get('arquivo_path', ''),
                arquivo_tipo=kwargs.get('arquivo_tipo', ''),
                dados_extraidos=kwargs.get('dados_extraidos', {})
            )
            session.add(comprovante)
            session.flush()
            return comprovante.id
    
    def listar_comprovantes(self, usuario_id: int, data_inicio: datetime = None,
                           data_fim: datetime = None, limite: int = 50) -> List[Dict]:
        """Lista comprovantes do usuário"""
        with self.get_session() as session:
            query = session.query(Comprovante).filter(Comprovante.usuario_id == usuario_id)
            
            if data_inicio:
                query = query.filter(Comprovante.data_pagamento >= data_inicio)
            if data_fim:
                query = query.filter(Comprovante.data_pagamento <= data_fim)
            
            comprovantes = query.order_by(Comprovante.data_pagamento.desc()).limit(limite).all()
            
            return [{
                'id': c.id,
                'tipo': c.tipo,
                'valor': c.valor,
                'data_pagamento': c.data_pagamento.isoformat() if c.data_pagamento else None,
                'destino': c.destino,
                'origem': c.origem,
                'identificador': c.identificador,
                'categoria': c.categoria_nome
            } for c in comprovantes]
    
    # ----- LEMBRETES -----
    def adicionar_lembrete(self, usuario_id: int, titulo: str, data_hora: datetime,
                           **kwargs) -> int:
        """Adiciona um lembrete"""
        with self.get_session() as session:
            lembrete = Lembrete(
                usuario_id=usuario_id,
                titulo=titulo,
                data_hora=data_hora,
                mensagem=kwargs.get('mensagem', ''),
                tipo=kwargs.get('tipo', 'unico'),
                canal=kwargs.get('canal', 'whatsapp'),
                referencia_tipo=kwargs.get('referencia_tipo'),
                referencia_id=kwargs.get('referencia_id')
            )
            session.add(lembrete)
            session.flush()
            return lembrete.id
    
    def lembretes_pendentes(self, usuario_id: int = None) -> List[Dict]:
        """Lista lembretes pendentes para envio"""
        with self.get_session() as session:
            query = session.query(Lembrete)\
                .filter(Lembrete.enviado == False, 
                       Lembrete.ativo == True,
                       Lembrete.data_hora <= datetime.now())
            
            if usuario_id:
                query = query.filter(Lembrete.usuario_id == usuario_id)
            
            lembretes = query.all()
            
            return [{
                'id': l.id,
                'usuario_id': l.usuario_id,
                'titulo': l.titulo,
                'mensagem': l.mensagem,
                'data_hora': l.data_hora.isoformat() if l.data_hora else None,
                'canal': l.canal
            } for l in lembretes]
    
    def marcar_lembrete_enviado(self, lembrete_id: int) -> bool:
        """Marca lembrete como enviado"""
        with self.get_session() as session:
            lembrete = session.query(Lembrete).get(lembrete_id)
            if lembrete:
                lembrete.enviado = True
                return True
            return False
    
    # ----- CADASTROS -----
    def adicionar_cadastro(self, usuario_id: int, nome: str, tipo: str = 'pessoa',
                           papel: str = 'contato', **kwargs) -> int:
        """Adiciona um cadastro (cliente/fornecedor/contato)"""
        with self.get_session() as session:
            cadastro = Cadastro(
                usuario_id=usuario_id,
                nome=nome,
                tipo=tipo,
                papel=papel,
                documento=kwargs.get('documento', ''),
                email=kwargs.get('email', ''),
                telefone=kwargs.get('telefone', ''),
                whatsapp=kwargs.get('whatsapp', ''),
                endereco=kwargs.get('endereco', ''),
                cidade=kwargs.get('cidade', ''),
                estado=kwargs.get('estado', ''),
                cep=kwargs.get('cep', ''),
                observacao=kwargs.get('observacao', '')
            )
            session.add(cadastro)
            session.flush()
            return cadastro.id
    
    def buscar_cadastro(self, usuario_id: int, termo: str) -> List[Dict]:
        """Busca cadastros por nome ou documento"""
        with self.get_session() as session:
            cadastros = session.query(Cadastro)\
                .filter(Cadastro.usuario_id == usuario_id)\
                .filter(
                    (Cadastro.nome.ilike(f'%{termo}%')) |
                    (Cadastro.documento.ilike(f'%{termo}%')) |
                    (Cadastro.telefone.ilike(f'%{termo}%'))
                ).all()
            
            return [{
                'id': c.id,
                'nome': c.nome,
                'tipo': c.tipo,
                'papel': c.papel,
                'documento': c.documento,
                'telefone': c.telefone,
                'email': c.email
            } for c in cadastros]
    
    # ----- DOCUMENTOS FISCAIS -----
    def adicionar_documento_fiscal(self, usuario_id: int, tipo: str, valor_total: float,
                                   vencimento: datetime, **kwargs) -> int:
        """Adiciona um documento fiscal (DAS, GPS, DARF, etc)"""
        with self.get_session() as session:
            doc = DocumentoFiscal(
                usuario_id=usuario_id,
                tipo=tipo,
                valor_total=valor_total,
                vencimento=vencimento,
                valor_principal=kwargs.get('valor_principal', valor_total),
                competencia=kwargs.get('competencia'),
                codigo_receita=kwargs.get('codigo_receita', ''),
                numero_documento=kwargs.get('numero_documento', ''),
                codigo_barras=kwargs.get('codigo_barras', ''),
                linha_digitavel=kwargs.get('linha_digitavel', ''),
                cnpj=kwargs.get('cnpj', ''),
                razao_social=kwargs.get('razao_social', ''),
                arquivo_original=kwargs.get('arquivo_original', ''),
                dados_extraidos=kwargs.get('dados_extraidos', {})
            )
            session.add(doc)
            session.flush()
            return doc.id
    
    def documentos_fiscais_pendentes(self, usuario_id: int, tipo: str = None) -> List[Dict]:
        """Lista documentos fiscais pendentes"""
        with self.get_session() as session:
            query = session.query(DocumentoFiscal)\
                .filter(DocumentoFiscal.usuario_id == usuario_id,
                       DocumentoFiscal.pago == False)
            
            if tipo:
                query = query.filter(DocumentoFiscal.tipo == tipo)
            
            docs = query.order_by(DocumentoFiscal.vencimento).all()
            
            return [{
                'id': d.id,
                'tipo': d.tipo,
                'valor_total': d.valor_total,
                'vencimento': d.vencimento.isoformat() if d.vencimento else None,
                'competencia': d.competencia.isoformat() if d.competencia else None,
                'codigo_barras': d.codigo_barras,
                'linha_digitavel': d.linha_digitavel,
                'cnpj': d.cnpj
            } for d in docs]
    
    # ----- CATEGORIAS -----
    def criar_categorias_padrao(self, usuario_id: int = None):
        """Cria categorias padrão do sistema"""
        categorias_padrao = [
            # Despesas
            ('alimentacao', 'saida', '🍽️', '#FF6B6B'),
            ('transporte', 'saida', '🚗', '#4ECDC4'),
            ('moradia', 'saida', '🏠', '#45B7D1'),
            ('saude', 'saida', '💊', '#96CEB4'),
            ('educacao', 'saida', '📚', '#FFEAA7'),
            ('lazer', 'saida', '🎮', '#DDA0DD'),
            ('vestuario', 'saida', '👕', '#98D8C8'),
            ('servicos', 'saida', '🔧', '#F7DC6F'),
            ('impostos', 'saida', '📋', '#BB8FCE'),
            ('outros_despesa', 'saida', '📦', '#85C1E9'),
            # Receitas
            ('salario', 'entrada', '💰', '#2ECC71'),
            ('freelance', 'entrada', '💻', '#3498DB'),
            ('vendas', 'entrada', '🛒', '#E74C3C'),
            ('investimentos', 'entrada', '📈', '#9B59B6'),
            ('outros_receita', 'entrada', '💵', '#1ABC9C'),
        ]
        
        with self.get_session() as session:
            for nome, tipo, icone, cor in categorias_padrao:
                existe = session.query(Categoria)\
                    .filter(Categoria.nome == nome,
                           Categoria.usuario_id == usuario_id).first()
                
                if not existe:
                    cat = Categoria(
                        usuario_id=usuario_id,
                        nome=nome,
                        tipo=tipo,
                        icone=icone,
                        cor=cor
                    )
                    session.add(cat)
    
    def listar_categorias(self, usuario_id: int = None, tipo: str = None) -> List[Dict]:
        """Lista categorias disponíveis"""
        with self.get_session() as session:
            query = session.query(Categoria).filter(
                (Categoria.usuario_id == usuario_id) | (Categoria.usuario_id == None)
            )
            
            if tipo:
                query = query.filter((Categoria.tipo == tipo) | (Categoria.tipo == 'ambos'))
            
            categorias = query.filter(Categoria.ativo == True)\
                .order_by(Categoria.ordem, Categoria.nome).all()
            
            return [{
                'id': c.id,
                'nome': c.nome,
                'tipo': c.tipo,
                'icone': c.icone,
                'cor': c.cor
            } for c in categorias]
    
    # ----- CONTAS BANCÁRIAS -----
    def adicionar_conta_bancaria(self, usuario_id: int, nome: str, tipo: str = 'corrente',
                                 **kwargs) -> int:
        """Adiciona uma conta bancária"""
        with self.get_session() as session:
            conta = ContaBancaria(
                usuario_id=usuario_id,
                nome=nome,
                tipo=tipo,
                banco_codigo=kwargs.get('banco_codigo', ''),
                banco_nome=kwargs.get('banco_nome', ''),
                agencia=kwargs.get('agencia', ''),
                conta=kwargs.get('conta', ''),
                saldo_inicial=kwargs.get('saldo_inicial', 0),
                saldo_atual=kwargs.get('saldo_atual', kwargs.get('saldo_inicial', 0)),
                limite=kwargs.get('limite'),
                cor=kwargs.get('cor', '#3498DB')
            )
            session.add(conta)
            session.flush()
            return conta.id
    
    def listar_contas(self, usuario_id: int) -> List[Dict]:
        """Lista contas bancárias do usuário"""
        with self.get_session() as session:
            contas = session.query(ContaBancaria)\
                .filter(ContaBancaria.usuario_id == usuario_id,
                       ContaBancaria.ativo == True).all()
            
            return [{
                'id': c.id,
                'nome': c.nome,
                'tipo': c.tipo,
                'banco_nome': c.banco_nome,
                'saldo_atual': c.saldo_atual,
                'limite': c.limite,
                'cor': c.cor
            } for c in contas]
    
    # ----- METAS -----
    def adicionar_meta(self, usuario_id: int, titulo: str, valor_meta: float,
                       tipo: str = 'economia', **kwargs) -> int:
        """Adiciona uma meta financeira"""
        with self.get_session() as session:
            meta = Meta(
                usuario_id=usuario_id,
                titulo=titulo,
                valor_meta=valor_meta,
                tipo=tipo,
                descricao=kwargs.get('descricao', ''),
                categoria_nome=kwargs.get('categoria', ''),
                data_inicio=kwargs.get('data_inicio', date.today()),
                data_fim=kwargs.get('data_fim'),
                periodo=kwargs.get('periodo', 'mensal')
            )
            session.add(meta)
            session.flush()
            return meta.id
    
    def atualizar_progresso_meta(self, meta_id: int, valor_atual: float) -> bool:
        """Atualiza progresso de uma meta"""
        with self.get_session() as session:
            meta = session.query(Meta).get(meta_id)
            if meta:
                meta.valor_atual = valor_atual
                if valor_atual >= meta.valor_meta:
                    meta.concluida = True
                return True
            return False
    
    # ----- RELATÓRIOS E ESTATÍSTICAS -----
    def resumo_financeiro(self, usuario_id: int, mes: int = None, ano: int = None) -> Dict:
        """Gera resumo financeiro do mês"""
        from sqlalchemy import extract
        
        if not mes:
            mes = datetime.now().month
        if not ano:
            ano = datetime.now().year
        
        with self.get_session() as session:
            # Transações do mês
            transacoes = session.query(Transacao)\
                .filter(Transacao.usuario_id == usuario_id,
                       extract('month', Transacao.data) == mes,
                       extract('year', Transacao.data) == ano).all()
            
            entradas = sum(t.valor for t in transacoes if t.tipo == 'entrada')
            saidas = sum(t.valor for t in transacoes if t.tipo == 'saida')
            
            # Gastos por categoria
            gastos_categoria = {}
            for t in transacoes:
                if t.tipo == 'saida':
                    cat = t.categoria_nome or 'outros'
                    gastos_categoria[cat] = gastos_categoria.get(cat, 0) + t.valor
            
            # Boletos pendentes
            boletos = session.query(Boleto)\
                .filter(Boleto.usuario_id == usuario_id,
                       Boleto.pago == False,
                       extract('month', Boleto.vencimento) == mes,
                       extract('year', Boleto.vencimento) == ano).all()
            
            total_boletos = sum(b.valor for b in boletos)
            
            return {
                'mes': mes,
                'ano': ano,
                'entradas': entradas,
                'saidas': saidas,
                'saldo': entradas - saidas,
                'gastos_por_categoria': gastos_categoria,
                'boletos_pendentes': len(boletos),
                'total_boletos': total_boletos,
                'total_transacoes': len(transacoes)
            }
    
    # ----- UTILITÁRIOS -----
    def executar_query(self, query: str, params: dict = None) -> List[Dict]:
        """Executa query SQL customizada (apenas SELECT)"""
        if not query.strip().upper().startswith('SELECT'):
            raise ValueError("Apenas queries SELECT são permitidas")
        
        with self.get_session() as session:
            result = session.execute(query, params or {})
            return [dict(row) for row in result]
    
    def backup_json(self, output_dir: str = 'data/backup') -> str:
        """Exporta dados para JSON (backup)"""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        backup_data = {}
        
        with self.get_session() as session:
            # Exporta cada tabela
            for table_name, model in [
                ('usuarios', Usuario),
                ('transacoes', Transacao),
                ('tarefas', Tarefa),
                ('eventos', Evento),
                ('boletos', Boleto),
                ('lembretes', Lembrete),
                ('comprovantes', Comprovante),
                ('cadastros', Cadastro),
                ('produtos', Produto),
                ('vendas', Venda),
                ('categorias', Categoria),
                ('metas', Meta),
                ('documentos_fiscais', DocumentoFiscal)
            ]:
                try:
                    items = session.query(model).all()
                    backup_data[table_name] = [
                        {c.name: getattr(item, c.name) for c in model.__table__.columns}
                        for item in items
                    ]
                except Exception as e:
                    backup_data[table_name] = []
        
        # Serializa datas
        def serialize(obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            return obj
        
        backup_file = os.path.join(output_dir, f'backup_{timestamp}.json')
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, default=serialize, ensure_ascii=False, indent=2)
        
        return backup_file


# Importação necessária para timedelta
from datetime import timedelta

# Singleton para uso global
_db_manager = None

def get_database() -> DatabaseManager:
    """Retorna instância singleton do DatabaseManager"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


# ========== SCRIPT DE MIGRAÇÃO JSON → SQLite ==========
def migrar_json_para_sqlite(data_dir: str = 'data'):
    """Migra dados dos arquivos JSON para SQLite"""
    print("🔄 Iniciando migração JSON → SQLite...")
    
    db = get_database()
    
    # Cria categorias padrão
    db.criar_categorias_padrao()
    print("✅ Categorias padrão criadas")
    
    # Migra boletos.json
    boletos_file = os.path.join(data_dir, 'boletos.json')
    if os.path.exists(boletos_file):
        try:
            with open(boletos_file, 'r', encoding='utf-8') as f:
                boletos = json.load(f)
            
            with db.get_session() as session:
                for b in boletos:
                    # Obtém ou cria usuário
                    usuario_id = db.get_ou_criar_usuario(whatsapp_id=b.get('usuario_id', 'default'))
                    
                    # Verifica se já existe
                    existe = session.query(Boleto).filter(
                        Boleto.codigo_barras == b.get('codigo_barras', ''),
                        Boleto.usuario_id == usuario_id
                    ).first()
                    
                    if not existe and b.get('codigo_barras'):
                        venc = b.get('vencimento')
                        if isinstance(venc, str):
                            try:
                                venc = datetime.fromisoformat(venc.replace('Z', '+00:00'))
                            except:
                                venc = datetime.now()
                        
                        boleto = Boleto(
                            usuario_id=usuario_id,
                            valor=float(b.get('valor', 0)),
                            vencimento=venc,
                            beneficiario=b.get('beneficiario', ''),
                            codigo_barras=b.get('codigo_barras', ''),
                            linha_digitavel=b.get('linha_digitavel', ''),
                            descricao=b.get('descricao', ''),
                            pago=b.get('pago', False)
                        )
                        session.add(boleto)
            
            print(f"✅ Migrados {len(boletos)} boletos")
        except Exception as e:
            print(f"⚠️ Erro ao migrar boletos: {e}")
    
    # Migra eventos.json
    eventos_file = os.path.join(data_dir, 'eventos.json')
    if os.path.exists(eventos_file):
        try:
            with open(eventos_file, 'r', encoding='utf-8') as f:
                eventos = json.load(f)
            
            with db.get_session() as session:
                for e in eventos:
                    usuario_id = db.get_ou_criar_usuario(whatsapp_id=e.get('usuario_id', 'default'))
                    
                    data = e.get('data')
                    if isinstance(data, str):
                        try:
                            data = datetime.fromisoformat(data.replace('Z', '+00:00'))
                        except:
                            data = datetime.now()
                    
                    evento = Evento(
                        usuario_id=usuario_id,
                        titulo=e.get('titulo', ''),
                        descricao=e.get('descricao', ''),
                        data=data,
                        hora=e.get('hora', ''),
                        local=e.get('local', ''),
                        google_event_id=e.get('google_event_id')
                    )
                    session.add(evento)
            
            print(f"✅ Migrados {len(eventos)} eventos")
        except Exception as e:
            print(f"⚠️ Erro ao migrar eventos: {e}")
    
    # Migra lembretes.json
    lembretes_file = os.path.join(data_dir, 'lembretes.json')
    if os.path.exists(lembretes_file):
        try:
            with open(lembretes_file, 'r', encoding='utf-8') as f:
                lembretes = json.load(f)
            
            with db.get_session() as session:
                for l in lembretes:
                    usuario_id = db.get_ou_criar_usuario(whatsapp_id=l.get('usuario_id', 'default'))
                    
                    data_hora = l.get('data_hora') or l.get('data')
                    if isinstance(data_hora, str):
                        try:
                            data_hora = datetime.fromisoformat(data_hora.replace('Z', '+00:00'))
                        except:
                            data_hora = datetime.now()
                    
                    lembrete = Lembrete(
                        usuario_id=usuario_id,
                        titulo=l.get('titulo', l.get('mensagem', '')),
                        mensagem=l.get('mensagem', ''),
                        data_hora=data_hora,
                        tipo=l.get('tipo', 'unico'),
                        enviado=l.get('enviado', False)
                    )
                    session.add(lembrete)
            
            print(f"✅ Migrados {len(lembretes)} lembretes")
        except Exception as e:
            print(f"⚠️ Erro ao migrar lembretes: {e}")
    
    # Migra gatilhos.json
    gatilhos_file = os.path.join(data_dir, 'gatilhos.json')
    if os.path.exists(gatilhos_file):
        try:
            with open(gatilhos_file, 'r', encoding='utf-8') as f:
                gatilhos = json.load(f)
            
            with db.get_session() as session:
                for g in gatilhos:
                    usuario_id = db.get_ou_criar_usuario(whatsapp_id=g.get('usuario_id', 'default'))
                    
                    gatilho = Gatilho(
                        usuario_id=usuario_id,
                        nome=g.get('nome', ''),
                        descricao=g.get('descricao', ''),
                        tipo=g.get('tipo', 'horario'),
                        condicao=g.get('condicao', {}),
                        acao=g.get('acao', {}),
                        ativo=g.get('ativo', True)
                    )
                    session.add(gatilho)
            
            print(f"✅ Migrados {len(gatilhos)} gatilhos")
        except Exception as e:
            print(f"⚠️ Erro ao migrar gatilhos: {e}")
    
    print("✅ Migração concluída!")
    print(f"📁 Banco de dados: data/assistente.db")
    return True


# Executa migração se chamado diretamente
if __name__ == '__main__':
    migrar_json_para_sqlite()
