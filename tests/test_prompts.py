"""
Testes automatizados para validacao de prompts.
"""
import pytest
import yaml
import sys
from pathlib import Path

# adiciona src ao path (para importar utils se precisar)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

# caminho do prompt otimizado
V2_PATH = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_v2():
    """Atalho: devolve so o dicionario do prompt v2."""
    data = load_prompts(str(V2_PATH))
    assert data is not None, "Nao consegui ler o YAML v2"
    assert PROMPT_KEY in data, f"Falta a chave {PROMPT_KEY} no YAML"
    return data[PROMPT_KEY]


class TestPrompts:
    def test_prompt_has_system_prompt(self):
        """Verifica se o campo 'system_prompt' existe e nao esta vazio."""
        prompt = get_v2()
        assert "system_prompt" in prompt
        assert prompt["system_prompt"].strip() != ""

    def test_prompt_has_role_definition(self):
        """Verifica se o prompt define uma persona (ex: Product Manager)."""
        prompt = get_v2()
        texto = prompt["system_prompt"].lower()
        # Role Prompting: precisa parecer uma persona
        tem_persona = (
            "voce e" in texto
            or "você é" in texto
            or "product manager" in texto
            or "persona" in texto
        )
        assert tem_persona, "Nao achei definicao de role/persona no system_prompt"

    def test_prompt_mentions_format(self):
        """Verifica se o prompt exige formato Markdown ou User Story padrao."""
        prompt = get_v2()
        texto = prompt["system_prompt"].lower()
        tem_formato = (
            "markdown" in texto
            or "user story" in texto
            or "como um" in texto
            or "criterios de aceitacao" in texto
            or "critérios de aceitação" in texto
        )
        assert tem_formato, "Nao achei referencia a formato Markdown/User Story"

    def test_prompt_has_few_shot_examples(self):
        """Verifica se o prompt contem exemplos de entrada/saida (Few-shot)."""
        prompt = get_v2()
        texto = prompt["system_prompt"].lower()
        tem_exemplos = (
            "exemplo" in texto
            or "few-shot" in texto
            or ("entrada" in texto and "saida" in texto)
            or ("entrada" in texto and "saída" in texto)
        )
        assert tem_exemplos, "Nao achei exemplos few-shot no system_prompt"

    def test_prompt_no_todos(self):
        """Garante que nao ficou nenhum [TODO] no texto."""
        prompt = get_v2()
        texto = (prompt.get("system_prompt") or "") + "\n" + (prompt.get("user_prompt") or "")
        assert "[TODO]" not in texto
        assert "TODO" not in texto

    def test_minimum_techniques(self):
        """Verifica nos metadados se pelo menos 2 tecnicas foram listadas."""
        prompt = get_v2()
        techniques = prompt.get("techniques_applied") or []
        assert isinstance(techniques, list)
        assert len(techniques) >= 2, f"Esperava >=2 tecnicas, achei {len(techniques)}"

        # tambem usa a validacao pronta do utils
        ok, errors = validate_prompt_structure(prompt)
        assert ok, f"validate_prompt_structure falhou: {errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
