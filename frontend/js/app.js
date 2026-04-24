const API_BASE = '/api';

let currentQuiz = null;
let currentQuizId = null;
let userAnswers = {};

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initGenerateForm();
    initSubmitQuiz();
    initNewQuiz();
    initUploadForm();
    initHistory();
    initPartsModal();
    initCategoryRadio();
    initFileUpload();
    loadCategories();
});

function initFileUpload() {
    const fileInput = document.getElementById('quiz-file');
    const fileNameDisplay = document.getElementById('quiz-file-name');
    const uploadArea = document.getElementById('file-upload-area');
    let fileInputRef = fileInput;
    
    const updateFileName = (name) => {
        fileNameDisplay.textContent = name;
        fileNameDisplay.style.display = name ? 'inline-block' : 'none';
    };
    
    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                updateFileName(e.target.files[0].name);
            } else {
                updateFileName('');
            }
        });
    }

    if (uploadArea) {
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                const file = files[0];
                const validTypes = ['.txt', '.pdf', '.docx'];
                const ext = '.' + file.name.split('.').pop().toLowerCase();
                
                if (validTypes.includes(ext)) {
                    fileInputRef.files = files;
                    updateFileName(file.name);
                } else {
                    alert('Tipo de arquivo inválido. Use: .txt, .pdf ou .docx');
                }
            }
        });
    }

    updateFileName('');
}

function initNavigation() {
    document.getElementById('btn-home').addEventListener('click', () => showSection('generate'));
    document.getElementById('btn-history').addEventListener('click', () => {
        showSection('history');
        loadHistory();
    });
}

function initCategoryRadio() {
    toggleCategory('generate', 'existing');
    toggleCategory('upload', 'existing');
}

function toggleCategory(formType, value) {
    if (formType === 'generate') {
        const selectQuiz = document.getElementById('quiz-categoria');
        const inputNova = document.getElementById('nova-categoria');
        
        if (value === 'existing') {
            selectQuiz.disabled = false;
            inputNova.disabled = true;
            inputNova.value = '';
        } else {
            selectQuiz.disabled = true;
            selectQuiz.value = '';
            inputNova.disabled = false;
            inputNova.focus();
        }
    } else {
        const selectUpload = document.getElementById('upload-category');
        const inputNova = document.getElementById('upload-new-category');
        
        if (value === 'existing') {
            selectUpload.disabled = false;
            inputNova.disabled = true;
            inputNova.value = '';
        } else {
            selectUpload.disabled = true;
            selectUpload.value = '';
            inputNova.disabled = false;
            inputNova.focus();
        }
    }
}

function showSection(sectionId) {
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.getElementById(`section-${sectionId}`).classList.add('active');
    
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    if (sectionId === 'generate') {
        document.getElementById('btn-home').classList.add('active');
    } else if (sectionId === 'history') {
        document.getElementById('btn-history').classList.add('active');
    }
}

function showLoading(text = 'Carregando...') {
    document.getElementById('loading-text').textContent = text;
    document.getElementById('loading-modal').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading-modal').classList.add('hidden');
}

async function loadCategories() {
    try {
        const response = await fetch(`${API_BASE}/categories`);
        const categories = await response.json();
        
        const selects = [
            document.getElementById('quiz-categoria'),
            document.getElementById('upload-category')
        ];
        
        selects.forEach(select => {
            const currentOptions = select.querySelectorAll('option:not(:first-child)');
            currentOptions.forEach(o => o.remove());
            
            categories.forEach(cat => {
                const option = document.createElement('option');
                option.value = cat.name;
                option.textContent = `${cat.name} (${cat.material_count} materiais)`;
                select.appendChild(option);
            });
        });
    } catch (error) {
        console.error('Erro ao carregar categorias:', error);
    }
}

function initGenerateForm() {
    document.getElementById('form-generate').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const titulo = document.getElementById('quiz-titulo').value;
        const conteudo = document.getElementById('quiz-conteudo').value;
        const numPeruntas = parseInt(document.getElementById('quiz-perguntas').value);
        const fileInput = document.getElementById('quiz-file');
        const file = fileInput.files[0];
        
        const categoriaTipo = document.querySelector('input[name="categoria-tipo"]:checked').value;
        let categoria = null;
        
        if (categoriaTipo === 'existing') {
            categoria = document.getElementById('quiz-categoria').value || null;
        } else {
            categoria = document.getElementById('nova-categoria').value || null;
        }

        const hasContent = conteudo || file;
        
        if (!hasContent && (categoriaTipo === 'new' || !categoria)) {
            alert('Adicione conteúdo ou faça upload de um arquivo, ou selecione uma categoria existente');
            return;
        }
        
        if (!hasContent && categoriaTipo === 'existing' && categoria) {
            const useExisting = confirm('Nenhum conteúdo novo adicionado. Deseja usar o material existente da categoria "' + categoria + '" para gerar o quiz?');
            if (!useExisting) return;
        }
        
        showLoading('Gerando quiz...');
        
        try {
            let response;
            
            if (file && !conteudo) {
                const formData = new FormData();
                formData.append('titulo', titulo);
                formData.append('num_perguntas', numPeruntas);
                if (categoria) formData.append('categoria', categoria);
                formData.append('file', file);
                
                response = await fetch(`${API_BASE}/generate/file`, {
                    method: 'POST',
                    body: formData
                });
            } else {
                response = await fetch(`${API_BASE}/generate`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        titulo,
                        conteudo,
                        num_perguntas: numPeruntas,
                        categoria
                    })
                });
            }
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Erro ao gerar quiz');
            }
            
            const data = await response.json();
            
            if (data.total_parts) {
                showPartsModal(data);
            } else {
                displayQuiz(data);
            }
        } catch (error) {
            alert('Erro: ' + error.message);
        } finally {
            hideLoading();
        }
    });
}

function showPartsModal(data) {
    document.getElementById('parts-message').textContent = data.message;
    
    const partsList = document.getElementById('parts-list');
    partsList.innerHTML = '';
    
    data.parts.forEach(part => {
        const btn = document.createElement('button');
        btn.className = 'part-item';
        btn.textContent = `Parte ${part.part_index + 1} (${part.char_count} caracteres)`;
        btn.addEventListener('click', () => generateQuizWithPart(data.categoria, data.titulo, part.part_index));
        partsList.appendChild(btn);
    });
    
    document.getElementById('parts-modal').classList.remove('hidden');
}

function initPartsModal() {
    document.getElementById('btn-close-parts').addEventListener('click', () => {
        document.getElementById('parts-modal').classList.add('hidden');
    });
}

async function generateQuizWithPart(categoria, titulo, partIndex) {
    document.getElementById('parts-modal').classList.add('hidden');
    showLoading('Gerando quiz...');
    
    try {
        const response = await fetch(`${API_BASE}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                titulo,
                categoria,
                part_index: partIndex,
                num_perguntas: 10
            })
        });
        
        const data = await response.json();
        displayQuiz(data);
    } catch (error) {
        alert('Erro: ' + error.message);
    } finally {
        hideLoading();
    }
}

function displayQuiz(quiz) {
    currentQuiz = quiz;
    currentQuizId = quiz.quiz_id;
    userAnswers = {};
    
    document.getElementById('quiz-title-display').textContent = quiz.titulo;
    
    const container = document.getElementById('questions-container');
    container.innerHTML = '';
    
    quiz.perguntas.forEach((pergunta, index) => {
        const card = document.createElement('div');
        card.className = 'question-card';
        
        const enunciado = document.createElement('div');
        enunciado.className = 'enunciado';
        enunciado.textContent = `${index + 1}. ${pergunta.enunciado}`;
        card.appendChild(enunciado);
        
        pergunta.opcoes.forEach((opcao, opIndex) => {
            const label = document.createElement('label');
            label.className = 'option-label';
            
            const radio = document.createElement('input');
            radio.type = 'radio';
            radio.name = `question-${index}`;
            radio.value = opIndex;
            radio.addEventListener('change', () => {
                userAnswers[index] = opIndex;
                document.querySelectorAll(`input[name="question-${index}"]`).forEach(r => {
                    r.closest('.option-label').classList.remove('selected');
                });
                label.classList.add('selected');
            });
            
            label.appendChild(radio);
            label.appendChild(document.createTextNode(opcao));
            card.appendChild(label);
        });
        
        container.appendChild(card);
    });
    
    showSection('quiz');
}

function initSubmitQuiz() {
    document.getElementById('btn-submit-quiz').addEventListener('click', async () => {
        if (!currentQuizId) return;
        
        const respostas = {};
        Object.keys(userAnswers).forEach(key => {
            respostas[key] = userAnswers[key];
        });
        
        showLoading('Enviando respostas...');
        
        try {
            const response = await fetch(`${API_BASE}/quiz/${currentQuizId}/submit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ respostas })
            });
            
            const result = await response.json();
            displayResult(result);
        } catch (error) {
            alert('Erro: ' + error.message);
        } finally {
            hideLoading();
        }
    });
}

function displayResult(result) {
    const container = document.getElementById('result-container');
    const percentage = Math.round((result.acertos / result.total) * 100);
    
    let emoji = '';
    if (percentage >= 80) emoji = '🎉';
    else if (percentage >= 50) emoji = '👍';
    else emoji = '📚';
    
    container.innerHTML = `
        <div class="result-header">
            <div class="result-score">${result.acertos}/${result.total}</div>
            <div class="result-label">${percentage}% ${emoji}</div>
        </div>
    `;
    
    const reviewContainer = document.getElementById('questions-review');
    reviewContainer.innerHTML = '<h3>Revisão das Respostas</h3>';
    
    currentQuiz.perguntas.forEach((pergunta, index) => {
        const userAnswer = userAnswers[index];
        const isCorrect = userAnswer === pergunta.resposta_correta;
        
        const item = document.createElement('div');
        item.className = `review-item ${isCorrect ? 'correct' : 'wrong'}`;
        
        item.innerHTML = `
            <div class="enunciado"><strong>Pergunta ${index + 1}:</strong> ${pergunta.enunciado}</div>
            <div>Sua resposta: ${userAnswer !== undefined ? pergunta.opcoes[userAnswer] : 'Não respondida'}</div>
            <div class="${isCorrect ? 'result-correct' : 'result-wrong'}">
                ${isCorrect ? '✓ Correta' : `✗ Correta: ${pergunta.opcoes[pergunta.resposta_correta]}`}
            </div>
            ${pergunta.explicacao ? `<div class="explanation">${pergunta.explicacao}</div>` : ''}
        `;
        
        reviewContainer.appendChild(item);
    });
    
    showSection('result');
}

function initNewQuiz() {
    document.getElementById('btn-new-quiz').addEventListener('click', () => {
        currentQuiz = null;
        currentQuizId = null;
        userAnswers = {};
        document.getElementById('form-generate').reset();
        
        document.querySelectorAll('input[name="categoria-tipo"]').forEach(r => r.checked = r.value === 'existing');
        toggleCategoryInputs('generate');
        
        showSection('generate');
    });
}

function initUploadForm() {
    document.getElementById('form-upload').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const fileInput = document.getElementById('upload-file');
        const file = fileInput.files[0];
        
        if (!file) {
            alert('Selecione um arquivo');
            return;
        }
        
        const categoriaTipo = document.querySelector('input[name="upload-categoria-tipo"]:checked').value;
        let categoria = null;
        
        if (categoriaTipo === 'existing') {
            categoria = document.getElementById('upload-category').value || null;
        } else {
            categoria = document.getElementById('upload-new-category').value || null;
        }
        
        showLoading('Enviando arquivo...');
        
        try {
            const formData = new FormData();
            formData.append('file', file);
            if (categoria) formData.append('category', categoria);
            
            const response = await fetch(`${API_BASE}/upload`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            const resultDiv = document.getElementById('upload-result');
            
            if (data.message && data.message.includes('duplicado')) {
                resultDiv.innerHTML = `<div class="upload-success">⚠️ Material já existe (hash duplicado)</div>`;
            } else {
                resultDiv.innerHTML = `<div class="upload-success">✓ Upload realizado com sucesso!</div>`;
                loadCategories();
            }
            
            fileInput.value = '';
        } catch (error) {
            alert('Erro: ' + error.message);
        } finally {
            hideLoading();
        }
    });
}

function initHistory() {
    document.getElementById('btn-history').addEventListener('click', loadHistory);
}

async function loadHistory() {
    showLoading('Carregando histórico...');
    
    try {
        const response = await fetch(`${API_BASE}/history`);
        const history = await response.json();
        
        const container = document.getElementById('history-container');
        
        if (history.length === 0) {
            container.innerHTML = '<p>Nenhum quiz realizado ainda.</p>';
        } else {
            container.innerHTML = '';
            
            history.forEach(item => {
                const div = document.createElement('div');
                div.className = 'history-item';
                
                const scoreClass = item.acertos !== undefined ? 'complete' : 'pending';
                const scoreText = item.acertos !== undefined 
                    ? `${item.acertos}/${item.total}` 
                    : 'Pendente';
                
                div.innerHTML = `
                    <div class="quiz-info-item">
                        <div class="quiz-title">${item.titulo}</div>
                        <div class="quiz-date">${formatDate(item.criado_em)}</div>
                    </div>
                    <div class="quiz-score ${scoreClass}">${scoreText}</div>
                `;
                
                div.addEventListener('click', () => viewQuiz(item.quiz_id));
                container.appendChild(div);
            });
        }
    } catch (error) {
        console.error('Erro ao carregar histórico:', error);
    } finally {
        hideLoading();
    }
}

async function viewQuiz(quizId) {
    showLoading('Carregando quiz...');
    
    try {
        const response = await fetch(`${API_BASE}/quiz/${quizId}`);
        const quiz = await response.json();
        
        displayQuiz(quiz);
    } catch (error) {
        alert('Erro: ' + error.message);
    } finally {
        hideLoading();
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}