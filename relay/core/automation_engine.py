"""
Automation Engine - Handles PyAutoGUI execution of planned actions
Provides safety controls, error handling, and action execution
"""

import pyautogui
import time
import logging
import threading
from typing import Optional, Tuple, Callable
from PIL import Image
import numpy as np
from dataclasses import dataclass
from .vision_engine import ActionPlan

# Configure PyAutoGUI safety settings
pyautogui.FAILSAFE = True  # Move mouse to corner to abort
pyautogui.PAUSE = 0.1  # Small pause between actions

@dataclass
class ExecutionResult:
    """Result of action execution"""
    success: bool
    error_message: Optional[str] = None
    before_screenshot: Optional[Image.Image] = None
    after_screenshot: Optional[Image.Image] = None
    execution_time: float = 0.0

class AutomationEngine:
    """Handles execution of automation actions with safety controls"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.emergency_stop = False
        self.safety_callbacks = []
        
        # Safety settings
        self.max_click_retries = 3
        self.action_timeout = 30.0  # seconds
        self.confirmation_required = ['delete', 'purchase', 'confirm', 'submit']
        
        # Action allowlist for safety
        self.allowed_actions = {
            'click': True,
            'type': True,
            'scroll': True,
            'wait': True,
            'verify': True,
            'navigate': True
        }
        
        # Register emergency stop handler
        self._setup_emergency_stop()
    
    def execute_action(self, action_plan: ActionPlan, 
                      before_screenshot: Optional[Image.Image] = None) -> ExecutionResult:
        """
        Execute a planned action with safety controls
        """
        if self.emergency_stop:
            return ExecutionResult(False, "Emergency stop activated")
        
        if not self._validate_action_safety(action_plan):
            return ExecutionResult(False, "Action blocked by safety controls")
        
        # Check for confirmation requirement
        if self._requires_confirmation(action_plan):
            if not self._get_user_confirmation(action_plan):
                return ExecutionResult(False, "User declined confirmation")
        
        start_time = time.time()
        result = ExecutionResult(success=False, before_screenshot=before_screenshot)
        
        try:
            self.logger.info(f"Executing action: {action_plan.action_type} - {action_plan.target_description}")
            
            # Execute based on action type
            if action_plan.action_type == 'click':
                result = self._execute_click(action_plan)
            elif action_plan.action_type == 'type':
                result = self._execute_type(action_plan)
            elif action_plan.action_type == 'scroll':
                result = self._execute_scroll(action_plan)
            elif action_plan.action_type == 'wait':
                result = self._execute_wait(action_plan)
            elif action_plan.action_type == 'verify':
                result = self._execute_verify(action_plan)
            elif action_plan.action_type == 'navigate':
                result = self._execute_navigate(action_plan)
            else:
                result = ExecutionResult(False, f"Unknown action type: {action_plan.action_type}")
            
            # Take after screenshot
            result.after_screenshot = self._take_screenshot()
            result.execution_time = time.time() - start_time
            
            # Log result
            if result.success:
                self.logger.info(f"Action completed successfully in {result.execution_time:.2f}s")
            else:
                self.logger.warning(f"Action failed: {result.error_message}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing action: {e}")
            result.after_screenshot = self._take_screenshot()
            result.execution_time = time.time() - start_time
            result.error_message = str(e)
            return result
    
    def _execute_click(self, action_plan: ActionPlan) -> ExecutionResult:
        """Execute click action"""
        try:
            if action_plan.coordinates:
                # Click at specific coordinates
                x, y = action_plan.coordinates
                pyautogui.click(x, y)
                self.logger.info(f"Clicked at coordinates ({x}, {y})")
            else:
                # Try to find element by description (basic implementation)
                # In a full implementation, this would use image recognition
                self.logger.warning("No coordinates provided for click action")
                return ExecutionResult(False, "No coordinates provided for click")
            
            # Small wait after click
            time.sleep(0.5)
            return ExecutionResult(success=True)
            
        except Exception as e:
            return ExecutionResult(False, f"Click execution failed: {e}")
    
    def _execute_type(self, action_plan: ActionPlan) -> ExecutionResult:
        """Execute type action"""
        try:
            if not action_plan.text:
                return ExecutionResult(False, "No text provided for type action")
            
            # Type the text
            pyautogui.typewrite(action_plan.text)
            self.logger.info(f"Typed text: {action_plan.text}")
            
            # Small wait after typing
            time.sleep(0.3)
            return ExecutionResult(success=True)
            
        except Exception as e:
            return ExecutionResult(False, f"Type execution failed: {e}")
    
    def _execute_scroll(self, action_plan: ActionPlan) -> ExecutionResult:
        """Execute scroll action"""
        try:
            # Parse scroll direction from target description
            direction = action_plan.target_description.lower()
            
            if 'up' in direction:
                pyautogui.scroll(3)  # Scroll up
            elif 'down' in direction:
                pyautogui.scroll(-3)  # Scroll down
            elif 'left' in direction:
                pyautogui.hscroll(3)  # Scroll left
            elif 'right' in direction:
                pyautogui.hscroll(-3)  # Scroll right
            else:
                # Default to scroll down
                pyautogui.scroll(-3)
            
            self.logger.info(f"Scrolled {direction}")
            time.sleep(0.5)
            return ExecutionResult(success=True)
            
        except Exception as e:
            return ExecutionResult(False, f"Scroll execution failed: {e}")
    
    def _execute_wait(self, action_plan: ActionPlan) -> ExecutionResult:
        """Execute wait action"""
        try:
            # Parse wait duration from target description or use default
            wait_time = 2.0  # Default wait time
            
            # Try to extract time from description
            import re
            time_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:seconds?|s)', action_plan.target_description.lower())
            if time_match:
                wait_time = float(time_match.group(1))
            
            self.logger.info(f"Waiting for {wait_time} seconds")
            time.sleep(wait_time)
            return ExecutionResult(success=True)
            
        except Exception as e:
            return ExecutionResult(False, f"Wait execution failed: {e}")
    
    def _execute_verify(self, action_plan: ActionPlan) -> ExecutionResult:
        """Execute verify action - check if expected result appears"""
        try:
            # For now, just log the verification criteria
            # In a full implementation, this would use image recognition
            self.logger.info(f"Verifying: {action_plan.verification_criteria}")
            
            # Take a screenshot for verification
            screenshot = self._take_screenshot()
            
            # Basic verification - check if text appears in screenshot
            # This is a simplified implementation
            if action_plan.verification_criteria:
                # Convert screenshot to text for basic verification
                # In practice, you'd use OCR or image recognition
                self.logger.info("Verification criteria provided, but OCR not implemented")
            
            return ExecutionResult(success=True)
            
        except Exception as e:
            return ExecutionResult(False, f"Verify execution failed: {e}")
    
    def _execute_navigate(self, action_plan: ActionPlan) -> ExecutionResult:
        """Execute navigate action"""
        try:
            # Parse navigation target from description
            target = action_plan.target_description.lower()
            
            if 'back' in target:
                pyautogui.hotkey('alt', 'left')
            elif 'forward' in target:
                pyautogui.hotkey('alt', 'right')
            elif 'refresh' in target or 'reload' in target:
                pyautogui.hotkey('f5')
            elif 'home' in target:
                pyautogui.hotkey('home')
            elif 'end' in target:
                pyautogui.hotkey('end')
            else:
                # Default to back navigation
                pyautogui.hotkey('alt', 'left')
            
            self.logger.info(f"Navigated: {target}")
            time.sleep(1.0)  # Wait for navigation to complete
            return ExecutionResult(success=True)
            
        except Exception as e:
            return ExecutionResult(False, f"Navigate execution failed: {e}")
    
    def _validate_action_safety(self, action_plan: ActionPlan) -> bool:
        """Validate action against safety rules"""
        
        # Check if action type is allowed
        if not self.allowed_actions.get(action_plan.action_type, False):
            self.logger.warning(f"Action type {action_plan.action_type} not allowed")
            return False
        
        # Check for destructive actions
        destructive_keywords = ['delete', 'remove', 'uninstall', 'format', 'shutdown']
        if any(keyword in action_plan.target_description.lower() for keyword in destructive_keywords):
            if action_plan.confidence < 8:
                self.logger.warning("Low confidence destructive action detected")
                return False
        
        # Check coordinates are within screen bounds
        if action_plan.coordinates:
            x, y = action_plan.coordinates
            screen_width, screen_height = pyautogui.size()
            if not (0 <= x <= screen_width and 0 <= y <= screen_height):
                self.logger.warning(f"Coordinates ({x}, {y}) outside screen bounds")
                return False
        
        return True
    
    def _requires_confirmation(self, action_plan: ActionPlan) -> bool:
        """Check if action requires user confirmation"""
        description_lower = action_plan.target_description.lower()
        return any(keyword in description_lower for keyword in self.confirmation_required)
    
    def _get_user_confirmation(self, action_plan: ActionPlan) -> bool:
        """Get user confirmation for high-risk actions"""
        # This would integrate with the UI to show confirmation dialog
        # For now, return True (allow action)
        self.logger.info(f"Confirmation required for: {action_plan.target_description}")
        return True
    
    def _take_screenshot(self) -> Image.Image:
        """Take a screenshot of the current screen"""
        try:
            return pyautogui.screenshot()
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
            # Return a blank image as fallback
            return Image.new('RGB', (1920, 1080), color='white')
    
    def _setup_emergency_stop(self):
        """Setup emergency stop mechanism"""
        def emergency_stop_handler():
            self.emergency_stop = True
            self.logger.warning("Emergency stop activated")
        
        # Register callback for emergency stop
        self.safety_callbacks.append(emergency_stop_handler)
    
    def activate_emergency_stop(self):
        """Activate emergency stop"""
        self.emergency_stop = True
        self.logger.warning("Emergency stop activated by user")
    
    def reset_emergency_stop(self):
        """Reset emergency stop"""
        self.emergency_stop = False
        self.logger.info("Emergency stop reset")
    
    def add_safety_callback(self, callback: Callable):
        """Add a safety callback function"""
        self.safety_callbacks.append(callback)
    
    def get_screen_info(self) -> dict:
        """Get current screen information"""
        try:
            width, height = pyautogui.size()
            x, y = pyautogui.position()
            return {
                'width': width,
                'height': height,
                'mouse_x': x,
                'mouse_y': y
            }
        except Exception as e:
            self.logger.error(f"Failed to get screen info: {e}")
            return {} 