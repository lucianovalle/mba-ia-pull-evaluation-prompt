"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull do prompt semente do desafio
3. Salva localmente em prompts/bug_to_user_story_v1.yml
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from utils import save_yaml, check_env_vars, print_section_header

# carrega o arquivo .env (LANGSMITH_API_KEY, etc.)
load_dotenv()

# pasta raiz do projeto (um nivel acima de src/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# prompt publico do desafio (dono/nome)
PROMPT_HUB_ID = "leonanluppi/bug_to_user_story_v1"
OUTPUT_FILE = PROJECT_ROOT / "prompts" / "bug_to_user_story_v1.yml"


def _extrair_texto_mensagem(mensagem) -> str:
    """
    Pega o texto de uma mensagem do ChatPromptTemplate.
    Em Java seria algo como mensagem.getPrompt().getTemplate().
    """
    # algumas mensagens tem .prompt.template
    if hasattr(mensagem, "prompt") and hasattr(mensagem.prompt, "template"):
        return mensagem.prompt.template
    # fallback: conteúdo direto
    if hasattr(mensagem, "content"):
        return str(mensagem.content)
    return str(mensagem)


def pull_prompts_from_langsmith():
    """
    Baixa o prompt ruim (v1) do LangSmith e salva em YAML local.
    Retorna 0 se deu certo, 1 se deu erro.
    """
    print_section_header("Pull do prompt do LangSmith")

    # valida se a chave do LangSmith esta no .env
    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    # Client = cliente HTTP que fala com a API do LangSmith
    # Ele usa LANGSMITH_API_KEY do ambiente automaticamente
    print("Conectando ao LangSmith...")
    client = Client()

    print(f"Baixando prompt: {PROMPT_HUB_ID}")
    # dangerously_pull_public_prompt=True -> obrigatorio quando o id tem "dono/nome"
    # Sem isso o LangSmith bloqueia o pull de prompts publicos de terceiros
    try:
        prompt = client.pull_prompt(
            PROMPT_HUB_ID,
            dangerously_pull_public_prompt=True,
        )
    except Exception as e:
        print(f"Erro no pull: {e}")
        return 1

    # o retorno e um ChatPromptTemplate (lista de mensagens system/user/...)
    system_prompt = ""
    user_prompt = ""

    for mensagem in prompt.messages:
        tipo = mensagem.__class__.__name__.lower()
        texto = _extrair_texto_mensagem(mensagem)

        if "system" in tipo:
            system_prompt = texto
        elif "human" in tipo or "user" in tipo:
            user_prompt = texto

    # monta o dicionario no formato do arquivo YAML do projeto
    dados = {
        "bug_to_user_story_v1": {
            "description": "Prompt para converter relatos de bugs em User Stories",
            "system_prompt": system_prompt,
            "user_prompt": user_prompt if user_prompt else "{bug_report}",
            "version": "v1",
            "created_at": "2025-01-15",
            "tags": ["bug-analysis", "user-story", "product-management"],
        }
    }

    print(f"Salvando em: {OUTPUT_FILE}")
    ok = save_yaml(dados, str(OUTPUT_FILE))
    if not ok:
        return 1

    print("Pull concluido com sucesso!")
    return 0


def main():
    """Funcao principal — ponto de entrada do script."""
    return pull_prompts_from_langsmith()


if __name__ == "__main__":
    sys.exit(main())
