"""
📋 Módulo de Cadastros
Gerencia cadastros de:
- Beneficiários (quem recebe pagamentos)
- Categorias personalizadas
- Fornecedores
- Membros de grupos
"""
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class Beneficiario:
    """Beneficiário/Destinatário de pagamentos"""
    id: str
    nome: str
    nome_normalizado: str  # Para busca
    tipo: str = "pessoa"   # pessoa, empresa, banco
    documento: str = ""    # CPF/CNPJ
    chave_pix: str = ""
    banco: str = ""
    categoria_padrao: str = "outros"
    user_id: str = ""
    grupo_id: str = ""     # Se pertence a um grupo
    criado_em: str = ""
    atualizado_em: str = ""
    
    def to_dict(self):
        return asdict(self)


@dataclass
class CategoriaPersonalizada:
    """Categoria personalizada de despesas"""
    id: str
    nome: str
    nome_normalizado: str
    icone: str = "💰"
    palavras_chave: List[str] = None
    user_id: str = ""
    grupo_id: str = ""
    criado_em: str = ""
    
    def __post_init__(self):
        if self.palavras_chave is None:
            self.palavras_chave = []
    
    def to_dict(self):
        return asdict(self)


@dataclass
class MembroGrupo:
    """Membro de um grupo"""
    id: str
    nome: str
    telefone: str = ""
    user_id: str = ""     # ID do WhatsApp
    grupo_id: str = ""
    is_admin: bool = False
    criado_em: str = ""
    
    def to_dict(self):
        return asdict(self)


class CadastrosModule:
    """Gerenciador de Cadastros"""
    
    # Categorias padrão do sistema
    CATEGORIAS_PADRAO = {
        'alimentacao': {'nome': 'Alimentação', 'icone': '🍔', 'palavras': ['mercado', 'supermercado', 'restaurante', 'ifood', 'padaria', 'lanchonete', 'açougue']},
        'transporte': {'nome': 'Transporte', 'icone': '🚗', 'palavras': ['uber', '99', 'gasolina', 'combustível', 'estacionamento', 'pedágio']},
        'moradia': {'nome': 'Moradia', 'icone': '🏠', 'palavras': ['aluguel', 'condomínio', 'luz', 'água', 'energia', 'internet', 'gás']},
        'saude': {'nome': 'Saúde', 'icone': '🏥', 'palavras': ['farmácia', 'médico', 'hospital', 'plano de saúde', 'dentista', 'exame']},
        'educacao': {'nome': 'Educação', 'icone': '📚', 'palavras': ['escola', 'faculdade', 'curso', 'livro', 'material escolar']},
        'lazer': {'nome': 'Lazer', 'icone': '🎮', 'palavras': ['cinema', 'netflix', 'spotify', 'viagem', 'hotel', 'show']},
        'vestuario': {'nome': 'Vestuário', 'icone': '👕', 'palavras': ['roupa', 'calçado', 'loja', 'shopping', 'tênis']},
        'servicos': {'nome': 'Serviços', 'icone': '🔧', 'palavras': ['assinatura', 'mensalidade', 'manutenção', 'conserto']},
        'impostos': {'nome': 'Impostos', 'icone': '📋', 'palavras': ['imposto', 'tributo', 'taxa', 'darf', 'gps', 'iptu', 'ipva']},
        'pets': {'nome': 'Pets', 'icone': '🐕', 'palavras': ['pet', 'veterinário', 'ração', 'animal']},
        'outros': {'nome': 'Outros', 'icone': '💰', 'palavras': []},
    }
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.cadastros_file = os.path.join(data_dir, "cadastros.json")
        
        os.makedirs(data_dir, exist_ok=True)
        self._load_data()
        
        # Cache de pendências (usuário -> pergunta pendente)
        self._pendencias: Dict[str, Dict] = {}
    
    def _load_data(self):
        """Carrega dados do disco"""
        if os.path.exists(self.cadastros_file):
            with open(self.cadastros_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.beneficiarios = data.get('beneficiarios', [])
                self.categorias = data.get('categorias', [])
                self.membros = data.get('membros', [])
        else:
            self.beneficiarios = []
            self.categorias = []
            self.membros = []
    
    def _save_data(self):
        """Salva dados no disco"""
        data = {
            'beneficiarios': self.beneficiarios,
            'categorias': self.categorias,
            'membros': self.membros
        }
        with open(self.cadastros_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _normalizar(self, texto: str) -> str:
        """Normaliza texto para busca (remove acentos, lowercase)"""
        import unicodedata
        texto = texto.lower().strip()
        # Remove acentos
        texto = unicodedata.normalize('NFD', texto)
        texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
        # Remove caracteres especiais
        texto = re.sub(r'[^\w\s]', '', texto)
        return texto
    
    def _gerar_id(self) -> str:
        """Gera ID único"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    # ==================== BENEFICIÁRIOS ====================
    
    def buscar_beneficiario(self, nome: str, user_id: str = None, grupo_id: str = None) -> Optional[Dict]:
        """Busca beneficiário por nome"""
        nome_norm = self._normalizar(nome)
        
        for b in self.beneficiarios:
            # Verifica se pertence ao usuário ou grupo
            if user_id and b.get('user_id') != user_id and not b.get('grupo_id'):
                continue
            if grupo_id and b.get('grupo_id') != grupo_id:
                continue
            
            # Busca por nome
            if nome_norm in b.get('nome_normalizado', ''):
                return b
            if nome_norm == self._normalizar(b.get('nome', '')):
                return b
        
        return None
    
    def cadastrar_beneficiario(self, nome: str, user_id: str = None, grupo_id: str = None,
                                tipo: str = "pessoa", documento: str = "", 
                                chave_pix: str = "", categoria_padrao: str = "outros") -> Dict:
        """Cadastra novo beneficiário"""
        beneficiario = {
            'id': self._gerar_id(),
            'nome': nome,
            'nome_normalizado': self._normalizar(nome),
            'tipo': tipo,
            'documento': documento,
            'chave_pix': chave_pix,
            'banco': '',
            'categoria_padrao': categoria_padrao,
            'user_id': user_id or '',
            'grupo_id': grupo_id or '',
            'criado_em': datetime.now().isoformat(),
            'atualizado_em': datetime.now().isoformat()
        }
        
        self.beneficiarios.append(beneficiario)
        self._save_data()
        return beneficiario
    
    def listar_beneficiarios(self, user_id: str = None, grupo_id: str = None) -> List[Dict]:
        """Lista beneficiários do usuário/grupo"""
        resultado = []
        for b in self.beneficiarios:
            if user_id and b.get('user_id') == user_id:
                resultado.append(b)
            elif grupo_id and b.get('grupo_id') == grupo_id:
                resultado.append(b)
        return resultado
    
    # ==================== CATEGORIAS ====================
    
    def buscar_categoria(self, nome: str, user_id: str = None) -> Optional[Dict]:
        """Busca categoria por nome ou palavra-chave"""
        nome_norm = self._normalizar(nome)
        
        # Primeiro busca nas categorias personalizadas
        for c in self.categorias:
            if user_id and c.get('user_id') != user_id:
                continue
            
            if nome_norm == c.get('nome_normalizado', ''):
                return c
            
            # Busca nas palavras-chave
            for palavra in c.get('palavras_chave', []):
                if self._normalizar(palavra) in nome_norm or nome_norm in self._normalizar(palavra):
                    return c
        
        # Depois busca nas categorias padrão
        for key, cat in self.CATEGORIAS_PADRAO.items():
            if nome_norm == self._normalizar(key) or nome_norm == self._normalizar(cat['nome']):
                return {'id': key, 'nome': cat['nome'], 'icone': cat['icone'], 'palavras_chave': cat['palavras']}
            
            for palavra in cat['palavras']:
                if self._normalizar(palavra) in nome_norm:
                    return {'id': key, 'nome': cat['nome'], 'icone': cat['icone'], 'palavras_chave': cat['palavras']}
        
        return None
    
    def cadastrar_categoria(self, nome: str, user_id: str = None, 
                            icone: str = "💰", palavras_chave: List[str] = None) -> Dict:
        """Cadastra nova categoria personalizada"""
        categoria = {
            'id': self._gerar_id(),
            'nome': nome,
            'nome_normalizado': self._normalizar(nome),
            'icone': icone,
            'palavras_chave': palavras_chave or [nome.lower()],
            'user_id': user_id or '',
            'grupo_id': '',
            'criado_em': datetime.now().isoformat()
        }
        
        self.categorias.append(categoria)
        self._save_data()
        return categoria
    
    def listar_categorias(self, user_id: str = None) -> List[Dict]:
        """Lista todas as categorias (padrão + personalizadas)"""
        # Categorias padrão
        resultado = []
        for key, cat in self.CATEGORIAS_PADRAO.items():
            resultado.append({
                'id': key,
                'nome': cat['nome'],
                'icone': cat['icone'],
                'tipo': 'padrao'
            })
        
        # Categorias personalizadas
        for c in self.categorias:
            if not user_id or c.get('user_id') == user_id:
                c_copy = c.copy()
                c_copy['tipo'] = 'personalizada'
                resultado.append(c_copy)
        
        return resultado
    
    # ==================== MEMBROS DE GRUPO ====================
    
    def buscar_membro(self, identificador: str, grupo_id: str) -> Optional[Dict]:
        """Busca membro do grupo por nome ou telefone"""
        identificador_norm = self._normalizar(identificador)
        
        for m in self.membros:
            if m.get('grupo_id') != grupo_id:
                continue
            
            if identificador_norm in self._normalizar(m.get('nome', '')):
                return m
            if identificador in m.get('telefone', ''):
                return m
            if identificador == m.get('user_id', ''):
                return m
        
        return None
    
    def cadastrar_membro(self, nome: str, grupo_id: str, telefone: str = "",
                          user_id: str = "", is_admin: bool = False) -> Dict:
        """Cadastra novo membro do grupo"""
        membro = {
            'id': self._gerar_id(),
            'nome': nome,
            'telefone': telefone,
            'user_id': user_id,
            'grupo_id': grupo_id,
            'is_admin': is_admin,
            'criado_em': datetime.now().isoformat()
        }
        
        self.membros.append(membro)
        self._save_data()
        return membro
    
    def listar_membros(self, grupo_id: str) -> List[Dict]:
        """Lista membros de um grupo"""
        return [m for m in self.membros if m.get('grupo_id') == grupo_id]
    
    # ==================== SISTEMA DE PERGUNTAS ====================
    
    def criar_pendencia(self, user_id: str, tipo: str, dados: Dict, pergunta: str) -> str:
        """Cria pendência de cadastro (pergunta ao usuário)"""
        self._pendencias[user_id] = {
            'tipo': tipo,
            'dados': dados,
            'pergunta': pergunta,
            'criado_em': datetime.now().isoformat()
        }
        return pergunta
    
    def tem_pendencia(self, user_id: str) -> bool:
        """Verifica se há pendência de cadastro"""
        return user_id in self._pendencias
    
    def processar_resposta_pendencia(self, user_id: str, resposta: str) -> Optional[str]:
        """Processa resposta de pendência de cadastro"""
        if user_id not in self._pendencias:
            return None
        
        pendencia = self._pendencias[user_id]
        resposta_lower = resposta.lower().strip()
        
        # Respostas afirmativas
        if resposta_lower in ['sim', 's', 'yes', 'y', '1', 'ok', 'pode', 'quero', 'cadastrar', 'cadastra']:
            tipo = pendencia['tipo']
            dados = pendencia['dados']
            
            if tipo == 'beneficiario':
                beneficiario = self.cadastrar_beneficiario(
                    nome=dados.get('nome'),
                    user_id=dados.get('user_id'),
                    grupo_id=dados.get('grupo_id'),
                    categoria_padrao=dados.get('categoria', 'outros')
                )
                del self._pendencias[user_id]
                return f"✅ *{dados.get('nome')}* cadastrado com sucesso!"
            
            elif tipo == 'categoria':
                categoria = self.cadastrar_categoria(
                    nome=dados.get('nome'),
                    user_id=dados.get('user_id'),
                    icone=dados.get('icone', '💰')
                )
                del self._pendencias[user_id]
                return f"✅ Categoria *{dados.get('nome')}* criada!"
            
            del self._pendencias[user_id]
            return "✅ Cadastrado!"
        
        # Respostas negativas
        elif resposta_lower in ['nao', 'não', 'n', 'no', '0', 'cancelar', 'cancela']:
            del self._pendencias[user_id]
            return "👍 Ok, não cadastrei."
        
        # Resposta não reconhecida - mantém pendência
        return None
    
    def cancelar_pendencia(self, user_id: str):
        """Cancela pendência de cadastro"""
        if user_id in self._pendencias:
            del self._pendencias[user_id]
    
    # ==================== COMANDOS ====================
    
    async def handle(self, command: str, args: List[str], 
                     user_id: str, attachments: list = None) -> str:
        """Processa comandos de cadastros"""
        
        if command == 'cadastros':
            return self._menu_cadastros()
        
        elif command == 'beneficiarios':
            return self._listar_beneficiarios_formatado(user_id)
        
        elif command == 'categorias':
            return self._listar_categorias_formatado(user_id)
        
        elif command in ['novo_beneficiario', 'cadastrar_beneficiario']:
            if args:
                nome = ' '.join(args)
                beneficiario = self.cadastrar_beneficiario(nome, user_id)
                return f"✅ Beneficiário *{nome}* cadastrado!"
            return "❌ Use: /cadastrar_beneficiario [nome]"
        
        elif command in ['nova_categoria', 'cadastrar_categoria']:
            if args:
                nome = ' '.join(args)
                categoria = self.cadastrar_categoria(nome, user_id)
                return f"✅ Categoria *{nome}* criada!"
            return "❌ Use: /cadastrar_categoria [nome]"
        
        return self._menu_cadastros()
    
    def _menu_cadastros(self) -> str:
        """Menu de cadastros"""
        return """📋 *Cadastros*

━━━━━━━━━━━━━━━━━━━━━

📌 *Gerenciar cadastros:*

👤 *beneficiarios* → Ver beneficiários
📁 *categorias* → Ver categorias

➕ *Adicionar:*
• cadastrar [nome] → Novo beneficiário
• nova categoria [nome] → Nova categoria

━━━━━━━━━━━━━━━━━━━━━

💡 _O sistema também cadastra automaticamente quando você confirma novos destinatários!_"""
    
    def _listar_beneficiarios_formatado(self, user_id: str) -> str:
        """Lista beneficiários formatado"""
        beneficiarios = self.listar_beneficiarios(user_id)
        
        if not beneficiarios:
            return """📋 *Beneficiários*

Nenhum beneficiário cadastrado ainda.

💡 Quando você fizer pagamentos, posso cadastrar automaticamente!"""
        
        texto = "📋 *Beneficiários Cadastrados*\n\n"
        for b in beneficiarios:
            icone = "🏢" if b.get('tipo') == 'empresa' else "👤"
            texto += f"{icone} *{b['nome']}*"
            if b.get('categoria_padrao') and b['categoria_padrao'] != 'outros':
                cat = self.CATEGORIAS_PADRAO.get(b['categoria_padrao'], {})
                texto += f" ({cat.get('icone', '')} {cat.get('nome', b['categoria_padrao'])})"
            texto += "\n"
        
        return texto
    
    def _listar_categorias_formatado(self, user_id: str) -> str:
        """Lista categorias formatado"""
        categorias = self.listar_categorias(user_id)
        
        texto = "📁 *Categorias*\n\n"
        texto += "*Padrão:*\n"
        
        for c in categorias:
            if c.get('tipo') == 'padrao':
                texto += f"{c['icone']} {c['nome']}\n"
        
        # Personalizadas
        personalizadas = [c for c in categorias if c.get('tipo') == 'personalizada']
        if personalizadas:
            texto += "\n*Personalizadas:*\n"
            for c in personalizadas:
                texto += f"{c.get('icone', '💰')} {c['nome']}\n"
        
        texto += "\n💡 _Digite 'nova categoria [nome]' para criar_"
        return texto


# Singleton
_cadastros: Optional[CadastrosModule] = None

def get_cadastros(data_dir: str = "data") -> CadastrosModule:
    """Retorna instância singleton"""
    global _cadastros
    if _cadastros is None:
        _cadastros = CadastrosModule(data_dir)
    return _cadastros
