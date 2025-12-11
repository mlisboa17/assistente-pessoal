/**
 * 🤖 Moga Bot - WhatsApp
 * Assistente Pessoal Inteligente
 * Usa Baileys para conectar ao WhatsApp Web
 * Suporta: Texto, Áudio, PDF e Comprovantes
 */

const makeWASocket = require('@whiskeysockets/baileys').default;
const { useMultiFileAuthState, DisconnectReason, downloadMediaMessage } = require('@whiskeysockets/baileys');
const qrcode = require('qrcode-terminal');
const pino = require('pino');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

// Configuração do logger
const logger = pino({ level: 'silent' });

// URL do servidor Python
const PYTHON_SERVER = process.env.PYTHON_SERVER || 'http://localhost:8005';

// Pasta para salvar sessão
const AUTH_FOLDER = './auth_info';

// Pasta temporária para arquivos
const TEMP_FOLDER = './temp';
if (!fs.existsSync(TEMP_FOLDER)) {
    fs.mkdirSync(TEMP_FOLDER, { recursive: true });
}

/**
 * Carrega configuração de usuários
 */
function loadUsersConfig() {
    try {
        const configPath = './usuarios_config.json';
        if (fs.existsSync(configPath)) {
            const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
            return config.usuarios || {};
        }
    } catch (err) {
        console.warn('⚠️ Erro ao carregar usuarios_config.json:', err.message);
    }
    return {};
}

/**
 * Obtém nome do usuário pelo número
 */
function getUserNameByNumber(number) {
    const usersConfig = loadUsersConfig();
    
    // Remove @s.us ou @g.us se existir
    const cleanNumber = number.split('@')[0];
    
    // Procura na configuração
    if (usersConfig[cleanNumber]) {
        return usersConfig[cleanNumber].nome;
    }
    
    // Se não encontrar, retorna um nome padrão baseado no número
    return `Usuário ${cleanNumber.slice(-4)}`;
}

/**
 * Verifica se usuário está ativo
 */
function isUserActive(number) {
    const usersConfig = loadUsersConfig();
    const cleanNumber = number.split('@')[0];
    
    if (usersConfig[cleanNumber]) {
        return usersConfig[cleanNumber].ativo !== false;
    }
    
    return true; // Por padrão, usuários desconhecidos são ativos
}

async function connectToWhatsApp() {
    // Carrega estado de autenticação
    const { state, saveCreds } = await useMultiFileAuthState(AUTH_FOLDER);

    // Cria socket
    const sock = makeWASocket({
        auth: state,
        printQRInTerminal: false,
        logger: logger
    });

    // Evento de atualização de conexão
    sock.ev.on('connection.update', async (update) => {
        const { connection, lastDisconnect, qr } = update;

        // Mostra QR Code no terminal
        if (qr) {
            console.log('\n📱 Escaneie o QR Code abaixo com seu WhatsApp:\n');
            qrcode.generate(qr, { small: true });
            console.log('\n⏳ Aguardando conexão...\n');
        }

        if (connection === 'close') {
            const statusCode = lastDisconnect?.error?.output?.statusCode;
            const shouldReconnect = statusCode !== DisconnectReason.loggedOut;
            console.log('❌ Conexão fechada:', lastDisconnect?.error?.message, '| Status:', statusCode);
            
            if (shouldReconnect) {
                // Aguarda um pouco antes de reconectar para evitar loops
                const delay = statusCode === DisconnectReason.restartRequired ? 1000 : 3000;
                console.log(`🔄 Reconectando em ${delay/1000}s...`);
                setTimeout(() => connectToWhatsApp(), delay);
            } else {
                console.log('👋 Deslogado pelo servidor. Delete a pasta auth_info e reinicie para reconectar.');
            }
        }

        if (connection === 'open') {
            console.log('\n✅ Conectado ao WhatsApp!');
            console.log('🔐 Sessão autenticada e persistida em ./auth_info');
            console.log('🤖 Moga Bot está pronto para receber mensagens!\n');
            console.log('📝 Funcionalidades ativas:');
            console.log('   • Mensagens de texto');
            console.log('   • Áudios (transcrição automática)');
            console.log('   • Arquivos PDF (boletos/faturas)');
            console.log('   • 🆕 Comprovantes (análise com IA)\n');
        }
    });

    // Salva credenciais quando atualizar
    sock.ev.on('creds.update', saveCreds);

    // Processa mensagens recebidas
    sock.ev.on('messages.upsert', async ({ messages, type }) => {
        if (type !== 'notify') return;

        for (const msg of messages) {
            // Ignora mensagens enviadas por mim
            if (msg.key.fromMe) continue;

            const from = msg.key.remoteJid;
            const pushName = msg.pushName || 'Usuário';
            
            // Obtém nome do usuário pela configuração ou pelo pushName
            const userName = getUserNameByNumber(from) || pushName;
            
            // Verifica se usuário está ativo
            if (!isUserActive(from)) {
                console.log(`🚫 ${userName}: Usuário bloqueado`);
                continue;
            }

            try {
                // === ÁUDIO ===
                if (msg.message?.audioMessage) {
                    console.log(`🎤 ${userName}: [ÁUDIO RECEBIDO]`);
                    await sock.sendMessage(from, { text: '🎤 Transcrevendo seu áudio...' });
                    
                    // Aguarda 1 segundo para processar áudio
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    
                    const response = await processAudio(msg, from, userName);
                    await sendWithButtons(sock, from, response);
                    console.log(`📤 Resposta enviada!`);
                    continue;
                }

                // === DOCUMENTO/ARQUIVO ===
                if (msg.message?.documentMessage) {
                    const filename = msg.message.documentMessage.fileName || 'arquivo';
                    const mimetype = msg.message.documentMessage.mimetype || '';
                    const caption = msg.message.documentMessage.caption || '';
                    const isPDF = mimetype.toLowerCase().includes('pdf') || filename.toLowerCase().endsWith('.pdf');
                    
                    console.log(`📄 ${userName}: [ARQUIVO: ${filename}] Caption: "${caption}"`);
                    
                    // DETECTAR SE É EXTRATO OU TARIFAS
                    const captionLower = caption.toLowerCase();
                    const isExtrato = captionLower.includes('extrato') || 
                                      captionLower.includes('bancário') || 
                                      captionLower.includes('bancario') ||
                                      captionLower.includes('banco') ||
                                      captionLower.includes('bb') ||
                                      captionLower.includes('bradesco') ||
                                      captionLower.includes('itau') ||
                                      captionLower.includes('santander') ||
                                      captionLower.includes('caixa') ||
                                      captionLower.includes('c6');
                    
                    const isTarifas = captionLower.includes('tarifa') || 
                                      captionLower.includes('taxa') ||
                                      captionLower.includes('tarifas');
                    
                    // Extrair senha se fornecida
                    const senhaMatch = caption.match(/senha[:\s]*(\S+)/i);
                    const senha = senhaMatch ? senhaMatch[1] : null;
                    
                    // PROCESSAR EXTRATO BANCÁRIO
                    if (isExtrato && isPDF) {
                        await sock.sendMessage(from, { text: `🏦 Processando extrato bancário...\n📄 ${filename}` });
                        await sock.readMessages([msg.key]);
                        await new Promise(resolve => setTimeout(resolve, 2000));
                        
                        const response = await processExtrato(msg, from, userName, senha);
                        await sendWithButtons(sock, from, response);
                        console.log(`📤 Extrato processado!`);
                        continue;
                    }
                    
                    // PROCESSAR TARIFAS
                    if (isTarifas && isPDF) {
                        await sock.sendMessage(from, { text: `💳 Analisando tarifas...\n📄 ${filename}` });
                        await sock.readMessages([msg.key]);
                        await new Promise(resolve => setTimeout(resolve, 2000));
                        
                        const response = await processTarifas(msg, from, userName, senha);
                        await sendWithButtons(sock, from, response);
                        console.log(`📤 Tarifas analisadas!`);
                        continue;
                    }
                    
                    // PROCESSAR ARQUIVO NORMAL
                    await sock.sendMessage(from, { text: `📄 Processando arquivo: ${filename}...${isPDF ? '\n⏳ Preparando download...' : ''}` });
                    
                    if (isPDF) {
                        try {
                            console.log('🖱️ Clicando no arquivo PDF para iniciar download...');
                            await sock.readMessages([msg.key]);
                            await new Promise(resolve => setTimeout(resolve, 2000));
                            console.log('✅ Arquivo preparado para download');
                        } catch (clickError) {
                            console.log('⚠️ Erro ao simular clique, continuando com download:', clickError.message);
                        }
                    }
                    
                    const waitTime = isPDF ? 3000 : 1000;
                    await new Promise(resolve => setTimeout(resolve, waitTime));
                    
                    const response = await processFile(msg, from, userName);
                    await sendWithButtons(sock, from, response);
                    console.log(`📤 Resposta enviada!`);
                    continue;
                }

                // === IMAGEM ===
                if (msg.message?.imageMessage) {
                    const caption = msg.message.imageMessage.caption || '';
                    console.log(`🖼️ ${userName}: [IMAGEM] ${caption}`);
                    await sock.sendMessage(from, { text: '🧾 Analisando comprovante...' });
                    
                    // Aguarda 1 segundo para processar imagem
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    
                    // Processa como possível comprovante
                    const response = await processImage(msg, from, userName);
                    await sendWithButtons(sock, from, response);
                    console.log(`📤 Resposta enviada!`);
                    continue;
                }

                // === CLIQUE EM BOTÃO ===
                let buttonId = '';
                if (msg.message?.buttonsResponseMessage?.selectedButtonId) {
                    buttonId = msg.message.buttonsResponseMessage.selectedButtonId;
                    console.log(`🔘 ${userName}: Clicou no botão: ${buttonId}`);
                    
                    // Converte ID de botão em comando
                    let commandText = '';
                    switch(buttonId) {
                        case 'agenda': commandText = '/agenda'; break;
                        case 'tarefas': commandText = '/tarefas'; break;
                        case 'gastos': commandText = '/gastos'; break;
                        case 'ajuda': commandText = '/ajuda'; break;
                        case 'nova_tarefa': commandText = '/tarefa'; break;
                        case 'concluir_tarefa': commandText = '/concluir'; break;
                        case 'listar_tarefas': commandText = '/listar'; break;
                        case 'adicionar_gasto': commandText = '/gasto'; break;
                        case 'ver_gastos': commandText = '/gastos'; break;
                        case 'relatorio': commandText = '/relatorio'; break;
                        case 'sim': commandText = 'sim'; break;
                        case 'nao': commandText = 'nao'; break;
                        default: commandText = buttonId;
                    }
                    
                    const response = await processMessage(commandText, from, userName, isGroup, groupName, participantId);
                    await sendWithButtons(sock, from, response);
                    console.log(`📤 Resposta enviada!`);
                    continue;
                }

                // === TEXTO ===
                let text = '';
                if (msg.message?.conversation) {
                    text = msg.message.conversation;
                } else if (msg.message?.extendedTextMessage?.text) {
                    text = msg.message.extendedTextMessage.text;
                }

                if (!text) continue;

                // Detecta se é grupo
                const isGroup = from.endsWith('@g.us');
                const groupName = isGroup ? (msg.key.participant ? await getGroupName(sock, from) : 'Grupo') : null;
                // Para grupos, o participante é quem enviou a mensagem
                const participantId = isGroup ? (msg.key.participant || from) : from;
                
                console.log(`📩 ${userName}${isGroup ? ` [${groupName}]` : ''}: ${text}`);

                const response = await processMessage(text, from, userName, isGroup, groupName, participantId);
                await sendWithButtons(sock, from, response);
                console.log(`📤 Resposta enviada!`);

            } catch (error) {
                console.error('❌ Erro ao processar:', error.message);
                await sendWithButtons(sock, from, '❌ Desculpe, ocorreu um erro ao processar sua mensagem.');
            }
        /**
         * Envia mensagem com botões interativos
         * Suporta botões de resposta rápida e listas interativas
         */
        async function sendWithButtons(sock, to, text) {
            try {
                const lower = text.toLowerCase();
                
                // Menu principal com lista interativa
                if (lower.includes('menu principal') || lower.includes('comandos disponíveis') || lower.includes('olá! sou o moga bot')) {
                    const sections = [
                        {
                            title: '📱 Principais Funções',
                            rows: [
                                { rowId: 'agenda', title: '📅 Agenda', description: 'Ver e criar compromissos' },
                                { rowId: 'tarefas', title: '✅ Tarefas', description: 'Gerenciar lista de tarefas' },
                                { rowId: 'financas', title: '💰 Finanças', description: 'Controle de gastos' },
                                { rowId: 'emails', title: '📧 E-mails', description: 'Verificar e-mails' }
                            ]
                        },
                        {
                            title: '⚙️ Outras Opções',
                            rows: [
                                { rowId: 'ajuda', title: '❓ Ajuda', description: 'Ver todos os comandos' },
                                { rowId: 'status', title: '📊 Status', description: 'Ver status do sistema' }
                            ]
                        }
                    ];
                    
                    const listMessage = {
                        text: text,
                        footer: '🤖 Escolha uma opção abaixo',
                        title: '✨ Menu Principal',
                        buttonText: 'Ver Opções',
                        sections
                    };
                    
                    await sock.sendMessage(to, listMessage);
                    return;
                }

                // Agenda com opções de ação
                if (lower.includes('📅 agenda') || (lower.includes('compromisso') && lower.includes('opções'))) {
                    const buttons = [
                        { buttonId: 'criar_evento', buttonText: { displayText: '➕ Novo Evento' }, type: 1 },
                        { buttonId: 'ver_agenda', buttonText: { displayText: '📋 Ver Agenda' }, type: 1 },
                        { buttonId: 'proximos', buttonText: { displayText: '⏰ Próximos' }, type: 1 }
                    ];
                    
                    await sock.sendMessage(to, {
                        text: text,
                        footer: '🤖 Escolha uma ação',
                        buttons: buttons,
                        headerType: 1
                    });
                    return;
                }

                // Google Login
                if (lower.includes('conectar com google') || lower.includes('google calendar')) {
                    // Para login, apenas texto pois precisa clicar no link
                    await sock.sendMessage(to, { text });
                    return;
                }

                // Confirmação Sim/Não
                if (lower.includes('tem certeza') || lower.includes('confirmar') || lower.includes('deseja') || lower.includes('confirme')) {
                    const buttons = [
                        { buttonId: 'sim', buttonText: { displayText: '✅ Sim' }, type: 1 },
                        { buttonId: 'nao', buttonText: { displayText: '❌ Não' }, type: 1 }
                    ];
                    
                    await sock.sendMessage(to, {
                        text: text,
                        footer: '🤖 Confirme sua escolha',
                        buttons: buttons,
                        headerType: 1
                    });
                    return;
                }

                // Tarefas com lista interativa
                if (lower.includes('tarefas') && (lower.includes('gerenciar') || lower.includes('lista'))) {
                    const sections = [
                        {
                            title: '✅ Gerenciar Tarefas',
                            rows: [
                                { rowId: 'nova_tarefa', title: '➕ Nova Tarefa', description: 'Criar nova tarefa' },
                                { rowId: 'listar_tarefas', title: '📋 Listar Tarefas', description: 'Ver todas as tarefas' },
                                { rowId: 'concluir_tarefa', title: '✔️ Concluir', description: 'Marcar tarefa como concluída' },
                                { rowId: 'excluir_tarefa', title: '🗑️ Excluir', description: 'Remover tarefa' }
                            ]
                        }
                    ];
                    
                    await sock.sendMessage(to, {
                        text: text,
                        footer: '🤖 Escolha uma ação',
                        title: '✅ Tarefas',
                        buttonText: 'Ver Opções',
                        sections
                    });
                    return;
                }

                // Finanças com lista interativa
                if (lower.includes('finanças') || lower.includes('gastos') || lower.includes('despesa')) {
                    const sections = [
                        {
                            title: '💰 Controle Financeiro',
                            rows: [
                                { rowId: 'adicionar_gasto', title: '➕ Adicionar Gasto', description: 'Registrar nova despesa' },
                                { rowId: 'ver_gastos', title: '📊 Ver Gastos', description: 'Listar gastos do mês' },
                                { rowId: 'relatorio', title: '📈 Relatório', description: 'Relatório detalhado' },
                                { rowId: 'categorias', title: '🏷️ Categorias', description: 'Ver gastos por categoria' }
                            ]
                        },
                        {
                            title: '💵 Entradas',
                            rows: [
                                { rowId: 'adicionar_entrada', title: '💸 Nova Entrada', description: 'Registrar receita' },
                                { rowId: 'saldo', title: '💰 Saldo', description: 'Ver saldo atual' }
                            ]
                        }
                    ];
                    
                    await sock.sendMessage(to, {
                        text: text,
                        footer: '🤖 Escolha uma opção',
                        title: '💰 Finanças',
                        buttonText: 'Ver Opções',
                        sections
                    });
                    return;
                }

                // E-mails
                if (lower.includes('e-mail') || lower.includes('email') || lower.includes('inbox')) {
                    const buttons = [
                        { buttonId: 'ler_emails', buttonText: { displayText: '📬 Ler E-mails' }, type: 1 },
                        { buttonId: 'buscar_email', buttonText: { displayText: '🔍 Buscar' }, type: 1 },
                        { buttonId: 'nao_lidos', buttonText: { displayText: '🔔 Não Lidos' }, type: 1 }
                    ];
                    
                    await sock.sendMessage(to, {
                        text: text,
                        footer: '🤖 O que deseja fazer?',
                        buttons: buttons,
                        headerType: 1
                    });
                    return;
                }

                // Padrão: só texto
                await sock.sendMessage(to, { text });
            } catch (err) {
                console.error('❌ Erro ao enviar mensagem com botões:', err);
                // Fallback para texto simples
                try {
                    await sock.sendMessage(to, { text });
                } catch (e) {
                    console.error('❌ Erro ao enviar fallback:', e);
                }
            }
        }
        }
    });

    return sock;
}

/**
 * Obtém nome do grupo
 */
async function getGroupName(sock, groupId) {
    try {
        const metadata = await sock.groupMetadata(groupId);
        return metadata.subject || 'Grupo';
    } catch {
        return 'Grupo';
    }
}

/**
 * Processa mensagem de texto enviando para o servidor Python
 */
async function processMessage(text, userId, userName, isGroup = false, groupName = null, participantId = null) {
    try {
        const payload = {
            message: text,
            user_id: userId,
            user_name: userName,
            is_group: isGroup,
            group_name: groupName,
            participant_id: participantId || userId
        };
        
        const response = await axios.post(`${PYTHON_SERVER}/process`, payload, {
            timeout: 30000
        });

        return response.data.response || 'Não entendi. Digite /ajuda para ver os comandos.';
    } catch (error) {
        if (error.code === 'ECONNREFUSED') {
            return processLocal(text);
        }
        throw error;
    }
}

/**
 * Processa áudio - Baixa, envia para API e retorna transcrição + resposta
 * Agora com timeout e verificação de download completo
 */
async function processAudio(msg, userId, userName) {
    try {
        // Baixa o áudio com timeout
        let buffer;
        try {
            buffer = await Promise.race([
                downloadMediaMessage(msg, 'buffer', {}),
                new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('Timeout no download')), 30000)
                )
            ]);
        } catch (downloadError) {
            return '⏳ Aguardando o áudio ser processado...\n\nSe o erro persistir, tente novamente em alguns segundos.';
        }
        
        if (!buffer || buffer.length === 0) {
            return '❌ Não consegui baixar o áudio. Tente novamente.';
        }

        // Converte para base64
        const audioBase64 = buffer.toString('base64');
        const mimetype = msg.message.audioMessage.mimetype || 'audio/ogg';

        // Envia para o servidor Python
        const response = await axios.post(`${PYTHON_SERVER}/process-audio`, {
            audio: audioBase64,
            mimetype: mimetype,
            user_id: userId,
            user_name: userName
        }, {
            timeout: 60000 // Áudio pode demorar mais
        });

        return response.data.response || '❌ Erro ao processar áudio.';

    } catch (error) {
        if (error.code === 'ECONNREFUSED') {
            return '❌ Servidor Python não está rodando.\n\nInicie com: `python api_server.py`';
        }
        console.error('Erro ao processar áudio:', error.message);
        return `❌ Erro ao processar áudio. Tente novamente.`;
    }
}

/**
 * Processa arquivo (PDF) - Baixa, envia para API
 * Agora com clique simulado e melhor tratamento de download
 */
async function processFile(msg, userId, userName) {
    try {
        const filename = msg.message.documentMessage.fileName || 'arquivo';
        const mimetype = msg.message.documentMessage.mimetype || '';
        const isPDF = mimetype.toLowerCase().includes('pdf') || filename.toLowerCase().endsWith('.pdf');
        
        console.log(`📂 Iniciando download do arquivo: ${filename}`);
        
        // Baixa o arquivo com timeout e retry
        let buffer;
        let tentativas = 0;
        const max_tentativas = 3;
        const downloadTimeout = isPDF ? 90000 : 45000; // 90s para PDF, 45s outros
        
        while (tentativas < max_tentativas) {
            try {
                console.log(`⬇️ Tentativa ${tentativas + 1} de download...`);
                
                buffer = await Promise.race([
                    downloadMediaMessage(msg, 'buffer', {}),
                    new Promise((_, reject) => 
                        setTimeout(() => reject(new Error('Timeout no download')), downloadTimeout)
                    )
                ]);
                
                if (buffer && buffer.length > 0) {
                    console.log(`✅ Download concluído: ${(buffer.length / 1024).toFixed(2)} KB`);
                    break;
                }
                
                tentativas++;
                console.log(`⚠️ Buffer vazio na tentativa ${tentativas}`);
                
            } catch (err) {
                tentativas++;
                console.error(`❌ Erro na tentativa ${tentativas}:`, err.message);
                
                if (tentativas >= max_tentativas) {
                    return `⏳ *Não consegui baixar o arquivo após ${max_tentativas} tentativas*\n\n📌 *Possíveis soluções:*\n\n1. Aguarde 10 segundos\n2. Clique no arquivo para abrir/visualizar\n3. Reenvie o arquivo\n\n💡 Arquivos muito grandes podem demorar mais para processar.`;
                }
                
                // Aguarda progressivamente mais tempo entre tentativas
                const waitTime = tentativas * 2000; // 2s, 4s, 6s
                console.log(`⏱️ Aguardando ${waitTime/1000}s antes da próxima tentativa...`);
                await new Promise(r => setTimeout(r, waitTime));
            }
        }
        
        if (!buffer || buffer.length === 0) {
            return '❌ Arquivo vazio ou corrompido. Tente reenviar.';
        }

        const caption = msg.message.documentMessage.caption || '';

        // Converte para base64
        const fileBase64 = buffer.toString('base64');
        console.log(`📦 Arquivo baixado: ${(buffer.length / 1024).toFixed(2)} KB`);

        // Envia para o servidor Python com timeout maior para PDFs
        const axiosTimeout = isPDF ? 120000 : 60000;
        const response = await axios.post(`${PYTHON_SERVER}/process-file`, {
            file: fileBase64,
            filename: filename,
            mimetype: mimetype,
            caption: caption,
            user_id: userId,
            user_name: userName
        }, {
            timeout: axiosTimeout,
            maxContentLength: Infinity,
            maxBodyLength: Infinity
        });

        return response.data.response || '❌ Erro ao processar arquivo.';

    } catch (error) {
        if (error.code === 'ECONNREFUSED') {
            return '❌ Servidor Python não está rodando.\n\nInicie com: `python api_server.py`';
        }
        if (error.code === 'ETIMEDOUT' || error.message.includes('timeout')) {
            return '⏰ Tempo limite excedido ao processar arquivo.\n\nO arquivo pode ser muito grande ou complexo.\nTente enviar um arquivo menor.';
        }
        console.error('Erro ao processar arquivo:', error.message);
        return `❌ Erro ao processar arquivo: ${error.message}\n\nTente enviar novamente.`;
    }
}

/**
 * Processa EXTRATO BANCÁRIO - Sistema Zero
 */
async function processExtrato(msg, userId, userName, senha = null) {
    try {
        const filename = msg.message.documentMessage.fileName || 'extrato.pdf';
        const mimetype = msg.message.documentMessage.mimetype || 'application/pdf';
        
        console.log(`🏦 Processando EXTRATO: ${filename} (senha: ${senha ? 'SIM' : 'NÃO'})`);
        
        // Baixa o PDF com timeout maior (90 segundos)
        let buffer;
        let tentativas = 0;
        const max_tentativas = 3;
        
        while (tentativas < max_tentativas) {
            try {
                console.log(`⬇️ Tentativa ${tentativas + 1} de download do extrato...`);
                
                buffer = await Promise.race([
                    downloadMediaMessage(msg, 'buffer', {}),
                    new Promise((_, reject) => 
                        setTimeout(() => reject(new Error('Timeout no download')), 90000)
                    )
                ]);
                
                if (buffer && buffer.length > 0) {
                    console.log(`✅ Extrato baixado: ${(buffer.length / 1024).toFixed(2)} KB`);
                    break;
                }
                
                tentativas++;
            } catch (err) {
                tentativas++;
                if (tentativas >= max_tentativas) {
                    return `⏳ *Não consegui baixar o extrato após ${max_tentativas} tentativas*\n\nAguarde e tente reenviar.`;
                }
                await new Promise(r => setTimeout(r, tentativas * 2000));
            }
        }
        
        if (!buffer || buffer.length === 0) {
            return '❌ Extrato vazio ou corrompido. Tente reenviar.';
        }

        // Converte para base64
        const fileBase64 = buffer.toString('base64');

        // Envia para endpoint de extrato
        const response = await axios.post(`${PYTHON_SERVER}/process-extrato`, {
            file: fileBase64,
            filename: filename,
            senha: senha,
            user_id: userId,
            user_name: userName
        }, {
            timeout: 120000, // 2 minutos
            headers: { 'Content-Type': 'application/json' }
        });

        console.log(`✅ Extrato processado com sucesso!`);
        return response.data.response || '✅ Extrato processado!';

    } catch (error) {
        console.error('❌ Erro ao processar extrato:', error.message);
        if (error.response) {
            console.error('Resposta do servidor:', error.response.data);
            return `❌ Erro no servidor: ${error.response.data.error || error.message}`;
        }
        return `❌ Erro ao processar extrato: ${error.message}\n\nTente enviar novamente.`;
    }
}

/**
 * Processa ANÁLISE DE TARIFAS BANCÁRIAS
 */
async function processTarifas(msg, userId, userName, senha = null) {
    try {
        const filename = msg.message.documentMessage.fileName || 'tarifas.pdf';
        const mimetype = msg.message.documentMessage.mimetype || 'application/pdf';
        
        console.log(`💳 Analisando TARIFAS: ${filename} (senha: ${senha ? 'SIM' : 'NÃO'})`);
        
        // Baixa o PDF com timeout maior (90 segundos)
        let buffer;
        let tentativas = 0;
        const max_tentativas = 3;
        
        while (tentativas < max_tentativas) {
            try {
                console.log(`⬇️ Tentativa ${tentativas + 1} de download das tarifas...`);
                
                buffer = await Promise.race([
                    downloadMediaMessage(msg, 'buffer', {}),
                    new Promise((_, reject) => 
                        setTimeout(() => reject(new Error('Timeout no download')), 90000)
                    )
                ]);
                
                if (buffer && buffer.length > 0) {
                    console.log(`✅ Arquivo de tarifas baixado: ${(buffer.length / 1024).toFixed(2)} KB`);
                    break;
                }
                
                tentativas++;
            } catch (err) {
                tentativas++;
                if (tentativas >= max_tentativas) {
                    return `⏳ *Não consegui baixar o arquivo após ${max_tentativas} tentativas*\n\nAguarde e tente reenviar.`;
                }
                await new Promise(r => setTimeout(r, tentativas * 2000));
            }
        }
        
        if (!buffer || buffer.length === 0) {
            return '❌ Arquivo vazio ou corrompido. Tente reenviar.';
        }

        // Converte para base64
        const fileBase64 = buffer.toString('base64');

        // Envia para endpoint de tarifas
        const response = await axios.post(`${PYTHON_SERVER}/process-tarifas`, {
            file: fileBase64,
            filename: filename,
            senha: senha,
            user_id: userId,
            user_name: userName
        }, {
            timeout: 120000, // 2 minutos
            headers: { 'Content-Type': 'application/json' }
        });

        console.log(`✅ Tarifas analisadas com sucesso!`);
        return response.data.response || '✅ Tarifas analisadas!';

    } catch (error) {
        console.error('❌ Erro ao analisar tarifas:', error.message);
        if (error.response) {
            console.error('Resposta do servidor:', error.response.data);
            return `❌ Erro no servidor: ${error.response.data.error || error.message}`;
        }
        return `❌ Erro ao analisar tarifas: ${error.message}\n\nTente enviar novamente.`;
    }
}

/**
 * Processa imagem (comprovantes, PIX, recibos) - Baixa, envia para API
 * Agora com melhor tratamento de download e delays
 */
async function processImage(msg, userId, userName) {
    try {
        // Aguarda 1 segundo para imagem ser processada pelo WhatsApp
        console.log('⏳ Aguardando 1s para imagem ser processada pelo WhatsApp...');
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Baixa a imagem com timeout
        let buffer;
        try {
            buffer = await Promise.race([
                downloadMediaMessage(msg, 'buffer', {}),
                new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('Timeout no download')), 40000)
                )
            ]);
        } catch (downloadError) {
            console.error('Erro no download:', downloadError.message);
            return '⏳ A imagem ainda está sendo processada pelo WhatsApp.\n\n📌 Por favor, aguarde 5 segundos e reenvie a imagem.';
        }
        
        if (!buffer || buffer.length === 0) {
            return '❌ Imagem vazia ou corrompida. Tente reenviar.';
        }

        const mimetype = msg.message.imageMessage.mimetype || 'image/jpeg';
        const caption = msg.message.imageMessage.caption || '';

        // Converte para base64
        const imageBase64 = buffer.toString('base64');
        console.log(`🖼️ Imagem baixada: ${(buffer.length / 1024).toFixed(2)} KB`);

        // Envia para o servidor Python (mesmo endpoint de arquivo)
        const response = await axios.post(`${PYTHON_SERVER}/process-file`, {
            file: imageBase64,
            filename: 'comprovante.jpg',
            mimetype: mimetype,
            caption: caption,
            user_id: userId,
            user_name: userName
        }, {
            timeout: 90000,
            maxContentLength: Infinity,
            maxBodyLength: Infinity
        });

        return response.data.response || '❌ Erro ao processar imagem.';

    } catch (error) {
        if (error.code === 'ECONNREFUSED') {
            return '❌ Servidor Python não está rodando.\n\nInicie com: `python api_server.py`';
        }
        if (error.code === 'ETIMEDOUT' || error.message.includes('timeout')) {
            return '⏰ Tempo limite excedido ao processar imagem.\n\nTente enviar uma imagem de menor qualidade.';
        }
        console.error('Erro ao processar imagem:', error.message);
        return `❌ Erro ao processar imagem: ${error.message}\n\nTente novamente.`;
    }
}

/**
 * Processamento local simples (fallback)
 */
function processLocal(text) {
    const cmd = text.toLowerCase().trim();

    if (cmd === '/start' || cmd === 'oi' || cmd === 'olá' || cmd === 'ola') {
        return `🤖 *Olá! Sou o Moga Bot!*

Seu Assistente Pessoal Inteligente.

Posso ajudar você com:
📅 Agenda e lembretes
💰 Controle de gastos
✅ Lista de tarefas
📄 Processar boletos (PDF)
🧾 Analisar comprovantes
🎤 Comandos por áudio

*Comandos disponíveis:*
/ajuda - Ver todos os comandos
/tarefas - Gerenciar tarefas
/gastos - Ver resumo financeiro
/agenda - Ver compromissos

💡 Use linguagem natural!
Ex: "Me lembra de pagar a conta amanhã"
🎤 Também aceito áudios!`;
    }

    if (cmd === '/ajuda' || cmd === 'ajuda') {
        return `📋 *Comandos Disponíveis:*

*Tarefas:*
/tarefas - Lista suas tarefas
/tarefa [texto] - Adiciona tarefa
/concluir [id] - Conclui tarefa

*Finanças:*
/gastos - Resumo de gastos
/saldo - Ver saldo
Ou diga: "Gastei 50 no mercado"

*Agenda:*
/agenda - Ver compromissos
/lembrete [texto] - Criar lembrete

*Boletos:*
📄 Envie um PDF de boleto
Eu extraio código de barras e vencimento!

*Áudio:*
🎤 Envie um áudio com seu comando
Eu transcrevo e executo!

*Outros:*
/status - Status do sistema

💡 Use linguagem natural!
Ex: "Me lembra de pagar a conta amanhã"`;
    }

    return `🤖 Recebi sua mensagem: "${text}"

⚠️ Para funcionar completamente, inicie o servidor Python:
\`python api_server.py\`

Ou digite /ajuda para ver os comandos básicos.`;
}

// Banner inicial
console.log(`
╔══════════════════════════════════════════════════╗
║     🤖 MOGA BOT - WHATSAPP                       ║
║                                                  ║
║  🎤 Áudio: Transcrição automática               ║
║  📄 PDF: Extração de boletos                    ║
║  🧾 Comprovantes: Análise com IA                ║
║  💬 Texto: Linguagem natural                    ║
║                                                  ║
║  Servidor: ${PYTHON_SERVER.padEnd(30)}║
╚══════════════════════════════════════════════════╝
`);

// Inicia conexão
connectToWhatsApp();
