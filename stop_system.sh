#!/bin/bash
# Stop PLC-RAG System

echo "🛑 Stopping PLC-RAG System..."
echo ""

# Stop API server
if [ -f .api.pid ]; then
    API_PID=$(cat .api.pid)
    if kill -0 $API_PID 2>/dev/null; then
        kill $API_PID
        echo "✅ API server stopped (PID: $API_PID)"
    else
        echo "⚠️  API server not running"
    fi
    rm .api.pid
else
    echo "⚠️  No API PID file found"
fi

# Stop UI server
if [ -f .ui.pid ]; then
    UI_PID=$(cat .ui.pid)
    if kill -0 $UI_PID 2>/dev/null; then
        kill $UI_PID
        echo "✅ UI server stopped (PID: $UI_PID)"
    else
        echo "⚠️  UI server not running"
    fi
    rm .ui.pid
else
    echo "⚠️  No UI PID file found"
fi

# Also kill any remaining processes on those ports (cleanup)
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null

echo ""
echo "✅ System stopped!"
