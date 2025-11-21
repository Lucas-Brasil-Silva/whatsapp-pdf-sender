import customtkinter as ctk
import threading
import time
import gerenciador_csv

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AppAutomacao(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Configuração da Janela Principal ---
        self.title("Sistema de Automação WhatsApp")
        self.geometry("800x600")
        
        # Dados (Simulando um Banco de Dados)
        # Estrutura: Lista de Dicionários
        self.banco_contatos = gerenciador_csv.ler_dados_csv(gerenciador_csv.CAMINHO_ARQUIVO_CSV)
        self.checkboxes_envio = {}

        # --- Layout Principal (Grid 1x2) ---
        # Coluna 0 = Menu Lateral | Coluna 1 = Área de Conteúdo
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ==================================================
        # 1. MENU LATERAL (NAVEGAÇÃO)
        # ==================================================
        self.frame_menu = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.frame_menu.grid(row=0, column=0, sticky="nsew")
        self.frame_menu.grid_rowconfigure(4, weight=1)

        self.lbl_app = ctk.CTkLabel(self.frame_menu, text="AutoBot", font=("Arial", 20, "bold"))
        self.lbl_app.grid(row=0, column=0, padx=20, pady=20)

        # Botões de Navegação
        self.btn_nav_envio = ctk.CTkButton(self.frame_menu, text="📤 Enviar Arquivos", 
                                           fg_color="transparent", border_width=2, text_color=("gray10", "gray90"),
                                           command=self.mostrar_tela_envio)
        self.btn_nav_envio.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.btn_nav_cadastro = ctk.CTkButton(self.frame_menu, text="👥 Gerenciar Contatos", 
                                              fg_color="transparent", border_width=2, text_color=("gray10", "gray90"),
                                              command=self.mostrar_tela_cadastro)
        self.btn_nav_cadastro.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        # ==================================================
        # 2. TELA DE ENVIO (DISPAROS)
        # ==================================================
        self.frame_envio = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        
        # Conteúdo da Tela de Envio
        ctk.CTkLabel(self.frame_envio, text="Selecione os Contatos para Disparo", font=("Arial", 18)).pack(pady=20)
        
        self.scroll_selecao = ctk.CTkScrollableFrame(self.frame_envio, label_text="Lista de Destinatários")
        self.scroll_selecao.pack(pady=10, padx=40, fill="both", expand=True)

        ctk.CTkLabel(self.frame_envio, text="Mensagem do Arquivo:").pack(pady=(10,0), anchor="w", padx=40)
        self.txt_mensagem = ctk.CTkTextbox(self.frame_envio, height=80)
        self.txt_mensagem.pack(pady=5, padx=40, fill="x")
        self.txt_mensagem.insert("1.0", "Olá! Segue anexo.")

        self.lbl_status = ctk.CTkLabel(self.frame_envio, text="Aguardando...", text_color="gray")
        self.lbl_status.pack(pady=5)

        self.barra_progresso = ctk.CTkProgressBar(self.frame_envio)
        self.barra_progresso.set(0)
        self.barra_progresso.pack(pady=5, padx=40, fill="x")

        self.btn_disparar = ctk.CTkButton(self.frame_envio, text="INICIAR ENVIO 🚀", 
                                          fg_color="green", height=40, command=self.iniciar_disparo)
        self.btn_disparar.pack(pady=20, padx=40, fill="x")

        # ==================================================
        # 3. TELA DE CADASTRO (GERENCIAMENTO)
        # ==================================================
        self.frame_cadastro = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")

        ctk.CTkLabel(self.frame_cadastro, text="Cadastro de Novos Contatos", font=("Arial", 18)).pack(pady=20)

        # Inputs
        self.entry_nome = ctk.CTkEntry(self.frame_cadastro, placeholder_text="Nome do Colaborador")
        self.entry_nome.pack(pady=5, padx=40, fill="x")
        
        self.entry_tel = ctk.CTkEntry(self.frame_cadastro, placeholder_text="Telefone (ex: 5511999999999)")
        self.entry_tel.pack(pady=5, padx=40, fill="x")

        self.btn_salvar = ctk.CTkButton(self.frame_cadastro, text="+ Salvar Contato", command=self.salvar_contato)
        self.btn_salvar.pack(pady=10, padx=40)

        ctk.CTkLabel(self.frame_cadastro, text="Contatos Já Cadastrados:", font=("Arial", 14, "bold")).pack(pady=(30, 10))

        # Lista de Visualização (Apenas leitura)
        self.scroll_visualizacao = ctk.CTkScrollableFrame(self.frame_cadastro, width=400)
        self.scroll_visualizacao.pack(pady=10, padx=40, fill="both", expand=True)


        # Inicialização: Mostra a tela de envio primeiro
        self.mostrar_tela_envio()

    # --- Lógica de Navegação ---
    
    def mostrar_tela_envio(self):
        self.frame_cadastro.grid_forget() # Esconde cadastro
        self.frame_envio.grid(row=0, column=1, sticky="nsew") # Mostra envio
        
        # Muda cor dos botões para indicar qual está ativo
        self.btn_nav_envio.configure(fg_color=("gray75", "gray25"))
        self.btn_nav_cadastro.configure(fg_color="transparent")
        
        self.atualizar_lista_selecao() # Recarrega checkboxes caso tenha novos cadastros

    def mostrar_tela_cadastro(self):
        self.frame_envio.grid_forget() # Esconde envio
        self.frame_cadastro.grid(row=0, column=1, sticky="nsew") # Mostra cadastro

        self.btn_nav_cadastro.configure(fg_color=("gray75", "gray25"))
        self.btn_nav_envio.configure(fg_color="transparent")
        
        self.atualizar_lista_visualizacao() # Recarrega a lista visual

    # --- Lógica de Cadastro ---

    def salvar_contato(self):
        nome = self.entry_nome.get()
        tel = self.entry_tel.get()

        if nome and tel:
            novo_contato = {"Colaborador": nome, "Telefone": tel}
            self.banco_contatos.append(novo_contato)
            
            # Limpa campos e atualiza lista
            self.entry_nome.delete(0, "end")
            self.entry_tel.delete(0, "end")
            self.atualizar_lista_visualizacao()
            print(f"Salvo: {nome} - {tel}")

    def atualizar_lista_visualizacao(self):
        # Limpa a lista visual antiga
        for widget in self.scroll_visualizacao.winfo_children():
            widget.destroy()
        
        # Cria os "Cartões" de contato
        for contato in self.banco_contatos:
            frame_card = ctk.CTkFrame(self.scroll_visualizacao, fg_color=("gray90", "gray30"))
            frame_card.pack(pady=5, padx=5, fill="x")
            
            lbl = ctk.CTkLabel(frame_card, text=f"{contato['Colaborador']}\n{contato['Telefone']}", anchor="w", justify="left")
            lbl.pack(pady=5, padx=10, side="left")

    # --- Lógica de Envio ---

    def atualizar_lista_selecao(self):
        # Limpa checkboxes antigos
        for widget in self.scroll_selecao.winfo_children():
            widget.destroy()
        self.checkboxes_envio = {}

        # Cria novos checkboxes baseados no banco atualizado
        for contato in self.banco_contatos:
            chave = contato['Telefone']
            texto_exibicao = f"{contato['Colaborador']} ({contato['Telefone']})"
            
            chk = ctk.CTkCheckBox(self.scroll_selecao, text=texto_exibicao)
            chk.pack(pady=5, padx=10, anchor="w")
            chk.select()
            
            # Guarda referência usando o telefone como chave
            self.checkboxes_envio[chave] = chk

    def iniciar_disparo(self):
        # Filtra quem está marcado
        telefones_destino = []
        for telefone, chk in self.checkboxes_envio.items():
            if chk.get() == 1:
                telefones_destino.append(telefone)
        
        mensagem = self.txt_mensagem.get("1.0", "end")
        
        if not telefones_destino:
            return

        threading.Thread(target=self.processo_backend, args=(telefones_destino, mensagem)).start()

    def processo_backend(self, lista_telefones, msg):
        self.btn_disparar.configure(state="disabled")
        total = len(lista_telefones)
        arquivo_fixo = r"C:\Temp\arquivo.pdf"

        for i, tel in enumerate(lista_telefones):
            self.lbl_status.configure(text=f"Enviando para {tel}...", text_color="cyan")
            
            # --- AQUI ENTRA SEU SELENIUM ---
            time.sleep(1.5) # Simula envio
            # -------------------------------
            
            self.barra_progresso.set((i+1)/total)

        self.lbl_status.configure(text="Concluído!", text_color="green")
        self.btn_disparar.configure(state="normal")

if __name__ == "__main__":
    app = AppAutomacao()
    app.mainloop()
    

# a interface precisa informar na tela a lista de contatos cadastrados e dar a opção de selecinar as contatos que vão receber o arquivo
# Precisa ter uma caixa dde texto onde possa ser informado uma mensagem que irar junto com o arquivo
#  inserir a opção que o usuario pode cadastrar um novo contato na lista de contatos diretamente pela interface
