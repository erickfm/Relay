# RELAY: Universal Desktop Assistant

A vision-guided automation system that executes arbitrary computer tasks through natural language commands. Tell it "make a dad rock playlist on Spotify" or "fill out this checkout form with my usual info" and it handles the entire workflow by seeing your screen and taking the same actions a human would.

## 🚀 Features

- **Pure Vision-Based**: Works with any application - desktop software, web browsers, games, utilities
- **Natural Language Commands**: Simple English descriptions of what you want done
- **Real-Time Narration**: See exactly what RELAY is thinking and doing
- **Safety Controls**: Emergency stop, confirmation prompts, and action allowlists
- **Failure Recovery**: Intelligent diagnosis and adaptation when things go wrong
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Modern Package Management**: Uses `uv` for fast, reliable dependency management

## 🎯 Core Mechanism

RELAY uses OpenAI GPT-4V to analyze desktop screenshots, plan appropriate actions, and generate PyAutoGUI automation scripts. The system:

1. Takes a screenshot of your screen
2. Asks GPT-4V "what should I do next to accomplish this task?"
3. Executes the returned mouse/keyboard commands
4. Verifies progress by taking another screenshot
5. Repeats until the task is complete

## 🛡️ Safety Architecture

- **Confirmation Prompts**: High-risk actions like purchases or deletions require user confirmation
- **Emergency Stop**: Move mouse to screen corner or press emergency stop button
- **Action Allowlists**: Prevents unauthorized system modifications
- **Session Isolation**: Tasks don't interfere with each other
- **Confidence Scoring**: Low-confidence actions trigger alternative approaches

## 📋 Requirements

- Python 3.8+
- OpenAI API key with GPT-4V access
- Screen recording permissions
- Accessibility permissions (for automation)
- `uv` package manager (automatically installed by install script)

## 🚀 Quick Start

### Option 1: Automated Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/relay.git
cd relay

# Run the installation script
chmod +x install.sh
./install.sh
```

The installation script will:
- Install `uv` if not present
- Set up all dependencies
- Create configuration directory
- Guide you through API key setup
- Test the installation

### Option 2: Manual Installation

#### 1. Install uv

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Restart your shell or source the environment
source ~/.cargo/env
```

#### 2. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/relay.git
cd relay

# Install dependencies
uv sync
```

#### 3. Set Up API Key

Set your OpenAI API key in one of these ways:

**Environment Variable:**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

**Configuration File:**
Create `~/.relay/config.json`:
```json
{
  "openai_api_key": "your-api-key-here",
  "model": "gpt-4-vision-preview",
  "max_iterations": 50,
  "max_failures": 10,
  "confidence_threshold": 3
}
```

#### 4. Run RELAY

```bash
# Run the main application
uv run python main.py

# Or use the relay command
uv run relay
```

### 5. Grant Permissions

When prompted, grant:
- Screen recording permissions
- Accessibility permissions (for automation)

## 🎮 Usage

1. **Enter a Task**: Describe what you want RELAY to do in natural language
2. **Watch It Work**: See real-time narration of what RELAY is thinking and doing
3. **Stay in Control**: Pause, stop, or take over at any time
4. **Emergency Stop**: Move mouse to screen corner or press emergency stop button

### Example Tasks

- "Make a dad rock playlist on Spotify"
- "Fill out this checkout form with my usual info"
- "Organize my desktop files into folders"
- "Navigate to my email and compose a new message"
- "Complete this online purchase with my saved payment info"

## 🏗️ Architecture

```
RELAY/
├── relay/
│   ├── core/
│   │   ├── vision_engine.py      # GPT-4V integration
│   │   ├── automation_engine.py  # PyAutoGUI execution
│   │   └── task_controller.py    # Main orchestrator
│   ├── ui/
│   │   └── main_window.py        # CustomTkinter interface
│   └── config.py                 # Configuration management
├── main.py                       # Application entry point
├── pyproject.toml                # Project configuration (uv)
├── uv.lock                       # Dependency lock file
└── README.md                     # This file
```

### Core Components

- **Vision Engine**: Analyzes screenshots with GPT-4V and plans actions
- **Automation Engine**: Executes mouse/keyboard actions with safety controls
- **Task Controller**: Orchestrates the complete automation workflow
- **Main Window**: Modern UI with real-time narration and controls

## ⚙️ Configuration

Configuration is stored in `~/.relay/config.json`:

```json
{
  "openai_api_key": "your-key",
  "model": "gpt-4-vision-preview",
  "max_iterations": 50,
  "max_failures": 10,
  "confidence_threshold": 3,
  "safety": {
    "emergency_stop_enabled": true,
    "confirmation_required": ["delete", "purchase", "confirm", "submit"]
  }
}
```

## 🔧 Development

### Project Structure

```
relay/
├── __init__.py
├── config.py
├── core/
│   ├── __init__.py
│   ├── vision_engine.py
│   ├── automation_engine.py
│   └── task_controller.py
└── ui/
    ├── __init__.py
    └── main_window.py
```

### Development Setup

```bash
# Install development dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Format code
uv run black .
uv run isort .

# Type checking
uv run mypy relay/

# Linting
uv run flake8 relay/
```

### Key Classes

- `VisionEngine`: Handles GPT-4V integration and action planning
- `AutomationEngine`: Executes automation actions with safety controls
- `TaskController`: Main orchestrator for task execution
- `MainWindow`: Modern UI built with CustomTkinter
- `Config`: Configuration management and validation

### Adding New Features

1. **New Action Types**: Add to `AutomationEngine` and update safety allowlists
2. **Enhanced Vision**: Extend `VisionEngine` with additional analysis capabilities
3. **UI Improvements**: Modify `MainWindow` for new interface elements
4. **Safety Features**: Add new controls to `AutomationEngine` safety system

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=relay --cov-report=html

# Run specific test categories
uv run pytest -m unit
uv run pytest -m integration
uv run pytest -m "not slow"
```

## 📦 Package Management with uv

RELAY uses `uv` for fast, reliable Python package management:

```bash
# Install dependencies
uv sync

# Add a new dependency
uv add package-name

# Add development dependency
uv add --dev package-name

# Update dependencies
uv sync --upgrade

# Run commands in the project environment
uv run python main.py
uv run pytest
uv run black .
```

## 🛠️ Troubleshooting

### Common Issues

**"Cannot take screenshots"**
- Grant screen recording permissions in System Preferences/Settings
- On macOS: System Preferences > Security & Privacy > Privacy > Screen Recording

**"Accessibility permissions required"**
- Grant accessibility permissions for automation
- On macOS: System Preferences > Security & Privacy > Privacy > Accessibility

**"OpenAI API key not found"**
- Set environment variable: `export OPENAI_API_KEY="your-key"`
- Or enter it when prompted on first run

**"uv command not found"**
- Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Restart your shell or run: `source ~/.cargo/env`

**"Task fails repeatedly"**
- Check if the target application is responsive
- Try simpler, more specific task descriptions
- Check logs in `~/.relay/logs/relay.log`

### Logs

Logs are stored in `~/.relay/logs/relay.log` and include:
- Task execution details
- Action success/failure information
- Error diagnostics
- Performance metrics

## 🔒 Security & Privacy

- **Local Execution**: All automation runs locally on your machine
- **No Data Collection**: RELAY doesn't collect or transmit personal data
- **API Usage**: Only screenshots are sent to OpenAI for analysis
- **Session Isolation**: Each task runs in isolation
- **Emergency Controls**: Multiple ways to stop automation immediately

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Run tests: `uv run pytest`
5. Format code: `uv run black . && uv run isort .`
6. Commit your changes: `git commit -m "Add feature"`
7. Push to the branch: `git push origin feature-name`
8. Submit a Pull Request

## ⚠️ Disclaimer

RELAY is a powerful automation tool. Use responsibly and ensure you have permission to automate any actions. The developers are not responsible for any misuse of this software.

---

**RELAY: See it. Think it. Do it.**
