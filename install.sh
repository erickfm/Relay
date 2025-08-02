#!/bin/bash

# RELAY: Universal Desktop Assistant - Installation Script
# This script installs RELAY and its dependencies using uv

set -e  # Exit on any error

echo "🚀 Installing RELAY: Universal Desktop Assistant"
echo "================================================"

# Check if Python 3.8+ is installed
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.8 or higher is required. Found: $python_version"
    echo "Please install Python 3.8+ and try again."
    exit 1
fi

echo "✅ Python version: $python_version"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Installing uv..."
    echo "Installing uv package manager..."
    
    # Install uv using the official installer
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Source the shell configuration to make uv available
    if [ -f "$HOME/.cargo/env" ]; then
        source "$HOME/.cargo/env"
    fi
    
    # Check if uv is now available
    if ! command -v uv &> /dev/null; then
        echo "❌ Failed to install uv. Please install it manually:"
        echo "   Visit: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi
fi

echo "✅ uv found: $(uv --version)"

# Initialize uv project (if not already done)
if [ ! -f "pyproject.toml" ]; then
    echo "❌ pyproject.toml not found. Please run this script from the RELAY project directory."
    exit 1
fi

# Sync dependencies
echo "📦 Installing dependencies with uv..."
uv sync

echo "✅ Dependencies installed successfully"

# Create configuration directory
echo "📁 Creating configuration directory..."
mkdir -p ~/.relay/logs

# Set up API key
echo ""
echo "🔑 OpenAI API Key Setup"
echo "======================"
echo "RELAY needs an OpenAI API key with GPT-4V access to function."
echo ""
echo "You can set it in several ways:"
echo "1. Environment variable: export OPENAI_API_KEY='your-key-here'"
echo "2. Configuration file: ~/.relay/config.json"
echo "3. Enter it now (will be saved to config file)"
echo ""

read -p "Enter your OpenAI API key now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "OpenAI API Key: " api_key
    if [ ! -z "$api_key" ]; then
        cat > ~/.relay/config.json << EOF
{
  "openai_api_key": "$api_key",
  "model": "gpt-4-vision-preview",
  "max_iterations": 50,
  "max_failures": 10,
  "confidence_threshold": 3
}
EOF
        echo "✅ API key saved to ~/.relay/config.json"
    else
        echo "❌ No API key provided. You'll need to set it later."
    fi
else
    echo "ℹ️  You'll need to set your API key before running RELAY."
fi

# Check permissions
echo ""
echo "🔐 Permission Check"
echo "=================="
echo "RELAY needs screen recording and accessibility permissions."
echo ""
echo "On macOS, you'll need to grant:"
echo "- Screen Recording permission in System Preferences > Security & Privacy > Privacy"
echo "- Accessibility permission in System Preferences > Security & Privacy > Privacy"
echo ""
echo "On Linux, you may need to install additional packages:"
echo "- sudo apt-get install python3-tk scrot (Ubuntu/Debian)"
echo "- sudo dnf install python3-tkinter scrot (Fedora)"
echo ""

# Test basic functionality
echo "🧪 Testing installation..."
if uv run python -c "import relay; print('✅ RELAY package imported successfully')" 2>/dev/null; then
    echo "✅ RELAY installation test passed"
else
    echo "⚠️  RELAY package import test failed. This might be normal if running outside the uv environment."
fi

echo ""
echo "🎉 Installation completed!"
echo "========================"
echo ""
echo "To run RELAY:"
echo "1. Run RELAY: uv run python main.py"
echo "2. Or use the relay command: uv run relay"
echo ""
echo "💡 Example tasks:"
echo "   - 'Make a dad rock playlist on Spotify'"
echo "   - 'Fill out this checkout form with my usual info'"
echo "   - 'Organize my desktop files into folders'"
echo ""
echo "🛑 Emergency stop: Move mouse to screen corner or press emergency stop button"
echo ""
echo "📚 For more information, see README.md"
echo ""
echo "Happy automating! 🚀" 