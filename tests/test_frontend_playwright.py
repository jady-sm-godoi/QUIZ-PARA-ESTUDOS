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
        assert page.locator("h1").text_content() == "Quiz para Estudos"

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