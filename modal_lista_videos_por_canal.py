
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from datetime import datetime
from pathlib import Path
from modal_editar_video import abrir_modal_editar_video  # Certifique-se de ter esse arquivo

VIDEOS_DB_PATH = Path("data/videos.db")

ESTADOS = {
    0: "Pendente",
    1: "Roteiro OK",
    2: "Áudio OK",
    3: "Vídeo Gerado",
    4: "Legendas OK",
    5: "Metadados OK",
    6: "Thumb OK",
    7: "Postado"
}

def abrir_modal_lista_videos_por_canal(janela_pai, canal_nome, callback_atualizar_canais=None):
    modal = tb.Toplevel(janela_pai)
    modal.title(f"Vídeos do Canal - {canal_nome}")
    modal.geometry("900x600")
    modal.grab_set()

    filtros_frame = ttk.Frame(modal)
    filtros_frame.pack(fill=X, padx=10, pady=10)

    ttk.Label(filtros_frame, text="🔍 Buscar por ID ou Link:").grid(row=0, column=0, sticky=W)
    busca_var = tk.StringVar()
    ttk.Entry(filtros_frame, textvariable=busca_var, width=40).grid(row=0, column=1, padx=10)

    ttk.Label(filtros_frame, text="📌 Filtrar por Estado:").grid(row=0, column=2, sticky=W, padx=(20, 0))
    estado_var = tk.StringVar()
    estado_combo = ttk.Combobox(filtros_frame, textvariable=estado_var, values=["Todos"] + list(ESTADOS.values()), state="readonly", width=20)
    estado_combo.grid(row=0, column=3)
    estado_combo.set("Todos")

    colunas = ("video_id", "link", "estado", "data", "editar")
    tabela = ttk.Treeview(modal, columns=colunas, show="headings")
    tabela.heading("video_id", text="ID do Vídeo")
    tabela.heading("link", text="Link")
    tabela.heading("estado", text="Estado")
    tabela.heading("data", text="Criado em")
    tabela.heading("editar", text="Editar")

    tabela.column("video_id", width=100)
    tabela.column("link", width=320)
    tabela.column("estado", width=120)
    tabela.column("data", width=150)
    tabela.column("editar", width=80, anchor="center")

    tabela.pack(fill=BOTH, expand=True, padx=10, pady=10)

    def ao_clicar(event):
        item = tabela.identify_row(event.y)
        coluna = tabela.identify_column(event.x)
        if coluna == "#5" and item:
            valores = tabela.item(item, "values")
            video_id = valores[0]
            abrir_modal_editar_video(
                modal,
                video_id,
                canal_nome,
                lambda: (carregar_videos(), callback_atualizar_canais()) if callback_atualizar_canais else carregar_videos()
            )


    def carregar_videos():
        tabela.delete(*tabela.get_children())
        busca = busca_var.get().lower()
        estado_filtro = estado_var.get()

        with sqlite3.connect(VIDEOS_DB_PATH) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='videos'")
            if not cursor.fetchone():
                messagebox.showwarning("Nenhum vídeo encontrado", "Clique em '➕ Adicionar Vídeos' no menu lateral para começar.")
                modal.destroy()
                return

            cursor.execute("SELECT video_id, link, estado, criado_em FROM videos WHERE canal = ? ORDER BY criado_em DESC", (canal_nome,))
            videos = cursor.fetchall()

        if not videos:
            messagebox.showinfo("Sem vídeos", "Este canal ainda não possui vídeos adicionados.")
            return

        for video_id, link, estado, criado_em in videos:
            estado_nome = ESTADOS.get(estado, "Desconhecido")
            if estado_filtro != "Todos" and estado_nome != estado_filtro:
                continue
            if busca and (busca not in video_id.lower() and busca not in link.lower()):
                continue
            data_formatada = datetime.fromisoformat(criado_em).strftime("%d/%m/%Y %H:%M") if criado_em else "-"
            tabela.insert("", tk.END, values=(video_id, link, estado_nome, data_formatada, "✏️"))

    ttk.Button(filtros_frame, text="🔄 Atualizar", bootstyle="primary", command=carregar_videos).grid(row=0, column=4, padx=(20, 0))

    tabela.bind("<Button-1>", ao_clicar)
    carregar_videos()


