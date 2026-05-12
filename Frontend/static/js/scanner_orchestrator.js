/**
 * 🕹️ Scanner Orchestrator (Faculty Operational OS)
 * Manages the high-fidelity scanning state machine and real-time DOM updates.
 */

const ScannerOS = {
    state: 'BOOTING',
    sessionId: null,
    scanCount: 0,
    isProcessing: false,

    init(sessionId) {
        this.sessionId = sessionId;
        this.updateState('READY');
        console.log(`📡 Scanner Environment Initialized for Session: ${sessionId}`);
    },

    updateState(newState) {
        this.state = newState;
        const overlay = document.getElementById('scanner-state');
        if (!overlay) return;

        // Hide all state views
        overlay.querySelectorAll('div').forEach(el => el.classList.add('hidden'));
        
        // Show active state
        const activeView = overlay.querySelector(`.state-${newState.toLowerCase()}`);
        if (activeView) activeView.classList.remove('hidden');

        // Apply kinetic signals
        if (newState === 'SUCCESS') this.triggerKineticSignal('success-flash');
        if (newState === 'DUPLICATE') this.triggerKineticSignal('warning-shiver');
    },

    triggerKineticSignal(signalClass) {
        const viewport = document.querySelector('.scanner-viewport');
        if (!viewport) return;

        viewport.classList.add(signalClass);
        setTimeout(() => viewport.classList.remove(signalClass), 800);
    },

    async simulateScan(studentId) {
        if (this.state !== 'READY' || this.isProcessing) return;
        
        this.isProcessing = true;
        this.updateState('VERIFYING');
        
        // 🏁 START OPERATIONAL LOOP
        try {
            const response = await fetch(`/dashboard/faculty/attendance/scan/process/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    student_id: studentId,
                    metadata: {
                        source: 'SIMULATOR',
                        timestamp: new Date().toISOString()
                    }
                })
            });

            const result = await response.json();
            this.handleScanResult(result);
        } catch (error) {
            this.handleError();
        } finally {
            this.isProcessing = false;
        }
    },

    handleScanResult(result) {
        if (result.status === 'SUCCESS') {
            this.updateState('SUCCESS');
            this.updateMetrics(result.metrics);
            this.addToVerifiedFeed(result);
            
            // Auto-reset to READY
            setTimeout(() => this.updateState('READY'), 1500);
        } else if (result.status === 'DUPLICATE') {
            this.updateState('DUPLICATE');
            this.updateStatusText('ALREADY VERIFIED', '#f59e0b');
            
            setTimeout(() => {
                this.updateState('READY');
                this.updateStatusText('READY TO SCAN', '');
            }, 1500);
        }
    },

    updateMetrics(metrics) {
        const countEl = document.getElementById('count-present');
        const rateEl = document.getElementById('scan-rate');
        
        if (countEl) countEl.textContent = metrics.present;
        if (rateEl) rateEl.textContent = metrics.scan_rate;
    },

    addToVerifiedFeed(data) {
        const feed = document.getElementById('verification-feed');
        if (!feed) return;

        const item = document.createElement('div');
        item.className = 'feed-item animate-slide-up';
        item.innerHTML = `
            <div class="item-avatar">${data.student[0]}</div>
            <div class="item-info">
                <div class="item-name">${data.student}</div>
                <div class="item-meta">JUST NOW • VERIFIED</div>
            </div>
            <i class="fas fa-check-circle text-success ml-auto"></i>
        `;

        feed.prepend(item);
        
        // Remove empty state if present
        const empty = feed.querySelector('.feed-empty');
        if (empty) empty.remove();

        // Limit feed size for performance
        if (feed.children.length > 5) {
            feed.lastElementChild.remove();
        }
    },

    updateStatusText(text, color) {
        const textEl = document.getElementById('success-name');
        if (textEl) {
            textEl.textContent = text;
            textEl.style.color = color;
        }
    },

    handleError() {
        this.updateState('READY');
        if (window.DashboardOrchestrator) {
            window.DashboardOrchestrator.showToast("SCAN SYNC FAILURE", "error");
        }
    },

    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
};
