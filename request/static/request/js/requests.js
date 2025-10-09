// Request-specific JavaScript functionality

// Document ready
document.addEventListener('DOMContentLoaded', function() {
    initializeRequestFunctionality();
});

function initializeRequestFunctionality() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize table search
    initializeTableSearch();
    
    // Initialize status filters
    initializeStatusFilters();
    
    // Initialize print functionality
    initializePrintFunctionality();
    
    // Initialize form validation
    initializeFormValidation();
}

// Table search functionality
function initializeTableSearch() {
    const searchInput = document.getElementById('tableSearch');
    if (!searchInput) return;
    
    searchInput.addEventListener('keyup', function() {
        const filter = this.value.toLowerCase();
        const table = document.querySelector('.request-table tbody');
        const rows = table.getElementsByTagName('tr');
        
        for (let i = 0; i < rows.length; i++) {
            const row = rows[i];
            const cells = row.getElementsByTagName('td');
            let found = false;
            
            for (let j = 0; j < cells.length; j++) {
                const cell = cells[j];
                if (cell.textContent.toLowerCase().indexOf(filter) > -1) {
                    found = true;
                    break;
                }
            }
            
            row.style.display = found ? '' : 'none';
        }
    });
}

// Status filter functionality
function initializeStatusFilters() {
    const filterButtons = document.querySelectorAll('.status-filter');
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const status = this.dataset.status;
            filterTableByStatus(status);
            
            // Update active state
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
        });
    });
}

function filterTableByStatus(status) {
    const table = document.querySelector('.request-table tbody');
    if (!table) return;
    
    const rows = table.getElementsByTagName('tr');
    
    for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        const statusCell = row.querySelector('.status-badge');
        
        if (status === 'all' || !statusCell) {
            row.style.display = '';
        } else {
            const rowStatus = statusCell.textContent.toLowerCase().trim();
            row.style.display = rowStatus === status.toLowerCase() ? '' : 'none';
        }
    }
}

// Print functionality
function initializePrintFunctionality() {
    // Print pickup slip
    window.printPickupSlip = function(requestId) {
        const url = `/request/approved/pickup-slip/${requestId}/`;
        const printWindow = window.open(url, '_blank', 'width=800,height=600');
        
        printWindow.onload = function() {
            setTimeout(() => {
                printWindow.print();
            }, 1000);
        };
    };
    
    // Download receipt
    window.downloadReceipt = function(requestId) {
        const url = `/request/completed/receipt/${requestId}/`;
        window.open(url, '_blank');
    };
    
    // Print current page
    window.printPage = function() {
        window.print();
    };
}

// Form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Focus on first invalid field
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                }
            }
            
            form.classList.add('was-validated');
        });
    });
}

// Request cancellation
function cancelRequest(requestId) {
    if (!confirm('Are you sure you want to cancel this request? This action cannot be undone.')) {
        return;
    }
    
    // Show loading state
    const button = event.target;
    const originalText = button.innerHTML;
    button.innerHTML = '<span class="loading-spinner"></span> Cancelling...';
    button.disabled = true;
    
    // Make AJAX request
    fetch(`/request/pending/cancel/${requestId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', 'Request cancelled successfully.');
            setTimeout(() => {
                location.reload();
            }, 1500);
        } else {
            showAlert('danger', data.error || 'Failed to cancel request.');
            button.innerHTML = originalText;
            button.disabled = false;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('danger', 'An error occurred while cancelling the request.');
        button.innerHTML = originalText;
        button.disabled = false;
    });
}

// Request detail view functions
function viewRequestDetail(requestId) {
    window.location.href = `/request/detail/${requestId}/`;
}

function viewRequestTimeline(requestId) {
    window.location.href = `/request/detail/${requestId}/timeline/`;
}

// Utility functions
function getCsrfToken() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    return csrfToken ? csrfToken.value : '';
}

function showAlert(type, message) {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at top of main content
    const main = document.querySelector('main') || document.querySelector('.container-fluid');
    if (main) {
        main.insertBefore(alertDiv, main.firstChild);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

// Date formatting
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Status badge color mapping
function getStatusBadgeClass(status) {
    const statusMap = {
        'pending': 'status-pending',
        'approved': 'status-approved',
        'completed': 'status-completed',
        'cancelled': 'status-cancelled'
    };
    
    return statusMap[status.toLowerCase()] || 'status-pending';
}

// Export functions for external use
window.RequestUtils = {
    cancelRequest,
    viewRequestDetail,
    viewRequestTimeline,
    printPickupSlip,
    downloadReceipt,
    showAlert,
    formatDate,
    formatDateTime,
    getStatusBadgeClass
};

// Initialize animations
function initializeAnimations() {
    // Fade in elements with fade-in class
    const fadeElements = document.querySelectorAll('.fade-in');
    fadeElements.forEach((element, index) => {
        element.style.animationDelay = `${index * 0.1}s`;
    });
    
    // Slide in elements with slide-in class
    const slideElements = document.querySelectorAll('.slide-in');
    slideElements.forEach((element, index) => {
        element.style.animationDelay = `${index * 0.1}s`;
    });
}

// Call animation initialization
document.addEventListener('DOMContentLoaded', initializeAnimations);

// Auto-refresh functionality for pending requests
function initializeAutoRefresh() {
    if (window.location.pathname.includes('/pending/')) {
        // Refresh every 30 seconds for pending requests
        setInterval(() => {
            const currentTime = new Date().toLocaleTimeString();
            console.log(`Auto-refresh at ${currentTime}`);
            
            // Check for new notifications or status updates
            checkForUpdates();
        }, 30000);
    }
}

function checkForUpdates() {
    // This would make an AJAX call to check for updates
    // Implementation would depend on your backend notification system
    fetch('/api/check-updates/', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.hasUpdates) {
            showAlert('info', 'New updates available. Refreshing page...');
            setTimeout(() => {
                location.reload();
            }, 2000);
        }
    })
    .catch(error => {
        console.log('Update check failed:', error);
    });
}

// Initialize auto-refresh on page load
document.addEventListener('DOMContentLoaded', initializeAutoRefresh);