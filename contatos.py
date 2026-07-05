from typing import Optional
import supabase_client


def garantir_existencia_csv() -> None:
    pass


def buscar_telefone(nome_colaborador: str) -> Optional[str]:
    return supabase_client.buscar_telefone_por_nome(nome_colaborador)
