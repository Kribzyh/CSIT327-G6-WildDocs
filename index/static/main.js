// WildDocs Main JavaScript

/**
 * Initialize the application when DOM is ready
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('WildDocs application initialized');
    
    // Initialize all components
    initializeToasts();
    initializeFormValidation();
    initializePageTransitions();
    initializeNavigationHighlight();
});

/**
 * Initialize Bootstrap toast notifications
 */
function initializeToasts() {
    // Auto-show and hide toasts
    const toasts = document.querySelectorAll('.toast');
    toasts.forEach(function(toast) {
        // Show toast
        $(toast).toast('show');
        
        // Auto-hide after 5 seconds
        setTimeout(function() {
            $(toast).toast('hide');
        }, 5000);
    });
    
    // Close button functionality
    document.querySelectorAll('.toast .close').forEach(function(closeBtn) {
        closeBtn.addEventListener('click', function() {
            const toast = this.closest('.toast');
            $(toast).toast('hide');
        });
    });
}

/**
 * Initialize form validation
 */
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Show error toast
                showToast('Please fill in all required fields correctly.', 'error');
            }
            
            form.classList.add('was-validated');
        });
    });
}

/**
 * Initialize page transitions
 */
function initializePageTransitions() {
    // Add transition class to main content
    const mainContent = document.querySelector('main');
    if (mainContent) {
        mainContent.classList.add('page-transition');
    }
}

/**
 * Highlight current navigation item
 */
function initializeNavigationHighlight() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    navLinks.forEach(function(link) {
        const linkPath = new URL(link.href).pathname;
        if (linkPath === currentPath) {
            link.parentElement.classList.add('active');
        } else {
            link.parentElement.classList.remove('active');
        }
    });
}

/**
 * Show a toast notification
 * @param {string} message - The message to display
 * @param {string} type - The type of toast (success, error, warning, info)
 */
function showToast(message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container') || createToastContainer();
    
    const toastId = 'toast-' + Date.now();
    const toastHTML = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true" data-delay="5000">
            <div class="toast-header">
                <strong class="mr-auto">
                    ${getToastTitle(type)}
                </strong>
                <button type="button" class="ml-2 mb-1 close" data-dismiss="toast" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    
    const newToast = document.getElementById(toastId);
    $(newToast).toast('show');
    
    // Auto-remove after hiding
    $(newToast).on('hidden.bs.toast', function() {
        this.remove();
    });
}

/**
 * Create toast container if it doesn't exist
 */
function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
}

/**
 * Get toast title based on type
 * @param {string} type - The type of toast
 * @returns {string} The title for the toast
 */
function getToastTitle(type) {
    const titles = {
        'success': 'Success',
        'error': 'Error',
        'warning': 'Warning',
        'info': 'Info'
    };
    return titles[type] || 'Notification';
}

/**
 * Loading spinner utilities
 */
const LoadingSpinner = {
    show: function(element) {
        if (element) {
            element.innerHTML = '<span class="spinner"></span> Loading...';
            element.disabled = true;
        }
    },
    
    hide: function(element, originalText = '') {
        if (element) {
            element.innerHTML = originalText;
            element.disabled = false;
        }
    }
};

/**
 * AJAX utility functions
 */
const Ajax = {
    get: async function(url) {
        try {
            const response = await fetch(url);
            return await response.json();
        } catch (error) {
            console.error('AJAX GET error:', error);
            showToast('An error occurred while fetching data.', 'error');
            throw error;
        }
    },
    
    post: async function(url, data) {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify(data)
            });
            return await response.json();
        } catch (error) {
            console.error('AJAX POST error:', error);
            showToast('An error occurred while sending data.', 'error');
            throw error;
        }
    }
};

/**
 * Get CSRF token for Django forms
 */
function getCSRFToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return cookieValue || '';
}

/**
 * Utility functions
 */
const Utils = {
    formatDate: function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    },
    
    debounce: function(func, wait) {
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
};

// Global error handler
window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
    // Only show toast for network errors or critical issues
    if (event.error && event.error.message.includes('fetch')) {
        showToast('A network error occurred. Please check your connection.', 'error');
    }
});

// Export for use in other scripts
window.WildDocs = {
    showToast,
    LoadingSpinner,
    Ajax,
    Utils
};