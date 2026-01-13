"""State management for storing user preferences."""
import json
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class StateManager:
    """Manages application state persistence."""
    
    def __init__(self, state_file: str = 'appointment_state.json'):
        """Initialize state manager."""
        self.state_file = state_file
        self.state = self._load_state()
    
    def _load_state(self) -> dict:
        """Load state from file."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
                return {}
        return {}
    
    def _save_state(self):
        """Save state to file."""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
            logger.debug(f"State saved to {self.state_file}")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def get_selected_counselor(self) -> Optional[str]:
        """Get selected counselor/region."""
        return self.state.get('selected_counselor')
    
    def set_selected_counselor(self, counselor_id: str):
        """Set selected counselor/region."""
        self.state['selected_counselor'] = counselor_id
        self._save_state()
    
    def get_counselors(self) -> list:
        """Get list of counselors."""
        return self.state.get('counselors', [])
    
    def set_counselors(self, counselors: list):
        """Set list of counselors."""
        self.state['counselors'] = counselors
        self._save_state()
    
    def get_last_checked_date(self) -> Optional[str]:
        """Get last checked date."""
        return self.state.get('last_checked_date')
    
    def set_last_checked_date(self, date: str):
        """Set last checked date."""
        self.state['last_checked_date'] = date
        self._save_state()
    
    def get_max_date(self) -> Optional[str]:
        """Get maximum date to check."""
        return self.state.get('max_date')
    
    def set_max_date(self, max_date: str):
        """Set maximum date to check."""
        self.state['max_date'] = max_date
        self._save_state()
    
    def clear_state(self):
        """Clear all state."""
        self.state = {}
        if os.path.exists(self.state_file):
            os.remove(self.state_file)
