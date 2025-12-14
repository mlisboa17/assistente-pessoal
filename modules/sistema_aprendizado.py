"""
🧠 Sistema de Aprendizado para Categorização de Despesas
Aprende com descrições de extratos para sugerir categorias automaticamente
Evita repetição de categorização manual
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional
from collections import defaultdict


class SistemaAprendizado:
    """Sistema que aprende categorias baseadas em descrições"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.aprendizado_file = os.path.join(data_dir, "aprendizado_categorias.json")
        self._carregar_aprendizado()

    def _carregar_aprendizado(self):
        """Carrega o aprendizado salvo"""
        if os.path.exists(self.aprendizado_file):
            try:
                with open(self.aprendizado_file, 'r', encoding='utf-8') as f:
                    self.aprendizado = json.load(f)
            except:
                self.aprendizado = {}
        else:
            self.aprendizado = {}

        # Garante estrutura
        if 'descricoes' not in self.aprendizado:
            self.aprendizado['descricoes'] = {}
        if 'estatisticas' not in self.aprendizado:
            self.aprendizado['estatisticas'] = defaultdict(int)

    def _salvar_aprendizado(self):
        """Salva o aprendizado"""
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.aprendizado_file, 'w', encoding='utf-8') as f:
            # Converte defaultdict para dict normal
            dados_salvar = dict(self.aprendizado)
            dados_salvar['estatisticas'] = dict(self.aprendizado['estatisticas'])
            json.dump(dados_salvar, f, indent=2, ensure_ascii=False)

    def aprender_categoria(self, descricao: str, categoria: str, confianca: float = 1.0):
        """Aprende uma nova associação descrição -> categoria"""
        desc_lower = descricao.lower().strip()

        # Salva a associação
        self.aprendizado['descricoes'][desc_lower] = {
            'categoria': categoria,
            'confianca': confianca,
            'ultima_atualizacao': str(datetime.now())
        }

        # Atualiza estatísticas
        self.aprendizado['estatisticas'][categoria] += 1

        self._salvar_aprendizado()

    def sugerir_categoria_aprendida(self, descricao: str) -> Optional[Dict[str, Any]]:
        """Sugere categoria baseada no aprendizado"""
        desc_lower = descricao.lower().strip()

        # Busca exata
        if desc_lower in self.aprendizado['descricoes']:
            dados = self.aprendizado['descricoes'][desc_lower]
            return {
                'categoria': dados['categoria'],
                'confianca': dados['confianca'],
                'fonte': 'aprendizado'
            }

        # Busca por similaridade (palavras-chave)
        palavras_descricao = set(desc_lower.split())
        melhor_match = None
        melhor_score = 0

        for desc_salva, dados in self.aprendizado['descricoes'].items():
            palavras_salva = set(desc_salva.split())
            intersecao = palavras_descricao & palavras_salva
            if intersecao:
                score = len(intersecao) / len(palavras_descricao)
                if score > melhor_score and score > 0.5:  # Pelo menos 50% das palavras
                    melhor_score = score
                    melhor_match = dados

        if melhor_match:
            return {
                'categoria': melhor_match['categoria'],
                'confianca': melhor_match['confianca'] * melhor_score,
                'fonte': 'aprendizado_similar'
            }

        return None

    def get_estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas do aprendizado"""
        return {
            'total_descricoes': len(self.aprendizado['descricoes']),
            'categorias_aprendidas': dict(self.aprendizado['estatisticas']),
            'aprendizado': self.aprendizado
        }

    def limpar_aprendizado(self):
        """Limpa todo o aprendizado (cuidado!)"""
        self.aprendizado = {'descricoes': {}, 'estatisticas': defaultdict(int)}
        self._salvar_aprendizado()


# Instância global
sistema_aprendizado = SistemaAprendizado()