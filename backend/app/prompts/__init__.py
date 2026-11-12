from pathlib import Path


DEFAULT_PROMPT = "FGV-TI"
PROMPTS_DIR = Path(__file__).parent


def available_prompts() -> list[str]:
    """Retorna os nomes dos prompts (.md) disponíveis, com o padrão primeiro."""
    names = sorted(path.stem for path in PROMPTS_DIR.glob("*.md"))

    if DEFAULT_PROMPT in names:
        names.remove(DEFAULT_PROMPT)
        names.insert(0, DEFAULT_PROMPT)

    return names


def load_prompt(name: str | None = None) -> str:
    """Carrega o conteúdo de prompts/<name>.md."""
    if not name:
        name = DEFAULT_PROMPT

    if name not in available_prompts():
        disponiveis = ", ".join(available_prompts()) or "nenhum"
        raise FileNotFoundError(
            f"Prompt '{name}' não encontrado em {PROMPTS_DIR}. "
            f"Prompts disponíveis: {disponiveis}."
        )

    path = PROMPTS_DIR / f"{name}.md"
    return path.read_text(encoding="utf-8").strip()
