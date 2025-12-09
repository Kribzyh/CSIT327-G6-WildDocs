// Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const currentDate = getPhilippinesDate();
    updateHeaderDate(currentDate);
    updateWelcomeDate(currentDate);
    initSidebarInteractions();
    initRequestForm();
    initNotificationIcon();
    initSettingsIcon();
    initStatCardNavigation();
    initStatCardHoverEffects();
    initRecentRequestsFilter();
    initAllRequestsFilter();
    // Refresh notifications every 3 seconds for real-time updates
    globalThis.setInterval(refreshNotifications, 3000);
    // Also refresh immediately on page load
    refreshNotifications();
    console.log('Dashboard loaded successfully - auto-refresh every 3 seconds');
    console.log('Philippines date:', currentDate.toLocaleDateString('en-US', headerDateOptions()));
});

function initAllRequestsFilter() {
    const searchInput = document.getElementById('allRequestsSearch');
    const table = document.querySelector('.admin-requests-table');

    if (!searchInput || !table) {
        return;
    }

    const dataRows = Array.from(table.querySelectorAll('tbody tr[data-request-id]'));
    const emptyRow = document.getElementById('allRequestsEmptyRow');
    const visibleCountTarget = document.getElementById('allRequestsVisibleCount');
    const totalRows = dataRows.length;

    const updateVisibleLabel = visibleCount => {
        if (!visibleCountTarget) return;
        const base = totalRows || dataRows.length || 0;
        visibleCountTarget.textContent = base ? `${visibleCount} of ${base} shown` : '0 of 0 shown';
    };

    const applyFilter = () => {
        const query = searchInput.value.trim().toLowerCase();
        let visibleCount = 0;

        for (const row of dataRows) {
            const haystack = (row.dataset.documentKey ? `${row.textContent} ${row.dataset.documentKey}` : row.textContent || '').toLowerCase();
            const matches = !query || haystack.includes(query);
            row.style.display = matches ? '' : 'none';
            if (matches) visibleCount += 1;
        }

        if (emptyRow) {
            if (dataRows.length === 0) {
                emptyRow.style.display = '';
            } else {
                emptyRow.style.display = visibleCount === 0 ? '' : 'none';
            }
        }

        updateVisibleLabel(visibleCount);
    };

    searchInput.addEventListener('input', applyFilter);
    searchInput.addEventListener('keydown', event => {
        if (event.key === 'Escape' && searchInput.value) {
            searchInput.value = '';
            applyFilter();
        }
    });

    applyFilter();
}

function getPhilippinesDate() {
    const philippinesDate = new Date().toLocaleString('en-US', { timeZone: 'Asia/Manila' });
    return new Date(philippinesDate);
}

function headerDateOptions() {
    return {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    };
}

function updateHeaderDate(currentDate) {
    const dateElement = document.getElementById('currentDate');
    if (!dateElement) {
        return;
    }
    dateElement.textContent = currentDate.toLocaleDateString('en-US', headerDateOptions());
}

function updateWelcomeDate(currentDate) {
    const welcomeDateElement = document.getElementById('welcomeDate');
    if (!welcomeDateElement) {
        return;
    }

    const day = currentDate.getDate();
    const month = currentDate.toLocaleDateString('en-US', { month: 'long' });
    const year = currentDate.getFullYear();
    welcomeDateElement.textContent = `${day}${ordinal(day)} day of ${month}, ${year}`;
}

function ordinal(day) {
    if (day > 3 && day < 21) {
        return 'th';
    }

    switch (day % 10) {
        case 1:
            return 'st';
        case 2:
            return 'nd';
        case 3:
            return 'rd';
        default:
            return 'th';
    }
}

function initSidebarInteractions() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    const navLinks = document.querySelectorAll('.sidebar .nav-item');
    const collapseViewport = globalThis.matchMedia('(max-width: 991px)');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            const isOpen = sidebar.classList.toggle('show');
            document.body.classList.toggle('sidebar-open', isOpen);
        });
    }

    function collapseSidebarIfNeeded() {
        if (collapseViewport.matches && sidebar) {
            sidebar.classList.remove('show');
            document.body.classList.remove('sidebar-open');
        }
    }

    for (const link of navLinks) {
        link.addEventListener('click', collapseSidebarIfNeeded);
    }
}

function initRequestForm() {
    const form = document.getElementById('documentRequestForm');
    if (!form) {
        return;
    }

    const submitBtn = document.getElementById('submitBtn');
    const submitText = document.getElementById('submitText');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const csrfToken = form.querySelector('input[name="csrfmiddlewaretoken"]')?.value;

    form.addEventListener('submit', async event => {
        event.preventDefault();
        setSubmitState(true);

        try {
            const formData = new FormData(form);
            const response = await fetch(form.action || globalThis.location.href, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {})
                },
                body: formData
            });
            let data;
            try {
                data = await response.json();
            } catch (jsonError) {
                console.error('Invalid JSON response', jsonError);
                throw new Error('Unexpected response from server.');
            }
            if (!response.ok) {
                throw new Error(data.error || 'Unable to submit request.');
            }

            if (data.success) {
                form.reset();
                updatePendingCount(data.pending_count);
                prependRecentRequest(data.request);
                showFormAlert('success', data.message || 'Request submitted successfully!');
            } else {
                showFormAlert('danger', data.error || 'Failed to submit request.');
            }
        } catch (error) {
            console.error('Document request submission failed:', error);
            showFormAlert('danger', error.message || 'Network error. Please try again.');
        } finally {
            setSubmitState(false);
        }
    });

    function setSubmitState(isSubmitting) {
        if (submitBtn) {
            submitBtn.disabled = isSubmitting;
        }
        if (submitText) {
            submitText.textContent = isSubmitting ? 'Submitting...' : 'Submit Request';
        }
        if (loadingSpinner) {
            loadingSpinner.style.display = isSubmitting ? 'inline-block' : 'none';
        }
    }
}

async function refreshNotifications() {
    try {
        const response = await fetch('/api/notifications/', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            },
            credentials: 'same-origin'
        });
        
        if (!response.ok) {
            console.warn('Failed to fetch notifications:', response.status);
            return;
        }
        
        const data = await response.json();
        if (!data.success) {
            console.warn('Notifications fetch unsuccessful:', data.error);
            return;
        }
        
        // Update notifications list
        renderNotifications(data.notifications);
        
        // Update stat cards if data is available
        if (data.stats) {
            updateStatCards(data.stats);
        }
        
        // Update recent requests if data is available
        if (data.recent_requests) {
            renderRecentRequests(data.recent_requests);
        }
        
    } catch (error) {
        console.warn('Error refreshing notifications:', error);
    }
}

function renderNotifications(notifications) {
    const notificationsList = document.querySelector('.notifications-list');
    if (!notificationsList) {
        return;
    }
    
    if (!notifications || notifications.length === 0) {
        notificationsList.innerHTML = `
            <div class="notification-empty">
                <i class="fas fa-bell-slash"></i>
                <p class="mb-1 fw-semibold">No notifications yet</p>
                <small>New updates will appear here once your requests move forward.</small>
            </div>
        `;
        return;
    }
    
    const notificationsHtml = notifications.map(notif => {
        const status = notif.request?.status || '';
        const documentName = notif.request?.document_name || 'Unknown';
        
        // Determine notification style based on status
        let notifClass = 'notification-info';
        let iconClass = 'fa-info-circle';
        
        if (status.includes('Approved') || status.includes('Ready')) {
            notifClass = 'notification-ready';
            iconClass = 'fa-check-circle';
        } else if (status === 'Completed') {
            notifClass = 'notification-complete';
            iconClass = 'fa-clipboard-check';
        } else if (status === 'Rejected' || status === 'Cancelled') {
            notifClass = 'notification-overdue';
            iconClass = 'fa-exclamation-triangle';
        } else if (status.includes('Requirements')) {
            notifClass = 'notification-info';
            iconClass = 'fa-file-alt';
        } else if (status.includes('Payment')) {
            notifClass = 'notification-info';
            iconClass = 'fa-credit-card';
        }
        
        return `
            <div class="notification-item ${notifClass}">
                <div class="notification-icon">
                    <i class="fas ${iconClass}"></i>
                </div>
                <div class="notification-body">
                    <div class="notification-date">${notif.date_sent}</div>
                    <div class="notification-title">
                        ${documentName} — ${status}
                    </div>
                    <div class="notification-text">${notif.message}</div>
                </div>
            </div>
        `;
    }).join('');
    
    notificationsList.innerHTML = notificationsHtml;
}

function updateStatCards(stats) {
    // Update pending count
    const pendingCountEl = document.getElementById('pendingCount');
    if (pendingCountEl && stats.pending_count !== undefined) {
        pendingCountEl.textContent = stats.pending_count;
    }
    
    // Update ready for pickup / approved count
    const approvedCountEl = document.getElementById('approvedCount');
    if (approvedCountEl && stats.ready_pickup_count !== undefined) {
        approvedCountEl.textContent = stats.ready_pickup_count;
    }
    
    // Update completed count
    const completedCountEl = document.getElementById('completedCount');
    if (completedCountEl && stats.completed_count !== undefined) {
        completedCountEl.textContent = stats.completed_count;
    }
}

function renderRecentRequests(requests) {
    const recentContainer = document.getElementById('recentRequestsContainer');
    if (!recentContainer) {
        return;
    }
    
    if (!requests || requests.length === 0) {
        recentContainer.innerHTML = `
            <div class="recent-item" id="noRecentRequests">
                <div class="recent-title">No recent requests</div>
                <div class="recent-status">Submit your first request above</div>
                <div class="recent-date">Get started today</div>
            </div>
        `;
        return;
    }
    
    const requestsHtml = requests.map(req => {
        // Determine status class
        let statusClass = '';
        const status = req.status || '';
        
        if (status.includes('Pending')) {
            statusClass = 'text-warning';
        } else if (status.includes('Approved') || status.includes('Ready')) {
            statusClass = 'text-info';
        } else if (status.includes('Completed')) {
            statusClass = 'text-success';
        } else if (status.includes('Rejected') || status.includes('Cancelled')) {
            statusClass = 'text-danger';
        } else if (status.includes('Requirements')) {
            statusClass = 'text-primary';
        } else if (status.includes('Payment')) {
            statusClass = 'text-warning';
        }
        
        return `
            <div class="recent-item">
                <div class="recent-title">${req.document_name}</div>
                <div class="recent-status">
                    <span class="${statusClass}">${req.status_label || req.status}</span>
                </div>
                <div class="recent-date">${req.date_requested}</div>
            </div>
        `;
    }).join('');
    
    recentContainer.innerHTML = requestsHtml;
}

function initNotificationIcon() {
    const notificationIcon = document.querySelector('.notification-icon');
    if (!notificationIcon) {
        return;
    }

    notificationIcon.addEventListener('click', function() {
        console.log('Show notifications');
    });
}

function initSettingsIcon() {
    const settingsIcon = document.querySelector('.settings-icon');
    if (!settingsIcon) {
        return;
    }

    settingsIcon.addEventListener('click', function() {
        globalThis.location.href = '/settings/';
    });
}

function showLoading(element) {
    const originalText = element.textContent;
    element.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
    element.disabled = true;

    return function hideLoading() {
        element.textContent = originalText;
        element.disabled = false;
    };
}

function initStatCardNavigation() {
    const statCards = document.querySelectorAll('.stat-card');
    for (const card of statCards) {
        if (card.classList.contains('recent-requests-card')) {
            continue;
        }

        card.style.cursor = 'pointer';
        card.addEventListener('click', function() {
            const header = this.querySelector('.stat-header').textContent;

            switch(header) {
                case 'Pending Requests':
                    globalThis.location.href = '/requests/pending/';
                    break;
                case 'Approved Requests':
                    globalThis.location.href = '/requested_documents/';
                    break;
                case 'Completed Requests':
                    globalThis.location.href = '/requests/completed/';
                    break;
            }
        });
    }
}

function initStatCardHoverEffects() {
    const statCards = document.querySelectorAll('.stat-card');
    for (const card of statCards) {
        if (card.classList.contains('recent-requests-card')) {
            continue;
        }

        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.boxShadow = '0 4px 15px rgba(0,0,0,0.15)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
        });
    }
}

function initRecentRequestsFilter() {
    const searchInput = document.getElementById('recentRequestsSearch');
    const table = document.getElementById('recentRequestsTable');

    if (!searchInput || !table) {
        return;
    }

    const dataRows = Array.from(table.querySelectorAll('tbody tr[data-filterable="true"]'));
    const emptyRow = document.getElementById('recentRequestsEmptyRow');
    const visibleCountTarget = document.getElementById('recentRequestsVisibleCount');
    const stageButtons = document.querySelectorAll('.stage-filter-btn');
    let activeStage = 'all';
    const totalRows = dataRows.length;

    const updateVisibleLabel = visibleCount => {
        if (!visibleCountTarget) {
            return;
        }
        const base = totalRows || dataRows.length || 0;
        visibleCountTarget.textContent = base ? `${visibleCount} of ${base} shown` : '0 of 0 shown';
    };

    const applyFilter = () => {
        const query = searchInput.value.trim().toLowerCase();
        let visibleCount = 0;

        dataRows.forEach(row => {
            const haystack = (row.dataset.filterValue || row.textContent || '').toLowerCase();
            const stageCategory = row.dataset.stageCategory || 'other';
            const stageKey = row.dataset.stageKey || '';
            let stageMatches = false;
            if (activeStage === 'all') {
                stageMatches = true;
            } else if (activeStage === 'requirements') {
                // Treat the 'requirements' stage as any request within the
                // requirements category (needed/submitted/issue). This ensures
                // items marked "Requirements Needed" and related requirement
                // statuses appear when the admin selects the Requirements Queue.
                stageMatches = stageCategory === 'requirements' || stageKey === 'requirements_needed';
            } else {
                stageMatches = stageCategory === activeStage;
            }
            const matches = (!query || haystack.includes(query)) && stageMatches;
            row.style.display = matches ? '' : 'none';
            if (matches) {
                visibleCount += 1;
            }
        });

        if (emptyRow) {
            if (dataRows.length === 0) {
                emptyRow.style.display = '';
            } else {
                emptyRow.style.display = visibleCount === 0 ? '' : 'none';
            }
        }

        updateVisibleLabel(visibleCount);
    };

    searchInput.addEventListener('input', applyFilter);
    searchInput.addEventListener('keydown', event => {
        if (event.key === 'Escape' && searchInput.value) {
            searchInput.value = '';
            applyFilter();
        }
    });

    for (const button of stageButtons) {
        button.addEventListener('click', () => {
            const nextStage = button.dataset.stageFilter || 'all';
            if (nextStage === activeStage) {
                return;
            }
            activeStage = nextStage;
            for (const btn of stageButtons) {
                btn.classList.toggle('active', btn === button);
            }
            applyFilter();
        });
    }

    applyFilter();

    // Document list removed — no dynamic document filter
}

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

function showFormAlert(type, message) {
    const requestSection = document.querySelector('.request-section');
    if (!requestSection) {
        return;
    }

    const existing = requestSection.querySelector('.alert');
    if (existing) {
        existing.remove();
    }

    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.role = 'alert';
    alert.textContent = message;
    alert.style.transition = 'opacity 0.3s ease';
    alert.style.opacity = '1';

    requestSection.querySelector('.section-title')?.insertAdjacentElement('afterend', alert) ?? requestSection.prepend(alert);

    setTimeout(() => {
        if (!alert.parentNode) {
            return;
        }
        alert.style.opacity = '0';
        alert.addEventListener('transitionend', () => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, { once: true });
    }, 2000);
}

function updatePendingCount(count) {
    if (typeof count !== 'number') {
        return;
    }
    const pendingCount = document.getElementById('pendingCount');
    if (pendingCount) {
        pendingCount.textContent = count;
    }
}

function prependRecentRequest(request) {
    if (!request) {
        return;
    }

    const container = document.getElementById('recentRequestsContainer');
    if (!container) {
        return;
    }

    const placeholder = document.getElementById('noRecentRequests');
    if (placeholder) {
        placeholder.remove();
    }

    const item = document.createElement('div');
    item.className = 'recent-item';
    item.innerHTML = `
        <div class="recent-title">${request.document_name}</div>
        <div class="recent-status">${formatRecentStatus(request.status)}</div>
        <div class="recent-date">Submitted ${request.date_requested}</div>
    `;

    container.prepend(item);

    const recentItems = container.querySelectorAll('.recent-item');
    if (recentItems.length > 3) {
        for (let i = 3; i < recentItems.length; i++) {
            recentItems[i].remove();
        }
    }
}

function formatRecentStatus(status) {
    if (!status) {
        return '';
    }

    const normalized = status.toLowerCase();
    if (normalized.includes('pending')) {
        return `<span class="text-warning">${status}</span>`;
    }
    if (normalized.includes('approved') || normalized.includes('pickup')) {
        return `<span class="text-info">${status}</span>`;
    }
    if (normalized.includes('complete')) {
        return `<span class="text-success">${status}</span>`;
    }
    return status;
}

globalThis.confirmLogout = function confirmLogout(event) {
    event.preventDefault();
    // Prefer the element that the handler was attached to; if not available,
    // try to find the nearest anchor element from the event target.
    const el = event.currentTarget || (event.target && event.target.closest && event.target.closest('a')) || event.target;
    let logoutUrl = null;
    try {
        logoutUrl = el?.getAttribute?.('href') ?? null;
    } catch (error_) {
        logoutUrl = null;
    }
    // Normalize common non-navigation hrefs to the actual logout endpoint.
    if (!logoutUrl || logoutUrl === '#' || logoutUrl.trim() === '') {
        logoutUrl = '/accounts/logout/';
    }

    if (globalThis.confirm('Are you sure you want to logout?')) {
        globalThis.location.href = logoutUrl;
    }
};