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
        
        # Configurações do recognizer
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
    
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
                # Ajusta para ruído ambiente
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio_data = self.recognizer.record(source)
            
            # Tenta transcrever em português
            try:
                texto = self.recognizer.recognize_google(
                    audio_data, 
                    language='pt-BR'
                )
                return {
                    'success': True,
                    'text': texto
                }
            except sr.UnknownValueError:
                return {
                    'success': False,
                    'error': 'Não consegui entender o áudio. Tente falar mais claramente.'
                }
            except sr.RequestError as e:
                return {
                    'success': False,
                    'error': f'Erro no serviço de reconhecimento: {str(e)}'
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
            audio = audio.set_channels(1)
            audio = audio.set_frame_rate(16000)
            
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
            return f"""
🎤 *Transcrição do Áudio:*

"{resultado['text']}"

_Processando comando..._
"""
        else:
            return f"""
❌ *Erro na Transcrição*

{resultado['error']}

💡 Dicas:
• Fale claramente e perto do microfone
• Evite ambientes com muito ruído
• Tente enviar um áudio mais curto
"""
