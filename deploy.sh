#!/bin/bash
# Quick Render Deployment Script
# This script helps you prepare and deploy to Render

set -e  # Exit on error

echo "🚀 Chronofact.ai - Render Deployment Helper"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python
echo "🐍 Checking Python..."
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓${NC} $PYTHON_VERSION"
else
    echo -e "${RED}✗${NC} Python 3 not found!"
    exit 1
fi

# Check Git
echo "📦 Checking Git..."
if command_exists git; then
    GIT_VERSION=$(git --version)
    echo -e "${GREEN}✓${NC} $GIT_VERSION"
else
    echo -e "${RED}✗${NC} Git not found!"
    exit 1
fi

# Check if in git repository
if [ ! -d .git ]; then
    echo -e "${RED}✗${NC} Not in a git repository!"
    echo "Run: git init"
    exit 1
fi

echo ""
echo "🔍 Running pre-deployment checks..."
python3 check_deployment.py

echo ""
echo "📋 Deployment Checklist:"
echo ""
echo "1. Environment Variables (set in Render Dashboard):"
echo "   □ GOOGLE_API_KEY"
echo "   □ QDRANT_URL"
echo "   □ QDRANT_API_KEY"
echo "   □ QDRANT_MODE=cloud"
echo ""
echo "2. Render Configuration:"
echo "   □ Blueprint setup or Manual Web Service"
echo "   □ Health Check Path: /health"
echo "   □ Auto-Deploy enabled"
echo ""
echo "3. Files to commit:"
echo "   □ Dockerfile (updated)"
echo "   □ start_production.py (updated)"
echo "   □ render.yaml (updated)"
echo "   □ .dockerignore (new)"
echo ""

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    echo -e "${YELLOW}⚠${NC} You have uncommitted changes:"
    git status --short
    echo ""
    read -p "Do you want to commit these changes? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📝 Committing changes..."
        git add .
        read -p "Commit message: " COMMIT_MSG
        git commit -m "$COMMIT_MSG"
        echo -e "${GREEN}✓${NC} Changes committed"
    fi
else
    echo -e "${GREEN}✓${NC} No uncommitted changes"
fi

echo ""
echo "🌐 Deployment Options:"
echo ""
echo "A. Auto-Deploy (Recommended):"
echo "   1. Push to GitHub: git push origin main"
echo "   2. Render will auto-deploy"
echo ""
echo "B. Manual Deploy:"
echo "   1. Go to Render Dashboard"
echo "   2. Click 'Manual Deploy'"
echo "   3. Select latest commit"
echo ""

read -p "Push to GitHub now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Pushing to GitHub..."
    
    # Get current branch
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
    
    git push origin "$BRANCH"
    echo -e "${GREEN}✓${NC} Pushed to GitHub ($BRANCH branch)"
    echo ""
    echo "✨ Render will now auto-deploy if configured"
fi

echo ""
echo "📊 Monitor deployment:"
echo "   1. Go to https://dashboard.render.com"
echo "   2. Select your service"
echo "   3. Check 'Logs' tab"
echo ""
echo "🏥 Test health endpoint after deployment:"
echo "   curl https://your-service.onrender.com/health"
echo ""
echo -e "${GREEN}✓${NC} Deployment preparation complete!"

