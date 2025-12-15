/**
 * 📱 Bot WhatsApp - Assistente Pessoal
 * Usa Baileys para conectar ao WhatsApp Web
 */

const makeWASocket = require('@whiskeysockets/baileys').default;
const { useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys');
const qrcode = require('qrcode-terminal');
const pino = require('pino');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

// Configuração do logger
const logger = pino({ level: 'silent' });

// URL do servidor Python (vamos criar)
const PYTHON_SERVER = 'http://localhost:5501';

// Pasta para salvar sessão
const AUTH_FOLDER = './auth_info';

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
            const shouldReconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
            console.log('❌ Conexão fechada:', lastDisconnect?.error?.message);
            
            if (shouldReconnect) {
                console.log('🔄 Reconectando...');
                connectToWhatsApp();
            } else {
                console.log('👋 Deslogado. Delete a pasta auth_info e reinicie para reconectar.');
            }
        }

        if (connection === 'open') {
            console.log('\n✅ Conectado ao WhatsApp!');
            console.log('🤖 Bot está pronto para receber mensagens!\n');
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

            // Ignora mensagens de grupo (opcional - pode remover)
            // if (msg.key.remoteJid.endsWith('@g.us')) continue;

            const from = msg.key.remoteJid;
            const pushName = msg.pushName || 'Usuário';

            // Extrai texto da mensagem
            let text = '';
            if (msg.message?.conversation) {
                text = msg.message.conversation;
            } else if (msg.message?.extendedTextMessage?.text) {
                text = msg.message.extendedTextMessage.text;
            } else if (msg.message?.audioMessage) {
                // Áudio - por enquanto só avisa
                text = '[AUDIO]';
            } else if (msg.message?.imageMessage) {
                text = msg.message.imageMessage.caption || '[IMAGEM]';
            }

            if (!text) continue;

            console.log(`📩 ${pushName}: ${text}`);

            try {
                // Envia para o servidor Python processar
                const response = await processMessage(text, from, pushName);
                
                // Responde no WhatsApp
                await sock.sendMessage(from, { text: response });
                console.log(`📤 Resposta enviada!`);
            } catch (error) {
                console.error('❌ Erro ao processar:', error.message);
                await sock.sendMessage(from, { 
                    text: '❌ Desculpe, ocorreu um erro ao processar sua mensagem.' 
                });
            }
        }
    });

    return sock;
}

/**
 * Processa mensagem enviando para o servidor Python
 */
async function processMessage(text, userId, userName) {
    try {
        const response = await axios.post(`${PYTHON_SERVER}/process`, {
            message: text,
            user_id: userId,
            user_name: userName
        }, {
            timeout: 30000
        });

        return response.data.response || 'Não entendi. Digite /ajuda para ver os comandos.';
    } catch (error) {
        // Se servidor Python não estiver rodando, processa localmente
        if (error.code === 'ECONNREFUSED') {
            return processLocal(text);
        }
        throw error;
    }
}

/**
 * Processamento local simples (fallback)
 */
function processLocal(text) {
    const cmd = text.toLowerCase().trim();

    if (cmd === '/start' || cmd === 'oi' || cmd === 'olá' || cmd === 'ola') {
        return `🤖 *Olá! Sou seu Assistente Pessoal!*

Posso ajudar você com:
📅 Agenda e lembretes
💰 Controle de gastos
✅ Lista de tarefas
📧 E-mails

*Comandos disponíveis:*
/ajuda - Ver todos os comandos
/tarefas - Gerenciar tarefas
/gastos - Ver resumo financeiro
/agenda - Ver compromissos

Ou simplesmente me diga o que precisa!`;
    }

    if (cmd === '/ajuda' || cmd === 'ajuda') {
        return `📋 *Comandos Disponíveis:*

*Tarefas:*
/tarefas - Lista suas tarefas
/tarefa [texto] - Adiciona tarefa

*Finanças:*
/gastos - Resumo de gastos
/despesas [valor] [desc] - Registra gasto
/entrada [valor] [desc] - Registra entrada
/saldo - Ver saldo

*Agenda:*
/agenda - Ver compromissos
/lembrete [texto] - Criar lembrete

*Outros:*
/status - Status do sistema
/ajuda - Esta mensagem

💡 Você também pode usar linguagem natural!
Ex: "Gastei 50 reais no mercado"`;
    }

    return `🤖 Recebi sua mensagem: "${text}"

Para o bot funcionar completamente, inicie o servidor Python:
\`python api_server.py\`

Ou digite /ajuda para ver os comandos básicos.`;
}

// Banner inicial
console.log(`
╔══════════════════════════════════════════════════╗
║     📱 ASSISTENTE PESSOAL - WHATSAPP BOT        ║
║                                                  ║
║  Usando: Baileys (WhatsApp Web)                 ║
║  Servidor: ${PYTHON_SERVER}                    ║
╚══════════════════════════════════════════════════╝
`);

// Inicia conexão
connectToWhatsApp();
