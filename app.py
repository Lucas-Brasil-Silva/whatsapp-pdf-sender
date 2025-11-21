import flet as ft
import time
import threading
from send_pdf_whatsapp_selenium import send_pdf
import gerenciador_csv
import lista_pdfs

def main(page: ft.Page):
    # --- Configurações da Janela ---
    page.title = "Bot WhatsApp Sender"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.Colors.BLUE_GREY_50 # Fundo da janela (fora do card)
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.window_min_width = 500
    page.window_height = 700

    # ==============================================================================
    # ELEMENTOS DA UI
    # ==============================================================================

    # 1. Título e Subtítulo
    titulo = ft.Column([
        ft.Text("Disparador de Arquivos", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
        ft.Text("Configure a mensagem e inicie o envio para a lista carregada.", size=12, color=ft.Colors.GREY_600),
    ], spacing=3)

    # 2. Input de Mensagem
    txt_mensagem = ft.TextField(
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
    
    # Contadores (Pequenos cards de estatística)
    def criar_contador(label, valor, cor):
        return ft.Container(
            content=ft.Column([
                ft.Text(str(valor), size=18, weight=ft.FontWeight.BOLD, color=cor),
                ft.Text(label, size=10, color=ft.Colors.GREY_600)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=7,
            border=ft.border.all(1, ft.Colors.GREY_200),
            border_radius=8,
            width=100,
            bgcolor=ft.Colors.WHITE
        )

    txt_total = ft.Text("0", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE)
    txt_sucesso = ft.Text("0", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)
    txt_erros = ft.Text("0", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.RED)

    row_stats = ft.Row([
        criar_contador("Total", txt_total.value, ft.Colors.BLUE), # Placeholder, vamos atualizar via ref depois
        criar_contador("Sucessos", txt_sucesso.value, ft.Colors.GREEN),
        criar_contador("Erros", txt_erros.value, ft.Colors.RED),
    ], alignment=ft.MainAxisAlignment.SPACE_EVENLY)
    
    # Hack para atualizar os textos dentro dos containers acima
    # Recriando a row de forma dinâmica seria mais complexo, então vamos simplificar a atualização:
    # (Na prática do Flet, atualizamos o controle de texto, não o container)
    stat_total_container = row_stats.controls[0].content.controls[0]
    stat_sucesso_container = row_stats.controls[1].content.controls[0]
    stat_erro_container = row_stats.controls[2].content.controls[0]


    # 4. Console de Logs (Terminal Style)
    log_list = ft.ListView(expand=True, spacing=2, auto_scroll=True, padding=10)
    
    console_container = ft.Container(
        content=log_list,
        bgcolor=ft.Colors.BLACK87, # Fundo escuro moderno
        border_radius=10,
        height=170, # Altura fixa para o console
        padding=5,
        shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.GREY_400, offset=ft.Offset(0, 5))
    )

    # ==============================================================================
    # LÓGICA
    # ==============================================================================

    def log_msg(msg, tipo="info"):
        cor = ft.Colors.WHITE
        icone = ">"
        if tipo == "sucesso": 
            cor = ft.Colors.GREEN_ACCENT
            icone = "✔"
        elif tipo == "erro": 
            cor = ft.Colors.RED_ACCENT
            icone = "✖"
        elif tipo == "aviso": 
            cor = ft.Colors.YELLOW_ACCENT
            icone = "⚠"

        log_list.controls.append(
            ft.Text(f"{time.strftime('%H:%M:%S')} [{icone}] {msg}", color=cor, size=12, font_family="Consolas")
        )
        page.update()

    def atualizar_stats(total, ok, erros):
        stat_total_container.value = str(total)
        stat_sucesso_container.value = str(ok)
        stat_erro_container.value = str(erros)
        page.update()

    def iniciar_envio(e):
        mensagem = txt_mensagem.value
        # verificar se a mensagem não está vazia
        if mensagem is None or mensagem.strip() == "":
            txt_mensagem.error_text = "Digite uma mensagem!"
            page.update()
            return
        
        else:
            log_msg("Iniciando a execução do programa.", "info")

            lista_arquivos = lista_pdfs.listar_pdfs_na_pasta()

            def thread_target():
                send_pdf(filepath=lista_arquivos,message=mensagem, callback_log=log_msg, callback_progress=atualizar_stats)

                # Reabilita UI após término
                btn_enviar.disabled = False
                txt_mensagem.disabled = False
                page.update()

            threading.Thread(target=thread_target).start()

            # Trava UI
            btn_enviar.disabled = True
            txt_mensagem.disabled = True
            atualizar_stats(len(lista_arquivos), 0, 0)
            page.update()

    # 5. Botão Principal
    btn_enviar = ft.ElevatedButton(
        text="INICIAR DISPARO",
        icon=ft.Icons.ROCKET_LAUNCH,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.TEAL,
            color=ft.Colors.WHITE,
            padding=20,
            shape=ft.RoundedRectangleBorder(radius=10),
            text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16)
        ),
        width=400, # Largura para preencher bem o card
        on_click=iniciar_envio
    )

    # ==============================================================================
    # MONTAGEM DO LAYOUT (CARD CENTRAL)
    # ==============================================================================

    # Este container age como o "Corpo" da aplicação
    main_card = ft.Container(
        content=ft.Column(
            [
                titulo,
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                txt_mensagem,
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                row_stats, # Estatísticas
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                ft.Text("Log de Execução:", weight=ft.FontWeight.BOLD, size=12),
                console_container,
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                btn_enviar
            ],
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH, # Estica os elementos na largura do card
        ),
        width=500, # Largura fixa do card para manter a elegância
        padding=30,
        bgcolor=ft.Colors.WHITE,
        border_radius=20,
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=20,
            color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
            offset=ft.Offset(0, 10)
        )
    )

    # Adiciona o card centralizado na página
    page.add(main_card)

if __name__ == "__main__":
    ft.app(target=main)