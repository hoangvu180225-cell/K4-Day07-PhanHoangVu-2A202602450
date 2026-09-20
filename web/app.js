// JavaScript Application Logic for Web Dashboard

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initSlider();
    initPresetQueries();
    initSearchForm();
    loadDocuments();
    loadBenchmarkData();
});

// Tab Switcher Logic
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            btn.classList.add('active');
            const targetTab = document.getElementById(btn.dataset.tab);
            if (targetTab) targetTab.classList.add('active');
        });
    });
}

// Slider Logic
function initSlider() {
    const slider = document.getElementById('top-k-slider');
    const valDisplay = document.getElementById('top-k-val');

    if (slider && valDisplay) {
        slider.addEventListener('input', () => {
            valDisplay.textContent = slider.value;
        });
    }
}

// Preset Queries Select
function initPresetQueries() {
    const select = document.getElementById('preset-query-select');
    const textarea = document.getElementById('search-query-input');

    if (select && textarea) {
        select.addEventListener('change', () => {
            if (select.value) {
                textarea.value = select.value;
            }
        });
    }
}

// Run Search API Call
function initSearchForm() {
    const btn = document.getElementById('btn-run-search');
    const queryInput = document.getElementById('search-query-input');
    const strategySelect = document.getElementById('strategy-select');
    const audienceSelect = document.getElementById('audience-select');
    const slider = document.getElementById('top-k-slider');
    const resultsContainer = document.getElementById('search-results-container');

    if (!btn) return;

    btn.addEventListener('click', async () => {
        const query = queryInput.value.trim();
        if (!query) {
            alert('Vui lòng nhập câu hỏi tra cứu!');
            return;
        }

        btn.disabled = true;
        btn.innerHTML = `<span class="btn-icon">⏳</span> Searching...`;

        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: query,
                    strategy: strategySelect.value,
                    audience: audienceSelect.value,
                    top_k: parseInt(slider.value),
                })
            });

            const data = await response.json();
            renderSearchResults(data);
        } catch (err) {
            console.error('Search error:', err);
            resultsContainer.innerHTML = `<div class="empty-state"><p style="color: red;">Lỗi khi thực hiện tìm kiếm: ${err.message}</p></div>`;
        } finally {
            btn.disabled = false;
            btn.innerHTML = `<span class="btn-icon">🚀</span> Run Vector Search & Agent RAG`;
        }
    });
}

// Render Search Results
function renderSearchResults(data) {
    const resultsContainer = document.getElementById('search-results-container');
    if (!resultsContainer) return;

    let html = '';

    // Agent Answer Box
    html += `
        <div class="agent-answer-box">
            <div class="agent-answer-header">🤖 Agent Synthesis Answer (${data.strategy}):</div>
            <div class="agent-answer-text">${escapeHtml(data.agent_answer)}</div>
        </div>
        <div class="chunk-list-title">Top ${data.results.length} Chunks Retrieved (Indexed Total: ${data.total_chunks_indexed} chunks):</div>
    `;

    if (data.results && data.results.length > 0) {
        data.results.forEach((rec, idx) => {
            const score = rec.score ? rec.score.toFixed(4) : 'N/A';
            const docId = rec.metadata?.doc_id || rec.id;
            const snippet = rec.content || '';

            html += `
                <div class="chunk-card">
                    <div class="chunk-card-header">
                        <span class="chunk-doc-badge">#${idx+1} Doc: ${escapeHtml(docId)}</span>
                        <span class="chunk-score-badge">Similarity: ${score}</span>
                    </div>
                    <div class="chunk-body">${escapeHtml(snippet)}</div>
                </div>
            `;
        });
    } else {
        html += `<div class="empty-state"><p>Không tìm thấy chunk nào khớp với bộ lọc metadata đã chọn.</p></div>`;
    }

    resultsContainer.innerHTML = html;
}

// Load Documents Explorer
async function loadDocuments() {
    const grid = document.getElementById('documents-grid');
    if (!grid) return;

    try {
        const response = await fetch('/api/documents');
        const docs = await response.json();

        grid.innerHTML = docs.map(doc => `
            <div class="doc-card" onclick="openDocModal('${escapeHtml(doc.doc_id)}')">
                <div class="doc-card-title">📄 ${escapeHtml(doc.title)}</div>
                <div class="doc-meta-tags">
                    <span class="meta-tag tag-${doc.audience}">${doc.audience.toUpperCase()}</span>
                    <span class="meta-tag">Ver: ${doc.document_version}</span>
                    <span class="meta-tag">${doc.char_count} chars</span>
                </div>
                <div class="doc-card-snippet">${escapeHtml(doc.content.substring(0, 150))}...</div>
            </div>
        `).join('');

        window.cachedDocs = docs;
    } catch (err) {
        console.error('Load documents error:', err);
    }
}

// Modal View for Document
window.openDocModal = function(docId) {
    const docs = window.cachedDocs || [];
    const doc = docs.find(d => d.doc_id === docId);
    if (!doc) return;

    document.getElementById('modal-doc-title').textContent = doc.title;
    document.getElementById('modal-doc-metadata').innerHTML = `
        <span><strong>Doc ID:</strong> ${doc.doc_id}</span> |
        <span><strong>Audience:</strong> ${doc.audience}</span> |
        <span><strong>Version:</strong> ${doc.document_version}</span> |
        <span><strong>Source:</strong> <a href="${doc.source_url}" target="_blank" style="color:#60a5fa;">Link</a></span>
    `;
    document.getElementById('modal-doc-content').textContent = doc.content;

    document.getElementById('doc-modal').classList.add('active');
};

document.getElementById('modal-close-btn')?.addEventListener('click', () => {
    document.getElementById('doc-modal').classList.remove('active');
});

// Load Benchmark Data & Render Chart
async function loadBenchmarkData() {
    const cardsContainer = document.getElementById('bench-cards-container');
    if (!cardsContainer) return;

    try {
        const response = await fetch('/api/benchmark');
        const data = await response.json();

        if (data && data.length > 0) {
            cardsContainer.innerHTML = data.map(item => `
                <div class="bench-card">
                    <div class="bench-card-title">🧩 ${escapeHtml(item.chunker_name)}</div>
                    <div class="bench-stat-row">
                        <span>Total Chunks Generated:</span>
                        <span class="bench-stat-val">${item.total_chunks}</span>
                    </div>
                    <div class="bench-stat-row">
                        <span>Doc Hits (Top-1 Match):</span>
                        <span class="bench-stat-val">${item.hits} / ${item.total_queries}</span>
                    </div>
                    <div class="bench-stat-row">
                        <span>Accuracy Rate:</span>
                        <span class="bench-stat-val green-text">${(item.accuracy * 100).toFixed(1)}%</span>
                    </div>
                </div>
            `).join('');

            renderBenchmarkChart(data);
        }
    } catch (err) {
        console.error('Load benchmark error:', err);
    }
}

let chartInstance = null;
function renderBenchmarkChart(data) {
    const ctx = document.getElementById('benchmark-chart')?.getContext('2d');
    if (!ctx) return;

    if (chartInstance) chartInstance.destroy();

    const labels = data.map(d => d.chunker_name);
    const chunkCounts = data.map(d => d.total_chunks);
    const accuracies = data.map(d => (d.accuracy * 100));

    chartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Accuracy (%)',
                    data: accuracies,
                    backgroundColor: 'rgba(139, 92, 246, 0.7)',
                    borderColor: '#8b5cf6',
                    borderWidth: 1,
                    yAxisID: 'y'
                },
                {
                    label: 'Total Chunks Generated',
                    data: chunkCounts,
                    backgroundColor: 'rgba(6, 182, 212, 0.7)',
                    borderColor: '#06b6d4',
                    borderWidth: 1,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                y: {
                    type: 'linear', position: 'left', max: 100,
                    title: { display: true, text: 'Accuracy (%)', color: '#8b5cf6' },
                    ticks: { color: '#9ca3af' }, grid: { color: 'rgba(255,255,255,0.05)' }
                },
                y1: {
                    type: 'linear', position: 'right',
                    title: { display: true, text: 'Chunks Count', color: '#06b6d4' },
                    ticks: { color: '#9ca3af' }, grid: { drawOnChartArea: false }
                }
            },
            plugins: {
                legend: { labels: { color: '#f3f4f6' } }
            }
        }
    });
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
