"""
Unit tests for Vision Engine
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import json

from relay.core.vision_engine import VisionEngine, ActionPlan, VisionContext

class TestVisionEngine(unittest.TestCase):
    """Test cases for VisionEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.api_key = "test-api-key"
        self.vision_engine = VisionEngine(self.api_key)
        
        # Create a mock screenshot
        self.mock_screenshot = Image.new('RGB', (1920, 1080), color='white')
        
        # Create a mock context
        self.mock_context = VisionContext(
            task_description="Test task",
            previous_actions=[],
            screenshots_history=[],
            current_screenshot="",
            iteration_count=0
        )
    
    def test_initialization(self):
        """Test VisionEngine initialization"""
        self.assertEqual(self.vision_engine.model, "gpt-4-vision-preview")
        self.assertEqual(self.vision_engine.max_iterations, 50)
        self.assertEqual(self.vision_engine.confidence_threshold, 3)
        self.assertIn('delete', self.vision_engine.destructive_actions)
    
    @patch('relay.core.vision_engine.openai.OpenAI')
    def test_analyze_screenshot_success(self, mock_openai):
        """Test successful screenshot analysis"""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "action_type": "click",
            "target_description": "Click the login button",
            "coordinates": [100, 200],
            "confidence": 8,
            "reasoning": "I can see a login button at these coordinates",
            "verification_criteria": "Login form should appear"
        }
        '''
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Test analysis
        action_plan = self.vision_engine.analyze_screenshot(
            self.mock_screenshot, 
            self.mock_context
        )
        
        # Verify result
        self.assertIsInstance(action_plan, ActionPlan)
        self.assertEqual(action_plan.action_type, "click")
        self.assertEqual(action_plan.target_description, "Click the login button")
        self.assertEqual(action_plan.coordinates, (100, 200))
        self.assertEqual(action_plan.confidence, 8)
        self.assertEqual(action_plan.reasoning, "I can see a login button at these coordinates")
        self.assertEqual(action_plan.verification_criteria, "Login form should appear")
    
    @patch('relay.core.vision_engine.openai.OpenAI')
    def test_analyze_screenshot_fallback(self, mock_openai):
        """Test fallback when analysis fails"""
        # Mock OpenAI to raise exception
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client
        
        # Test analysis
        action_plan = self.vision_engine.analyze_screenshot(
            self.mock_screenshot, 
            self.mock_context
        )
        
        # Verify fallback action
        self.assertIsInstance(action_plan, ActionPlan)
        self.assertEqual(action_plan.action_type, "wait")
        self.assertIn("fallback", action_plan.reasoning.lower())
    
    def test_validate_action_plan_valid(self):
        """Test validation of valid action plan"""
        action_plan = ActionPlan(
            action_type="click",
            target_description="Click button",
            coordinates=(100, 200),
            confidence=7
        )
        
        self.assertTrue(self.vision_engine._validate_action_plan(action_plan))
    
    def test_validate_action_plan_invalid_type(self):
        """Test validation of invalid action type"""
        action_plan = ActionPlan(
            action_type="invalid_action",
            target_description="Do something",
            confidence=5
        )
        
        self.assertFalse(self.vision_engine._validate_action_plan(action_plan))
    
    def test_validate_action_plan_low_confidence_destructive(self):
        """Test validation of low confidence destructive action"""
        action_plan = ActionPlan(
            action_type="click",
            target_description="Delete important file",
            confidence=3
        )
        
        self.assertFalse(self.vision_engine._validate_action_plan(action_plan))
    
    def test_validate_action_plan_high_confidence_destructive(self):
        """Test validation of high confidence destructive action"""
        action_plan = ActionPlan(
            action_type="click",
            target_description="Delete important file",
            confidence=9
        )
        
        self.assertTrue(self.vision_engine._validate_action_plan(action_plan))
    
    def test_validate_action_plan_invalid_confidence(self):
        """Test validation of invalid confidence level"""
        action_plan = ActionPlan(
            action_type="click",
            target_description="Click button",
            confidence=15  # Invalid confidence
        )
        
        self.assertFalse(self.vision_engine._validate_action_plan(action_plan))
    
    def test_create_fallback_action(self):
        """Test creation of fallback action"""
        fallback = self.vision_engine._create_fallback_action()
        
        self.assertIsInstance(fallback, ActionPlan)
        self.assertEqual(fallback.action_type, "wait")
        self.assertEqual(fallback.confidence, 1)
        self.assertIn("fallback", fallback.reasoning.lower())
    
    def test_parse_action_response_valid_json(self):
        """Test parsing valid JSON response"""
        response_text = '''
        {
            "action_type": "type",
            "target_description": "Enter username",
            "text": "testuser",
            "confidence": 9,
            "reasoning": "Username field is visible",
            "verification_criteria": "Username should be entered"
        }
        '''
        
        action_plan = self.vision_engine._parse_action_response(response_text)
        
        self.assertEqual(action_plan.action_type, "type")
        self.assertEqual(action_plan.target_description, "Enter username")
        self.assertEqual(action_plan.text, "testuser")
        self.assertEqual(action_plan.confidence, 9)
        self.assertEqual(action_plan.reasoning, "Username field is visible")
        self.assertEqual(action_plan.verification_criteria, "Username should be entered")
    
    def test_parse_action_response_invalid_json(self):
        """Test parsing invalid JSON response"""
        response_text = "Invalid JSON response"
        
        action_plan = self.vision_engine._parse_action_response(response_text)
        
        # Should return fallback action
        self.assertEqual(action_plan.action_type, "wait")
        self.assertEqual(action_plan.confidence, 1)
    
    def test_parse_action_response_with_coordinates(self):
        """Test parsing response with coordinates"""
        response_text = '''
        {
            "action_type": "click",
            "target_description": "Click here",
            "coordinates": [500, 300],
            "confidence": 8,
            "reasoning": "Button is at these coordinates"
        }
        '''
        
        action_plan = self.vision_engine._parse_action_response(response_text)
        
        self.assertEqual(action_plan.coordinates, (500, 300))
    
    def test_parse_action_response_no_coordinates(self):
        """Test parsing response without coordinates"""
        response_text = '''
        {
            "action_type": "wait",
            "target_description": "Wait for loading",
            "confidence": 5,
            "reasoning": "Page is loading"
        }
        '''
        
        action_plan = self.vision_engine._parse_action_response(response_text)
        
        self.assertIsNone(action_plan.coordinates)
    
    @patch('relay.core.vision_engine.openai.OpenAI')
    def test_diagnose_failure(self, mock_openai):
        """Test failure diagnosis"""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "failure_type": "timing",
            "confidence": 8,
            "explanation": "Action executed too quickly",
            "suggested_fix": "Wait longer before next action"
        }
        '''
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Create mock action plan
        action_plan = ActionPlan(
            action_type="click",
            target_description="Click button",
            confidence=7
        )
        
        # Test diagnosis
        failure_type = self.vision_engine.diagnose_failure(
            self.mock_screenshot,
            self.mock_screenshot,  # Same screenshot for simplicity
            action_plan
        )
        
        self.assertEqual(failure_type, "timing")
    
    @patch('relay.core.vision_engine.openai.OpenAI')
    def test_diagnose_failure_error(self, mock_openai):
        """Test failure diagnosis with error"""
        # Mock OpenAI to raise exception
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client
        
        action_plan = ActionPlan(
            action_type="click",
            target_description="Click button",
            confidence=7
        )
        
        # Test diagnosis
        failure_type = self.vision_engine.diagnose_failure(
            self.mock_screenshot,
            self.mock_screenshot,
            action_plan
        )
        
        self.assertEqual(failure_type, "unknown")

if __name__ == '__main__':
    unittest.main() 