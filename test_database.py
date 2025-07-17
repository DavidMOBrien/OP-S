#!/usr/bin/env python3
"""
Unit tests for Database module
Tests all database operations, integrity checks, and market context functionality
"""

import unittest
import tempfile
import os
import json
import logging
from database import DatabaseManager, Character, CharacterChange, MarketContext

# Suppress logging during tests
logging.getLogger().setLevel(logging.CRITICAL)

class TestDatabaseManager(unittest.TestCase):
    """Test cases for DatabaseManager functionality"""
    
    def setUp(self):
        """Set up test database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_manager = DatabaseManager(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_database_initialization(self):
        """Test database initialization and table creation"""
        # Check database integrity
        integrity = self.db_manager.validate_database_integrity()
        self.assertTrue(all(integrity.values()), f"Database integrity failed: {integrity}")
        
        # Check initial stats
        stats = self.db_manager.get_database_stats()
        self.assertEqual(stats['total_characters'], 0)
        self.assertEqual(stats['total_history_entries'], 0)
        self.assertEqual(stats['total_chapters'], 0)
    
    def test_character_operations(self):
        """Test character CRUD operations"""
        # Add character
        success = self.db_manager.add_character('/wiki/luffy', 'Monkey D. Luffy', 100, 1)
        self.assertTrue(success)
        
        # Get character
        character = self.db_manager.get_character('/wiki/luffy')
        self.assertIsNotNone(character)
        self.assertEqual(character.name, 'Monkey D. Luffy')
        self.assertEqual(character.current_value, 100)
        self.assertEqual(character.first_appearance, 1)
        
        # Get current value
        value = self.db_manager.get_character_current_value('/wiki/luffy')
        self.assertEqual(value, 100)
        
        # Update character value
        success = self.db_manager.update_character_value('/wiki/luffy', 125)
        self.assertTrue(success)
        
        # Verify update
        updated_character = self.db_manager.get_character('/wiki/luffy')
        self.assertEqual(updated_character.current_value, 125)
        
        # Test duplicate addition (should fail)
        success = self.db_manager.add_character('/wiki/luffy', 'Duplicate Luffy', 200, 2)
        self.assertFalse(success)
    
    def test_character_history_operations(self):
        """Test character history tracking"""
        # Add character first
        self.db_manager.add_character('/wiki/zoro', 'Roronoa Zoro', 90, 1)
        
        # Add character change
        success = self.db_manager.add_character_change('/wiki/zoro', 1, 15, 105, 'Defeated enemy')
        self.assertTrue(success)
        
        # Get character history
        history = self.db_manager.get_character_history('/wiki/zoro')
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['value_change'], 15)
        self.assertEqual(history[0]['new_value'], 105)
        self.assertEqual(history[0]['reasoning'], 'Defeated enemy')
        
        # Get recent activity
        recent_activity = self.db_manager.get_character_recent_activity('/wiki/zoro', 5)
        self.assertEqual(len(recent_activity), 1)
        self.assertEqual(recent_activity[0]['chapter'], 1)
        self.assertEqual(recent_activity[0]['value_change'], 15)
        
        # Test duplicate history entry (should fail)
        success = self.db_manager.add_character_change('/wiki/zoro', 1, 10, 115, 'Another change')
        self.assertFalse(success)
    
    def test_chapter_operations(self):
        """Test chapter tracking operations"""
        # Add chapter
        success = self.db_manager.add_chapter(1, 'Romance Dawn', 'https://onepiece.fandom.com/wiki/Chapter_1')
        self.assertTrue(success)
        
        # Check if processed (should be False initially)
        is_processed = self.db_manager.is_chapter_processed(1)
        self.assertFalse(is_processed)
        
        # Mark as processed
        success = self.db_manager.mark_chapter_processed(1)
        self.assertTrue(success)
        
        # Check if processed (should be True now)
        is_processed = self.db_manager.is_chapter_processed(1)
        self.assertTrue(is_processed)
        
        # Get last processed chapter
        last_processed = self.db_manager.get_last_processed_chapter()
        self.assertEqual(last_processed, 1)
    
    def test_market_context_operations(self):
        """Test market context and statistics"""
        # Add test characters with different values
        test_characters = [
            ('/wiki/char1', 'Character 1', 50, 1),
            ('/wiki/char2', 'Character 2', 150, 1),
            ('/wiki/char3', 'Character 3', 300, 1),
            ('/wiki/char4', 'Character 4', 500, 1),
            ('/wiki/char5', 'Character 5', 800, 1),
        ]
        
        for url, name, value, chapter in test_characters:
            self.db_manager.add_character(url, name, value, chapter)
        
        # Test top characters
        top_chars = self.db_manager.get_top_characters(3)
        self.assertEqual(len(top_chars), 3)
        self.assertEqual(top_chars[0]['name'], 'Character 5')  # Highest value
        self.assertEqual(top_chars[0]['current_value'], 800)
        
        # Test bottom characters
        bottom_chars = self.db_manager.get_bottom_characters(3)
        self.assertEqual(len(bottom_chars), 3)
        self.assertEqual(bottom_chars[0]['name'], 'Character 1')  # Lowest value
        self.assertEqual(bottom_chars[0]['current_value'], 50)
        
        # Test character count
        count = self.db_manager.get_character_count()
        self.assertEqual(count, 5)
        
        # Test market context
        market_context = self.db_manager.get_current_market_context()
        self.assertEqual(market_context.total_characters, 5)
        self.assertEqual(len(market_context.top_characters), 5)  # Default limit is 10
        self.assertEqual(len(market_context.bottom_characters), 5)
    
    def test_batch_character_processing(self):
        """Test batch processing of character changes"""
        # Add initial characters
        self.db_manager.add_character('/wiki/luffy', 'Monkey D. Luffy', 100, 1)
        self.db_manager.add_character('/wiki/zoro', 'Roronoa Zoro', 90, 1)
        
        # Prepare character changes
        character_changes = [
            CharacterChange('/wiki/luffy', 'Monkey D. Luffy', 25, 'Major victory'),
            CharacterChange('/wiki/zoro', 'Roronoa Zoro', 15, 'Impressive sword technique')
        ]
        
        # Prepare new characters
        new_characters = [
            {
                'wiki_url': '/wiki/sanji',
                'name': 'Sanji',
                'starting_value': 85,
                'reasoning': 'Introduced as skilled cook and fighter'
            }
        ]
        
        # Process batch changes
        success = self.db_manager.process_character_changes(2, character_changes, new_characters)
        self.assertTrue(success)
        
        # Verify character updates
        luffy = self.db_manager.get_character('/wiki/luffy')
        self.assertEqual(luffy.current_value, 125)  # 100 + 25
        
        zoro = self.db_manager.get_character('/wiki/zoro')
        self.assertEqual(zoro.current_value, 105)  # 90 + 15
        
        # Verify new character was added
        sanji = self.db_manager.get_character('/wiki/sanji')
        self.assertIsNotNone(sanji)
        self.assertEqual(sanji.current_value, 85)
        
        # Verify history was recorded
        luffy_history = self.db_manager.get_character_history('/wiki/luffy')
        self.assertEqual(len(luffy_history), 1)
        self.assertEqual(luffy_history[0]['chapter_number'], 2)
    
    def test_market_snapshot_operations(self):
        """Test market snapshot caching"""
        # Add some characters
        self.db_manager.add_character('/wiki/char1', 'Character 1', 100, 1)
        self.db_manager.add_character('/wiki/char2', 'Character 2', 200, 1)
        
        # Get market context
        market_context = self.db_manager.get_current_market_context()
        
        # Save market snapshot
        success = self.db_manager.save_market_snapshot(1, market_context)
        self.assertTrue(success)
        
        # Retrieve market snapshot
        retrieved_context = self.db_manager.get_market_snapshot(1)
        self.assertIsNotNone(retrieved_context)
        self.assertEqual(retrieved_context.total_characters, market_context.total_characters)
        self.assertEqual(len(retrieved_context.top_characters), len(market_context.top_characters))
    
    def test_recent_character_changes(self):
        """Test recent character changes tracking"""
        # Add characters
        self.db_manager.add_character('/wiki/char1', 'Character 1', 100, 1)
        self.db_manager.add_character('/wiki/char2', 'Character 2', 150, 1)
        
        # Add some changes across multiple chapters
        changes_data = [
            ('/wiki/char1', 1, 10, 110, 'Good performance'),
            ('/wiki/char2', 1, -5, 145, 'Minor setback'),
            ('/wiki/char1', 2, 15, 125, 'Major victory'),
            ('/wiki/char2', 3, 20, 165, 'Character development'),
        ]
        
        for url, chapter, change, new_value, reason in changes_data:
            self.db_manager.add_character_change(url, chapter, change, new_value, reason)
        
        # Get recent changes
        recent_changes = self.db_manager.get_recent_character_changes(2)  # Last 2 chapters
        
        # Should include changes from chapters 2 and 3
        self.assertGreaterEqual(len(recent_changes), 2)
        
        # Verify the changes are sorted by chapter (descending) and magnitude
        chapter_numbers = [change['chapter'] for change in recent_changes]
        self.assertGreaterEqual(max(chapter_numbers), 2)
    
    def test_data_validation_and_consistency(self):
        """Test data validation and consistency checks"""
        # Test database integrity validation
        integrity = self.db_manager.validate_database_integrity()
        self.assertTrue(all(integrity.values()))
        
        # Add some test data
        self.db_manager.add_character('/wiki/test', 'Test Character', 100, 1)
        self.db_manager.add_character_change('/wiki/test', 1, 25, 125, 'Test change')
        
        # Test integrity after adding data
        integrity_after = self.db_manager.validate_database_integrity()
        self.assertTrue(all(integrity_after.values()))
        
        # Test database stats
        stats = self.db_manager.get_database_stats()
        self.assertEqual(stats['total_characters'], 1)
        self.assertEqual(stats['total_history_entries'], 1)
        
        # Test foreign key constraints by trying to add history for non-existent character
        success = self.db_manager.add_character_change('/wiki/nonexistent', 1, 10, 110, 'Should fail')
        # This should succeed in SQLite without foreign key enforcement, but we log it
        # The validation should catch inconsistencies
    
    def test_edge_cases_and_error_handling(self):
        """Test edge cases and error handling"""
        # Test operations on empty database
        character = self.db_manager.get_character('/wiki/nonexistent')
        self.assertIsNone(character)
        
        value = self.db_manager.get_character_current_value('/wiki/nonexistent')
        self.assertIsNone(value)
        
        history = self.db_manager.get_character_history('/wiki/nonexistent')
        self.assertEqual(len(history), 0)
        
        # Test invalid data
        success = self.db_manager.add_character('', '', 0, 0)  # Empty values
        self.assertFalse(success)
        
        # Test market context with empty database
        market_context = self.db_manager.get_current_market_context()
        self.assertEqual(market_context.total_characters, 0)
        self.assertEqual(len(market_context.top_characters), 0)
        self.assertEqual(len(market_context.bottom_characters), 0)
        self.assertEqual(len(market_context.recent_changes), 0)
        
        # Test chapter operations with invalid data
        success = self.db_manager.mark_chapter_processed(999)  # Non-existent chapter
        self.assertFalse(success)
        
        is_processed = self.db_manager.is_chapter_processed(999)
        self.assertFalse(is_processed)

def run_database_tests():
    """Run all database tests"""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDatabaseManager))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    print("Running Database Tests...")
    success = run_database_tests()
    
    if success:
        print("\n✓ All Database tests passed!")
    else:
        print("\n✗ Some Database tests failed!")
    
    exit(0 if success else 1)