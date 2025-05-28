import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
import sqlite3
from pathlib import Path
import threading


DB_CHANNELS = Path("data/channels.db")
DB_VIDEOS = Path("data/videos.db")

def abrir_modal_videoforge(janela_pai, callback_executar_controller):
    modal = tb.Toplevel(janela_pai)
    modal.title("Executar VideoForge")
    modal.geometry("500x400")
    modal.grab_set()

    modo_var = tk.StringVar()
    canal_var = tk.StringVar()
    video_var = tk.StringVar()

    canais = []
    videos = []

    def carregar_canais():
        nonlocal canais
        with sqlite3.connect(DB_CHANNELS) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT nome FROM canais")
            canais = [row[0] for row in cursor.fetchall()]
        canal_dropdown["values"] = canais
        canal_dropdown_canal["values"] = canais

    def carregar_videos(event):
        canal_selecionado = canal_var.get()
        with sqlite3.connect(DB_VIDEOS) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT video_id FROM videos WHERE canal = ?", (canal_selecionado,))
            resultado = cursor.fetchall()
            video_ids = [str(row[0]) for row in resultado]
            video_dropdown["values"] = video_ids
            video_var.set("")

    # Frame principal
    frame = ttk.Frame(modal, padding=20)
    frame.pack(fill="both", expand=True)

    # Opção: Vídeo específico
    ttk.Radiobutton(frame, text="Rodar um vídeo específico", variable=modo_var, value="video").pack(anchor="w")
    canal_dropdown = ttk.Combobox(frame, textvariable=canal_var, state="readonly")
    canal_dropdown.pack(fill="x", pady=(5, 5))
    canal_dropdown.bind("<<ComboboxSelected>>", carregar_videos)

    video_dropdown = ttk.Combobox(frame, textvariable=video_var, state="readonly")
    video_dropdown.pack(fill="x", pady=(5, 20))

    # Opção: Canal completo
    ttk.Radiobutton(frame, text="Rodar um canal completo", variable=modo_var, value="canal").pack(anchor="w")
    canal_dropdown_canal = ttk.Combobox(frame, state="readonly")
    canal_dropdown_canal.pack(fill="x", pady=(5, 20))

    # Opção: Todos os canais
    ttk.Radiobutton(frame, text="Rodar todos os canais", variable=modo_var, value="todos").pack(anchor="w", pady=(0, 20))

    # Botão iniciar
    def iniciar():
        modo = modo_var.get()

        if modo == "video":
            canal = canal_var.get()
            video_id = video_var.get()
            if not canal or not video_id:
                messagebox.showerror("Erro", "Selecione um canal e um vídeo.")
                return
            threading.Thread(target=callback_executar_controller, kwargs={
                "modo": "video", "canal": canal, "video_id": video_id
            }).start()

        elif modo == "canal":
            canal = canal_dropdown_canal.get()
            if not canal:
                messagebox.showerror("Erro", "Selecione um canal.")
                return
            threading.Thread(target=callback_executar_controller, kwargs={
                "modo": "canal", "canal": canal
            }).start()

        elif modo == "todos":
            threading.Thread(target=callback_executar_controller, kwargs={
                "modo": "todos"
            }).start()

        else:
            messagebox.showerror("Erro", "Selecione uma opção de execução.")
            return

        modal.destroy()


    ttk.Button(frame, text="Iniciar", bootstyle="success", command=iniciar).pack(pady=10)
    ttk.Button(frame, text="Cancelar", command=modal.destroy).pack()

    carregar_canais()
