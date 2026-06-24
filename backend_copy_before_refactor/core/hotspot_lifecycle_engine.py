from enum import Enum
from typing import Dict, Any


class HotspotState(str, Enum):
    CREATED = "CREATED"
    PROVISIONING = "PROVISIONING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    FAILED = "FAILED"


ALLOWED_TRANSITIONS: Dict[str, list] = {
    HotspotState.CREATED: [HotspotState.PROVISIONING],
    HotspotState.PROVISIONING: [HotspotState.ACTIVE, HotspotState.FAILED],
    HotspotState.ACTIVE: [HotspotState.SUSPENDED],
    HotspotState.SUSPENDED: [HotspotState.ACTIVE],
    HotspotState.FAILED: [HotspotState.PROVISIONING],
}


class HotspotLifecycleError(Exception):
    pass


class HotspotLifecycleEngine:
    """
    Single source of truth for hotspot state transitions.
    This does NOT touch DB directly — only validates and returns next state.
    """

    @staticmethod
    def validate_transition(current: str, next_state: str) -> None:
        try:
            current_state = HotspotState(current)
            next_state_enum = HotspotState(next_state)
        except Exception:
            raise HotspotLifecycleError(f"Invalid state: {current} -> {next_state}")

        allowed = ALLOWED_TRANSITIONS.get(current_state, [])

        if next_state_enum not in allowed:
            raise HotspotLifecycleError(
                f"Illegal transition: {current_state} -> {next_state_enum}"
            )

    @staticmethod
    def transition(hotspot: Dict[str, Any], next_state: str, actor: str = "system") -> Dict[str, Any]:
        """
        Safe transition function.
        Returns updated hotspot object (no DB mutation here).
        """

        current_state = hotspot.get("status")

        HotspotLifecycleEngine.validate_transition(current_state, next_state)

        hotspot["status"] = next_state
        hotspot["last_transition_by"] = actor
        hotspot["last_transition_at"] = "AUTO_TIMESTAMP_PLACEHOLDER"

        return hotspot
