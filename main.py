import os
import threading
from functools import partial
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.clock import mainthread
from kivy.properties import StringProperty, NumericProperty
import speech_recognition as sr
from pydub import AudioSegment
from pydub.utils import make_chunks

class MainScreen(Screen):
    def on_enter(self):
        # Limpiamos la lista por si volvemos a esta pantalla
        self.ids.file_list.clear_widgets()
        
        # Escaneo de la carpeta de descargas
        # En Android, la ruta a la memoria interna principal suele ser /sdcard/ o /storage/emulated/0/
        folder = "/sdcard/Download/"
        files_in_folder = []
        if os.path.exists(folder):
            files_in_folder = [f for f in os.listdir(folder) if f.lower().endswith(('.m4a', '.mp3', '.wav', '.ogg', '.flac'))]

        if not files_in_folder:
            label = Button(text="No se encontraron archivos de audio en /Download/", size_hint_y=None, height=dp(50), background_color=(0.1, 0.1, 0.1, 1))
            self.ids.file_list.add_widget(label)
            return

        for f in files_in_folder:
            full_path = os.path.join(folder, f)
            btn = Button(text=f, size_hint_y=None, height='48dp', background_color=(0.15, 0.15, 0.15, 1))
            # Usamos partial para pasar el argumento de la ruta al callback
            btn.bind(on_release=partial(self.start_processing_for_file, full_path))
            self.ids.file_list.add_widget(btn)

    def start_processing_for_file(self, file_path, *args):
        # Obtenemos la pantalla de procesamiento y llamamos a su método
        processing_screen = self.manager.get_screen('procesando')
        processing_screen.iniciar_proceso(file_path)
        # Cambiamos a la pantalla de procesamiento
        self.manager.current = 'procesando'


class ProcessingScreen(Screen):
    progress_val = NumericProperty(0)
    status_text = StringProperty("INICIANDO MOTOR NEURAL...")
    segment_text = StringProperty("SEGMENTO 0 DE 0")

    def iniciar_proceso(self, path):
        # Reseteamos los labels al iniciar un nuevo proceso
        self.progress_val = 0
        self.status_text = "INICIANDO MOTOR NEURAL..."
        self.segment_text = "SEGMENTO 0 DE 0"
        threading.Thread(target=self.worker, args=(path,), daemon=True).start()

    def worker(self, path):
        try:
            self.update_status_text("Cargando audio...")
            audio = AudioSegment.from_file(path)
            chunks = make_chunks(audio, 30000) # Segmentos de 30 seg
            total = len(chunks)
            full_text = ""
            rec = sr.Recognizer()
            app = App.get_running_app()
            user_dir = app.user_data_dir

            for i, chunk in enumerate(chunks):
                self.update_status(i + 1, total)
                temp_filename = f"temp_{i}.wav"
                temp_path = os.path.join(user_dir, temp_filename)
                
                chunk.export(temp_path, format="wav")
                
                with sr.AudioFile(temp_path) as source:
                    audio_data = rec.record(source)
                    try:
                        text = rec.recognize_google(audio_data, language="es-ES")
                        full_text += text + " "
                    except sr.UnknownValueError:
                        # Este error significa que no se pudo entender nada, es normal
                        pass
                    except Exception as e:
                        # Otros errores de la API, los registramos
                        print(f"Error en recognize_google: {e}")
                
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
            self.finalizar(full_text if full_text else "No se pudo transcribir el audio.")
        except Exception as e:
            self.finalizar(f"Error crítico en el worker: {str(e)}")

    @mainthread
    def update_status_text(self, text):
        self.status_text = text

    @mainthread
    def update_status(self, current, total):
        self.progress_val = (current / total) * 100
        self.segment_text = f"PROCESANDO SEGMENTO {current} DE {total}"
        self.status_text = "Transcribiendo..."

    @mainthread
    def finalizar(self, texto):
        app = App.get_running_app()
        app.root.get_screen('resultados').ids.txt_final.text = texto
        app.root.current = 'resultados'

class ResultScreen(Screen):
    pass

class NeuralApp(App):
    def build(self):
        # Cargar el archivo KV es importante para que los ids estén disponibles
        return Builder.load_file('neural.kv')

if __name__ == '__main__':
    NeuralApp().run()