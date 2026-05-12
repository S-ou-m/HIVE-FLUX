/**
 * 🧠 Dashboard Orchestrator (Academic OS Edition)
 * Manages HTMX lifecycles, UI roots, and operational stability.
 */

const DashboardOrchestrator = {
    init() {
        this.bindEvents();
        this.setupHTMXHooks();
        console.log("🚀 Execution OS Orchestrator Initialized");
    },

    bindEvents() {
        // Global Command Palette (Ctrl+K)
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.toggleCommandPalette();
            }
        });
    },

    setupHTMXHooks() {
        // 1. Cleanup before content swap
        document.body.addEventListener('htmx:beforeSwap', (evt) => {
            this.cleanupDynamicComponents(evt.detail.target);
        });

        // 2. Hydrate after content swap (with Guard & Filter)
        document.body.addEventListener('htmx:afterOnLoad', (evt) => {
            // Target Filter: Only hydrate if swapping main content or specific operational zones
            const targetId = evt.detail.target.id;
            const validTargets = ['dashboard-content', 'global-modal-root', 'global-drawer-root', 'global-drawer-content'];
            
            if (validTargets.includes(targetId)) {
                this.hydrateOperationalZone(evt.detail.target);
            }
        });

        // 3. Error Fallback Orchestration
        document.body.addEventListener('htmx:responseError', (evt) => {
            this.handleOperationalFailure(evt);
        });
    },

    cleanupDynamicComponents(target) {
        if (!target) return;
        console.log("🧹 Cleaning up old intelligence components in:", target.id || 'anonymous-target');
        
        // Destroy Chart.js instances if any exist in target
        if (window.Chart) {
            const canvases = target.querySelectorAll('canvas');
            canvases.forEach(canvas => {
                try {
                    const chart = Chart.getChart(canvas);
                    if (chart) chart.destroy();
                } catch(e) {}
            });
        }
    },

    hydrateOperationalZone(target) {
        // 🛑 Hydration Guard: Prevent recursive loop
        if (this.isHydrating) return;
        this.isHydrating = true;

        console.log("🔋 Hydrating operational signals for:", target.id);
        
        try {
            // Re-initialize any micro-animations or tooltips
            this.initGlowSignals(target);
        } finally {
            // Unlock after a safe buffer
            setTimeout(() => {
                this.isHydrating = false;
            }, 300);
        }
    },

    initGlowSignals(target) {
        const signals = target.querySelectorAll('.pulse-indicator');
        signals.forEach(sig => {
            // Logic for dynamic signal pulsing
        });
    },

    toggleCommandPalette() {
        if (typeof openCommandPalette === 'function') {
            openCommandPalette();
        }
    },

    handleOperationalFailure(evt) {
        console.error("🚨 Operational Module Failure:", evt.detail.error);
        // Show Global Toast or Error Modal
        this.showToast("INTELLIGENCE SYNC FAILURE", "error");
    },

    showToast(message, type = "info") {
        const root = document.getElementById('toast-root');
        if (!root) return;

        const toast = document.createElement('div');
        toast.className = `toast-pill ${type} animate-slide-up`;
        toast.innerHTML = `
            <div class="toast-indicator"></div>
            <span>${message}</span>
        `;
        
        root.appendChild(toast);
        setTimeout(() => {
            toast.classList.add('animate-fade-out');
            setTimeout(() => toast.remove(), 500);
        }, 4000);
    },

    toggleFocusMode() {
        const isActive = document.body.classList.toggle('focus-mode-active');
        
        if (isActive) {
            this.logOperationalEvent('FOCUS_MODE_ENGAGED', 'User entered immersive focus environment.');
            this.showToast("FOCUS MODE ACTIVE", "info");
        } else {
            this.logOperationalEvent('FOCUS_MODE_EXITED', 'User returned to standard dashboard.');
            this.showToast("FOCUS MODE TERMINATED", "info");
        }
    },

    setUIDensity(mode) {
        const body = document.body;
        body.classList.remove('density-relaxed', 'density-compact');
        if (mode !== 'default') {
            body.classList.add(`density-${mode}`);
        }
        this.showToast(`UI DENSITY: ${mode.toUpperCase()}`, "info");
        
        // Update Segmented Control UI
        document.querySelectorAll('.segmented-control .seg-btn').forEach(btn => {
            btn.classList.toggle('active', btn.textContent.toLowerCase() === mode);
        });
    },

    toggleAtmosphere() {
        const avatarRing = document.querySelector('.avatar-ring');
        const isActive = avatarRing?.classList.toggle('pulse-active');
        this.showToast(`ATMOSPHERE PULSE: ${isActive ? 'ON' : 'OFF'}`, "info");
        
        document.querySelector('.toggle-switch.pulse-toggle')?.classList.toggle('active', isActive);
    },

    toggleMotion() {
        const isActive = document.body.classList.toggle('motion-reduced');
        this.showToast(`MOTION REDUCTION: ${isActive ? 'ON' : 'OFF'}`, "info");
        document.querySelector('.toggle-switch.motion-toggle')?.classList.toggle('active', isActive);
    },

    updateAccessKey() {
        this.showToast("SECURITY CHALLENGE INITIATED", "info");
        setTimeout(() => {
            alert("🔒 Secure Password Update Protocol Activated.\n\nIn a production environment, this would trigger an OTP-verified modal or a redirect to the secure IAM service.");
        }, 500);
    },

    reverifyDevice(deviceName) {
        this.showToast(`VERIFYING ${deviceName}...`, "info");
        setTimeout(() => {
            this.showToast(`${deviceName} VERIFIED`, "success");
        }, 1500);
    },

    revokeDevice(deviceName, el) {
        if (confirm(`⚠️ WARNING: Revoke trust for ${deviceName}?\n\nThis will instantly terminate all active sessions on this device.`)) {
            const item = el.closest('.device-item');
            item.style.opacity = '0.5';
            item.style.pointerEvents = 'none';
            this.showToast(`${deviceName} ACCESS REVOKED`, "error");
            this.logOperationalEvent('DEVICE_REVOKED', deviceName);
        }
    },

    logOperationalEvent(type, detail) {
        console.log(`🔋 [ExecutionOS] ${type}: ${detail}`);
    }
};

// Initialize on DOM Load
document.addEventListener('DOMContentLoaded', () => {
    DashboardOrchestrator.init();
});
