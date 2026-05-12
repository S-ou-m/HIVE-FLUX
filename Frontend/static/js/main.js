// Main JavaScript file for ERP CMS

document.addEventListener('DOMContentLoaded', () => {
    console.log('ERP CMS Frontend Initialized.');
    
    // Initialize Sidebar Engine
    if (document.getElementById('main-sidebar')) {
        window.sidebarEngine = new SidebarEngine();
    }
});

// HTMX CSRF Configuration
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.body.addEventListener('htmx:configRequest', (event) => {
    const csrftoken = getCookie('csrftoken');
    if (csrftoken) {
        event.detail.headers['X-CSRFToken'] = csrftoken;
    }
});

// Global Modal Control
function openModal() {
    const modalContainer = document.getElementById('modal-container');
    if (modalContainer) {
        modalContainer.classList.add('active');
    }
}

function closeModal() {
    const modalContainer = document.getElementById('modal-container');
    if (modalContainer) {
        modalContainer.classList.remove('active');
        modalContainer.innerHTML = '';
    }
}

// Side Panel Control
function openSidePanel(title = "Transaction Ledger") {
    const panel = document.getElementById('side-panel');
    const overlay = document.getElementById('side-panel-overlay');
    const titleEl = document.getElementById('side-panel-title');
    
    if (panel && overlay) {
        if (titleEl) titleEl.innerText = title;
        panel.classList.add('active');
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden'; // Lock background scroll
    }
}

function closeSidePanel() {
    const panel = document.getElementById('side-panel');
    const overlay = document.getElementById('side-panel-overlay');
    
    if (panel && overlay) {
        panel.classList.remove('active');
        overlay.classList.remove('active');
        document.body.style.overflow = ''; // Restore scroll
        
        // Clean content after animation
        setTimeout(() => {
            document.getElementById('side-panel-content').innerHTML = '';
        }, 400);
    }
}

/**
 * ELITE SIDEBAR INTELLIGENCE ENGINE
 * Handles: State Persistence, Hover Expansion, Search Navigation, and Keyboard Shortcuts
 */
class SidebarEngine {
    constructor() {
        this.sidebar = document.getElementById('main-sidebar');
        this.searchInput = document.getElementById('nav-search');
        this.navItems = this.sidebar.querySelectorAll('.nav-item');
        this.init();
    }

    init() {
        // Search Logic
        if (this.searchInput) {
            this.searchInput.addEventListener('input', (e) => this.filterNavigation(e.target.value));
        }

        // Navigation Active State Logic
        this.navItems.forEach(item => {
            item.addEventListener('click', (e) => this.handleActiveState(e.currentTarget));
        });

        // Global Keyboard Shortcuts (Ctrl+K)
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.focusSearch();
            }
        });

        this.initStatusPolling();
    }

    filterNavigation(query) {
        const q = query.toLowerCase().trim();
        
        this.navItems.forEach(item => {
            const title = item.getAttribute('data-nav-title')?.toLowerCase() || "";
            const text = item.querySelector('span')?.innerText.toLowerCase() || "";
            
            if (title.includes(q) || text.includes(q)) {
                item.style.display = 'flex';
                item.style.opacity = '1';
            } else {
                item.style.display = 'none';
                item.style.opacity = '0';
            }
        });

        // Hide empty groups
        this.sidebar.querySelectorAll('.nav-group').forEach(group => {
            const hasVisibleItems = Array.from(group.querySelectorAll('.nav-item')).some(i => i.style.display !== 'none');
            group.style.display = hasVisibleItems ? 'block' : 'none';
        });
    }

    focusSearch() {
        this.searchInput.focus();
    }

    handleActiveState(clickedItem) {
        // Remove active class from all items
        this.navItems.forEach(item => item.classList.remove('active'));
        
        // Add to clicked item
        clickedItem.classList.add('active');

        // Close mobile sidebar after navigation
        if (window.innerWidth <= 1024) {
            toggleMobileSidebar();
        }
    }

    initStatusPolling() {
        document.body.addEventListener('sessionCreated', () => {
            const liveBadge = document.getElementById('sidebar-live-session');
            if (liveBadge) liveBadge.style.display = 'inline-flex';
        });
    }
}

// Global Sidebar Toggle Control
function toggleSidebar() {
    const root = document.documentElement;
    const isCompact = root.classList.toggle('sidebar-compact-init');
    localStorage.setItem('sidebar_state', isCompact ? 'compact' : 'expanded');
    
    // Dispatch resize event to force charts to update if any
    window.dispatchEvent(new Event('resize'));
}

function toggleMobileSidebar() {
    const sidebar = document.getElementById('main-sidebar') || document.querySelector('.stu-sidebar') || document.querySelector('.dashboard-sidebar');
    const overlay = document.getElementById('mobile-sidebar-overlay');
    
    if (sidebar) {
        sidebar.classList.toggle('mobile-active');
    }
    if (overlay) {
        overlay.classList.toggle('active');
    }
}

// Table Action Dropdown Control
function toggleActionDropdown(btn, event) {
    event.stopPropagation();
    const wrapper = btn.closest('.saas-dropdown-wrapper');
    const menu = wrapper.querySelector('.saas-dropdown-menu');
    
    // Close all other open dropdowns
    document.querySelectorAll('.saas-dropdown-menu.active').forEach(m => {
        if (m !== menu) m.classList.remove('active');
    });
    
    menu.classList.toggle('active');

    // Smart Positioning: If hitting bottom of viewport, drop up instead
    if (menu.classList.contains('active')) {
        const rect = menu.getBoundingClientRect();
        const viewportHeight = window.innerHeight;
        
        if (rect.bottom > viewportHeight) {
            menu.classList.add('drop-up');
        } else {
            menu.classList.remove('drop-up');
        }
    }
}

// Global Click-away Listener for Dropdowns
document.addEventListener('click', (e) => {
    if (!e.target.closest('.saas-dropdown-wrapper')) {
        document.querySelectorAll('.saas-dropdown-menu.active').forEach(m => {
            m.classList.remove('active');
        });
    }
    
    // Also handle profile dropdown if exists
    if (!e.target.closest('.user-profile-wrapper')) {
        const profileDropdown = document.querySelector('.profile-dropdown.active');
        if (profileDropdown) profileDropdown.classList.remove('active');
    }
});

/**
 * HTMX GLOBAL ERROR & STATE RECOVERY
 * Ensures that institutional command surfaces (Modals, Panels) do not lock the UI on failure.
 */
document.body.addEventListener('htmx:responseError', (event) => {
    console.error('HTMX Response Error:', event.detail.xhr);
    document.body.style.overflow = ''; // Restore scroll on failure
});

document.body.addEventListener('htmx:sendError', (event) => {
    console.error('HTMX Send Error:', event.detail.error);
    document.body.style.overflow = ''; // Restore scroll on failure
});

document.body.addEventListener('htmx:beforeRequest', (event) => {
    // Optional: Add global loading state if needed
});
