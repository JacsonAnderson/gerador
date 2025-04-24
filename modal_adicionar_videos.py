import os
import json
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from tkinter import messagebox
from datetime import datetime


def abrir_modal_adicionar_videos(janela_pai):
    modal = tb.Toplevel(janela_pai)
    modal.title("Adicionar Vídeos")
    modal.geometry("600x500")
    modal.grab_set()

    canais_disponiveis = [
        f.replace(".json", "") for f in os.listdir("db/canais") if f.endswith(".json")
    ]

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
    gerar_campos_links()  # inicializa com 1 campo

    def salvar():
        canal = canal_var.get()
        links = [e.get().strip() for e in entries]

        if not all(links):
            messagebox.showwarning("Atenção", "Preencha todos os links.")
            return

        canal_path = os.path.join("data", canal)
        os.makedirs(canal_path, exist_ok=True)

        # Verifica qual o próximo número disponível
        existentes = [int(p) for p in os.listdir(canal_path) if p.isdigit()]
        proximo_id = max(existentes, default=0) + 1

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

        messagebox.showinfo("Sucesso", "Vídeos adicionados com sucesso.")
        modal.destroy()

    ttk.Button(modal, text="Adicionar Vídeos", bootstyle="success", command=salvar).pack(pady=10)
