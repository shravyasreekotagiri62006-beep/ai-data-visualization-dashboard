// charts.js - Handles ChartJS and GridStack integration

window.ChartManager = (function() {
    let grid = null;
    let chartIdCounter = 0;
    let datasetMetrics = null;

    function init(chartData) {
        datasetMetrics = chartData;
        
        // Populate Selectors
        const typeSelector = document.getElementById('chart-type-selector');
        const xSelector = document.getElementById('x-axis-selector');
        const ySelector = document.getElementById('y-axis-selector');
        
        xSelector.innerHTML = '';
        ySelector.innerHTML = '';
        
        chartData.columns.forEach(col => {
            xSelector.innerHTML += `<option value="${col}">${col}</option>`;
        });
        
        chartData.numeric.forEach(col => {
            ySelector.innerHTML += `<option value="${col}">${col}</option>`;
        });
        
        // Initialize GridStack
        if(!grid) {
            grid = GridStack.init({
                margin: 10,
                cellHeight: '100px',
                float: true
            });
        } else {
            grid.removeAll();
        }

        // Event listener for adding charts
        const addBtn = document.getElementById('add-chart-btn');
        // Prevent multiple bindings
        const newAddBtn = addBtn.cloneNode(true);
        addBtn.parentNode.replaceChild(newAddBtn, addBtn);
        
        newAddBtn.addEventListener('click', () => {
            addChart(
                typeSelector.value,
                xSelector.value,
                ySelector.value
            );
        });

        // Add a default chart automatically to show wow factor
        if (chartData.numeric.length > 0) {
            const defaultX = chartData.categorical.length > 0 ? chartData.categorical[0] : chartData.columns[0];
            const defaultY = chartData.numeric[0];
            addChart('bar', defaultX, defaultY);
            
            if (chartData.numeric.length > 1) {
                addChart('line', defaultX, chartData.numeric[1]);
            }
        }
    }

    function addChart(type, xCol, yCol) {
        if(!datasetMetrics) return;

        const id = `chart-${chartIdCounter++}`;
        const title = `${yCol} by ${xCol}`;

        // Create Grid node HTML
        const nodeHtml = `
            <div class="grid-stack-item" gs-w="6" gs-h="4" id="item-${id}">
                <div class="grid-stack-item-content">
                    <div class="item-header">
                        <span>${title}</span>
                        <i class="fa-solid fa-xmark remove-chart" data-id="${id}"></i>
                    </div>
                    <div class="chart-container">
                        <canvas id="${id}"></canvas>
                    </div>
                </div>
            </div>
        `;

        grid.addWidget(nodeHtml);

        // Render Chart using Chart.js
        renderChartJS(id, type, xCol, yCol, title);

        // Bind remove event
        document.querySelector(`.remove-chart[data-id="${id}"]`).addEventListener('click', function() {
            grid.removeWidget(document.getElementById(`item-${id}`));
        });
    }

    function renderChartJS(canvasId, type, xCol, yCol, label) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        
        // Extract data
        let labels = datasetMetrics.preview.map(row => row[xCol]);
        let data = datasetMetrics.preview.map(row => row[yCol]);

        // Simple aggregation if pie or doughnut (count/sum)
        if (type === 'pie' || type === 'doughnut') {
            let agg = {};
            for(let i=0; i<labels.length; i++) {
                let l = labels[i] || 'Unknown';
                agg[l] = (agg[l] || 0) + parseFloat(data[i] || 0);
            }
            
            // Sort by value descending and group "Others" if too many categories
            let entries = Object.entries(agg).sort((a, b) => b[1] - a[1]);
            
            if (entries.length > 10) {
                const top9 = entries.slice(0, 9);
                const othersSum = entries.slice(9).reduce((sum, current) => sum + current[1], 0);
                labels = [...top9.map(e => e[0]), 'Others'];
                data = [...top9.map(e => e[1]), othersSum];
            } else {
                labels = entries.map(e => e[0]);
                data = entries.map(e => e[1]);
            }
        }


        // Colors
        const colors = [
            'rgba(99, 102, 241, 0.7)',
            'rgba(236, 72, 153, 0.7)',
            'rgba(16, 185, 129, 0.7)',
            'rgba(245, 158, 11, 0.7)',
            'rgba(139, 92, 246, 0.7)',
            'rgba(59, 130, 246, 0.7)'
        ];

        // Colorful dynamic arrays for Bar & Line
        const bgColors = colors.slice(0, data.length);
        while(bgColors.length < data.length) { bgColors.push(...colors); } // loop colors

        new Chart(ctx, {
            type: type,
            data: {
                labels: labels.slice(0, 50),
                datasets: [{
                    label: label,
                    data: data.slice(0, 50),
                    backgroundColor: (type === 'line') ? 'rgba(99, 102, 241, 0.2)' : bgColors,
                    borderColor: (type === 'line') ? 'rgba(99, 102, 241, 1)' : bgColors.map(c => c.replace('0.7', '1')),
                    borderWidth: 2,
                    tension: 0.3,
                    fill: type === 'line' ? true : false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: '#1e293b', font: { weight: '500' } }
                    }
                },
                scales: (type === 'pie' || type === 'doughnut') ? {} : {
                    x: { 
                        ticks: { color: '#475569' }, 
                        grid: { color: 'rgba(0,0,0,0.05)' } 
                    },
                    y: { 
                        ticks: { color: '#475569' }, 
                        grid: { color: 'rgba(0,0,0,0.05)' } 
                    }
                }

            }
        });
    }

    return { init };
})();
