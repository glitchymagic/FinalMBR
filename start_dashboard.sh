#!/bin/bash

echo "🚀 Starting FY26 Tech Spot Operational Metrics Dashboard..."
echo ""

# Check if virtual environment exists, if not create one
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check if data file exists
if [ ! -f "FY26-6Months.xlsx" ]; then
    echo "❌ Error: FY26-6Months.xlsx not found!"
    echo "Please ensure the Excel file is in the project directory."
    exit 1
fi

echo "✅ Data file found: FY26-6Months.xlsx"
echo ""

# Start the Flask application
echo "🌟 Starting dashboard server..."
echo "📊 Dashboard will be available at: http://localhost:8080"
echo "Press Ctrl+C to stop the server"
echo ""

python app.py 