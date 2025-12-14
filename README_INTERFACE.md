# 🌐 Interface Web - Assistente Pessoal

## Visão Geral

A interface web do Assistente Pessoal oferece uma experiência bonita e intuitiva para gerenciar extratos bancários, categorizar transações e visualizar dados financeiros de forma organizada.

## 🚀 Funcionalidades Principais

### 📊 Dashboard
- **Visão Geral**: Cards com estatísticas principais (extratos processados, entradas, saídas, saldo)
- **Bancos Suportados**: Visualização gráfica dos 5 bancos atualmente suportados
- **Ações Rápidas**: Botões para upload de extratos e revisão de categorias

### 📝 Revisão de Categorias
- **Tabela Interativa**: Lista todas as transações com filtros avançados
- **Edição Individual**: Modal para editar transações (data, descrição, valor, categoria)
- **Categorização em Massa**: Seleção múltipla e aplicação de categorias
- **Nova Categoria**: Criação de categorias personalizadas
- **Filtros Inteligentes**: Por tipo, categoria, período e texto
- **Estatísticas em Tempo Real**: Contadores atualizados dinamicamente

### 📤 Upload de Extratos
- **Suporte Multi-Banco**: Upload de PDFs de diferentes bancos
- **Proteção por Senha**: Suporte a arquivos protegidos
- **Processamento Automático**: Extração e normalização automática

## 🎨 Design e UX

### Tema Visual
- **Gradientes Modernos**: Cores vibrantes com gradientes suaves
- **Cards Elevados**: Sombras e efeitos de hover para profundidade
- **Tipografia Clara**: Fontes legíveis e hierarquia bem definida
- **Ícones Expressivos**: Font Awesome para melhor compreensão visual

### Responsividade
- **Mobile-First**: Design adaptável para dispositivos móveis
- **Sidebar Colapsível**: Navegação otimizada para telas pequenas
- **Botões Adaptáveis**: Grupos de botões que se ajustam ao tamanho da tela

### Interatividade
- **Animações Suaves**: Transições CSS para melhor experiência
- **Feedback Visual**: Cores e ícones para indicar estados
- **Modais Elegantes**: Diálogos com design moderno
- **Loading States**: Indicadores de progresso durante operações

## 🛠️ Tecnologias Utilizadas

### Backend
- **Flask**: Framework web Python
- **Jinja2**: Templates dinâmicos
- **REST API**: Endpoints para operações CRUD

### Frontend
- **Bootstrap 5**: Framework CSS responsivo
- **Font Awesome**: Biblioteca de ícones
- **Vanilla JavaScript**: Interatividade sem frameworks pesados
- **CSS Custom**: Estilos personalizados para branding

### Funcionalidades Técnicas
- **Filtros Dinâmicos**: Busca e filtragem em tempo real
- **Validação de Formulários**: Verificação de dados no frontend
- **AJAX**: Requisições assíncronas para melhor performance
- **Local Storage**: Persistência de preferências do usuário

## 📱 Como Usar

### 1. Acessar o Dashboard
```
http://localhost:5001/
```

### 2. Upload de Extrato
1. Clique em "Upload Extrato" no dashboard
2. Selecione o banco de origem
3. Escolha o arquivo PDF
4. Digite a senha se necessário
5. Clique em "Processar"

### 3. Revisar Categorias
1. Acesse "Revisão Categorias" no menu lateral
2. Use os filtros para encontrar transações específicas
3. Clique no ícone de edição para modificar transações
4. Use "Nova Categoria" para criar categorias personalizadas
5. Selecione múltiplas transações para categorização em massa
6. Clique em "Salvar e Integrar" quando finalizar

## 🎯 Recursos Avançados

### Filtros Inteligentes
- **Por Tipo**: Crédito/Débito
- **Por Categoria**: Todas as categorias disponíveis
- **Por Período**: Intervalo de datas
- **Por Texto**: Busca na descrição das transações

### Edição de Transações
- **Campos Editáveis**: Data, tipo, descrição, valor, categoria
- **Validação**: Verificação de formato e consistência
- **Preview**: Visualização das alterações antes de salvar

### Gestão de Categorias
- **Criação**: Adicionar novas categorias personalizadas
- **Padronização**: Lista de categorias pré-definidas
- **Validação**: Evita duplicatas e nomes inválidos

### Estatísticas em Tempo Real
- **Contadores Dinâmicos**: Atualização automática
- **Progresso Visual**: Barras de progresso para categorização
- **Alertas**: Notificações de ações importantes

## 🔧 Configuração e Desenvolvimento

### Iniciar o Servidor
```bash
python api_server.py
```

### Acessar a Interface
- **URL**: http://localhost:5001
- **Dashboard**: http://localhost:5001/
- **Revisão**: http://localhost:5001/revisao-categorias
- **Upload**: http://localhost:5001/upload-extrato

### Estrutura de Arquivos
```
templates/
├── base.html          # Layout base com sidebar
├── dashboard.html     # Página inicial
├── revisao_categorias.html  # Interface principal
└── upload_extrato.html     # Upload de arquivos

static/
└── style.css         # Estilos personalizados
```

## 🚀 Próximas Melhorias

- [ ] Gráficos interativos com Chart.js
- [ ] Exportação de relatórios em PDF
- [ ] Tema escuro/claro
- [ ] Notificações push
- [ ] Integração com APIs bancárias
- [ ] Dashboard personalizado por usuário
- [ ] Histórico de alterações
- [ ] Backup e restauração de dados

## 📞 Suporte

Para dúvidas ou sugestões sobre a interface web, consulte a documentação principal do projeto ou abra uma issue no repositório.</content>
<parameter name="filePath">c:\Users\gabri\OneDrive\Área de Trabalho\Projetos\assistente-pessoal-main\README_INTERFACE.md