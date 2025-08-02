"""
Vision Engine - Core component for GPT-4V integration
Handles screenshot analysis and action planning
"""

import base64
import json
import logging
from typing import Dict, List, Tuple, Optional
from PIL import Image
import io
import openai
from dataclasses import dataclass

@dataclass
class ActionPlan:
    """Represents a planned action with confidence scoring"""
    action_type: str  # 'click', 'type', 'scroll', 'wait', 'verify'
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
    """Handles GPT-4V integration for screenshot analysis and action planning"""
    
    def __init__(self, api_key: str, model: str = "gpt-4-vision-preview"):
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
            
            # Prepare context for GPT-4V
            messages = self._build_context_messages(context, screenshot_b64)
            
            # Get response from GPT-4V
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1000,
                temperature=0.1
            )
            
            # Parse response into action plan
            action_plan = self._parse_action_response(response.choices[0].message.content)
            
            # Validate action plan
            if not self._validate_action_plan(action_plan):
                raise ValueError("Invalid action plan generated")
                
            return action_plan
            
        except Exception as e:
            self.logger.error(f"Error in vision analysis: {e}")
            return self._create_fallback_action()
    
    def _build_context_messages(self, context: VisionContext, screenshot_b64: str) -> List[Dict]:
        """Build messages for GPT-4V with proper context"""
        
        system_prompt = f"""
        You are RELAY, a vision-guided desktop assistant. Your job is to analyze screenshots and plan the next action to accomplish user tasks.

        TASK: {context.task_description}

        SAFETY RULES:
        - Never suggest destructive actions without explicit user confirmation
        - Rate confidence 1-10 for each action (1=very unsure, 10=very confident)
        - If confidence < 4, suggest alternative approaches
        - Avoid actions that could cause data loss
        - Prioritize user safety and data protection

        ACTION TYPES:
        - click: Click on UI element (provide coordinates if visible)
        - type: Type text into field
        - scroll: Scroll up/down/left/right
        - wait: Wait for loading/processing
        - verify: Check if expected result appears
        - navigate: Navigate to different screen/app

        RESPONSE FORMAT:
        {{
            "action_type": "click|type|scroll|wait|verify|navigate",
            "target_description": "Clear description of what to interact with",
            "coordinates": [x, y] or null,
            "text": "Text to type (for type actions)",
            "confidence": 1-10,
            "reasoning": "Why this action is needed",
            "verification_criteria": "What to look for to confirm success"
        }}

        Previous actions taken: {len(context.previous_actions)}
        Current iteration: {context.iteration_count}
        """
        
        # Add recent action history for context
        recent_actions = context.previous_actions[-5:] if context.previous_actions else []
        action_history = ""
        for i, action in enumerate(recent_actions):
            action_history += f"{i+1}. {action.action_type}: {action.target_description} (confidence: {action.confidence})\n"
        
        if action_history:
            system_prompt += f"\nRecent actions:\n{action_history}"
        
        return [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Analyze this screenshot and tell me what action to take next to accomplish the task."
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
        """Parse GPT-4V response into structured ActionPlan"""
        try:
            # Extract JSON from response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            json_str = response_text[start_idx:end_idx]
            
            data = json.loads(json_str)
            
            # Parse coordinates if present
            coordinates = None
            if data.get('coordinates') and len(data['coordinates']) == 2:
                coordinates = tuple(data['coordinates'])
            
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
        valid_types = ['click', 'type', 'scroll', 'wait', 'verify', 'navigate']
        if action_plan.action_type not in valid_types:
            return False
        
        return True
    
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
                    - unknown: Unable to determine cause
                    
                    RESPONSE FORMAT:
                    {
                        "failure_type": "timing|wrong_element|ui_change|loading|permission|network|unknown",
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
                max_tokens=500,
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