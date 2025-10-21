// Cogniware Core - Enhanced Admin Portal JavaScript

const API_BASE = 'http://localhost:8099';
let currentToken = null;
let currentUser = null;
let allOrganizations = [];

// Login
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, password})
        });

        const data = await response.json();

        if (data.success) {
            currentToken = data.token;
            currentUser = data.user;
            document.getElementById('loginBox').style.display = 'none';
            document.getElementById('dashboard').style.display = 'block';
            document.getElementById('currentUser').textContent = currentUser.full_name;
            document.getElementById('currentRole').textContent = currentUser.role;
            loadDashboard();
        } else {
            showLoginError('Invalid credentials');
        }
    } catch (error) {
        showLoginError('Connection error: ' + error.message);
    }
});

function showLoginError(message) {
    const alert = document.getElementById('loginAlert');
    alert.textContent = message;
    alert.style.display = 'block';
}

function logout() {
    currentToken = null;
    currentUser = null;
    document.getElementById('dashboard').style.display = 'none';
    document.getElementById('loginBox').style.display = 'block';
    document.getElementById('password').value = '';
}

async function apiCall(endpoint, method = 'GET', body = null) {
    const options = {
        method,
        headers: {
            'Authorization': `Bearer ${currentToken}`,
            'Content-Type': 'application/json'
        }
    };

    if (body) {
        options.body = JSON.stringify(body);
    }

    const response = await fetch(`${API_BASE}${endpoint}`, options);
    return await response.json();
}

async function loadDashboard() {
    loadOrganizations();
    loadLicenses();
    loadUsers();
    updateStats();
}

async function updateStats() {
    try {
        const orgs = await apiCall('/admin/organizations');
        const licenses = await apiCall('/admin/licenses');
        const users = await apiCall('/admin/users');
        
        document.getElementById('statOrgs').textContent = orgs.count || 0;
        document.getElementById('statLicenses').textContent = licenses.count || 0;
        document.getElementById('statUsers').textContent = users.count || 0;
    } catch (error) {
        console.error('Error updating stats:', error);
    }
}

async function loadOrganizations() {
    try {
        const data = await apiCall('/admin/organizations');
        const container = document.getElementById('orgsList');
        allOrganizations = data.organizations || [];
        
        if (allOrganizations.length > 0) {
            let html = '<table><thead><tr><th>ID</th><th>Name</th><th>Type</th><th>Contact</th><th>Created</th><th>Status</th></tr></thead><tbody>';
            allOrganizations.forEach(org => {
                const createdDate = org.created_at ? new Date(org.created_at).toLocaleDateString() : 'N/A';
                html += `<tr>
                    <td><code style="font-size: 0.85em;">${org.org_id}</code></td>
                    <td><strong>${org.org_name}</strong></td>
                    <td>${org.org_type}</td>
                    <td>${org.contact_email}</td>
                    <td>${createdDate}</td>
                    <td><span class="badge ${org.status}">${org.status}</span></td>
                </tr>`;
            });
            html += '</tbody></table>';
            container.innerHTML = html;
        } else {
            container.innerHTML = '<p style="color: #999;">No organizations found. Create your first organization!</p>';
        }
    } catch (error) {
        document.getElementById('orgsList').innerHTML = '<p style="color: #c33;">Error loading organizations</p>';
    }
}

async function loadLicenses() {
    try {
        const data = await apiCall('/admin/licenses');
        const container = document.getElementById('licensesList');
        
        if (data.licenses && data.licenses.length > 0) {
            let html = '<table><thead><tr><th>License Key</th><th>Organization</th><th>Type</th><th>Expiry</th><th>Status</th><th>Actions</th></tr></thead><tbody>';
            data.licenses.forEach(lic => {
                const expiryDate = new Date(lic.expiry_date).toLocaleDateString();
                html += `<tr>
                    <td><code style="font-size: 0.75em;">${lic.license_key}</code></td>
                    <td><code>${lic.org_id}</code></td>
                    <td><span class="badge active">${lic.license_type}</span></td>
                    <td>${expiryDate}</td>
                    <td><span class="badge ${lic.status}">${lic.status}</span></td>
                    <td>
                        ${lic.status === 'active' ? `<button class="btn-small btn-danger" onclick="revokeLicense('${lic.license_key}')">Revoke</button>` : ''}
                    </td>
                </tr>`;
            });
            html += '</tbody></table>';
            container.innerHTML = html;
        } else {
            container.innerHTML = '<p style="color: #999;">No licenses found. Create a license for an organization!</p>';
        }
    } catch (error) {
        document.getElementById('licensesList').innerHTML = '<p style="color: #c33;">Error loading licenses</p>';
    }
}

async function loadUsers() {
    try {
        const data = await apiCall('/admin/users');
        const container = document.getElementById('usersList');
        
        if (data.users && data.users.length > 0) {
            let html = '<table><thead><tr><th>ID</th><th>Username</th><th>Email</th><th>Full Name</th><th>Role</th><th>Organization</th><th>Status</th><th>Actions</th></tr></thead><tbody>';
            data.users.forEach(user => {
                html += `<tr>
                    <td><code style="font-size: 0.75em;">${user.user_id}</code></td>
                    <td><strong>${user.username}</strong></td>
                    <td>${user.email}</td>
                    <td>${user.full_name}</td>
                    <td><span class="badge ${user.role}">${user.role}</span></td>
                    <td><code style="font-size: 0.75em;">${user.org_id}</code></td>
                    <td><span class="badge ${user.status}">${user.status}</span></td>
                    <td>
                        <button class="btn-small" style="background: #ff9800; font-size: 11px; padding: 6px 10px;" onclick="changeUserPassword('${user.user_id}', '${user.username}')">🔑 Password</button>
                        ${user.status === 'active' ? 
                            `<button class="btn-small" style="background: #f44336; font-size: 11px; padding: 6px 10px;" onclick="updateUserStatus('${user.user_id}', 'inactive')">❌ Deactivate</button>` : 
                            `<button class="btn-small" style="background: #4caf50; font-size: 11px; padding: 6px 10px;" onclick="updateUserStatus('${user.user_id}', 'active')">✅ Activate</button>`
                        }
                    </td>
                </tr>`;
            });
            html += '</tbody></table>';
            container.innerHTML = html;
        } else {
            container.innerHTML = '<p style="color: #999;">No users found</p>';
        }
    } catch (error) {
        document.getElementById('usersList').innerHTML = '<p style="color: #c33;">Error loading users</p>';
    }
}

async function changeUserPassword(userId, username) {
    const newPassword = prompt(`🔑 Change Password for: ${username}\n\nEnter new password (minimum 8 characters):`);
    
    if (newPassword && newPassword.length >= 8) {
        try {
            const result = await apiCall(`/admin/users/${userId}/password`, 'POST', {
                new_password: newPassword
            });
            
            if (result.success) {
                alert(`✅ Password Changed Successfully!\n\nUsername: ${username}\nNew Password: ${newPassword}\n\n⚠️ Please save this password securely and share with the user.`);
            } else {
                alert(`❌ Error: ${result.error || 'Failed to change password'}`);
            }
        } catch (error) {
            alert(`❌ Error: ${error.message}`);
        }
    } else if (newPassword !== null) {
        alert('❌ Password must be at least 8 characters');
    }
}

async function updateUserStatus(userId, newStatus) {
    const action = newStatus === 'active' ? 'activate' : 'deactivate';
    
    if (confirm(`⚠️ Are you sure you want to ${action} this user?\n\n${newStatus === 'inactive' ? 'The user will immediately lose access to the platform.' : 'The user will regain access to the platform.'}`)) {
        try {
            const result = await apiCall(`/admin/users/${userId}/status`, 'POST', {
                status: newStatus
            });
            
            if (result.success) {
                alert(`✅ User ${action}d successfully!`);
                loadUsers(); // Reload users list
            } else {
                alert(`❌ Error: ${result.error || 'Failed to update status'}`);
            }
        } catch (error) {
            alert(`❌ Error: ${error.message}`);
        }
    }
}

async function loadAuditLog() {
    try {
        const data = await apiCall('/admin/audit?limit=50');
        const container = document.getElementById('auditLog');
        
        if (data.logs && data.logs.length > 0) {
            let html = '<table><thead><tr><th>Time</th><th>User</th><th>Action</th><th>Resource</th><th>IP</th></tr></thead><tbody>';
            data.logs.forEach(log => {
                html += `<tr>
                    <td>${new Date(log.timestamp).toLocaleString()}</td>
                    <td><code style="font-size: 0.75em;">${log.user_id || 'System'}</code></td>
                    <td><span class="badge active">${log.action}</span></td>
                    <td>${log.resource}</td>
                    <td>${log.ip_address || 'N/A'}</td>
                </tr>`;
            });
            html += '</tbody></table>';
            container.innerHTML = html;
        } else {
            container.innerHTML = '<p style="color: #999;">No audit logs found</p>';
        }
    } catch (error) {
        document.getElementById('auditLog').innerHTML = '<p style="color: #c33;">Error loading audit log</p>';
    }
}

function showTab(tabName) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.content-card').forEach(c => c.classList.remove('active'));
    
    event.target.classList.add('active');
    document.getElementById(`tab-${tabName}`).classList.add('active');
    
    // Load data for tab
    if (tabName === 'organizations') loadOrganizations();
    else if (tabName === 'licenses') loadLicenses();
    else if (tabName === 'users') loadUsers();
    else if (tabName === 'llms') loadLLMModels();
    else if (tabName === 'audit') loadAuditLog();
    else if (tabName === 'use-cases') loadUseCasesOverview();
}

// Modal functions
function showModal(type) {
    const modal = document.getElementById('modal');
    const modalBody = document.getElementById('modalBody');
    const modalTitle = document.getElementById('modalTitle');
    
    if (type === 'createOrg') {
        modalTitle.textContent = 'Create Organization';
        modalBody.innerHTML = `
            <div class="form-group">
                <label>Organization Name *</label>
                <input type="text" id="newOrgName" placeholder="Acme Corporation">
            </div>
            <div class="form-group">
                <label>Type</label>
                <select id="newOrgType">
                    <option value="customer">Customer</option>
                    <option value="partner">Partner</option>
                    <option value="reseller">Reseller</option>
                </select>
            </div>
            <div class="form-group">
                <label>Contact Email *</label>
                <input type="email" id="newOrgEmail" placeholder="admin@acme.com">
            </div>
            <div class="form-group">
                <label>Phone</label>
                <input type="tel" id="newOrgPhone" placeholder="+1-555-1234">
            </div>
            <div class="form-group">
                <label>Address</label>
                <textarea id="newOrgAddress" rows="3" placeholder="123 Main St, City, State, ZIP"></textarea>
            </div>
            <button class="btn" onclick="createOrganization()">Create Organization</button>
        `;
    } else if (type === 'createLicense') {
        modalTitle.textContent = 'Create License';
        let orgOptions = '<option value="">Select Organization</option>';
        allOrganizations.forEach(org => {
            orgOptions += `<option value="${org.org_id}">${org.org_name}</option>`;
        });
        
        modalBody.innerHTML = `
            <div class="form-group">
                <label>Organization *</label>
                <select id="newLicenseOrg">${orgOptions}</select>
            </div>
            <div class="form-group">
                <label>License Type</label>
                <select id="newLicenseType">
                    <option value="basic">Basic ($99/month)</option>
                    <option value="professional">Professional ($299/month)</option>
                    <option value="enterprise">Enterprise ($999/month)</option>
                </select>
            </div>
            <div class="form-group">
                <label>Features</label>
                <div>
                    <label><input type="checkbox" value="database" checked> Database Q&A</label><br>
                    <label><input type="checkbox" value="code_generation" checked> Code Generation</label><br>
                    <label><input type="checkbox" value="documents" checked> Document Processing</label><br>
                    <label><input type="checkbox" value="integration" checked> Data Integration</label><br>
                    <label><input type="checkbox" value="workflow" checked> Workflow Automation</label><br>
                    <label><input type="checkbox" value="browser_automation" checked> Browser Automation</label><br>
                    <label><input type="checkbox" value="rpa" checked> RPA Workflows</label>
                </div>
            </div>
            <div class="form-group">
                <label>Max Users</label>
                <input type="number" id="newLicenseUsers" value="10">
            </div>
            <div class="form-group">
                <label>Max API Calls/Month</label>
                <input type="number" id="newLicenseAPICalls" value="1000000">
            </div>
            <div class="form-group">
                <label>Validity (Days)</label>
                <input type="number" id="newLicenseDays" value="365">
            </div>
            <button class="btn" onclick="createLicense()">Create License</button>
        `;
    } else if (type === 'createUser') {
        modalTitle.textContent = 'Create User';
        let orgOptions = '<option value="">Select Organization</option>';
        allOrganizations.forEach(org => {
            orgOptions += `<option value="${org.org_id}">${org.org_name}</option>`;
        });
        
        modalBody.innerHTML = `
            <div class="form-group">
                <label>Organization *</label>
                <select id="newUserOrg">${orgOptions}</select>
            </div>
            <div class="form-group">
                <label>Username *</label>
                <input type="text" id="newUsername" placeholder="john.doe">
            </div>
            <div class="form-group">
                <label>Email *</label>
                <input type="email" id="newUserEmail" placeholder="john.doe@company.com">
            </div>
            <div class="form-group">
                <label>Full Name *</label>
                <input type="text" id="newUserFullName" placeholder="John Doe">
            </div>
            <div class="form-group">
                <label>Password *</label>
                <input type="password" id="newUserPassword" placeholder="Minimum 8 characters">
            </div>
            <div class="form-group">
                <label>Role</label>
                <select id="newUserRole">
                    <option value="user">User</option>
                    <option value="admin">Admin</option>
                </select>
            </div>
            <button class="btn" onclick="createUser()">Create User</button>
        `;
    }
    
    modal.style.display = 'block';
}

function closeModal() {
    document.getElementById('modal').style.display = 'none';
}

async function createOrganization() {
    const data = {
        org_name: document.getElementById('newOrgName').value,
        org_type: document.getElementById('newOrgType').value,
        contact_email: document.getElementById('newOrgEmail').value,
        contact_phone: document.getElementById('newOrgPhone').value,
        address: document.getElementById('newOrgAddress').value
    };

    const result = await apiCall('/admin/organizations', 'POST', data);
    if (result.success) {
        alert(`✅ Organization Created!\n\nOrg ID: ${result.org_id}\nName: ${result.org_name}`);
        closeModal();
        loadOrganizations();
        updateStats();
    } else {
        alert('❌ Error: ' + (result.error || JSON.stringify(result)));
    }
}

async function createLicense() {
    const features = [];
    document.querySelectorAll('#modalBody input[type="checkbox"]:checked').forEach(cb => {
        features.push(cb.value);
    });

    const data = {
        org_id: document.getElementById('newLicenseOrg').value,
        license_type: document.getElementById('newLicenseType').value,
        features: features,
        max_users: parseInt(document.getElementById('newLicenseUsers').value),
        max_api_calls: parseInt(document.getElementById('newLicenseAPICalls').value),
        days_valid: parseInt(document.getElementById('newLicenseDays').value)
    };

    const result = await apiCall('/admin/licenses', 'POST', data);
    if (result.success) {
        alert(`✅ License Created!\n\n📋 License Key:\n${result.license_key}\n\n⚠️ Save this key! It won't be shown again.\n\nExpires: ${new Date(result.expiry_date).toLocaleDateString()}`);
        closeModal();
        loadLicenses();
        updateStats();
    } else {
        alert('❌ Error: ' + (result.error || JSON.stringify(result)));
    }
}

async function createUser() {
    const data = {
        org_id: document.getElementById('newUserOrg').value,
        username: document.getElementById('newUsername').value,
        email: document.getElementById('newUserEmail').value,
        full_name: document.getElementById('newUserFullName').value,
        password: document.getElementById('newUserPassword').value,
        role: document.getElementById('newUserRole').value
    };

    const result = await apiCall('/admin/users', 'POST', data);
    if (result.success) {
        alert(`✅ User Created!\n\nUser ID: ${result.user_id}\nUsername: ${result.username}\n\nThe user can now login and create API keys.`);
        closeModal();
        loadUsers();
        updateStats();
    } else {
        alert('❌ Error: ' + (result.error || JSON.stringify(result)));
    }
}

async function revokeLicense(key) {
    if (confirm(`⚠️ Revoke license ${key}?\n\nThis will immediately disable access for all users with this license.`)) {
        const result = await apiCall(`/admin/licenses/${key}/revoke`, 'POST');
        if (result.success) {
            alert('✅ License revoked successfully!');
            loadLicenses();
        } else {
            alert('❌ Error revoking license');
        }
    }
}

// Use Cases Display
function showUseCases(category) {
    showTab('use-cases');
    loadUseCasesDetail(category);
}

function loadUseCasesOverview() {
    const container = document.getElementById('useCasesContent');
    container.innerHTML = `
        <h3 style="margin: 30px 0 20px 0;">Click on a module above to see specific use cases</h3>
        <p style="color: #666; margin-bottom: 30px;">Each module has proven business use cases with ROI calculations</p>
    `;
}

function loadUseCasesDetail(category) {
    const container = document.getElementById('useCasesContent');
    
    const useCases = getUseCasesForCategory(category);
    
    let html = '<div style="margin-top: 30px;">';
    useCases.forEach((useCase, index) => {
        html += `
            <div class="use-case-card">
                <h4>📌 ${useCase.title}</h4>
                <p><strong>Scenario:</strong> ${useCase.scenario}</p>
                <p><strong>Business Value:</strong> <span class="value">${useCase.value}</span></p>
                <p><strong>ROI:</strong> ${useCase.roi}</p>
                ${useCase.example ? `<div class="code-block">${useCase.example}</div>` : ''}
            </div>
        `;
    });
    html += '</div>';
    
    container.innerHTML = html;
}

function getUseCasesForCategory(category) {
    const useCasesData = {
        'database': [
            {
                title: 'Customer Analytics Dashboard',
                scenario: 'Analyze customer data without writing SQL queries',
                value: '87% time savings, $50K/year per analyst',
                roi: 'Immediate - No SQL knowledge required',
                example: 'Ask: "Show me customers who spent over $1000 last month"'
            },
            {
                title: 'Real-Time Business Intelligence',
                scenario: 'Track KPIs and metrics in natural language',
                value: 'Faster decision making, 10x query speed',
                roi: '500% ROI in first year'
            },
            {
                title: 'Compliance Reporting',
                scenario: 'Generate compliance reports automatically',
                value: 'Reduce audit prep from weeks to hours',
                roi: '$100K+ savings annually'
            }
        ],
        'codegen': [
            {
                title: 'Rapid API Development',
                scenario: 'Generate complete REST APIs in minutes',
                value: '95% faster development, consistent quality',
                roi: '$200K/year in dev cost savings',
                example: 'Generate: Web API, CLI Tool, Microservice in seconds'
            },
            {
                title: 'Microservices Generation',
                scenario: 'Create distributed system components automatically',
                value: 'Reduce development time from 4 weeks to 3 days',
                roi: '15x productivity increase'
            },
            {
                title: 'Function Library Creation',
                scenario: 'Build reusable function libraries',
                value: 'Consistent code quality, reduced bugs',
                roi: '50% reduction in maintenance costs'
            }
        ],
        'documents': [
            {
                title: 'Contract Analysis',
                scenario: 'Search and analyze legal contracts',
                value: 'Faster contract review, instant clause finding',
                roi: '80% time savings in legal review',
                example: 'Search: "liability clause" across 1000s of contracts instantly'
            },
            {
                title: 'Knowledge Base Management',
                scenario: 'Build searchable corporate knowledge base',
                value: 'Find information 10x faster',
                roi: '40 hours/month saved per employee'
            },
            {
                title: 'Compliance Documentation',
                scenario: 'Organize and search compliance documents',
                value: 'Instant compliance verification',
                roi: 'Reduce audit time by 90%'
            }
        ],
        'integration': [
            {
                title: 'Multi-Source Data Aggregation',
                scenario: 'Combine data from multiple APIs into unified database',
                value: 'Unified data view, automated pipelines',
                roi: '90% reduction in manual data entry',
                example: 'Import from 10 APIs → Transform → Export to dashboard'
            },
            {
                title: 'Real-Time Synchronization',
                scenario: 'Keep databases synchronized across systems',
                value: 'Always up-to-date data',
                roi: 'Eliminate data inconsistencies'
            },
            {
                title: 'Legacy System Integration',
                scenario: 'Connect modern and legacy systems',
                value: 'Extend legacy system lifespan',
                roi: 'Avoid $500K+ system replacement'
            }
        ],
        'workflow': [
            {
                title: 'Automated Report Generation',
                scenario: 'Daily automated business reports',
                value: '95% time savings, consistent schedules',
                roi: '20 hours/week saved',
                example: 'Fetch data → Generate report → Email → Archive (fully automated)'
            },
            {
                title: 'Customer Onboarding Automation',
                scenario: 'Automate new customer setup',
                value: 'Reduce onboarding from 3 days to 30 minutes',
                roi: '90% faster customer activation'
            },
            {
                title: 'Multi-System Orchestration',
                scenario: 'Coordinate actions across multiple systems',
                value: 'Complex business processes automated',
                roi: '$150K/year in operational savings'
            }
        ],
        'rpa': [
            {
                title: 'Competitive Price Monitoring',
                scenario: 'Automatically track competitor prices with screenshots',
                value: '100% automated, real-time intelligence',
                roi: '15% revenue increase from dynamic pricing',
                example: 'Navigate → Screenshot → Extract prices → Store → Alert on changes'
            },
            {
                title: 'Automated Form Filling',
                scenario: 'Auto-fill repetitive web forms',
                value: '100% elimination of manual data entry',
                roi: '$75K/year per employee saved'
            },
            {
                title: 'Web Data Scraping',
                scenario: 'Extract structured data from websites',
                value: 'Automated market research and lead generation',
                roi: 'Collect 1000s of leads automatically'
            },
            {
                title: 'E-Commerce Testing',
                scenario: 'Automated checkout flow testing',
                value: 'Continuous quality assurance',
                roi: 'Catch bugs before customers do'
            },
            {
                title: 'Social Media Monitoring',
                scenario: 'Monitor brand mentions and sentiment',
                value: 'Real-time brand awareness',
                roi: 'Respond to issues 10x faster'
            },
            {
                title: 'Invoice Processing',
                scenario: 'Automated invoice data extraction',
                value: 'Eliminate manual data entry',
                roi: '95% reduction in processing time'
            }
        ]
    };
    
    return useCasesData[category] || [];
}

// Initialize
if (localStorage.getItem('cogniware_token')) {
    // Auto-login if token exists
    currentToken = localStorage.getItem('cogniware_token');
    // Verify token and load dashboard
}

