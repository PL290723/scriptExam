#!/usr/bin/env python3
"""
Exam Solver — Resuelve exámenes con un click (Versión Windows).

Botón flotante siempre visible. Al hacer click:
  1. Se oculta el botón
  2. Toma captura de pantalla inmediatamente (sin diálogos)
  3. Envía la captura a Google Gemini 2.0 Flash (Gratis)
  4. Muestra la respuesta en un popup flotante

La API key se lee de config.py.
"""

import os
import sys
import threading
import tkinter as tk
import io
from pathlib import Path
from tkinter import messagebox, simpledialog

try:
    from PIL import ImageGrab
except ImportError:
    print("Falta instalador Pillow. Ejecuta: pip install Pillow")
    sys.exit(1)

from google import genai
from google.genai import types
import config

# --- Constantes ---

MODEL_NAME = "gemini-2.5-flash"

# --- Estado global ---

language = ""
app = None
lock = threading.Lock()
client = None


# --- API Key ---

def get_api_key():
    """Obtiene la key desde config.py o env."""
    if hasattr(config, "API_KEY") and config.API_KEY and config.API_KEY != "TU_API_KEY_AQUI":
        return config.API_KEY
    return os.environ.get("GEMINI_API_KEY", "")


# --- Captura de pantalla (Windows) ---

def capture_screen():
    """Captura pantalla en Windows usando Pillow. Retorna dictionary con mime_type y data."""
    # En Windows ImageGrab captura todas las pantallas automáticamente
    img = ImageGrab.grab(all_screens=True)
    
    byte_stream = io.BytesIO()
    img.save(byte_stream, format='PNG')
    png_bytes = byte_stream.getvalue()
    
    return {
        "mime_type": "image/png",
        "data": png_bytes
    }


# --- IA (Gemini) ---

def ask_ai(image_data, lang):
    """Envía imagen a Gemini Vision, retorna texto."""
    prompt = (
        f"You are an exam solver. The user sends a screenshot "
        f"of a question. Answer correctly and concisely in {lang}. "
        f"If multiple choice, state the correct option first, "
        f"then briefly explain."
    )
    
    part = types.Part.from_bytes(data=image_data["data"], mime_type=image_data["mime_type"])
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[prompt, part]
    )
    return response.text


# --- GUI ---

def show_popup(title, body, timeout_ms=None):
    """Popup flotante en esquina superior derecha."""
    popup = tk.Toplevel(app)
    popup.withdraw()
    popup.overrideredirect(True)
    popup.attributes("-topmost", True)
    popup.configure(bg="#1a1a2e")

    bar = tk.Frame(popup, bg="#16213e")
    bar.pack(fill="x", padx=2, pady=(2, 0))

    tk.Label(
        bar, text=title, font=("sans-serif", 11, "bold"),
        fg="#e94560", bg="#16213e", anchor="w", padx=10, pady=6,
    ).pack(side="left", fill="x", expand=True)

    close_lbl = tk.Label(
        bar, text="X", font=("sans-serif", 12),
        fg="#888", bg="#16213e", cursor="hand2", padx=10,
    )
    close_lbl.pack(side="right")
    close_lbl.bind("<Button-1>", lambda e: popup.destroy())

    txt = tk.Text(
        popup, wrap="word", font=("sans-serif", 10),
        fg="#eee", bg="#1a1a2e", relief="flat",
        padx=15, pady=10, borderwidth=0, highlightthickness=0,
    )
    txt.insert("1.0", body)
    txt.config(state="disabled")
    lines = int(txt.index("end-1c").split(".")[0])
    txt.config(height=min(lines + 1, 18))
    txt.pack(fill="both", expand=True, padx=2, pady=(0, 2))

    popup.update_idletasks()
    w, h = 440, popup.winfo_reqheight()
    x = popup.winfo_screenwidth() - w - 20
    popup.geometry(f"{w}x{h}+{x}+40")
    popup.deiconify()

    if timeout_ms:
        popup.after(
            timeout_ms,
            lambda: popup.destroy() if popup.winfo_exists() else None,
        )


def solve():
    """Oculta botón -> captura -> IA -> popup con respuesta."""
    if not lock.acquire(blocking=False):
        return

    app.withdraw()

    def _after_hide():
        def _work():
            try:
                img_data = capture_screen()

                app.after(0, app.deiconify)
                app.after(0, lambda: show_popup(
                    "Pensando...",
                    "Consultando a Gemini...",
                    timeout_ms=30000,
                ))

                answer = ask_ai(img_data, language)
                app.after(0, lambda: show_popup("Respuesta", answer))

            except Exception as e:
                err = str(e)
                app.after(0, app.deiconify)
                app.after(0, lambda: show_popup("Error", err))
            finally:
                lock.release()

        threading.Thread(target=_work, daemon=True).start()

    # En Windows podemos tomar la captura casi de inmediato sin esperar al portal de D-Bus
    app.after(200, _after_hide)


class DragHandler:
    """Permite arrastrar una ventana sin decoración."""

    def __init__(self, widget):
        self._dx = 0
        self._dy = 0
        widget.bind("<Button-1>", self._on_press)
        widget.bind("<B1-Motion>", self._on_drag)

    def _on_press(self, event):
        self._dx = event.x
        self._dy = event.y

    def _on_drag(self, event):
        top = event.widget.winfo_toplevel()
        x = top.winfo_x() + event.x - self._dx
        y = top.winfo_y() + event.y - self._dy
        top.geometry(f"+{x}+{y}")


def build_toolbar():
    """Crea el botón flotante arrastrable."""
    app.overrideredirect(True)
    app.attributes("-topmost", True)
    app.configure(bg="#16213e")

    frame = tk.Frame(app, bg="#16213e")
    frame.pack(padx=2, pady=2)

    grip = tk.Label(
        frame, text="::", font=("sans-serif", 10),
        fg="#555", bg="#16213e", cursor="fleur", padx=4,
    )
    grip.pack(side="left")
    DragHandler(grip)

    tk.Button(
        frame, text="[Resolver]", font=("sans-serif", 11, "bold"),
        fg="#fff", bg="#2196F3", activebackground="#1976D2",
        activeforeground="#fff", relief="flat",
        padx=12, pady=6, cursor="hand2", command=solve,
    ).pack(side="left", padx=(0, 2))

    tk.Button(
        frame, text="X", font=("sans-serif", 10),
        fg="#888", bg="#16213e", activebackground="#e94560",
        activeforeground="#fff", relief="flat",
        padx=6, pady=6, cursor="hand2", command=app.quit,
    ).pack(side="left")

    app.update_idletasks()
    x = app.winfo_screenwidth() - app.winfo_reqwidth() - 30
    y = app.winfo_screenheight() - app.winfo_reqheight() - 60
    app.geometry(f"+{x}+{y}")


# --- Main ---

def main():
    global language, app, client

    app = tk.Tk()
    app.withdraw()

    api_key = get_api_key()
    if not api_key:
        messagebox.showerror(
            "Exam Solver",
            "Falta API_KEY en config.py.\nCrea el archivo o asegúrate de que tenga la key.",
        )
        sys.exit(1)

    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
         messagebox.showerror("Error Gemini", f"Error configurando Gemini:\n{e}")
         sys.exit(1)

    language = simpledialog.askstring(
        "Exam Solver",
        "¿En qué idioma quieres las respuestas?\nWhat language?",
        initialvalue="español",
        parent=app,
    )
    if not language:
        language = "español"

    build_toolbar()
    app.deiconify()

    show_popup(
        "Exam Solver (Windows)",
        f"Idioma: {language}\nModelo: {MODEL_NAME}\n\n"
        f"1. Click en [Resolver]\n"
        f"2. Espera unos segundos\n"
        f"3. La respuesta aparece aquí\n\n"
        f"Arrastra :: para mover el botón.",
        timeout_ms=8000,
    )

    app.mainloop()


if __name__ == "__main__":
    main()
