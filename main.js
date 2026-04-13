// Global state to share between modules
window.AppState = {
    datasetId: null,
    chartData: null
};

document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const loadingOverlay = document.getElementById('loading');
    const dashboardContent = document.getElementById('dashboard-content');
    const downloadBtn = document.getElementById('download-report-btn');
    const downloadCsvBtn = document.getElementById('download-csv-btn');
    const uploadNewBtn = document.getElementById('upload-new-btn');
    const historyList = document.getElementById('history-items');
    const headerArea = document.getElementById('header-area');

    // Fetch history
    loadHistory();

    // Reset Dashboard to Upload state
    uploadNewBtn.addEventListener('click', () => {
        dashboardContent.classList.add('hidden');
        dropZone.style.display = 'block';
        dropZone.querySelector('span').innerHTML = `Drag & drop CSV or JSON, or <span class="highlight">browse</span>`;
        uploadNewBtn.style.display = 'none';
        AppState.datasetId = null;
        if(window.ChartManager && typeof window.ChartManager.clear === 'function') {
            window.ChartManager.clear();
        }
    });

    // Make drop zone clickable
    dropZone.addEventListener('click', () => fileInput.click());

    // Drag events
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(evt => {
        dropZone.addEventListener(evt, (e) => { e.preventDefault(); e.stopPropagation(); }, false);
    });

    ['dragenter', 'dragover'].forEach(evt => {
        dropZone.addEventListener(evt, () => dropZone.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(evt => {
        dropZone.addEventListener(evt, () => dropZone.classList.remove('dragover'), false);
    });

    dropZone.addEventListener('drop', (e) => {
        let dt = e.dataTransfer;
        let files = dt.files;
        handleFiles(files);
    });

    fileInput.addEventListener('change', function() { handleFiles(this.files); });

    function handleFiles(files) {
        if (!files.length) return;
        const file = files[0];
        if (!file.name.endsWith('.csv') && !file.name.endsWith('.json')) {
            alert("Only CSV and JSON files are supported.");
            return;
        }
        uploadFile(file);
    }

    async function uploadFile(file) {
        let formData = new FormData();
        formData.append('file', file);
        loadingOverlay.classList.remove('hidden');

        try {
            let response = await fetch('/api/upload', { method: 'POST', body: formData });
            let data = await response.json();
            
            if (response.ok) {
                renderDashboard(data);
                loadHistory(); // refresh history
            } else {
                alert("Upload failed: " + (data.error || "Unknown error"));
            }
        } catch (error) {
            console.error(error);
            alert("Connection error. Ensure the server is running.");
        } finally {
            loadingOverlay.classList.add('hidden');
            fileInput.value = '';
        }
    }

    async function loadDataset(ds_id) {
        loadingOverlay.classList.remove('hidden');
        try {
            let response = await fetch(`/api/load/${ds_id}`);
            let data = await response.json();
            if (response.ok) {
                renderDashboard(data);
            } else {
                alert("Failed to load dataset: " + data.error);
            }
        } catch (error) {
            console.error(error);
        } finally {
            loadingOverlay.classList.add('hidden');
        }
    }

    function renderDashboard(data) {
        document.getElementById('ai-summary-content').innerHTML = marked(data.summary);
        AppState.datasetId = data.dataset_id;
        AppState.chartData = data.chart_data;

        if (window.ChartManager && typeof window.ChartManager.init === 'function') {
            window.ChartManager.init(data.chart_data);
        }
        
        document.getElementById('chat-input').disabled = false;
        document.getElementById('send-chat').disabled = false;

        dropZone.style.display = 'none';
        uploadNewBtn.style.display = 'block';
        dashboardContent.classList.remove('hidden');
    }

    async function loadHistory() {
        try {
            let response = await fetch('/api/history');
            if(response.ok) {
                let items = await response.json();
                historyList.innerHTML = '';
                items.forEach(item => {
                    let d = document.createElement('div');
                    d.className = 'history-item';
                    d.innerHTML = `<i class="fa-solid fa-file-csv"></i> ${item.filename}`;
                    d.title = new Date(item.upload_date).toLocaleString();
                    d.addEventListener('click', () => loadDataset(item.id));
                    historyList.appendChild(d);
                });
            }
        } catch(e) { console.error("History fetch error", e); }
    }

    downloadBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if(!AppState.datasetId) {
            alert("Please upload or load a dataset first."); return;
        }
        const controls = document.querySelectorAll('.controls-panel, .filter-panel, .ai-chat-widget');
        controls.forEach(c => c.style.display = 'none');

        const element = document.getElementById('report-content');
        const opt = {
            margin: 0.5, filename: 'AI_Data_Report.pdf',
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { scale: 2, useCORS: true },
            jsPDF: { unit: 'in', format: 'letter', orientation: 'landscape' }
        };

        html2pdf().set(opt).from(element).save().then(() => {
            controls.forEach(c => c.style.display = 'flex');
        });
    });

    downloadCsvBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if(!AppState.datasetId) {
            alert("Please upload or load a dataset first."); return;
        }
        // Native browser download flow
        window.location.href = `/api/download_clean/${AppState.datasetId}`;
    });

    function marked(str) {
        if(!str) return "";
        let parsed = str.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        parsed = parsed.replace(/### (.*?)\n/g, '<h3>$1</h3>');
        parsed = parsed.replace(/\n\n/g, '</p><p>');
        parsed = parsed.replace(/\n/g, '<br>');
        parsed = parsed.replace(/- (.*?)<br>/g, '<li>$1</li>');
        parsed = parsed.replace(/- (.*?)$/g, '<li>$1</li>');
        if(parsed.includes('<li>')) { parsed = parsed.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>'); }
        return `<p>${parsed}</p>`;
    }
});
