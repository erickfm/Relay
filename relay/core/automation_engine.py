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
from .vision_engine import ActionPlan, VisionEngine
import json

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
    action_verified: bool = False
    verification_message: Optional[str] = None

class AutomationEngine:
    """Handles execution of automation actions with safety controls"""
    
    def __init__(self, vision_engine: Optional[VisionEngine] = None):
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.emergency_stop = False
        self.safety_callbacks = []
        self.vision_engine = vision_engine
        
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
            'navigate': True,
            'hotkey': True,
            'move': True,
            'double_click': True,
            'right_click': True,
            'drag': True
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
            elif action_plan.action_type == 'double_click':
                result = self._execute_double_click(action_plan)
            elif action_plan.action_type == 'right_click':
                result = self._execute_right_click(action_plan)
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
            elif action_plan.action_type == 'hotkey':
                result = self._execute_hotkey(action_plan)
            elif action_plan.action_type == 'move':
                result = self._execute_move(action_plan)
            elif action_plan.action_type == 'drag':
                result = self._execute_drag(action_plan)
            else:
                result = ExecutionResult(False, f"Unknown action type: {action_plan.action_type}")
            
            # Take after screenshot
            result.after_screenshot = self._take_screenshot()
            result.execution_time = time.time() - start_time
            
            # Verify action success if we have a vision engine
            if self.vision_engine and result.success:
                result = self._verify_action_success(action_plan, result)
            
            # Log result with verification status
            if result.success:
                if result.action_verified:
                    self.logger.info(f"✅ Action completed and VERIFIED in {result.execution_time:.2f}s")
                else:
                    self.logger.warning(f"⚠️ Action completed but NOT VERIFIED in {result.execution_time:.2f}s")
            else:
                self.logger.error(f"❌ Action failed: {result.error_message}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing action: {e}")
            result.after_screenshot = self._take_screenshot()
            result.execution_time = time.time() - start_time
            result.error_message = str(e)
            return result
    
    def _verify_action_success(self, action_plan: ActionPlan, result: ExecutionResult) -> ExecutionResult:
        """Verify if the action actually worked by asking the AI to compare before/after screenshots"""
        try:
            if not result.before_screenshot or not result.after_screenshot:
                self.logger.warning("Cannot verify action - missing before/after screenshots")
                result.action_verified = False
                result.verification_message = "Missing screenshots for verification"
                return result
            
            # Ask AI to verify if the action worked
            verification_result = self._ask_ai_for_verification(action_plan, result.before_screenshot, result.after_screenshot)
            
            result.action_verified = verification_result['verified']
            result.verification_message = verification_result['message']
            
            if result.action_verified:
                self.logger.info(f"✅ AI verified action success: {result.verification_message}")
            else:
                self.logger.warning(f"❌ AI says action failed: {result.verification_message}")
                # Mark as failed if AI says it didn't work
                result.success = False
                result.error_message = f"Action verification failed: {result.verification_message}"
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in action verification: {e}")
            result.action_verified = False
            result.verification_message = f"Verification error: {e}"
            return result
    
    def _ask_ai_for_verification(self, action_plan: ActionPlan, before_screenshot: Image.Image, after_screenshot: Image.Image) -> dict:
        """Ask the AI to verify if the action worked by comparing before/after screenshots"""
        try:
            import base64
            import io
            
            # Convert screenshots to base64
            buffer1 = io.BytesIO()
            buffer2 = io.BytesIO()
            before_screenshot.save(buffer1, format='PNG')
            after_screenshot.save(buffer2, format='PNG')
            
            before_b64 = base64.b64encode(buffer1.getvalue()).decode('utf-8')
            after_b64 = base64.b64encode(buffer2.getvalue()).decode('utf-8')
            
            messages = [
                {
                    "role": "system",
                    "content": """
                    You are an action verification expert. Compare before/after screenshots to determine if an automation action was successful.
                    
                    Be SKEPTICAL - assume the action failed unless you can clearly see evidence of success.
                    
                    VERIFICATION CRITERIA:
                    - For clicks: Look for visual changes, new windows, UI state changes
                    - For typing: Look for text appearing in fields
                    - For navigation: Look for page/app changes
                    - For scrolling: Look for content movement
                    - For hotkeys: Look for expected system responses
                    
                    RESPONSE FORMAT:
                    {
                        "verified": true/false,
                        "confidence": 1-10,
                        "message": "Detailed explanation of what you see and why you think it worked or failed",
                        "evidence": "Specific visual evidence you found"
                    }
                    """
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""
                            Action attempted: {action_plan.action_type} - {action_plan.target_description}
                            Coordinates: {action_plan.coordinates}
                            Target description: {action_plan.target_description}
                            
                            Did this action actually work? Compare the before and after screenshots.
                            """
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{before_b64}"}
                        },
                        {
                            "type": "image_url", 
                            "image_url": {"url": f"data:image/png;base64,{after_b64}"}
                        }
                    ]
                }
            ]
            
            response = self.vision_engine.client.chat.completions.create(
                model=self.vision_engine.model,
                messages=messages,
                max_tokens=10000,
                temperature=0.1
            )
            
            # Parse verification response
            verification_text = response.choices[0].message.content
            start_idx = verification_text.find('{')
            end_idx = verification_text.rfind('}') + 1
            verification_json = json.loads(verification_text[start_idx:end_idx])
            
            return {
                'verified': verification_json.get('verified', False),
                'message': verification_json.get('message', 'No verification message'),
                'confidence': verification_json.get('confidence', 1),
                'evidence': verification_json.get('evidence', 'No evidence provided')
            }
            
        except Exception as e:
            self.logger.error(f"Error asking AI for verification: {e}")
            return {
                'verified': False,
                'message': f'Verification failed: {e}',
                'confidence': 1,
                'evidence': 'Error during verification'
            }
    
    # ---------------------------------------------------------------------
    # Utility
    # ---------------------------------------------------------------------
    def _annotate_click_location(self, screenshot: Image.Image, x: int, y: int) -> Image.Image:
        """Draw a red crosshair at the given coordinates on a copy of the screenshot."""
        from PIL import ImageDraw
        annotated = screenshot.copy()
        draw = ImageDraw.Draw(annotated)
        cross_size = 10
        color = (255, 0, 0)
        draw.line((x - cross_size, y, x + cross_size, y), fill=color, width=2)
        draw.line((x, y - cross_size, x, y + cross_size), fill=color, width=2)
        return annotated

    def _execute_click(self, action_plan: ActionPlan) -> ExecutionResult:
        """Execute click action at specified coordinates"""
        try:
            if not action_plan.coordinates:
                return ExecutionResult(False, "No coordinates provided for click action")
            
            x, y = action_plan.coordinates
            
            # Get current screen info for debugging
            screen_width, screen_height = pyautogui.size()
            current_x, current_y = pyautogui.position()
            
            self.logger.info(f"🎯 Attempting click at coordinates ({x}, {y})")
            self.logger.info(f"📺 Screen size: {screen_width}x{screen_height}, Current mouse: ({current_x}, {current_y})")
            
            # Validate coordinates are within screen bounds
            if not (0 <= x <= screen_width and 0 <= y <= screen_height):
                self.logger.warning(f"❌ Coordinates ({x}, {y}) outside screen bounds ({screen_width}x{screen_height})")
                return ExecutionResult(False, f"Coordinates outside screen bounds")
            
            # Move mouse to proposed location first (do NOT click yet)
            pyautogui.moveTo(x, y, duration=0.2)
            time.sleep(0.1)  # let cursor settle

            # Take screenshot with cursor at target position
            screenshot_pre_click = self._take_screenshot()
            before_screenshot = screenshot_pre_click  # keep original for verification later

            # Annotate screenshot so the AI can clearly see the intended point
            annotated = self._annotate_click_location(screenshot_pre_click, x, y)

            # If a VisionEngine is attached, ask it to confirm the click before proceeding
            if self.vision_engine is not None:
                attempts = 0
                while attempts < self.max_click_retries:
                    confirm_result = self.vision_engine.confirm_click(annotated, (x, y), action_plan.target_description)
                    self.logger.debug(f"AI click confirmation: {confirm_result}")

                    if confirm_result.get('confirm'):
                        break  # Proceed with click

                    # If AI suggests new coordinates, move there and try again
                    suggested = confirm_result.get('suggested_coordinates')
                    if suggested:
                        self.logger.info(f"🔄 AI suggested new coordinates {suggested}; moving and reconfirming")
                        x, y = suggested
                        pyautogui.moveTo(x, y, duration=0.2)
                        time.sleep(0.1)
                        screenshot_pre_click = self._take_screenshot()
                        before_screenshot = screenshot_pre_click
                        annotated = self._annotate_click_location(screenshot_pre_click, x, y)
                    else:
                        self.logger.warning("❌ AI did not confirm click and provided no alternative. Aborting click.")
                        return ExecutionResult(False, "Click not confirmed by AI")

                    attempts += 1

                if attempts >= self.max_click_retries and not confirm_result.get('confirm'):
                    return ExecutionResult(False, "Max confirmation attempts reached without approval")

            # Finally, click
            pyautogui.click(x, y)
            
            # Small wait after click
            time.sleep(0.5)
            
            # Log the attempt
            self.logger.info(f"🖱️ Click executed at ({x}, {y}) - waiting for verification...")
            
            return ExecutionResult(success=True, before_screenshot=before_screenshot)
            
        except Exception as e:
            return ExecutionResult(False, f"Click execution failed: {e}")
    
    def _execute_double_click(self, action_plan: ActionPlan) -> ExecutionResult:
        """Execute double-click action at specified coordinates"""
        try:
            if not action_plan.coordinates:
                return ExecutionResult(False, "No coordinates provided for double-click action")
            
            x, y = action_plan.coordinates
            self.logger.info(f"🎯 Attempting double-click at coordinates ({x}, {y})")
            
            # Take before screenshot
            before_screenshot = self._take_screenshot()
            
            # Move to position first
            pyautogui.moveTo(x, y, duration=0.2)
            time.sleep(0.1)
            
            # Double click
            pyautogui.doubleClick(x, y)
            
            # Small wait after click
            time.sleep(0.5)
            
            self.logger.info(f"🖱️ Double-click executed at ({x}, {y}) - waiting for verification...")
            return ExecutionResult(success=True, before_screenshot=before_screenshot)
            
        except Exception as e:
            return ExecutionResult(False, f"Double-click execution failed: {e}")
    
    def _execute_right_click(self, action_plan: ActionPlan) -> ExecutionResult:
        """Execute right-click action at specified coordinates"""
        try:
            if not action_plan.coordinates:
                return ExecutionResult(False, "No coordinates provided for right-click action")
            
            x, y = action_plan.coordinates
            self.logger.info(f"🎯 Attempting right-click at coordinates ({x}, {y})")
            
            # Take before screenshot
            before_screenshot = self._take_screenshot()
            
            # Move to position first
            pyautogui.moveTo(x, y, duration=0.2)
            time.sleep(0.1)
            
            # Right click
            pyautogui.rightClick(x, y)
            
            # Small wait after click
            time.sleep(0.5)
            
            self.logger.info(f"🖱️ Right-click executed at ({x}, {y}) - waiting for verification...")
            return ExecutionResult(success=True, before_screenshot=before_screenshot)
            
        except Exception as e:
            return ExecutionResult(False, f"Right-click execution failed: {e}")
    
    def _execute_type(self, action_plan: ActionPlan) -> ExecutionResult:
        """Execute type action"""
        try:
            if not action_plan.text:
                return ExecutionResult(False, "No text provided for type action")
            
            self.logger.info(f"⌨️ Attempting to type: {action_plan.text}")
            
            # Take before screenshot
            before_screenshot = self._take_screenshot()
            
            # Type the text
            pyautogui.typewrite(action_plan.text)
            
            # Small wait after typing
            time.sleep(0.3)
            
            self.logger.info(f"⌨️ Typing completed - waiting for verification...")
            return ExecutionResult(success=True, before_screenshot=before_screenshot)
            
        except Exception as e:
            return ExecutionResult(False, f"Type execution failed: {e}")
    
    def _execute_scroll(self, action_plan: ActionPlan) -> ExecutionResult:
        """Execute scroll action"""
        try:
            # Parse scroll direction and amount from target description
            direction = action_plan.target_description.lower()
            
            # Default scroll amount
            scroll_amount = 3
            
            # Try to extract scroll amount from description
            import re
            amount_match = re.search(r'(\d+)', action_plan.target_description)
            if amount_match:
                scroll_amount = int(amount_match.group(1))
            
            self.logger.info(f"📜 Attempting to scroll {direction} by {scroll_amount}")
            
            # Take before screenshot
            before_screenshot = self._take_screenshot()
            
            if 'up' in direction:
                pyautogui.scroll(scroll_amount)  # Scroll up
            elif 'down' in direction:
                pyautogui.scroll(-scroll_amount)  # Scroll down
            elif 'left' in direction:
                pyautogui.hscroll(scroll_amount)  # Scroll left
            elif 'right' in direction:
                pyautogui.hscroll(-scroll_amount)  # Scroll right
            else:
                # Default to scroll down
                pyautogui.scroll(-scroll_amount)
            
            time.sleep(0.5)
            
            self.logger.info(f"📜 Scrolling completed - waiting for verification...")
            return ExecutionResult(success=True, before_screenshot=before_screenshot)
            
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
            
            self.logger.info(f"⏳ Waiting for {wait_time} seconds")
            time.sleep(wait_time)
            return ExecutionResult(success=True)
            
        except Exception as e:
            return ExecutionResult(False, f"Wait execution failed: {e}")
    
    def _execute_verify(self, action_plan: ActionPlan) -> ExecutionResult:
        """Execute verify action - check if expected result appears"""
        try:
            # For now, just log the verification criteria
            # In a full implementation, this would use image recognition
            self.logger.info(f"🔍 Verifying: {action_plan.verification_criteria}")
            
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
        """Execute navigate action - this should be clicking on UI elements, not keyboard shortcuts"""
        try:
            # Parse navigation target from description
            target = action_plan.target_description.lower()
            
            # If coordinates are provided, click there
            if action_plan.coordinates:
                x, y = action_plan.coordinates
                self.logger.info(f"🧭 Attempting navigation by clicking at ({x}, {y})")
                
                # Take before screenshot
                before_screenshot = self._take_screenshot()
                
                pyautogui.moveTo(x, y, duration=0.2)
                time.sleep(0.1)
                pyautogui.click(x, y)
                time.sleep(1.0)
                
                self.logger.info(f"🧭 Navigation click executed - waiting for verification...")
                return ExecutionResult(success=True, before_screenshot=before_screenshot)
            
            # Fallback to keyboard shortcuts for common navigation
            self.logger.info(f"🧭 Attempting navigation with keyboard shortcuts: {target}")
            
            # Take before screenshot
            before_screenshot = self._take_screenshot()
            
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
            
            time.sleep(1.0)  # Wait for navigation to complete
            
            self.logger.info(f"🧭 Navigation completed - waiting for verification...")
            return ExecutionResult(success=True, before_screenshot=before_screenshot)
            
        except Exception as e:
            return ExecutionResult(False, f"Navigate execution failed: {e}")
    
    def _execute_hotkey(self, action_plan: ActionPlan) -> ExecutionResult:
        """Execute hotkey combination"""
        try:
            if not action_plan.text:
                return ExecutionResult(False, "No hotkey combination provided")
            
            self.logger.info(f"⌨️ Attempting hotkey: {action_plan.text}")
            
            # Take before screenshot
            before_screenshot = self._take_screenshot()
            
            # Parse hotkey combination (e.g., "ctrl+c", "cmd+space")
            keys = action_plan.text.split('+')
            pyautogui.hotkey(*keys)
            time.sleep(0.5)
            
            self.logger.info(f"⌨️ Hotkey executed - waiting for verification...")
            return ExecutionResult(success=True, before_screenshot=before_screenshot)
            
        except Exception as e:
            return ExecutionResult(False, f"Hotkey execution failed: {e}")
    
    def _execute_move(self, action_plan: ActionPlan) -> ExecutionResult:
        """Execute mouse move action"""
        try:
            if not action_plan.coordinates:
                return ExecutionResult(False, "No coordinates provided for move action")
            
            x, y = action_plan.coordinates
            self.logger.info(f"🖱️ Moving mouse to ({x}, {y})")
            
            pyautogui.moveTo(x, y, duration=0.5)
            time.sleep(0.2)
            return ExecutionResult(success=True)
            
        except Exception as e:
            return ExecutionResult(False, f"Move execution failed: {e}")
    
    def _execute_drag(self, action_plan: ActionPlan) -> ExecutionResult:
        """Execute drag action"""
        try:
            # Parse drag coordinates from target description or use provided coordinates
            # Format: "drag from x1,y1 to x2,y2" or use coordinates for start point
            target = action_plan.target_description.lower()
            
            import re
            coords_match = re.search(r'from\s+(\d+),(\d+)\s+to\s+(\d+),(\d+)', target)
            
            if coords_match:
                x1, y1, x2, y2 = map(int, coords_match.groups())
            elif action_plan.coordinates:
                # Use provided coordinates as start point, need end point
                x1, y1 = action_plan.coordinates
                # For now, drag a small distance
                x2, y2 = x1 + 100, y1 + 100
            else:
                return ExecutionResult(False, "No drag coordinates provided")
            
            self.logger.info(f"🖱️ Attempting drag from ({x1}, {y1}) to ({x2}, {y2})")
            
            # Take before screenshot
            before_screenshot = self._take_screenshot()
            
            pyautogui.moveTo(x1, y1, duration=0.2)
            time.sleep(0.1)
            pyautogui.drag(x2 - x1, y2 - y1, duration=0.5)
            time.sleep(0.2)
            
            self.logger.info(f"🖱️ Drag completed - waiting for verification...")
            return ExecutionResult(success=True, before_screenshot=before_screenshot)
            
        except Exception as e:
            return ExecutionResult(False, f"Drag execution failed: {e}")
    
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
    
    def debug_coordinate_mapping(self, screenshot: Image.Image) -> dict:
        """Debug coordinate mapping between screenshot and screen"""
        try:
            screenshot_width, screenshot_height = screenshot.size
            screen_width, screen_height = pyautogui.size()
            
            scale_x = screen_width / screenshot_width
            scale_y = screen_height / screenshot_height
            
            return {
                'screenshot_size': (screenshot_width, screenshot_height),
                'screen_size': (screen_width, screen_height),
                'scale_factors': (scale_x, scale_y),
                'current_mouse': pyautogui.position()
            }
        except Exception as e:
            self.logger.error(f"Failed to debug coordinate mapping: {e}")
            return {} 