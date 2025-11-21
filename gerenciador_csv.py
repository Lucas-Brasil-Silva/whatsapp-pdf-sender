import csv
import os
from lista_pdfs import CAMINHO_AREA_DE_TRABALHO

CAMINHO_ARQUIVO_CSV = os.path.join(CAMINHO_AREA_DE_TRABALHO, "Contatos Colaboradores.csv")

def verificar_arquivo_csv(nome_arquivo, cabecalhos):
    try:
        with open(nome_arquivo, 'r', newline='', encoding='utf-8') as arquivo_csv:
            pass
    except FileNotFoundError:
        with open(nome_arquivo, 'w', newline='', encoding='utf-8') as arquivo_csv:
            escritor_csv = csv.DictWriter(arquivo_csv, fieldnames=cabecalhos)
            escritor_csv.writeheader()

def ler_dados_csv(nome_arquivo):
    dados = []
    with open(nome_arquivo, 'r', newline='', encoding='utf-8') as arquivo_csv:
        leitor_csv = csv.DictReader(arquivo_csv)
        for linha in leitor_csv:
            dados.append(linha)
    return dados

def retornar_contato(colaborador):
    dados_existentes = ler_dados_csv(CAMINHO_ARQUIVO_CSV)
    for dado in dados_existentes:
        if dado['Colaborador'].strip().upper() == colaborador.strip().upper():
            return dado['Telefone']
              
    return False

if __name__ == "__main__":
    telefone = retornar_contato("  LUCAS BRASI")  # Exemplo de uso
    print(f"Telefone encontrado: {telefone}")
