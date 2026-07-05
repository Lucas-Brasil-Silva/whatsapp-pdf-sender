from pathlib import Path
from typing import List


def obter_caminho_area_de_trabalho() -> Path:
    home = Path.home()
    caminho_onedrive = home / "OneDrive" / "Área de Trabalho"
    if caminho_onedrive.exists():
        return caminho_onedrive
    return home / "Área de Trabalho"


CAMINHO_BASE = obter_caminho_area_de_trabalho()

PASTA_ENVIAR = Path("enviar_pdfs")
PASTA_ENVIADOS = Path("pdfs_enviados")


def criar_estruturas_pastas() -> None:
    PASTA_ENVIAR.mkdir(parents=True, exist_ok=True)
    PASTA_ENVIADOS.mkdir(parents=True, exist_ok=True)


def mover_arquivo(nome_arquivo: str) -> None:
    origem = PASTA_ENVIAR / nome_arquivo
    destino = PASTA_ENVIADOS / nome_arquivo
    try:
        origem.replace(destino)
    except FileNotFoundError:
        print(f"Erro: O arquivo {nome_arquivo} não foi encontrado na origem.")
    except PermissionError:
        print(f"Erro: Permissão negada ao mover {nome_arquivo}.")


def listar_arquivos_na_pasta() -> List[Path]:
    return [p for p in PASTA_ENVIAR.glob("*") if p.is_file()]
