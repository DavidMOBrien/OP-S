#!/usr/bin/env python3
"""
Simple verification script for One Piece Character Tracker
Tests core functionality without starting a server
"""

import os
import sys
import sqlite3
from app import app, check_database_health

def test_app_functionality():
    """Test core app functionality using Flask test client"""
    print("🧪 Testing application functionality...")
    
    with app.test_client() as client:
        tests_passed = 0
        total_tests = 6
        
        # Test 1: Health endpoint
        try:
            response = client.get('/health')
            if response.status_code in [200, 503]:
                print("✅ Health endpoint: OK")
                tests_passed += 1
            else:
                print(f"❌ Health endpoint: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Health endpoint: Error - {e}")
        
        # Test 2: Main page
        try:
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Main page: OK")
                tests_passed += 1
            else:
                print(f"❌ Main page: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Main page: Error - {e}")
        
        # Test 3: Charts page
        try:
            response = client.get('/charts')
            if response.status_code == 200:
                print("✅ Charts page: OK")
                tests_passed += 1
            else:
                print(f"❌ Charts page: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Charts page: Error - {e}")
        
        # Test 4: API endpoints
        try:
            response = client.get('/api/characters')
            if response.status_code == 200:
                data = response.get_json()
                if data and 'characters' in data:
                    print("✅ Characters API: OK")
                    tests_passed += 1
                else:
                    print("❌ Characters API: Invalid response format")
            else:
                print(f"❌ Characters API: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Characters API: Error - {e}")
        
        # Test 5: Error handling (404)
        try:
            response = client.get('/nonexistent-page')
            if response.status_code == 404:
                print("✅ 404 Error handling: OK")
                tests_passed += 1
            else:
                print(f"❌ 404 Error handling: Expected 404, got {response.status_code}")
        except Exception as e:
            print(f"❌ 404 Error handling: Error - {e}")
        
        # Test 6: Character detail with real data
        try:
            # Get a character from the API first
            response = client.get('/api/characters')
            if response.status_code == 200:
                data = response.get_json()
                characters = data.get('characters', [])
                if characters:
                    test_character = characters[0]
                    wiki_url = test_character['wiki_url']
                    
                    # Test character detail page
                    detail_response = client.get(f'/character/{wiki_url}')
                    if detail_response.status_code == 200:
                        print("✅ Character detail page: OK")
                        tests_passed += 1
                    else:
                        print(f"❌ Character detail page: HTTP {detail_response.status_code}")
                else:
                    print("❌ Character detail page: No characters available for testing")
            else:
                print("❌ Character detail page: Could not get test data")
        except Exception as e:
            print(f"❌ Character detail page: Error - {e}")
        
        return tests_passed, total_tests

def test_database():
    """Test database connectivity and data"""
    print("🗄️  Testing database...")
    
    if not os.path.exists('one_piece_tracker.db'):
        print("❌ Database file not found!")
        return False
    
    try:
        is_healthy, message = check_database_health()
        if is_healthy:
            print(f"✅ Database: {message}")
            return True
        else:
            print(f"❌ Database: {message}")
            return False
    except Exception as e:
        print(f"❌ Database: Error - {e}")
        return False

def test_static_files():
    """Test that static files exist"""
    print("📁 Testing static files...")
    
    static_files = [
        'static/css/style.css',
        'templates/base.html',
        'templates/index.html',
        'templates/character.html',
        'templates/charts.html',
        'templates/error.html'
    ]
    
    missing_files = []
    for file_path in static_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    else:
        print("✅ All static files present")
        return True

def test_deployment_files():
    """Test deployment configuration files"""
    print("🚀 Testing deployment files...")
    
    deployment_files = [
        'Dockerfile',
        'docker-compose.yml',
        'deploy.sh',
        'nginx.conf',
        '.env.production'
    ]
    
    missing_files = []
    for file_path in deployment_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing deployment files: {', '.join(missing_files)}")
        return False
    else:
        print("✅ All deployment files present")
        return True

def test_mobile_responsiveness():
    """Test mobile responsiveness by checking CSS"""
    print("📱 Testing mobile responsiveness...")
    
    try:
        with open('static/css/style.css', 'r') as f:
            css_content = f.read()
        
        # Check for media queries
        if '@media' in css_content and 'max-width' in css_content:
            print("✅ Responsive CSS media queries found")
        else:
            print("❌ No responsive CSS media queries found")
            return False
        
        # Check for mobile-specific styles
        mobile_indicators = [
            'flex-direction: column',
            'grid-template-columns: 1fr',
            'display: none'
        ]
        
        mobile_styles_found = sum(1 for indicator in mobile_indicators if indicator in css_content)
        if mobile_styles_found >= 2:
            print("✅ Mobile-specific CSS styles found")
            return True
        else:
            print("❌ Insufficient mobile-specific CSS styles")
            return False
            
    except Exception as e:
        print(f"❌ Mobile responsiveness test failed: {e}")
        return False

def main():
    """Run all verification tests"""
    print("🏴‍☠️ One Piece Character Tracker - Application Verification")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 5
    
    # Test 1: Database
    if test_database():
        tests_passed += 1
    
    # Test 2: Static files
    if test_static_files():
        tests_passed += 1
    
    # Test 3: Deployment files
    if test_deployment_files():
        tests_passed += 1
    
    # Test 4: Mobile responsiveness
    if test_mobile_responsiveness():
        tests_passed += 1
    
    # Test 5: App functionality
    app_tests_passed, app_total_tests = test_app_functionality()
    if app_tests_passed >= app_total_tests * 0.8:  # 80% pass rate
        tests_passed += 1
        print(f"✅ App functionality: {app_tests_passed}/{app_total_tests} tests passed")
    else:
        print(f"❌ App functionality: Only {app_tests_passed}/{app_total_tests} tests passed")
    
    # Final results
    print("\n" + "=" * 60)
    print(f"📊 Verification Results: {tests_passed}/{total_tests} test categories passed")
    
    if tests_passed == total_tests:
        print("🎉 All verification tests passed! Application is ready for deployment.")
        return 0
    elif tests_passed >= 4:
        print("⚠️  Most tests passed. Review failed tests before deployment.")
        return 1
    else:
        print("❌ Multiple test categories failed. Fix issues before deployment.")
        return 2

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)