"""
🤖 Interpretador com HuggingFace Zero-Shot Classification
Integração com o interpretador existente para melhorar detecção de intenções
"""

import os
from typing import Dict, Optional, List
from functools import lru_cache

try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("⚠️ Transformers não instalado. Instale com: pip install transformers torch")


class InterpretadorComTransformers:
    """
    Interpretador melhorado com HuggingFace Transformers
    Combina classificação zero-shot com seu sistema existente
    """
    
    def __init__(self, usar_transformers=True):
        self.usar_transformers = usar_transformers and TRANSFORMERS_AVAILABLE
        self.classifier = None
        
        # Intenções que seu sistema reconhece
        self.intencoes = [
            'agenda',
            'tarefa', 
            'lembrete',
            'financeiro',
            'email',
            'sistema',
            'conversa'
        ]
        
        # Mapeamento de sinônimos para intenções
        self.sinonimos_intencao = {
            'agenda': ['evento', 'compromisso', 'reunião', 'encontro', 'marcação'],
            'tarefa': ['afazer', 'trabalho', 'dever', 'responsabilidade'],
            'lembrete': ['aviso', 'alerta', 'notificação', 'alarme'],
            'financeiro': ['gasto', 'despesa', 'receita', 'dinheiro', 'custa'],
            'email': ['mensagem', 'correspondência', 'mail'],
            'conversa': ['bate-papo', 'conversa', 'pergunta'],
            'sistema': ['ajuda', 'status', 'comando']
        }
        
        if self.usar_transformers:
            self._carregar_modelo()
    
    def _carregar_modelo(self):
        """Carrega modelo HuggingFace de forma lazy"""
        try:
            print("📦 Carregando modelo HuggingFace (primeira vez pode demorar)...")
            self.classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=self._get_device()
            )
            print("✅ Modelo carregado com sucesso!")
        except Exception as e:
            print(f"⚠️ Erro ao carregar modelo: {e}")
            self.usar_transformers = False
    
    @staticmethod
    def _get_device():
        """Detecta se CUDA está disponível"""
        try:
            import torch
            return 0 if torch.cuda.is_available() else -1
        except:
            return -1  # CPU
    
    @lru_cache(maxsize=1000)
    def interpretar_com_transformers(self, mensagem: str) -> Dict:
        """
        Interpreta mensagem usando zero-shot classification
        
        Args:
            mensagem: Texto a interpretar
            
        Returns:
            Dicionário com intenção e confiança
        """
        if not self.usar_transformers or self.classifier is None:
            return self._resultado_vazio(mensagem)
        
        try:
            resultado = self.classifier(
                mensagem,
                self.intencoes,
                multi_class=False,
                hypothesis_template="Este texto é sobre {}."
            )
            
            return {
                'intencao': resultado['labels'][0],
                'confianca': float(resultado['scores'][0]),
                'alternativas': list(zip(resultado['labels'], resultado['scores'])),
                'metodo': 'transformers',
                'mensagem': mensagem
            }
        except Exception as e:
            print(f"❌ Erro ao interpretar: {e}")
            return self._resultado_vazio(mensagem)
    
    def _resultado_vazio(self, mensagem: str) -> Dict:
        """Retorna resultado vazio quando classifier não está disponível"""
        return {
            'intencao': None,
            'confianca': 0.0,
            'alternativas': [],
            'metodo': 'erro',
            'mensagem': mensagem
        }
    
    def combinar_com_interpretador_local(self, 
                                        mensagem: str,
                                        resultado_local: Dict) -> Dict:
        """
        Combina resultado local com resultado Transformers
        Usa confiança combinada para decisão final
        
        Args:
            mensagem: Mensagem original
            resultado_local: Resultado do interpretador local
            
        Returns:
            Resultado combinado com melhor confiança
        """
        if not self.usar_transformers:
            return resultado_local
        
        # Obter resultado do Transformers
        resultado_tf = self.interpretar_com_transformers(mensagem)
        
        # Se ambos concordam e confiança é alta, usar
        if (resultado_local.get('intencao') == resultado_tf['intencao'] and
            resultado_local.get('confianca', 0) > 0.7 and
            resultado_tf['confianca'] > 0.7):
            
            # Combinar confiançasmedia_confianca = (resultado_local.get('confianca', 0.5) + resultado_tf['confianca']) / 2
            resultado_local['confianca'] = media_confianca
            resultado_local['metodo'] = 'combinado'
            return resultado_local
        
        # Se Transformers tem confiança muito alta, usar
        if resultado_tf['confianca'] > 0.85:
            return resultado_tf
        
        # Caso contrário, usar resultado local
        return resultado_local
    
    def obter_intenao_corrigida(self, 
                               mensagem: str,
                               intenao_usuario: Optional[str] = None) -> str:
        """
        Obtém intenção corrigida com feedback do usuário
        
        Args:
            mensagem: Mensagem interpretada
            intenao_usuario: Intenção corrigida pelo usuário
            
        Returns:
            Intenção final (corrigida ou original)
        """
        if intenao_usuario in self.intencoes:
            # Guardar feedback para futuro treinamento
            self._guardar_feedback(mensagem, intenao_usuario)
            return intenao_usuario
        
        return self.interpretar_com_transformers(mensagem)['intencao']
    
    def _guardar_feedback(self, mensagem: str, intenacao_correta: str):
        """Guarda feedback para futuro fine-tuning"""
        # Implementar persistência em arquivo ou BD
        feedback_file = 'data/feedback_interpretador.jsonl'
        
        import json
        from datetime import datetime
        
        feedback = {
            'timestamp': datetime.now().isoformat(),
            'mensagem': mensagem,
            'intenacao': intenacao_correta
        }
        
        try:
            with open(feedback_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(feedback, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"⚠️ Erro ao guardar feedback: {e}")
    
    def treinar_modelo_customizado(self, exemplos: List[tuple]):
        """
        Fine-tuning com seus dados customizados
        
        Args:
            exemplos: Lista de (mensagem, intenção)
            
        Exemplo:
            exemplos = [
                ("Tenho reunião amanhã", "agenda"),
                ("Preciso comprar leite", "tarefa"),
                ("Me lembra em 30 minutos", "lembrete")
            ]
        """
        try:
            from simpletransformers.classification import ClassificationModel
            
            print("🔄 Iniciando fine-tuning...")
            
            # Preparar dados
            train_data = [
                [msg, self.intencoes.index(intent)]
                for msg, intent in exemplos
            ]
            
            # Criar modelo customizado
            model = ClassificationModel(
                'bert',
                'bert-base-multilingual-cased',
                num_labels=len(self.intencoes),
                args={'num_train_epochs': 3}
            )
            
            # Treinar
            model.train_model(train_data)
            
            print("✅ Modelo treinado com sucesso!")
            
        except ImportError:
            print("⚠️ SimpleTransformers não instalado.")
            print("Instale com: pip install simpletransformers")


# ============ EXEMPLOS DE USO ============

def exemplo_basico():
    """Exemplo básico de uso"""
    print("\n=== Exemplo 1: Uso Básico ===\n")
    
    interpretador = InterpretadorComTransformers()
    
    mensagens = [
        "Tenho reunião amanhã às 14h",
        "Preciso comprar leite no mercado",
        "Me lembra em 30 minutos",
        "Gastei 50 reais no almoço",
        "Oi, tudo bem?",
        "Buscar email de João"
    ]
    
    for msg in mensagens:
        resultado = interpretador.interpretar_com_transformers(msg)
        print(f"📝 '{msg}'")
        print(f"   → Intenção: {resultado['intencao']}")
        print(f"   → Confiança: {resultado['confianca']:.2%}")
        print()


def exemplo_combinado():
    """Exemplo combinando com interpretador local"""
    print("\n=== Exemplo 2: Combinado (Local + Transformers) ===\n")
    
    interpretador = InterpretadorComTransformers()
    
    # Simular resultado local
    resultado_local = {
        'intencao': 'agenda',
        'confianca': 0.80,
        'parametros': {'data': '2024-12-09'}
    }
    
    mensagem = "Tenho reunião amanhã"
    resultado_combinado = interpretador.combinar_com_interpretador_local(
        mensagem, 
        resultado_local
    )
    
    print(f"Mensagem: '{mensagem}'")
    print(f"Resultado Combinado:")
    print(f"  - Intenção: {resultado_combinado['intencao']}")
    print(f"  - Confiança: {resultado_combinado['confianca']:.2%}")
    print(f"  - Método: {resultado_combinado['metodo']}")


def exemplo_feedback():
    """Exemplo com feedback do usuário"""
    print("\n=== Exemplo 3: Com Feedback ===\n")
    
    interpretador = InterpretadorComTransformers()
    
    mensagem = "Me avisa em 1 hora"
    resultado = interpretador.interpretar_com_transformers(mensagem)
    
    print(f"Mensagem: '{mensagem}'")
    print(f"Interpretação: {resultado['intencao']} ({resultado['confianca']:.2%})")
    
    # Usuário corrige
    intenacao_corrigida = interpretador.obter_intenao_corrigida(
        mensagem,
        intenacao_usuario='lembrete'
    )
    
    print(f"Intenção Corrigida: {intenacao_corrigida}")
    print("✅ Feedback guardado para futuro treinamento")


def exemplo_multiplas_opcoes():
    """Exemplo com múltiplas opções de classificação"""
    print("\n=== Exemplo 4: Múltiplas Opções ===\n")
    
    interpretador = InterpretadorComTransformers()
    
    mensagem = "Preciso lembrar de pagar a conta"
    resultado = interpretador.interpretar_com_transformers(mensagem)
    
    print(f"Mensagem: '{mensagem}'")
    print(f"\nOpções de Classificação:")
    for i, (intenacao, score) in enumerate(resultado['alternativas'], 1):
        print(f"  {i}. {intenacao}: {score:.2%}")


if __name__ == '__main__':
    print("🚀 Exemplos de Interpretador com Transformers\n")
    
    try:
        exemplo_basico()
        exemplo_combinado()
        exemplo_feedback()
        exemplo_multiplas_opcoes()
        
        print("\n✅ Todos os exemplos executados com sucesso!")
        
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        print("\nCertifique-se de instalar as dependências:")
        print("pip install transformers torch")

