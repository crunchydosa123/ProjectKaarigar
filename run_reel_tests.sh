#!/bin/bash

echo "🎬 Reel Generation API Test Runner"
echo "=================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed or not in PATH"
    exit 1
fi

# Check if Flask server is running
echo "🔍 Checking if Flask server is running..."
if curl -s http://localhost:5000/ > /dev/null; then
    echo "✅ Flask server is running"
else
    echo "❌ Flask server is not running. Please start it first:"
    echo "   cd ProjectKaarigar/backend && python app.py"
    exit 1
fi

# Install test requirements
echo "📦 Installing test requirements..."
pip3 install -r test_requirements.txt

echo ""
echo "🚀 Running comprehensive tests..."
echo "=================================="
python3 test_reel_generation.py

echo ""
echo "🚀 Running quick tests..."
echo "========================="
python3 quick_reel_test.py

echo ""
echo "✅ All tests completed!"
