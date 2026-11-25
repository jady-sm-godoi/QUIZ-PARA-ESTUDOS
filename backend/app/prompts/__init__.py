from pathlib import Path


DEFAULT_PROMPT = "FGV-TI"
BASE_PROMPT = "_base"
PROMPTS_DIR = Path(__file__).parent


def available_prompts() -> list[str]:
    """Retorna os nomes dos prompts (.md) disponíveis, com o padrão primeiro.

    Arquivos que começam com "_" são trechos compartilhados (como o
    _base.md) e não aparecem como opções de banca no seletor.
    """
    names = sorted(
        path.stem
        for path in PROMPTS_DIR.glob("*.md")
        if not path.name.startswith("_")
    )

    if DEFAULT_PROMPT in names:
        names.remove(DEFAULT_PROMPT)
        names.insert(0, DEFAULT_PROMPT)

    return names


def load_prompt(name: str | None = None) -> str:
    """Carrega prompts/<name>.md precedido pela política de fontes genérica."""
    if not name:
        name = DEFAULT_PROMPT

    if name not in available_prompts():
        disponiveis = ", ".join(available_prompts()) or "nenhum"
        raise FileNotFoundError(
            f"Prompt '{name}' não encontrado em {PROMPTS_DIR}. "
            f"Prompts disponíveis: {disponiveis}."
        )

    base_path = PROMPTS_DIR / f"{BASE_PROMPT}.md"
    base = (
        base_path.read_text(encoding="utf-8").strip()
        if base_path.exists()
        else ""
    )

    path = PROMPTS_DIR / f"{name}.md"
    prompt = path.read_text(encoding="utf-8").strip()

    if not base:
        return prompt

    return f"{base}\n\n---\n\n{prompt}"
