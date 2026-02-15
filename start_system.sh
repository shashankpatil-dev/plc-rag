#!/bin/bash
# Start PLC-RAG System (API + UI)

echo "🚀 Starting PLC-RAG System..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run: python -m venv venv"
    exit 1
fi

# Start API server in background
echo "1️⃣ Starting FastAPI server (port 8000)..."
source venv/bin/activate
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload > api.log 2>&1 &
API_PID=$!
echo "✅ API server started (PID: $API_PID)"
echo "   Logs: tail -f api.log"
echo "   Docs: http://localhost:8000/docs"
echo ""

# Wait for API to start
echo "⏳ Waiting for API to be ready..."
sleep 3

# Start Next.js UI in background
echo "2️⃣ Starting Next.js UI (port 3000)..."
cd ui
npm run dev > ../ui.log 2>&1 &
UI_PID=$!
cd ..
echo "✅ UI server started (PID: $UI_PID)"
echo "   Logs: tail -f ui.log"
echo "   URL: http://localhost:3000"
echo ""

echo "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "="
echo "🎉 PLC-RAG System is running!"
echo "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "="
echo ""
echo "📱 Frontend UI:  http://localhost:3000"
echo "🔧 API Server:   http://localhost:8000"
echo "📚 API Docs:     http://localhost:8000/docs"
echo ""
echo "💡 To stop the servers, run: ./stop_system.sh"
echo "   Or kill processes: kill $API_PID $UI_PID"
echo ""
echo "📊 View logs:"
echo "   API: tail -f api.log"
echo "   UI:  tail -f ui.log"
echo ""

# Save PIDs to file for easy stopping
echo "$API_PID" > .api.pid
echo "$UI_PID" > .ui.pid

echo "🧪 Ready to test!"
echo "   1. Open http://localhost:3000 in your browser"
echo "   2. Upload LogicSheet03.csv from assets/ folder"
echo "   3. Watch the RAG-enhanced generation in action!"
echo ""
