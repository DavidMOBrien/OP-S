#!/usr/bin/env python3
"""
Test script to verify character detail functionality
"""
import sqlite3
import os
from urllib.parse import quote

def test_character_detail_data():
    """Test that character detail data is accessible"""
    DATABASE_PATH = 'one_piece_tracker.db'
    
    if not os.path.exists(DATABASE_PATH):
        print("❌ Database not found. Run data generation script first.")
        return False
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get a sample character
        cursor.execute("""
            SELECT wiki_url, name, current_value, first_appearance 
            FROM characters 
            ORDER BY current_value DESC 
            LIMIT 1
        """)
        character = cursor.fetchone()
        
        if not character:
            print("❌ No characters found in database")
            return False
        
        print(f"✅ Testing character: {character['name']}")
        print(f"   Wiki URL: {character['wiki_url']}")
        print(f"   Current Value: {character['current_value']}")
        print(f"   First Appearance: Chapter {character['first_appearance']}")
        
        # Test character history with chapter titles
        cursor.execute("""
            SELECT ch.chapter_number, ch.value_change, ch.reasoning, c.title as chapter_title
            FROM character_history ch
            LEFT JOIN chapters c ON ch.chapter_number = c.number
            WHERE ch.character_wiki_url = ? 
            ORDER BY ch.chapter_number
            LIMIT 3
        """, (character['wiki_url'],))
        history = cursor.fetchall()
        
        print(f"✅ Found {len(history)} history entries (showing first 3):")
        for entry in history:
            chapter_info = f"Chapter {entry['chapter_number']}"
            if entry['chapter_title']:
                chapter_info += f" - {entry['chapter_title']}"
            print(f"   {chapter_info}: {entry['value_change']:+d} ({entry['reasoning'][:50]}...)")
        
        # Test navigation data
        cursor.execute("""
            SELECT wiki_url, name, current_value 
            FROM characters 
            WHERE current_value > ? 
            ORDER BY current_value ASC 
            LIMIT 1
        """, (character['current_value'],))
        next_character = cursor.fetchone()
        
        cursor.execute("""
            SELECT wiki_url, name, current_value 
            FROM characters 
            WHERE current_value < ? 
            ORDER BY current_value DESC 
            LIMIT 1
        """, (character['current_value'],))
        prev_character = cursor.fetchone()
        
        print(f"✅ Navigation:")
        if prev_character:
            print(f"   Previous: {prev_character['name']} ({prev_character['current_value']})")
        if next_character:
            print(f"   Next: {next_character['name']} ({next_character['current_value']})")
        
        # Test related characters
        cursor.execute("""
            SELECT DISTINCT c.wiki_url, c.name, c.current_value
            FROM characters c
            JOIN character_history ch ON c.wiki_url = ch.character_wiki_url
            WHERE ch.chapter_number IN (
                SELECT chapter_number 
                FROM character_history 
                WHERE character_wiki_url = ?
                LIMIT 5
            )
            AND c.wiki_url != ?
            ORDER BY c.current_value DESC
            LIMIT 3
        """, (character['wiki_url'], character['wiki_url']))
        related = cursor.fetchall()
        
        print(f"✅ Found {len(related)} related characters (showing first 3):")
        for rel in related:
            print(f"   {rel['name']}: {rel['current_value']}")
        
        # Test character statistics
        if history:
            total_changes = sum(h['value_change'] for h in history)
            positive_changes = sum(h['value_change'] for h in history if h['value_change'] > 0)
            negative_changes = sum(h['value_change'] for h in history if h['value_change'] < 0)
            
            print(f"✅ Character Statistics:")
            print(f"   Total Changes: {len(history)}")
            print(f"   Total Value Change: {total_changes:+d}")
            print(f"   Positive Changes: +{positive_changes}")
            print(f"   Negative Changes: {negative_changes}")
            print(f"   Average Change: {total_changes/len(history):+.1f}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error testing character detail: {e}")
        return False

def test_url_encoding():
    """Test URL encoding for character wiki URLs"""
    test_urls = [
        "https://onepiece.fandom.com/wiki/Monkey_D._Luffy",
        "https://onepiece.fandom.com/wiki/Roronoa_Zoro",
        "https://onepiece.fandom.com/wiki/Nami_(Navigator)"
    ]
    
    print("✅ Testing URL encoding:")
    for url in test_urls:
        encoded = quote(url, safe='')
        print(f"   Original: {url}")
        print(f"   Encoded:  {encoded}")
        print()

if __name__ == "__main__":
    print("Testing Character Detail Views")
    print("=" * 40)
    
    success = test_character_detail_data()
    print()
    test_url_encoding()
    
    if success:
        print("✅ Character detail functionality appears to be working correctly!")
        print("\nTo test the web interface:")
        print("1. Run: python app.py")
        print("2. Open: http://localhost:5001")
        print("3. Click on any character name to view their detail page")
    else:
        print("❌ Character detail functionality has issues that need to be resolved")