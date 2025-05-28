import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
import sqlite3
from pathlib import Path
from datetime import datetime
from modal_configuracoes_avancadas_video import abrir_modal_configuracoes_avancadas_video

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

STATUS_OK_MAP = {0: "Não feito", 1: "OK", 2: "Ignorado"}
INVERSE_STATUS_OK_MAP = {v: k for k, v in STATUS_OK_MAP.items()}
INVERSE_ESTADOS = {v: k for k, v in ESTADOS.items()}

def abrir_modal_editar_video(janela_pai, video_id, canal_nome, callback_atualizar_lista=None):
    modal = tb.Toplevel(janela_pai)
    modal.title(f"Editar Vídeo {video_id} - {canal_nome}")
    modal.geometry("500x550")
    modal.grab_set()

    switches = {}
    datas_atuais = {}

    with sqlite3.connect(VIDEOS_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT roteiro_ok, audio_ok, legenda_ok, metadado_ok, thumb_ok,
                   estado, roteiro_data, audio_data, legenda_data, metadado_data, thumb_data
            FROM videos
            WHERE canal = ? AND video_id = ?
        """, (canal_nome, video_id))
        dados = cursor.fetchone()

    if not dados:
        messagebox.showerror("Erro", "Vídeo não encontrado.")
        modal.destroy()
        return

    valores_ok = list(dados[:5])
    estado = dados[5]
    datas = list(dados[6:])

    frame = ttk.Frame(modal)
    frame.pack(padx=20, pady=20, fill="both", expand=True)

    chaves = ["roteiro_ok", "audio_ok", "legenda_ok", "metadado_ok", "thumb_ok"]
    datas_keys = ["roteiro_data", "audio_data", "legenda_data", "metadado_data", "thumb_data"]
    textos = ["Roteiro", "Áudio", "Legenda", "Metadado", "Thumb"]

    def ao_alterar_switch(chave, data_key, var):
        valor = INVERSE_STATUS_OK_MAP[var.get()]
        if valor == 1:
            datas_atuais[data_key] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            datas_atuais[data_key] = ""

    for i in range(5):
        valor_textual = STATUS_OK_MAP.get(valores_ok[i], "Não feito")
        var = tk.StringVar(value=valor_textual)

        ttk.Label(frame, text=f"{textos[i]}").pack(anchor="w", pady=(10, 0))
        combo = ttk.Combobox(frame, textvariable=var, state="readonly", values=list(STATUS_OK_MAP.values()), width=20)
        combo.pack(anchor="w")
        switches[chaves[i]] = var
        datas_atuais[datas_keys[i]] = datas[i] or ""

        combo.bind("<<ComboboxSelected>>", lambda e, k=chaves[i], d=datas_keys[i], v=var: ao_alterar_switch(k, d, v))

    ttk.Label(frame, text="Estado do Vídeo").pack(pady=(20, 0))
    estado_text = ESTADOS.get(estado, "Pendente")
    estado_var = tk.StringVar(value=estado_text)
    estado_combo = ttk.Combobox(frame, textvariable=estado_var, values=list(ESTADOS.values()), state="readonly")
    estado_combo.pack(fill="x")

    def salvar():
        novos_valores = [INVERSE_STATUS_OK_MAP[switches[k].get()] for k in chaves]
        novas_datas = [datas_atuais[k] for k in datas_keys]
        novo_estado = INVERSE_ESTADOS.get(estado_var.get(), 0)

        with sqlite3.connect(VIDEOS_DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE videos SET
                    roteiro_ok = ?, audio_ok = ?, legenda_ok = ?, metadado_ok = ?, thumb_ok = ?,
                    estado = ?,
                    roteiro_data = ?, audio_data = ?, legenda_data = ?, metadado_data = ?, thumb_data = ?
                WHERE canal = ? AND video_id = ?
            """, (*novos_valores, novo_estado, *novas_datas, canal_nome, video_id))
            conn.commit()

        if callback_atualizar_lista:
            callback_atualizar_lista()

        messagebox.showinfo("Salvo", "Dados do vídeo atualizados com sucesso.")
        modal.destroy()

    # 🔘 Botões finais
    ttk.Button(modal, text="Salvar Alterações", bootstyle="success", command=salvar).pack(pady=(15, 5))
    ttk.Button(modal, text="⚙️ Configurações Avançadas", bootstyle="dark-outline", command=lambda: abrir_modal_configuracoes_avancadas_video(
        janela_pai=janela_pai,
        video_id=video_id,
        fechar_modal_pai=modal.destroy
    )).pack(pady=5)

    ttk.Button(modal, text="Cancelar", command=modal.destroy).pack(pady=(5, 15))
