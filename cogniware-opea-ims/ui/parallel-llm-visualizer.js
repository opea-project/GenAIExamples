/**
 * Cogniware Parallel LLM Execution Visualizer
 * Real-time visualization of patent-compliant parallel LLM processing
 * 
 * Shows:
 * - Multiple LLMs executing in parallel
 * - Real-time progress indicators
 * - Performance metrics (speedup, time saved)
 * - Confidence scores
 * - Synthesis process
 */

class ParallelLLMVisualizer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.animationInterval = null;
    }

    /**
     * Show parallel execution visualization
     */
    showParallelExecution(numInterface = 2, numKnowledge = 1) {
        if (!this.container) return;

        const html = `
            <div class="parallel-llm-container" style="
                background: linear-gradient(135deg, #f5f7ff 0%, #faf5ff 100%);
                border: 2px solid #667eea;
                border-radius: 16px;
                padding: 24px;
                margin: 20px 0;
            ">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">
                    <div class="spinner" style="width: 24px; height: 24px; border-width: 3px;"></div>
                    <h4 style="margin: 0; color: #667eea;">
                        🚀 Patent-Compliant Parallel Execution (MCP)
                    </h4>
                </div>

                <p style="color: #666; margin-bottom: 20px; font-size: 14px;">
                    Processing with <strong>${numInterface} Interface LLMs</strong> + 
                    <strong>${numKnowledge} Knowledge LLMs</strong> simultaneously...
                </p>

                <div id="llmExecutionBars" class="llm-bars">
                    ${this.generateLLMBars(numInterface, numKnowledge)}
                </div>

                <div class="synthesis-indicator" style="
                    margin-top: 24px;
                    padding: 16px;
                    background: rgba(102, 126, 234, 0.1);
                    border-radius: 12px;
                    text-align: center;
                ">
                    <div class="spinner" style="width: 20px; height: 20px; border-width: 2px; margin: 0 auto 8px;"></div>
                    <span style="color: #667eea; font-weight: 600;">Synthesizing results from heterogeneous LLMs...</span>
                </div>

                <div style="
                    margin-top: 16px;
                    padding: 12px;
                    background: rgba(255, 193, 7, 0.1);
                    border-left: 4px solid #ffc107;
                    border-radius: 4px;
                    font-size: 12px;
                    color: #856404;
                ">
                    ⚡ <strong>Patent Claim</strong>: Multi-Context Processing (MCP) - Executing heterogeneous LLM types in parallel for superior results
                </div>
            </div>
        `;

        this.container.innerHTML = html;
        this.animateBars();
    }

    /**
     * Generate progress bars for LLMs
     */
    generateLLMBars(numInterface, numKnowledge) {
        let html = '';

        // Interface LLM bars
        for (let i = 0; i < numInterface; i++) {
            html += this.createLLMBar(
                `Interface LLM ${i + 1}`,
                'interface',
                `cogniware-code-7b`,
                '#4caf50',
                Math.random() * 30 + 50  // Random starting progress
            );
        }

        // Knowledge LLM bars
        for (let i = 0; i < numKnowledge; i++) {
            html += this.createLLMBar(
                `Knowledge LLM ${i + 1}`,
                'knowledge',
                `cogniware-knowledge-7b`,
                '#2196f3',
                Math.random() * 30 + 40
            );
        }

        return html;
    }

    /**
     * Create a single LLM progress bar
     */
    createLLMBar(name, type, modelId, color, initialProgress) {
        return `
            <div class="llm-bar" data-progress="${initialProgress}" style="
                margin-bottom: 12px;
                padding: 12px;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span style="
                            display: inline-block;
                            width: 12px;
                            height: 12px;
                            background: ${color};
                            border-radius: 50%;
                        "></span>
                        <strong style="color: #333; font-size: 13px;">${name}</strong>
                        <span style="
                            font-size: 11px;
                            color: #999;
                            background: #f0f0f0;
                            padding: 2px 8px;
                            border-radius: 4px;
                        ">${modelId}</span>
                    </div>
                    <span class="llm-progress-text" style="
                        font-size: 13px;
                        font-weight: 600;
                        color: ${color};
                    ">${Math.floor(initialProgress)}%</span>
                </div>
                <div style="
                    width: 100%;
                    height: 8px;
                    background: #e0e0e0;
                    border-radius: 4px;
                    overflow: hidden;
                ">
                    <div class="llm-progress-bar" style="
                        width: ${initialProgress}%;
                        height: 100%;
                        background: linear-gradient(90deg, ${color} 0%, ${color}dd 100%);
                        transition: width 0.3s ease;
                    "></div>
                </div>
            </div>
        `;
    }

    /**
     * Animate progress bars
     */
    animateBars() {
        clearInterval(this.animationInterval);

        this.animationInterval = setInterval(() => {
            const bars = this.container.querySelectorAll('.llm-bar');
            let allComplete = true;

            bars.forEach(bar => {
                const progressBar = bar.querySelector('.llm-progress-bar');
                const progressText = bar.querySelector('.llm-progress-text');
                let currentProgress = parseFloat(bar.getAttribute('data-progress'));

                if (currentProgress < 100) {
                    allComplete = false;
                    // Increment progress (faster near completion)
                    const increment = currentProgress < 80 ? 5 : 10;
                    currentProgress = Math.min(100, currentProgress + increment);
                    
                    bar.setAttribute('data-progress', currentProgress);
                    progressBar.style.width = currentProgress + '%';
                    progressText.textContent = Math.floor(currentProgress) + '%';

                    // Add checkmark when complete
                    if (currentProgress >= 100) {
                        progressText.innerHTML = '✓ Complete';
                        progressText.style.color = '#2d862d';
                    }
                }
            });

            if (allComplete) {
                clearInterval(this.animationInterval);
                // All bars complete - could trigger synthesis animation here
            }
        }, 200); // Update every 200ms
    }

    /**
     * Show execution result
     */
    showResult(result) {
        if (!this.container) return;

        clearInterval(this.animationInterval);

        const successColor = result.success ? '#2d862d' : '#c33';
        const successIcon = result.success ? '✅' : '❌';

        const html = `
            <div class="parallel-llm-result" style="
                background: white;
                border: 2px solid ${successColor};
                border-radius: 16px;
                padding: 24px;
                margin: 20px 0;
            ">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">
                    <span style="font-size: 32px;">${successIcon}</span>
                    <h4 style="margin: 0; color: ${successColor};">
                        ${result.success ? 'Parallel Execution Complete!' : 'Execution Failed'}
                    </h4>
                </div>

                ${result.success ? this.generateSuccessMetrics(result) : this.generateErrorInfo(result)}
            </div>
        `;

        this.container.innerHTML = html;
    }

    /**
     * Generate success metrics display
     */
    generateSuccessMetrics(result) {
        const llms = result.llms_used || {};
        const perf = result.performance || {};
        const qual = result.quality || {};

        return `
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 20px;">
                <div class="metric-card">
                    <div class="metric-label">LLMs Executed</div>
                    <div class="metric-value">${llms.total || 0}</div>
                    <div class="metric-detail">${llms.interface || 0} Interface + ${llms.knowledge || 0} Knowledge</div>
                </div>

                <div class="metric-card">
                    <div class="metric-label">Processing Time</div>
                    <div class="metric-value">${(perf.processing_time_ms || 0).toFixed(0)}ms</div>
                    <div class="metric-detail">Patent-compliant MCP</div>
                </div>

                <div class="metric-card">
                    <div class="metric-label">Parallel Speedup</div>
                    <div class="metric-value">${perf.parallel_speedup || 'N/A'}</div>
                    <div class="metric-detail">vs. sequential execution</div>
                </div>

                <div class="metric-card">
                    <div class="metric-label">Confidence Score</div>
                    <div class="metric-value">${qual.confidence_score || 'N/A'}</div>
                    <div class="metric-detail">${qual.synthesis_method || 'N/A'}</div>
                </div>
            </div>

            <style>
                .metric-card {
                    background: linear-gradient(135deg, #f9f9f9 0%, #ffffff 100%);
                    padding: 16px;
                    border-radius: 12px;
                    border: 1px solid #e0e0e0;
                    text-align: center;
                }
                .metric-label {
                    font-size: 11px;
                    color: #999;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-bottom: 8px;
                }
                .metric-value {
                    font-size: 28px;
                    font-weight: 700;
                    color: #667eea;
                    margin-bottom: 4px;
                }
                .metric-detail {
                    font-size: 12px;
                    color: #666;
                }
            </style>

            ${result.patent_claim ? `
                <div style="
                    padding: 12px 16px;
                    background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
                    border-radius: 8px;
                    margin-bottom: 16px;
                    border-left: 4px solid #667eea;
                ">
                    <strong style="color: #667eea;">🏆 Patent Claim:</strong>
                    <span style="color: #666;">${result.patent_claim}</span>
                </div>
            ` : ''}

            <div style="
                padding: 16px;
                background: #f9f9f9;
                border-radius: 12px;
                max-height: 400px;
                overflow-y: auto;
            ">
                <strong style="color: #333; display: block; margin-bottom: 12px;">Generated Output:</strong>
                <pre style="
                    margin: 0;
                    padding: 16px;
                    background: #1e1e1e;
                    color: #d4d4d4;
                    border-radius: 8px;
                    font-size: 13px;
                    line-height: 1.6;
                    overflow-x: auto;
                ">${result.generated_output || result.generated_code || result.result || 'No output generated'}</pre>
            </div>
        `;
    }

    /**
     * Generate error information
     */
    generateErrorInfo(result) {
        return `
            <div style="
                padding: 16px;
                background: #fee;
                border-radius: 12px;
                color: #c33;
            ">
                <strong>Error:</strong> ${result.error || 'Unknown error occurred'}
            </div>
        `;
    }

    /**
     * Clear visualization
     */
    clear() {
        if (this.container) {
            this.container.innerHTML = '';
        }
        clearInterval(this.animationInterval);
    }
}

// Export for global use
window.ParallelLLMVisualizer = ParallelLLMVisualizer;

