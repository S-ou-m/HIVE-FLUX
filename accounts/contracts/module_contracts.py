from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class OperationalModuleContract:
    """
    🏛️ Operational Module Contract
    Foundational governance schema for institutional-grade drawer modules.
    Defines hydration, freshness, and degradation behaviors.
    """
    module_id: str
    display_name: str
    hydration_priority: int  # 1 (Highest) to 5 (Lowest)
    freshness_ttl: int      # Seconds before data is considered STALE
    degradation_strategy: str # 'SNAPSHOT', 'PARTIAL_DISABLE', 'STALE_WARNING'
    visibility_policy: str   # 'STUDENT_ONLY', 'MENTOR_VISIBLE', 'ADMIN_ONLY'
    sync_strategy: str      # 'POLLING', 'SSE', 'MANUAL'
    fallback_surface: str   # Template path for degraded state
    dependencies: List[str] = field(default_factory=list)
    
    def get_health_state(self, last_sync_seconds: int) -> str:
        """Determines the operational health state based on TTL."""
        if last_sync_seconds <= self.freshness_ttl:
            return "LIVE"
        elif last_sync_seconds <= self.freshness_ttl * 1.5:
            return "DELAYED"
        elif last_sync_seconds <= self.freshness_ttl * 2:
            return "STALE"
        return "DEGRADED"

# 🚀 INSTITUTIONAL MODULE REGISTRY
MODULE_REGISTRY: Dict[str, OperationalModuleContract] = {
    "identity_surface": OperationalModuleContract(
        module_id="identity_surface",
        display_name="Institutional Identity",
        hydration_priority=1,
        freshness_ttl=3600, # Identity metadata is stable
        degradation_strategy="SNAPSHOT",
        visibility_policy="STUDENT_ONLY",
        sync_strategy="MANUAL",
        fallback_surface="dashboard/views/student/profile_drawer/fallbacks/surface_degraded.html",
        dependencies=["Student"]
    ),
    "telemetry": OperationalModuleContract(
        module_id="telemetry",
        display_name="Operational Telemetry",
        hydration_priority=1,
        freshness_ttl=15, # Presence decays rapidly
        degradation_strategy="STALE_WARNING",
        visibility_policy="STUDENT_ONLY",
        sync_strategy="POLLING",
        fallback_surface="dashboard/views/student/profile_drawer/fallbacks/telemetry_degraded.html",
        dependencies=["IdentitySession", "IdentityScanEvent"]
    ),
    "success_trajectory": OperationalModuleContract(
        module_id="success_trajectory",
        display_name="Success Trajectory",
        hydration_priority=2,
        freshness_ttl=300, # 5 min refresh for intelligence
        degradation_strategy="SNAPSHOT",
        visibility_policy="MENTOR_VISIBLE",
        sync_strategy="POLLING",
        fallback_surface="dashboard/views/student/profile_drawer/fallbacks/trajectory_degraded.html",
        dependencies=["SuccessConfidenceHistory"]
    ),
    "security_hub": OperationalModuleContract(
        module_id="security_hub",
        display_name="Security & Device Center",
        hydration_priority=3,
        freshness_ttl=60,
        degradation_strategy="PARTIAL_DISABLE",
        visibility_policy="STUDENT_ONLY",
        sync_strategy="MANUAL",
        fallback_surface="dashboard/views/student/profile_drawer/fallbacks/security_degraded.html",
        dependencies=["TrustedDevice"]
    ),
    "actions_grid": OperationalModuleContract(
        module_id="actions_grid",
        display_name="Operational Actions",
        hydration_priority=1,
        freshness_ttl=3600,
        degradation_strategy="PARTIAL_DISABLE",
        visibility_policy="STUDENT_ONLY",
        sync_strategy="MANUAL",
        fallback_surface="dashboard/views/student/profile_drawer/fallbacks/actions_degraded.html"
    )
}
