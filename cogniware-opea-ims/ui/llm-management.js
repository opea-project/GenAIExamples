// LLM Management JavaScript - Updated for Cogniware Built-in LLMs

let availableOllamaModels = [];
let availableHuggingFaceModels = [];
let currentLLMTab = 'cogniware';

// Show LLM Tab (Cogniware or Import)
function showLLMTab(tab) {
    currentLLMTab = tab;
    
    const cogniwareTab = document.getElementById('cogniwareLLMsTab');
    const importTab = document.getElementById('importLLMsTab');
    const btnCogniware = document.getElementById('btnCogniwareLLMs');
    const btnImport = document.getElementById('btnImportLLMs');
    
    if (tab === 'cogniware') {
        cogniwareTab.style.display = 'block';
        importTab.style.display = 'none';
        btnCogniware.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
        btnImport.style.background = '#f0f0f0';
        btnImport.style.color = '#666';
        loadCogniwareLLMs();
    } else {
        cogniwareTab.style.display = 'none';
        importTab.style.display = 'block';
        btnCogniware.style.background = '#f0f0f0';
        btnCogniware.style.color = '#666';
        btnImport.style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
        btnImport.style.color = '#fff';
        loadImportedModels();
    }
}

// Load Cogniware Built-in LLMs
async function loadCogniwareLLMs() {
    try {
        const data = await apiCall('/admin/llm/cogniware/all');
        
        if (data.success) {
            // Update stats
            const summary = data.summary;
            document.getElementById('llmStats').innerHTML = `
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; padding: 20px; background: linear-gradient(135deg, #f5f7ff 0%, #faf5ff 100%); border-radius: 12px; border: 2px solid #667eea;">
                    <div style="text-align: center;">
                        <div style="font-size: 2.5em; font-weight: 700; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">${summary.total}</div>
                        <div style="color: #666; font-weight: 600;">Total Models</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 2.5em; font-weight: 700; color: #4caf50;">${summary.interface}</div>
                        <div style="color: #666; font-weight: 600;">Interface</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 2.5em; font-weight: 700; color: #2196f3;">${summary.knowledge}</div>
                        <div style="color: #666; font-weight: 600;">Knowledge</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 2.5em; font-weight: 700; color: #ff9800;">${summary.embedding}</div>
                        <div style="color: #666; font-weight: 600;">Embedding</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 2.5em; font-weight: 700; color: #9c27b0;">${summary.specialized}</div>
                        <div style="color: #666; font-weight: 600;">Specialized</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 2.5em; font-weight: 700; color: #2d862d;">${summary.total_size_gb.toFixed(1)}</div>
                        <div style="color: #666; font-weight: 600;">Total GB</div>
                    </div>
                </div>
            `;
            
            // Display models
            const container = document.getElementById('cogniwareLLMsList');
            
            if (data.llms && data.llms.length > 0) {
                // Group by type
                const interface_models = data.llms.filter(m => m.model_type === 'interface');
                const knowledge_models = data.llms.filter(m => m.model_type === 'knowledge');
                const embedding_models = data.llms.filter(m => m.model_type === 'embedding');
                const specialized_models = data.llms.filter(m => m.model_type === 'specialized');
                
                let html = '';
                
                // Interface Models
                if (interface_models.length > 0) {
                    html += '<h4 style="margin-top: 30px; color: #4caf50;">🗣️ Interface Models (Chat, Code, Translation)</h4>';
                    html += '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 20px; margin-top: 15px;">';
                    interface_models.forEach(model => {
                        html += createModelCard(model);
                    });
                    html += '</div>';
                }
                
                // Knowledge Models
                if (knowledge_models.length > 0) {
                    html += '<h4 style="margin-top: 30px; color: #2196f3;">📚 Knowledge Models (Q&A, RAG)</h4>';
                    html += '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 20px; margin-top: 15px;">';
                    knowledge_models.forEach(model => {
                        html += createModelCard(model);
                    });
                    html += '</div>';
                }
                
                // Embedding Models
                if (embedding_models.length > 0) {
                    html += '<h4 style="margin-top: 30px; color: #ff9800;">🔍 Embedding Models (Semantic Search)</h4>';
                    html += '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 20px; margin-top: 15px;">';
                    embedding_models.forEach(model => {
                        html += createModelCard(model);
                    });
                    html += '</div>';
                }
                
                // Specialized Models
                if (specialized_models.length > 0) {
                    html += '<h4 style="margin-top: 30px; color: #9c27b0;">🎯 Specialized Models (Sentiment, Classification)</h4>';
                    html += '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 20px; margin-top: 15px;">';
                    specialized_models.forEach(model => {
                        html += createModelCard(model);
                    });
                    html += '</div>';
                }
                
                container.innerHTML = html;
            } else {
                container.innerHTML = '<p style="color: #999;">No Cogniware models found.</p>';
            }
        }
    } catch (error) {
        console.error('Error loading Cogniware LLMs:', error);
        document.getElementById('cogniwareLLMsList').innerHTML = '<p style="color: #c33;">Error loading Cogniware models</p>';
    }
}

// Create Model Card
function createModelCard(model) {
    const typeColors = {
        'interface': '#4caf50',
        'knowledge': '#2196f3',
        'embedding': '#ff9800',
        'specialized': '#9c27b0'
    };
    
    const color = typeColors[model.model_type] || '#667eea';
    
    let capabilitiesHTML = '';
    if (model.capabilities && model.capabilities.length > 0) {
        capabilitiesHTML = model.capabilities.slice(0, 3).map(c => 
            `<span style="background: rgba(102, 126, 234, 0.1); color: #667eea; padding: 4px 8px; border-radius: 4px; font-size: 11px; margin-right: 5px;">${c}</span>`
        ).join('');
    }
    
    return `
        <div style="background: white; border: 2px solid ${color}; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: transform 0.2s;" onmouseover="this.style.transform='translateY(-4px)'" onmouseout="this.style.transform='translateY(0)'">
            <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
                <div>
                    <h4 style="margin: 0; color: ${color};">${model.model_name}</h4>
                    <p style="margin: 5px 0 0 0; font-size: 12px; color: #999;">${model.model_id}</p>
                </div>
                <span class="badge active" style="background: ${color};">✅ Ready</span>
            </div>
            
            <p style="color: #666; font-size: 13px; margin: 10px 0; line-height: 1.5;">${model.description}</p>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 15px 0; padding: 10px; background: #f9f9f9; border-radius: 8px;">
                <div>
                    <strong style="font-size: 11px; color: #999;">Parameters:</strong><br>
                    <span style="font-size: 14px; font-weight: 600;">${model.parameters}</span>
                </div>
                <div>
                    <strong style="font-size: 11px; color: #999;">Size:</strong><br>
                    <span style="font-size: 14px; font-weight: 600;">${model.size_gb.toFixed(1)} GB</span>
                </div>
                <div>
                    <strong style="font-size: 11px; color: #999;">Context:</strong><br>
                    <span style="font-size: 14px; font-weight: 600;">${model.max_context_length || 'N/A'} tokens</span>
                </div>
                <div>
                    <strong style="font-size: 11px; color: #999;">Version:</strong><br>
                    <span style="font-size: 14px; font-weight: 600;">${model.version}</span>
                </div>
            </div>
            
            <div style="margin: 10px 0;">
                <strong style="font-size: 11px; color: #999;">CAPABILITIES:</strong><br>
                <div style="margin-top: 8px;">
                    ${capabilitiesHTML}
                </div>
            </div>
            
            <button class="btn-small" style="width: 100%; margin-top: 10px; background: ${color};" onclick="viewCogniwareModelDetails('${model.model_id}')">📊 View Details</button>
        </div>
    `;
}

// View Cogniware Model Details
async function viewCogniwareModelDetails(modelId) {
    try {
        const result = await apiCall(`/admin/llm/cogniware/${modelId}`);
        
        if (result.success) {
            const model = result.llm;
            const modal = document.getElementById('modal');
            const modalTitle = document.getElementById('modalTitle');
            const modalBody = document.getElementById('modalBody');
            
            modalTitle.textContent = model.model_name;
            
            let useCasesHTML = '';
            if (model.use_cases && model.use_cases.length > 0) {
                useCasesHTML = '<div style="margin-top: 15px;"><strong>Use Cases:</strong><ul style="margin: 5px 0 0 20px;">';
                model.use_cases.forEach(uc => {
                    useCasesHTML += `<li>${uc}</li>`;
                });
                useCasesHTML += '</ul></div>';
            }
            
            let tasksHTML = '';
            if (model.supported_tasks && model.supported_tasks.length > 0) {
                tasksHTML = '<div style="margin-top: 15px;"><strong>Supported Tasks:</strong><ul style="margin: 5px 0 0 20px;">';
                model.supported_tasks.forEach(task => {
                    tasksHTML += `<li>${task}</li>`;
                });
                tasksHTML += '</ul></div>';
            }
            
            let languagesHTML = '';
            if (model.supported_languages && model.supported_languages.length > 0) {
                languagesHTML = `<div style="margin-top: 15px;"><strong>Supported Languages:</strong><br>${model.supported_languages.join(', ')}</div>`;
            }
            
            let databasesHTML = '';
            if (model.supported_databases && model.supported_databases.length > 0) {
                databasesHTML = `<div style="margin-top: 15px;"><strong>Supported Databases:</strong><br>${model.supported_databases.join(', ')}</div>`;
            }
            
            modalBody.innerHTML = `
                <div style="background: #f9f9f9; padding: 20px; border-radius: 12px;">
                    <p style="color: #666; margin-bottom: 20px;">${model.description}</p>
                    
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 20px;">
                        <div style="background: white; padding: 15px; border-radius: 8px;">
                            <strong style="color: #999; font-size: 12px;">MODEL ID</strong><br>
                            <code style="font-size: 12px;">${model.model_id}</code>
                        </div>
                        <div style="background: white; padding: 15px; border-radius: 8px;">
                            <strong style="color: #999; font-size: 12px;">TYPE</strong><br>
                            <span style="font-size: 14px; font-weight: 600; text-transform: capitalize;">${model.model_type}</span>
                        </div>
                        <div style="background: white; padding: 15px; border-radius: 8px;">
                            <strong style="color: #999; font-size: 12px;">PARAMETERS</strong><br>
                            <span style="font-size: 18px; font-weight: 700; color: #667eea;">${model.parameters}</span>
                        </div>
                        <div style="background: white; padding: 15px; border-radius: 8px;">
                            <strong style="color: #999; font-size: 12px;">SIZE</strong><br>
                            <span style="font-size: 18px; font-weight: 700; color: #667eea;">${model.size_gb.toFixed(1)} GB</span>
                        </div>
                        <div style="background: white; padding: 15px; border-radius: 8px;">
                            <strong style="color: #999; font-size: 12px;">CONTEXT LENGTH</strong><br>
                            <span style="font-size: 14px; font-weight: 600;">${model.max_context_length || 'N/A'} tokens</span>
                        </div>
                        <div style="background: white; padding: 15px; border-radius: 8px;">
                            <strong style="color: #999; font-size: 12px;">STATUS</strong><br>
                            <span style="font-size: 14px; font-weight: 600; color: #2d862d;">✅ ${model.status}</span>
                        </div>
                    </div>
                    
                    <div style="background: white; padding: 15px; border-radius: 8px;">
                        <strong>Capabilities:</strong><br>
                        <div style="margin-top: 10px;">
                            ${model.capabilities.map(c => `<span class="badge active" style="margin: 5px 5px 0 0; background: #667eea;">${c}</span>`).join('')}
                        </div>
                    </div>
                    
                    ${tasksHTML}
                    ${languagesHTML}
                    ${databasesHTML}
                    ${useCasesHTML}
                </div>
            `;
            
            modal.style.display = 'block';
        }
    } catch (error) {
        alert('Error loading model details: ' + error.message);
    }
}

// Load Imported Models (from Ollama/HuggingFace)
async function loadImportedModels() {
    try {
        const models = await apiCall('/admin/llm/models');
        const container = document.getElementById('importedModelsList');
        
        if (models.models && models.models.length > 0) {
            let html = '<table><thead><tr><th>Model Name</th><th>Type</th><th>Source</th><th>Parameters</th><th>Size</th><th>Status</th><th>Progress</th><th>Usage</th><th>Actions</th></tr></thead><tbody>';
            
            models.models.forEach(model => {
                let statusBadge = '';
                if (model.status === 'ready') {
                    statusBadge = `<span class="badge active">✅ Ready</span>`;
                } else if (model.status === 'downloading') {
                    statusBadge = `<span class="badge" style="background: #fff3cd; color: #856404;">⬇️ Downloading</span>`;
                } else if (model.status === 'error') {
                    statusBadge = `<span class="badge inactive">❌ Error</span>`;
                } else {
                    statusBadge = `<span class="badge" style="background: #e0e0e0; color: #666;">⏳ Pending</span>`;
                }
                
                const progress = model.download_progress || 0;
                const progressBar = `
                    <div style="width: 100px; background: #e0e0e0; height: 8px; border-radius: 4px; overflow: hidden;">
                        <div style="width: ${progress}%; height: 100%; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);"></div>
                    </div>
                    <div style="font-size: 0.85em; color: #666;">${progress.toFixed(0)}%</div>
                `;
                
                const typeBadge = model.model_type === 'interface' ? 
                    '<span class="badge" style="background: #e6f3ff; color: #2d5c86;">🗣️ Interface</span>' :
                    '<span class="badge" style="background: #f3e6ff; color: #6d2d86;">📚 Knowledge</span>';
                
                html += `<tr>
                    <td><strong>${model.model_name}</strong></td>
                    <td>${typeBadge}</td>
                    <td><span class="badge" style="background: #f0f0f0;">${model.source}</span></td>
                    <td>${model.parameters || 'N/A'}</td>
                    <td>${model.size_gb ? model.size_gb.toFixed(1) + ' GB' : 'N/A'}</td>
                    <td>${statusBadge}</td>
                    <td>${progressBar}</td>
                    <td>${model.usage_count || 0} calls</td>
                    <td>
                        <button class="btn-small" style="background: #2196f3; font-size: 11px; padding: 6px 10px;" onclick="viewImportedModelDetails('${model.model_id}')">📊 Details</button>
                        <button class="btn-small btn-danger" style="font-size: 11px; padding: 6px 10px;" onclick="deleteModel('${model.model_id}')">🗑️ Delete</button>
                    </td>
                </tr>`;
            });
            html += '</tbody></table>';
            container.innerHTML = html;
            
            // Auto-refresh if any models are downloading
            if (models.models.some(m => m.status === 'downloading')) {
                setTimeout(loadImportedModels, 5000);
            }
        } else {
            container.innerHTML = '<p style="color: #999;">No imported models. Use the buttons above to import models from Ollama or HuggingFace.</p>';
        }
    } catch (error) {
        document.getElementById('importedModelsList').innerHTML = '<p style="color: #c33;">Error loading imported models</p>';
    }
}

// Main load function
async function loadLLMModels() {
    if (currentLLMTab === 'cogniware') {
        await loadCogniwareLLMs();
    } else {
        await loadImportedModels();
    }
}

// Ollama/HuggingFace model loading (for import modals)
async function loadOllamaModels() {
    try {
        const data = await apiCall('/admin/llm/sources/ollama');
        availableOllamaModels = data.models || [];
        return data;
    } catch (error) {
        return {success: false, models: []};
    }
}

async function loadHuggingFaceModels() {
    try {
        const data = await apiCall('/admin/llm/sources/huggingface');
        availableHuggingFaceModels = data.models || [];
        return data;
    } catch (error) {
        return {success: false, models: []};
    }
}

// Modal functions for importing external models
async function showCreateInterfaceLLMModal() {
    await loadOllamaModels();
    await loadHuggingFaceModels();
    
    const modal = document.getElementById('modal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    modalTitle.textContent = 'Import Interface LLM from External Source';
    
    let ollamaOptions = '';
    availableOllamaModels.forEach(model => {
        ollamaOptions += `<option value="${model.id}" data-size="${model.size}">${model.name} (${model.size})</option>`;
    });
    
    let hfOptions = '';
    availableHuggingFaceModels.forEach(model => {
        hfOptions += `<option value="${model.id}" data-size="${model.size}">${model.name} (${model.size})</option>`;
    });
    
    modalBody.innerHTML = `
        <p style="color: #666; margin-bottom: 20px;">Download and import an Interface LLM from Ollama or HuggingFace. These models will be downloaded and integrated into Cogniware's inference engine.</p>
        
        <div class="form-group">
            <label>Source</label>
            <select id="llmSource" onchange="updateLLMModelList('interface')">
                <option value="ollama">Ollama</option>
                <option value="huggingface">HuggingFace</option>
            </select>
        </div>
        
        <div class="form-group" id="ollamaModelsGroup">
            <label>Select Ollama Model</label>
            <select id="ollamaModelSelect" onchange="updateLLMFormData('interface')">
                <option value="">Choose a model...</option>
                ${ollamaOptions}
            </select>
        </div>
        
        <div class="form-group" id="hfModelsGroup" style="display: none;">
            <label>Select HuggingFace Model</label>
            <select id="hfModelSelect" onchange="updateLLMFormData('interface')">
                <option value="">Choose a model...</option>
                ${hfOptions}
            </select>
        </div>
        
        <div class="form-group">
            <label>Model Name (Display)</label>
            <input type="text" id="llmDisplayName" placeholder="My Interface LLM">
        </div>
        
        <div id="llmSizeInfo" style="background: #f9f9f9; padding: 15px; border-radius: 8px; margin: 15px 0;"></div>
        
        <button class="btn" onclick="createInterfaceLLM()">🚀 Import & Download</button>
        <p style="color: #999; font-size: 0.85em; margin-top: 10px;">Download will start in background. Check "Import from External" tab for progress.</p>
    `;
    
    modal.style.display = 'block';
}

async function showCreateKnowledgeLLMModal() {
    await loadOllamaModels();
    await loadHuggingFaceModels();
    
    const modal = document.getElementById('modal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    modalTitle.textContent = 'Import Knowledge LLM from External Source';
    
    let ollamaOptions = '';
    availableOllamaModels.forEach(model => {
        ollamaOptions += `<option value="${model.id}" data-size="${model.size}">${model.name} (${model.size})</option>`;
    });
    
    let hfOptions = '';
    availableHuggingFaceModels.forEach(model => {
        hfOptions += `<option value="${model.id}" data-size="${model.size}">${model.name} (${model.size})</option>`;
    });
    
    modalBody.innerHTML = `
        <p style="color: #666; margin-bottom: 20px;">Download and import a Knowledge LLM from Ollama or HuggingFace. These models are optimized for Q&A and information retrieval.</p>
        
        <div class="form-group">
            <label>Source</label>
            <select id="llmSource" onchange="updateLLMModelList('knowledge')">
                <option value="ollama">Ollama</option>
                <option value="huggingface">HuggingFace</option>
            </select>
        </div>
        
        <div class="form-group" id="ollamaModelsGroup">
            <label>Select Ollama Model</label>
            <select id="ollamaModelSelect" onchange="updateLLMFormData('knowledge')">
                <option value="">Choose a model...</option>
                ${ollamaOptions}
            </select>
        </div>
        
        <div class="form-group" id="hfModelsGroup" style="display: none;">
            <label>Select HuggingFace Model</label>
            <select id="hfModelSelect" onchange="updateLLMFormData('knowledge')">
                <option value="">Choose a model...</option>
                ${hfOptions}
            </select>
        </div>
        
        <div class="form-group">
            <label>Model Name (Display)</label>
            <input type="text" id="llmDisplayName" placeholder="My Knowledge LLM">
        </div>
        
        <div id="llmSizeInfo" style="background: #f9f9f9; padding: 15px; border-radius: 8px; margin: 15px 0;"></div>
        
        <button class="btn" onclick="createKnowledgeLLM()">🚀 Import & Download</button>
        <p style="color: #999; font-size: 0.85em; margin-top: 10px;">Download will start in background. Check "Import from External" tab for progress.</p>
    `;
    
    modal.style.display = 'block';
}

function updateLLMModelList(llmType) {
    const source = document.getElementById('llmSource').value;
    
    if (source === 'ollama') {
        document.getElementById('ollamaModelsGroup').style.display = 'block';
        document.getElementById('hfModelsGroup').style.display = 'none';
    } else {
        document.getElementById('ollamaModelsGroup').style.display = 'none';
        document.getElementById('hfModelsGroup').style.display = 'block';
    }
}

function updateLLMFormData(llmType) {
    const source = document.getElementById('llmSource').value;
    let selectedOption;
    
    if (source === 'ollama') {
        const select = document.getElementById('ollamaModelSelect');
        selectedOption = select.options[select.selectedIndex];
    } else {
        const select = document.getElementById('hfModelSelect');
        selectedOption = select.options[select.selectedIndex];
    }
    
    if (selectedOption && selectedOption.value) {
        const size = selectedOption.getAttribute('data-size');
        const modelName = selectedOption.text.split(' (')[0];
        
        document.getElementById('llmDisplayName').value = modelName;
        document.getElementById('llmSizeInfo').innerHTML = `
            <strong>Download Size:</strong> ${size}<br>
            <strong>Type:</strong> ${llmType === 'interface' ? 'Interface LLM (Chat, Dialogue)' : 'Knowledge LLM (Q&A, Retrieval)'}<br>
            <strong>Source:</strong> ${source === 'ollama' ? 'Ollama' : 'HuggingFace'}<br>
            <br>
            <strong style="color: #ff9800;">⚠️ Download will start immediately and run in background.</strong>
        `;
    }
}

async function createInterfaceLLM() {
    const source = document.getElementById('llmSource').value;
    let sourceModelId, sizeStr;
    
    if (source === 'ollama') {
        const select = document.getElementById('ollamaModelSelect');
        const selectedOption = select.options[select.selectedIndex];
        sourceModelId = select.value;
        sizeStr = selectedOption.getAttribute('data-size');
    } else {
        const select = document.getElementById('hfModelSelect');
        const selectedOption = select.options[select.selectedIndex];
        sourceModelId = select.value;
        sizeStr = selectedOption.getAttribute('data-size');
    }
    
    if (!sourceModelId) {
        alert('Please select a model');
        return;
    }
    
    const sizeGB = parseFloat(sizeStr.replace(/[^0-9.]/g, ''));
    
    const result = await apiCall('/admin/llm/interface', 'POST', {
        model_name: document.getElementById('llmDisplayName').value,
        source: source,
        source_model_id: sourceModelId,
        size_gb: sizeGB,
        parameters: 'Unknown'
    });
    
    if (result.success) {
        alert(`✅ Interface LLM Import Started!\n\nModel ID: ${result.model_id}\nName: ${result.model_name}\n\nDownload started in background.\nSwitch to "Import from External" tab to see progress.`);
        closeModal();
        showLLMTab('import');
    } else {
        alert('❌ Error: ' + (result.error || JSON.stringify(result)));
    }
}

async function createKnowledgeLLM() {
    const source = document.getElementById('llmSource').value;
    let sourceModelId, sizeStr;
    
    if (source === 'ollama') {
        const select = document.getElementById('ollamaModelSelect');
        const selectedOption = select.options[select.selectedIndex];
        sourceModelId = select.value;
        sizeStr = selectedOption.getAttribute('data-size');
    } else {
        const select = document.getElementById('hfModelSelect');
        const selectedOption = select.options[select.selectedIndex];
        sourceModelId = select.value;
        sizeStr = selectedOption.getAttribute('data-size');
    }
    
    if (!sourceModelId) {
        alert('Please select a model');
        return;
    }
    
    const sizeGB = parseFloat(sizeStr.replace(/[^0-9.]/g, ''));
    
    const result = await apiCall('/admin/llm/knowledge', 'POST', {
        model_name: document.getElementById('llmDisplayName').value,
        source: source,
        source_model_id: sourceModelId,
        size_gb: sizeGB,
        parameters: 'Unknown'
    });
    
    if (result.success) {
        alert(`✅ Knowledge LLM Import Started!\n\nModel ID: ${result.model_id}\nName: ${result.model_name}\n\nDownload started in background.\nSwitch to "Import from External" tab to see progress.`);
        closeModal();
        showLLMTab('import');
    } else {
        alert('❌ Error: ' + (result.error || JSON.stringify(result)));
    }
}

async function viewImportedModelDetails(modelId) {
    const result = await apiCall(`/admin/llm/models/${modelId}`);
    
    if (result.success) {
        const model = result.model;
        const modal = document.getElementById('modal');
        const modalTitle = document.getElementById('modalTitle');
        const modalBody = document.getElementById('modalBody');
        
        modalTitle.textContent = `Imported Model: ${model.model_name}`;
        
        const statusColor = model.status === 'ready' ? '#2d862d' : 
                          model.status === 'downloading' ? '#ff9800' : '#c33';
        
        modalBody.innerHTML = `
            <div style="background: #f9f9f9; padding: 20px; border-radius: 8px;">
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">
                    <div>
                        <strong>Model ID:</strong><br>
                        <code style="font-size: 0.85em;">${model.model_id}</code>
                    </div>
                    <div>
                        <strong>Model Type:</strong><br>
                        ${model.model_type}
                    </div>
                    <div>
                        <strong>Source:</strong><br>
                        ${model.source}
                    </div>
                    <div>
                        <strong>Parameters:</strong><br>
                        ${model.parameters || 'N/A'}
                    </div>
                    <div>
                        <strong>Size:</strong><br>
                        ${model.size_gb ? model.size_gb.toFixed(1) + ' GB' : 'N/A'}
                    </div>
                    <div>
                        <strong>Status:</strong><br>
                        <span style="color: ${statusColor}; font-weight: 600;">${model.status}</span>
                    </div>
                    <div>
                        <strong>Download Progress:</strong><br>
                        ${model.download_progress ? model.download_progress.toFixed(0) + '%' : 'N/A'}
                    </div>
                    <div>
                        <strong>Usage Count:</strong><br>
                        ${model.usage_count || 0} calls
                    </div>
                </div>
                
                ${model.error_message ? `
                    <div style="margin-top: 20px; color: #c33;">
                        <strong>Error:</strong><br>
                        ${model.error_message}
                    </div>
                ` : ''}
            </div>
        `;
        
        modal.style.display = 'block';
    }
}

async function deleteModel(modelId) {
    if (confirm('⚠️ Delete this model?\n\nThis will remove the model from the database and delete downloaded files.')) {
        const result = await apiCall(`/admin/llm/models/${modelId}`, 'DELETE');
        
        if (result.success) {
            alert('✅ Model deleted successfully!');
            loadImportedModels();
        } else {
            alert('❌ Error: ' + (result.error || 'Failed to delete model'));
        }
    }
}

// Update the existing showModal function
const originalShowModal = window.showModal;
window.showModal = function(type) {
    if (type === 'createInterfaceLLM') {
        showCreateInterfaceLLMModal();
    } else if (type === 'createKnowledgeLLM') {
        showCreateKnowledgeLLMModal();
    } else if (originalShowModal) {
        originalShowModal(type);
    }
};
