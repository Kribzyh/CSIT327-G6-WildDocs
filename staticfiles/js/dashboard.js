// Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Get current date in Philippines timezone
    const philippinesDate = new Date().toLocaleString("en-US", {timeZone: "Asia/Manila"});
    const currentDate = new Date(philippinesDate);
    
    // Set current date for header (if element exists)
    const options = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    };
    
    const dateElement = document.getElementById('currentDate');
    if (dateElement) {
        dateElement.textContent = currentDate.toLocaleDateString('en-US', options);
    }
    
    // Set date for welcome section with ordinal suffix (Philippines timezone)
    const welcomeDateElement = document.getElementById('welcomeDate');
    if (welcomeDateElement) {
        const day = currentDate.getDate();
        const month = currentDate.toLocaleDateString('en-US', { month: 'long' });
        const year = currentDate.getFullYear();
        
        // Add ordinal suffix
        const ordinal = (day) => {
            if (day > 3 && day < 21) return 'th';
            switch (day % 10) {
                case 1: return 'st';
                case 2: return 'nd';
                case 3: return 'rd';
                default: return 'th';
            }
        };
        
        welcomeDateElement.textContent = `${day}${ordinal(day)} day of ${month}, ${year}`;
    }

    // Mobile sidebar toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
    }
    
    // Handle document request form
    const requestForm = document.querySelector('.request-form');
    const requestSelect = document.querySelector('.request-select');
    const confirmBtn = document.querySelector('.btn-confirm');
    
    if (confirmBtn && requestSelect) {
        confirmBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            const selectedDocument = requestSelect.value;
            if (selectedDocument && selectedDocument !== 'Select type of document') {
                // Show confirmation dialog
                if (confirm(`Are you sure you want to request: ${requestSelect.options[requestSelect.selectedIndex].text}?`)) {
                    // Here you would typically send the request to the server
                    alert('Document request submitted successfully!');
                    requestSelect.value = '';
                }
            } else {
                alert('Please select a document type first.');
            }
        });
    }
    
    // Handle edit information button
    const editInfoBtn = document.querySelector('.btn-edit-info');
    if (editInfoBtn) {
        editInfoBtn.addEventListener('click', function() {
            // Redirect to profile edit page or show modal
            window.location.href = '/profile/edit/';
        });
    }
    
    // Auto-refresh notifications (optional)
    function refreshNotifications() {
        // This would typically fetch new notifications from the server
        console.log('Refreshing notifications...');
    }
    
    // Refresh notifications every 5 minutes
    setInterval(refreshNotifications, 300000);
    
    // Handle notification clicks
    const notificationIcon = document.querySelector('.notification-icon');
    if (notificationIcon) {
        notificationIcon.addEventListener('click', function() {
            // Show notifications dropdown or redirect to notifications page
            console.log('Show notifications');
        });
    }
    
    // Handle settings clicks
    const settingsIcon = document.querySelector('.settings-icon');
    if (settingsIcon) {
        settingsIcon.addEventListener('click', function() {
            // Show settings dropdown or redirect to settings page
            window.location.href = '/settings/';
        });
    }
    
    // Add loading states for async operations
    function showLoading(element) {
        const originalText = element.textContent;
        element.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
        element.disabled = true;
        
        return function hideLoading() {
            element.textContent = originalText;
            element.disabled = false;
        };
    }
    
    // Handle stat card clicks for navigation
    const statCards = document.querySelectorAll('.stat-card');
    statCards.forEach(card => {
        // Skip navigation for recent requests card - it's display only
        if (card.classList.contains('recent-requests-card')) {
            return;
        }
        
        card.style.cursor = 'pointer';
        card.addEventListener('click', function() {
            const header = this.querySelector('.stat-header').textContent;
            
            switch(header) {
                case 'Pending Requests':
                    window.location.href = '/requests/pending/';
                    break;
                case 'Approved Requests':
                    window.location.href = '/requests/approved/';
                    break;
                case 'Completed Requests':
                    window.location.href = '/requests/completed/';
                    break;
            }
        });
    });
    
    // Add hover effects
    statCards.forEach(card => {
        // Recent requests card has different hover behavior defined in CSS
        if (card.classList.contains('recent-requests-card')) {
            return;
        }
        
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.boxShadow = '0 4px 15px rgba(0,0,0,0.15)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
        });
    });
    
    console.log('Dashboard loaded successfully');
    console.log('Philippines date:', currentDate.toLocaleDateString('en-US', options));
});

// Utility functions
function formatDate(date) {
    // Format date in Philippines timezone
    const philippinesDate = new Date(date).toLocaleString("en-US", {timeZone: "Asia/Manila"});
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        timeZone: "Asia/Manila"
    }).format(new Date(philippinesDate));
}

function showToast(message, type = 'info') {
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show`;
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to page
    const container = document.querySelector('.dashboard-content') || document.body;
    container.insertBefore(toast, container.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 5000);
}