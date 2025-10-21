/**
 * Cogniware Core - Shared JavaScript Utilities
 * Common functions and utilities for all UI components
 */

// =============================================================================
// CONFIGURATION
// =============================================================================

const CONFIG = {
    API_BASE: 'http://localhost:8099',
    API_TIMEOUT: 30000,
    REFRESH_INTERVAL: 30000,
    TOAST_DURATION: 5000
};

// =============================================================================
// AUTHENTICATION
// =============================================================================

/**
 * Get stored authentication token
 */
function getAuthToken() {
    return localStorage.getItem('cogniware_token') || sessionStorage.getItem('cogniware_token');
}

/**
 * Get stored user data
 */
function getCurrentUser() {
    const userStr = localStorage.getItem('cogniware_user') || sessionStorage.getItem('cogniware_user');
    return userStr ? JSON.parse(userStr) : null;
}

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    return !!getAuthToken();
}

/**
 * Check if user has specific role
 */
function hasRole(role) {
    const user = getCurrentUser();
    if (!user) return false;
    if (Array.isArray(role)) {
        return role.includes(user.role);
    }
    return user.role === role;
}

/**
 * Logout and redirect to login
 */
function logout() {
    localStorage.removeItem('cogniware_token');
    localStorage.removeItem('cogniware_user');
    localStorage.removeItem('cogniware_login_time');
    sessionStorage.removeItem('cogniware_token');
    sessionStorage.removeItem('cogniware_user');
    sessionStorage.removeItem('cogniware_login_time');
    window.location.href = 'login.html';
}

/**
 * Verify authentication and redirect if not authenticated
 */
function requireAuth(allowedRoles = null) {
    if (!isAuthenticated()) {
        window.location.href = 'login.html';
        return false;
    }

    if (allowedRoles && !hasRole(allowedRoles)) {
        showToast('Access Denied', 'You do not have permission to access this page', 'error');
        setTimeout(() => {
            window.location.href = 'login.html';
        }, 2000);
        return false;
    }

    return true;
}

// =============================================================================
// API UTILITIES
// =============================================================================

/**
 * Make authenticated API request
 */
async function apiRequest(endpoint, options = {}) {
    const token = getAuthToken();
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': token ? `Bearer ${token}` : '',
            ...options.headers
        }
    };

    const finalOptions = { ...defaultOptions, ...options };

    try {
        const response = await fetch(`${CONFIG.API_BASE}${endpoint}`, finalOptions);
        
        // Handle 401 Unauthorized
        if (response.status === 401) {
            showToast('Session Expired', 'Please log in again', 'warning');
            setTimeout(logout, 2000);
            throw new Error('Unauthorized');
        }

        // Handle 403 Forbidden
        if (response.status === 403) {
            showToast('Access Denied', 'You do not have permission for this action', 'error');
            throw new Error('Forbidden');
        }

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || data.error || 'Request failed');
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

/**
 * GET request helper
 */
async function apiGet(endpoint) {
    return apiRequest(endpoint, { method: 'GET' });
}

/**
 * POST request helper
 */
async function apiPost(endpoint, data) {
    return apiRequest(endpoint, {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

/**
 * PUT request helper
 */
async function apiPut(endpoint, data) {
    return apiRequest(endpoint, {
        method: 'PUT',
        body: JSON.stringify(data)
    });
}

/**
 * DELETE request helper
 */
async function apiDelete(endpoint) {
    return apiRequest(endpoint, { method: 'DELETE' });
}

// =============================================================================
// UI COMPONENTS
// =============================================================================

/**
 * Show toast notification
 */
function showToast(title, message, type = 'info') {
    const toastContainer = getOrCreateToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type} animate-fade-in`;
    
    const icons = {
        success: '✓',
        error: '✗',
        warning: '⚠',
        info: 'ℹ'
    };

    toast.innerHTML = `
        <div class="toast-icon">${icons[type]}</div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;

    toastContainer.appendChild(toast);

    // Auto remove after duration
    setTimeout(() => {
        toast.classList.add('toast-fade-out');
        setTimeout(() => toast.remove(), 300);
    }, CONFIG.TOAST_DURATION);
}

function getOrCreateToastContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);

        // Add toast styles if not already present
        if (!document.getElementById('toast-styles')) {
            const style = document.createElement('style');
            style.id = 'toast-styles';
            style.textContent = `
                .toast-container {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: var(--z-tooltip, 1070);
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                    max-width: 400px;
                }

                .toast {
                    background: white;
                    padding: 16px;
                    border-radius: 12px;
                    box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                    display: flex;
                    gap: 12px;
                    align-items: flex-start;
                    border-left: 4px solid;
                }

                .toast-success { border-left-color: #22c55e; }
                .toast-error { border-left-color: #ef4444; }
                .toast-warning { border-left-color: #f59e0b; }
                .toast-info { border-left-color: #3b82f6; }

                .toast-icon {
                    font-size: 20px;
                    font-weight: bold;
                    width: 24px;
                    height: 24px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 50%;
                    flex-shrink: 0;
                }

                .toast-success .toast-icon { background: #22c55e; color: white; }
                .toast-error .toast-icon { background: #ef4444; color: white; }
                .toast-warning .toast-icon { background: #f59e0b; color: white; }
                .toast-info .toast-icon { background: #3b82f6; color: white; }

                .toast-content {
                    flex: 1;
                }

                .toast-title {
                    font-weight: 600;
                    margin-bottom: 4px;
                    color: #1f2937;
                }

                .toast-message {
                    font-size: 14px;
                    color: #6b7280;
                }

                .toast-close {
                    background: none;
                    border: none;
                    font-size: 24px;
                    color: #9ca3af;
                    cursor: pointer;
                    padding: 0;
                    width: 24px;
                    height: 24px;
                    line-height: 1;
                    flex-shrink: 0;
                }

                .toast-close:hover {
                    color: #374151;
                }

                .toast-fade-out {
                    animation: fadeOut 300ms ease-out forwards;
                }

                @keyframes fadeOut {
                    from {
                        opacity: 1;
                        transform: translateX(0);
                    }
                    to {
                        opacity: 0;
                        transform: translateX(100%);
                    }
                }

                @media (max-width: 768px) {
                    .toast-container {
                        left: 20px;
                        right: 20px;
                        max-width: none;
                    }
                }
            `;
            document.head.appendChild(style);
        }
    }
    return container;
}

/**
 * Show loading overlay
 */
function showLoading(message = 'Loading...') {
    hideLoading(); // Remove any existing overlay

    const overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.className = 'loading-overlay';
    overlay.innerHTML = `
        <div style="text-align: center; background: white; padding: 40px; border-radius: 16px; box-shadow: 0 25px 50px rgba(0,0,0,0.25);">
            <div class="spinner spinner-lg"></div>
            <div style="margin-top: 20px; font-size: 18px; font-weight: 600; color: #374151;">${message}</div>
        </div>
    `;
    document.body.appendChild(overlay);
    document.body.style.overflow = 'hidden';
}

/**
 * Hide loading overlay
 */
function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.remove();
        document.body.style.overflow = '';
    }
}

/**
 * Show confirmation dialog
 */
function showConfirm(title, message, onConfirm, onCancel) {
    const backdrop = document.createElement('div');
    backdrop.className = 'modal-backdrop';
    
    const modal = document.createElement('div');
    modal.className = 'modal animate-fade-in';
    modal.style.maxWidth = '500px';
    modal.innerHTML = `
        <div class="modal-header">
            <h3 class="modal-title">${title}</h3>
        </div>
        <div class="modal-body">
            <p style="font-size: 16px; color: #4b5563;">${message}</p>
        </div>
        <div class="modal-footer">
            <button class="btn btn-secondary" id="confirmCancel">Cancel</button>
            <button class="btn btn-primary" id="confirmOk">Confirm</button>
        </div>
    `;

    backdrop.appendChild(modal);
    document.body.appendChild(backdrop);
    document.body.style.overflow = 'hidden';

    function cleanup() {
        backdrop.remove();
        document.body.style.overflow = '';
    }

    document.getElementById('confirmCancel').onclick = () => {
        cleanup();
        if (onCancel) onCancel();
    };

    document.getElementById('confirmOk').onclick = () => {
        cleanup();
        if (onConfirm) onConfirm();
    };

    backdrop.onclick = (e) => {
        if (e.target === backdrop) {
            cleanup();
            if (onCancel) onCancel();
        }
    };
}

// =============================================================================
// DATA FORMATTING
// =============================================================================

/**
 * Format date for display
 */
function formatDate(date, format = 'full') {
    if (!date) return 'N/A';
    
    const d = new Date(date);
    if (isNaN(d.getTime())) return 'Invalid Date';

    const options = {
        'full': { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' },
        'date': { year: 'numeric', month: 'long', day: 'numeric' },
        'short': { month: 'short', day: 'numeric', year: 'numeric' },
        'time': { hour: '2-digit', minute: '2-digit' },
        'relative': null // Special case handled below
    };

    if (format === 'relative') {
        return formatRelativeTime(d);
    }

    return d.toLocaleDateString('en-US', options[format] || options['full']);
}

/**
 * Format relative time (e.g., "2 hours ago")
 */
function formatRelativeTime(date) {
    const now = new Date();
    const diff = now - date;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (seconds < 60) return 'Just now';
    if (minutes < 60) return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
    if (hours < 24) return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
    if (days < 7) return `${days} day${days !== 1 ? 's' : ''} ago`;
    if (days < 30) return `${Math.floor(days / 7)} week${Math.floor(days / 7) !== 1 ? 's' : ''} ago`;
    if (days < 365) return `${Math.floor(days / 30)} month${Math.floor(days / 30) !== 1 ? 's' : ''} ago`;
    return `${Math.floor(days / 365)} year${Math.floor(days / 365) !== 1 ? 's' : ''} ago`;
}

/**
 * Format number with commas
 */
function formatNumber(number, decimals = 0) {
    if (number === null || number === undefined) return 'N/A';
    return Number(number).toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

/**
 * Format bytes to human readable
 */
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    if (!bytes) return 'N/A';

    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB'];

    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

/**
 * Format currency
 */
function formatCurrency(amount, currency = 'USD') {
    if (amount === null || amount === undefined) return 'N/A';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

/**
 * Format percentage
 */
function formatPercent(value, decimals = 1) {
    if (value === null || value === undefined) return 'N/A';
    return `${Number(value).toFixed(decimals)}%`;
}

// =============================================================================
// VALIDATION
// =============================================================================

/**
 * Validate email address
 */
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(String(email).toLowerCase());
}

/**
 * Validate password strength
 */
function validatePassword(password) {
    const minLength = 8;
    const hasUpper = /[A-Z]/.test(password);
    const hasLower = /[a-z]/.test(password);
    const hasNumber = /\d/.test(password);
    const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password);

    const errors = [];
    if (password.length < minLength) errors.push(`At least ${minLength} characters`);
    if (!hasUpper) errors.push('One uppercase letter');
    if (!hasLower) errors.push('One lowercase letter');
    if (!hasNumber) errors.push('One number');
    if (!hasSpecial) errors.push('One special character');

    return {
        valid: errors.length === 0,
        errors: errors
    };
}

/**
 * Validate URL
 */
function validateURL(url) {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}

// =============================================================================
// LOCAL STORAGE HELPERS
// =============================================================================

/**
 * Save to localStorage with JSON stringify
 */
function saveToStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
        return true;
    } catch (error) {
        console.error('Error saving to localStorage:', error);
        return false;
    }
}

/**
 * Load from localStorage with JSON parse
 */
function loadFromStorage(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
        console.error('Error loading from localStorage:', error);
        return defaultValue;
    }
}

/**
 * Remove from localStorage
 */
function removeFromStorage(key) {
    try {
        localStorage.removeItem(key);
        return true;
    } catch (error) {
        console.error('Error removing from localStorage:', error);
        return false;
    }
}

// =============================================================================
// DEBOUNCE & THROTTLE
// =============================================================================

/**
 * Debounce function execution
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Throttle function execution
 */
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// =============================================================================
// COPY TO CLIPBOARD
// =============================================================================

/**
 * Copy text to clipboard
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast('Copied!', 'Text copied to clipboard', 'success');
        return true;
    } catch (error) {
        console.error('Failed to copy:', error);
        showToast('Copy Failed', 'Could not copy to clipboard', 'error');
        return false;
    }
}

// =============================================================================
// TABLE HELPERS
// =============================================================================

/**
 * Create sortable table
 */
function makeSortable(table) {
    const headers = table.querySelectorAll('th[data-sortable]');
    
    headers.forEach((header, index) => {
        header.style.cursor = 'pointer';
        header.style.userSelect = 'none';
        
        // Add sort icon
        if (!header.querySelector('.sort-icon')) {
            const icon = document.createElement('span');
            icon.className = 'sort-icon';
            icon.textContent = ' ⇅';
            icon.style.opacity = '0.3';
            header.appendChild(icon);
        }

        header.addEventListener('click', () => {
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const currentDir = header.getAttribute('data-sort-dir') || 'asc';
            const newDir = currentDir === 'asc' ? 'desc' : 'asc';

            // Remove sort indicators from all headers
            headers.forEach(h => {
                h.removeAttribute('data-sort-dir');
                const icon = h.querySelector('.sort-icon');
                if (icon) icon.textContent = ' ⇅';
            });

            // Set new sort direction
            header.setAttribute('data-sort-dir', newDir);
            const icon = header.querySelector('.sort-icon');
            if (icon) icon.textContent = newDir === 'asc' ? ' ↑' : ' ↓';

            // Sort rows
            rows.sort((a, b) => {
                const aValue = a.children[index].textContent.trim();
                const bValue = b.children[index].textContent.trim();
                
                // Try numeric sort
                const aNum = parseFloat(aValue);
                const bNum = parseFloat(bValue);
                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return newDir === 'asc' ? aNum - bNum : bNum - aNum;
                }

                // String sort
                return newDir === 'asc' 
                    ? aValue.localeCompare(bValue)
                    : bValue.localeCompare(aValue);
            });

            // Reappend sorted rows
            rows.forEach(row => tbody.appendChild(row));
        });
    });
}

// =============================================================================
// SEARCH/FILTER HELPERS
// =============================================================================

/**
 * Filter table rows by search term
 */
function filterTable(table, searchTerm) {
    const rows = table.querySelectorAll('tbody tr');
    const term = searchTerm.toLowerCase();

    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(term) ? '' : 'none';
    });
}

// =============================================================================
// EXPORT FUNCTIONS
// =============================================================================

/**
 * Export table to CSV
 */
function exportTableToCSV(table, filename = 'export.csv') {
    const rows = table.querySelectorAll('tr');
    const csv = Array.from(rows).map(row => {
        const cells = Array.from(row.querySelectorAll('th, td'));
        return cells.map(cell => `"${cell.textContent.trim()}"`).join(',');
    }).join('\n');

    downloadFile(csv, filename, 'text/csv');
}

/**
 * Download file
 */
function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

// =============================================================================
// INITIALIZATION
// =============================================================================

// Run when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Cogniware Core Utilities Loaded');
});

// Export for use in other modules (if using modules)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        CONFIG,
        getAuthToken,
        getCurrentUser,
        isAuthenticated,
        hasRole,
        logout,
        requireAuth,
        apiRequest,
        apiGet,
        apiPost,
        apiPut,
        apiDelete,
        showToast,
        showLoading,
        hideLoading,
        showConfirm,
        formatDate,
        formatNumber,
        formatBytes,
        formatCurrency,
        formatPercent,
        validateEmail,
        validatePassword,
        validateURL,
        saveToStorage,
        loadFromStorage,
        removeFromStorage,
        debounce,
        throttle,
        copyToClipboard,
        makeSortable,
        filterTable,
        exportTableToCSV,
        downloadFile
    };
}

