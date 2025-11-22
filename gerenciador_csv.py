import csv
import os
from lista_pdfs import CAMINHO_AREA_DE_TRABALHO

NOME_ARQUIVO = "Contatos Colaboradores.csv"

CABECALHO = ["Colaborador","Telefone"]

CAMINHO_ARQUIVO_CSV = os.path.join(CAMINHO_AREA_DE_TRABALHO, NOME_ARQUIVO)

def verificar_arquivo_csv():

    try:
        with open(CAMINHO_ARQUIVO_CSV, 'r', newline='', encoding='utf-8') as arquivo_csv:
            pass
    except FileNotFoundError:
        with open(CAMINHO_ARQUIVO_CSV, 'w', newline='', encoding='utf-8') as arquivo_csv:
            escritor_csv = csv.DictWriter(arquivo_csv, fieldnames=CABECALHO)
            escritor_csv.writeheader()

def ler_dados_csv():
    dados = []
    with open(CAMINHO_ARQUIVO_CSV, 'r', newline='', encoding='utf-8') as arquivo_csv:
        leitor_csv = csv.DictReader(arquivo_csv)
        for linha in leitor_csv:
            dados.append(linha)
    return dados

def retornar_contato(colaborador):
    dados_existentes = ler_dados_csv()
    for dado in dados_existentes:
        if dado[CABECALHO[0]].strip().upper() == colaborador.strip().upper():
            return dado[CABECALHO[1]]
              
    return False