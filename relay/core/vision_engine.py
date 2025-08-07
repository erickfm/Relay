"""
Vision Engine - Core component for o3-mini integration
Handles screenshot analysis and action planning
"""

import base64
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from PIL import Image
import io
import openai
import pyautogui
from dataclasses import dataclass

@dataclass
class ActionPlan:
    """Represents a planned action with confidence scoring"""
    action_type: str  # 'click', 'type', 'scroll', 'wait', 'verify', 'navigate', 'hotkey', 'move', 'double_click', 'right_click', 'drag'
    target_description: str
    coordinates: Optional[Tuple[int, int]] = None
    text: Optional[str] = None
    confidence: int = 5  # 1-10 scale
    reasoning: str = ""
    verification_criteria: Optional[str] = None

@dataclass
class VisionContext:
    """Maintains context for vision processing"""
    task_description: str
    previous_actions: List[ActionPlan]
    screenshots_history: List[str]  # base64 encoded
    current_screenshot: str
    iteration_count: int = 0

class VisionEngine:
    """Handles o3-mini integration for screenshot analysis and action planning"""
    
    def __init__(self, api_key: str, model: str = "o3-mini"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.logger = logging.getLogger(__name__)
        
        # Safety boundaries
        self.max_iterations = 50
        self.confidence_threshold = 3
        self.destructive_actions = ['delete', 'format', 'uninstall', 'shutdown']
        
    def analyze_screenshot(self, screenshot: Image.Image, context: VisionContext) -> ActionPlan:
        """
        Analyze screenshot and return next action plan
        """
        try:
            # Convert screenshot to base64
            buffer = io.BytesIO()
            screenshot.save(buffer, format='PNG')
            screenshot_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # Get screen information for coordinate mapping
            screen_info = self._get_screen_info()
            
            # Prepare context for o3-mini
            messages = self._build_context_messages(context, screenshot_b64, screen_info)
            
            # Debug: log prompt being sent
            if self.logger.isEnabledFor(logging.DEBUG):
                self._log_prompt(messages)
            
            # Get response from o3-mini
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=10000,
                temperature=0.1
            )
            
            # Debug: log raw response
            if self.logger.isEnabledFor(logging.DEBUG):
                self._log_response(response.choices[0].message.content)
            
            # Parse response into action plan
            action_plan = self._parse_action_response(response.choices[0].message.content)
            
            # Map coordinates from screenshot space to screen space
            if action_plan.coordinates:
                action_plan.coordinates = self._map_coordinates(action_plan.coordinates, screenshot, screen_info)
            
            # Validate action plan
            if not self._validate_action_plan(action_plan):
                raise ValueError("Invalid action plan generated")
                
            return action_plan
            
        except Exception as e:
            self.logger.error(f"Error in vision analysis: {e}")
            return self._create_fallback_action()
    
    def _get_screen_info(self) -> Dict[str, int]:
        """Get current screen information"""
        try:
            width, height = pyautogui.size()
            return {
                'screen_width': width,
                'screen_height': height
            }
        except Exception as e:
            self.logger.error(f"Failed to get screen info: {e}")
            return {'screen_width': 1920, 'screen_height': 1080}  # fallback
    
    def _map_coordinates(self, screenshot_coords: Tuple[int, int], screenshot: Image.Image, screen_info: Dict[str, int]) -> Tuple[int, int]:
        """
        Map coordinates from screenshot space to actual screen space
        Handles display scaling, multiple monitors, etc.
        """
        try:
            screenshot_x, screenshot_y = screenshot_coords
            screenshot_width, screenshot_height = screenshot.size
            # If coords appear to be ratios (0-1), convert to pixels first
            if 0 <= screenshot_x <= 1 and 0 <= screenshot_y <= 1:
                screenshot_x = screenshot_x * screenshot_width
                screenshot_y = screenshot_y * screenshot_height
            screen_width = screen_info['screen_width']
            screen_height = screen_info['screen_height']
            
            # Calculate scaling factors
            scale_x = screen_width / screenshot_width
            scale_y = screen_height / screenshot_height
            
            # Map coordinates
            screen_x = int(screenshot_x * scale_x)
            screen_y = int(screenshot_y * scale_y)
            
            self.logger.info(f"Coordinate mapping: ({screenshot_x}, {screenshot_y}) -> ({screen_x}, {screen_y})")
            self.logger.info(f"Scaling factors: x={scale_x:.2f}, y={scale_y:.2f}")
            
            return (screen_x, screen_y)
            
        except Exception as e:
            self.logger.error(f"Coordinate mapping failed: {e}")
            return screenshot_coords  # fallback to original coordinates

    # ---------------------------------------------------------------------
    # Click confirmation helper
    # ---------------------------------------------------------------------
    def confirm_click(self, screenshot: Image.Image, coordinates: Tuple[int, int], target_description: str) -> Dict[str, Any]:
        """Ask the model to confirm that clicking at the given coordinates is correct.

        Returns a dict with:
            confirm (bool): Whether to proceed.
            suggested_coordinates (Tuple[int,int]|None): Alternative coords if any.
            confidence (int): 1-10 confidence.
            reasoning (str): Explanation.
        """
        try:
            # Encode screenshot
            import base64, io, json
            buf = io.BytesIO(); screenshot.save(buf, format='PNG')
            b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

            system_prompt = """
            You are a UI click-confirmation assistant. The automation system plans to click at the given pixel
            coordinates to interact with the target element. Your job is to confirm whether this location looks
            correct. If it does, return {\"confirm\": true}. If not, return {\"confirm\": false} and, if you can
            visually identify a better location to click, include it in \"suggested_coordinates\" as an array
            [x, y] relative to the screenshot.

            RESPONSE FORMAT:
            {"confirm": true/false, "suggested_coordinates": [x, y] | null, "confidence": 1-10, "reasoning": "..."}
            """

            user_text = f"Target description: {target_description}\nPlanned click coordinates: {coordinates}.\nDoes this look correct?"

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "text", "text": user_text},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
                ]}
            ]

            # Debug log
            if self.logger.isEnabledFor(logging.DEBUG):
                self._log_prompt(messages)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1000,
                temperature=0.1
            )

            response_text = response.choices[0].message.content
            if self.logger.isEnabledFor(logging.DEBUG):
                self._log_response(response_text)

            start = response_text.find('{'); end = response_text.rfind('}') + 1
            data = json.loads(response_text[start:end])

            return {
                'confirm': bool(data.get('confirm', False)),
                'suggested_coordinates': tuple(data['suggested_coordinates']) if data.get('suggested_coordinates') else None,
                'confidence': data.get('confidence', 1),
                'reasoning': data.get('reasoning', '')
            }
        except Exception as e:
            self.logger.error(f"Click confirmation failed: {e}")
            return {'confirm': False, 'suggested_coordinates': None, 'confidence': 1, 'reasoning': str(e)}
    
    def _build_context_messages(self, context: VisionContext, screenshot_b64: str, screen_info: Dict[str, int]) -> List[Dict]:
        """Build messages for o3-mini with proper context"""
        
        system_prompt = f"""
        You are RELAY, a vision-guided desktop assistant. Your job is to analyze screenshots and plan the next action to accomplish user tasks.

        TASK: {context.task_description}

        SCREEN INFORMATION:
        - Actual screen resolution: {screen_info['screen_width']}x{screen_info['screen_height']} pixels
        - Screenshot dimensions: You will see the screenshot dimensions in the image
        - IMPORTANT: Provide coordinates based on the screenshot image, not the actual screen
        - The system will automatically map screenshot coordinates to screen coordinates

        CRITICAL REQUIREMENTS:
        - Prefer returning coordinates_pct which are the element center position as ratios (0.0-1.0) of screenshot width and height. Example: coordinates_pct: [0.25, 0.9] means 25% from left, 90% from top.
        - If coordinates_pct is provided the system will convert them to absolute pixels automatically.
        - You may still return integer pixel coordinates in "coordinates"; but coordinates_pct is recommended to avoid scaling errors.
        - For ANY click, double_click, right_click, or navigate action, you MUST provide exact pixel coordinates [x, y]
        - Look at the screenshot and identify the exact pixel location of UI elements
        - Do NOT make up coordinates - only provide coordinates for elements you can actually see
        - If you cannot see the target element, use 'wait' or 'scroll' to find it
        - Be precise about coordinates - this is how the system will actually click
        - Provide coordinates relative to the screenshot image, not the actual screen

        SAFETY RULES:
        - Never suggest destructive actions without explicit user confirmation
        - Rate confidence 1-10 for each action (1=very unsure, 10=very confident)
        - If confidence < 4, suggest alternative approaches
        - Avoid actions that could cause data loss
        - Prioritize user safety and data protection

        ACTION TYPES:
        - click: Click on UI element (REQUIRES coordinates [x, y])
        - double_click: Double-click on UI element (REQUIRES coordinates [x, y])
        - right_click: Right-click on UI element (REQUIRES coordinates [x, y])
        - type: Type text into field (no coordinates needed)
        - scroll: Scroll up/down/left/right (no coordinates needed)
        - wait: Wait for loading/processing (no coordinates needed)
        - verify: Check if expected result appears (no coordinates needed)
        - navigate: Click on navigation element (REQUIRES coordinates [x, y])
        - hotkey: Use keyboard shortcuts (provide in 'text' field like "cmd+space")
        - move: Move mouse to position (REQUIRES coordinates [x, y])
        - drag: Drag from one position to another (REQUIRES coordinates [x, y])

        RESPONSE FORMAT:
        {{
            "action_type": "click|double_click|right_click|type|scroll|wait|verify|navigate|hotkey|move|drag",
            "target_description": "Clear description of what to interact with",
            "coordinates": [x, y] or null,
            "coordinates_pct": [x_ratio, y_ratio] or null,
            "text": "Text to type (for type actions) or hotkey combination (for hotkey actions)",
            "confidence": 1-10,
            "reasoning": "Why this action is needed and how you identified the target",
            "verification_criteria": "What to look for to confirm success"
        }}

        Previous actions taken: {len(context.previous_actions)}
        Current iteration: {context.iteration_count}
        """
        
        # Add recent action history for context
        recent_actions = context.previous_actions[-5:] if context.previous_actions else []
        action_history = ""
        for i, action in enumerate(recent_actions):
            coords_str = f" at ({action.coordinates[0]}, {action.coordinates[1]})" if action.coordinates else ""
            action_history += f"{i+1}. {action.action_type}: {action.target_description}{coords_str} (confidence: {action.confidence})\n"
        
        if action_history:
            system_prompt += f"\nRecent actions:\n{action_history}"
        
        return [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Analyze this screenshot and tell me what action to take next to accomplish the task. If you need to click something, provide the exact pixel coordinates where to click. The screenshot is {screen_info['screen_width']}x{screen_info['screen_height']} pixels."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{screenshot_b64}"
                        }
                    }
                ]
            }
        ]
    
    def _parse_action_response(self, response_text: str) -> ActionPlan:
        """Parse o3-mini response into structured ActionPlan"""
        try:
            # Extract JSON from response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            json_str = response_text[start_idx:end_idx]
            
            data = json.loads(json_str)
            
            # Parse coordinates if present
            coordinates = None
            if data.get('coordinates_pct') and len(data['coordinates_pct']) == 2:
                # convert percentage to screenshot pixel coords later in mapping
                coordinates = tuple(data['coordinates_pct'])
                # mark as percentage by storing float ratios >1? we store as negative to mark? We'll handle below
                pct_flag = True
            elif data.get('coordinates') and len(data['coordinates']) == 2:
                coordinates = tuple(data['coordinates'])
                pct_flag = False
            else:
                pct_flag = False
            
            return ActionPlan(
                action_type=data.get('action_type', 'wait'),
                target_description=data.get('target_description', 'Unknown target'),
                coordinates=coordinates,
                text=data.get('text'),
                confidence=data.get('confidence', 5),
                reasoning=data.get('reasoning', ''),
                verification_criteria=data.get('verification_criteria')
            )
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Failed to parse action response: {e}")
            return self._create_fallback_action()
    
    def _validate_action_plan(self, action_plan: ActionPlan) -> bool:
        """Validate action plan for safety and completeness"""
        
        # Check for destructive actions
        if any(destructive in action_plan.target_description.lower() 
               for destructive in self.destructive_actions):
            if action_plan.confidence < 8:
                self.logger.warning("Low confidence destructive action detected")
                return False
        
        # Validate confidence range
        if not 1 <= action_plan.confidence <= 10:
            return False
        
        # Validate action types
        valid_types = ['click', 'double_click', 'right_click', 'type', 'scroll', 'wait', 'verify', 'navigate', 'hotkey', 'move', 'drag']
        if action_plan.action_type not in valid_types:
            return False
        
        # Validate that click actions have coordinates
        click_actions = ['click', 'double_click', 'right_click', 'navigate', 'move', 'drag']
        if action_plan.action_type in click_actions and not action_plan.coordinates:
            self.logger.warning(f"{action_plan.action_type} action requires coordinates")
            return False
        
        return True
    # ---------------------------------------------------------------------
    # Debug helpers
    # ---------------------------------------------------------------------
    def _shorten_text(self, text: str, max_len: int = 400) -> str:
        """Return a shortened preview of text without newlines."""
        text = text.replace("\n", " ").strip()
        if len(text) > max_len:
            return text[:max_len] + "..."
        return text

    def _log_prompt(self, messages: List[Dict]):
        """Pretty print the prompt that will be sent to the AI model."""
        separator = "=" * 60
        self.logger.debug("%s\n📤 Prompt sent to model:", separator)
        for msg in messages:
            if msg["role"] == "system":
                content_preview = self._shorten_text(msg["content"])
                self.logger.debug("[SYSTEM] %s", content_preview)
            else:
                user_parts = []
                content_field = msg.get("content", [])
                if isinstance(content_field, list):
                    for part in content_field:
                        if part.get("type") == "text":
                            user_parts.append(self._shorten_text(part["text"]))
                        elif part.get("type") == "image_url":
                            user_parts.append("<image>")
                else:
                    user_parts.append(self._shorten_text(str(content_field)))
                self.logger.debug("[USER] %s", " ".join(user_parts))
        self.logger.debug(separator)

    def _log_response(self, response_text: str):
        """Pretty print the raw model response."""
        separator = "=" * 60
        self.logger.debug("%s\n📥 Raw model response:\n%s\n%s", separator, response_text.strip(), separator)

    def _create_fallback_action(self) -> ActionPlan:
        """Create a safe fallback action when analysis fails"""
        return ActionPlan(
            action_type='wait',
            target_description='Waiting for system to stabilize',
            confidence=1,
            reasoning='Vision analysis failed, taking safe fallback action',
            verification_criteria='Screen appears stable'
        )
    
    def diagnose_failure(self, before_screenshot: Image.Image, after_screenshot: Image.Image, 
                        action_plan: ActionPlan) -> str:
        """
        Diagnose why an action failed by comparing before/after screenshots
        """
        try:
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
                    You are a failure diagnosis expert. Analyze before/after screenshots to determine why an automation action failed.
                    
                    FAILURE TYPES:
                    - timing: Action executed too quickly/slowly
                    - wrong_element: Clicked on wrong UI element
                    - ui_change: Interface changed between screenshots
                    - loading: Page/application still loading
                    - permission: Access denied or permission required
                    - network: Network connectivity issues
                    - coordinates: Wrong coordinates provided
                    - unknown: Unable to determine cause
                    
                    RESPONSE FORMAT:
                    {
                        "failure_type": "timing|wrong_element|ui_change|loading|permission|network|coordinates|unknown",
                        "confidence": 1-10,
                        "explanation": "Detailed explanation of the failure",
                        "suggested_fix": "How to address this failure"
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
                            Confidence: {action_plan.confidence}
                            Reasoning: {action_plan.reasoning}
                            
                            Analyze these screenshots to determine why the action failed.
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
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=10000,
                temperature=0.1
            )
            
            # Parse diagnosis
            diagnosis_text = response.choices[0].message.content
            start_idx = diagnosis_text.find('{')
            end_idx = diagnosis_text.rfind('}') + 1
            diagnosis_json = json.loads(diagnosis_text[start_idx:end_idx])
            
            return diagnosis_json.get('failure_type', 'unknown')
            
        except Exception as e:
            self.logger.error(f"Error in failure diagnosis: {e}")
            return 'unknown' 