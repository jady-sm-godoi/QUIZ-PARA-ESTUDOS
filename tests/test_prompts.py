import pytest

import app.prompts as prompts_module
from app.prompts import BASE_PROMPT, DEFAULT_PROMPT, available_prompts, load_prompt


class TestPromptLoader:

    def test_default_prompt_exists(self):
        """O prompt padrão deve existir na pasta."""
        assert DEFAULT_PROMPT in available_prompts()

    def test_load_default_prompt(self):
        """O prompt padrão deve carregar e conter o placeholder de perguntas."""
        prompt = load_prompt()

        assert len(prompt) > 1000
        assert "{num_questions}" in prompt

    def test_load_prompt_with_none_uses_default(self):
        """None deve usar o prompt padrão."""
        assert load_prompt(None) == load_prompt(DEFAULT_PROMPT)

    def test_prompt_uses_plain_json_braces(self):
        """O arquivo .md não deve ter os escapes de chaves do .format()."""
        prompt = load_prompt()

        assert "{{" not in prompt
        assert "}}" not in prompt
        assert '"questions"' in prompt
        assert '"resposta_correta"' in prompt

    def test_prompt_keeps_escaped_newlines_literal(self):
        """\\n deve chegar ao modelo como texto, não como quebra de linha real."""
        prompt = load_prompt()

        assert r"Use \n para quebras de linha" in prompt
        assert r"\nI. Permite recuperar" in prompt

    def test_load_unknown_prompt_raises(self):
        """Nome inexistente deve gerar erro claro."""
        with pytest.raises(FileNotFoundError, match="nao_existe"):
            load_prompt("nao_existe")

    def test_load_prompt_rejects_path_traversal(self):
        """O nome do prompt não pode escapar da pasta prompts."""
        with pytest.raises(FileNotFoundError):
            load_prompt("../quiz")

    def test_available_prompts_lists_default(self):
        """O prompt padrão deve aparecer na listagem."""
        assert DEFAULT_PROMPT in available_prompts()

    def test_available_prompts_puts_default_first(self, tmp_path, monkeypatch):
        """O prompt padrão deve vir primeiro na lista."""
        (tmp_path / "fgv.md").write_text("FGV", encoding="utf-8")
        (tmp_path / (DEFAULT_PROMPT + ".md")).write_text("Padrão", encoding="utf-8")
        monkeypatch.setattr(prompts_module, "PROMPTS_DIR", tmp_path)

        assert available_prompts()[0] == DEFAULT_PROMPT

    def test_load_prompt_from_custom_dir(self, tmp_path, monkeypatch):
        """Deve ser possível carregar qualquer .md da pasta."""
        (tmp_path / "fgv.md").write_text("Prompt FGV", encoding="utf-8")
        (tmp_path / "cespe.md").write_text("Prompt CESPE", encoding="utf-8")
        monkeypatch.setattr(prompts_module, "PROMPTS_DIR", tmp_path)

        assert available_prompts() == ["cespe", "fgv"]
        assert load_prompt("fgv") == "Prompt FGV"

    @pytest.mark.parametrize("name", available_prompts())
    def test_all_available_prompts_load(self, name):
        """Todos os prompts da pasta devem carregar sem erro."""
        assert load_prompt(name)


class TestBasePromptPolicy:

    def test_base_prompt_exists(self):
        """A política de fontes compartilhada deve existir na pasta."""
        assert (prompts_module.PROMPTS_DIR / f"{BASE_PROMPT}.md").exists()

    def test_base_prompt_is_not_listed_as_banca(self):
        """O _base.md não deve aparecer no seletor de prompts."""
        assert BASE_PROMPT not in available_prompts()

    def test_base_prompt_cannot_be_loaded_as_banca(self):
        """O _base.md é um trecho compartilhado, não uma banca selecionável."""
        with pytest.raises(FileNotFoundError):
            load_prompt(BASE_PROMPT)

    def test_load_prompt_includes_source_policy(self):
        """Todo prompt de banca deve vir precedido da política de fontes."""
        prompt = load_prompt()

        assert "POLÍTICA DE FONTES E ORIGINALIDADE" in prompt
        assert "CONTEÚDO-FONTE" in prompt
        assert "CONTEÚDO-QUESTÃO" in prompt
        assert "<material_de_estudo>" in prompt

    def test_base_prompt_is_prepended_in_custom_dir(self, tmp_path, monkeypatch):
        """A política deve ser prefixada mesmo em pastas de teste."""
        (tmp_path / f"{BASE_PROMPT}.md").write_text("BASE GENÉRICA", encoding="utf-8")
        (tmp_path / "fgv.md").write_text("Prompt FGV", encoding="utf-8")
        monkeypatch.setattr(prompts_module, "PROMPTS_DIR", tmp_path)

        prompt = load_prompt("fgv")

        assert prompt.startswith("BASE GENÉRICA")
        assert "Prompt FGV" in prompt
        assert BASE_PROMPT not in available_prompts()
