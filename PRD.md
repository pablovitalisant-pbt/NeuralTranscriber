# Documento de Requisitos de Producto (PRD): NeuralTranscriber

**Versión:** 1.0
**Autor:** Gemini
**Fecha:** 2026-02-19

---

## 1. Visión y Oportunidad

### 1.1. El Problema
La transcripción manual de archivos de audio (entrevistas, clases, reuniones, notas de voz) es un proceso lento, tedioso y propenso a errores. Profesionales y estudiantes invierten una cantidad significativa de tiempo en convertir voz a texto, tiempo que podría ser utilizado en tareas de mayor valor.

### 1.2. La Solución
**NeuralTranscriber** es una aplicación móvil para Android que simplifica radicalmente este proceso. La aplicación permite a los usuarios seleccionar un archivo de audio de su dispositivo, procesarlo a través de un servicio de reconocimiento de voz y obtener una transcripción de texto completa, todo desde una interfaz simple e intuitiva.

### 1.3. Audiencia Objetivo
- **Estudiantes:** Para transcribir clases grabadas y material de estudio.
- **Periodistas y Creadores de Contenido:** Para transcribir entrevistas, podcasts y guiones.
- **Profesionales:** Para documentar reuniones, conferencias y dictar notas.
- **Cualquier persona** que necesite convertir audio a texto de forma rápida y eficiente.

---

## 2. Metas y Objetivos del Producto

### 2.1. Metas del Usuario
- Transcribir un archivo de audio local con un mínimo de pasos.
- Obtener una transcripción de texto precisa en español.
- Copiar y compartir fácilmente el texto transcrito.
- Monitorear el progreso de una transcripción en curso.

### 2.2. Metas del Proyecto (MVP - Producto Mínimo Viable)
- Desarrollar una aplicación funcional y estable para Android.
- Validar la arquitectura técnica (Kivy + Buildozer + API de transcripción).
- Lograr una tasa de éxito de transcripción superior al 95% para audios claros.
- Asegurar una experiencia de usuario fluida y sin bloqueos.

---

## 3. Características y Requisitos Funcionales

### F1: Descubrimiento y Selección de Archivos
- **REQ-1.1:** La aplicación debe solicitar explícitamente los permisos de lectura de almacenamiento en tiempo de ejecución. La funcionalidad de búsqueda no debe ejecutarse hasta que el usuario conceda el permiso.
- **REQ-1.2:** Al iniciar la acción de búsqueda, la app debe escanear el directorio público de "Descargas" del dispositivo en busca de archivos de audio compatibles.
- **REQ-1.3:** Los formatos de audio soportados en el MVP son: `.mp3`, `.m4a`, `.wav`, `.ogg`, `.flac`.
- **REQ-1.4:** Los archivos encontrados deben mostrarse en una lista vertical y desplazable, mostrando el nombre completo de cada archivo.
- **REQ-1.5:** Si no se encuentran archivos, la app debe mostrar un mensaje claro e informativo en el área de la lista (ej. "No se encontraron archivos de audio en la carpeta de Descargas").
- **REQ-1.6:** Si el usuario deniega los permisos, se debe mostrar un mensaje explicando que son necesarios para la funcionalidad principal.

### F2: Proceso de Transcripción
- **REQ-2.1:** Al tocar un archivo de la lista, debe iniciarse el proceso de transcripción.
- **REQ-2.2:** La transcripción debe ejecutarse en un hilo de fondo (`background thread`) para no congelar la interfaz de usuario.
- **REQ-2.3:** El usuario debe ser llevado a una pantalla de "Procesando" que muestre el estado actual de forma clara.
- **REQ-2.4:** La pantalla de "Procesando" debe incluir:
    - Un indicador de progreso (barra de progreso o similar).
    - Un texto de estado (ej. "Procesando segmento 3 de 10...").
- **REQ-2.5:** Para manejar archivos largos y las limitaciones de las APIs, los archivos de audio deben ser divididos en fragmentos (chunks) de 30-60 segundos.
- **REQ-2.6:** La app utilizará un servicio de Speech-to-Text en la nube. La implementación debe ser modular para poder cambiar de proveedor en el futuro. El MVP usará la API de Google Speech Recognition (a través de la librería `speech_recognition`).

### F3: Visualización y Uso de Resultados
- **REQ-3.1:** Una vez finalizada la transcripción, el usuario será llevado a una pantalla de "Resultados".
- **REQ-3.2:** El texto completo de la transcripción se mostrará en un campo de texto desplazable y de solo lectura.
- **REQ-3.3:** El usuario debe poder seleccionar y copiar manualmente el texto.
- **REQ-3.4:** La pantalla debe incluir un botón "Copiar Todo" para copiar el texto completo al portapapeles con un solo toque.
- **REQ-3.5:** Debe haber un botón "Transcribir Otro Archivo" que devuelva al usuario a la pantalla principal para iniciar un nuevo proceso.

### F4: Manejo de Errores
- **REQ-4.1:** **Sin Conexión:** Si no hay conexión a internet al intentar transcribir, se debe mostrar un error claro al usuario.
- **REQ-4.2:** **Error de API:** Si el servicio de transcripción devuelve un error, este debe ser comunicado al usuario (ej. "El servicio de transcripción no está disponible").
- **REQ-4.3:** **Audio Corrupto:** Si `pydub` o la librería de reconocimiento no pueden procesar el archivo, se debe mostrar un error "Archivo de audio dañado o no compatible".
- **REQ-4.4:** **Transcripción Vacía:** Si el audio no contiene voz discernible, la pantalla de resultados mostrará el mensaje "No se pudo detectar voz en el audio".

---

## 4. Diseño y Experiencia de Usuario (UX)

- **Principio General:** La simplicidad es clave. La app debe ser auto-explicativa y requerir el mínimo esfuerzo del usuario.
- **Flujo de Pantallas:**
    1.  **Pantalla Principal:** Contiene el título, un botón "Buscar Archivos" y un área de lista vacía. Al completarse la búsqueda, el área se llena con los archivos.
    2.  **Pantalla de Procesamiento:** Pantalla modal o de transición que muestra una animación de progreso y el estado.
    3.  **Pantalla de Resultados:** Muestra el texto final y las acciones (Copiar, Nuevo).
- **Tema Visual:** Se mantendrá el tema oscuro (fondo `#0B0E14`) con acentos en cian (`#00f2ff`) para una apariencia moderna y profesional.

---

## 5. Arquitectura y Stack Tecnológico

- **Framework Principal:** Python 3 con Kivy para la interfaz de usuario multiplataforma.
- **Empaquetado Android:** Buildozer.
- **Librerías Clave:**
    - `kivy`: Núcleo de la aplicación.
    - `pydub`: Para manipulación de audio (carga, división en chunks).
    - `speech_recognition`: Como cliente para la API de Google Speech-to-Text.
    - `python-for-android`: El backend de compilación de Buildozer.
- **Dependencias Nativas (Recetas de Buildozer):**
    - `ffmpeg`: Requerimiento crítico para que `pydub` pueda manejar múltiples formatos de audio. Debe ser incluido en los requisitos de `buildozer.spec`.
- **Arquitectura de Software:**
    - **Separación de Lógica y Vista:** El código Python (`main.py`) contendrá la lógica de la aplicación, mientras que el diseño de la interfaz estará en el archivo Kivy Language (`neural.kv`).
    - **Hilos de Fondo:** Cualquier operación que dure más de unos pocos milisegundos (procesamiento de audio, llamadas a API) **debe** ejecutarse en un hilo separado para no bloquear el hilo principal de la UI.
    - **Actualización Segura de la UI:** Utilizar el decorador `@mainthread` de Kivy para cualquier función que modifique la interfaz de usuario desde un hilo de fondo.
    - **Modularidad:** Se recomienda abstraer el servicio de transcripción en su propia clase o módulo para facilitar futuras sustituciones (ej. cambiar a OpenAI Whisper).

---

## 6. Futuras Mejoras (Post-MVP)

- **Editor de Texto:** Permitir la edición del texto transcrito directamente en la app.
- **Soporte Multilenguaje:** Añadir una opción para seleccionar el idioma del audio.
- **Grabación en Vivo:** Implementar una función para grabar audio directamente desde el micrófono del dispositivo y transcribirlo.
- **Diarización:** Identificar y etiquetar a diferentes hablantes en el audio ("Hablante A", "Hablante B").
- **Soporte para iOS:** Generar una versión compatible para iOS.
- **Exportar a .txt:** Guardar la transcripción como un archivo de texto en el dispositivo.

---

## 7. Criterios de Éxito

- La aplicación se instala y se inicia sin errores en Android 8.0 y versiones posteriores.
- El flujo completo (seleccionar, transcribir, copiar) se puede completar de forma intuitiva.
- La tasa de fallos de la aplicación (crashes) es inferior al 1%.
