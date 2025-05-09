import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
import threading
from ttkbootstrap.constants import *


from modal_criar_canal import abrir_modal_criar_canal
from modal_adicionar_videos import abrir_modal_adicionar_videos


from app_roteiro import controller_roteiro


class GeradorDeVideosApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerador De Videos")
        self.root.geometry("1000x600")
        self.root.minsize(800, 500)

        style = tb.Style("darkly")

        # Container principal
        self.container = ttk.Frame(self.root)
        self.container.pack(fill=BOTH, expand=True)

        # Sidebar mais larga com padding
        self.sidebar = ttk.Frame(self.container, width=150, style="secondary.TFrame", padding=(20, 30))
        self.sidebar.pack(side=LEFT, fill=Y)
        self.sidebar.pack_propagate(False)  # Impede a sidebar de encolher com o conteúdo

        # Linha divisória
        self.divider = ttk.Separator(self.container, orient=VERTICAL)
        self.divider.pack(side=LEFT, fill=Y)

        # Conteúdo principal
        self.main_frame = ttk.Frame(self.container, padding=20)
        self.main_frame.pack(side=LEFT, fill=BOTH, expand=True)

        # Título da sidebar (centralizado)
        ttk.Label(self.sidebar, text="Menu", style="TLabel", anchor="center", font=("Segoe UI", 12, "bold")).pack(pady=(0, 20))

        ttk.Button(
            self.sidebar, 
            text="Criar Canal", 
            bootstyle="secondary-outline", 
            command=lambda: abrir_modal_criar_canal(self.root)
        ).pack(pady=(0, 10), fill=X)

        ttk.Button(
            self.sidebar, 
            text="Adicionar Vídeos", 
            bootstyle="secondary-outline", 
            command=lambda: abrir_modal_adicionar_videos(self.root)
        ).pack(pady=(0, 10), fill=X)



        # Botões centrais
        self.buttons_frame = ttk.Frame(self.main_frame)
        self.buttons_frame.pack(anchor="center", pady=(20, 30))

        self.botao_style = {"bootstyle": "secondary", "width": 18}

        nomes_botoes = ["Gerar Roteiro", "Botão 2", "Botão 3", "Botão 4"]
        for i, nome in enumerate(nomes_botoes):
            if nome == "Gerar Roteiro":
                action = lambda: threading.Thread(target=controller_roteiro.iniciar_controller, daemon=True).start()
            else:
                action = lambda: self.add_log(f"Botão {nome} clicado")

            ttk.Button(self.buttons_frame, text=nome, command=action, **self.botao_style).grid(row=0, column=i, padx=10)



        # Logs inferiores
        self.logs_frame = ttk.Frame(self.main_frame)
        self.logs_frame.pack(side=BOTTOM, fill=X, pady=20)

        ttk.Label(self.logs_frame, text="Logs em tempo real:", style="TLabel").pack(anchor="w")

        self.log_text = tk.Text(self.logs_frame, height=8, bg="#1e1e1e", fg="white", insertbackground="white", borderwidth=0)
        self.log_text.pack(fill=X, pady=(5, 0))

        self.add_log("Aplicação iniciada...")

        controller_roteiro.set_logger(self.add_log)


    def add_log(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)

if __name__ == "__main__":
    root = tb.Window(themename="darkly")
    app = GeradorDeVideosApp(root)
    root.mainloop()
