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
    from android.storage import primary_external_storage_path

class MainScreen(Screen):
    
    def find_and_display_files(self):
        """
        Este método es llamado por el botón. Controla todo el flujo
        de permisos y carga de archivos.
        """
        self.ids.file_list.clear_widgets()
        
        def on_permissions_granted(permissions, grants):
            """Callback que se ejecuta después de que el usuario responde a la solicitud de permisos."""
            if all(grants):
                # Si los permisos fueron concedidos, cargamos los archivos
                self.load_audio_files()
            else:
                # Si no, mostramos un mensaje de error claro en la lista
                error_text = "Error: Se requieren permisos de almacenamiento para buscar archivos."
                label = Button(text=error_text, font_size='12sp', size_hint_y=None, height=200, background_color=(0.1, 0.1, 0.1, 1))
                self.ids.file_list.add_widget(label)

        if platform == "android":
            # Pedimos los permisos. El resto de la lógica continúa en el callback 'on_permissions_granted'.
            request_permissions(
                [Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE],
                on_permissions_granted
            )
        else:
            # En un PC, simplemente cargamos los archivos.
            self.load_audio_files()

    def load_audio_files(self):
        """
        Esta función escanea el almacenamiento y muestra los archivos o un informe de depuración.
        Ahora solo es llamada después de que los permisos han sido confirmados.
        """
        debug_info = []
        try:
            debug_info.append("Iniciando búsqueda de archivos...")
            
            # Usamos una ruta genérica para la carpeta de descargas en PC para pruebas
            folder = os.path.join(os.path.expanduser('~'), 'Downloads')
            if platform == "android":
                folder = os.path.join(primary_external_storage_path(), 'Download')
            
            debug_info.append(f"Ruta de búsqueda: {folder}")
            
            path_exists = os.path.exists(folder)
            debug_info.append(f"¿La ruta existe?: {path_exists}")

            files_in_folder = []
            if path_exists:
                files_in_folder = [f for f in os.listdir(folder) if f.lower().endswith(('.m4a', '.mp3', '.wav', '.ogg', '.flac'))]
                debug_info.append(f"Archivos de audio encontrados: {len(files_in_folder)}")
            
            if not files_in_folder:
                # Si no hay archivos, mostramos toda la información de depuración
                label_text = "\n".join(debug_info)
                label = Button(text=label_text, font_size='12sp', halign='center', size_hint_y=None, height=200, background_color=(0.1, 0.1, 0.1, 1))
                self.ids.file_list.add_widget(label)
                return

            for f in files_in_folder:
                full_path = os.path.join(folder, f)
                btn = Button(text=f, size_hint_y=None, height='48dp', background_color=(0.15, 0.15, 0.15, 1))
                btn.bind(on_release=partial(self.start_processing_for_file, full_path))
                self.ids.file_list.add_widget(btn)

        except Exception as e:
            # Si ocurre cualquier error, lo mostramos en pantalla
            error_text = "\n".join(debug_info) + f"\n\nERROR INESPERADO: {str(e)}"
            label = Button(text=error_text, font_size='12sp', halign='center', size_hint_y=None, height=200, background_color=(0.1, 0.1, 0.1, 1))
            self.ids.file_list.add_widget(label)

    def start_processing_for_file(self, file_path, *args):
        processing_screen = self.manager.get_screen('procesando')
        processing_screen.iniciar_proceso(file_path)
        self.manager.current = 'procesando'

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

class NeuralApp(App):
    def build(self):
        return Builder.load_file('neural.kv')

if __name__ == '__main__':
    NeuralApp().run()