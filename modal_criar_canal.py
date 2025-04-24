import os
import json
import uuid
import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from tkinter import messagebox


def abrir_modal_criar_canal(janela_pai):
    modal = tb.Toplevel(janela_pai)
    modal.title("Criar Canal")
    modal.geometry("600x600")
    modal.grab_set()

    # ----------- Campos de entrada -----------

    def adicionar_label(texto):
        return ttk.Label(modal, text=texto, font=("Segoe UI", 10)).pack(pady=(10, 0), anchor="w", padx=20)

    # Nome
    adicionar_label("Nome do canal:")
    nome_entry = ttk.Entry(modal, width=50)
    nome_entry.pack(pady=2, padx=20)

    # Idioma
    adicionar_label("Idioma do canal:")
    idioma_entry = ttk.Entry(modal, width=50)
    idioma_entry.pack(pady=2, padx=20)

    # Marca d'água
    adicionar_label("Marca d'água (texto ou caminho):")
    marca_entry = ttk.Entry(modal, width=50)
    marca_entry.pack(pady=2, padx=20)

    # Música
    adicionar_label("Música (em breve será um menu):")
    ttk.Label(modal, text="(em breve)", font=("Segoe UI", 9, "italic")).pack(pady=(0, 10), padx=20, anchor="w")

    # Prompt
    adicionar_label("Prompt padrão:")
    prompt_text = tk.Text(modal, height=10, wrap="word", bg="#1e1e1e", fg="white", insertbackground="white")
    prompt_text.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    # ----------- Botão de salvar -----------

    def salvar():
        nome = nome_entry.get().strip()
        idioma = idioma_entry.get().strip()
        marca = marca_entry.get().strip()
        prompt = prompt_text.get("1.0", tk.END).strip()

        if not nome:
            messagebox.showerror("Erro", "O nome do canal não pode estar vazio.")
            return

        canal_id = str(uuid.uuid4())
        db_path = os.path.join("db", "canais", f"{nome}.json")
        data_dir = os.path.join("data", nome)
        data_config_path = os.path.join(data_dir, "config.json")

        if os.path.exists(db_path):
            messagebox.showwarning("Aviso", f"O canal '{nome}' já existe.")
            return

        try:
            os.makedirs(data_dir, exist_ok=True)

            with open(data_config_path, "w", encoding="utf-8") as f:
                json.dump({"id": canal_id}, f, indent=4)

            canal_config = {
                "id": canal_id,
                "nome": nome,
                "idioma": idioma,
                "marca_dagua": marca,
                "prompt": prompt,
                "ativo": True,
                "caminho_videos": data_dir,
                "config_criacao": {
                    "roteiros_gerados": 0,
                    "data_criacao": os.path.getctime(data_config_path)
                }
            }

            with open(db_path, "w", encoding="utf-8") as f:
                json.dump(canal_config, f, indent=4)

            messagebox.showinfo("Sucesso", f"Canal '{nome}' criado com sucesso.")
            modal.destroy()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao criar canal:\n{e}")

    ttk.Button(modal, text="Salvar", bootstyle="success", command=salvar).pack(pady=15)

