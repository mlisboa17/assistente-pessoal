"""
🗄️ Database Manager
Gerenciador de banco de dados com suporte a SQLite, PostgreSQL e MongoDB
"""
import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from contextlib import contextmanager

# SQLAlchemy para SQL
try:
    from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, relationship
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

# MongoDB
try:
    from pymongo import MongoClient
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False


Base = declarative_base() if SQLALCHEMY_AVAILABLE else None


# ========== MODELOS SQL ==========
if SQLALCHEMY_AVAILABLE:
    
    class Usuario(Base):
        """Modelo de usuário"""
        __tablename__ = 'usuarios'
        
        id = Column(Integer, primary_key=True)
        telegram_id = Column(String(50), unique=True, nullable=True)
        whatsapp_id = Column(String(50), unique=True, nullable=True)
        nome = Column(String(100))
        email = Column(String(100))
        criado_em = Column(DateTime, default=datetime.utcnow)
        ativo = Column(Boolean, default=True)
        
        # Relacionamentos
        transacoes = relationship("Transacao", back_populates="usuario")
        tarefas = relationship("Tarefa", back_populates="usuario")
        eventos = relationship("Evento", back_populates="usuario")
    
    
    class Transacao(Base):
        """Modelo de transação financeira"""
        __tablename__ = 'transacoes'
        
        id = Column(Integer, primary_key=True)
        usuario_id = Column(Integer, ForeignKey('usuarios.id'))
        tipo = Column(String(20))  # entrada, saida
        valor = Column(Float)
        descricao = Column(String(200))
        categoria = Column(String(50))
        data = Column(DateTime)
        criado_em = Column(DateTime, default=datetime.utcnow)
        
        usuario = relationship("Usuario", back_populates="transacoes")
    
    
    class Tarefa(Base):
        """Modelo de tarefa"""
        __tablename__ = 'tarefas'
        
        id = Column(Integer, primary_key=True)
        usuario_id = Column(Integer, ForeignKey('usuarios.id'))
        titulo = Column(String(200))
        descricao = Column(Text)
        prioridade = Column(String(20), default='media')
        status = Column(String(20), default='pendente')
        data_limite = Column(DateTime, nullable=True)
        concluido_em = Column(DateTime, nullable=True)
        criado_em = Column(DateTime, default=datetime.utcnow)
        
        usuario = relationship("Usuario", back_populates="tarefas")
    
    
    class Evento(Base):
        """Modelo de evento/compromisso"""
        __tablename__ = 'eventos'
        
        id = Column(Integer, primary_key=True)
        usuario_id = Column(Integer, ForeignKey('usuarios.id'))
        titulo = Column(String(200))
        descricao = Column(Text)
        data = Column(DateTime)
        hora = Column(String(10))
        duracao_min = Column(Integer, default=60)
        lembrete_min = Column(Integer, default=30)
        criado_em = Column(DateTime, default=datetime.utcnow)
        
        usuario = relationship("Usuario", back_populates="eventos")
    
    
    class Produto(Base):
        """Modelo de produto"""
        __tablename__ = 'produtos'
        
        id = Column(Integer, primary_key=True)
        nome = Column(String(100))
        codigo = Column(String(50))
        preco = Column(Float)
        estoque = Column(Integer, default=0)
        estoque_minimo = Column(Integer, default=5)
        categoria = Column(String(50))
        criado_em = Column(DateTime, default=datetime.utcnow)
    
    
    class Venda(Base):
        """Modelo de venda"""
        __tablename__ = 'vendas'
        
        id = Column(Integer, primary_key=True)
        valor_total = Column(Float)
        cliente = Column(String(100))
        forma_pagamento = Column(String(50))
        status = Column(String(20), default='concluida')
        data = Column(DateTime, default=datetime.utcnow)
        criado_em = Column(DateTime, default=datetime.utcnow)
    
    
    class Boleto(Base):
        """Modelo de boleto"""
        __tablename__ = 'boletos'
        
        id = Column(Integer, primary_key=True)
        usuario_id = Column(Integer, ForeignKey('usuarios.id'))
        valor = Column(Float)
        codigo_barras = Column(String(100))
        linha_digitavel = Column(String(100))
        vencimento = Column(DateTime)
        beneficiario = Column(String(100))
        pagador = Column(String(100))
        descricao = Column(Text)
        pago = Column(Boolean, default=False)
        criado_em = Column(DateTime, default=datetime.utcnow)


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
                         beneficiario: str, codigo_barras: str = "") -> int:
        """Adiciona um boleto"""
        with self.get_session() as session:
            boleto = Boleto(
                usuario_id=usuario_id,
                valor=valor,
                vencimento=vencimento,
                beneficiario=beneficiario,
                codigo_barras=codigo_barras
            )
            session.add(boleto)
            session.flush()
            return boleto.id
    
    def boletos_pendentes(self, usuario_id: int) -> List[Dict]:
        """Lista boletos pendentes"""
        with self.get_session() as session:
            boletos = session.query(Boleto)\
                .filter(Boleto.usuario_id == usuario_id, Boleto.pago == False)\
                .order_by(Boleto.vencimento)\
                .all()
            
            return [{
                'id': b.id,
                'valor': b.valor,
                'vencimento': b.vencimento.isoformat() if b.vencimento else None,
                'beneficiario': b.beneficiario,
                'codigo_barras': b.codigo_barras
            } for b in boletos]


# Singleton para uso global
_db_manager = None

def get_database() -> DatabaseManager:
    """Retorna instância singleton do DatabaseManager"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
