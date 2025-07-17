"""
Basic tests for the Flask web application
"""
import pytest
import tempfile
import os
import sqlite3
from app import app, get_db_connection, init_db

@pytest.fixture
def client():
    """Create a test client"""
    # Create a temporary database for testing
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client
    
    os.close(db_fd)
    os.unlink(app.config['DATABASE'])

def test_index_route_no_database():
    """Test index route when database doesn't exist"""
    with app.test_client() as client:
        response = client.get('/')
        assert response.status_code == 200
        assert b'No Character Data Available' in response.data or b'Database connection failed' in response.data

def test_api_characters_no_database():
    """Test API endpoint when database doesn't exist"""
    with app.test_client() as client:
        response = client.get('/api/characters')
        assert response.status_code == 500
        assert b'error' in response.data

def test_character_detail_not_found():
    """Test character detail route with non-existent character"""
    with app.test_client() as client:
        response = client.get('/character/non-existent')
        assert response.status_code == 404 or response.status_code == 500

def test_404_handler():
    """Test 404 error handler"""
    with app.test_client() as client:
        response = client.get('/non-existent-route')
        assert response.status_code == 404
        assert b'Page not found' in response.data

if __name__ == '__main__':
    pytest.main([__file__])