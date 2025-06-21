import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
import threading
from ttkbootstrap.constants import *

# Importações de módulos locais
from modal_criar_canal import abrir_modal_criar_canal
from modal_adicionar_videos import abrir_modal_adicionar_videos
from modal_lista_canais import criar_lista_canais
from db_manager import inicializar_bancos_de_dados

# Importações para o VideoForge (movidas para o topo para eficiência)
from app_videoforge.abrir_modal_videoforge import abrir_modal_videoforge as videoforge_abrir_modal
from app_videoforge.controller import iniciar_fluxo_videoforge
from app_videoforge import controller as videoforge_controller # Renomeado para evitar conflito se houver outro 'controller'

# Chame a função de inicialização do banco de dados antes de qualquer outra coisa
try:
    inicializar_bancos_de_dados()
except Exception as e:
    # Se a inicialização falhar, o app não pode continuar.
    # Em uma aplicação real, você poderia usar um messagebox aqui antes de sair.
    print(f"Falha crítica na inicialização do banco de dados: {e}")
    exit()

class GeradorDeVideosApp:
    def __init__(self, root):
        """
        Inicializa a aplicação Gerador De Videos.

        Args:
            root (tb.Window): A janela principal da aplicação.
        """
        self.root = root
        self.root.title("Gerador De Videos")
        self.root.geometry("1000x600")
        self.root.minsize(800, 500)

        # Aplica o estilo ttkbootstrap
        style = tb.Style("darkly")

        # Container principal que preenche toda a janela
        self.container = ttk.Frame(self.root)
        self.container.pack(fill=BOTH, expand=True)

        # Sidebar (painel lateral esquerdo)
        self.sidebar = ttk.Frame(self.container, width=150, style="secondary.TFrame", padding=(5, 30))
        self.sidebar.pack(side=LEFT, fill=Y)
        self.sidebar.pack_propagate(False) # Impede que o sidebar se ajuste ao conteúdo

        # Linha divisória entre o sidebar e a área principal
        self.divider = ttk.Separator(self.container, orient=VERTICAL)
        self.divider.pack(side=LEFT, fill=Y)

        # Área principal (painel direito)
        self.main_frame = ttk.Frame(self.container, padding=20)
        self.main_frame.pack(side=LEFT, fill=BOTH, expand=True)

        # Conteúdo do Sidebar - Menu
        ttk.Label(self.sidebar, text="Menu", style="TLabel", anchor="center", font=("Segoe UI", 12, "bold")).pack(pady=(0, 20))

        # Botão para criar um novo canal
        ttk.Button(
            self.sidebar,
            text="Criar Canal",
            bootstyle="secondary-outline",
            command=lambda: abrir_modal_criar_canal(self.root, callback_atualizar_lista=self.atualizar_lista_canais)
        ).pack(pady=(0, 10), fill=X)

        # Botão para adicionar vídeos a um canal existente
        ttk.Button(
            self.sidebar,
            text="Adicionar Vídeos",
            bootstyle="secondary-outline",
            command=lambda: abrir_modal_adicionar_videos(self.root, callback_atualizar_lista=self.atualizar_lista_canais)
        ).pack(pady=(0, 10), fill=X)

        # Frame para os botões centrais de ação
        self.buttons_frame = ttk.Frame(self.main_frame)
        self.buttons_frame.pack(anchor="center", pady=(20, 30))

        self.botao_style = {"bootstyle": "secondary", "width": 18}

        # Cria os botões centrais
        nomes_botoes = ["Gerar Roteiro", "Botão 2", "Botão 3", "Botão 4"]
        for i, nome in enumerate(nomes_botoes):
            if nome == "Gerar Roteiro":
                # Inicia a função gerar_roteiro em uma nova thread para não bloquear a UI
                action = lambda n=nome: self.add_log(f"Botão '{n}' clicado, porem ainda não funciona")
            else:
                action = lambda n=nome: self.add_log(f"Botão '{n}' clicado") # Usa n=nome para capturar o valor correto
            ttk.Button(self.buttons_frame, text=nome, command=action, **self.botao_style).grid(row=0, column=i, padx=10)

        # Botão VideoForge - Abre o modal para geração de vídeos
        self.videoforge_button = ttk.Button(
            self.main_frame,
            text="VideoForge",
            bootstyle="info",
            width=25,
            command=self.abrir_modal_videoforge # Não precisa de lambda se não há argumentos
        )
        self.videoforge_button.pack(pady=(5, 10))

        # Frame para exibir os logs em tempo real
        self.logs_frame = ttk.Frame(self.main_frame)
        self.logs_frame.pack(side=BOTTOM, fill=X, pady=20)

        ttk.Label(self.logs_frame, text="Logs em tempo real:", style="TLabel").pack(anchor="w")

        # Widget de texto para exibir os logs
        self.log_text = tk.Text(
            self.logs_frame, height=6,
            bg="#1e1e1e", fg="white",
            insertbackground="white", borderwidth=0
        )
        self.log_text.pack(fill=X, pady=(5, 0))

        # Frame para a lista de canais (preenche o espaço restante acima dos logs)
        self.lista_canais_frame = ttk.Frame(self.main_frame)
        self.lista_canais_frame.pack(side=TOP, fill=BOTH, expand=True)

        # Atualiza a lista de canais ao iniciar a aplicação
        self.atualizar_lista_canais()

        # Adiciona uma mensagem de log inicial
        self.add_log("Aplicação iniciada...")

    def atualizar_lista_canais(self):
        """
        Atualiza a exibição da lista de canais na interface.
        """
        # Limpa o frame antes de recriar a lista para evitar duplicatas
        for widget in self.lista_canais_frame.winfo_children():
            widget.destroy()
        criar_lista_canais(self.lista_canais_frame)

    def gerar_roteiro(self):
        """
        Inicia o processo de geração de roteiro em uma thread separada.
        """
        from app_roteiro import controller_roteiro
        controller_roteiro.set_logger(self.add_log) # Define a função de log para o controller do roteiro
        controller_roteiro.iniciar_controller()
        self.add_log("Processo de geração de roteiro concluído.")

    def add_log(self, message):
        """
        Adiciona uma mensagem ao widget de log, garantindo que a atualização seja na thread principal da UI.
        """
        # Usa root.after para agendar a atualização do log na thread principal
        self.root.after(0, lambda: self._actual_add_log_update(message))

    def _actual_add_log_update(self, message):
        """
        Método interno para realizar a atualização do log no widget tk.Text.
        """
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END) # Rola para o final para mostrar a mensagem mais recente

    def abrir_modal_videoforge(self):
        """
        Abre o modal do VideoForge e configura seu logger.
        """
        videoforge_controller.set_logger(self.add_log) # Define a função de log para o controller do VideoForge
        videoforge_abrir_modal(
            self.root,
            callback_executar_controller=iniciar_fluxo_videoforge
        )

# Ponto de entrada da aplicação
if __name__ == "__main__":
    # Cria a janela principal usando ttkbootstrap.Window
    root = tb.Window(themename="darkly")
    # Instancia a aplicação
    app = GeradorDeVideosApp(root)
    # Guarda uma referência global para a instância do app, se necessário
    # (Pode ser removido se não houver dependências externas que precisem dela)
    global app_ref
    app_ref = app
    # Inicia o loop principal da interface gráfica
    root.mainloop()
