#!/bin/bash
# Verification script for Phase 0 setup

echo "=================================="
echo "PLC-RAG Phase 0 Verification"
echo "=================================="
echo ""

# Check Python virtual environment
echo "1. Checking Python virtual environment..."
if [ -d "venv" ]; then
    echo "   ✅ Virtual environment exists"
else
    echo "   ❌ Virtual environment not found"
    exit 1
fi

# Activate venv and check FastAPI
echo "2. Checking FastAPI installation..."
source venv/bin/activate
if python -c "import fastapi" 2>/dev/null; then
    echo "   ✅ FastAPI installed"
else
    echo "   ❌ FastAPI not installed"
    deactivate
    exit 1
fi

# Check if main.py imports correctly
echo "3. Checking FastAPI app..."
if python -c "from src.api.main import app" 2>/dev/null; then
    echo "   ✅ FastAPI app imports successfully"
else
    echo "   ❌ FastAPI app import failed"
    deactivate
    exit 1
fi
deactivate

# Check Node.js dependencies
echo "4. Checking Node.js installation..."
if [ -d "ui/node_modules" ]; then
    echo "   ✅ Node modules installed"
else
    echo "   ❌ Node modules not found"
    exit 1
fi

# Check key files
echo "5. Checking project files..."
files=(
    "README.md"
    "CLAUDE.md"
    "MVP_ARCHITECTURE.md"
    ".env"
    "requirements.txt"
    "run_server.py"
    "src/api/main.py"
    "src/config/settings.py"
    "ui/package.json"
    "ui/app/page.tsx"
)

all_files_exist=true
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file (missing)"
        all_files_exist=false
    fi
done

echo ""
echo "=================================="
if [ "$all_files_exist" = true ]; then
    echo "✅ Phase 0 Setup Complete!"
    echo "=================================="
    echo ""
    echo "Next steps:"
    echo "1. Terminal 1: python run_server.py"
    echo "2. Terminal 2: cd ui && npm run dev"
    echo "3. Open: http://localhost:3000"
    echo ""
else
    echo "❌ Setup incomplete - some files missing"
    echo "=================================="
    exit 1
fi
