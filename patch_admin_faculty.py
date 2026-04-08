import os

admin_path = r'c:\Users\mamta\OneDrive\Desktop\satisfypulse\frontend\admin.html'
faculty_path = r'c:\Users\mamta\OneDrive\Desktop\satisfypulse\frontend\faculty.html'

with open(admin_path, 'r', encoding='utf-8') as f:
    admin_content = f.read()

# 1. Add Faculty Performance Tab button
tab_btn_old = """<button class="tab-btn" onclick="showTab('analytics')"><i class="fas fa-chart-pie"></i> Analytics</button>"""
tab_btn_new = """<button class="tab-btn" onclick="showTab('analytics')"><i class="fas fa-chart-pie"></i> Analytics</button>
            <button class="tab-btn" onclick="showTab('performance')"><i class="fas fa-star-half-alt"></i> Faculty Performance</button>"""

if "Faculty Performance</button>" not in admin_content:
    admin_content = admin_content.replace(tab_btn_old, tab_btn_new)

# 2. Add the Performance Tab Content
tab_content_old = """        <div id="analyticsTab" class="tab-content">"""
tab_content_new = """        <div id="performanceTab" class="tab-content">
            <div class="card">
                <h3><i class="fas fa-star-half-alt"></i> Faculty Performance & Alerts</h3>
                <p>Institute Average Rating: <span id="globalAverage" style="font-weight:bold; color:var(--primary-color);">0</span> / 5</p>
                <div class="table-container">
                    <table>
                        <thead><tr><th>Name</th><th>Department</th><th>Avg Rating</th><th>Feedback Count</th><th>Status</th><th>Action</th></tr></thead>
                        <tbody id="performanceList"></tbody>
                    </table>
                </div>
            </div>
        </div>

        <div id="analyticsTab" class="tab-content">"""

if "id=\"performanceTab\"" not in admin_content:
    admin_content = admin_content.replace(tab_content_old, tab_content_new)

# 3. Add the JS for loading Performance
js_old = "if (tab === 'analytics') loadAnalytics();"
js_new = """if (tab === 'analytics') loadAnalytics();
            if (tab === 'performance') loadPerformance();"""

if "loadPerformance();" not in admin_content:
    admin_content = admin_content.replace(js_old, js_new)

js_funcs = """async function loadPerformance() {
            const res = await fetch(`/api/admin/faculty-performance`, { credentials: 'include' });
            const data = await res.json();
            document.getElementById('globalAverage').textContent = data.global_average;
            const tbody = document.getElementById('performanceList');
            tbody.innerHTML = '';
            data.performances.forEach(perf => {
                const row = tbody.insertRow();
                row.insertCell(0).textContent = perf.name;
                row.insertCell(1).textContent = perf.department;
                row.insertCell(2).innerHTML = `<strong>${parseFloat(perf.avg_rating).toFixed(1)}</strong>`;
                row.insertCell(3).textContent = perf.feedback_count;
                
                const isBelowAvg = parseFloat(perf.avg_rating) < parseFloat(data.global_average) && perf.feedback_count > 0;
                row.insertCell(4).innerHTML = isBelowAvg 
                    ? '<span style="color:red; font-weight:bold;"><i class="fas fa-exclamation-circle"></i> Below Avg</span>' 
                    : '<span style="color:green;"><i class="fas fa-check-circle"></i> Good</span>';
                
                const btnCell = row.insertCell(5);
                if (isBelowAvg) {
                    btnCell.innerHTML = `<button onclick="sendAlert('${perf.name}')" style="background:#dc3545; color:white; border:none; padding:5px 10px; border-radius:5px; cursor:pointer;"><i class="fas fa-bell"></i> Send Alert</button>`;
                } else {
                    btnCell.textContent = '-';
                }
            });
        }

        async function sendAlert(facultyName) {
            if (confirm(`Send improvement alert to ${facultyName}?`)) {
                await fetch(`/api/admin/send-alert`, {
                    method: 'POST', credentials: 'include',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ faculty_name: facultyName })
                });
                alert('Alert sent successfully!');
            }
        }
"""
if "async function loadPerformance" not in admin_content:
    admin_content = admin_content.replace("function showTab(tab) {", js_funcs + "\n        function showTab(tab) {")

with open(admin_path, 'w', encoding='utf-8', newline='') as f:
    f.write(admin_content)

# Update Faculty HTML
with open(faculty_path, 'r', encoding='utf-8') as f:
    faculty_content = f.read()

fac_tab_btn_old = """<button class="tab-btn" onclick="showTab('analytics')"><i class="fas fa-chart-pie"></i> Analytics</button>"""
fac_tab_btn_new = """<button class="tab-btn" onclick="showTab('analytics')"><i class="fas fa-chart-pie"></i> Analytics</button>
            <button class="tab-btn" onclick="showTab('alerts')"><i class="fas fa-bell"></i> Alerts</button>"""

if "showTab('alerts')" not in faculty_content:
    faculty_content = faculty_content.replace(fac_tab_btn_old, fac_tab_btn_new)

fac_content_old = """        <div id="analyticsTab" class="tab-content">"""
fac_content_new = """        <div id="alertsTab" class="tab-content">
            <div class="card">
                <h3><i class="fas fa-bell"></i> Admin Alerts</h3>
                <div id="alertsContainer"></div>
            </div>
        </div>

        <div id="analyticsTab" class="tab-content">"""

if "id=\"alertsTab\"" not in faculty_content:
    faculty_content = faculty_content.replace(fac_content_old, fac_content_new)

fac_js_old = "if (tab === 'analytics') loadAnalytics();"
fac_js_new = """if (tab === 'analytics') loadAnalytics();
            if (tab === 'alerts') loadAlerts();"""

if "loadAlerts();" not in faculty_content:
    faculty_content = faculty_content.replace(fac_js_old, fac_js_new)

fac_js_funcs = """async function loadAlerts() {
            const res = await fetch(`/api/faculty/alerts`, { credentials: 'include' });
            const alerts = await res.json();
            const container = document.getElementById('alertsContainer');
            if (alerts.length === 0) {
                container.innerHTML = '<p style="color:green; padding:10px;"><i class="fas fa-check-circle"></i> You have no alerts. Keep up the good work!</p>';
                return;
            }
            container.innerHTML = alerts.map(a => `
                <div style="background:#f8d7da; color:#721c24; padding:15px; border-radius:5px; margin-bottom:10px; border-left:4px solid #dc3545;">
                    <i class="fas fa-exclamation-triangle"></i> <strong>Alert from Admin:</strong> ${a.message}
                    <div style="font-size:12px; margin-top:5px; color:#555;">${new Date(a.created_at).toLocaleString()}</div>
                </div>
            `).join('');
        }
"""
if "async function loadAlerts" not in faculty_content:
    faculty_content = faculty_content.replace("function showTab(tab) {", fac_js_funcs + "\n        function showTab(tab) {")

with open(faculty_path, 'w', encoding='utf-8', newline='') as f:
    f.write(faculty_content)

print("Patched admin.html and faculty.html")
