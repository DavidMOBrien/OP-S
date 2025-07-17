#!/usr/bin/env python3
"""
Test script for the character history API endpoint and charts functionality
"""
import sqlite3
import json
from app import app

def test_character_history_api():
    """Test the character history API endpoint"""
    
    # Get a sample character from the database
    conn = sqlite3.connect('one_piece_tracker.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT wiki_url, name FROM characters LIMIT 1")
    character = cursor.fetchone()
    
    if not character:
        print("No characters found in database")
        return
    
    print(f"Testing API for character: {character['name']}")
    print(f"Wiki URL: {character['wiki_url']}")
    
    # Test the API endpoint
    with app.test_client() as client:
        response = client.get(f"/api/character/{character['wiki_url']}/history")
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.get_json()
            print(f"Character name: {data['character']['name']}")
            print(f"Current value: {data['character']['current_value']}")
            print(f"First appearance: {data['character']['first_appearance']}")
            print(f"History entries: {len(data['history'])}")
            
            if data['history']:
                print("\nFirst few history entries:")
                for entry in data['history'][:3]:
                    print(f"  Chapter {entry['chapter']}: Value {entry['value']} (change: {entry['change']})")
                    print(f"    Reasoning: {entry['reasoning'][:50]}...")
        else:
            print(f"Error: {response.get_data(as_text=True)}")
    
    conn.close()

def test_charts_page():
    """Test the charts page loads correctly"""
    print("\n" + "="*50)
    print("Testing Charts Page")
    print("="*50)
    
    with app.test_client() as client:
        response = client.get("/charts")
        print(f"Charts page status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.get_data(as_text=True)
            # Check for key elements
            checks = [
                ("Chart.js script", "chart.js" in content.lower()),
                ("Character selection", "character-selection" in content),
                ("Chart container", "character-chart" in content),
                ("Chart options", "chart-options" in content),
                ("Selected characters", "selected-characters" in content)
            ]
            
            for check_name, result in checks:
                status = "✓" if result else "✗"
                print(f"  {status} {check_name}")
        else:
            print(f"Error loading charts page: {response.status_code}")

def test_character_detail_with_chart():
    """Test character detail page includes chart"""
    print("\n" + "="*50)
    print("Testing Character Detail Page with Chart")
    print("="*50)
    
    # Get a character with history
    conn = sqlite3.connect('one_piece_tracker.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT c.wiki_url, c.name 
        FROM characters c 
        JOIN character_history ch ON c.wiki_url = ch.character_wiki_url 
        LIMIT 1
    """)
    character = cursor.fetchone()
    conn.close()
    
    if not character:
        print("No characters with history found")
        return
    
    with app.test_client() as client:
        response = client.get(f"/character/{character['wiki_url']}")
        print(f"Character detail page status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.get_data(as_text=True)
            # Check for chart elements
            checks = [
                ("Chart.js script", "chart.js" in content.lower()),
                ("Chart section", "character-chart-section" in content),
                ("Chart canvas", "character-chart" in content),
                ("Navigation links", "navigation-links" in content),
                ("Compare button", "Compare with Others" in content)
            ]
            
            for check_name, result in checks:
                status = "✓" if result else "✗"
                print(f"  {status} {check_name}")
        else:
            print(f"Error loading character detail page: {response.status_code}")

def test_api_endpoints():
    """Test all API endpoints"""
    print("\n" + "="*50)
    print("Testing API Endpoints")
    print("="*50)
    
    with app.test_client() as client:
        # Test characters API
        response = client.get("/api/characters")
        print(f"Characters API status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.get_json()
            print(f"  Characters returned: {len(data.get('characters', []))}")
        
        # Test character history API with multiple characters
        conn = sqlite3.connect('one_piece_tracker.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT c.wiki_url, c.name 
            FROM characters c 
            JOIN character_history ch ON c.wiki_url = ch.character_wiki_url 
            LIMIT 3
        """)
        characters = cursor.fetchall()
        conn.close()
        
        print(f"\nTesting history API for {len(characters)} characters:")
        for char in characters:
            response = client.get(f"/api/character/{char['wiki_url']}/history")
            status = "✓" if response.status_code == 200 else "✗"
            print(f"  {status} {char['name']}: {response.status_code}")

if __name__ == "__main__":
    test_character_history_api()
    test_charts_page()
    test_character_detail_with_chart()
    test_api_endpoints()
    
    print("\n" + "="*50)
    print("All tests completed!")
    print("="*50)