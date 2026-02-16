import os
import threading
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import mainthread
from kivy.properties import StringProperty, NumericProperty
import speech_recognition as sr
from pydub import AudioSegment
from pydub.utils import make_chunks

class MainScreen(Screen):
    def on_enter(self):
        # Escaneo automático de la carpeta de descargas
        folder = "/sdcard/Download/"
        if os.path.exists(folder):
            files = [f for f in os.listdir(folder) if f.endswith(('.m4a', '.mp3', '.wav'))]
            # Lógica para mostrar archivos en la UI de Stitch

class ProcessingScreen(Screen):
    progress_val = NumericProperty(0)
    status_text = StringProperty("INICIANDO MOTOR NEURAL...")
    segment_text = StringProperty("SEGMENTO 0 DE 0")

    def iniciar_proceso(self, path):
        threading.Thread(target=self.worker, args=(path,), daemon=True).start()

    def worker(self, path):
        try:
            audio = AudioSegment.from_file(path)
            chunks = make_chunks(audio, 30000) # Segmentos de 30 seg
            total = len(chunks)
            full_text = ""
            rec = sr.Recognizer()

            for i, chunk in enumerate(chunks):
                self.update_status(i + 1, total)
                temp = f"temp_{i}.wav"
                chunk.export(temp, format="wav")
                with sr.AudioFile(temp) as source:
                    audio_data = rec.record(source)
                    try:
                        text = rec.recognize_google(audio_data, language="es-ES")
                        full_text += text + " "
                    except: pass
                if os.path.exists(temp): os.remove(temp)
            
            self.finalizar(full_text)
        except Exception as e:
            self.finalizar(f"Error crítico: {str(e)}")

    @mainthread
    def update_status(self, current, total):
        self.progress_val = (current / total) * 100
        self.segment_text = f"PROCESANDO SEGMENTO {current} DE {total}"

    @mainthread
    def finalizar(self, texto):
        app = App.get_running_app()
        app.root.get_screen('resultados').ids.txt_final.text = texto
        app.root.current = 'resultados'

class ResultScreen(Screen):
    pass

class NeuralApp(App):
    def build(self):
        return Builder.load_file('neural.kv')

if __name__ == '__main__':
    NeuralApp().run()