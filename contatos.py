import csv
from typing import List, Dict, Optional
from file_organizer import CAMINHO_BASE

NOME_ARQUIVO = "Contatos Colaboradores.csv"
CAMINHO_ARQUIVO_CSV = CAMINHO_BASE / NOME_ARQUIVO
COL_COLABORADOR = "Colaborador"
COL_TELEFONE = "Telefone"
CABECALHO = [COL_COLABORADOR, COL_TELEFONE]

def garantir_existencia_csv() -> None:
    """
    Verifica se o CSV existe. Se não, cria o arquivo com o cabeçalho.
    """
    if not CAMINHO_ARQUIVO_CSV.exists():
        with open(CAMINHO_ARQUIVO_CSV, 'w', newline='', encoding='utf-8') as arquivo_csv:
            escritor_csv = csv.DictWriter(arquivo_csv, fieldnames=CABECALHO)
            escritor_csv.writeheader()

def ler_dados_csv() -> List[Dict[str,str]]:
    """
    Lê todo o CSV e retorna uma lista de dicionários.
    """
    with open(CAMINHO_ARQUIVO_CSV, 'r', newline='', encoding='utf-8') as arquivo_csv:
        leitor_csv = csv.DictReader(arquivo_csv)
        return list(leitor_csv)

def buscar_telefone(nome_colaborador: str) -> Optional[str]:
    """
    Busca o telefone de um colaborador pelo nome.
    """
    dados = ler_dados_csv()
    nome_buscado = nome_colaborador.strip().upper()

    for linha in dados:
        nome_atual = linha[COL_COLABORADOR].strip().upper()
        if nome_atual == nome_buscado:
            return linha[COL_TELEFONE]         
    return None