import os
import json
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import ttkbootstrap as tb
from pathlib import Path
from app_videoforge.vf_roteiro import IDIOMAS_SUPORTADOS
from modal_configuracoes_avancadas import abrir_modal_configuracoes_avancadas

DB_PATH = Path("data/channels.db")


def abrir_modal_configurar_canal(janela_pai, canal_id, callback_atualizar_lista=None):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nome, idioma, marca_dagua, caminho_videos FROM canais WHERE id = ?", (canal_id,))
        canal = cursor.fetchone()

    if not canal:
        messagebox.showerror("Erro", "Canal não encontrado.")
        return

    nome, idioma, marca, caminho = canal
    caminho = Path(caminho)
    caminho_prompts = caminho / "prompts.json"

    prompt_topicos = ""
    prompt_roteiro = ""
    if caminho_prompts.exists():
        with open(caminho_prompts, "r", encoding="utf-8") as f:
            dados = json.load(f)
            prompt_topicos = dados.get("prompt_topicos", "")
            prompt_roteiro = dados.get("prompt_roteiro", "")

    modal = tb.Toplevel(janela_pai)
    modal.title(f"Configurar Canal - {nome}")
    modal.geometry("700x800")
    modal.grab_set()

    def adicionar_label(texto):
        return ttk.Label(modal, text=texto, font=("Segoe UI", 10)).pack(pady=(10, 0), anchor="w", padx=20)

    # Idioma
    adicionar_label("Idioma do canal:")
    idioma_var = tk.StringVar()
    idiomas_disponiveis = [f"{codigo.upper()} - {info['nome']}" for codigo, info in IDIOMAS_SUPORTADOS.items()]
    idioma_combo = ttk.Combobox(modal, textvariable=idioma_var, values=idiomas_disponiveis, state="readonly", width=58)
    idioma_combo.pack(pady=2, padx=20)
    idioma_combo.set(next((i for i in idiomas_disponiveis if i.lower().startswith(idioma)), idiomas_disponiveis[0]))

    # Marca d'água
    adicionar_label("Marca d'água (texto ou caminho):")
    marca_entry = ttk.Entry(modal, width=60)
    marca_entry.pack(pady=2, padx=20)
    marca_entry.insert(0, marca)

    # Prompt tópicos
    adicionar_label("Prompt para gerar tópicos:")
    prompt_topicos_text = tk.Text(modal, height=8, wrap="word", bg="#1e1e1e", fg="white", insertbackground="white")
    prompt_topicos_text.pack(fill="both", expand=False, padx=20, pady=(0, 10))
    prompt_topicos_text.insert("1.0", prompt_topicos)

    # Prompt roteiro
    adicionar_label("Prompt para gerar roteiro (baseado em tópicos):")
    prompt_roteiro_text = tk.Text(modal, height=8, wrap="word", bg="#1e1e1e", fg="white", insertbackground="white")
    prompt_roteiro_text.pack(fill="both", expand=False, padx=20, pady=(0, 10))
    prompt_roteiro_text.insert("1.0", prompt_roteiro)

    def salvar():
        novo_idioma = idioma_var.get().split(" - ")[0].lower()
        nova_marca = marca_entry.get().strip()
        novo_topico = prompt_topicos_text.get("1.0", tk.END).strip()
        novo_roteiro = prompt_roteiro_text.get("1.0", tk.END).strip()

        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE canais
                    SET idioma = ?, marca_dagua = ?
                    WHERE id = ?
                """, (novo_idioma, nova_marca, canal_id))
                conn.commit()

            with open(caminho_prompts, "w", encoding="utf-8") as f:
                json.dump({
                    "prompt_topicos": novo_topico,
                    "prompt_roteiro": novo_roteiro
                }, f, indent=4, ensure_ascii=False)

            messagebox.showinfo("Sucesso", "Canal atualizado com sucesso.")
            if callback_atualizar_lista:
                callback_atualizar_lista()
            modal.destroy()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao atualizar canal:\n{e}")

    def excluir():
        resposta = simpledialog.askstring("Confirmar exclusão", f"Digite o nome do canal '{nome}' para confirmar:")
        if resposta != nome:
            messagebox.showwarning("Cancelado", "Nome incorreto. A exclusão foi cancelada.")
            return

        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM canais WHERE id = ?", (canal_id,))
                conn.commit()

            if caminho.exists():
                import shutil
                shutil.rmtree(caminho)

            messagebox.showinfo("Excluído", f"Canal '{nome}' foi removido com sucesso.")
            if callback_atualizar_lista:
                callback_atualizar_lista()
            modal.destroy()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao excluir canal:\n{e}")

    ttk.Button(modal, text="Salvar Alterações", bootstyle="success", command=salvar).pack(pady=10)
    ttk.Button(modal, text="Excluir Canal", bootstyle="danger-outline", command=excluir).pack(pady=10)
    ttk.Button(modal, text="Configurações Avançadas", bootstyle="secondary", command=lambda: abrir_modal_configuracoes_avancadas(modal, canal_id, modal.destroy)).pack(pady=10)