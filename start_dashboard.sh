#!/bin/bash

# Start the FY26 Tech Spot Operational Metrics Dashboard
echo "🚀 Starting FY26 Tech Spot Operational Metrics Dashboard..."

# Determine the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check for Python - try python3 first, then python
PYTHON_CMD="python3"
if ! command -v $PYTHON_CMD &> /dev/null; then
    PYTHON_CMD="python"
    if ! command -v $PYTHON_CMD &> /dev/null; then
        echo "❌ Error: Python not found! Please install Python 3.7+"
        exit 1
    fi
fi
echo "✅ Using Python: $($PYTHON_CMD --version)"

# Activate virtual environment if it exists
echo "🔧 Activating virtual environment..."
if [ -d "venv" ]; then
    source venv/bin/activate
    # Check if activation worked
    if [ $? -ne 0 ]; then
        echo "⚠️  Virtual environment activation failed, using system Python"
    else
        echo "✅ Virtual environment activated"
    fi
else
    echo "⚠️  Virtual environment not found, using system Python"
fi

# Check for pip
PIP_CMD="pip3"
if ! command -v $PIP_CMD &> /dev/null; then
    PIP_CMD="pip"
    if ! command -v $PIP_CMD &> /dev/null; then
        echo "⚠️  pip not found, skipping dependency installation"
    else
        echo "📚 Installing dependencies..."
        $PIP_CMD install -r requirements.txt
    fi
else
    echo "📚 Installing dependencies..."
    $PIP_CMD install -r requirements.txt
fi

# Check if data files exist
if [ -f "FY26-6Months.xlsx" ]; then
    echo "✅ Data file found: FY26-6Months.xlsx"
else
    echo "❌ Error: Data file FY26-6Months.xlsx not found!"
    exit 1
fi

if [ -f "Combined_Incidents_Report_Feb_to_June_2025.xlsx" ]; then
    echo "✅ Data file found: Combined_Incidents_Report_Feb_to_June_2025.xlsx"
else
    echo "⚠️  Warning: Combined_Incidents_Report_Feb_to_June_2025.xlsx not found!"
fi

# Start the dashboard
echo "🌟 Starting dashboard server..."
echo "📊 Dashboard will be available at: http://localhost:8080"
echo "Press Ctrl+C to stop the server"
echo ""

$PYTHON_CMD app.py