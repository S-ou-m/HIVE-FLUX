/**
 * 🏛️ Institutional Identity Drawer State Machine
 * Deterministic lifecycle governance for the Success OS command surface.
 * Prevents UI race conditions and manages operational state transitions.
 */
class IdentityDrawerStateMachine {
    constructor() {
        this.states = {
            IDLE: 'IDLE',
            OPENING: 'OPENING',
            LOADING: 'LOADING',
            READY: 'READY',
            SYNCING: 'SYNCING',
            STALE: 'STALE',
            DEGRADED: 'DEGRADED',
            ERROR: 'ERROR',
            CLOSING: 'CLOSING'
        };
        
        this.currentState = this.states.IDLE;
        this.lastTransitionSource = 'system_init';
        this.subscriptions = [];
        this.abortControllers = new Map();
    }

    transition(newState, source = 'user_action') {
        const oldState = this.currentState;
        
        // 🛡️ Transition Guards
        if (oldState === newState) return;
        
        console.log(`[IdentityOS] Transition: ${oldState} -> ${newState} (via ${source})`);
        
        this.currentState = newState;
        this.lastTransitionSource = source;
        
        this._notifySubscribers(newState, oldState, source);
        this._handleStateSideEffects(newState);
    }

    _handleStateSideEffects(state) {
        const body = document.body;
        
        switch(state) {
            case this.states.OPENING:
                body.classList.add('drawer-active');
                this._lockScroll();
                break;
                
            case this.states.LOADING:
                this._showGlobalLoader();
                break;
                
            case this.states.READY:
                this._hideGlobalLoader();
                break;
                
            case this.states.CLOSING:
                body.classList.remove('drawer-active');
                this._unlockScroll();
                this._cleanup();
                setTimeout(() => this.transition(this.states.IDLE), 400);
                break;
                
            case this.states.ERROR:
                this._showErrorSurface();
                break;
        }
    }

    subscribe(callback) {
        this.subscriptions.push(callback);
    }

    _notifySubscribers(newState, oldState, source) {
        this.subscriptions.forEach(cb => cb(newState, oldState, source));
    }

    _lockScroll() {
        document.documentElement.style.overflow = 'hidden';
    }

    _unlockScroll() {
        document.documentElement.style.overflow = '';
    }

    _showGlobalLoader() {
        const loader = document.getElementById('drawer-loader');
        if (loader) loader.classList.remove('hidden');
    }

    _hideGlobalLoader() {
        const loader = document.getElementById('drawer-loader');
        if (loader) loader.classList.add('hidden');
    }

    _cleanup() {
        // Abort any ongoing secondary hydration requests
        this.abortControllers.forEach(ctrl => ctrl.abort());
        this.abortControllers.clear();
        console.log('[IdentityOS] Cleanup: Listeners and requests purged.');
    }

    destroy() {
        this._cleanup();
        this.subscriptions = [];
        this.currentState = this.states.IDLE;
    }
}

// 🚀 Initialize Global State Machine
window.IdentityOS = window.IdentityOS || {};
window.IdentityOS.StateMachine = new IdentityDrawerStateMachine();
