/**
 * 🏛️ StudentNavigationOrchestrator
 * Enterprise-grade navigation state management for persistent HTMX shells.
 * Ensures the 'Absolute Source of Truth' (URL) is always reflected in the UI.
 */
class StudentNavigationOrchestrator {
    constructor() {
        this.navContainer = document.getElementById('stu-sidebar-nav');
        this.contextLabel = document.getElementById('header-context-label');
        this.basePath = '/dashboard/student/';
    }

    /**
     * 🔄 Synchronize UI state with current URL
     */
    sync() {
        if (!this.navContainer) return;

        const currentPath = window.location.pathname;
        const navLinks = this.navContainer.querySelectorAll('.nav-link');
        
        console.log(`[NavOrchestrator] Synchronizing state for: ${currentPath}`);

        navLinks.forEach(link => {
            const targetPath = link.getAttribute('data-path');
            
            // Logic: 
            // 1. Direct path match (e.g. /radar/ in /dashboard/student/radar/)
            // 2. Base path fallback (for /dashboard/student/ matching /overview/)
            const isBaseMatch = (currentPath === this.basePath || currentPath === this.basePath.slice(0, -1)) && targetPath === '/overview/';
            const isExactMatch = targetPath && currentPath.includes(targetPath);

            if (isExactMatch || isBaseMatch) {
                link.classList.add('active');
                this.updateContext(link);
                // Persistence: Remember last workspace
                localStorage.setItem('last_student_workspace', currentPath);
            } else {
                link.classList.remove('active');
            }
        });
    }

    /**
     * 🧠 Update cognitive context (Page Title & Topbar)
     */
    updateContext(activeLink) {
        const titleElement = activeLink.querySelector('span');
        if (!titleElement) return;

        const title = titleElement.innerText;
        document.title = `${title} | Student Success OS`;
        
        if (this.contextLabel) {
            const groupElement = activeLink.closest('.workspace-group')?.querySelector('div');
            const groupName = groupElement ? groupElement.innerText : 'Workspace';
            this.contextLabel.innerText = `${groupName} | ${title}`;
        }
    }

    /**
     * 🚀 Initialize Orchestrator & Listeners
     */
    initialize() {
        console.log("🎓 Student Success OS Navigation Orchestrator Initialized");
        
        // Initial Sync
        this.sync();

        // HTMX Lifecycle Sync: After every swap, re-evaluate.
        document.body.addEventListener('htmx:afterSwap', () => this.sync());
        
        // Native History Sync: Back/Forward buttons.
        window.addEventListener('popstate', () => this.sync());

        // Restore last workspace if at root
        if (window.location.pathname === this.basePath) {
            const lastPath = localStorage.getItem('last_student_workspace');
            if (lastPath && lastPath !== this.basePath) {
                console.log(`[NavOrchestrator] Restoring last workspace: ${lastPath}`);
                // Optional: Auto-redirect or load? 
                // For now, we stay at root but let the user know they can return.
            }
        }
    }
}

// 🏗️ Global Bootstrapper
document.addEventListener('DOMContentLoaded', () => {
    window.studentNav = new StudentNavigationOrchestrator();
    window.studentNav.initialize();
});
