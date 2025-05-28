import os
import json
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from pathlib import Path
from tkinter import simpledialog

DB_PATH = Path("data/channels.db")
SENHA_SECRETA = "595985656729"

def abrir_modal_configuracoes_avancadas(janela_pai, canal_id, fechar_modal_pai=None):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nome, configs FROM canais WHERE id = ?", (canal_id,))
        resultado = cursor.fetchone()

    if not resultado:
        messagebox.showerror("Erro", "Canal não encontrado.")
        return

    nome, configs_raw = resultado

    try:
        configs = json.loads(configs_raw)
    except json.JSONDecodeError:
        messagebox.showerror("Erro", "Configurações inválidas.")
        return

    # Solicitar senha
    senha = simpledialog.askstring("Senha Requerida", "Digite a senha para acessar as configurações avançadas:", show="*")
    if senha != SENHA_SECRETA:
        messagebox.showwarning("Acesso Negado", "Senha incorreta.")
        return
    # Fecha o modal anterior (opcional)
    if fechar_modal_pai:
        fechar_modal_pai()

    # Criar modal
    modal = tb.Toplevel(janela_pai)
    modal.title(f"Configurações Avançadas - {nome}")
    modal.geometry("400x500")
    modal.grab_set()

    switches = {}

    def adicionar_switch(chave, texto):
        var = tk.BooleanVar(value=configs.get(chave, False))
        chk = ttk.Checkbutton(modal, text=texto, variable=var, style="Switch.TCheckbutton")
        chk.pack(anchor="w", padx=30, pady=10)
        switches[chave] = var

    # Adiciona todos os switches
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
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE canais SET configs = ? WHERE id = ?", (json.dumps(configs), canal_id))
                conn.commit()
            messagebox.showinfo("Sucesso", "Configurações salvas com sucesso.")
            modal.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar configurações:\n{e}")

    ttk.Button(modal, text="Salvar", bootstyle="success", command=salvar_configuracoes).pack(pady=20)
