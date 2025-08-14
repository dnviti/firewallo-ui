/**
 * Firewallo UI - Common JavaScript Utilities
 * Provides shared functionality across the web interface
 */

// Global configuration
const FirewalloUI = {
    config: {
        apiBaseUrl: '/api',
        refreshInterval: 60000, // 1 minute default
        requestTimeout: 10000,  // 10 seconds
        maxRetries: 3
    },

    // Store for managing application state
    state: {
        user: null,
        notifications: [],
        isLoading: false
    }
};

/**
 * API Request Helper
 */
class ApiClient {
    constructor(baseUrl = FirewalloUI.config.apiBaseUrl) {
        this.baseUrl = baseUrl;
        this.defaultHeaders = {
            'Content-Type': 'application/json'
        };
    }

    // Get authentication token from localStorage or cookies
    getAuthToken() {
        return localStorage.getItem('access_token') ||
               this.getCookie('access_token');
    }

    // Set authorization header if token exists
    getHeaders(customHeaders = {}) {
        const headers = { ...this.defaultHeaders, ...customHeaders };
        const token = this.getAuthToken();

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        return headers;
    }

    // Generic request method
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            timeout: FirewalloUI.config.requestTimeout,
            ...options,
            headers: this.getHeaders(options.headers)
        };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }

            return await response.text();
        } catch (error) {
            console.error(`API request failed: ${endpoint}`, error);
            throw error;
        }
    }

    // HTTP method shortcuts
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url, { method: 'GET' });
    }

    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    // Upload file
    async upload(endpoint, formData) {
        return this.request(endpoint, {
            method: 'POST',
            body: formData,
            headers: {} // Let browser set content-type for FormData
        });
    }

    // Utility method to get cookie value
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) {
            return parts.pop().split(';').shift();
        }
        return null;
    }
}

// Global API client instance
const api = new ApiClient();

/**
 * Notification System
 */
class NotificationManager {
    constructor() {
        this.container = null;
        this.notifications = [];
        this.init();
    }

    init() {
        // Create notification container if it doesn't exist
        if (!document.getElementById('notification-container')) {
            this.container = document.createElement('div');
            this.container.id = 'notification-container';
            this.container.className = 'position-fixed top-0 end-0 p-3';
            this.container.style.zIndex = '1055';
            document.body.appendChild(this.container);
        } else {
            this.container = document.getElementById('notification-container');
        }
    }

    show(message, type = 'info', duration = 5000) {
        const id = 'notification-' + Date.now();
        const notification = this.createNotification(id, message, type);

        this.container.appendChild(notification);
        this.notifications.push({ id, element: notification });

        // Show notification with animation
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);

        // Auto-dismiss
        if (duration > 0) {
            setTimeout(() => {
                this.dismiss(id);
            }, duration);
        }

        return id;
    }

    createNotification(id, message, type) {
        const icons = {
            success: 'bi-check-circle',
            error: 'bi-exclamation-triangle',
            warning: 'bi-exclamation-circle',
            info: 'bi-info-circle'
        };

        const colors = {
            success: 'alert-success',
            error: 'alert-danger',
            warning: 'alert-warning',
            info: 'alert-info'
        };

        const notification = document.createElement('div');
        notification.id = id;
        notification.className = `alert ${colors[type]} alert-dismissible fade`;
        notification.setAttribute('role', 'alert');

        notification.innerHTML = `
            <i class="bi ${icons[type]} me-2"></i>
            <span>${message}</span>
            <button type="button" class="btn-close" data-bs-dismiss="alert" onclick="notifications.dismiss('${id}')"></button>
        `;

        return notification;
    }

    dismiss(id) {
        const notification = document.getElementById(id);
        if (notification) {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
                this.notifications = this.notifications.filter(n => n.id !== id);
            }, 150);
        }
    }

    dismissAll() {
        this.notifications.forEach(n => this.dismiss(n.id));
    }

    // Convenience methods
    success(message, duration) { return this.show(message, 'success', duration); }
    error(message, duration) { return this.show(message, 'error', duration); }
    warning(message, duration) { return this.show(message, 'warning', duration); }
    info(message, duration) { return this.show(message, 'info', duration); }
}

// Global notification manager
const notifications = new NotificationManager();

/**
 * Loading State Manager
 */
class LoadingManager {
    constructor() {
        this.activeLoaders = new Set();
    }

    show(element = document.body, message = 'Loading...') {
        const loaderId = 'loader-' + Date.now();
        const loader = this.createLoader(loaderId, message);

        if (element === document.body) {
            document.body.appendChild(loader);
        } else {
            element.style.position = 'relative';
            element.appendChild(loader);
        }

        this.activeLoaders.add(loaderId);
        return loaderId;
    }

    createLoader(id, message) {
        const loader = document.createElement('div');
        loader.id = id;
        loader.className = 'loading-overlay fade-in';
        loader.innerHTML = `
            <div class="text-center">
                <div class="spinner-border text-primary mb-3" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <div class="text-muted">${message}</div>
            </div>
        `;
        return loader;
    }

    hide(loaderId) {
        const loader = document.getElementById(loaderId);
        if (loader) {
            loader.classList.remove('fade-in');
            setTimeout(() => {
                if (loader.parentNode) {
                    loader.parentNode.removeChild(loader);
                }
            }, 150);
            this.activeLoaders.delete(loaderId);
        }
    }

    hideAll() {
        this.activeLoaders.forEach(id => this.hide(id));
    }
}

// Global loading manager
const loading = new LoadingManager();

/**
 * Form Validation Utilities
 */
class FormValidator {
    constructor(form) {
        this.form = form;
        this.rules = {};
        this.errors = {};
    }

    addRule(fieldName, validator, message) {
        if (!this.rules[fieldName]) {
            this.rules[fieldName] = [];
        }
        this.rules[fieldName].push({ validator, message });
        return this;
    }

    validate() {
        this.errors = {};
        let isValid = true;

        for (const [fieldName, rules] of Object.entries(this.rules)) {
            const field = this.form.querySelector(`[name="${fieldName}"]`);
            if (!field) continue;

            const value = field.value.trim();

            for (const rule of rules) {
                if (!rule.validator(value, field)) {
                    this.errors[fieldName] = rule.message;
                    this.showFieldError(field, rule.message);
                    isValid = false;
                    break;
                }
            }

            if (!this.errors[fieldName]) {
                this.clearFieldError(field);
            }
        }

        return isValid;
    }

    showFieldError(field, message) {
        field.classList.add('is-invalid');

        let feedback = field.parentNode.querySelector('.invalid-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            field.parentNode.appendChild(feedback);
        }
        feedback.textContent = message;
    }

    clearFieldError(field) {
        field.classList.remove('is-invalid');
        const feedback = field.parentNode.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.remove();
        }
    }

    // Common validation rules
    static rules = {
        required: (value) => value.length > 0,
        email: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
        minLength: (min) => (value) => value.length >= min,
        maxLength: (max) => (value) => value.length <= max,
        numeric: (value) => /^\d+$/.test(value),
        alphanumeric: (value) => /^[a-zA-Z0-9]+$/.test(value),
        url: (value) => {
            try {
                new URL(value);
                return true;
            } catch {
                return false;
            }
        }
    };
}

/**
 * Data Formatting Utilities
 */
const formatters = {
    // Format bytes to human readable string
    bytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    },

    // Format number with thousands separator
    number(num, locale = 'en-US') {
        return new Intl.NumberFormat(locale).format(num);
    },

    // Format date/time
    dateTime(date, options = {}) {
        const defaultOptions = {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        return new Date(date).toLocaleDateString('en-US', { ...defaultOptions, ...options });
    },

    // Format relative time (e.g., "2 hours ago")
    relativeTime(date) {
        const now = new Date();
        const diff = now - new Date(date);
        const seconds = Math.floor(diff / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);

        if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
        if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
        if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
        return 'Just now';
    },

    // Format duration in seconds to human readable
    duration(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;

        if (hours > 0) {
            return `${hours}h ${minutes}m ${secs}s`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    },

    // Format percentage
    percentage(value, decimals = 1) {
        return `${(value * 100).toFixed(decimals)}%`;
    }
};

/**
 * Local Storage Utilities
 */
const storage = {
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.error('Failed to save to localStorage:', error);
        }
    },

    get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Failed to read from localStorage:', error);
            return defaultValue;
        }
    },

    remove(key) {
        try {
            localStorage.removeItem(key);
        } catch (error) {
            console.error('Failed to remove from localStorage:', error);
        }
    },

    clear() {
        try {
            localStorage.clear();
        } catch (error) {
            console.error('Failed to clear localStorage:', error);
        }
    }
};

/**
 * Theme Management
 */
const theme = {
    init() {
        const savedTheme = storage.get('theme');
        if (savedTheme) {
            this.set(savedTheme);
        } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
            this.set('dark');
        }
    },

    set(themeName) {
        document.documentElement.setAttribute('data-theme', themeName);
        storage.set('theme', themeName);
    },

    toggle() {
        const current = document.documentElement.getAttribute('data-theme');
        this.set(current === 'dark' ? 'light' : 'dark');
    }
};

/**
 * Utility Functions
 */
const utils = {
    // Debounce function calls
    debounce(func, wait, immediate = false) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func(...args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func(...args);
        };
    },

    // Throttle function calls
    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    // Generate random ID
    generateId(prefix = 'id') {
        return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    },

    // Deep clone object
    clone(obj) {
        return JSON.parse(JSON.stringify(obj));
    },

    // Check if object is empty
    isEmpty(obj) {
        return Object.keys(obj).length === 0;
    },

    // Capitalize first letter
    capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    },

    // Copy text to clipboard
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            notifications.success('Copied to clipboard');
        } catch (error) {
            console.error('Failed to copy to clipboard:', error);
            notifications.error('Failed to copy to clipboard');
        }
    },

    // Download data as file
    downloadFile(data, filename, type = 'application/json') {
        const blob = new Blob([data], { type });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }
};

/**
 * Initialize on DOM content loaded
 */
document.addEventListener('DOMContentLoaded', function() {
    // Initialize theme
    theme.init();

    // Set up global error handler
    window.addEventListener('unhandledrejection', function(event) {
        console.error('Unhandled promise rejection:', event.reason);
        notifications.error('An unexpected error occurred');
    });

    // Set up CSRF token for forms (if needed)
    const csrfToken = document.querySelector('meta[name="csrf-token"]');
    if (csrfToken) {
        api.defaultHeaders['X-CSRF-Token'] = csrfToken.getAttribute('content');
    }

    // Add loading indicators to forms
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';

                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }, 5000);
            }
        });
    });

    console.log('Firewallo UI initialized');
});

// Export globals for use in other scripts
window.FirewalloUI = FirewalloUI;
window.api = api;
window.notifications = notifications;
window.loading = loading;
window.FormValidator = FormValidator;
window.formatters = formatters;
window.storage = storage;
window.theme = theme;
window.utils = utils;
