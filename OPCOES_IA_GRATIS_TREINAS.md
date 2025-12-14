# 🤖 Opções de IA Gratuitas e Treinadas para Diálogos

## 1. **Rasa** ⭐⭐⭐ (MELHOR PARA VOCÊ!)

### URL: https://github.com/RasaHQ/rasa

**O que é:**
- Framework open-source completo para chatbots conversacionais
- Treinado em NLU (Natural Language Understanding)
- Detecção automática de intenção e extração de entidades
- **Totalmente gratuito** e sem necessidade de API key

**Vantagens:**
- ✅ Intent recognition pré-treinado
- ✅ Dialogue management automático
- ✅ Extração de contexto em conversas
- ✅ Funciona offline (não precisa internet)
- ✅ Excelente documentação
- ✅ Comunidade grande

**Como usar:**
```python
from rasa_nlu.model import Interpreter

# Carregar modelo pré-treinado
interpreter = Interpreter.load("path/to/nlu_model")

# Interpretar mensagem
result = interpreter.parse("Tenho reunião amanhã às 14h")
# Retorna: 
# {
#     'intent': {'name': 'agenda', 'confidence': 0.95},
#     'entities': [
#         {'entity': 'data', 'value': 'amanhã'},
#         {'entity': 'hora', 'value': '14h'}
#     ]
# }
```

**Instalação:**
```bash
pip install rasa
```

---

## 2. **Doccano** ⭐⭐ (Para Criar Seu Próprio Dataset)

### URL: https://github.com/doccano/doccano

**O que é:**
- Ferramenta de anotação de dados colaborativa
- Permite criar datasets treinados customizados
- Interface visual para labeling de intenções e diálogos
- Open-source e 100% gratuita

**Vantagens:**
- ✅ Interface web fácil
- ✅ Suporta intent detection e slot filling
- ✅ Colaboração em equipe
- ✅ Exporta em múltiplos formatos
- ✅ Auto-labeling com IA

**Como funciona:**
1. Importa seus diálogos/mensagens
2. Anota com intenções e entidades
3. Exporta dataset treinado
4. Usa com qualquer modelo

**Use case para você:**
```
1. Importar seus diálogos de agenda
2. Anotar como "agenda", "tarefa", "lembrete"
3. Exportar dataset
4. Treinar modelo local com Rasa/HuggingFace
```

---

## 3. **HuggingFace Transformers** ⭐⭐⭐ (Modelos Pré-Treinados)

### URL: https://github.com/huggingface/transformers

**Modelos Gratuitos e Pré-Treinados:**

### A) Zero-Shot Classification (Melhor para seus casos)
```python
from transformers import pipeline

classifier = pipeline("zero-shot-classification")

result = classifier(
    "Tenho reunião amanhã às 14h",
    ["agenda", "tarefa", "lembrete", "financeiro"]
)
# Retorna: {'sequence': '...', 'labels': ['agenda'], 'scores': [0.95]}
```

### B) Intent Detection para Áudio
```python
from transformers import pipeline

# Classificação de intenção de fala
intent_detector = pipeline("audio-classification", 
                          model="superb/hubert-base-superb-ic")
```

**Modelos Recomendados:**
- `facebook/bart-large-mnli` - Classificação zero-shot
- `microsoft/deberta-base` - Melhor acurácia
- `distilbert-base-cased` - Rápido e leve

---

## 4. **Simpletransformers** ⭐⭐ (Mais Fácil que HF)

### URL: https://github.com/ThilinaRajapakse/simpletransformers

**O que é:**
- Wrapper simplificado do HuggingFace
- Fine-tuning com 3 linhas de código
- Detecção de intenção pré-treinada

**Exemplo:**
```python
from simpletransformers.classification import ClassificationModel

# Modelo pré-treinado
model = ClassificationModel('bert', 'bert-base-cased')

predictions, raw_outputs = model.predict([
    "Tenho reunião amanhã às 14h"
])

# Treinar seu próprio modelo
train_data = [
    ['Reunião amanhã', 'agenda'],
    ['Preciso comprar leite', 'tarefa'],
    ['Lembrete em 30 minutos', 'lembrete']
]

model.train_model(train_data)
```

---

## 5. **MITIE** (Minimal Information Extraction)

### URL: https://github.com/mit-nlp/MITIE

**O que é:**
- Modelo leve de extração de informações
- Sem dependências pesadas
- Funciona offline

**Use case:**
- Extrair entidades de mensagens de agenda/tarefas
- Rápido e confiável

---

## 6. **Snips NLU** (Descontinuado, mas ainda usado)

### URL: https://github.com/snipsco/snips-nlu

**Status:** Descontinuado em 2020, mas código ainda funciona
- Excelente para pequenos projetos
- Zero-shot learning
- Muito leve

---

## 🎯 RECOMENDAÇÃO PARA SEU PROJETO

### Combinação Ideal:

```python
# 1. Para classificação rápida de intenção
from transformers import pipeline

classifier = pipeline("zero-shot-classification", 
                     model="facebook/bart-large-mnli")

# 2. Para extração de entidades
from transformers import pipeline

ner = pipeline("token-classification", 
              model="dslim/bert-base-multilingual-cased-ner")

# 3. Seu interpretador atual + essa combinação
# = Solução completa e gratuita!
```

### Arquivo de Integração:

```python
"""interpretador_com_transformers.py"""

from transformers import pipeline

class InterpretadorAvancado:
    def __init__(self):
        # Classificador de intenção
        self.classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli"
        )
        
        # Extrator de entidades
        self.ner = pipeline(
            "token-classification",
            model="dslim/bert-base-multilingual-cased-ner"
        )
        
        self.intencoes = [
            "agenda", "tarefa", "lembrete", 
            "financeiro", "email", "conversa"
        ]
    
    def interpretar(self, mensagem):
        # Detectar intenção
        intent_result = self.classifier(
            mensagem, 
            self.intencoes,
            multi_class=False
        )
        
        intenção = intent_result['labels'][0]
        confiança = intent_result['scores'][0]
        
        # Extrair entidades
        entities = self.ner(mensagem)
        
        return {
            'intencao': intenção,
            'confianca': confiança,
            'entidades': entities,
            'mensagem_original': mensagem
        }

# Uso:
interpretador = InterpretadorAvancado()
resultado = interpretador.interpretar("Tenho reunião amanhã às 14h")
print(resultado)
```

---

## 📊 Comparação de Opções

| Opção | Grátis | Treinado | Offline | Fácil | Intent | Entidades |
|-------|--------|----------|---------|-------|--------|-----------|
| **Rasa** | ✅ | ✅ | ✅ | ⭐⭐ | ✅✅ | ✅✅ |
| **HF Zero-Shot** | ✅ | ✅ | ✅ | ⭐⭐⭐ | ✅✅ | ⭐ |
| **SimpleTransformers** | ✅ | ✅ | ✅ | ⭐⭐⭐ | ✅✅ | ✅ |
| **Doccano** | ✅ | ⭐ | ⭐ | ⭐⭐⭐ | - | - |
| **MITIE** | ✅ | ✅ | ✅ | ⭐⭐ | ⭐ | ✅✅ |

---

## 🚀 Instalação Rápida (Para Começar Hoje)

```bash
# Opção 1: Zero-Shot (mais rápido)
pip install transformers torch

# Opção 2: Rasa (completo)
pip install rasa

# Opção 3: SimpleTransformers (fácil)
pip install simpletransformers torch transformers
```

---

## 📚 Exemplos de Diálogos Pré-Treinados

### Encontre no HuggingFace Hub:
- `superb/hubert-base-superb-ic` - Intent Classification em áudio
- `facebook/bart-large-mnli` - Melhor classificação zero-shot
- `microsoft/deberta-v3-base` - Estado-da-arte em classificação

**Link:** https://huggingface.co/models

---

## 💡 Próximos Passos Para Seu Projeto

1. **Integrar HuggingFace Zero-Shot** (rápido, funciona com Gemini fallback)
2. **Coletar exemplos de diálogos** com seus usuários
3. **Usar Doccano** para anotar + treinar Rasa customizado
4. **Fine-tunar modelo** com seus dados específicos
5. **Deployar offline** em seu servidor

---

## 🔗 Recursos Adicionais

- [HuggingFace Hub - Modelos PT-BR](https://huggingface.co/models?language=pt&sort=downloads)
- [Rasa Docs - Intent Recognition](https://rasa.com/docs/rasa/nlu-only/)
- [Doccano - Getting Started](https://github.com/doccano/doccano#quick-start)
- [Transformers - Text Classification](https://huggingface.co/docs/transformers/tasks/sequence_classification)

---

## ✅ Checklist - Implementar Hoje

- [ ] Instalar `transformers` e `torch`
- [ ] Testar `zero-shot-classification` com suas intenções
- [ ] Integrar com seu `IAInterpreter` atual
- [ ] Coletar exemplos reais de diálogos
- [ ] Setup Doccano para dataset customizado
- [ ] Treinar modelo Rasa customizado
- [ ] Deploy em produção

