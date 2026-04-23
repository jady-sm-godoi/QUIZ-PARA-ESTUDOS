import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


# Adiciona o diretório backend ao caminho de importação
# Python precisa "encontrar" os módulos. Sem isso, os testes não acham from app.models import ...
