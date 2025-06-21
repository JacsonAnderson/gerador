import os
import uuid
import json
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from datetime import datetime
from pathlib import Path
from app_roteiro.modulo_idioma import IDIOMAS_SUPORTADOS

DB_PATH = Path("data/channels.db")

def verificar_e_criar_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    if not DB_PATH.exists():
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS canais (
                    id TEXT PRIMARY KEY,
                    nome TEXT NOT NULL UNIQUE,
                    idioma TEXT,
                    marca_dagua TEXT,
                    ativo INTEGER DEFAULT 1,
                    caminho_videos TEXT,
                    roteiros_gerados INTEGER DEFAULT 0,
                    data_criacao TEXT,
                    configs TEXT
                );
            """)
            conn.commit()

def abrir_modal_criar_canal(janela_pai, callback_atualizar_lista=None):

    modal = tb.Toplevel(janela_pai)
    modal.title("Criar Canal")
    modal.geometry("700x750")
    modal.grab_set()

    def adicionar_label(texto):
        return ttk.Label(modal, text=texto, font=("Segoe UI", 10)).pack(pady=(10, 0), anchor="w", padx=20)

    # Nome do canal
    adicionar_label("Nome do canal:")
    nome_entry = ttk.Entry(modal, width=60)
    nome_entry.pack(pady=2, padx=20)

    # Idioma do canal
    adicionar_label("Idioma do canal:")
    idioma_var = tk.StringVar()
    idiomas_disponiveis = [f"{codigo.upper()} - {info['nome']}" for codigo, info in IDIOMAS_SUPORTADOS.items()]
    idioma_combo = ttk.Combobox(modal, textvariable=idioma_var, values=idiomas_disponiveis, state="readonly", width=58)
    idioma_combo.pack(pady=2, padx=20)
    idioma_combo.set(idiomas_disponiveis[0])

    # Marca d'água
    adicionar_label("Marca d'água (texto ou caminho):")
    marca_entry = ttk.Entry(modal, width=60)
    marca_entry.pack(pady=2, padx=20)

    # Música (placeholder)
    adicionar_label("Música (em breve será um menu):")
    ttk.Label(modal, text="(em breve)", font=("Segoe UI", 9, "italic")).pack(pady=(0, 10), padx=20, anchor="w")

    # Prompt tópicos
    adicionar_label("Prompt para gerar tópicos:")
    prompt_topicos_text = tk.Text(modal, height=8, wrap="word", bg="#1e1e1e", fg="white", insertbackground="white")
    prompt_topicos_text.pack(fill="both", expand=False, padx=20, pady=(0, 10))

    # Prompt roteiro
    adicionar_label("Prompt para gerar roteiro (baseado em tópicos):")
    prompt_roteiro_text = tk.Text(modal, height=8, wrap="word", bg="#1e1e1e", fg="white", insertbackground="white")
    prompt_roteiro_text.pack(fill="both", expand=False, padx=20, pady=(0, 10))

    def salvar():
        nome = nome_entry.get().strip()
        idioma_selecionado = idioma_var.get().split(" - ")[0].lower()
        marca = marca_entry.get().strip()
        prompt_topicos = prompt_topicos_text.get("1.0", tk.END).strip()
        prompt_roteiro = prompt_roteiro_text.get("1.0", tk.END).strip()

        if not nome:
            messagebox.showerror("Erro", "O nome do canal não pode estar vazio.")
            return

        canal_id = str(uuid.uuid4())
        pasta_canal = Path("data") / nome
        pasta_canal.mkdir(parents=True, exist_ok=True)
        caminho_prompts = pasta_canal / "prompts.json"
        data_criacao = datetime.now().isoformat()

        # Configurações padrão ocultas (sem idioma duplicado)
        configs_ocultas = {
            "gerar_roteiro": True,
            "gerar_audio": False,
            "audio_manual": True,
            "gerar_video": True,
            "gerar_legendas": True,
            "gerar_metadados": True,
            "gerar_thumb": True,
            "thumb_manual": False
        }

        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM canais WHERE nome = ?", (nome,))
                if cursor.fetchone()[0] > 0:
                    messagebox.showwarning("Aviso", f"O canal '{nome}' já existe.")
                    return

                cursor.execute("""
                    INSERT INTO canais (
                        id, nome, idioma, marca_dagua,
                        ativo, caminho_videos,
                        roteiros_gerados, data_criacao, configs
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    canal_id,
                    nome,
                    idioma_selecionado,
                    marca,
                    1,
                    str(pasta_canal),
                    0,
                    data_criacao,
                    json.dumps(configs_ocultas)
                ))
                conn.commit()

            # Salvar prompts em JSON separado
            with open(caminho_prompts, "w", encoding="utf-8") as f:
                json.dump({
                    "prompt_topicos": prompt_topicos,
                    "prompt_roteiro": prompt_roteiro
                }, f, indent=4, ensure_ascii=False)

            messagebox.showinfo("Sucesso", f"Canal '{nome}' criado com sucesso.")
            if callback_atualizar_lista:
                callback_atualizar_lista()
            modal.destroy()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao criar canal:\n{e}")

    ttk.Button(modal, text="Salvar", bootstyle="success", command=salvar).pack(pady=20)
