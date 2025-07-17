#!/bin/bash

echo "🏴‍☠️ One Piece Character Tracker - GitHub Setup"
echo "=============================================="

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "❌ Git repository not initialized. Run 'git init' first."
    exit 1
fi

# Check if we have commits
if ! git log --oneline -n 1 > /dev/null 2>&1; then
    echo "❌ No commits found. Make sure you've committed your code first."
    exit 1
fi

echo "📝 Please follow these steps to create your GitHub repository:"
echo ""
echo "1. Go to https://github.com/new"
echo "2. Repository name: one-piece-character-tracker"
echo "3. Description: A web application that tracks One Piece character values over time with interactive charts"
echo "4. Make it Public (recommended)"
echo "5. DO NOT initialize with README, .gitignore, or license"
echo "6. Click 'Create repository'"
echo ""
echo "7. After creating the repository, GitHub will show you commands to run."
echo "   Use these commands instead:"
echo ""

# Get the current user's GitHub username if possible
if command -v gh &> /dev/null; then
    USERNAME=$(gh api user --jq .login 2>/dev/null)
    if [ -n "$USERNAME" ]; then
        echo "   git remote add origin https://github.com/$USERNAME/one-piece-character-tracker.git"
    else
        echo "   git remote add origin https://github.com/YOUR_USERNAME/one-piece-character-tracker.git"
    fi
else
    echo "   git remote add origin https://github.com/YOUR_USERNAME/one-piece-character-tracker.git"
fi

echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "8. Replace YOUR_USERNAME with your actual GitHub username"
echo ""
echo "🚀 After pushing to GitHub, follow the Render deployment instructions in DEPLOYMENT_INSTRUCTIONS.md"
echo ""
echo "📊 Your repository will include:"
echo "   - ✅ Complete Flask web application"
echo "   - ✅ Interactive charts with Chart.js"
echo "   - ✅ Mobile-responsive design"
echo "   - ✅ Docker deployment configuration"
echo "   - ✅ Real character data (54 characters, 113+ history entries)"
echo "   - ✅ Comprehensive documentation"
echo ""
echo "🎉 Ready to deploy to the world! 🌍"