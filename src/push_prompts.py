"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Le o prompt otimizado de prompts/bug_to_user_story_v2.yml
2. Valida a estrutura basica
3. Faz push PUBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descricao, tecnicas)
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

# carrega variaveis do .env
load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
V2_FILE = PROJECT_ROOT / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura basica do prompt (versao simples, estilo Java: lista de erros).
    Retorna (True, []) se ok, ou (False, [erros...]).
    """
    errors = []

    if not prompt_data.get("description"):
        errors.append("description esta vazio")

    system_prompt = (prompt_data.get("system_prompt") or "").strip()
    if not system_prompt:
        errors.append("system_prompt esta vazio")

    user_prompt = (prompt_data.get("user_prompt") or "").strip()
    if not user_prompt:
        errors.append("user_prompt esta vazio")

    # o dataset usa a chave {bug_report}
    if "{bug_report}" not in user_prompt and "{bug_report}" not in system_prompt:
        errors.append("o prompt precisa ter a variavel {bug_report}")

    techniques = prompt_data.get("techniques_applied") or []
    if len(techniques) < 2:
        errors.append(f"precisa de pelo menos 2 tecnicas, achou {len(techniques)}")

    if "TODO" in system_prompt or "[TODO]" in system_prompt:
        errors.append("ainda tem TODO no system_prompt")

    return (len(errors) == 0, errors)


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o Hub (publico).
    prompt_name: ex. bug_to_user_story_v2
    """
    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()
    if not username:
        print("Erro: USERNAME_LANGSMITH_HUB nao esta no .env")
        return False

    # monta o ChatPromptTemplate (system + user)
    # {bug_report} vai ser preenchido depois na avaliacao
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", prompt_data["system_prompt"]),
            ("user", prompt_data["user_prompt"]),
        ]
    )

    # nome publico no Hub: handle/nome
    hub_id = f"{username}/{prompt_name}"

    tags = prompt_data.get("tags") or []
    techniques = prompt_data.get("techniques_applied") or []
    description = prompt_data.get("description") or "Prompt otimizado bug -> user story"

    # junta tecnicas na descricao para ficar visivel no Hub
    full_description = (
        f"{description} | Tecnicas: {', '.join(techniques)}"
    )

    print(f"Enviando prompt publico: {hub_id}")
    client = Client()

    try:
        url = client.push_prompt(
            hub_id,
            object=prompt,
            is_public=True,
            description=full_description,
            tags=list(tags) + list(techniques),
        )
        print(f"Push OK: {url}")
        return True
    except Exception as e:
        print(f"Erro no push: {e}")
        return False


def main():
    """Funcao principal."""
    print_section_header("Push do prompt otimizado (v2)")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    print(f"Lendo arquivo: {V2_FILE}")
    data = load_yaml(str(V2_FILE))
    if not data:
        return 1

    # o YAML tem a chave bug_to_user_story_v2 na raiz
    prompt_data = data.get(PROMPT_KEY)
    if not prompt_data:
        print(f"Erro: nao achei a chave '{PROMPT_KEY}' no YAML")
        return 1

    ok, errors = validate_prompt(prompt_data)
    if not ok:
        print("Prompt invalido:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("Validacao OK")
    success = push_prompt_to_langsmith(PROMPT_KEY, prompt_data)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
