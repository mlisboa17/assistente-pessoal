#!/usr/bin/env python3
"""
🚀 INTEGRAÇÃO RÁPIDA: HuggingFace com seu Interpretador
Cole isto no seu middleware/ia_interpreter.py
"""

# ============ ADICIONAR NO TOPO DO SEU ia_interpreter.py ============

# from typing import Dict, Optional, List
# import os
# 
# try:
#     from transformers import pipeline
#     TRANSFORMERS_AVAILABLE = True
# except ImportError:
#     TRANSFORMERS_AVAILABLE = False
#     print("⚠️ HuggingFace não instalado. Run: pip install transformers torch")


# ============ ADICIONAR NA CLASSE IAInterpreter ============

class IAInterpreterComTransformers:
    """
    Versão melhorada do IAInterpreter com suporte a HuggingFace
    """
    
    def __init__(self):
        # ... seu código existente ...
        self.gemini_key = os.getenv('GEMINI_API_KEY')
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.model = None
        
        # NOVO: Suporte a Transformers
        self.transformer_classifier = None
        self.usar_transformers = TRANSFORMERS_AVAILABLE
        
        if self.usar_transformers:
            self._init_transformers()
    
    def _init_transformers(self):
        """Inicializa modelo HuggingFace"""
        try:
            print("📦 Carregando modelo HuggingFace...")
            self.transformer_classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli"
            )
            print("✅ HuggingFace carregado!")
        except Exception as e:
            print(f"⚠️ Erro ao carregar HuggingFace: {e}")
            self.usar_transformers = False
    
    def interpretar(self, mensagem: str, contexto: dict = None, arquivo_dados: dict = None) -> dict:
        """
        Interpreta com suporte a HuggingFace (MELHORADO)
        """
        mensagem_lower = mensagem.lower().strip()
        
        # Se houver arquivo, processa com contexto
        if arquivo_dados:
            return self._interpretar_com_arquivo(mensagem_lower, arquivo_dados, contexto)
        
        # Primeiro tenta interpretação local (rápida)
        resultado_local = self._interpretar_local(mensagem_lower)
        
        # Se encontrou intenção com confiança alta, retorna
        if resultado_local.get('intencao') != 'desconhecido' and resultado_local.get('confianca', 0) > 0.8:
            return resultado_local
        
        # NOVO: Se confiança média/baixa, tenta Transformers
        if self.usar_transformers and resultado_local.get('confianca', 0) < 0.8:
            resultado_tf = self._interpretar_com_transformers(mensagem)
            
            # Se Transformers tem alta confiança, usa
            if resultado_tf.get('confianca', 0) > 0.75:
                return resultado_tf
            
            # Caso contrário, mescla resultados
            if resultado_local.get('intencao') == resultado_tf.get('intencao'):
                # Ambos concordam, combina confiança
                resultado_local['confianca'] = (
                    resultado_local.get('confianca', 0.5) + resultado_tf.get('confianca', 0)
                ) / 2
                resultado_local['metodo'] = 'combinado'
                return resultado_local
        
        # Se tem IA disponível, usa como último recurso
        if self.model or self.provider == 'openai':
            return self._interpretar_ia(mensagem, contexto)
        
        # Fallback
        return {
            'intencao': 'conversa',
            'acao': 'responder',
            'parametros': {},
            'confianca': 0.3,
            'resposta_direta': self._resposta_generica(mensagem)
        }
    
    def _interpretar_com_transformers(self, mensagem: str) -> dict:
        """
        Interpreta com HuggingFace Zero-Shot Classification
        """
        if not self.usar_transformers or self.transformer_classifier is None:
            return {'intencao': None, 'confianca': 0.0}
        
        try:
            intencoes = [
                'agenda', 'tarefa', 'lembrete', 'financeiro', 
                'email', 'sistema', 'conversa'
            ]
            
            resultado = self.transformer_classifier(
                mensagem,
                intencoes,
                multi_class=False,
                hypothesis_template="Este texto é sobre {}."
            )
            
            return {
                'intencao': resultado['labels'][0],
                'acao': self._mapear_acao(resultado['labels'][0]),
                'confianca': float(resultado['scores'][0]),
                'parametros': {},
                'metodo': 'transformers'
            }
        except Exception as e:
            print(f"⚠️ Erro Transformers: {e}")
            return {'intencao': None, 'confianca': 0.0}
    
    def _mapear_acao(self, intencao: str) -> str:
        """Mapeia intenção para ação padrão"""
        mapeamento = {
            'agenda': 'adicionar',
            'tarefa': 'adicionar',
            'lembrete': 'criar',
            'financeiro': 'adicionar_despesa',
            'email': 'buscar',
            'sistema': 'ajuda',
            'conversa': 'responder'
        }
        return mapeamento.get(intencao, 'desconhecido')


# ============ MODO QUICK-START (COPIE E COLE) ============

def quick_test_transformers():
    """Teste rápido do HuggingFace"""
    try:
        from transformers import pipeline
        
        print("🚀 Testando HuggingFace...")
        classifier = pipeline("zero-shot-classification", 
                            model="facebook/bart-large-mnli")
        
        mensagens = [
            "Tenho reunião amanhã",
            "Preciso comprar leite",
            "Me lembra em 30 minutos",
            "Oi, tudo bem?"
        ]
        
        for msg in mensagens:
            result = classifier(msg, 
                              ['agenda', 'tarefa', 'lembrete', 'conversa'],
                              multi_class=False)
            print(f"✅ '{msg}' → {result['labels'][0]} ({result['scores'][0]:.2%})")
        
        print("\n✅ HuggingFace funcionando!")
        
    except ImportError:
        print("❌ Instale: pip install transformers torch")


# ============ PERFORMANCE COMPARISON ============

def comparar_metodos():
    """Compara velocidade entre métodos"""
    import time
    
    mensagens = [
        "Tenho reunião amanhã às 14h",
        "Preciso comprar leite",
        "Me lembra em 30 minutos",
        "Gastei 50 reais",
        "Qual meu saldo?",
        "Buscar email de João"
    ] * 10  # Repetir para teste de performance
    
    print("\n📊 COMPARAÇÃO DE PERFORMANCE\n")
    
    # Método 1: Local (Regex)
    start = time.time()
    for msg in mensagens:
        # Simular interpretação local
        _ = msg.lower().startswith(('tenho', 'preciso', 'me lembra'))
    local_time = time.time() - start
    print(f"Local (Regex):     {local_time:.4f}s - ⭐⭐⭐⭐⭐ RÁPIDO")
    
    # Método 2: HuggingFace
    try:
        from transformers import pipeline
        classifier = pipeline("zero-shot-classification")
        
        start = time.time()
        for msg in mensagens[:6]:  # Menos para demonstração
            _ = classifier(msg, ['agenda', 'tarefa', 'lembrete', 'conversa'])
        tf_time = time.time() - start
        print(f"HuggingFace:       {tf_time:.4f}s - ⭐⭐⭐⭐ MÉDIO")
        print(f"  Vantagem: Maior acurácia em casos complexos")
        
    except ImportError:
        print("HuggingFace:       (não instalado)")
    
    print(f"\n💡 Recomendação: Use Local para rápido, HF para complexo")


# ============ INSTALAÇÃO RÁPIDA ============

def instalar_dependencias():
    """Instala dependências necessárias"""
    import subprocess
    import sys
    
    print("\n🔧 Instalando HuggingFace + PyTorch...")
    
    pacotes = [
        'transformers>=4.30.0',
        'torch>=2.0.0',
    ]
    
    for pacote in pacotes:
        print(f"  Installing {pacote}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', pacote])
    
    print("\n✅ Instalação concluída!")
    print("⚠️ IMPORTANTE: PyTorch é grande (~500MB)")
    print("Isso vai demorar alguns minutos na primeira vez")


# ============ CONFIGURAÇÃO RECOMENDADA ============

CONFIGURACAO_RECOMENDADA = {
    "usar_transformers": True,
    "modelo_transformers": "facebook/bart-large-mnli",  # Melhor acurácia
    "limiar_confianca_local": 0.8,  # Se < 80%, tenta Transformers
    "limiar_confianca_tf": 0.75,    # Se < 75%, usa outra coisa
    "cache_resultados": True,       # Cache para performance
    "gpu_disponivel": None          # Auto-detectado
}


# ============ EXEMPLO COMPLETO ============

EXEMPLO_USO = """
# 1. Instalar (primeira vez)
pip install transformers torch

# 2. Usar no seu código
from middleware.ia_interpreter import IAInterpreterComTransformers

interpretador = IAInterpreterComTransformers()

# 3. Interpretar
resultado = interpretador.interpretar("Tenho reunião amanhã às 14h")
print(resultado)
# Output: {
#     'intencao': 'agenda',
#     'acao': 'adicionar', 
#     'confianca': 0.95,
#     'metodo': 'combinado'  # Local + HuggingFace
# }

# 4. Com arquivo
resultado = interpretador.interpretar(
    "Processa esse boleto",
    arquivo_dados={'tipo': 'pdf', 'nome': 'boleto.pdf'}
)
"""


if __name__ == '__main__':
    print("="*60)
    print("🚀 INTEGRAÇÃO HuggingFace com Interpretador")
    print("="*60)
    
    print("\n1️⃣ TEST")
    quick_test_transformers()
    
    print("\n2️⃣ COMPARISON")
    comparar_metodos()
    
    print("\n3️⃣ QUICK START")
    print(EXEMPLO_USO)
    
    print("\n4️⃣ INSTALL")
    # Descomente para instalar:
    # instalar_dependencias()

