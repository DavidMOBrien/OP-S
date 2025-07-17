#!/usr/bin/env python3
"""
Comprehensive testing script for One Piece Character Tracker deployment
Tests website functionality, mobile responsiveness, error handling, and deployment readiness
"""

import requests
import sqlite3
import os
import sys
import time
import subprocess
from urllib.parse import quote

def test_database_health():
    """Test database connectivity and data integrity"""
    print("🗄️  Testing database health...")
    
    if not os.path.exists('one_piece_tracker.db'):
        print("❌ Database file not found!")
        return False
    
    try:
        conn = sqlite3.connect('one_piece_tracker.db')
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        expected_tables = ['characters', 'character_history', 'chapters']
        
        missing_tables = [table for table in expected_tables if table not in tables]
        if missing_tables:
            print(f"❌ Missing database tables: {missing_tables}")
            return False
        
        # Check data exists
        cursor.execute("SELECT COUNT(*) FROM characters")
        character_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM character_history")
        history_count = cursor.fetchone()[0]
        
        conn.close()
        
        if character_count == 0:
            print("❌ No character data found!")
            return False
        
        print(f"✅ Database healthy: {character_count} characters, {history_count} history entries")
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_web_endpoints(base_url="http://localhost:5001"):
    """Test all web endpoints for functionality"""
    print(f"🌐 Testing web endpoints at {base_url}...")
    
    endpoints_to_test = [
        ("/health", "Health check"),
        ("/", "Main page"),
        ("/charts", "Charts page"),
        ("/api/characters", "Characters API"),
    ]
    
    success_count = 0
    
    for endpoint, description in endpoints_to_test:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"✅ {description}: OK")
                success_count += 1
            else:
                print(f"❌ {description}: HTTP {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {description}: Connection error - {e}")
    
    # Test character detail page with real data
    try:
        # Get a character from the API first
        response = requests.get(f"{base_url}/api/characters", timeout=10)
        if response.status_code == 200:
            characters = response.json().get('characters', [])
            if characters:
                test_character = characters[0]
                wiki_url = test_character['wiki_url']
                encoded_url = quote(wiki_url, safe='')
                
                # Test character detail page
                detail_response = requests.get(f"{base_url}/character/{encoded_url}", timeout=10)
                if detail_response.status_code == 200:
                    print("✅ Character detail page: OK")
                    success_count += 1
                else:
                    print(f"❌ Character detail page: HTTP {detail_response.status_code}")
                
                # Test character history API
                history_response = requests.get(f"{base_url}/api/character/{encoded_url}/history", timeout=10)
                if history_response.status_code == 200:
                    print("✅ Character history API: OK")
                    success_count += 1
                else:
                    print(f"❌ Character history API: HTTP {history_response.status_code}")
    except Exception as e:
        print(f"❌ Character endpoints test failed: {e}")
    
    return success_count >= 4  # At least basic endpoints should work

def test_error_handling(base_url="http://localhost:5001"):
    """Test error handling for missing data and invalid requests"""
    print("🚨 Testing error handling...")
    
    error_tests = [
        ("/character/invalid-character-url", "Invalid character URL", 404),
        ("/api/character/invalid-character-url/history", "Invalid character history", 404),
        ("/nonexistent-page", "404 page", 404),
    ]
    
    success_count = 0
    
    for endpoint, description, expected_status in error_tests:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code == expected_status:
                print(f"✅ {description}: Correctly returns {expected_status}")
                success_count += 1
            else:
                print(f"❌ {description}: Expected {expected_status}, got {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {description}: Connection error - {e}")
    
    return success_count >= 2

def test_mobile_responsiveness(base_url="http://localhost:5001"):
    """Test mobile responsiveness by checking CSS and viewport meta tag"""
    print("📱 Testing mobile responsiveness...")
    
    try:
        # Test main page
        response = requests.get(base_url, timeout=10)
        if response.status_code == 200:
            content = response.text
            
            # Check for viewport meta tag
            if 'name="viewport"' in content and 'width=device-width' in content:
                print("✅ Viewport meta tag present")
            else:
                print("❌ Missing or incorrect viewport meta tag")
                return False
            
            # Check for responsive CSS
            css_response = requests.get(f"{base_url}/static/css/style.css", timeout=10)
            if css_response.status_code == 200:
                css_content = css_response.text
                
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
                    'display: none'  # For hiding elements on mobile
                ]
                
                mobile_styles_found = sum(1 for indicator in mobile_indicators if indicator in css_content)
                if mobile_styles_found >= 2:
                    print("✅ Mobile-specific CSS styles found")
                    return True
                else:
                    print("❌ Insufficient mobile-specific CSS styles")
                    return False
            else:
                print("❌ Could not load CSS file")
                return False
        else:
            print("❌ Could not load main page")
            return False
            
    except Exception as e:
        print(f"❌ Mobile responsiveness test failed: {e}")
        return False

def test_deployment_files():
    """Test that deployment configuration files exist and are valid"""
    print("🚀 Testing deployment configuration...")
    
    required_files = [
        ('Dockerfile', 'Docker configuration'),
        ('docker-compose.yml', 'Docker Compose configuration'),
        ('deploy.sh', 'Deployment script'),
        ('nginx.conf', 'Nginx configuration'),
        ('.env.production', 'Production environment config')
    ]
    
    success_count = 0
    
    for filename, description in required_files:
        if os.path.exists(filename):
            print(f"✅ {description}: Found")
            success_count += 1
        else:
            print(f"❌ {description}: Missing")
    
    # Check if deploy.sh is executable
    if os.path.exists('deploy.sh'):
        if os.access('deploy.sh', os.X_OK):
            print("✅ Deploy script is executable")
        else:
            print("❌ Deploy script is not executable")
    
    return success_count >= 4

def start_test_server():
    """Start the Flask application for testing"""
    print("🚀 Starting test server...")
    
    try:
        # Start the server in the background with proper environment
        env = os.environ.copy()
        env['FLASK_ENV'] = 'development'  # Use development for testing
        
        process = subprocess.Popen([
            sys.executable, 'app.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        
        # Wait for server to start with retries
        max_retries = 10
        for attempt in range(max_retries):
            time.sleep(1)
            try:
                response = requests.get('http://localhost:5001/health', timeout=2)
                if response.status_code in [200, 503]:  # 503 is also acceptable for health check
                    print("✅ Test server started successfully")
                    return process
                else:
                    print(f"⏳ Server starting... (attempt {attempt + 1}/{max_retries})")
            except requests.exceptions.RequestException:
                if attempt < max_retries - 1:
                    print(f"⏳ Waiting for server... (attempt {attempt + 1}/{max_retries})")
                else:
                    print("❌ Could not connect to test server after multiple attempts")
                    # Print server output for debugging
                    stdout, stderr = process.communicate(timeout=1)
                    if stdout:
                        print(f"Server stdout: {stdout.decode()}")
                    if stderr:
                        print(f"Server stderr: {stderr.decode()}")
                    process.terminate()
                    return None
        
        print("❌ Server failed to start within timeout")
        process.terminate()
        return None
            
    except Exception as e:
        print(f"❌ Failed to start test server: {e}")
        return None

def main():
    """Run all deployment tests"""
    print("🏴‍☠️ One Piece Character Tracker - Deployment Testing")
    print("=" * 60)
    
    # Test results
    tests_passed = 0
    total_tests = 5
    
    # Test 1: Database health
    if test_database_health():
        tests_passed += 1
    
    # Test 2: Deployment files
    if test_deployment_files():
        tests_passed += 1
    
    # Start test server for web tests
    server_process = start_test_server()
    
    if server_process:
        try:
            # Test 3: Web endpoints
            if test_web_endpoints():
                tests_passed += 1
            
            # Test 4: Error handling
            if test_error_handling():
                tests_passed += 1
            
            # Test 5: Mobile responsiveness
            if test_mobile_responsiveness():
                tests_passed += 1
                
        finally:
            # Clean up server process
            print("🛑 Stopping test server...")
            server_process.terminate()
            server_process.wait()
    else:
        print("❌ Could not start server for web tests")
    
    # Final results
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Deployment ready.")
        return 0
    elif tests_passed >= 3:
        print("⚠️  Most tests passed. Review failed tests before deployment.")
        return 1
    else:
        print("❌ Multiple tests failed. Fix issues before deployment.")
        return 2

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)