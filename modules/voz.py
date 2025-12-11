"""
🎤 Módulo de Voz
Reconhecimento de áudio e transcrição para texto
"""
import os
import tempfile
from typing import Optional, Any
import speech_recognition as sr
from pydub import AudioSegment


class VozModule:
    """Módulo de reconhecimento de voz"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.recognizer = sr.Recognizer()
        self.temp_dir = os.path.join(data_dir, "audio_temp")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Configurações otimizadas do recognizer
        self.recognizer.energy_threshold = 200  # Mais sensível
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8  # Pausa entre palavras
        self.recognizer.phrase_threshold = 0.3  # Threshold de frase
        self.recognizer.non_speaking_duration = 0.5  # Duração de não-fala
    
    async def handle(self, command: str, args: list, 
                     user_id: str, attachments: list = None) -> str:
        """Processa comandos de voz"""
        
        if command == 'voz':
            return """
🎤 *Módulo de Voz*

Envie um áudio e eu vou transcrever para texto!

Formatos suportados:
• Áudio do Telegram (voz)
• Arquivos de áudio (.ogg, .mp3, .wav)

A transcrição será processada automaticamente.
"""
        
        return "🎤 Envie um áudio para transcrever."
    
    async def handle_natural(self, message: str, analysis: Any,
                              user_id: str, attachments: list = None) -> str:
        """Processa linguagem natural sobre voz"""
        return await self.handle('voz', [], user_id, attachments)
    
    async def transcrever_audio(self, audio_path: str, formato: str = "ogg") -> dict:
        """
        Transcreve um arquivo de áudio para texto
        
        Args:
            audio_path: Caminho para o arquivo de áudio
            formato: Formato do áudio (ogg, mp3, wav)
            
        Returns:
            dict com 'success', 'text' ou 'error'
        """
        wav_path = None
        
        try:
            # Converte para WAV se necessário (speech_recognition só aceita WAV)
            if formato.lower() != 'wav':
                wav_path = await self._converter_para_wav(audio_path, formato)
            else:
                wav_path = audio_path
            
            if not wav_path or not os.path.exists(wav_path):
                return {
                    'success': False,
                    'error': 'Erro ao converter áudio'
                }
            
            # Transcreve usando Google Speech Recognition (gratuito)
            with sr.AudioFile(wav_path) as source:
                # Ajusta para ruído ambiente (tempo maior para melhor calibração)
                self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
                audio_data = self.recognizer.record(source)
            
            # Tenta transcrever em português com opções alternativas
            try:
                # Primeira tentativa: português do Brasil
                texto = self.recognizer.recognize_google(
                    audio_data, 
                    language='pt-BR',
                    show_all=False  # Apenas melhor resultado
                )
                return {
                    'success': True,
                    'text': texto,
                    'confidence': 'alta'
                }
            except sr.UnknownValueError:
                # Segunda tentativa: com show_all para pegar alternativas
                try:
                    resultado_completo = self.recognizer.recognize_google(
                        audio_data, 
                        language='pt-BR',
                        show_all=True
                    )
                    if resultado_completo and 'alternative' in resultado_completo:
                        melhor_alternativa = resultado_completo['alternative'][0]
                        if 'transcript' in melhor_alternativa:
                            return {
                                'success': True,
                                'text': melhor_alternativa['transcript'],
                                'confidence': 'baixa'
                            }
                except:
                    pass
                
                return {
                    'success': False,
                    'error': '🎤 Não consegui entender o áudio.\n\n💡 *Dicas:*\n• Fale mais devagar e claramente\n• Reduza ruído de fundo\n• Aproxime-se do microfone'
                }
            except sr.RequestError as e:
                return {
                    'success': False,
                    'error': f'❌ Erro no serviço de reconhecimento.\n\n🔧 Detalhes técnicos: {str(e)}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Erro ao processar áudio: {str(e)}'
            }
        finally:
            # Limpa arquivo temporário
            if wav_path and wav_path != audio_path and os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                except:
                    pass
    
    async def _converter_para_wav(self, audio_path: str, formato: str) -> Optional[str]:
        """Converte áudio para WAV usando pydub"""
        try:
            # Carrega o áudio
            if formato.lower() == 'ogg':
                audio = AudioSegment.from_ogg(audio_path)
            elif formato.lower() == 'mp3':
                audio = AudioSegment.from_mp3(audio_path)
            elif formato.lower() == 'oga':
                audio = AudioSegment.from_ogg(audio_path)
            elif formato.lower() == 'm4a':
                audio = AudioSegment.from_file(audio_path, format='m4a')
            else:
                audio = AudioSegment.from_file(audio_path)
            
            # Converte para mono e 16kHz (melhor para speech recognition)
            audio = audio.set_channels(1)  # Mono
            audio = audio.set_frame_rate(16000)  # 16kHz
            audio = audio.set_sample_width(2)  # 16-bit
            
            # Normaliza volume (melhora reconhecimento)
            audio = audio.normalize()
            
            # Remove silêncio do início e fim
            audio = audio.strip_silence(silence_thresh=-50, padding=100)
            
            # Salva como WAV
            wav_path = os.path.join(
                self.temp_dir, 
                f"audio_{os.path.basename(audio_path)}.wav"
            )
            audio.export(wav_path, format='wav')
            
            return wav_path
            
        except Exception as e:
            print(f"Erro ao converter áudio: {e}")
            return None
    
    def formatar_resposta_transcricao(self, resultado: dict) -> str:
        """Formata a resposta da transcrição"""
        if resultado['success']:
            confianca = resultado.get('confidence', 'alta')
            icon_confianca = "🟢" if confianca == 'alta' else "🟡"
            
            return f"""
🎤 *Transcrição do Áudio:*

"{resultado['text']}"

{icon_confianca} Confiança: {confianca}
_Processando comando..._
"""
        else:
            return f"""
❌ *Erro na Transcrição*

{resultado['error']}

💡 *Sugestões para melhorar:*
• 🗣️ Fale claramente e pausadamente
• 🔇 Reduza ruído de fundo
• 📱 Aproxime o celular da boca
• ⏱️ Envie áudios de 3-30 segundos
• 🔊 Aumente o volume da gravação
"""
