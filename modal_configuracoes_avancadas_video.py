import os
import json
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from pathlib import Path
from tkinter import simpledialog

VIDEOS_DB_PATH = Path("data/videos.db")
SENHA_SECRETA = "123"

def abrir_modal_configuracoes_avancadas_video(janela_pai, video_id, fechar_modal_pai=None):
    # Solicita senha
    senha = simpledialog.askstring("Senha Requerida", "Digite a senha para acessar as configurações avançadas:", show="*")
    if senha != SENHA_SECRETA:
        messagebox.showwarning("Acesso Negado", "Senha incorreta.")
        return

    # Busca configs no banco
    with sqlite3.connect(VIDEOS_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT canal, configs FROM videos WHERE video_id = ?", (video_id,))
        resultado = cursor.fetchone()

    if not resultado:
        messagebox.showerror("Erro", "Vídeo não encontrado.")
        return

    canal, configs_raw = resultado

    try:
        configs = json.loads(configs_raw) if configs_raw else {}
    except json.JSONDecodeError:
        configs = {}

    # Fecha modal anterior (opcional)
    if fechar_modal_pai:
        fechar_modal_pai()

    # Cria modal
    modal = tb.Toplevel(janela_pai)
    modal.title(f"Configurações Avançadas - Vídeo {video_id} ({canal})")
    modal.geometry("400x500")
    modal.grab_set()

    switches = {}

    def adicionar_switch(chave, texto):
        var = tk.BooleanVar(value=configs.get(chave, False))
        chk = ttk.Checkbutton(modal, text=texto, variable=var, style="Switch.TCheckbutton")
        chk.pack(anchor="w", padx=30, pady=10)
        switches[chave] = var

    # Switches disponíveis
    adicionar_switch("gerar_roteiro", "Gerar Roteiro")
    adicionar_switch("gerar_audio", "Gerar Áudio")
    adicionar_switch("audio_manual", "Áudio Manual")
    adicionar_switch("gerar_video", "Gerar Vídeo")
    adicionar_switch("gerar_legendas", "Gerar Legendas")
    adicionar_switch("gerar_metadados", "Gerar Metadados")
    adicionar_switch("gerar_thumb", "Gerar Thumb")
    adicionar_switch("thumb_manual", "Thumb Manual")

    def salvar_configuracoes():
        for chave, var in switches.items():
            configs[chave] = var.get()

        try:
            with sqlite3.connect(VIDEOS_DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE videos SET configs = ? WHERE video_id = ?", (json.dumps(configs), video_id))
                conn.commit()
            messagebox.showinfo("Sucesso", "Configurações salvas com sucesso.")
            modal.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar configurações:\n{e}")

    ttk.Button(modal, text="Salvar", bootstyle="success", command=salvar_configuracoes).pack(pady=20)
