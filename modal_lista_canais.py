import os
import sqlite3
import tkinter as tk
from pathlib import Path
from tkinter import ttk
import ttkbootstrap as tb
from modal_configurar_canal import abrir_modal_configurar_canal
from modal_lista_videos_por_canal import abrir_modal_lista_videos_por_canal

DB_PATH = Path("data/channels.db")
VIDEOS_DB_PATH = Path("data/videos.db")

def obter_contagem_videos(canal_nome):
    if not VIDEOS_DB_PATH.exists():
        return 0, 0

    with sqlite3.connect(VIDEOS_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT estado FROM videos WHERE canal = ?", (canal_nome,))
        estados = [row[0] for row in cursor.fetchall()]
        total = len(estados)
        pendentes = len([e for e in estados if e != 7])
        return pendentes, total

def criar_lista_canais(container):
    for widget in container.winfo_children():
        widget.destroy()

    outer_frame = ttk.Frame(container)
    outer_frame.pack(fill="both", expand=True)

    canvas = tk.Canvas(outer_frame, borderwidth=0, highlightthickness=0)
    scrollbar = ttk.Scrollbar(outer_frame, orient="vertical", command=canvas.yview)

    scroll_frame = ttk.Frame(canvas)
    scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    canvas_frame = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

    def expandir_horizontal(event):
        canvas.itemconfig(canvas_frame, width=event.width)

    canvas.bind("<Configure>", expandir_horizontal)

    def _on_mousewheel(event):
        canvas.yview_scroll(-1 * int(event.delta / 120), "units")

    scroll_frame.bind_all("<MouseWheel>", _on_mousewheel)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    canvas.configure(yscrollcommand=scrollbar.set)

    if not DB_PATH.exists():
        mostrar_mensagem_boas_vindas(scroll_frame)
        return

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, caminho_videos FROM canais ORDER BY nome ASC")
        canais = cursor.fetchall()

    if not canais:
        mostrar_mensagem_boas_vindas(scroll_frame)
        return

    for canal_id, nome, caminho_videos in canais:
        pendentes, total = obter_contagem_videos(nome)

        frame = ttk.Frame(scroll_frame, padding=(10, 4), style="secondary.TFrame")
        frame.pack(fill="x", pady=2, padx=5)

        info_frame = ttk.Frame(frame)
        info_frame.pack(side="left", fill="x", expand=True)

        ttk.Label(info_frame, text=nome, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        ttk.Label(info_frame, text=f"🎯 Pendentes: {pendentes} | 📦 Total: {total}", font=("Segoe UI", 9)).pack(anchor="w")

        botoes_frame = ttk.Frame(frame)
        botoes_frame.pack(side="right")

        ttk.Button(
            botoes_frame,
            text="📂 Ver Vídeos",
            bootstyle="warning-outline",
            width=13,
            command=lambda n=nome: abrir_modal_lista_videos_por_canal(
                janela_pai=container.winfo_toplevel(),
                canal_nome=n,
                callback_atualizar_canais=lambda: criar_lista_canais(container)
            )


        ).pack(side="left", padx=2, pady=2)

        ttk.Button(
            botoes_frame,
            text="⚙ Configurar",
            bootstyle="info-outline",
            width=13,
            command=lambda c=canal_id: abrir_modal_configurar_canal(
                janela_pai=container.winfo_toplevel(),
                canal_id=c,
                callback_atualizar_lista=lambda: criar_lista_canais(container)
            )
        ).pack(side="left", padx=2, pady=2)


def mostrar_mensagem_boas_vindas(frame_destino):
    mensagem = (
        "⚠ Nenhum canal encontrado!\n\n"
        "🎯 Já pensou em ganhar dinheiro no automático com vídeos que trabalham por você?\n\n"
        "💡 Com o VideoForge v1.0.0 você transforma ideias em vídeos prontos para viralizar — mesmo dormindo.\n\n"
        "🚀 Comece agora clicando em *'Criar Canal'* na barra lateral à esquerda e dê o primeiro passo rumo à automação total.\n\n"
        "💰 Quanto antes começar, mais cedo os resultados aparecem. Está pronto para escalar?"
    )

    ttk.Label(
        frame_destino,
        text=mensagem,
        font=("Segoe UI", 10, "italic"),
        justify="center",
        wraplength=600
    ).pack(pady=50)
