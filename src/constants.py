"""
WiFi State Machine Constants.

Provides both class-based and legacy constant-style access for compatibility.
"""


class WiFiState:
    """
    WiFi state machine states with type-safe access and utility methods.

    Usage:
        from constants import WiFiState

        state = WiFiState.CONNECTED
        print(WiFiState.get_name(state))  # "CONNECTED"

        # Check if valid state
        if WiFiState.is_valid(state):
            ...
    """
    IDLE = 0
    CONNECTING = 1
    CONNECTED = 2
    FAIL = 3
    AP_MODE = 4

    _NAMES = {
        0: 'IDLE',
        1: 'CONNECTING',
        2: 'CONNECTED',
        3: 'FAIL',
        4: 'AP_MODE'
    }

    @staticmethod
    def get_name(state: int) -> str:
        """
        Get the human-readable name of a state.

        Args:
            state: State constant value.

        Returns:
            State name string, or 'UNKNOWN' if invalid.
        """
        return WiFiState._NAMES.get(state, 'UNKNOWN')

    @staticmethod
    def is_valid(state: int) -> bool:
        """
        Check if a value is a valid state constant.

        Args:
            state: Value to check.

        Returns:
            True if state is a valid WiFi state constant.
        """
        return state in WiFiState._NAMES

    @staticmethod
    def all_states() -> list:
        """
        Get all valid state values.

        Returns:
            List of all state constants.
        """
        return list(WiFiState._NAMES.keys())


# Legacy constants for backward compatibility
STATE_IDLE = WiFiState.IDLE
STATE_CONNECTING = WiFiState.CONNECTING
STATE_CONNECTED = WiFiState.CONNECTED
STATE_FAIL = WiFiState.FAIL
STATE_AP_MODE = WiFiState.AP_MODE
