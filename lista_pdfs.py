import os

def obter_caminho_area_de_trabalho():
    caminho_onedrive = os.path.join(os.path.expanduser("~"), "OneDrive", "Área de Trabalho")
    if os.path.exists(caminho_onedrive):
        return caminho_onedrive
    else:
        return os.path.join(os.path.expanduser("~"), "Área de Trabalho")

CAMINHO_AREA_DE_TRABALHO = obter_caminho_area_de_trabalho()

def listar_pdfs_na_pasta(pasta='arquivos_pdf'):

    caminho_pasta_arquivos = os.path.join(CAMINHO_AREA_DE_TRABALHO, pasta)
    
    # Verifica se a pasta existe; se não, cria a pasta
    if not os.path.exists(caminho_pasta_arquivos):
        os.makedirs(caminho_pasta_arquivos)
        print(f"Pasta '{pasta}' criada na área de trabalho.")
    
    # Lista para armazenar os nomes dos arquivos PDF
    caminhos_pdfs = []
    
    # Percorre os arquivos na pasta
    for arquivo in os.listdir(caminho_pasta_arquivos):
        if arquivo.lower().endswith('.pdf'):
            caminhos_pdfs.append(os.path.join(caminho_pasta_arquivos,arquivo))
    
    return caminhos_pdfs

#  funcão que verifica se a area de trabalho do usuario fica no onedrive ou no c:\users\nome_do_usuario\Área de Trabalho

if __name__ == "__main__":
    pdfs = listar_pdfs_na_pasta()
    print("Arquivos PDF encontrados na pasta:")
    for pdf in pdfs:
        # deixar somente o nome de quem é o pdf e remover o .pdf do final
        print(f"{pdf.split('-')[-1].replace('.pdf','')}")