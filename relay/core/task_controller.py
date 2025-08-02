"""
Task Controller - Main orchestrator for RELAY automation tasks
Coordinates vision analysis, action execution, and task completion
"""

import time
import logging
import threading
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from PIL import Image
import pyautogui

from .vision_engine import VisionEngine, VisionContext, ActionPlan
from .automation_engine import AutomationEngine, ExecutionResult

@dataclass
class TaskStatus:
    """Current status of a task execution"""
    is_running: bool = False
    is_complete: bool = False
    current_iteration: int = 0
    total_actions: int = 0
    successful_actions: int = 0
    failed_actions: int = 0
    current_action: Optional[str] = None
    error_message: Optional[str] = None
    start_time: Optional[float] = None
    estimated_completion: Optional[float] = None

class TaskController:
    """Main controller for orchestrating RELAY automation tasks"""
    
    def __init__(self, vision_engine: VisionEngine, automation_engine: AutomationEngine):
        self.vision_engine = vision_engine
        self.automation_engine = automation_engine
        self.logger = logging.getLogger(__name__)
        
        # Task state
        self.current_task: Optional[str] = None
        self.task_status = TaskStatus()
        self.context: Optional[VisionContext] = None
        
        # Control flags
        self.should_stop = False
        self.is_paused = False
        
        # Callbacks for UI updates
        self.status_callbacks: List[Callable] = []
        self.narration_callbacks: List[Callable] = []
        self.completion_callbacks: List[Callable] = []
        
        # Task limits and safety
        self.max_iterations = 50
        self.max_failures = 10
        self.iteration_timeout = 60.0  # seconds
        
        # Failure tracking
        self.consecutive_failures = 0
        self.failure_history: List[Dict[str, Any]] = []
        
    def execute_task(self, task_description: str, 
                    on_status_update: Optional[Callable] = None,
                    on_narration: Optional[Callable] = None,
                    on_completion: Optional[Callable] = None) -> bool:
        """
        Execute a complete automation task
        """
        if self.task_status.is_running:
            self.logger.warning("Task already running")
            return False
        
        # Setup callbacks
        if on_status_update:
            self.status_callbacks.append(on_status_update)
        if on_narration:
            self.narration_callbacks.append(on_narration)
        if on_completion:
            self.completion_callbacks.append(on_completion)
        
        # Initialize task
        self.current_task = task_description
        self.task_status = TaskStatus(
            is_running=True,
            start_time=time.time()
        )
        self.should_stop = False
        self.is_paused = False
        self.consecutive_failures = 0
        self.failure_history = []
        
        # Start task execution in separate thread
        task_thread = threading.Thread(target=self._execute_task_loop)
        task_thread.daemon = True
        task_thread.start()
        
        return True
    
    def _execute_task_loop(self):
        """Main task execution loop"""
        try:
            self.logger.info(f"Starting task: {self.current_task}")
            self._narrate(f"Starting task: {self.current_task}")
            
            # Initialize context
            self.context = VisionContext(
                task_description=self.current_task,
                previous_actions=[],
                screenshots_history=[],
                current_screenshot=""
            )
            
            # Main execution loop
            while (self.task_status.current_iteration < self.max_iterations and 
                   not self.should_stop and 
                   not self.task_status.is_complete):
                
                # Check for pause
                if self.is_paused:
                    time.sleep(0.5)
                    continue
                
                # Check for emergency stop
                if self.automation_engine.emergency_stop:
                    self._handle_emergency_stop()
                    break
                
                # Execute single iteration
                success = self._execute_iteration()
                
                if not success:
                    self.consecutive_failures += 1
                    if self.consecutive_failures >= self.max_failures:
                        self._handle_max_failures()
                        break
                else:
                    self.consecutive_failures = 0
                
                # Update status
                self._update_status()
                
                # Small delay between iterations
                time.sleep(0.1)
            
            # Task completion
            self._handle_task_completion()
            
        except Exception as e:
            self.logger.error(f"Error in task execution: {e}")
            self._handle_task_error(str(e))
    
    def _execute_iteration(self) -> bool:
        """Execute a single task iteration"""
        iteration_start = time.time()
        self.task_status.current_iteration += 1
        
        try:
            # Take screenshot
            screenshot = self._take_screenshot()
            if not screenshot:
                return False
            
            # Update context
            self.context.current_screenshot = self._screenshot_to_base64(screenshot)
            self.context.iteration_count = self.task_status.current_iteration
            
            # Analyze screenshot and plan action
            self._narrate("Analyzing current screen...")
            action_plan = self.vision_engine.analyze_screenshot(screenshot, self.context)
            
            if not action_plan:
                self.logger.error("Failed to generate action plan")
                return False
            
            # Update current action
            self.task_status.current_action = f"{action_plan.action_type}: {action_plan.target_description}"
            self._narrate(f"Planning: {action_plan.reasoning}")
            
            # Check confidence level
            if action_plan.confidence < 4:
                self._narrate(f"Low confidence action ({action_plan.confidence}/10), proceeding carefully")
            
            # Execute action
            self._narrate(f"Executing: {action_plan.action_type} - {action_plan.target_description}")
            execution_result = self.automation_engine.execute_action(action_plan, screenshot)
            
            # Handle execution result
            if execution_result.success:
                self._handle_successful_action(action_plan, execution_result)
                return True
            else:
                self._handle_failed_action(action_plan, execution_result)
                return False
            
        except Exception as e:
            self.logger.error(f"Error in iteration {self.task_status.current_iteration}: {e}")
            self._narrate(f"Error occurred: {str(e)}")
            return False
    
    def _handle_successful_action(self, action_plan: ActionPlan, result: ExecutionResult):
        """Handle successful action execution"""
        self.task_status.successful_actions += 1
        self.task_status.total_actions += 1
        
        # Add to context history
        self.context.previous_actions.append(action_plan)
        
        # Add screenshot to history (keep last 10)
        if result.after_screenshot:
            screenshot_b64 = self._screenshot_to_base64(result.after_screenshot)
            self.context.screenshots_history.append(screenshot_b64)
            if len(self.context.screenshots_history) > 10:
                self.context.screenshots_history.pop(0)
        
        self._narrate(f"Success! Action completed in {result.execution_time:.2f}s")
        
        # Check if task is complete
        if action_plan.action_type == 'verify' and action_plan.verification_criteria:
            self._narrate("Verification criteria met - task may be complete")
            # In a full implementation, you'd do more sophisticated completion detection
    
    def _handle_failed_action(self, action_plan: ActionPlan, result: ExecutionResult):
        """Handle failed action execution"""
        self.task_status.failed_actions += 1
        self.task_status.total_actions += 1
        
        # Record failure
        failure_record = {
            'iteration': self.task_status.current_iteration,
            'action': action_plan,
            'error': result.error_message,
            'timestamp': time.time()
        }
        self.failure_history.append(failure_record)
        
        self._narrate(f"Action failed: {result.error_message}")
        
        # Try to diagnose failure if we have before/after screenshots
        if result.before_screenshot and result.after_screenshot:
            failure_type = self.vision_engine.diagnose_failure(
                result.before_screenshot, 
                result.after_screenshot, 
                action_plan
            )
            self._narrate(f"Failure diagnosis: {failure_type}")
            
            # Apply failure-specific recovery
            self._apply_failure_recovery(failure_type, action_plan)
    
    def _apply_failure_recovery(self, failure_type: str, action_plan: ActionPlan):
        """Apply recovery strategy based on failure type"""
        if failure_type == 'timing':
            self._narrate("Timing issue detected - waiting longer")
            time.sleep(2.0)
        elif failure_type == 'wrong_element':
            self._narrate("Wrong element clicked - will try alternative approach")
            # Could implement alternative element finding
        elif failure_type == 'ui_change':
            self._narrate("UI changed - taking new screenshot")
            # Screenshot will be taken in next iteration
        elif failure_type == 'loading':
            self._narrate("Page still loading - waiting")
            time.sleep(3.0)
        elif failure_type == 'permission':
            self._narrate("Permission required - may need user intervention")
            # Could trigger user confirmation
        else:
            self._narrate("Unknown failure - taking safe fallback action")
            time.sleep(1.0)
    
    def _handle_emergency_stop(self):
        """Handle emergency stop activation"""
        self._narrate("EMERGENCY STOP ACTIVATED")
        self.task_status.error_message = "Emergency stop activated"
        self.task_status.is_running = False
        self._notify_completion(False, "Emergency stop")
    
    def _handle_max_failures(self):
        """Handle reaching maximum consecutive failures"""
        self._narrate(f"Too many consecutive failures ({self.consecutive_failures})")
        self.task_status.error_message = f"Max failures reached: {self.consecutive_failures}"
        self.task_status.is_running = False
        self._notify_completion(False, "Max failures reached")
    
    def _handle_task_completion(self):
        """Handle normal task completion"""
        self.task_status.is_running = False
        self.task_status.is_complete = True
        
        if self.task_status.error_message:
            self._narrate(f"Task ended with error: {self.task_status.error_message}")
            self._notify_completion(False, self.task_status.error_message)
        else:
            self._narrate("Task completed successfully!")
            self._notify_completion(True, "Task completed")
    
    def _handle_task_error(self, error_message: str):
        """Handle unexpected task error"""
        self.task_status.is_running = False
        self.task_status.error_message = error_message
        self._narrate(f"Task error: {error_message}")
        self._notify_completion(False, error_message)
    
    def _take_screenshot(self) -> Optional[Image.Image]:
        """Take a screenshot with error handling"""
        try:
            return pyautogui.screenshot()
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
            return None
    
    def _screenshot_to_base64(self, screenshot: Image.Image) -> str:
        """Convert screenshot to base64 string"""
        import base64
        import io
        
        buffer = io.BytesIO()
        screenshot.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def _update_status(self):
        """Update task status and notify callbacks"""
        # Calculate estimated completion
        if self.task_status.total_actions > 0:
            success_rate = self.task_status.successful_actions / self.task_status.total_actions
            remaining_iterations = self.max_iterations - self.task_status.current_iteration
            if success_rate > 0:
                estimated_time = remaining_iterations / success_rate * 2  # Rough estimate
                self.task_status.estimated_completion = time.time() + estimated_time
        
        # Notify status callbacks
        for callback in self.status_callbacks:
            try:
                callback(self.task_status)
            except Exception as e:
                self.logger.error(f"Error in status callback: {e}")
    
    def _narrate(self, message: str):
        """Send narration message to callbacks"""
        self.logger.info(f"Narration: {message}")
        for callback in self.narration_callbacks:
            try:
                callback(message)
            except Exception as e:
                self.logger.error(f"Error in narration callback: {e}")
    
    def _notify_completion(self, success: bool, message: str):
        """Notify completion callbacks"""
        for callback in self.completion_callbacks:
            try:
                callback(success, message)
            except Exception as e:
                self.logger.error(f"Error in completion callback: {e}")
    
    # Control methods
    def stop_task(self):
        """Stop current task"""
        self.should_stop = True
        self._narrate("Task stop requested")
    
    def pause_task(self):
        """Pause current task"""
        self.is_paused = True
        self._narrate("Task paused")
    
    def resume_task(self):
        """Resume paused task"""
        self.is_paused = False
        self._narrate("Task resumed")
    
    def get_task_status(self) -> TaskStatus:
        """Get current task status"""
        return self.task_status
    
    def get_failure_history(self) -> List[Dict[str, Any]]:
        """Get failure history"""
        return self.failure_history.copy() 