import os
import threading
from functools import partial
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.clock import mainthread
from kivy.properties import StringProperty, NumericProperty
from kivy.utils import platform

# --- Lógica de Permisos de Android ---
if platform == "android":
    from android.permissions import request_permissions, Permission

class MainScreen(Screen):
    def on_enter(self):
        # La carga de archivos ahora se llama desde el método on_start de la app
        # después de verificar los permisos.
        app = App.get_running_app()
        if app.permissions_granted:
            self.load_audio_files()

    def load_audio_files(self):
        self.ids.file_list.clear_widgets()
        
        folder = "/sdcard/Download/"
        files_in_folder = []
        if os.path.exists(folder):
            files_in_folder = [f for f in os.listdir(folder) if f.lower().endswith(('.m4a', '.mp3', '.wav', '.ogg', '.flac'))]

        if not files_in_folder:
            label = Button(text="Permiso concedido. No se encontraron audios en /Download/", size_hint_y=None, height=48, background_color=(0.1, 0.1, 0.1, 1))
            self.ids.file_list.add_widget(label)
            return

        for f in files_in_folder:
            full_path = os.path.join(folder, f)
            btn = Button(text=f, size_hint_y=None, height='48dp', background_color=(0.15, 0.15, 0.15, 1))
            btn.bind(on_release=partial(self.start_processing_for_file, full_path))
            self.ids.file_list.add_widget(btn)

    def start_processing_for_file(self, file_path, *args):
        processing_screen = self.manager.get_screen('procesando')
        processing_screen.iniciar_proceso(file_path)
        self.manager.current = 'procesando'

# ... (El resto de las clases ProcessingScreen y ResultScreen no cambian) ...
class ProcessingScreen(Screen):
    progress_val = NumericProperty(0)
    status_text = StringProperty("INICIANDO MOTOR NEURAL...")
    segment_text = StringProperty("SEGMENTO 0 DE 0")

    def iniciar_proceso(self, path):
        self.progress_val = 0
        self.status_text = "INICIANDO MOTOR NEURAL..."
        self.segment_text = "SEGMENTO 0 DE 0"
        threading.Thread(target=self.worker, args=(path,), daemon=True).start()

    def worker(self, path):
        try:
            self.update_status_text("Cargando audio...")
            audio = AudioSegment.from_file(path)
            chunks = make_chunks(audio, 30000)
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
                        pass
                    except Exception as e:
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
# --- Fin de las clases que no cambian ---


class NeuralApp(App):
    permissions_granted = False # Flag para saber si tenemos permisos

    def build(self):
        return Builder.load_file('neural.kv')

    def on_start(self):
        if platform == "android":
            self.request_android_permissions()
        else:
            # En otros sistemas operativos, asumimos que tenemos permiso
            self.permissions_granted = True
            self.root.get_screen('inicio').load_audio_files()

    def request_android_permissions(self):
        def on_permissions_result(permissions, grants):
            if all(grants):
                self.permissions_granted = True
                # Si los permisos fueron concedidos, cargamos los archivos
                self.root.get_screen('inicio').load_audio_files()
            else:
                # Opcional: mostrar un mensaje al usuario
                label = Button(text="Se necesitan permisos de almacenamiento para funcionar", size_hint_y=None, height=48)
                self.root.get_screen('inicio').ids.file_list.add_widget(label)

        request_permissions(
            [Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE],
            on_permissions_result
        )
    
    def on_resume(self):
        # Si la app se minimiza y vuelve, verifica los permisos de nuevo si no los tenía
        if platform == "android" and not self.permissions_granted:
             # Recargamos la lista de archivos por si los permisos se otorgan mientras la app estaba pausada
             self.root.get_screen('inicio').load_audio_files()


if __name__ == '__main__':
    NeuralApp().run()