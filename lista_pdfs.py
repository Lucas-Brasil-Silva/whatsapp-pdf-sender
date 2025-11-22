import os

def obter_caminho_area_de_trabalho():
    caminho_onedrive = os.path.join(os.path.expanduser("~"), "OneDrive", "Área de Trabalho")
    if os.path.exists(caminho_onedrive):
        return caminho_onedrive
    else:
        return os.path.join(os.path.expanduser("~"), "Área de Trabalho")

CAMINHO_AREA_DE_TRABALHO = obter_caminho_area_de_trabalho()

CAMINHO_ENVIAR_PDFS = os.path.join(CAMINHO_AREA_DE_TRABALHO, "enviar_pdfs")

CAMINHO_PDFS_ENVIADOS = os.path.join(CAMINHO_AREA_DE_TRABALHO, "pdfs_envidos")

def criar_pastas():
    if not os.path.exists(CAMINHO_ENVIAR_PDFS):
        os.makedirs(CAMINHO_ENVIAR_PDFS)
    
    if not os.path.exists(CAMINHO_PDFS_ENVIADOS):
        os.makedirs(CAMINHO_PDFS_ENVIADOS)

def mover_pdf(pathfile):
    caminho_atual = os.path.join(CAMINHO_ENVIAR_PDFS,pathfile)
    caminho_novo = os.path.join(CAMINHO_PDFS_ENVIADOS,pathfile)
    os.rename(caminho_atual, caminho_novo)

def listar_pdfs_na_pasta():
    
    caminhos_pdfs = []
    
    # Percorre os arquivos na pasta
    for arquivo in os.listdir(CAMINHO_ENVIAR_PDFS):
        if arquivo.lower().endswith('.pdf'):
            caminhos_pdfs.append(os.path.join(CAMINHO_ENVIAR_PDFS,arquivo))
    
    return caminhos_pdfs