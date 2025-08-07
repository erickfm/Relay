"""
Main UI Window - Modern interface for RELAY desktop assistant
Built with CustomTkinter for beautiful, responsive design
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import customtkinter as ctk
import threading
import time
from typing import Optional, Callable
from PIL import Image, ImageTk
import os

from ..core.task_controller import TaskController, TaskStatus
from ..core.vision_engine import VisionEngine
from ..core.automation_engine import AutomationEngine

# Configure CustomTkinter appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class MainWindow:
    """Main application window for RELAY"""
    
    def __init__(self, task_controller: TaskController):
        self.task_controller = task_controller
        self.root = ctk.CTk()
        self.setup_window()
        self.setup_ui()
        self.setup_callbacks()
        
        # UI state
        self.is_task_running = False
        self.narration_buffer = []
        self.max_narration_lines = 100
        
    def setup_window(self):
        """Setup main window properties"""
        self.root.title("RELAY - Universal Desktop Assistant")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Center window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1200 // 2)
        y = (self.root.winfo_screenheight() // 2) - (800 // 2)
        self.root.geometry(f"1200x800+{x}+{y}")
        
    def setup_ui(self):
        """Setup the user interface"""
        # Configure grid weights
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=2)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Create main frames
        self.create_control_panel()
        self.create_main_content()
        
    def create_control_panel(self):
        """Create the left control panel"""
        self.control_frame = ctk.CTkFrame(self.root, width=300)
        self.control_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.control_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            self.control_frame, 
            text="RELAY", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(20, 10))
        
        subtitle_label = ctk.CTkLabel(
            self.control_frame,
            text="Universal Desktop Assistant",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        subtitle_label.grid(row=1, column=0, pady=(0, 20))
        
        # Task input section
        self.create_task_input_section()
        
        # Control buttons
        self.create_control_buttons()
        
        # Status display
        self.create_status_display()
        
        # Emergency stop
        self.create_emergency_stop()
        
    def create_task_input_section(self):
        """Create task input section"""
        # Task input frame
        input_frame = ctk.CTkFrame(self.control_frame)
        input_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        input_frame.grid_columnconfigure(0, weight=1)
        
        # Label
        input_label = ctk.CTkLabel(
            input_frame,
            text="What would you like me to do?",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        input_label.grid(row=0, column=0, pady=(15, 10), padx=15)
        
        # Text input
        self.task_input = ctk.CTkTextbox(
            input_frame,
            height=100
        )
        self.task_input.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 15))
        
        # Example tasks
        examples_frame = ctk.CTkFrame(input_frame)
        examples_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 15))
        examples_frame.grid_columnconfigure(0, weight=1)
        
        examples_label = ctk.CTkLabel(
            examples_frame,
            text="Example Tasks:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        examples_label.grid(row=0, column=0, pady=(10, 5), padx=10)
        
        examples = [
            "• Create a playlist on Spotify",
            "• Fill out web forms",
            "• Organize desktop files",
            "• Navigate to specific websites",
            "• Complete online purchases"
        ]
        
        for i, example in enumerate(examples):
            example_label = ctk.CTkLabel(
                examples_frame,
                text=example,
                font=ctk.CTkFont(size=10),
                text_color="lightblue"
            )
            example_label.grid(row=i+1, column=0, pady=2, padx=10, sticky="w")
        
    def create_control_buttons(self):
        """Create control buttons"""
        button_frame = ctk.CTkFrame(self.control_frame)
        button_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=10)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        # Start button
        self.start_button = ctk.CTkButton(
            button_frame,
            text="Start Task",
            command=self.start_task,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.start_button.grid(row=0, column=0, padx=(15, 5), pady=15, sticky="ew")
        
        # Stop button
        self.stop_button = ctk.CTkButton(
            button_frame,
            text="Stop",
            command=self.stop_task,
            height=40,
            fg_color="red",
            hover_color="darkred",
            state="disabled"
        )
        self.stop_button.grid(row=0, column=1, padx=(5, 15), pady=15, sticky="ew")
        
        # Pause/Resume button
        self.pause_button = ctk.CTkButton(
            button_frame,
            text="Pause",
            command=self.toggle_pause,
            height=35,
            fg_color="orange",
            hover_color="darkorange",
            state="disabled"
        )
        self.pause_button.grid(row=1, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="ew")
        
    def create_status_display(self):
        """Create status display section"""
        status_frame = ctk.CTkFrame(self.control_frame)
        status_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=10)
        status_frame.grid_columnconfigure(0, weight=1)
        
        # Status label
        status_label = ctk.CTkLabel(
            status_frame,
            text="Task Status",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        status_label.grid(row=0, column=0, pady=(15, 10), padx=15)
        
        # Status indicators
        self.status_indicators = {}
        
        status_items = [
            ("status", "Status", "Idle"),
            ("iterations", "Iterations", "0"),
            ("actions", "Actions", "0/0"),
            ("success_rate", "Success Rate", "0%"),
            ("current_action", "Current Action", "None")
        ]
        
        for i, (key, label, default_value) in enumerate(status_items):
            # Label
            item_label = ctk.CTkLabel(
                status_frame,
                text=f"{label}:",
                font=ctk.CTkFont(size=11, weight="bold")
            )
            item_label.grid(row=i+1, column=0, pady=2, padx=(15, 5), sticky="w")
            
            # Value
            value_label = ctk.CTkLabel(
                status_frame,
                text=default_value,
                font=ctk.CTkFont(size=11),
                text_color="lightgreen"
            )
            value_label.grid(row=i+1, column=1, pady=2, padx=(5, 15), sticky="w")
            
            self.status_indicators[key] = value_label
        
    def create_emergency_stop(self):
        """Create emergency stop section"""
        emergency_frame = ctk.CTkFrame(self.control_frame)
        emergency_frame.grid(row=5, column=0, sticky="ew", padx=20, pady=10)
        emergency_frame.grid_columnconfigure(0, weight=1)
        
        emergency_label = ctk.CTkLabel(
            emergency_frame,
            text="Emergency Stop",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="red"
        )
        emergency_label.grid(row=0, column=0, pady=(15, 10), padx=15)
        
        self.emergency_button = ctk.CTkButton(
            emergency_frame,
            text="EMERGENCY STOP",
            command=self.emergency_stop,
            height=50,
            fg_color="red",
            hover_color="darkred",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.emergency_button.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="ew")
        
        # Instructions
        instructions = ctk.CTkLabel(
            emergency_frame,
            text="Move mouse to screen corner\nor press this button to stop",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        instructions.grid(row=2, column=0, pady=(0, 15), padx=15)
        
    def create_main_content(self):
        """Create the main content area"""
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)
        
        # Title
        main_title = ctk.CTkLabel(
            self.main_frame,
            text="Task Execution",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        main_title.grid(row=0, column=0, pady=(20, 10), padx=20, sticky="w")
        
        # Narration area
        self.create_narration_area()
        
    def create_narration_area(self):
        """Create the narration display area"""
        narration_frame = ctk.CTkFrame(self.main_frame)
        narration_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        narration_frame.grid_columnconfigure(0, weight=1)
        narration_frame.grid_rowconfigure(1, weight=1)
        
        # Narration header
        narration_header = ctk.CTkLabel(
            narration_frame,
            text="What RELAY is thinking and doing:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        narration_header.grid(row=0, column=0, pady=(15, 10), padx=15, sticky="w")
        
        # Narration text area
        self.narration_text = ctk.CTkTextbox(
            narration_frame,
            font=ctk.CTkFont(size=12, family="monospace"),
            wrap="word"
        )
        self.narration_text.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        
        # Scroll to bottom
        self.narration_text.configure(state="disabled")
        
        # Clear button
        clear_button = ctk.CTkButton(
            narration_frame,
            text="Clear Log",
            command=self.clear_narration,
            height=30,
            width=100
        )
        clear_button.grid(row=2, column=0, pady=(0, 15), padx=15, sticky="w")
        
    def setup_callbacks(self):
        """Setup callbacks for task controller"""
        self.task_controller.status_callbacks.append(self.update_status)
        self.task_controller.narration_callbacks.append(self.add_narration)
        self.task_controller.completion_callbacks.append(self.handle_completion)
        
    def start_task(self):
        """Start a new task"""
        task_description = self.task_input.get("1.0", "end-1c").strip()
        
        if not task_description:
            messagebox.showwarning("No Task", "Please enter a task description.")
            return
        
        # Update UI state
        self.is_task_running = True
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.pause_button.configure(state="normal")
        self.task_input.configure(state="disabled")
        
        # Clear previous narration
        self.clear_narration()
        
        # Start task
        success = self.task_controller.execute_task(
            task_description,
            on_status_update=self.update_status,
            on_narration=self.add_narration,
            on_completion=self.handle_completion
        )
        
        if not success:
            messagebox.showerror("Error", "Failed to start task. Task may already be running.")
            self.reset_ui_state()
    
    def stop_task(self):
        """Stop current task"""
        self.task_controller.stop_task()
        self.add_narration("Task stop requested by user")
    
    def toggle_pause(self):
        """Toggle pause/resume"""
        if self.task_controller.is_paused:
            self.task_controller.resume_task()
            self.pause_button.configure(text="Pause")
        else:
            self.task_controller.pause_task()
            self.pause_button.configure(text="Resume")
    
    def emergency_stop(self):
        """Activate emergency stop"""
        self.task_controller.automation_engine.activate_emergency_stop()
        self.add_narration("EMERGENCY STOP ACTIVATED!")
        messagebox.showwarning("Emergency Stop", "Emergency stop activated!")
    
    def update_status(self, status: TaskStatus):
        """Update status display"""
        # Update status indicators
        self.status_indicators["status"].configure(
            text="Running" if status.is_running else "Idle" if not status.is_complete else "Complete"
        )
        self.status_indicators["iterations"].configure(text=str(status.current_iteration))
        self.status_indicators["actions"].configure(
            text=f"{status.successful_actions}/{status.total_actions}"
        )
        
        # Calculate success rate
        if status.total_actions > 0:
            success_rate = (status.successful_actions / status.total_actions) * 100
            self.status_indicators["success_rate"].configure(text=f"{success_rate:.1f}%")
        else:
            self.status_indicators["success_rate"].configure(text="0%")
        
        # Update current action
        current_action = status.current_action if status.current_action else "None"
        self.status_indicators["current_action"].configure(text=current_action[:50])
        
        # Update UI state if task completed
        if not status.is_running and self.is_task_running:
            self.reset_ui_state()
    
    def add_narration(self, message: str):
        """Add narration message to display"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        # Add to buffer
        self.narration_buffer.append(formatted_message)
        
        # Limit buffer size
        if len(self.narration_buffer) > self.max_narration_lines:
            self.narration_buffer.pop(0)
        
        # Update display
        self.narration_text.configure(state="normal")
        self.narration_text.delete("1.0", "end")
        self.narration_text.insert("1.0", "".join(self.narration_buffer))
        self.narration_text.configure(state="disabled")
        
        # Scroll to bottom
        self.narration_text.see("end")
    
    def clear_narration(self):
        """Clear narration display"""
        self.narration_buffer.clear()
        self.narration_text.configure(state="normal")
        self.narration_text.delete("1.0", "end")
        self.narration_text.configure(state="disabled")
    
    def handle_completion(self, success: bool, message: str):
        """Handle task completion"""
        if success:
            self.add_narration(f"✅ Task completed successfully: {message}")
            messagebox.showinfo("Task Complete", f"Task completed successfully!\n\n{message}")
        else:
            self.add_narration(f"❌ Task failed: {message}")
            messagebox.showerror("Task Failed", f"Task failed:\n\n{message}")
    
    def reset_ui_state(self):
        """Reset UI to idle state"""
        self.is_task_running = False
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.pause_button.configure(state="disabled", text="Pause")
        self.task_input.configure(state="normal")
    
    def run(self):
        """Start the main application loop"""
        self.root.mainloop()
    
    def on_closing(self):
        """Handle window closing"""
        if self.is_task_running:
            if messagebox.askokcancel("Quit", "Task is running. Do you want to stop and quit?"):
                self.task_controller.stop_task()
                self.root.quit()
        else:
            self.root.quit() 