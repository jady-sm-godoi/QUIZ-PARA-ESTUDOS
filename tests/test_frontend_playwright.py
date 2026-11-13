import pytest
import subprocess
import time
import os
from pathlib import Path

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
BACKEND_DIR = Path(__file__).parent.parent / "backend"


@pytest.fixture(scope="module")
def server():
    """Inicia o servidor FastAPI para os testes"""
    os.chdir(BACKEND_DIR)
    env = os.environ.copy()
    env['PYTHONPATH'] = str(BACKEND_DIR)
    
    proc = subprocess.Popen(
        ["python", "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8766"],
        cwd=str(BACKEND_DIR),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    time.sleep(3)
    
    yield "http://127.0.0.1:8766"
    
    proc.terminate()
    proc.wait()
    time.sleep(1)


@pytest.fixture
def page(browser):
    """Cria uma nova página para cada teste"""
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()


class TestFrontendPage:

    def test_page_loads(self, page, server):
        """Testa que a página carrega sem erros"""
        page.goto(f"{server}/")
        
        assert page.title() == "Quiz para Estudos"
        assert page.locator("header h1").text_content() == "Quiz para Estudos"

    def test_navigation_buttons_exist(self, page, server):
        """Testa que botões de navegação existem"""
        page.goto(f"{server}/")
        
        assert page.locator("#btn-home").is_visible()
        assert page.locator("#btn-history").is_visible()

    def test_generate_form_elements(self, page, server):
        """Testa que todos os elementos do formulário de geração existem"""
        page.goto(f"{server}/")
        
        assert page.locator("#quiz-titulo").is_visible()
        assert page.locator("#quiz-conteudo").is_visible()
        assert page.locator("#quiz-perguntas").is_visible()
        assert page.locator("#form-generate button[type='submit']").is_visible()

    def test_prompt_select_is_populated(self, page, server):
        """O select de prompt deve ser carregado a partir da API"""
        page.goto(f"{server}/")

        prompt_select = page.locator("#quiz-prompt")
        assert prompt_select.is_visible()

        page.wait_for_function(
            "document.querySelector('#quiz-prompt option') !== null && "
            "document.querySelector('#quiz-prompt option').value !== ''"
        )
        assert prompt_select.input_value() != ""

    def test_large_content_flow_reuses_content_for_selected_part(self, page, server):
        """Ao escolher uma parte, o conteúdo original deve ser reenviado"""
        requests = []

        def handle_generate(route):
            payload = route.request.post_data_json
            requests.append(payload)

            if payload.get("part_index") is None:
                route.fulfill(json={
                    "titulo": payload["titulo"],
                    "categoria": payload.get("categoria"),
                    "total_parts": 2,
                    "parts": [
                        {"part_index": 0, "char_count": 50000, "total_parts": 2, "needs_split": True},
                        {"part_index": 1, "char_count": 20000, "total_parts": 2, "needs_split": True},
                    ],
                    "message": "Material dividido em 2 partes."
                })
            else:
                route.fulfill(json={
                    "quiz_id": "quiz-parte-2",
                    "titulo": payload["titulo"],
                    "perguntas": [
                        {
                            "enunciado": "Pergunta da parte 2?",
                            "opcoes": ["A", "B", "C", "D", "E"],
                            "resposta_correta": 0,
                            "explicacao": "Explicação"
                        }
                    ]
                })

        page.route("**/api/generate", handle_generate)
        page.goto(f"{server}/")

        page.fill("#quiz-titulo", "Material Grande")
        page.fill("#quiz-conteudo", "conteudo original")
        page.click("#form-generate button[type='submit']")

        page.wait_for_selector("#parts-modal:not(.hidden)")
        page.locator("#parts-list .part-item").nth(1).click()
        page.wait_for_selector("#section-quiz.active")

        assert len(requests) == 2
        assert requests[1]["part_index"] == 1
        assert requests[1]["conteudo"] == "conteudo original"

    def test_category_radio_buttons(self, page, server):
        """Testa botões de categoria existente/nova"""
        page.goto(f"{server}/")
        
        existing_radio = page.locator('input[name="categoria-tipo"][value="existing"]')
        new_radio = page.locator('input[name="categoria-tipo"][value="new"]')
        
        assert existing_radio.is_visible()
        assert new_radio.is_visible()
        assert existing_radio.is_checked()
        assert not new_radio.is_checked()

    def test_category_toggle_existing_select_enabled(self, page, server):
        """Testa que select de categoria está habilitado para existing"""
        page.goto(f"{server}/")
        
        select = page.locator("#quiz-categoria")
        input_nova = page.locator("#nova-categoria")
        
        assert not select.is_disabled()
        assert input_nova.is_disabled()

    def test_category_toggle_new_input_enabled(self, page, server):
        """Testa que input de nova categoria fica habilitado"""
        page.goto(f"{server}/")
        
        new_radio = page.locator('input[name="categoria-tipo"][value="new"]')
        new_radio.dispatch_event("click")
        
        select = page.locator("#quiz-categoria")
        input_nova = page.locator("#nova-categoria")
        
        assert select.is_disabled()
        assert not input_nova.is_disabled()

    def test_file_upload_area_exists(self, page, server):
        """Testa que área de upload de arquivo existe"""
        page.goto(f"{server}/")
        
        assert page.locator("#file-upload-area").is_visible()
        assert page.locator("#quiz-file").count() > 0

    def test_file_name_hidden_initially(self, page, server):
        """Testa que nome do arquivo está oculto inicialmente"""
        page.goto(f"{server}/")
        
        file_name = page.locator("#quiz-file-name")
        
        assert file_name.text_content() == ""
        is_hidden = file_name.evaluate("el => window.getComputedStyle(el).display === 'none'")
        assert is_hidden

    def test_navigation_to_history(self, page, server):
        """Testa navegação para seção de histórico"""
        page.goto(f"{server}/")
        
        page.locator("#btn-history").click()
        
        generate_section = page.locator("#section-generate")
        history_section = page.locator("#section-history")
        
        assert history_section.is_visible()
        assert not generate_section.is_visible()

    def test_back_to_generate_from_history(self, page, server):
        """Testa voltar para geração de quiz"""
        page.goto(f"{server}/")
        
        page.locator("#btn-history").click()
        page.locator("#btn-home").click()
        
        assert page.locator("#section-generate").is_visible()

    def test_new_quiz_button_in_dom(self, page, server):
        """Testa que botão de novo quiz existe no DOM"""
        page.goto(f"{server}/")
        
        assert page.locator("#btn-new-quiz").count() > 0


class TestFrontendDragAndDrop:

    def test_dragover_style(self, page, server):
        """Testa que estilo muda ao arrastar arquivo"""
        page.goto(f"{server}/")
        
        upload_area = page.locator("#file-upload-area")
        
        assert "dragover" not in upload_area.get_attribute("class")
        
        upload_area.dispatch_event("dragover")
        
        assert "dragover" in upload_area.get_attribute("class")