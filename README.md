# Exam Solver

Herramienta ligera y de un solo click para resolver examenes usando **Google Gemini 2.0 Flash (Gratis)** o modelos compatibles, construida bajo la filosofía funcional y minimalista (código limpio, 0 emojis, puro texto claro).

## Estructura

Por seguridad y organización, el proyecto está dividido por sistemas operativos:

- **Linux** (`/Linux`): Usa el sub-sistema oficial de Wayland (`xdg-desktop-portal`) gestionando permisos de forma nativa sin romper la seguridad. Requiere las librerías `PygObject` de GNOME.
- **Windows** (`/Windows`): Captura súper rápida transparente usando `Pillow`, saltándose diálogos ya que el OS no bloquea capturas.

## Instalación

1. Clona este repositorio
2. Instala los requerimientos:
   ```bash
   pip install -r requirements.txt
   ```
3. Renombra `config.example.py` a `config.py` e ingresa tu API key de Google Gemini.

## Uso

- **Windows:** Ejecuta `python Windows/exam_solver_windows.py`
- **Linux (Wayland):** Ejecuta `python Linux/exam_solver.py`

Un botón flotante `[Resolver]` aparecerá en la esquina. Al hacerle click tomará una captura y resolverá lo que esté en tu pantalla en segundos. Puedes arrastrarlo desde el `::`.

## Seguridad

Las llaves API y los archivos `config.py` están **ignorados** de fábrica en git para evitar subidas accidentales de llaves privadas.
