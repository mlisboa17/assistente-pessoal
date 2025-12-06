"""
💰 Módulo de Finanças
Gerencia gastos, despesas e relatórios financeiros
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class Transacao:
    """Representa uma transação financeira"""
    id: str
    tipo: str  # 'entrada' ou 'saida'
    valor: float
    descricao: str
    categoria: str = "outros"
    data: str = ""  # ISO format
    user_id: str = ""
    criado_em: str = ""
    
    def to_dict(self):
        return asdict(self)


class FinancasModule:
    """Gerenciador de Finanças"""
    
    CATEGORIAS = {
        'alimentacao': [
            # Refeições
            'comida', 'almoço', 'almoco', 'janta', 'jantar', 'café', 'cafe', 'lanche', 'refeição', 'refeicao',
            'café da manhã', 'cafe da manha', 'marmita', 'quentinha', 'self service', 'self-service',
            # Estabelecimentos
            'restaurante', 'lanchonete', 'padaria', 'açougue', 'acougue', 'peixaria', 'hortifruti',
            'mercado', 'supermercado', 'mercadinho', 'mercearia', 'feira', 'sacolão', 'sacolao',
            'atacadão', 'atacadao', 'atacado', 'assaí', 'assai', 'carrefour', 'extra', 'pão de açúcar',
            'big', 'walmart', 'sam\'s', 'sams', 'costco',
            # Delivery/Apps
            'ifood', 'uber eats', 'rappi', 'zé delivery', 'ze delivery', 'aiqfome', 'delivery',
            # Bebidas
            'refrigerante', 'suco', 'bebida', 'drinks',
            # Fast food
            'mcdonald', 'mc', 'burger king', 'bk', 'subway', 'pizza', 'pizzaria', 'hambúrguer', 'hamburger',
            'hot dog', 'cachorro quente', 'açaí', 'acai', 'sorvete', 'sorveteria', 'doceria', 'doce',
            # Específicos
            'pão', 'pao', 'leite', 'carne', 'frango', 'peixe', 'arroz', 'feijão', 'feijao',
            'legumes', 'frutas', 'verduras', 'ovos', 'queijo', 'presunto', 'frios',
            'bolacha', 'biscoito', 'chocolate', 'bolo', 'salgado', 'coxinha', 'pastel',
            # Genéricos
            'comer', 'comendo', 'comi', 'alimentação', 'alimentacao', 'rancho', 'compras do mês'
        ],
        'combustivel': [
            # Combustíveis
            'gasolina', 'combustível', 'combustivel', 'álcool', 'alcool', 'etanol', 'diesel', 'gnv',
            'posto', 'abastecimento', 'abastecer', 'abasteci', 'tanque', 'encher o tanque',
            'shell', 'petrobras', 'br', 'ipiranga', 'ale', 'posto de gasolina'
        ],
        'transporte': [
            'uber', '99', '99pop', 'taxi', 'táxi', 'cabify', 'indriver',
            'estacionamento', 'zona azul', 'valet', 'garagem',
            'ônibus', 'onibus', 'metrô', 'metro', 'trem', 'brt', 'passagem', 'bilhete único',
            'pedágio', 'pedagio', 'ipva', 'licenciamento', 'multa', 'detran',
            'mecânico', 'mecanico', 'oficina', 'pneu', 'borracharia', 'troca de óleo', 'revisão',
            'carro', 'moto', 'bicicleta', 'bike', 'patinete'
        ],
        'moradia': [
            'aluguel', 'condomínio', 'condominio', 'iptu', 'luz', 'energia', 'conta de luz',
            'água', 'agua', 'conta de água', 'saneamento', 'esgoto',
            'gás', 'gas', 'botijão', 'botijao',
            'internet', 'wifi', 'banda larga', 'fibra',
            'telefone', 'plano', 'tim', 'vivo', 'claro', 'oi',
            'tv', 'tv a cabo', 'sky', 'net',
            'faxina', 'diarista', 'empregada', 'limpeza',
            'móveis', 'moveis', 'eletrodoméstico', 'eletrodomestico', 'geladeira', 'fogão', 'fogao',
            'manutenção', 'manutencao', 'conserto', 'reparo', 'encanador', 'eletricista', 'pintor'
        ],
        'saude': [
            'farmácia', 'farmacia', 'remédio', 'remedio', 'medicamento', 'droga', 'drogaria',
            'médico', 'medico', 'consulta', 'doutor', 'dr', 'clínica', 'clinica',
            'exame', 'laboratório', 'laboratorio', 'raio x', 'ultrassom', 'ressonância',
            'hospital', 'emergência', 'emergencia', 'pronto socorro', 'upa',
            'dentista', 'odonto', 'ortodontia', 'aparelho',
            'psicólogo', 'psicologo', 'terapia', 'psiquiatra',
            'plano de saúde', 'plano de saude', 'unimed', 'amil', 'bradesco saúde', 'sulamerica',
            'óculos', 'oculos', 'lente', 'oftalmologista', 'oculista',
            'fisioterapia', 'fisioterapeuta', 'massagem', 'quiropraxia',
            'vacina', 'vitamina', 'suplemento'
        ],
        'lazer': [
            # Cinema/Entretenimento
            'cinema', 'filme', 'teatro', 'show', 'ingresso', 'evento', 'espetáculo', 'espetaculo',
            # Streaming
            'netflix', 'spotify', 'amazon prime', 'disney', 'hbo', 'globoplay', 'streaming',
            'youtube premium', 'deezer', 'apple music',
            # Games
            'jogo', 'game', 'playstation', 'xbox', 'nintendo', 'steam', 'videogame',
            # Viagem
            'viagem', 'hotel', 'pousada', 'airbnb', 'passagem aérea', 'avião', 'voo',
            # Social
            'bar', 'balada', 'festa', 'churrasco', 'churras', 'cerveja', 'happy hour',
            'boteco', 'pub', 'boate', 'night', 'drinks',
            # Atividades
            'praia', 'parque', 'clube', 'piscina', 'resort', 'spa',
            'hobby', 'diversão', 'diversao', 'passeio', 'tour', 'excursão', 'excursao',
            # Esportes/Academia
            'academia', 'gym', 'smartfit', 'bluefit', 'crossfit', 'musculação', 'musculacao',
            'futebol', 'quadra', 'tênis', 'natação', 'natacao', 'corrida', 'esporte',
            # Outros
            'parque de diversão', 'zoológico', 'zoologico', 'aquário', 'aquario', 'museu',
            'escape room', 'boliche', 'sinuca', 'karaokê', 'karaoke'
        ],
        'educacao': [
            'curso', 'aula', 'escola', 'colégio', 'colegio', 'faculdade', 'universidade',
            'mensalidade', 'matrícula', 'matricula', 'material escolar', 'apostila',
            'livro', 'livraria', 'ebook', 'kindle',
            'inglês', 'ingles', 'espanhol', 'idioma', 'língua', 'lingua',
            'workshop', 'palestra', 'congresso', 'seminário', 'seminario',
            'udemy', 'coursera', 'alura', 'rocketseat', 'online'
        ],
        'vestuario': [
            'roupa', 'camisa', 'camiseta', 'calça', 'calca', 'short', 'bermuda', 'vestido', 'saia',
            'sapato', 'tênis', 'tenis', 'sandália', 'sandalia', 'chinelo', 'bota',
            'loja', 'shopping', 'renner', 'riachuelo', 'c&a', 'cea', 'marisa', 'hering',
            'roupa íntima', 'cueca', 'calcinha', 'meia', 'cinto', 'acessório', 'acessorio',
            'bolsa', 'mochila', 'carteira', 'óculos de sol'
        ],
        'beleza': [
            'salão', 'salao', 'cabeleireiro', 'cabelo', 'corte', 'escova', 'tintura',
            'manicure', 'pedicure', 'unha', 'esmalte',
            'barbeiro', 'barbearia', 'barba',
            'estética', 'estetica', 'depilação', 'depilacao', 'sobrancelha',
            'maquiagem', 'make', 'batom', 'base', 'rímel', 'rimel',
            'perfume', 'creme', 'hidratante', 'shampoo', 'condicionador', 'sabonete',
            'desodorante', 'protetor solar'
        ],
        'pets': [
            'pet', 'cachorro', 'gato', 'animal', 'ração', 'racao', 'petshop', 'pet shop',
            'veterinário', 'veterinario', 'vet', 'vacina pet', 'banho e tosa', 'tosa',
            'coleira', 'brinquedo pet', 'casinha', 'cama pet'
        ],
        'tecnologia': [
            'celular', 'smartphone', 'iphone', 'samsung', 'motorola', 'xiaomi',
            'computador', 'notebook', 'pc', 'mac', 'apple', 'dell', 'lenovo',
            'tablet', 'ipad', 'fone', 'airpod', 'eletrônico', 'eletronico',
            'carregador', 'cabo', 'acessório tech', 'case', 'película', 'pelicula'
        ],
        'assinaturas': [
            'assinatura', 'mensalidade', 'plano mensal', 'recorrente',
            'amazon', 'prime', 'spotify', 'netflix', 'youtube premium', 'icloud', 'google one',
            'gym', 'academia', 'smartfit', 'bluefit'
        ],
        'impostos': [
            'imposto', 'tributo', 'taxa', 'darf', 'gps', 'das', 'inss', 'irpf', 'irpj',
            'pis', 'cofins', 'csll', 'itr', 'fgts', 'icms', 'iss', 'iptu', 'ipva',
            'itbi', 'itcmd', 'contribuição', 'contribuicao', 'guia', 'receita federal',
            'sefaz', 'prefeitura', 'licenciamento', 'multa', 'mei', 'simples nacional'
        ],
        'outros': []
    }
    
    # Mapeamento de números/textos para categorias
    CATEGORIA_MAP = {
        '1': 'alimentacao', 'alimentacao': 'alimentacao', 'alimentação': 'alimentacao',
        '2': 'combustivel', 'combustivel': 'combustivel', 'combustível': 'combustivel',
        '3': 'transporte', 'transporte': 'transporte',
        '4': 'moradia', 'moradia': 'moradia', 'casa': 'moradia',
        '5': 'saude', 'saude': 'saude', 'saúde': 'saude',
        '6': 'lazer', 'lazer': 'lazer', 'diversao': 'lazer', 'diversão': 'lazer',
        '7': 'educacao', 'educacao': 'educacao', 'educação': 'educacao',
        '8': 'vestuario', 'vestuario': 'vestuario', 'vestuário': 'vestuario', 'roupa': 'vestuario',
        '9': 'beleza', 'beleza': 'beleza',
        '10': 'tecnologia', 'tecnologia': 'tecnologia', 'tech': 'tecnologia',
        '0': 'outros', 'outros': 'outros'
    }
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.transacoes_file = os.path.join(data_dir, "transacoes.json")
        self.pendencias_file = os.path.join(data_dir, "pendencias_categoria.json")
        self.sugestoes_file = os.path.join(data_dir, "sugestoes_categoria.json")
        self.categorias_personalizadas_file = os.path.join(data_dir, "categorias_personalizadas.json")
        
        os.makedirs(data_dir, exist_ok=True)
        self._load_data()
        self._load_pendencias()
        self._load_sugestoes()
        self._load_categorias_personalizadas()
    
    def _load_data(self):
        """Carrega dados do disco"""
        if os.path.exists(self.transacoes_file):
            with open(self.transacoes_file, 'r', encoding='utf-8') as f:
                self.transacoes = json.load(f)
        else:
            self.transacoes = []
    
    def _load_pendencias(self):
        """Carrega pendências de categorização"""
        if os.path.exists(self.pendencias_file):
            with open(self.pendencias_file, 'r', encoding='utf-8') as f:
                self.pendencias = json.load(f)
        else:
            self.pendencias = {}
    
    def _load_sugestoes(self):
        """Carrega sugestões de palavras-chave pendentes de aprovação"""
        if os.path.exists(self.sugestoes_file):
            with open(self.sugestoes_file, 'r', encoding='utf-8') as f:
                self.sugestoes = json.load(f)
        else:
            self.sugestoes = []
    
    def _load_categorias_personalizadas(self):
        """Carrega categorias personalizadas criadas pelo usuário"""
        if os.path.exists(self.categorias_personalizadas_file):
            with open(self.categorias_personalizadas_file, 'r', encoding='utf-8') as f:
                self.categorias_personalizadas = json.load(f)
        else:
            self.categorias_personalizadas = {}
        
        # Atualiza CATEGORIAS e CATEGORIA_MAP com as personalizadas
        self._atualizar_categorias_personalizadas()
    
    def _save_categorias_personalizadas(self):
        """Salva categorias personalizadas no disco"""
        with open(self.categorias_personalizadas_file, 'w', encoding='utf-8') as f:
            json.dump(self.categorias_personalizadas, f, ensure_ascii=False, indent=2)
    
    def _atualizar_categorias_personalizadas(self):
        """Atualiza dicionários com categorias personalizadas"""
        for nome, dados in self.categorias_personalizadas.items():
            nome_lower = nome.lower()
            # Adiciona ao CATEGORIAS se não existir
            if nome_lower not in self.CATEGORIAS:
                self.CATEGORIAS[nome_lower] = dados.get('palavras_chave', [])
            # Adiciona ao CATEGORIA_MAP
            self.CATEGORIA_MAP[nome_lower] = nome_lower
            # Adiciona variações sem acento
            nome_sem_acento = self._remover_acentos(nome_lower)
            if nome_sem_acento != nome_lower:
                self.CATEGORIA_MAP[nome_sem_acento] = nome_lower
    
    def _remover_acentos(self, texto: str) -> str:
        """Remove acentos de uma string"""
        import unicodedata
        return ''.join(
            c for c in unicodedata.normalize('NFD', texto)
            if unicodedata.category(c) != 'Mn'
        )
    
    def _save_pendencias(self):
        """Salva pendências no disco"""
        with open(self.pendencias_file, 'w', encoding='utf-8') as f:
            json.dump(self.pendencias, f, ensure_ascii=False, indent=2)
    
    def _save_sugestoes(self):
        """Salva sugestões no disco"""
        with open(self.sugestoes_file, 'w', encoding='utf-8') as f:
            json.dump(self.sugestoes, f, ensure_ascii=False, indent=2)
    
    def _salvar_pendencia_categoria(self, user_id: str, transacao_id: str, descricao: str):
        """Salva uma transação pendente de categorização"""
        self.pendencias[user_id] = {
            'transacao_id': transacao_id,
            'descricao': descricao,
            'etapa': 'categoria'  # categoria -> sugestao
        }
        self._save_pendencias()
    
    def _tem_pendencia_categoria(self, user_id: str) -> bool:
        """Verifica se usuário tem pendência de categoria"""
        return user_id in self.pendencias
    
    def _adicionar_sugestao(self, palavra: str, categoria: str, descricao_original: str, user_id: str):
        """Adiciona uma sugestão de palavra-chave para aprovação futura"""
        sugestao = {
            'id': str(len(self.sugestoes) + 1),
            'palavra': palavra.lower().strip(),
            'categoria': categoria,
            'descricao_original': descricao_original,
            'user_id': user_id,
            'data': datetime.now().isoformat(),
            'status': 'pendente'  # pendente, aprovado, rejeitado
        }
        self.sugestoes.append(sugestao)
        self._save_sugestoes()
        return sugestao
    
    def _processar_categoria_pendente(self, user_id: str, resposta: str) -> str:
        """Processa a resposta de categorização pendente"""
        if user_id not in self.pendencias:
            return None
        
        pendencia = self.pendencias[user_id]
        
        # Compatibilidade com formato antigo
        if isinstance(pendencia, str):
            transacao_id = pendencia
            etapa = 'categoria'
            descricao = ''
        else:
            transacao_id = pendencia.get('transacao_id')
            etapa = pendencia.get('etapa', 'categoria')
            descricao = pendencia.get('descricao', '')
        
        resposta_lower = resposta.lower().strip()
        
        # ETAPA 1: Escolher categoria
        if etapa == 'categoria':
            # Verifica se é uma resposta de categoria válida
            if resposta_lower not in self.CATEGORIA_MAP:
                return None  # Não é uma resposta de categoria, ignora
            
            nova_categoria = self.CATEGORIA_MAP[resposta_lower]
            
            # Atualiza a transação
            for t in self.transacoes:
                if t.get('id') == transacao_id:
                    t['categoria'] = nova_categoria
                    self._save_data()
                    
                    emoji = self._emoji_categoria(nova_categoria)
                    
                    # Atualiza pendência para etapa de sugestão
                    self.pendencias[user_id] = {
                        'transacao_id': transacao_id,
                        'descricao': t.get('descricao', descricao),
                        'categoria': nova_categoria,
                        'etapa': 'sugestao'
                    }
                    self._save_pendencias()
                    
                    return f"""
✅ *Categoria atualizada!*

{emoji} {nova_categoria.capitalize()}
📝 {t.get('descricao', '')}
💰 R$ {t.get('valor', 0):.2f}

💡 *Quer sugerir uma palavra-chave?*
Qual palavra devo associar a "{nova_categoria}" no futuro?

_Exemplo: se gastou no "Zé da Pizza", digite "zé da pizza"_
_Ou digite "não" para pular_"""
            
            return None
        
        # ETAPA 2: Sugerir palavra-chave
        elif etapa == 'sugestao':
            categoria = pendencia.get('categoria', 'outros')
            
            # Se não quiser sugerir
            if resposta_lower in ['não', 'nao', 'n', 'pular', 'skip', 'cancelar']:
                del self.pendencias[user_id]
                self._save_pendencias()
                return "👍 Ok, sem sugestão. Pode continuar!"
            
            # Salva a sugestão para aprovação futura
            sugestao = self._adicionar_sugestao(
                palavra=resposta_lower,
                categoria=categoria,
                descricao_original=descricao,
                user_id=user_id
            )
            
            # Remove pendência
            del self.pendencias[user_id]
            self._save_pendencias()
            
            emoji = self._emoji_categoria(categoria)
            return f"""
📝 *Sugestão salva!*

{emoji} Palavra: *{resposta_lower}*
🏷️ Categoria: {categoria.capitalize()}

_Aguardando aprovação. Use /sugestoes para ver todas._"""
        
        return None
    
    def _listar_sugestoes(self, user_id: str = None) -> str:
        """Lista sugestões pendentes de aprovação"""
        pendentes = [s for s in self.sugestoes if s.get('status') == 'pendente']
        
        if not pendentes:
            return "✅ Nenhuma sugestão pendente de aprovação!"
        
        texto = "📋 *Sugestões Pendentes de Aprovação*\n\n"
        
        for s in pendentes:
            emoji = self._emoji_categoria(s.get('categoria', 'outros'))
            texto += f"🔹 *ID {s['id']}*: \"{s['palavra']}\" → {emoji} {s['categoria'].capitalize()}\n"
            texto += f"   _Origem: {s.get('descricao_original', 'N/A')[:30]}..._\n\n"
        
        texto += "\n*Comandos:*\n"
        texto += "• `/aprovar [id]` - Aprova e adiciona à categoria\n"
        texto += "• `/rejeitar [id]` - Rejeita a sugestão"
        
        return texto
    
    def _aprovar_sugestao(self, sugestao_id: str) -> str:
        """Aprova uma sugestão e adiciona à categoria"""
        for s in self.sugestoes:
            if s.get('id') == sugestao_id and s.get('status') == 'pendente':
                palavra = s['palavra']
                categoria = s['categoria']
                
                # Adiciona à categoria (em memória - para persistir, seria em arquivo separado)
                if categoria in self.CATEGORIAS:
                    if palavra not in self.CATEGORIAS[categoria]:
                        self.CATEGORIAS[categoria].append(palavra)
                
                s['status'] = 'aprovado'
                s['aprovado_em'] = datetime.now().isoformat()
                self._save_sugestoes()
                
                emoji = self._emoji_categoria(categoria)
                return f"""
✅ *Sugestão aprovada!*

{emoji} "{palavra}" → {categoria.capitalize()}

_A palavra será reconhecida automaticamente!_"""
        
        return "❌ Sugestão não encontrada ou já processada."
    
    def _rejeitar_sugestao(self, sugestao_id: str) -> str:
        """Rejeita uma sugestão"""
        for s in self.sugestoes:
            if s.get('id') == sugestao_id and s.get('status') == 'pendente':
                s['status'] = 'rejeitado'
                s['rejeitado_em'] = datetime.now().isoformat()
                self._save_sugestoes()
                
                return f"🗑️ Sugestão \"{s['palavra']}\" rejeitada."
        
        return "❌ Sugestão não encontrada ou já processada."
    
    # ==========================================
    # 🆕 CATEGORIAS PERSONALIZADAS
    # ==========================================
    
    def criar_categoria(self, nome: str, emoji: str = None, palavras_chave: List[str] = None, user_id: str = None) -> str:
        """
        Cria uma nova categoria personalizada
        
        Args:
            nome: Nome da categoria (ex: "investimentos", "freelance")
            emoji: Emoji para a categoria (opcional)
            palavras_chave: Lista de palavras-chave associadas (opcional)
            user_id: ID do usuário que criou
        """
        nome_lower = nome.lower().strip()
        nome_sem_acento = self._remover_acentos(nome_lower)
        
        # Verifica se já existe
        if nome_lower in self.CATEGORIAS or nome_lower in self.categorias_personalizadas:
            return f"⚠️ A categoria *{nome}* já existe!"
        
        # Define emoji padrão se não fornecido
        if not emoji:
            emojis_padrao = ['🏷️', '📌', '🔖', '📂', '💼', '🎯', '⭐', '🔹']
            emoji = emojis_padrao[len(self.categorias_personalizadas) % len(emojis_padrao)]
        
        # Cria a categoria
        self.categorias_personalizadas[nome_lower] = {
            'nome': nome,
            'nome_display': nome.capitalize(),
            'emoji': emoji,
            'palavras_chave': palavras_chave or [],
            'criado_por': user_id,
            'criado_em': datetime.now().isoformat(),
            'total_transacoes': 0
        }
        
        # Salva no arquivo
        self._save_categorias_personalizadas()
        
        # Atualiza em memória
        self.CATEGORIAS[nome_lower] = palavras_chave or []
        self.CATEGORIA_MAP[nome_lower] = nome_lower
        if nome_sem_acento != nome_lower:
            self.CATEGORIA_MAP[nome_sem_acento] = nome_lower
        
        return f"""
✅ *Categoria criada com sucesso!*

{emoji} *{nome.capitalize()}*

📝 Palavras-chave: {', '.join(palavras_chave) if palavras_chave else 'Nenhuma definida'}

💡 *Dicas:*
• Use `gastei X em {nome}` para registrar despesas
• Use `adicionar palavra {nome} <palavra>` para associar palavras-chave
• Use `categorias` para ver todas as categorias"""

    def listar_categorias(self, incluir_sistema: bool = True) -> str:
        """Lista todas as categorias disponíveis"""
        texto = "📋 *CATEGORIAS DISPONÍVEIS*\n\n"
        
        # Categorias do sistema
        if incluir_sistema:
            texto += "🔷 *Categorias do Sistema:*\n"
            categorias_sistema = [
                ('alimentacao', '🍔'), ('combustivel', '⛽'), ('transporte', '🚗'),
                ('moradia', '🏠'), ('saude', '💊'), ('lazer', '🎮'),
                ('educacao', '📚'), ('vestuario', '👕'), ('beleza', '💇'),
                ('pets', '🐕'), ('tecnologia', '📱'), ('assinaturas', '📋'),
                ('impostos', '🏛️'), ('outros', '📦')
            ]
            for cat, emoji in categorias_sistema:
                texto += f"   {emoji} {cat.capitalize()}\n"
        
        # Categorias personalizadas
        if self.categorias_personalizadas:
            texto += "\n🔶 *Suas Categorias Personalizadas:*\n"
            for nome, dados in self.categorias_personalizadas.items():
                emoji = dados.get('emoji', '🏷️')
                qtd = dados.get('total_transacoes', 0)
                palavras = dados.get('palavras_chave', [])
                texto += f"   {emoji} *{dados.get('nome_display', nome.capitalize())}*"
                if qtd > 0:
                    texto += f" ({qtd} transações)"
                texto += "\n"
                if palavras:
                    texto += f"      _Palavras: {', '.join(palavras[:5])}{'...' if len(palavras) > 5 else ''}_\n"
        else:
            texto += "\n_Você ainda não criou categorias personalizadas._\n"
        
        texto += "\n💡 *Criar nova categoria:*\n"
        texto += "`criar categoria <nome>` ou\n"
        texto += "`criar categoria <nome> <emoji> <palavras>`"
        
        return texto
    
    def adicionar_palavra_categoria(self, categoria: str, palavra: str) -> str:
        """Adiciona uma palavra-chave a uma categoria"""
        categoria_lower = categoria.lower().strip()
        palavra_lower = palavra.lower().strip()
        
        # Verifica se é categoria personalizada
        if categoria_lower in self.categorias_personalizadas:
            if palavra_lower not in self.categorias_personalizadas[categoria_lower]['palavras_chave']:
                self.categorias_personalizadas[categoria_lower]['palavras_chave'].append(palavra_lower)
                self._save_categorias_personalizadas()
                
                # Atualiza em memória também
                if categoria_lower in self.CATEGORIAS:
                    self.CATEGORIAS[categoria_lower].append(palavra_lower)
                
                emoji = self.categorias_personalizadas[categoria_lower].get('emoji', '🏷️')
                return f"""
✅ *Palavra adicionada!*

{emoji} Categoria: *{categoria.capitalize()}*
📝 Nova palavra: *{palavra}*

_Agora "{palavra}" será automaticamente categorizado como {categoria}!_"""
            else:
                return f"⚠️ A palavra *{palavra}* já está associada a *{categoria}*!"
        
        # Verifica se é categoria do sistema
        if categoria_lower in self.CATEGORIAS:
            if palavra_lower not in self.CATEGORIAS[categoria_lower]:
                self.CATEGORIAS[categoria_lower].append(palavra_lower)
                emoji = self._emoji_categoria(categoria_lower)
                return f"""
✅ *Palavra adicionada!*

{emoji} Categoria: *{categoria.capitalize()}*
📝 Nova palavra: *{palavra}*

_Agora "{palavra}" será automaticamente categorizado como {categoria}!_"""
            else:
                return f"⚠️ A palavra *{palavra}* já está associada a *{categoria}*!"
        
        return f"❌ Categoria *{categoria}* não encontrada. Use `categorias` para ver as disponíveis."
    
    def remover_categoria(self, nome: str, user_id: str) -> str:
        """Remove uma categoria personalizada"""
        nome_lower = nome.lower().strip()
        
        # Não permite remover categorias do sistema
        categorias_sistema = ['alimentacao', 'combustivel', 'transporte', 'moradia', 'saude', 
                             'lazer', 'educacao', 'vestuario', 'beleza', 'pets', 'tecnologia', 
                             'assinaturas', 'impostos', 'outros']
        
        if nome_lower in categorias_sistema:
            return f"❌ Não é possível remover a categoria do sistema *{nome}*."
        
        if nome_lower not in self.categorias_personalizadas:
            return f"❌ Categoria *{nome}* não encontrada nas suas categorias personalizadas."
        
        # Conta transações nessa categoria
        qtd_transacoes = sum(1 for t in self.transacoes if t.get('categoria') == nome_lower)
        
        # Remove
        dados = self.categorias_personalizadas.pop(nome_lower)
        self._save_categorias_personalizadas()
        
        # Remove da memória
        if nome_lower in self.CATEGORIAS:
            del self.CATEGORIAS[nome_lower]
        if nome_lower in self.CATEGORIA_MAP:
            del self.CATEGORIA_MAP[nome_lower]
        
        emoji = dados.get('emoji', '🏷️')
        msg = f"""
🗑️ *Categoria removida!*

{emoji} *{dados.get('nome_display', nome.capitalize())}*"""
        
        if qtd_transacoes > 0:
            msg += f"""

⚠️ *Atenção:* {qtd_transacoes} transações ainda estão com essa categoria.
Use `recategorizar {nome} <nova_categoria>` para movê-las."""
        
        return msg
    
    def _save_data(self):
        """Salva dados no disco"""
        with open(self.transacoes_file, 'w', encoding='utf-8') as f:
            json.dump(self.transacoes, f, ensure_ascii=False, indent=2)
    
    def _detectar_categoria(self, descricao: str) -> str:
        """Detecta categoria baseado na descrição"""
        descricao_lower = descricao.lower()
        
        # Primeiro verifica palavras aprovadas das sugestões
        for s in self.sugestoes:
            if s.get('status') == 'aprovado':
                if s['palavra'] in descricao_lower:
                    return s['categoria']
        
        for categoria, palavras in self.CATEGORIAS.items():
            for palavra in palavras:
                if palavra in descricao_lower:
                    return categoria
        
        return 'outros'
    
    def _emoji_categoria(self, categoria: str) -> str:
        """Retorna emoji da categoria"""
        # Primeiro verifica categorias personalizadas
        if categoria in self.categorias_personalizadas:
            return self.categorias_personalizadas[categoria].get('emoji', '🏷️')
        
        emojis = {
            'alimentacao': '🍔',
            'combustivel': '⛽',
            'transporte': '🚗',
            'moradia': '🏠',
            'saude': '💊',
            'lazer': '🎮',
            'educacao': '📚',
            'vestuario': '👕',
            'beleza': '💇',
            'pets': '🐕',
            'tecnologia': '📱',
            'assinaturas': '📋',
            'impostos': '🏛️',
            'outros': '📦'
        }
        return emojis.get(categoria, '💸')
    
    async def handle(self, command: str, args: List[str], 
                     user_id: str, attachments: list = None) -> str:
        """Processa comandos de finanças"""
        
        if command == 'gastos':
            return self._resumo_gastos(user_id)
        
        elif command == 'despesas':
            if args:
                return self._registrar_despesa(user_id, args)
            return self._listar_despesas(user_id)
        
        elif command in ['saldo', 'financas']:
            return self._saldo_geral(user_id)
        
        elif command == 'entrada':
            if args:
                return self._registrar_entrada(user_id, args)
            return "💵 Use: /entrada [valor] [descrição]"
        
        # Comandos de sugestões
        elif command == 'sugestoes':
            return self._listar_sugestoes(user_id)
        
        elif command == 'aprovar':
            if args:
                return self._aprovar_sugestao(args[0])
            return "❌ Use: /aprovar [id]"
        
        elif command == 'rejeitar':
            if args:
                return self._rejeitar_sugestao(args[0])
            return "❌ Use: /rejeitar [id]"
        
        # 🆕 Comandos de categorias personalizadas
        elif command in ['categorias', 'categoria']:
            if not args:
                return self.listar_categorias()
            # criar categoria X
            if args[0].lower() == 'criar' and len(args) > 1:
                return self.criar_categoria(args[1], args[2] if len(args) > 2 else None, args[3:] if len(args) > 3 else None, user_id)
            return self.listar_categorias()
        
        elif command == 'criar':
            # criar categoria X ou criar categoria X emoji palavras
            if args and args[0].lower() == 'categoria' and len(args) > 1:
                nome = args[1]
                emoji = args[2] if len(args) > 2 and len(args[2]) <= 2 else None
                palavras = args[3:] if emoji and len(args) > 3 else args[2:] if len(args) > 2 else None
                return self.criar_categoria(nome, emoji, palavras, user_id)
            return "❌ Use: criar categoria <nome> [emoji] [palavras-chave]"
        
        elif command == 'remover' and args and args[0].lower() == 'categoria':
            if len(args) > 1:
                return self.remover_categoria(args[1], user_id)
            return "❌ Use: remover categoria <nome>"
        
        elif command == 'adicionar' and args and args[0].lower() == 'palavra':
            # adicionar palavra <categoria> <palavra>
            if len(args) >= 3:
                return self.adicionar_palavra_categoria(args[1], ' '.join(args[2:]))
            return "❌ Use: adicionar palavra <categoria> <palavra>"
        
        return "💰 Comandos: /gastos, /despesas, /saldo, /categorias, /sugestoes"
    
    async def handle_natural(self, message: str, analysis: Any,
                              user_id: str, attachments: list = None) -> str:
        """Processa linguagem natural"""
        text_lower = message.lower()
        
        # Detecta valor
        valor = None
        if analysis and analysis.entities.get('money'):
            valor = analysis.entities['money'].get('value')
        
        # Detecta ação
        if any(word in text_lower for word in ['gastei', 'paguei', 'comprei', 'despesa']):
            if valor:
                return self._registrar_despesa(user_id, [str(valor), message])
            return "💸 Quanto você gastou? Informe o valor."
        
        if any(word in text_lower for word in ['recebi', 'ganhei', 'entrada', 'salário']):
            if valor:
                return self._registrar_entrada(user_id, [str(valor), message])
            return "💵 Quanto você recebeu? Informe o valor."
        
        if any(word in text_lower for word in ['gasto', 'quanto', 'despesas']):
            return self._resumo_gastos(user_id)
        
        return self._resumo_gastos(user_id)
    
    def _registrar_despesa(self, user_id: str, args: List[str]) -> str:
        """Registra uma despesa"""
        from uuid import uuid4
        
        if not args:
            return "❌ Informe o valor e descrição da despesa."
        
        # Primeiro argumento é o valor
        try:
            valor_str = args[0].replace('R$', '').replace(',', '.').strip()
            valor = float(valor_str)
        except:
            return "❌ Valor inválido. Use: /despesas 50.00 Almoço"
        
        # Resto é a descrição
        descricao = ' '.join(args[1:]) if len(args) > 1 else "Despesa"
        categoria = self._detectar_categoria(descricao)
        
        transacao = Transacao(
            id=str(uuid4())[:8],
            tipo='saida',
            valor=valor,
            descricao=descricao,
            categoria=categoria,
            data=datetime.now().strftime('%Y-%m-%d'),
            user_id=user_id,
            criado_em=datetime.now().isoformat()
        )
        
        self.transacoes.append(transacao.to_dict())
        self._save_data()
        
        emoji = self._emoji_categoria(categoria)
        
        # Se categoria ficou como "outros", pergunta se quer definir
        pergunta_categoria = ""
        if categoria == 'outros':
            pergunta_categoria = """

❓ *Não reconheci a categoria.*
Em qual categoria você quer salvar?

1️⃣ Alimentação
2️⃣ Combustível
3️⃣ Transporte
4️⃣ Moradia
5️⃣ Saúde
6️⃣ Lazer
7️⃣ Educação
8️⃣ Vestuário
9️⃣ Beleza
🔟 Tecnologia
0️⃣ Outros (manter)

_Responda com o número ou nome da categoria_"""
            # Salva transação pendente para categorização
            self._salvar_pendencia_categoria(user_id, transacao.id, descricao)
        
        return f"""
💸 *DESPESA Registrada!*

{emoji} R$ {valor:.2f}
📝 {descricao}
🏷️ Categoria: {categoria.capitalize()}
📅 {datetime.now().strftime('%d/%m/%Y')}
{pergunta_categoria}"""
    
    def _registrar_entrada(self, user_id: str, args: List[str]) -> str:
        """Registra uma entrada"""
        from uuid import uuid4
        
        if not args:
            return "❌ Informe o valor e descrição."
        
        try:
            valor_str = args[0].replace('R$', '').replace(',', '.').strip()
            valor = float(valor_str)
        except:
            return "❌ Valor inválido."
        
        descricao = ' '.join(args[1:]) if len(args) > 1 else "Entrada"
        
        transacao = Transacao(
            id=str(uuid4())[:8],
            tipo='entrada',
            valor=valor,
            descricao=descricao,
            categoria='renda',
            data=datetime.now().strftime('%Y-%m-%d'),
            user_id=user_id,
            criado_em=datetime.now().isoformat()
        )
        
        self.transacoes.append(transacao.to_dict())
        self._save_data()
        
        return f"""
💵 *RECEITA Registrada!*

✅ R$ {valor:.2f}
📝 {descricao}
📅 {datetime.now().strftime('%d/%m/%Y')}
"""
    
    def _resumo_gastos(self, user_id: str) -> str:
        """Retorna resumo de gastos do mês"""
        hoje = datetime.now()
        inicio_mes = hoje.replace(day=1).strftime('%Y-%m-%d')
        
        # Filtra transações do usuário no mês
        transacoes_mes = [
            t for t in self.transacoes
            if t.get('user_id') == user_id 
            and t.get('data', '') >= inicio_mes
            and t.get('tipo') == 'saida'
        ]
        
        if not transacoes_mes:
            return f"""
💰 *Resumo de Gastos* ({hoje.strftime('%B/%Y')})

📭 Nenhum gasto registrado este mês.

_Use /despesas [valor] [descrição] para registrar._
"""
        
        # Agrupa por categoria
        por_categoria = defaultdict(float)
        total = 0
        
        for t in transacoes_mes:
            categoria = t.get('categoria', 'outros')
            valor = t.get('valor', 0)
            por_categoria[categoria] += valor
            total += valor
        
        # Monta resposta
        response = f"💰 *Resumo de Gastos* ({hoje.strftime('%B/%Y')})\n\n"
        
        # Ordena por valor
        for categoria, valor in sorted(por_categoria.items(), key=lambda x: -x[1]):
            emoji = self._emoji_categoria(categoria)
            percent = (valor / total * 100) if total > 0 else 0
            response += f"{emoji} {categoria.capitalize()}: R$ {valor:.2f} ({percent:.0f}%)\n"
        
        response += f"\n💸 *Total: R$ {total:.2f}*"
        
        # Média diária
        dias = hoje.day
        media = total / dias if dias > 0 else 0
        response += f"\n📊 Média diária: R$ {media:.2f}"
        
        return response
    
    def _listar_despesas(self, user_id: str) -> str:
        """Lista últimas despesas"""
        despesas = [
            t for t in self.transacoes
            if t.get('user_id') == user_id and t.get('tipo') == 'saida'
        ][-10:]  # Últimas 10
        
        if not despesas:
            return "📭 Nenhuma despesa registrada."
        
        response = "💸 *Últimas Despesas:*\n\n"
        
        for d in reversed(despesas):
            data = d.get('data', '')
            valor = d.get('valor', 0)
            desc = d.get('descricao', '')[:30]
            response += f"• {data}: R$ {valor:.2f} - {desc}\n"
        
        return response
    
    def _saldo_geral(self, user_id: str) -> str:
        """Retorna saldo geral"""
        transacoes_user = [
            t for t in self.transacoes
            if t.get('user_id') == user_id
        ]
        
        entradas = sum(t.get('valor', 0) for t in transacoes_user if t.get('tipo') == 'entrada')
        saidas = sum(t.get('valor', 0) for t in transacoes_user if t.get('tipo') == 'saida')
        saldo = entradas - saidas
        
        emoji_saldo = "✅" if saldo >= 0 else "⚠️"
        
        return f"""
💰 *Resumo Financeiro*

💵 Entradas: R$ {entradas:.2f}
💸 Saídas: R$ {saidas:.2f}

{emoji_saldo} *Saldo: R$ {saldo:.2f}*
"""
    
    def _emoji_categoria(self, categoria: str) -> str:
        """Retorna emoji da categoria"""
        emojis = {
            'alimentacao': '🍔',
            'transporte': '🚗',
            'moradia': '🏠',
            'saude': '💊',
            'lazer': '🎮',
            'educacao': '📚',
            'vestuario': '👕',
            'beleza': '💇',
            'pets': '🐕',
            'tecnologia': '📱',
            'assinaturas': '📺',
            'renda': '💵',
            'outros': '📦'
        }
        return emojis.get(categoria, '📦')
