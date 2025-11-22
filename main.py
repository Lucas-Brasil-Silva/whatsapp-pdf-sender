import flet as ft
import threading
import time
from typing import Callable

# Importação dos seus módulos
from whatsapp_bot import processar_fila_envio, WhatsAppBot
import contatos
import file_organizer

class AppDisparador:
    def __init__(self, page: ft.Page):
        self.page = page
        self.configurar_janela()
        
        # --- Estado da Aplicação (Referências aos Controles) ---
        self.txt_mensagem = ft.TextField(
            label="Mensagem do WhatsApp",
            hint_text="Digite aqui o texto que acompanhará o arquivo...",
            multiline=True,
            min_lines=3,
            max_lines=4,
            border_radius=10,
            border_color=ft.Colors.BLUE_GREY_200,
            bgcolor=ft.Colors.WHITE,
            text_size=14,
            content_padding=15
        )
        
        # Referências diretas aos textos dos contadores (sem precisar buscar na árvore)
        self.lbl_total = ft.Text("0", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE)
        self.lbl_sucesso = ft.Text("0", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)
        self.lbl_erros = ft.Text("0", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.RED)
        
        # Botão (precisamos da referência para desabilitar/habilitar)
        self.btn_enviar = ft.ElevatedButton(
            text="INICIAR DISPARO",
            icon=ft.Icons.ROCKET_LAUNCH,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.TEAL,
                color=ft.Colors.WHITE,
                padding=20,
                shape=ft.RoundedRectangleBorder(radius=10),
                text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16)
            ),
            width=400,
            on_click=self.iniciar_envio
        )

        # Lista de Logs
        self.log_list = ft.ListView(expand=True, spacing=2, auto_scroll=True, padding=10)

        # Montagem da UI
        self.montar_interface()

    def configurar_janela(self):
        self.page.title = "Bot WhatsApp Sender"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = ft.Colors.BLUE_GREY_50
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.page.window_width = 550 # Ajustado para Flet moderno
        self.page.window_height = 750
        self.page.window_prevent_close = True
        self.page.on_window_event = self.evento_fechar_janela

    def evento_fechar_janela(self, e):
        if e.data == "close":
            self.page.dialog = ft.AlertDialog(
                title=ft.Text("Encerrando..."),
                content=ft.Text("Finalizando processos e fechando navegador."),
                open=True,
                modal=True # Impede clicar fora
            )
            self.page.update()
            
            # Garante que o driver feche
            try:
                # Se seu modulo whatsapp_bot tiver uma instância global ou metodo estático:
                WhatsAppBot(headless=False).fechar() # Ou método específico de cleanup
            except:
                pass
            
            self.page.window_destroy()

    # --- Métodos de Construção de UI (Helpers) ---
    def _criar_card_stat(self, label: str, controle_texto: ft.Text):
        return ft.Container(
            content=ft.Column([
                controle_texto,
                ft.Text(label, size=10, color=ft.Colors.GREY_600)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=10,
            border=ft.border.all(1, ft.Colors.GREY_200),
            border_radius=8,
            width=100,
            bgcolor=ft.Colors.WHITE
        )

    def montar_interface(self):
        # Cabeçalho
        titulo = ft.Column([
            ft.Text("Disparador de Arquivos", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
            ft.Text("Automação de envio de PDFs via WhatsApp", size=12, color=ft.Colors.GREY_600),
        ], spacing=3)

        # Área de Estatísticas
        row_stats = ft.Row([
            self._criar_card_stat("Total", self.lbl_total),
            self._criar_card_stat("Sucessos", self.lbl_sucesso),
            self._criar_card_stat("Erros", self.lbl_erros),
        ], alignment=ft.MainAxisAlignment.SPACE_EVENLY)

        # Console Container
        console_container = ft.Container(
            content=self.log_list,
            bgcolor=ft.Colors.BLACK87,
            border_radius=10,
            height=200,
            padding=5,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.GREY_400, offset=ft.Offset(0, 5))
        )

        # Card Principal (Corpo)
        main_card = ft.Container(
            content=ft.Column(
                [
                    titulo,
                    ft.Divider(height=15, color=ft.Colors.TRANSPARENT),
                    self.txt_mensagem,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    row_stats,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.Text("Log de Execução:", weight=ft.FontWeight.BOLD, size=12),
                    console_container,
                    ft.Divider(height=15, color=ft.Colors.TRANSPARENT),
                    self.btn_enviar
                ],
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            width=500,
            padding=30,
            bgcolor=ft.Colors.WHITE,
            border_radius=20,
            shadow=ft.BoxShadow(
                blur_radius=20,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 10)
            )
        )

        self.page.add(main_card)

    # --- Lógica de Negócios e Callbacks ---

    def log_msg(self, msg: str, tipo: str = "info"):
        """Adiciona mensagem ao console da UI"""
        cor = ft.Colors.WHITE
        icone = ">"
        
        if tipo == "sucesso": 
            cor, icone = ft.Colors.GREEN_ACCENT, "✔"
        elif tipo == "erro": 
            cor, icone = ft.Colors.RED_ACCENT, "✖"
        elif tipo == "aviso": 
            cor, icone = ft.Colors.YELLOW_ACCENT, "⚠"

        self.log_list.controls.append(
            ft.Text(f"{time.strftime('%H:%M:%S')} [{icone}] {msg}", color=cor, size=12, font_family="Consolas")
        )
        self.page.update()

    def atualizar_stats(self, total, ok, erros):
        """Atualiza os números na UI"""
        self.lbl_total.value = str(total)
        self.lbl_sucesso.value = str(ok)
        self.lbl_erros.value = str(erros)
        self.page.update()

    def _thread_tarefa(self, arquivos, mensagem):
        """Função que roda em segundo plano"""
        # Chama a função do seu módulo whatsapp_bot
        processar_fila_envio(
            caminhos_arquivos=arquivos, 
            mensagem=mensagem, 
            callbacks=(self.log_msg, self.atualizar_stats)
        )
        
        # Pós-processamento (Reabilitar UI)
        self.btn_enviar.disabled = False
        self.btn_enviar.text = "INICIAR NOVO DISPARO"
        self.txt_mensagem.disabled = False
        self.page.update()

    def iniciar_envio(self, e):
        mensagem = self.txt_mensagem.value
        
        # Validação simples
        if not mensagem or not mensagem.strip():
            self.txt_mensagem.error_text = "Por favor, escreva uma mensagem."
            self.txt_mensagem.update()
            
            # Garante estruturas (caso o usuário tenha apagado pastas)
            file_organizer.criar_estruturas_pastas()
            contatos.garantir_existencia_csv()
            return
        
        self.txt_mensagem.error_text = None
        
        # Preparação
        try:
            arquivos = file_organizer.listar_pdfs_na_pasta()
        except Exception as ex:
            self.log_msg(f"Erro ao ler pasta: {ex}", "erro")
            return

        if not arquivos:
            self.log_msg("Nenhum arquivo PDF encontrado na pasta 'enviar_pdfs'.", "aviso")
            return

        # Trava UI
        self.btn_enviar.disabled = True
        self.btn_enviar.text = "ENVIANDO..."
        self.txt_mensagem.disabled = True
        self.atualizar_stats(len(arquivos), 0, 0)
        self.log_msg("Iniciando thread de envio...", "info")
        
        # Inicia Thread para não travar a janela
        threading.Thread(
            target=self._thread_tarefa, 
            args=(arquivos, mensagem), 
            daemon=True
        ).start()

# --- Ponto de Entrada ---
def main(page: ft.Page):
    AppDisparador(page)

if __name__ == "__main__":
    ft.app(target=main)