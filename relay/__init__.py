"""
RELAY: Universal Desktop Assistant
A vision-guided automation system that executes arbitrary computer tasks through natural language commands.
"""

__version__ = "1.0.0"
__author__ = "RELAY Team"
__description__ = "Universal Desktop Assistant powered by GPT-4V"

from .core.vision_engine import VisionEngine, ActionPlan, VisionContext
from .core.automation_engine import AutomationEngine, ExecutionResult
from .core.task_controller import TaskController, TaskStatus
from .config import Config

__all__ = [
    'VisionEngine',
    'ActionPlan', 
    'VisionContext',
    'AutomationEngine',
    'ExecutionResult',
    'TaskController',
    'TaskStatus',
    'Config'
] 