import os
import ssl

ssl._create_default_https_context = ssl._create_unverified_context
os.environ["PYTHONHTTPSVERIFY"] = "0"

import flet as ft
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Set

from whatsapp_bot import processar_fila_envio, enviar_para_lista, WhatsAppBot
import contatos
import file_organizer
import supabase_client


STATUS_OPTIONS = [
    ("todos", "Todos"),
    ("7",  "Ativo"),
    ("5",  "Férias"),
    ("9",  "Em Teste"),
    ("8",  "Em Processo de Admissão"),
    ("3",  "Aviso Prévio"),
    ("12", "Afastado"),
    ("6",  "Desligado"),
]

STATUS_CORES = {
    "Ativo":                     (ft.Colors.GREEN_100,  ft.Colors.GREEN_900),
    "Férias":                    (ft.Colors.BLUE_100,   ft.Colors.BLUE_900),
    "Em Teste":                  (ft.Colors.AMBER_100,  ft.Colors.AMBER_900),
    "Em Processo de Admissão":   (ft.Colors.PURPLE_100, ft.Colors.PURPLE_900),
    "Aviso Prévio":              (ft.Colors.ORANGE_100, ft.Colors.ORANGE_900),
    "Desligado":                 (ft.Colors.RED_100,    ft.Colors.RED_900),
    "Afastado":                  (ft.Colors.GREY_200,   ft.Colors.GREY_800),
}


class AppDisparador:
    def __init__(self, page: ft.Page):
        self.page = page
        self.configurar_janela()

        # ── Shared state ──────────────────────────────────────────────────
        self._colaboradores_cache: List[Dict] = []
        self._empresas_cache: List[Dict] = []
        self._visiveis_pontual: List[Dict] = []
        self._selecionados_pontual: Set[int] = set()
        self._arquivo_pontual_path: Optional[str] = None
        self._editando_id: Optional[int] = None
        self._excluindo_id: Optional[int] = None

        # ── Controls — Disparador em Massa ────────────────────────────────
        self.txt_mensagem_massa = ft.TextField(
            label="Mensagem do WhatsApp",
            hint_text="Digite aqui o texto que acompanhará o arquivo...",
            multiline=True, min_lines=3, max_lines=4,
            border_radius=10, border_color=ft.Colors.BLUE_GREY_200,
            bgcolor=ft.Colors.WHITE, text_size=14, content_padding=15,
        )
        self.lbl_total   = ft.Text("0", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE)
        self.lbl_sucesso = ft.Text("0", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)
        self.lbl_erros   = ft.Text("0", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.RED)
        self.btn_enviar_massa = ft.ElevatedButton(
            text="INICIAR DISPARO", icon=ft.Icons.ROCKET_LAUNCH,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.TEAL, color=ft.Colors.WHITE, padding=20,
                shape=ft.RoundedRectangleBorder(radius=10),
                text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=16),
            ),
            width=400, on_click=self.iniciar_envio_massa,
        )
        self.log_list_massa = ft.ListView(expand=True, spacing=2, auto_scroll=True, padding=10)

        # ── Controls — Disparo Pontual ────────────────────────────────────
        self.txt_mensagem_pontual = ft.TextField(
            label="Mensagem do WhatsApp",
            hint_text="Digite aqui o texto da mensagem (obrigatório)...",
            multiline=True, min_lines=3, max_lines=4,
            border_radius=10, border_color=ft.Colors.BLUE_GREY_200,
            bgcolor=ft.Colors.WHITE, text_size=14, content_padding=15,
        )
        self.lbl_arquivo_pontual = ft.Text(
            "Sem arquivo — somente mensagem de texto", color=ft.Colors.GREY_500, size=12, italic=True,
        )
        self.file_picker = ft.FilePicker(on_result=self._on_file_picked)
        self.tf_busca_pontual = ft.TextField(
            label="Buscar colaborador...", prefix_icon=ft.Icons.SEARCH,
            border_radius=10, border_color=ft.Colors.BLUE_GREY_200,
            bgcolor=ft.Colors.WHITE, text_size=13,
            on_change=lambda e: self._filtrar_pontual(),
            expand=True,
        )
        self.dd_empresa_pontual = ft.Dropdown(
            label="Empresa", border_radius=10, border_color=ft.Colors.BLUE_GREY_200,
            bgcolor=ft.Colors.WHITE, value="todos",
            options=[ft.dropdown.Option("todos", "Todas as empresas")],
            width=210, on_change=lambda e: self._filtrar_pontual(),
        )
        self.cb_selecionar_todos = ft.Checkbox(
            label="Selecionar todos", value=False,
            on_change=self._on_selecionar_todos_change,
        )
        self.lista_colaboradores_pontual = ft.ListView(spacing=0)
        self.lbl_total_pontual   = ft.Text("0", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE)
        self.lbl_sucesso_pontual = ft.Text("0", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN)
        self.lbl_erros_pontual   = ft.Text("0", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.RED)
        self.btn_enviar_pontual = ft.ElevatedButton(
            text="ENVIAR PARA SELECIONADOS", icon=ft.Icons.SEND,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.TEAL, color=ft.Colors.WHITE, padding=20,
                shape=ft.RoundedRectangleBorder(radius=10),
                text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=15),
            ),
            on_click=self.iniciar_envio_pontual,
        )
        self.log_list_pontual = ft.ListView(expand=True, spacing=2, auto_scroll=True, padding=10)

        # ── Controls — Contatos ───────────────────────────────────────────
        self.tf_nome = ft.TextField(
            label="Nome completo", border_radius=10,
            border_color=ft.Colors.BLUE_GREY_200, bgcolor=ft.Colors.WHITE, expand=True,
        )
        self.tf_telefone = ft.TextField(
            label="Telefone", hint_text="55DDD...", border_radius=10,
            border_color=ft.Colors.BLUE_GREY_200, bgcolor=ft.Colors.WHITE, width=180,
        )
        self.dd_empresa = ft.Dropdown(
            label="Empresa", border_radius=10,
            border_color=ft.Colors.BLUE_GREY_200, bgcolor=ft.Colors.WHITE,
            options=[], expand=True,
        )
        self.dd_novo_status = ft.Dropdown(
            label="Status", border_radius=10,
            border_color=ft.Colors.BLUE_GREY_200, bgcolor=ft.Colors.WHITE, value="7",
            options=[ft.dropdown.Option(k, v) for k, v in STATUS_OPTIONS if k != "todos"],
            expand=True,
        )
        self.btn_adicionar = ft.ElevatedButton(
            text="+ Adicionar Colaborador", icon=ft.Icons.PERSON_ADD,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.TEAL, color=ft.Colors.WHITE,
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
            on_click=self.adicionar_colaborador,
        )
        self.tabela_contatos = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Nome",     weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Telefone", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Empresa",  weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Status",   weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Ações",    weight=ft.FontWeight.BOLD)),
            ],
            rows=[],
            border=ft.border.all(1, ft.Colors.GREY_200),
            border_radius=10,
            horizontal_lines=ft.BorderSide(1, ft.Colors.GREY_100),
            column_spacing=16,
        )
        self.lbl_status_contatos = ft.Text("", color=ft.Colors.GREY_600, size=12)
        self.tf_busca_contatos = ft.TextField(
            label="Buscar colaborador...", prefix_icon=ft.Icons.SEARCH,
            border_radius=10, border_color=ft.Colors.BLUE_GREY_200,
            bgcolor=ft.Colors.WHITE, text_size=13,
            on_change=lambda e: self._filtrar_contatos(),
            expand=True,
        )
        self.dd_status_contatos = ft.Dropdown(
            label="Filtrar por status", border_radius=10,
            border_color=ft.Colors.BLUE_GREY_200, bgcolor=ft.Colors.WHITE, value="7",
            options=[ft.dropdown.Option(k, v) for k, v in STATUS_OPTIONS],
            width=230, on_change=lambda e: self._filtrar_contatos(),
        )

        # ── Controls — Dialog de Edição ───────────────────────────────────
        self.tf_edit_nome = ft.TextField(
            label="Nome completo", border_radius=10,
            border_color=ft.Colors.BLUE_GREY_200, bgcolor=ft.Colors.WHITE,
        )
        self.tf_edit_telefone = ft.TextField(
            label="Telefone", border_radius=10,
            border_color=ft.Colors.BLUE_GREY_200, bgcolor=ft.Colors.WHITE,
        )
        self.dd_edit_empresa = ft.Dropdown(
            label="Empresa", border_radius=10,
            border_color=ft.Colors.BLUE_GREY_200, bgcolor=ft.Colors.WHITE, options=[],
        )
        self.dd_edit_status = ft.Dropdown(
            label="Status", border_radius=10,
            border_color=ft.Colors.BLUE_GREY_200, bgcolor=ft.Colors.WHITE,
            options=[ft.dropdown.Option(k, v) for k, v in STATUS_OPTIONS if k != "todos"],
        )
        self._btn_salvar_edicao = ft.TextButton(
            "Salvar", icon=ft.Icons.SAVE, on_click=self._salvar_edicao,
        )
        self.dlg_editar = ft.AlertDialog(
            modal=True,
            title=ft.Text("Editar Colaborador", weight=ft.FontWeight.BOLD),
            content=ft.Column(
                [self.tf_edit_nome, self.tf_edit_telefone, self.dd_edit_empresa, self.dd_edit_status],
                spacing=12, tight=True, width=400,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._fechar_dialog(self.dlg_editar)),
                self._btn_salvar_edicao,
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        # ── Controls — Dialog de Exclusão ─────────────────────────────────
        self.lbl_excluir_nome = ft.Text("", weight=ft.FontWeight.BOLD, size=14)
        self.dlg_excluir = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar Exclusão", weight=ft.FontWeight.BOLD),
            content=ft.Column(
                [
                    ft.Text("Tem certeza que deseja excluir:"),
                    self.lbl_excluir_nome,
                    ft.Text("Esta ação não pode ser desfeita.", color=ft.Colors.RED_700, size=12),
                ],
                spacing=6, tight=True,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self._fechar_dialog(self.dlg_excluir)),
                ft.TextButton(
                    "Excluir", icon=ft.Icons.DELETE,
                    style=ft.ButtonStyle(color=ft.Colors.RED),
                    on_click=self._confirmar_exclusao,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        # ── Navigation Rail ───────────────────────────────────────────────
        self.nav_rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            bgcolor=ft.Colors.WHITE,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icons.ROCKET_LAUNCH_OUTLINED,
                    selected_icon=ft.Icons.ROCKET_LAUNCH,
                    label="Massa",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.SEND_OUTLINED,
                    selected_icon=ft.Icons.SEND,
                    label="Pontual",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.PEOPLE_OUTLINED,
                    selected_icon=ft.Icons.PEOPLE,
                    label="Contatos",
                ),
            ],
            on_change=self.on_nav_change,
        )

        # ── Build screens ─────────────────────────────────────────────────
        self.tela_massa    = self._montar_tela_massa()
        self.tela_pontual  = self._montar_tela_pontual()
        self.tela_contatos = self._montar_tela_contatos()

        self.stack_telas = ft.Stack(
            controls=[self.tela_massa, self.tela_pontual, self.tela_contatos],
            expand=True,
        )

        self.page.overlay.extend([self.file_picker, self.dlg_editar, self.dlg_excluir])

        self.page.add(
            ft.Row(
                [
                    self.nav_rail,
                    ft.VerticalDivider(width=1, color=ft.Colors.GREY_200),
                    self.stack_telas,
                ],
                expand=True,
                spacing=0,
                vertical_alignment=ft.CrossAxisAlignment.START,
            )
        )

        threading.Thread(target=self._carregar_dados_iniciais, daemon=True).start()

    # ──────────────────────────────────────────────────────────────────────
    #  Window
    # ──────────────────────────────────────────────────────────────────────

    def configurar_janela(self):
        self.page.title = "Bot WhatsApp Sender"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = ft.Colors.BLUE_GREY_50
        self.page.padding = 0
        self.page.window_width = 900
        self.page.window_height = 820
        self.page.window_prevent_close = True
        self.page.on_window_event = self.evento_fechar_janela

    def evento_fechar_janela(self, e):
        if e.data == "close":
            self.page.dialog = ft.AlertDialog(
                title=ft.Text("Encerrando..."),
                content=ft.Text("Finalizando processos e fechando navegador."),
                open=True, modal=True,
            )
            self.page.update()
            try:
                WhatsAppBot(headless=False).fechar()
            except Exception:
                pass
            self.page.window_destroy()

    # ──────────────────────────────────────────────────────────────────────
    #  Navigation
    # ──────────────────────────────────────────────────────────────────────

    def on_nav_change(self, e):
        idx = self.nav_rail.selected_index
        self.tela_massa.visible    = (idx == 0)
        self.tela_pontual.visible  = (idx == 1)
        self.tela_contatos.visible = (idx == 2)
        self.page.update()

    # ──────────────────────────────────────────────────────────────────────
    #  Shared UI helpers
    # ──────────────────────────────────────────────────────────────────────

    def _criar_card_stat(self, label: str, ctrl: ft.Text) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [ctrl, ft.Text(label, size=10, color=ft.Colors.GREY_600)],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=10, border=ft.border.all(1, ft.Colors.GREY_200),
            border_radius=8, width=100, bgcolor=ft.Colors.WHITE,
        )

    def _status_badge(self, descricao: str) -> ft.Container:
        bg, fg = STATUS_CORES.get(descricao, (ft.Colors.GREY_100, ft.Colors.GREY_700))
        return ft.Container(
            content=ft.Text(descricao, size=10, color=fg),
            bgcolor=bg, border_radius=4,
            padding=ft.padding.symmetric(horizontal=6, vertical=2),
        )

    # ──────────────────────────────────────────────────────────────────────
    #  Data loading
    # ──────────────────────────────────────────────────────────────────────

    def _carregar_dados_iniciais(self):
        try:
            self._colaboradores_cache = supabase_client.listar_colaboradores()
            self._empresas_cache = supabase_client.listar_empresas()
            opcoes_empresa = [
                ft.dropdown.Option(key=str(e["id_empresa"]), text=e["nome_empresa"])
                for e in self._empresas_cache
            ]
            self.dd_empresa.options = opcoes_empresa
            self.dd_edit_empresa.options = opcoes_empresa
            self.dd_empresa_pontual.options = [
                ft.dropdown.Option("todos", "Todas as empresas")
            ] + opcoes_empresa
            self._filtrar_contatos(update=False)
            self._filtrar_pontual(update=False)
        except Exception as ex:
            self.lbl_status_contatos.value = f"Erro ao carregar dados: {ex}"
        finally:
            self.page.update()

    # ──────────────────────────────────────────────────────────────────────
    #  Screen builders
    # ──────────────────────────────────────────────────────────────────────

    def _montar_tela_massa(self) -> ft.Container:
        titulo = ft.Column(
            [
                ft.Text("Disparador em Massa", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
                ft.Text("Lê todos os arquivos da pasta 'enviar_pdfs' e envia via WhatsApp", size=11, color=ft.Colors.GREY_600),
            ],
            spacing=3,
        )
        row_stats = ft.Row(
            [
                self._criar_card_stat("Total",    self.lbl_total),
                self._criar_card_stat("Sucessos", self.lbl_sucesso),
                self._criar_card_stat("Erros",    self.lbl_erros),
            ],
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
        )
        console = ft.Container(
            content=self.log_list_massa, bgcolor=ft.Colors.BLACK87,
            border_radius=10, height=200, padding=5,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.GREY_400, offset=ft.Offset(0, 5)),
        )
        card = ft.Container(
            content=ft.Column(
                [
                    titulo,
                    ft.Divider(height=15, color=ft.Colors.TRANSPARENT),
                    self.txt_mensagem_massa,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    row_stats,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.Text("Log de Execução:", weight=ft.FontWeight.BOLD, size=12),
                    console,
                    ft.Divider(height=15, color=ft.Colors.TRANSPARENT),
                    self.btn_enviar_massa,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
            width=540, padding=30, bgcolor=ft.Colors.WHITE, border_radius=20,
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK), offset=ft.Offset(0, 10)),
        )
        return ft.Container(
            content=ft.Column([card], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO),
            expand=True, visible=True,
            padding=ft.padding.symmetric(vertical=20, horizontal=10),
        )

    def _montar_tela_pontual(self) -> ft.Container:
        titulo = ft.Column(
            [
                ft.Text("Disparo Pontual", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
                ft.Text("Selecione colaboradores e um arquivo para envio", size=11, color=ft.Colors.GREY_600),
            ],
            spacing=3,
        )
        arquivo_row = ft.Row(
            [
                ft.ElevatedButton(
                    text="Anexar Arquivo (opcional)", icon=ft.Icons.ATTACH_FILE,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE_GREY_50, color=ft.Colors.BLUE_GREY_800,
                        shape=ft.RoundedRectangleBorder(radius=8),
                    ),
                    on_click=lambda e: self.file_picker.pick_files(allow_multiple=False),
                ),
                self.lbl_arquivo_pontual,
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=12,
        )
        filtros_row = ft.Row(
            [self.tf_busca_pontual, self.dd_empresa_pontual],
            spacing=10, vertical_alignment=ft.CrossAxisAlignment.END,
        )
        row_stats_pontual = ft.Row(
            [
                self._criar_card_stat("Total",    self.lbl_total_pontual),
                self._criar_card_stat("Sucessos", self.lbl_sucesso_pontual),
                self._criar_card_stat("Erros",    self.lbl_erros_pontual),
            ],
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
        )
        lista_container = ft.Container(
            content=self.lista_colaboradores_pontual,
            border=ft.border.all(1, ft.Colors.GREY_200),
            border_radius=10, height=230, bgcolor=ft.Colors.WHITE,
        )
        console_pontual = ft.Container(
            content=self.log_list_pontual, bgcolor=ft.Colors.BLACK87,
            border_radius=10, height=120, padding=5,
        )
        card = ft.Container(
            content=ft.Column(
                [
                    titulo,
                    ft.Divider(height=12, color=ft.Colors.TRANSPARENT),
                    self.txt_mensagem_pontual,
                    ft.Divider(height=8,  color=ft.Colors.TRANSPARENT),
                    arquivo_row,
                    ft.Divider(height=8,  color=ft.Colors.TRANSPARENT),
                    filtros_row,
                    ft.Divider(height=4,  color=ft.Colors.TRANSPARENT),
                    self.cb_selecionar_todos,
                    ft.Divider(height=2,  color=ft.Colors.GREY_200),
                    lista_container,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    row_stats_pontual,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    self.btn_enviar_pontual,
                    ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                    ft.Text("Log de Execução:", weight=ft.FontWeight.BOLD, size=12),
                    console_pontual,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                scroll=ft.ScrollMode.AUTO,
            ),
            width=560, padding=30, bgcolor=ft.Colors.WHITE, border_radius=20,
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK), offset=ft.Offset(0, 10)),
        )
        return ft.Container(
            content=ft.Column([card], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO),
            expand=True, visible=False,
            padding=ft.padding.symmetric(vertical=20, horizontal=10),
        )

    def _montar_tela_contatos(self) -> ft.Container:
        titulo = ft.Column(
            [
                ft.Text("Gerenciar Contatos", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_GREY_900),
                ft.Text("Colaboradores cadastrados no Supabase", size=11, color=ft.Colors.GREY_600),
            ],
            spacing=3,
        )
        formulario = ft.Container(
            content=ft.Column(
                [
                    ft.Row([self.tf_nome, self.tf_telefone], spacing=10),
                    ft.Row([self.dd_empresa, self.dd_novo_status], spacing=10),
                    ft.Row(
                        [self.btn_adicionar, self.lbl_status_contatos],
                        spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=10,
            ),
            padding=15, border=ft.border.all(1, ft.Colors.GREY_200),
            border_radius=12, bgcolor=ft.Colors.WHITE,
        )
        tabela_scroll = ft.Container(
            content=ft.ListView(controls=[self.tabela_contatos], expand=True),
            expand=True,
            border=ft.border.all(1, ft.Colors.GREY_200),
            border_radius=12, bgcolor=ft.Colors.WHITE,
        )
        card = ft.Container(
            content=ft.Column(
                [
                    titulo,
                    ft.Divider(height=12, color=ft.Colors.TRANSPARENT),
                    formulario,
                    ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
                    ft.Row(
                        [self.tf_busca_contatos, self.dd_status_contatos],
                        spacing=10, vertical_alignment=ft.CrossAxisAlignment.END,
                    ),
                    ft.Divider(height=4, color=ft.Colors.TRANSPARENT),
                    tabela_scroll,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                expand=True,
            ),
            width=620, padding=30, bgcolor=ft.Colors.WHITE, border_radius=20,
            shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK), offset=ft.Offset(0, 10)),
            expand=True,
        )
        return ft.Container(
            content=ft.Column([card], horizontal_alignment=ft.CrossAxisAlignment.CENTER, expand=True),
            expand=True, visible=False,
            padding=ft.padding.symmetric(vertical=20, horizontal=10),
        )

    # ──────────────────────────────────────────────────────────────────────
    #  Disparador em Massa — logic
    # ──────────────────────────────────────────────────────────────────────

    def log_msg(self, msg: str, tipo: str = "info"):
        cor, icone = ft.Colors.WHITE, ">"
        if tipo == "sucesso": cor, icone = ft.Colors.GREEN_ACCENT, "✔"
        elif tipo == "erro":  cor, icone = ft.Colors.RED_ACCENT,   "✖"
        elif tipo == "aviso": cor, icone = ft.Colors.YELLOW_ACCENT, "⚠"
        self.log_list_massa.controls.append(
            ft.Text(f"{time.strftime('%H:%M:%S')} [{icone}] {msg}", color=cor, size=12, font_family="Consolas")
        )
        self.page.update()

    def atualizar_stats(self, total, ok, erros):
        self.lbl_total.value   = str(total)
        self.lbl_sucesso.value = str(ok)
        self.lbl_erros.value   = str(erros)
        self.page.update()

    def _thread_tarefa_massa(self, arquivos, mensagem):
        processar_fila_envio(
            caminhos_arquivos=arquivos,
            mensagem=mensagem,
            callbacks=(self.log_msg, self.atualizar_stats),
        )
        self.btn_enviar_massa.disabled = False
        self.btn_enviar_massa.text = "INICIAR NOVO DISPARO"
        self.txt_mensagem_massa.disabled = False
        self.page.update()

    def iniciar_envio_massa(self, e):
        mensagem = self.txt_mensagem_massa.value
        if not mensagem or not mensagem.strip():
            self.txt_mensagem_massa.error_text = "Por favor, escreva uma mensagem."
            self.txt_mensagem_massa.update()
            file_organizer.criar_estruturas_pastas()
            contatos.garantir_existencia_csv()
            return

        self.txt_mensagem_massa.error_text = None
        try:
            arquivos = file_organizer.listar_arquivos_na_pasta()
        except Exception as ex:
            self.log_msg(f"Erro ao ler pasta: {ex}", "erro")
            return

        if not arquivos:
            self.log_msg("Nenhum arquivo encontrado na pasta 'enviar_pdfs'.", "aviso")
            return

        self.btn_enviar_massa.disabled = True
        self.btn_enviar_massa.text = "ENVIANDO..."
        self.txt_mensagem_massa.disabled = True
        self.atualizar_stats(len(arquivos), 0, 0)
        self.log_msg("Iniciando thread de envio...", "info")
        threading.Thread(target=self._thread_tarefa_massa, args=(arquivos, mensagem), daemon=True).start()

    # ──────────────────────────────────────────────────────────────────────
    #  Disparo Pontual — logic
    # ──────────────────────────────────────────────────────────────────────

    def _on_file_picked(self, e: ft.FilePickerResultEvent):
        if e.files:
            self._arquivo_pontual_path = e.files[0].path
            self.lbl_arquivo_pontual.value  = e.files[0].name
            self.lbl_arquivo_pontual.color  = ft.Colors.BLUE_GREY_800
            self.lbl_arquivo_pontual.italic = False
        else:
            self._arquivo_pontual_path = None
            self.lbl_arquivo_pontual.value  = "Sem arquivo — somente mensagem de texto"
            self.lbl_arquivo_pontual.color  = ft.Colors.GREY_500
            self.lbl_arquivo_pontual.italic = True
        self.page.update()

    def _construir_item_pontual(self, c: Dict) -> ft.Container:
        id_col  = c["id_colaborador"]
        nome    = c.get("nome_completo", "")
        tel     = c.get("telefone", "") or "-"
        empresa = (c.get("empresas") or {}).get("nome_empresa", "")
        return ft.Container(
            content=ft.Row(
                [
                    ft.Checkbox(
                        value=(id_col in self._selecionados_pontual),
                        on_change=lambda e, cid=id_col: self._on_checkbox_change(e, cid),
                    ),
                    ft.Column(
                        [
                            ft.Text(nome, size=12, weight=ft.FontWeight.W_500),
                            ft.Text(f"{tel}  {empresa}", size=10, color=ft.Colors.GREY_600),
                        ],
                        spacing=1, tight=True,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.symmetric(vertical=3, horizontal=8),
        )

    def _filtrar_pontual(self, update: bool = True):
        busca       = (self.tf_busca_pontual.value or "").lower().strip()
        empresa_val = self.dd_empresa_pontual.value or "todos"

        resultado = self._colaboradores_cache

        if empresa_val != "todos":
            try:
                eid = int(empresa_val)
                resultado = [c for c in resultado if c.get("id_empresa") == eid]
            except ValueError:
                pass

        if busca:
            resultado = [c for c in resultado if busca in c.get("nome_completo", "").lower()]

        self._visiveis_pontual = resultado
        self.lista_colaboradores_pontual.controls = [self._construir_item_pontual(c) for c in resultado]
        self._atualizar_btn_pontual()
        if update:
            self.page.update()

    def _on_checkbox_change(self, e, id_col: int):
        if e.control.value:
            self._selecionados_pontual.add(id_col)
        else:
            self._selecionados_pontual.discard(id_col)
        self._atualizar_btn_pontual()
        self.page.update()

    def _on_selecionar_todos_change(self, e):
        if e.control.value:
            for c in self._visiveis_pontual:
                self._selecionados_pontual.add(c["id_colaborador"])
        else:
            for c in self._visiveis_pontual:
                self._selecionados_pontual.discard(c["id_colaborador"])
        self._filtrar_pontual()

    def _atualizar_btn_pontual(self):
        count = len(self._selecionados_pontual)
        self.btn_enviar_pontual.text = (
            f"ENVIAR PARA SELECIONADOS ({count})" if count else "ENVIAR PARA SELECIONADOS"
        )

    def log_msg_pontual(self, msg: str, tipo: str = "info"):
        cor, icone = ft.Colors.WHITE, ">"
        if tipo == "sucesso": cor, icone = ft.Colors.GREEN_ACCENT, "✔"
        elif tipo == "erro":  cor, icone = ft.Colors.RED_ACCENT,   "✖"
        elif tipo == "aviso": cor, icone = ft.Colors.YELLOW_ACCENT, "⚠"
        self.log_list_pontual.controls.append(
            ft.Text(f"{time.strftime('%H:%M:%S')} [{icone}] {msg}", color=cor, size=12, font_family="Consolas")
        )
        self.page.update()

    def atualizar_stats_pontual(self, total, ok, erros):
        self.lbl_total_pontual.value   = str(total)
        self.lbl_sucesso_pontual.value = str(ok)
        self.lbl_erros_pontual.value   = str(erros)
        self.page.update()

    def iniciar_envio_pontual(self, e):
        if not self._selecionados_pontual:
            self.log_msg_pontual("Selecione ao menos um colaborador.", "aviso")
            return

        mensagem = self.txt_mensagem_pontual.value
        if not mensagem or not mensagem.strip():
            self.txt_mensagem_pontual.error_text = "Por favor, escreva uma mensagem."
            self.txt_mensagem_pontual.update()
            return
        self.txt_mensagem_pontual.error_text = None

        colaboradores = [
            c for c in self._colaboradores_cache
            if c["id_colaborador"] in self._selecionados_pontual
        ]

        caminho = Path(self._arquivo_pontual_path) if self._arquivo_pontual_path else None

        self.btn_enviar_pontual.disabled = True
        self.atualizar_stats_pontual(len(colaboradores), 0, 0)
        modo = "arquivo + mensagem" if caminho else "somente mensagem de texto"
        self.log_msg_pontual(f"Iniciando envio ({modo}) para {len(colaboradores)} colaborador(es)...", "info")

        threading.Thread(
            target=self._thread_tarefa_pontual,
            args=(colaboradores, caminho, mensagem),
            daemon=True,
        ).start()

    def _thread_tarefa_pontual(self, colaboradores, caminho, mensagem):
        enviar_para_lista(
            colaboradores=colaboradores,
            mensagem=mensagem,
            caminho_arquivo=caminho,
            callbacks=(self.log_msg_pontual, self.atualizar_stats_pontual),
        )
        self.btn_enviar_pontual.disabled = False
        self._atualizar_btn_pontual()
        self.page.update()

    # ──────────────────────────────────────────────────────────────────────
    #  Contatos — logic
    # ──────────────────────────────────────────────────────────────────────

    def _filtrar_contatos(self, update: bool = True):
        busca      = (self.tf_busca_contatos.value or "").lower().strip()
        status_val = self.dd_status_contatos.value or "todos"
        resultado  = self._colaboradores_cache

        if status_val != "todos":
            try:
                sid = int(status_val)
                resultado = [
                    c for c in resultado
                    if (c.get("statuscolaborador") or {}).get("id_status") == sid
                ]
            except ValueError:
                pass

        if busca:
            resultado = [c for c in resultado if busca in c.get("nome_completo", "").lower()]

        self._popular_tabela(resultado)
        if update:
            self.page.update()

    def _popular_tabela(self, colaboradores: list):
        self.tabela_contatos.rows = [
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(c.get("nome_completo", ""), size=12)),
                ft.DataCell(ft.Text(c.get("telefone", "") or "-", size=12)),
                ft.DataCell(ft.Text((c.get("empresas") or {}).get("nome_empresa", "-"), size=12)),
                ft.DataCell(self._status_badge((c.get("statuscolaborador") or {}).get("descricao_status", "-"))),
                ft.DataCell(
                    ft.Row(
                        [
                            ft.IconButton(
                                icon=ft.Icons.EDIT_OUTLINED,
                                icon_color=ft.Colors.BLUE_GREY_500,
                                icon_size=18,
                                tooltip="Editar",
                                on_click=lambda e, col=c: self._abrir_dialog_editar(col),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_color=ft.Colors.RED_400,
                                icon_size=18,
                                tooltip="Excluir",
                                on_click=lambda e, col=c: self._abrir_dialog_excluir(col),
                            ),
                        ],
                        spacing=0,
                    )
                ),
            ])
            for c in colaboradores
        ]

    def adicionar_colaborador(self, e):
        nome     = self.tf_nome.value     or ""
        telefone = self.tf_telefone.value or ""
        self.tf_nome.error_text     = "Obrigatório" if not nome.strip()     else None
        self.tf_telefone.error_text = "Obrigatório" if not telefone.strip() else None
        if not nome.strip() or not telefone.strip():
            self.page.update()
            return

        id_empresa = None
        if self.dd_empresa.value:
            try:
                id_empresa = int(self.dd_empresa.value)
            except ValueError:
                pass

        id_status = None
        if self.dd_novo_status.value:
            try:
                id_status = int(self.dd_novo_status.value)
            except ValueError:
                pass

        self.btn_adicionar.disabled     = True
        self.lbl_status_contatos.value = "Salvando..."
        self.page.update()
        threading.Thread(target=self._thread_adicionar, args=(nome, telefone, id_empresa, id_status), daemon=True).start()

    def _thread_adicionar(self, nome, telefone, id_empresa, id_status):
        ok = supabase_client.adicionar_colaborador(nome, telefone, id_empresa, id_status)
        if ok:
            self.tf_nome.value        = ""
            self.tf_telefone.value    = ""
            self.dd_empresa.value     = None
            self.dd_novo_status.value = "7"
            self.lbl_status_contatos.value = "Colaborador adicionado!"
            self._colaboradores_cache = supabase_client.listar_colaboradores()
            self._filtrar_contatos(update=False)
            self._filtrar_pontual(update=False)
        else:
            self.lbl_status_contatos.value = "Erro ao salvar. Tente novamente."
        self.btn_adicionar.disabled = False
        self.page.update()

    # ──────────────────────────────────────────────────────────────────────
    #  Editar e Excluir Colaboradores
    # ──────────────────────────────────────────────────────────────────────

    def _fechar_dialog(self, dlg: ft.AlertDialog):
        dlg.open = False
        self.page.update()

    # ── Editar ────────────────────────────────────────────────────────────

    def _abrir_dialog_editar(self, c: Dict):
        self._editando_id = c["id_colaborador"]
        self.tf_edit_nome.value     = c.get("nome_completo", "")
        self.tf_edit_telefone.value = c.get("telefone", "") or ""
        self.tf_edit_nome.error_text     = None
        self.tf_edit_telefone.error_text = None
        id_emp = c.get("id_empresa")
        self.dd_edit_empresa.value = str(id_emp) if id_emp else None
        id_st  = c.get("id_status")
        self.dd_edit_status.value  = str(id_st)  if id_st  else None
        self._btn_salvar_edicao.disabled = False
        self.dlg_editar.open = True
        self.page.update()

    def _salvar_edicao(self, e):
        nome     = self.tf_edit_nome.value     or ""
        telefone = self.tf_edit_telefone.value or ""
        self.tf_edit_nome.error_text     = "Obrigatório" if not nome.strip()     else None
        self.tf_edit_telefone.error_text = "Obrigatório" if not telefone.strip() else None
        if not nome.strip() or not telefone.strip():
            self.page.update()
            return

        id_empresa = None
        if self.dd_edit_empresa.value:
            try:
                id_empresa = int(self.dd_edit_empresa.value)
            except ValueError:
                pass

        id_status = None
        if self.dd_edit_status.value:
            try:
                id_status = int(self.dd_edit_status.value)
            except ValueError:
                pass

        self._btn_salvar_edicao.disabled = True
        self.page.update()
        threading.Thread(
            target=self._thread_atualizar,
            args=(self._editando_id, nome, telefone, id_empresa, id_status),
            daemon=True,
        ).start()

    def _thread_atualizar(self, id_col, nome, telefone, id_empresa, id_status):
        ok = supabase_client.atualizar_colaborador(id_col, nome, telefone, id_empresa, id_status)
        if ok:
            # Encontra nome da empresa no cache
            empresa_nome = "-"
            for emp in self._empresas_cache:
                if emp["id_empresa"] == id_empresa:
                    empresa_nome = emp["nome_empresa"]
                    break

            # Encontra descrição do status nas opções
            status_desc = "-"
            for key, val in STATUS_OPTIONS:
                if key == str(id_status):
                    status_desc = val
                    break

            # Atualiza cache in-place
            for item in self._colaboradores_cache:
                if item["id_colaborador"] == id_col:
                    item["nome_completo"]     = nome
                    item["telefone"]          = telefone
                    item["id_empresa"]        = id_empresa
                    item["id_status"]         = id_status
                    item["empresas"]          = {"nome_empresa": empresa_nome}
                    item["statuscolaborador"] = {"id_status": id_status, "descricao_status": status_desc}
                    break

            self._fechar_dialog(self.dlg_editar)
            self._filtrar_contatos(update=False)
            self._filtrar_pontual(update=False)
            self.lbl_status_contatos.value = "Colaborador atualizado!"
        else:
            self.lbl_status_contatos.value = "Erro ao atualizar. Tente novamente."
            self._btn_salvar_edicao.disabled = False
        self.page.update()

    # ── Excluir ───────────────────────────────────────────────────────────

    def _abrir_dialog_excluir(self, c: Dict):
        self._excluindo_id = c["id_colaborador"]
        self.lbl_excluir_nome.value = c.get("nome_completo", "")
        self.dlg_excluir.open = True
        self.page.update()

    def _confirmar_exclusao(self, e):
        self._fechar_dialog(self.dlg_excluir)
        threading.Thread(target=self._thread_excluir, args=(self._excluindo_id,), daemon=True).start()

    def _thread_excluir(self, id_col: int):
        ok = supabase_client.excluir_colaborador(id_col)
        if ok:
            self._colaboradores_cache = [
                c for c in self._colaboradores_cache if c["id_colaborador"] != id_col
            ]
            self._filtrar_contatos(update=False)
            self._filtrar_pontual(update=False)
            self.lbl_status_contatos.value = "Colaborador excluído."
        else:
            self.lbl_status_contatos.value = "Erro ao excluir. Verifique se há dependentes cadastrados."
        self.page.update()


def main(page: ft.Page):
    AppDisparador(page)


if __name__ == "__main__":
    ft.app(target=main)
