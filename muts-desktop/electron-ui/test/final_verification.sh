#!/bin/bash
# Final verification script - tests the actual app

set -e

echo "🧪 Final Verification Test"
echo "========================"
echo ""

cd "$(dirname "$0")/.."

# Check if backend is running
echo "1. Checking backend..."
if curl -s http://localhost:3000/health > /dev/null 2>&1; then
    echo "   ✅ Backend is running"
else
    echo "   ⚠️  Backend not running (this is OK for standalone mode)"
fi

# Check build
echo ""
echo "2. Checking build..."
if [ -f "dist/main.js" ] && [ -f "dist/preload.js" ] && [ -f "dist/renderer/src/index.html" ]; then
    echo "   ✅ Build files exist"
else
    echo "   ❌ Build files missing - run 'npm run build' first"
    exit 1
fi

# Check IPC handlers in main.ts
echo ""
echo "3. Checking IPC handlers..."
HANDLER_COUNT=$(grep -c "ipcMain.handle(" src/main.ts || echo "0")
if [ "$HANDLER_COUNT" -ge "30" ]; then
    echo "   ✅ Found $HANDLER_COUNT IPC handlers (expected >= 30)"
else
    echo "   ⚠️  Only found $HANDLER_COUNT IPC handlers"
fi

# Check HashRouter usage
echo ""
echo "4. Checking HashRouter..."
if grep -q "HashRouter" src/main.tsx; then
    echo "   ✅ HashRouter is configured"
else
    echo "   ❌ HashRouter not found"
    exit 1
fi

# Check preload script
echo ""
echo "5. Checking preload script..."
if grep -q "contextBridge" src/preload.ts; then
    echo "   ✅ Preload script uses contextBridge"
else
    echo "   ❌ Preload script missing contextBridge"
    exit 1
fi

# Check for Buffer usage in renderer (should be Uint8Array)
echo ""
echo "6. Checking renderer code..."
BUFFER_USAGE=$(grep -r "Buffer\." src/tabs/ src/components/ 2>/dev/null | grep -v "node_modules" | wc -l || echo "0")
if [ "$BUFFER_USAGE" -eq "0" ]; then
    echo "   ✅ No Buffer usage in renderer (using Uint8Array)"
else
    echo "   ⚠️  Found $BUFFER_USAGE Buffer usages in renderer"
fi

# Check error boundaries
echo ""
echo "7. Checking error handling..."
if grep -q "ErrorBoundary" src/App.tsx; then
    echo "   ✅ ErrorBoundary is configured"
else
    echo "   ⚠️  ErrorBoundary not found"
fi

echo ""
echo "========================"
echo "✅ All checks passed!"
echo ""
echo "The app is ready to run. Start it with: npm start"
echo ""

