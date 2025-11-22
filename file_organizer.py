from pathlib import Path
from typing  import List

def obter_caminho_area_de_trabalho() -> Path:
    """
    Retorna o caminho da Área de Trabalho, verificando a existência
    da pasta no OneDrive ou no caminho padrão do usuário.
    """
    home = Path.home()

    caminho_onedrive = home / "OneDrive" / "Área de Trabalho"
    if caminho_onedrive.exists():
        return caminho_onedrive
    
    return home / "Área de Trabalho"

CAMINHO_BASE = obter_caminho_area_de_trabalho()
PASTA_ENVIAR = CAMINHO_BASE / "enviar_pdfs"
PASTA_ENVIADOS = CAMINHO_BASE / "pdfs_enviados"

def criar_estruturas_pastas() -> None:
    """
    Cria as pastas necessárias se elas não existirem.
    """
    PASTA_ENVIAR.mkdir(parents=True, exist_ok=True)
    PASTA_ENVIADOS.mkdir(parents=True, exist_ok=True)

def mover_pdf(nome_arquivo: str) -> None:
    """
    Move um arquivo PDF da pasta de origem para a pasta de enviados.
    """
    origem = PASTA_ENVIAR / nome_arquivo
    destino = PASTA_ENVIADOS / nome_arquivo

    try:
        origem.replace(destino)
    except FileNotFoundError:
        print(f"Erro: O arquivo {nome_arquivo} não foi encontrado na origem.")
    except PermissionError:
        print(f"Erro: Permissão negada ao mover {nome_arquivo}.")

def listar_pdfs_na_pasta() -> List[Path]:
    """
    Lista todos os arquivos .pdf na pasta de envio.
    Retorna uma lista de objetos Path.
    """
    arquivos_pdf = list(PASTA_ENVIAR.glob("*.pdf"))
    return arquivos_pdf