import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv
from supabase import create_client, Client

if getattr(sys, "frozen", False):
    _env_dir = Path(sys.executable).parent
else:
    _env_dir = Path(__file__).parent
load_dotenv(dotenv_path=_env_dir / ".env")

_client: Optional[Client] = None


def get_client() -> Client:
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL e SUPABASE_KEY devem estar definidos no arquivo .env")
        _client = create_client(url, key)
    return _client


def listar_colaboradores() -> List[Dict]:
    res = get_client().table("colaboradores") \
        .select("id_colaborador, nome_completo, telefone, id_status, id_empresa, empresas(nome_empresa), statuscolaborador(id_status, descricao_status)") \
        .order("nome_completo") \
        .execute()
    return res.data or []


def listar_empresas() -> List[Dict]:
    res = get_client().table("empresas") \
        .select("id_empresa, nome_empresa") \
        .order("nome_empresa") \
        .execute()
    return res.data or []


def buscar_telefone_por_nome(nome: str) -> Optional[str]:
    res = get_client().table("colaboradores") \
        .select("telefone") \
        .filter("nome_completo", "ilike", nome.strip()) \
        .execute()
    if res.data:
        return res.data[0]["telefone"]
    return None


def adicionar_colaborador(nome_completo: str, telefone: str, id_empresa: Optional[int], id_status: Optional[int] = None) -> bool:
    payload: Dict = {"nome_completo": nome_completo.strip(), "telefone": telefone.strip()}
    if id_empresa is not None:
        payload["id_empresa"] = id_empresa
    if id_status is not None:
        payload["id_status"] = id_status
    try:
        res = get_client().table("colaboradores").insert(payload).execute()
        return bool(res.data)
    except Exception:
        return False


def atualizar_colaborador(
    id_colaborador: int,
    nome_completo: str,
    telefone: str,
    id_empresa: Optional[int],
    id_status: Optional[int],
) -> bool:
    payload: Dict = {
        "nome_completo": nome_completo.strip(),
        "telefone": telefone.strip(),
        "id_empresa": id_empresa,
        "id_status": id_status,
    }
    try:
        res = (
            get_client()
            .table("colaboradores")
            .update(payload)
            .eq("id_colaborador", id_colaborador)
            .execute()
        )
        return bool(res.data)
    except Exception:
        return False


def excluir_colaborador(id_colaborador: int) -> bool:
    try:
        get_client().table("colaboradores").delete().eq("id_colaborador", id_colaborador).execute()
        return True
    except Exception:
        return False
