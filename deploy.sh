#!/bin/bash

# One Piece Character Tracker - Simple Deployment Script

set -e

echo "🏴‍☠️ One Piece Character Tracker Deployment Script"
echo "=================================================="

# Check if database exists
if [ ! -f "one_piece_tracker.db" ]; then
    echo "❌ Error: Database file 'one_piece_tracker.db' not found!"
    echo "Please run the data gathering script first to create the database."
    exit 1
fi

# Create data directory
mkdir -p data

# Copy database to data directory
cp one_piece_tracker.db data/

echo "✅ Database copied to data directory"

# Check deployment method
if [ "$1" = "docker" ]; then
    echo "🐳 Deploying with Docker..."
    
    # Build and run with Docker Compose
    docker-compose build
    docker-compose up -d
    
    echo "✅ Application deployed with Docker!"
    echo "🌐 Access the application at: http://localhost:5001"
    echo "📊 Health check: http://localhost:5001/health"
    
elif [ "$1" = "docker-prod" ]; then
    echo "🐳 Deploying with Docker + Nginx..."
    
    # Build and run with production profile
    docker-compose --profile production build
    docker-compose --profile production up -d
    
    echo "✅ Application deployed with Docker + Nginx!"
    echo "🌐 Access the application at: http://localhost"
    echo "📊 Health check: http://localhost:5001/health"
    
elif [ "$1" = "local" ]; then
    echo "🐍 Deploying locally with Python..."
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    pip install -r requirements.txt
    
    # Set environment variables
    export FLASK_ENV=production
    export DATABASE_PATH=one_piece_tracker.db
    
    # Run the application
    echo "🚀 Starting application..."
    python app.py &
    
    echo "✅ Application started locally!"
    echo "🌐 Access the application at: http://localhost:5001"
    echo "📊 Health check: http://localhost:5001/health"
    echo "⚠️  Use 'pkill -f \"python app.py\"' to stop the application"
    
else
    echo "Usage: $0 [docker|docker-prod|local]"
    echo ""
    echo "Deployment options:"
    echo "  docker      - Deploy with Docker (simple)"
    echo "  docker-prod - Deploy with Docker + Nginx (production)"
    echo "  local       - Deploy locally with Python"
    echo ""
    echo "Examples:"
    echo "  $0 docker      # Simple Docker deployment"
    echo "  $0 docker-prod # Production Docker deployment with Nginx"
    echo "  $0 local       # Local Python deployment"
    exit 1
fi

echo ""
echo "🎉 Deployment complete!"
echo "📝 Check logs with: docker-compose logs -f (for Docker deployments)"