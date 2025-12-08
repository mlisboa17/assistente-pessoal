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
                    const response = await processAudio(msg, from, userName);
                    await sendWithButtons(sock, from, response);
                    console.log(`📤 Resposta enviada!`);
                    continue;
                }

                // === DOCUMENTO/ARQUIVO ===
                if (msg.message?.documentMessage) {
                    const filename = msg.message.documentMessage.fileName || 'arquivo';
                    const mimetype = msg.message.documentMessage.mimetype || '';
                    console.log(`📄 ${userName}: [ARQUIVO: ${filename}]`);
                    await sock.sendMessage(from, { text: `📄 Processando arquivo: ${filename}...` });
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
         * Envia mensagem com botões usando template (ButtonMessage)
         * Este é o formato que realmente funciona no WhatsApp Web
         */
        async function sendWithButtons(sock, to, text) {
            try {
                const lower = text.toLowerCase();
                
                // Menu principal
                if (lower.includes('menu principal') || lower.includes('comandos disponíveis') || lower.includes('olá! sou o moga bot')) {
                    await sock.sendMessage(to, {
                        text: text,
                        buttons: [
                            { buttonId: 'agenda', buttonText: { displayText: '📅 Agenda' }, type: 1 },
                            { buttonId: 'tarefas', buttonText: { displayText: '✅ Tarefas' }, type: 1 },
                            { buttonId: 'gastos', buttonText: { displayText: '💰 Finanças' }, type: 1 },
                            { buttonId: 'ajuda', buttonText: { displayText: '❓ Ajuda' }, type: 1 }
                        ],
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
                    await sock.sendMessage(to, {
                        text: text,
                        buttons: [
                            { buttonId: 'sim', buttonText: { displayText: '✅ Sim' }, type: 1 },
                            { buttonId: 'nao', buttonText: { displayText: '❌ Não' }, type: 1 }
                        ],
                        headerType: 1
                    });
                    return;
                }

                // Tarefas
                if (lower.includes('tarefas') && (lower.includes('criar') || lower.includes('nova') || lower.includes('adicionar'))) {
                    await sock.sendMessage(to, {
                        text: text,
                        buttons: [
                            { buttonId: 'nova_tarefa', buttonText: { displayText: '✨ Nova Tarefa' }, type: 1 },
                            { buttonId: 'concluir_tarefa', buttonText: { displayText: '✅ Concluir' }, type: 1 },
                            { buttonId: 'listar_tarefas', buttonText: { displayText: '📋 Listar' }, type: 1 }
                        ],
                        headerType: 1
                    });
                    return;
                }

                // Finanças
                if (lower.includes('finanças') || lower.includes('gastos') || lower.includes('despesa')) {
                    await sock.sendMessage(to, {
                        text: text,
                        buttons: [
                            { buttonId: 'adicionar_gasto', buttonText: { displayText: '➕ Adicionar' }, type: 1 },
                            { buttonId: 'ver_gastos', buttonText: { displayText: '📊 Ver' }, type: 1 },
                            { buttonId: 'relatorio', buttonText: { displayText: '📈 Relatório' }, type: 1 }
                        ],
                        headerType: 1
                    });
                    return;
                }

                // Padrão: só texto
                await sock.sendMessage(to, { text });
            } catch (err) {
                console.error('❌ Erro ao enviar mensagem:', err);
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
 */
async function processAudio(msg, userId, userName) {
    try {
        // Baixa o áudio
        const buffer = await downloadMediaMessage(msg, 'buffer', {});
        
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
        return `❌ Erro ao processar áudio: ${error.message}`;
    }
}

/**
 * Processa arquivo (PDF) - Baixa, envia para API
 */
async function processFile(msg, userId, userName) {
    try {
        // Baixa o arquivo
        const buffer = await downloadMediaMessage(msg, 'buffer', {});
        
        if (!buffer || buffer.length === 0) {
            return '❌ Não consegui baixar o arquivo. Tente novamente.';
        }

        const filename = msg.message.documentMessage.fileName || 'arquivo';
        const mimetype = msg.message.documentMessage.mimetype || '';
        const caption = msg.message.documentMessage.caption || '';

        // Converte para base64
        const fileBase64 = buffer.toString('base64');

        // Envia para o servidor Python
        const response = await axios.post(`${PYTHON_SERVER}/process-file`, {
            file: fileBase64,
            filename: filename,
            mimetype: mimetype,
            caption: caption,
            user_id: userId,
            user_name: userName
        }, {
            timeout: 60000
        });

        return response.data.response || '❌ Erro ao processar arquivo.';

    } catch (error) {
        if (error.code === 'ECONNREFUSED') {
            return '❌ Servidor Python não está rodando.\n\nInicie com: `python api_server.py`';
        }
        console.error('Erro ao processar arquivo:', error.message);
        return `❌ Erro ao processar arquivo: ${error.message}`;
    }
}

/**
 * Processa imagem (comprovantes, PIX, recibos) - Baixa, envia para API
 */
async function processImage(msg, userId, userName) {
    try {
        // Baixa a imagem
        const buffer = await downloadMediaMessage(msg, 'buffer', {});
        
        if (!buffer || buffer.length === 0) {
            return '❌ Não consegui baixar a imagem. Tente novamente.';
        }

        const mimetype = msg.message.imageMessage.mimetype || 'image/jpeg';
        const caption = msg.message.imageMessage.caption || '';

        // Converte para base64
        const imageBase64 = buffer.toString('base64');

        // Envia para o servidor Python (mesmo endpoint de arquivo)
        const response = await axios.post(`${PYTHON_SERVER}/process-file`, {
            file: imageBase64,
            filename: 'comprovante.jpg',
            mimetype: mimetype,
            caption: caption,
            user_id: userId,
            user_name: userName
        }, {
            timeout: 60000
        });

        return response.data.response || '❌ Erro ao processar imagem.';

    } catch (error) {
        if (error.code === 'ECONNREFUSED') {
            return '❌ Servidor Python não está rodando.\n\nInicie com: `python api_server.py`';
        }
        console.error('Erro ao processar imagem:', error.message);
        return `❌ Erro ao processar imagem: ${error.message}`;
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
