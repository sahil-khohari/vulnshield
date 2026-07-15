document.addEventListener('DOMContentLoaded', function() {
    // Navigation elements
    const navHome = document.getElementById('nav-home');
    const navScanner = document.getElementById('nav-scanner');
    const navReports = document.getElementById('nav-reports');
    const navAbout = document.getElementById('nav-about');
    
    // Content sections
    const homeSection = document.getElementById('home-section');
    const scannerSection = document.getElementById('scanner-section');
    const reportsSection = document.getElementById('reports-section');
    const aboutSection = document.getElementById('about-section');
    
    // Buttons
    const startScanningBtn = document.getElementById('start-scanning-btn');
    const scanForm = document.getElementById('scan-form');
    const backToReportsBtn = document.getElementById('back-to-reports');
    
    // Other elements
    const scanProgress = document.getElementById('scan-progress');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const reportDetail = document.getElementById('report-detail');
    const reportsListContainer = document.getElementById('reports-list');
    const vulnerabilitiesList = document.getElementById('vulnerabilities-list');
    
    // Navigation functions
    function showSection(section) {
        homeSection.classList.add('hidden');
        scannerSection.classList.add('hidden');
        reportsSection.classList.add('hidden');
        aboutSection.classList.add('hidden');
        
        section.classList.remove('hidden');
    }
    
    // Navigation event listeners
    navHome.addEventListener('click', function(e) {
        e.preventDefault();
        showSection(homeSection);
    });
    
    navScanner.addEventListener('click', function(e) {
        e.preventDefault();
        showSection(scannerSection);
    });
    
    navReports.addEventListener('click', function(e) {
        e.preventDefault();
        showSection(reportsSection);
        loadReports();
    });
    
    navAbout.addEventListener('click', function(e) {
        e.preventDefault();
        showSection(aboutSection);
    });
    
    startScanningBtn.addEventListener('click', function() {
        showSection(scannerSection);
    });
    
    // Scan type selection
    const scanTypeOptions = document.querySelectorAll('.scan-type-option');
    scanTypeOptions.forEach(option => {
        option.addEventListener('click', function() {
            const radio = this.querySelector('input[type="radio"]');
            radio.checked = true;
        });
    });
    
    // Handle scan form submission
    scanForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const target = document.getElementById('target').value.trim();
        const scanType = document.querySelector('input[name="scan-type"]:checked').value;
        
        if (!target) {
            alert('Please enter a target URL or IP address');
            return;
        }
        
        // Show progress bar
        scanForm.classList.add('hidden');
        scanProgress.classList.remove('hidden');
        progressBar.style.width = '10%';
        progressText.textContent = 'Initializing scan...';
        
        try {
            // Start the scan
            const response = await fetch('/api/scan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    target: target,
                    scan_type: scanType
                })
            });
            
            if (!response.ok) {
                throw new Error('Scan failed to start');
            }
            
            const data = await response.json();
            
            if (data.status === 'success' && data.scan_id) {
                // Poll for scan status
                const pollInterval = setInterval(async () => {
                    try {
                        const statusResponse = await fetch(`/api/scan/${data.scan_id}/status`);
                        const statusData = await statusResponse.json();
                        
                        if (statusData.status === 'completed') {
                            clearInterval(pollInterval);
                            progressBar.style.width = '100%';
                            progressText.textContent = 'Scan completed successfully!';
                            
                            // Wait a moment before switching to reports
                            setTimeout(() => {
                                showSection(reportsSection);
                                // Reset scan form for next use
                                scanForm.reset();
                                scanForm.classList.remove('hidden');
                                scanProgress.classList.add('hidden');
                                progressBar.style.width = '0%';
                                // Load and display updated reports
                                loadReports();
                            }, 2000);
                        } else if (statusData.status === 'error') {
                            clearInterval(pollInterval);
                            throw new Error(statusData.message || 'Scan failed');
                        } else {
                            // Update progress
                            progressBar.style.width = `${statusData.progress || 10}%`;
                            progressText.textContent = statusData.message || 'Scanning...';
                        }
                    } catch (error) {
                        clearInterval(pollInterval);
                        throw error;
                    }
                }, 5000); // Poll every 5 seconds
            } else {
                throw new Error(data.message || 'Scan failed to start');
            }
        } catch (error) {
            console.error('Scan error:', error);
            progressText.textContent = `Error: ${error.message}`;
            progressBar.style.width = '0%';
            
            // Show retry button
            scanProgress.innerHTML += `
                <button onclick="location.reload()" class="mt-4 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                    Retry Scan
                </button>
            `;
        }
    });
    
    // Back to reports list button
    backToReportsBtn.addEventListener('click', function() {
        reportDetail.classList.add('hidden');
    });
    
    // Load reports from API
    function loadReports() {
        fetch('/api/reports')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch reports');
                }
                return response.json();
            })
            .then(reports => {
                // Add a check for empty array
                if (!reports || !Array.isArray(reports)) {
                    reports = [];
                }
                displayReportsList(reports);
            })
            .catch(error => {
                console.error('Error loading reports:', error);
                reportsListContainer.innerHTML = `
                    <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                        <p>Error loading reports: ${error.message}</p>
                    </div>
                    <p class="text-gray-700">Try refreshing the page or check the connection to the server.</p>
                `;
            });
    }
    
    // Display list of reports
    function displayReportsList(reports) {
        if (!reports || reports.length === 0) {
            reportsListContainer.innerHTML = `
                <div class="text-gray-600 py-4">
                    <p>No reports found. Run a scan to generate reports.</p>
                </div>
                <button id="no-reports-scan-btn" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
                    Start a Scan
                </button>
            `;
            
            document.getElementById('no-reports-scan-btn').addEventListener('click', function() {
                showSection(scannerSection);
            });
            
            return;
        }
        
        let html = `
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Target</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Vulnerabilities</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Risk Score</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
        `;
        
        reports.forEach(report => {
            // Format date
            const scanDate = new Date(report.scan_date);
            const formattedDate = scanDate.toLocaleDateString() + ' ' + scanDate.toLocaleTimeString();
            
            // Risk score color
            let riskScoreClass = 'text-green-600';
            if (report.max_risk_score >= 9) {
                riskScoreClass = 'text-red-600';
            } else if (report.max_risk_score >= 7) {
                riskScoreClass = 'text-orange-500';
            } else if (report.max_risk_score >= 4) {
                riskScoreClass = 'text-yellow-500';
            }
            
            html += `
                <tr class="hover:bg-gray-50">
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm font-medium text-gray-900">${report.target}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm text-gray-500">${formattedDate}</div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                            ${report.status}
                        </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        ${report.vuln_count || 0}
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <div class="text-sm font-medium ${riskScoreClass}">
                            ${report.max_risk_score !== null && report.max_risk_score !== undefined ? Number(report.max_risk_score).toFixed(1) : 'N/A'}
                        </div>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button class="text-blue-600 hover:text-blue-900 view-report-btn" data-scan-id="${report.scan_id}">
                            View Details
                        </button>
                    </td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
        
        reportsListContainer.innerHTML = html;
        
        // Add event listeners to view report buttons
        document.querySelectorAll('.view-report-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const scanId = this.getAttribute('data-scan-id');
                loadReportDetail(scanId);
            });
        });
    }
    
    // Load report detail from API
    function loadReportDetail(scanId) {
        fetch(`/api/report/${scanId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch report');
                }
                return response.json();
            })
            .then(report => {
                displayReportDetail(report);
            })
            .catch(error => {
                console.error('Error loading report detail:', error);
                reportDetail.innerHTML = `
                    <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                        <p>Error loading report: ${error.message}</p>
                    </div>
                    <button id="back-to-reports-error" class="text-blue-600 hover:underline flex items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-1" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M7.707 14.707a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l2.293 2.293a1 1 0 010 1.414z" clip-rule="evenodd" />
                        </svg>
                        Back to Reports
                    </button>
                `;
                
                document.getElementById('back-to-reports-error').addEventListener('click', function() {
                    reportDetail.classList.add('hidden');
                });
            });
    }
    
    // Display report detail
    function displayReportDetail(report) {
        // Show reports section if not already visible
        reportsSection.classList.remove('hidden');
        
        // Show report detail section and hide reports list container
        reportDetail.classList.remove('hidden');
        
        // Hide the reports list container (the first div in the reports section)
        const reportsListContainer = document.querySelector('#reports-section > div:first-child');
        reportsListContainer.classList.add('hidden');
        
        // Update report info
        document.getElementById('report-title').textContent = `Report for ${report.scan_info.target}`;
        document.getElementById('report-target').textContent = report.scan_info.target;
        document.getElementById('report-date').textContent = new Date(report.scan_info.scan_date).toLocaleString();
        document.getElementById('report-status').textContent = report.scan_info.status;
        
        // Ensure we're only working with vulnerabilities from this specific scan
        const scanVulnerabilities = report.vulnerabilities || [];
        
        // Update vulnerability counts based on this scan's data only
        const riskLevels = {
            critical: scanVulnerabilities.filter(v => v.risk_score >= 9).length,
            high: scanVulnerabilities.filter(v => v.risk_score >= 7 && v.risk_score < 9).length,
            medium: scanVulnerabilities.filter(v => v.risk_score >= 4 && v.risk_score < 7).length,
            low: scanVulnerabilities.filter(v => v.risk_score < 4 && v.risk_score !== undefined && v.risk_score !== null && !isNaN(v.risk_score)).length
        };
        
        document.getElementById('critical-count').textContent = riskLevels.critical;
        document.getElementById('high-count').textContent = riskLevels.high;
        document.getElementById('medium-count').textContent = riskLevels.medium;
        document.getElementById('low-count').textContent = riskLevels.low;
        
        // Calculate overall risk score (average of all vulnerabilities from this scan only)
        let overallScore = 0;
        
        if (scanVulnerabilities.length > 0) {
            // Filter out any vulnerabilities with undefined or NaN risk scores
            const validScores = scanVulnerabilities
                .filter(v => v.risk_score !== undefined && v.risk_score !== null && !isNaN(v.risk_score))
                .map(v => Number(v.risk_score));
            
            if (validScores.length > 0) {
                // Calculate the average of valid scores
                overallScore = validScores.reduce((sum, score) => sum + score, 0) / validScores.length;
                // Round to 1 decimal place
                overallScore = Math.round(overallScore * 10) / 10;
            }
        }
        
        // Ensure we display a valid number or fallback to a meaningful string
        document.getElementById('overall-risk-score').textContent = 
            (!isNaN(overallScore) && overallScore !== null && overallScore !== undefined) 
                ? overallScore.toFixed(1) 
                : '0.0';
        
        // Create charts with scan-specific data
        createRiskScoreChart(overallScore);
        createSeverityChart(riskLevels);
        createSourceChart({
            nmap: scanVulnerabilities.filter(v => v.source === "nmap").length,
            zap: scanVulnerabilities.filter(v => v.source === "zap").length
        });
        
        // Display vulnerabilities from this scan only
        displayVulnerabilities(scanVulnerabilities);
        
        // Remove any existing event listeners from the back button by cloning and replacing it
        const backButton = document.getElementById('back-to-reports');
        const newBackButton = backButton.cloneNode(true);
        backButton.parentNode.replaceChild(newBackButton, backButton);
        
        // Add event listener to the new back button
        newBackButton.addEventListener('click', function() {
            // Hide report detail and show reports list
            reportDetail.classList.add('hidden');
            reportsListContainer.classList.remove('hidden');
        });
    }
    
    // Create risk score chart (gauge)
    function createRiskScoreChart(score) {
        if (score === null || score === undefined) {
            score = 0;
        }
        score = Number(score);
        
        const ctx = document.getElementById('risk-score-chart').getContext('2d');
        
        // Destroy existing chart if it exists
        if (window.riskScoreChart) {
            window.riskScoreChart.destroy();
        }
        
        // Risk score gauge chart
        window.riskScoreChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [score, 10 - score],
                    backgroundColor: [
                        getScoreColor(score),
                        '#f0f0f0'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                cutout: '70%',
                responsive: true,
                maintainAspectRatio: true,
                circumference: 180,
                rotation: -90,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: false
                    }
                }
            }
        });
    }
    
    // Create severity distribution chart
    function createSeverityChart(riskLevels) {
        const ctx = document.getElementById('severity-chart').getContext('2d');
        
        // Destroy existing chart if it exists
        if (window.severityChart) {
            window.severityChart.destroy();
        }
        
        window.severityChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Critical', 'High', 'Medium', 'Low'],
                datasets: [{
                    label: 'Vulnerabilities by Severity',
                    data: [
                        riskLevels.critical || 0,
                        riskLevels.high || 0,
                        riskLevels.medium || 0,
                        riskLevels.low || 0
                    ],
                    backgroundColor: [
                        '#dc2626', // red-600
                        '#ea580c', // orange-500
                        '#eab308', // yellow-500
                        '#16a34a'  // green-600
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Vulnerabilities by Severity',
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    },
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
    }
    
    // Create source distribution chart
    function createSourceChart(sources) {
        const ctx = document.getElementById('source-chart').getContext('2d');
        
        // Destroy existing chart if it exists
        if (window.sourceChart) {
            window.sourceChart.destroy();
        }
        
        window.sourceChart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: ['NMAP', 'ZAP'],
                datasets: [{
                    label: 'Vulnerabilities by Source',
                    data: [
                        sources.nmap || 0,
                        sources.zap || 0
                    ],
                    backgroundColor: [
                        '#3b82f6', // blue-500
                        '#8b5cf6'  // purple-500
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Vulnerabilities by Source',
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    },
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20
                        }
                    }
                }
            }
        });
    }
    
    // Display vulnerabilities list
    function displayVulnerabilities(vulnerabilities) {
        if (!vulnerabilities || vulnerabilities.length === 0) {
            vulnerabilitiesList.innerHTML = `
                <div class="text-gray-600 py-4">
                    <p>No vulnerabilities found in this scan.</p>
                </div>
            `;
            return;
        }
        
        // Filter out vulnerabilities with risk score of 0
        const significantVulnerabilities = vulnerabilities.filter(v => v.risk_score > 0);
        
        if (significantVulnerabilities.length === 0) {
            vulnerabilitiesList.innerHTML = `
                <div class="text-gray-600 py-4">
                    <p>No significant vulnerabilities found in this scan.</p>
                </div>
            `;
            return;
        }
        
        // Group vulnerabilities by source for normal display
        const vulnsBySource = {
            nmap: significantVulnerabilities.filter(v => v.source === "nmap"),
            zap: significantVulnerabilities.filter(v => v.source === "zap"),
            other: significantVulnerabilities.filter(v => v.source !== "nmap" && v.source !== "zap")
        };
        
        let html = `<div class="space-y-8">`;
        
        // Display NMAP vulnerabilities
        if (vulnsBySource.nmap.length > 0) {
            html += `
                <div class="mb-6">
                    <h4 class="text-lg font-semibold mb-2 flex items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                        </svg>
                        NMAP Vulnerabilities
                    </h4>
                    <p class="text-sm text-gray-600">Found ${vulnsBySource.nmap.length} vulnerabilities</p>
                </div>
            `;
            
            vulnsBySource.nmap.sort((a, b) => b.risk_score - a.risk_score);
            vulnsBySource.nmap.forEach((vuln, index) => {
                html += generateVulnerabilityHTML(vuln, index);
            });
        }
        
        // Display ZAP vulnerabilities
        if (vulnsBySource.zap.length > 0) {
            html += `
                <div class="mb-6 mt-8">
                    <h4 class="text-lg font-semibold mb-2 flex items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
                        </svg>
                        ZAP Vulnerabilities
                    </h4>
                    <p class="text-sm text-gray-600">Found ${vulnsBySource.zap.length} vulnerabilities</p>
                </div>
            `;
            
            vulnsBySource.zap.sort((a, b) => b.risk_score - a.risk_score);
            vulnsBySource.zap.forEach((vuln, index) => {
                html += generateVulnerabilityHTML(vuln, index);
            });
        }
        
        // Display other vulnerabilities
        if (vulnsBySource.other.length > 0) {
            html += `
                <div class="mb-6 mt-8">
                    <h4 class="text-lg font-semibold mb-2 flex items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                        Other Vulnerabilities
                    </h4>
                    <p class="text-sm text-gray-600">Found ${vulnsBySource.other.length} vulnerabilities</p>
                </div>
            `;
            
            vulnsBySource.other.sort((a, b) => b.risk_score - a.risk_score);
            vulnsBySource.other.forEach((vuln, index) => {
                html += generateVulnerabilityHTML(vuln, index);
            });
        }
        
        html += `</div>`;
        vulnerabilitiesList.innerHTML = html;
        
        // Add click event listeners to vulnerability headers
        document.querySelectorAll('.vuln-header').forEach(header => {
            header.addEventListener('click', function() {
                const vulnId = this.getAttribute('data-vuln-id');
                const vulnBody = this.nextElementSibling;
                const chevron = this.querySelector('.vuln-chevron');
                
                if (vulnBody.classList.contains('hidden')) {
                    vulnBody.classList.remove('hidden');
                    if (chevron) {
                        chevron.classList.add('transform', 'rotate-180');
                    }
                } else {
                    vulnBody.classList.add('hidden');
                    if (chevron) {
                        chevron.classList.remove('transform', 'rotate-180');
                    }
                }
            });
        });
    }
    
    // Helper function to generate vulnerability HTML
    function generateVulnerabilityHTML(vuln, index) {
        // Determine severity class
        let severityClass = 'bg-green-100 text-green-800';
        let severityText = 'Low';
        
        if (vuln.risk_score >= 9) {
            severityClass = 'bg-red-100 text-red-800';
            severityText = 'Critical';
        } else if (vuln.risk_score >= 7) {
            severityClass = 'bg-orange-100 text-orange-800';
            severityText = 'High';
        } else if (vuln.risk_score >= 4) {
            severityClass = 'bg-yellow-100 text-yellow-800';
            severityText = 'Medium';
        }
        
        // Ensure risk_score is a number and greater than 0
        const riskScore = vuln.risk_score !== null && vuln.risk_score !== undefined && vuln.risk_score > 0
            ? Number(vuln.risk_score).toFixed(1) 
            : '1.0'; // Default to 1.0 instead of showing 0.0
        
        // Format description for better readability, especially for Nmap results
        let formattedDescription = vuln.description || 'No description available';
        
        // Special handling for vulners scanner output
        if (vuln.source === 'nmap') {
            // Always use the full script_output if available
            if (vuln.script_output) {
                formattedDescription = formatNmapDescription(vuln.script_output);
            } else {
                formattedDescription = formatNmapDescription(vuln.description);
            }
        } else if (vuln.source === 'zap') {
            formattedDescription = formatZapDescription(vuln);
        }
        
        return `
            <div class="mb-6 border rounded-lg overflow-hidden ${index === 0 ? 'border-2 border-red-300' : ''}">
                <div class="flex justify-between items-center p-4 bg-gray-50 cursor-pointer vuln-header" data-vuln-id="${vuln.vuln_id || index}">
                    <div class="flex-1">
                        <h5 class="font-semibold">${vuln.name || 'Unknown'}</h5>
                        <p class="text-sm text-gray-600">Source: ${(vuln.source || 'unknown').toUpperCase()}</p>
                    </div>
                    <div class="flex items-center space-x-3">
                        <span class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${severityClass}">
                            ${severityText}
                        </span>
                        <div class="text-center">
                            <div class="font-semibold">${riskScore}</div>
                            <div class="text-xs text-gray-500">Risk Score</div>
                        </div>
                        <svg class="h-5 w-5 text-gray-500 vuln-chevron" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
                        </svg>
                    </div>
                </div>
                <div class="p-4 border-t hidden vuln-details">
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div>
                            <h6 class="font-semibold mb-2">Details</h6>
                            <div class="text-sm text-gray-700 mb-2 whitespace-pre-line overflow-auto max-h-96">${formattedDescription}</div>
                            <div class="grid grid-cols-2 gap-2 mt-4">
                                <div>
                                    <span class="text-xs text-gray-500">CVSS Score</span>
                                    <div class="font-medium">${vuln.cvss_score !== null && vuln.cvss_score !== undefined ? Number(vuln.cvss_score).toFixed(1) : 'N/A'}</div>
                                </div>
                                <div>
                                    <span class="text-xs text-gray-500">EPSS Score</span>
                                    <div class="font-medium">${vuln.epss_score !== null && vuln.epss_score !== undefined ? Number(vuln.epss_score).toFixed(4) : 'N/A'}</div>
                                </div>
                            </div>
                            ${vuln.urls && vuln.urls.length > 0 ? `
                            <div class="mt-3">
                                <h6 class="text-xs text-gray-500 mb-1">Affected URLs</h6>
                                <ul class="list-disc pl-5 text-xs text-gray-700">
                                    ${vuln.urls.map(url => `<li class="mb-1 break-all">${url}</li>`).join('')}
                                </ul>
                            </div>` : ''}
                            ${vuln.cwe_id ? `
                            <div class="mt-2">
                                <span class="text-xs text-gray-500">CWE ID</span>
                                <div class="text-xs text-gray-700">${vuln.cwe_id}</div>
                            </div>` : ''}
                            ${vuln.cves && vuln.cves.length > 0 ? `
                            <div class="mt-3">
                                <h6 class="text-xs text-gray-500 mb-1">CVE IDs</h6>
                                <div class="flex flex-wrap gap-1">
                                    ${vuln.cves.map(cve => `<span class="inline-block px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">${cve}</span>`).join('')}
                                </div>
                            </div>` : ''}
                        </div>
                        <div>
                            <h6 class="font-semibold mb-2">Recommendations</h6>
                            <ul class="list-disc pl-5 text-sm text-gray-700">
                                ${vuln.recommendation ? vuln.recommendation.map(rec => `<li>${rec}</li>`).join('') : 
                                  vuln.solution ? `<li>${vuln.solution}</li>` : 
                                  '<li>No specific recommendations available</li>'}
                            </ul>
                            ${vuln.reference ? `
                            <div class="mt-3">
                                <h6 class="text-xs text-gray-500 mb-1">References</h6>
                                <div class="text-xs text-gray-700 break-all">${formatReferences(vuln.reference)}</div>
                            </div>` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Helper function to format Nmap description for better readability
    function formatNmapDescription(description) {
        if (!description) return 'No description available';
        
        // Special handling for vulners scanner output
        if (description.includes('vulners')) {
            // Extract CVE IDs and their scores
            const cveMatches = description.match(/CVE-\d{4}-\d{4,}(?:\s+\d+\.\d+)?/g) || [];
            
            // Extract affected software/services
            let affectedSoftware = '';
            const serviceMatch = description.match(/Service:\s*([^\n]+)/);
            if (serviceMatch) {
                affectedSoftware = serviceMatch[1].trim();
            }
            
            // Create a user-friendly summary
            let summary = '<div class="mb-4">';
            
            // Add affected software/service info
            if (affectedSoftware) {
                summary += `<div class="mb-2"><span class="font-semibold">Affected Service:</span> ${affectedSoftware}</div>`;
            }
            
            // Add vulnerability summary
            summary += `<div class="mb-2"><span class="font-semibold">Summary:</span> This scan detected ${cveMatches.length} potential vulnerabilities in the target system.</div>`;
            
            // Add CVE details in a more structured format
            if (cveMatches.length > 0) {
                summary += '<div class="mb-2"><span class="font-semibold">Detected Vulnerabilities:</span></div>';
                summary += '<div class="grid gap-2 mb-4">';
                
                // Process each CVE
                const processedCVEs = new Set(); // To avoid duplicates
                cveMatches.forEach(cveMatch => {
                    const cveParts = cveMatch.split(/\s+/);
                    const cveId = cveParts[0];
                    const cveScore = cveParts[1] || 'N/A';
                    
                    // Skip if we've already processed this CVE
                    if (processedCVEs.has(cveId)) return;
                    processedCVEs.add(cveId);
                    
                    // Determine severity class based on score
                    let severityClass = 'bg-green-100 text-green-800';
                    let severityText = 'Low';
                    
                    if (cveScore >= 9) {
                        severityClass = 'bg-red-100 text-red-800';
                        severityText = 'Critical';
                    } else if (cveScore >= 7) {
                        severityClass = 'bg-orange-100 text-orange-800';
                        severityText = 'High';
                    } else if (cveScore >= 4) {
                        severityClass = 'bg-yellow-100 text-yellow-800';
                        severityText = 'Medium';
                    }
                    
                    // Create a card for each CVE
                    summary += `
                        <div class="border rounded p-2 bg-gray-50">
                            <div class="flex justify-between items-center mb-1">
                                <span class="font-medium">${cveId}</span>
                                <span class="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${severityClass}">
                                    ${severityText} ${cveScore !== 'N/A' ? '(' + cveScore + ')' : ''}
                                </span>
                            </div>
                            <div class="text-xs text-gray-600">
                                <a href="https://nvd.nist.gov/vuln/detail/${cveId}" target="_blank" class="text-blue-600 hover:underline">
                                    View details on National Vulnerability Database
                                </a>
                            </div>
                        </div>
                    `;
                });
                
                summary += '</div>';
            }
            
            // Add explanation about what this means
            summary += `
                <div class="mt-4 p-3 bg-blue-50 rounded text-sm">
                    <p class="font-semibold mb-1">What does this mean?</p>
                    <p>These are potential security vulnerabilities that might affect your system. Each vulnerability (CVE) has a score indicating its severity, with higher scores representing greater risk.</p>
                    <p class="mt-2">You should consider patching or updating the affected services to address these vulnerabilities.</p>
                </div>
            `;
            
            summary += '</div>';
            
            // Add a collapsible section with the raw technical details for advanced users
            summary += `
                <details class="mt-4 border rounded">
                    <summary class="p-2 bg-gray-100 cursor-pointer font-medium">Technical Details (for advanced users)</summary>
                    <div class="p-3 text-xs font-mono whitespace-pre-wrap overflow-auto max-h-60 bg-gray-50">
                        ${description.replace(/</g, '&lt;').replace(/>/g, '&gt;')}
                    </div>
                </details>
            `;
            
            return summary;
        } 
        // For non-vulners output, create a more readable format
        else {
            // Replace URLs with clickable links
            const urlRegex = /(https?:\/\/[^\s]+)/g;
            let formatted = description.replace(urlRegex, '<a href="$1" target="_blank" class="text-blue-600 hover:underline">$1</a>');
            
            // Extract key information
            const portMatch = formatted.match(/Port\s+(\d+)/i);
            const serviceMatch = formatted.match(/Service:\s*([^\n]+)/i);
            const versionMatch = formatted.match(/Version:\s*([^\n]+)/i);
            
            // Create a user-friendly summary
            let summary = '<div class="mb-4">';
            
            if (portMatch || serviceMatch || versionMatch) {
                summary += '<div class="mb-2 font-semibold">Detected Information:</div>';
                summary += '<ul class="list-disc pl-5 mb-4">';
                
                if (portMatch) {
                    summary += `<li>Port: ${portMatch[1]}</li>`;
                }
                
                if (serviceMatch) {
                    summary += `<li>Service: ${serviceMatch[1].trim()}</li>`;
                }
                
                if (versionMatch) {
                    summary += `<li>Version: ${versionMatch[1].trim()}</li>`;
                }
                
                summary += '</ul>';
            }
            
            // Add a simple explanation
            summary += `
                <div class="p-3 bg-blue-50 rounded text-sm">
                    <p>This scan detected information about your system that could potentially be used by attackers. While not necessarily vulnerabilities, exposed services and version information can help attackers identify potential weak points.</p>
                </div>
            `;
            
            summary += '</div>';
            
            // Add a collapsible section with the raw technical details
            summary += `
                <details class="mt-4 border rounded">
                    <summary class="p-2 bg-gray-100 cursor-pointer font-medium">Technical Details (for advanced users)</summary>
                    <div class="p-3 text-xs font-mono whitespace-pre-wrap overflow-auto max-h-60 bg-gray-50">
                        ${formatted}
                    </div>
                </details>
            `;
            
            return summary;
        }
    }
    
    // Helper function to format ZAP description for better readability
    function formatZapDescription(vuln) {
        if (!vuln) return 'No description available';
        
        // Special handling for incomplete scans
        if (vuln.name === 'Scan Incomplete' || vuln.scan_status === 'incomplete') {
            let html = `
                <div class="p-4 bg-blue-50 rounded-lg mb-4">
                    <div class="flex items-start">
                        <div class="flex-shrink-0">
                            <svg class="h-5 w-5 text-blue-600" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
                            </svg>
                        </div>
                        <div class="ml-3">
                            <h3 class="text-sm font-medium text-blue-800">ZAP Scan Information</h3>
                            <div class="mt-2 text-sm text-blue-700">
                                <p>${vuln.description}</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="mb-4">
                    <h4 class="font-medium text-gray-800 mb-2">Why did this happen?</h4>
                    <p class="text-sm text-gray-700">
                        ZAP scans can be incomplete for several reasons:
                    </p>
                    <ul class="list-disc pl-5 mt-2 text-sm text-gray-700 space-y-1">
                        <li>The scan exceeded the maximum allowed time</li>
                        <li>The target website is very large or complex</li>
                        <li>Connection issues occurred during the scan</li>
                        <li>The target website has rate limiting or protection mechanisms</li>
                    </ul>
                </div>
                
                <div class="mb-4">
                    <h4 class="font-medium text-gray-800 mb-2">Recommended Actions</h4>
                    <ul class="list-disc pl-5 text-sm text-gray-700 space-y-1">
                        ${vuln.recommendations ? 
                            vuln.recommendations.map(rec => `<li>${rec}</li>`).join('') : 
                            `<li>Focus on scanning specific critical paths rather than the entire website</li>
                             <li>Increase the scan timeout in the settings</li>
                             <li>Verify the target is accessible before scanning</li>`
                        }
                    </ul>
                </div>
            `;
            
            return html;
        }
        
        // Standard ZAP vulnerability formatting
        let formatted = vuln.description || 'No description available';
        
        // Add solution if available
        if (vuln.solution) {
            formatted += `
                <div class="mt-4">
                    <h4 class="font-medium text-gray-800 mb-2">Solution</h4>
                    <p class="text-sm text-gray-700">${vuln.solution}</p>
                </div>
            `;
        }
        
        // Add references if available
        if (vuln.reference) {
            formatted += `
                <div class="mt-4">
                    <h4 class="font-medium text-gray-800 mb-2">References</h4>
                    <p class="text-sm text-gray-700">${formatReferences(vuln.reference)}</p>
                </div>
            `;
        }
        
        return formatted;
    }
    
    // Helper function to format references as clickable links
    function formatReferences(reference) {
        if (!reference) return '';
        
        // Check if it's a URL
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        if (urlRegex.test(reference)) {
            // Split multiple URLs by commas or spaces
            const urls = reference.split(/[,\s]+/).filter(url => urlRegex.test(url));
            
            if (urls.length > 0) {
                return urls.map(url => 
                    `<a href="${url}" target="_blank" class="text-blue-600 hover:underline">${url}</a>`
                ).join('<br>');
            }
        }
        
        return reference;
    }
    
    // Helper function to get color based on score
    function getScoreColor(score) {
        if (score >= 9) return '#ef4444'; // red-500
        if (score >= 7) return '#f97316'; // orange-500
        if (score >= 4) return '#eab308'; // yellow-500
        return '#22c55e'; // green-500
    }
    
    // Initialize
    showSection(homeSection);
});
