/**
 * 🍞 Hiveflux Institutional Toast Engine
 * Orchestrates professional feedback for operational events.
 */
class HivefluxToast {
    static init() {
        this.container = document.getElementById('toast-root');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'toast-root';
            this.container.className = 'fixed bottom-8 right-8 z-[9999] flex flex-col gap-3 pointer-events-none';
            document.body.appendChild(this.container);
        }
    }

    static show(message, type = 'info', duration = 4000) {
        if (!this.container) this.init();

        const toast = document.createElement('div');
        toast.className = `
            toast-item pointer-events-auto
            flex items-center gap-3 px-6 py-4 
            rounded-2xl border backdrop-blur-xl shadow-2xl
            translate-x-full transition-all duration-500 ease-[cubic-bezier(0.16,1,0.3,1)]
            ${this.getStyles(type)}
        `;

        toast.innerHTML = `
            <div class="w-8 h-8 rounded-xl flex items-center justify-center bg-white/10">
                <i class="fas ${this.getIcon(type)}"></i>
            </div>
            <div class="flex flex-col">
                <span class="text-[10px] font-black uppercase tracking-widest opacity-40">${type}</span>
                <span class="text-sm font-bold text-white">${message}</span>
            </div>
        `;

        this.container.appendChild(toast);

        // Animate in
        requestAnimationFrame(() => {
            toast.classList.remove('translate-x-full');
        });

        // Auto remove
        setTimeout(() => {
            toast.classList.add('translate-x-full');
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 500);
        }, duration);
    }

    static getStyles(type) {
        switch (type) {
            case 'success': return 'bg-emerald-500/20 border-emerald-500/30 text-emerald-400';
            case 'error': return 'bg-red-500/20 border-red-500/30 text-red-400';
            case 'warning': return 'bg-orange-500/20 border-orange-500/30 text-orange-400';
            default: return 'bg-blue-500/20 border-blue-500/30 text-blue-400';
        }
    }

    static getIcon(type) {
        switch (type) {
            case 'success': return 'fa-check-circle';
            case 'error': return 'fa-exclamation-circle';
            case 'warning': return 'fa-exclamation-triangle';
            default: return 'fa-info-circle';
        }
    }
}

// HTMX Integration
document.addEventListener('htmx:beforeRequest', (evt) => {
    // Optional: Show loading state
});

document.addEventListener('htmx:afterRequest', (evt) => {
    if (evt.detail.successful) {
        // Only show success for specific actions if needed
    } else {
        HivefluxToast.show('Institutional Service Interruption', 'error');
    }
});

// ⚡ Dynamic Toast Trigger (For HX-Trigger headers)
document.addEventListener('showToast', (evt) => {
    const data = evt.detail;
    if (data && data.message) {
        HivefluxToast.show(data.message, data.type || 'info');
    }
});

// Global Window Access
window.showToast = (msg, type) => HivefluxToast.show(msg, type);
window.HivefluxToast = HivefluxToast;
