import os
import json
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from datetime import datetime
from pathlib import Path

VIDEOS_DB_PATH = Path("data/videos.db")
CHANNELS_DB_PATH = Path("data/channels.db")

def verificar_ou_criar_videos_db():
    if not VIDEOS_DB_PATH.exists():
        VIDEOS_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(VIDEOS_DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    canal TEXT NOT NULL,
                    video_id TEXT NOT NULL,
                    link TEXT,
                    roteiro_ok INTEGER DEFAULT 0,
                    roteiro_data TEXT,
                    criado_em TEXT
                );
            """)
            conn.commit()

def obter_lista_canais():
    canais = []
    if CHANNELS_DB_PATH.exists():
        with sqlite3.connect(CHANNELS_DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT nome FROM canais ORDER BY nome ASC")
            canais = [row[0] for row in cursor.fetchall()]
    return canais

def abrir_modal_adicionar_videos(janela_pai):
    verificar_ou_criar_videos_db()

    modal = tb.Toplevel(janela_pai)
    modal.title("Adicionar Vídeos")
    modal.geometry("600x500")
    modal.grab_set()

    canais_disponiveis = obter_lista_canais()

    if not canais_disponiveis:
        messagebox.showerror("Erro", "Nenhum canal encontrado.")
        modal.destroy()
        return

    ttk.Label(modal, text="Selecionar Canal:").pack(pady=10, anchor="w", padx=20)
    canal_var = tk.StringVar(value=canais_disponiveis[0])
    canal_combo = ttk.Combobox(modal, textvariable=canal_var, values=canais_disponiveis, state="readonly")
    canal_combo.pack(padx=20, fill="x")

    ttk.Label(modal, text="Quantos vídeos deseja adicionar?").pack(pady=10, anchor="w", padx=20)
    qtd_var = tk.IntVar(value=1)
    qtd_combo = ttk.Combobox(modal, textvariable=qtd_var, values=list(range(1, 6)), state="readonly")
    qtd_combo.pack(padx=20, fill="x")

    links_frame = ttk.Frame(modal)
    links_frame.pack(padx=20, pady=20, fill="both", expand=True)

    entries = []

    def gerar_campos_links(*args):
        for widget in links_frame.winfo_children():
            widget.destroy()
        entries.clear()

        for i in range(qtd_var.get()):
            ttk.Label(links_frame, text=f"Link do vídeo {i+1}:").pack(anchor="w")
            entry = ttk.Entry(links_frame, width=70)
            entry.pack(pady=5, fill="x")
            entries.append(entry)

    qtd_var.trace_add("write", gerar_campos_links)
    gerar_campos_links()

    def salvar():
        canal = canal_var.get()
        links = [e.get().strip() for e in entries]

        if not all(links):
            messagebox.showwarning("Atenção", "Preencha todos os links.")
            return

        canal_path = os.path.join("data", canal)
        os.makedirs(canal_path, exist_ok=True)

        existentes = [int(p) for p in os.listdir(canal_path) if p.isdigit()]
        proximo_id = max(existentes, default=0) + 1

        with sqlite3.connect(VIDEOS_DB_PATH) as conn:
            cursor = conn.cursor()

            for i, link in enumerate(links):
                numero_video = str(proximo_id + i).zfill(3)
                video_path = os.path.join(canal_path, numero_video)

                if os.path.exists(video_path):
                    messagebox.showwarning("Atenção", f"O vídeo {numero_video} já existe. Pulando.")
                    continue

                os.makedirs(os.path.join(video_path, "control"), exist_ok=True)

                metadados = {
                    "link": link,
                    "adicionado_em": datetime.now().isoformat()
                }

                with open(os.path.join(video_path, "control", "metadados.json"), "w", encoding="utf-8") as f:
                    json.dump(metadados, f, indent=4)

                cursor.execute("""
                    INSERT INTO videos (canal, video_id, link, roteiro_ok, roteiro_data, criado_em)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    canal,
                    numero_video,
                    link,
                    0,
                    None,
                    datetime.now().isoformat()
                ))

            conn.commit()

        messagebox.showinfo("Sucesso", "Vídeos adicionados com sucesso.")
        modal.destroy()

    ttk.Button(modal, text="Adicionar Vídeos", bootstyle="success", command=salvar).pack(pady=10)
