#!/usr/bin/env python3

class FallbackAgent:
    def __init__(self):
        self.context = {}
        self.state_backup = {}
        self.transition_integrity = True
    
    def preserve_context(self, current_state):
        """Preserve context during transitions"""
        self.context = current_state.copy()
        self.state_backup = current_state.copy()
        return True
    
    def recover_context(self):
        """Recover preserved context"""
        if self.context and self.state_backup:
            return self.context
        return None

if __name__ == '__main__':
    agent = FallbackAgent()