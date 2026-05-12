/**
 * 🚀 Performance Capability Detector
 * Dynamically scales institutional visual fidelity based on client hardware.
 * Tiers: ULTRA, HIGH, MEDIUM, LOW, SAFE
 */
class PerformanceCapabilityDetector {
    constructor() {
        this.tiers = {
            ULTRA: 'fidelity-ultra',
            HIGH: 'fidelity-high',
            MEDIUM: 'fidelity-medium',
            LOW: 'fidelity-low',
            SAFE: 'fidelity-safe'
        };
    }

    detectAndApply() {
        const capability = this._getCapabilities();
        const tier = this._calculateTier(capability);
        
        console.log(`[IdentityOS] Capability Detected: ${tier}`);
        
        document.body.classList.remove(...Object.values(this.tiers));
        document.body.classList.add(this.tiers[tier]);
        
        return tier;
    }

    _getCapabilities() {
        return {
            memory: navigator.deviceMemory || 4, // GB
            cores: navigator.hardwareConcurrency || 4,
            dpr: window.devicePixelRatio || 1,
            reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
            connection: navigator.connection ? navigator.connection.effectiveType : '4g'
        };
    }

    _calculateTier(cap) {
        // 🛡️ Safe Mode Guards
        if (cap.reducedMotion || cap.connection === '2g') return 'SAFE';
        
        // 🏗️ Fidelity Logic
        if (cap.memory >= 8 && cap.cores >= 8 && cap.dpr >= 2) return 'ULTRA';
        if (cap.memory >= 4 && cap.cores >= 4) return 'HIGH';
        if (cap.memory >= 2) return 'MEDIUM';
        
        return 'LOW';
    }
}

// 🚀 Initialize Global Detector
window.IdentityOS = window.IdentityOS || {};
window.IdentityOS.Performance = new PerformanceCapabilityDetector();
window.addEventListener('DOMContentLoaded', () => window.IdentityOS.Performance.detectAndApply());
