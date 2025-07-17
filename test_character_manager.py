#!/usr/bin/env python3
"""
Test suite for Character Management System
Tests character identification, value scaling, market dynamics, and validation
"""

import unittest
import tempfile
import os
import logging
from database import DatabaseManager, CharacterChange
from character_manager import CharacterManager

# Suppress logging during tests
logging.getLogger().setLevel(logging.CRITICAL)

class TestCharacterManager(unittest.TestCase):
    """Test cases for CharacterManager functionality"""
    
    def setUp(self):
        """Set up test database and character manager"""
        # Create temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.db_manager = DatabaseManager(self.temp_db.name)
        self.char_manager = CharacterManager(self.db_manager)
    
    def tearDown(self):
        """Clean up test database"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_character_duplicate_identification(self):
        """Test identification of duplicate characters"""
        test_characters = [
            {'name': 'Monkey D. Luffy', 'wiki_url': '/wiki/Monkey_D._Luffy'},
            {'name': 'Monkey D Luffy', 'wiki_url': '/wiki/Monkey_D._Luffy_Alt'},  # Similar name
            {'name': 'Roronoa Zoro', 'wiki_url': '/wiki/Roronoa_Zoro'},
            {'name': 'Roronoa Zoro', 'wiki_url': '/wiki/Roronoa_Zoro'},  # Exact duplicate
            {'name': 'Sanji', 'wiki_url': '/wiki/Sanji'},
        ]
        
        duplicates = self.char_manager.identify_character_duplicates(test_characters)
        
        # Should find at least one duplicate group
        self.assertGreater(len(duplicates), 0)
        
        # Check for exact URL duplicates
        exact_duplicates = [group for group in duplicates.values() 
                          if any(char['wiki_url'] == '/wiki/Roronoa_Zoro' for char in group)]
        self.assertGreater(len(exact_duplicates), 0)
    
    def test_starting_value_calculation(self):
        """Test starting value calculation for new characters"""
        # Test different character types
        test_cases = [
            {
                'character': {'name': 'Test Admiral', 'wiki_url': '/wiki/Test_Admiral'},
                'chapter': 500,
                'expected_min': 800,  # Should be high for Admiral
            },
            {
                'character': {'name': 'Random Pirate', 'wiki_url': '/wiki/Random_Pirate'},
                'chapter': 100,
                'expected_min': 50,   # Should be lower for early chapter
            },
            {
                'character': {'name': 'Yonko Character', 'wiki_url': '/wiki/Yonko_Character'},
                'chapter': 800,
                'expected_min': 1000,  # Should be very high for late-game Yonko
            }
        ]
        
        market_context = {
            'total_characters': 10,
            'top_characters': [{'name': 'Top', 'current_value': 900}],
            'bottom_characters': [{'name': 'Bottom', 'current_value': 50}],
            'recent_changes': []
        }
        
        for case in test_cases:
            introduction = self.char_manager.calculate_starting_value(
                case['character'], case['chapter'], market_context
            )
            
            self.assertGreaterEqual(introduction.starting_value, case['expected_min'])
            self.assertLessEqual(introduction.starting_value, 1000)  # Max cap
            self.assertGreater(len(introduction.reasoning), 10)  # Should have reasoning
    
    def test_value_change_validation(self):
        """Test value change validation and adjustment"""
        # Add a test character to database
        test_char_url = '/wiki/Test_Character'
        self.db_manager.add_character(test_char_url, 'Test Character', 300, 1)
        
        # Test various change scenarios
        test_cases = [
            {
                'change': 25,
                'reasoning': 'Defeated major opponent in epic battle',
                'should_be_valid': True
            },
            {
                'change': 150,  # Too large
                'reasoning': 'Minor appearance',
                'should_be_valid': True,  # Should be adjusted, not rejected
                'expect_adjustment': True
            },
            {
                'change': -200,  # Too large decrease
                'reasoning': 'Lost badly',
                'should_be_valid': True,  # Should be adjusted
                'expect_adjustment': True
            },
            {
                'change': 10,
                'reasoning': 'Good performance in battle with advanced techniques',
                'should_be_valid': True
            }
        ]
        
        for case in test_cases:
            validation = self.char_manager.validate_value_change(
                test_char_url, case['change'], case['reasoning'], 1
            )
            
            self.assertEqual(validation.is_valid, case['should_be_valid'])
            
            if case.get('expect_adjustment'):
                self.assertNotEqual(validation.adjusted_change, case['change'])
                self.assertLess(abs(validation.adjusted_change), abs(case['change']))
    
    def test_market_dynamics_calculation(self):
        """Test market dynamics calculation"""
        # Add some test characters with different values
        test_characters = [
            ('char1', 'Character 1', 100),
            ('char2', 'Character 2', 300),
            ('char3', 'Character 3', 500),
            ('char4', 'Character 4', 800),
            ('char5', 'Character 5', 50),
        ]
        
        for url, name, value in test_characters:
            self.db_manager.add_character(f'/wiki/{url}', name, value, 1)
        
        # Calculate market dynamics
        dynamics = self.char_manager.calculate_market_dynamics()
        
        # Verify calculations
        expected_average = sum(char[2] for char in test_characters) / len(test_characters)
        self.assertAlmostEqual(dynamics.average_value, expected_average, places=1)
        
        # Should have value distribution
        self.assertGreater(len(dynamics.value_distribution), 0)
        
        # Thresholds should be reasonable
        self.assertGreater(dynamics.top_tier_threshold, dynamics.mid_tier_threshold)
        self.assertGreater(dynamics.mid_tier_threshold, 0)
    
    def test_tier_threshold_updates(self):
        """Test tier threshold updates based on market dynamics"""
        # Add characters to create a market
        for i in range(10):
            value = (i + 1) * 100  # Values from 100 to 1000
            self.db_manager.add_character(f'/wiki/char_{i}', f'Character {i}', value, 1)
        
        # Calculate market dynamics and update thresholds
        dynamics = self.char_manager.calculate_market_dynamics()
        old_thresholds = self.char_manager.tier_thresholds.copy()
        
        self.char_manager.update_tier_thresholds(dynamics)
        
        # Thresholds should have been updated
        self.assertNotEqual(old_thresholds, self.char_manager.tier_thresholds)
        
        # New thresholds should be reasonable
        thresholds = self.char_manager.tier_thresholds
        self.assertGreater(thresholds['legendary'], thresholds['top_tier'])
        self.assertGreater(thresholds['top_tier'], thresholds['high_tier'])
        self.assertGreater(thresholds['high_tier'], thresholds['mid_tier'])
    
    def test_character_history_maintenance(self):
        """Test character history maintenance"""
        # Add a character and some history
        char_url = '/wiki/test_char'
        self.db_manager.add_character(char_url, 'Test Char', 200, 1)
        
        # Add some character changes
        changes = [
            CharacterChange(char_url, 'Test Char', 25, 'Good performance'),
            CharacterChange(char_url, 'Test Char', -10, 'Minor setback'),
        ]
        
        self.db_manager.process_character_changes(1, changes, [])
        
        # Test maintenance
        success = self.char_manager.maintain_character_histories(1)
        self.assertTrue(success)
        
        # Verify market snapshot was created
        market_context = self.db_manager.get_market_snapshot(1)
        self.assertIsNotNone(market_context)
    
    def test_character_recommendations(self):
        """Test character recommendation system"""
        # Add some existing characters
        self.db_manager.add_character('/wiki/existing_char', 'Existing Character', 500, 1)
        
        # Add some history to make it volatile
        changes = [CharacterChange('/wiki/existing_char', 'Existing Character', 50, 'Big win')]
        self.db_manager.process_character_changes(1, changes, [])
        
        # Test chapter characters
        chapter_characters = [
            {'name': 'Existing Character', 'wiki_url': '/wiki/existing_char'},
            {'name': 'New Character', 'wiki_url': '/wiki/new_char'},
            {'name': 'Duplicate Name', 'wiki_url': '/wiki/duplicate1'},
            {'name': 'Duplicate Name', 'wiki_url': '/wiki/duplicate2'},
        ]
        
        market_context = {
            'total_characters': 1,
            'top_characters': [{'name': 'Existing Character', 'current_value': 550}],
            'bottom_characters': [],
            'recent_changes': []
        }
        
        recommendations = self.char_manager.get_character_recommendations(
            chapter_characters, market_context
        )
        
        # Should identify new character
        self.assertIn('New Character', recommendations['new_introductions'])
        
        # Should identify potential duplicates
        self.assertGreater(len(recommendations['potential_duplicates']), 0)
    
    def test_reasoning_quality_evaluation(self):
        """Test reasoning quality evaluation"""
        test_cases = [
            ('Defeated major boss in epic battle', 0.6),  # High quality
            ('Appeared in chapter', 0.1),  # Low quality
            ('', 0.0),  # Empty reasoning
            ('Showed advanced haki techniques and defeated multiple opponents', 0.8),  # Very high quality
        ]
        
        for reasoning, expected_min_score in test_cases:
            score = self.char_manager._evaluate_reasoning_quality(reasoning)
            self.assertGreaterEqual(score, expected_min_score)
            self.assertLessEqual(score, 1.0)

class TestCharacterManagerIntegration(unittest.TestCase):
    """Integration tests for character manager with database"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.db_manager = DatabaseManager(self.temp_db.name)
        self.char_manager = CharacterManager(self.db_manager)
    
    def tearDown(self):
        """Clean up"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_full_character_processing_workflow(self):
        """Test complete character processing workflow"""
        # Simulate processing a chapter with new and existing characters
        
        # Add an existing character
        existing_char_url = '/wiki/luffy'
        self.db_manager.add_character(existing_char_url, 'Monkey D. Luffy', 150, 1)
        
        # Simulate LLM analysis results
        character_changes = [
            CharacterChange(existing_char_url, 'Monkey D. Luffy', 25, 'Defeated Arlong in epic battle')
        ]
        
        new_characters = [
            {
                'name': 'Dracule Mihawk',
                'wiki_url': '/wiki/mihawk',
                'starting_value': 800,  # Will be recalculated
                'reasoning': 'Introduced as World\'s Strongest Swordsman'
            }
        ]
        
        # Process character changes directly through database manager
        success = self.db_manager.process_character_changes(2, character_changes, new_characters)
        self.assertTrue(success)
        
        # Verify results
        # Check existing character was updated
        luffy = self.db_manager.get_character(existing_char_url)
        self.assertEqual(luffy.current_value, 175)  # 150 + 25
        
        # Check new character was added
        mihawk = self.db_manager.get_character('/wiki/mihawk')
        self.assertIsNotNone(mihawk)
        self.assertEqual(mihawk.current_value, 800)  # Starting value
        
        # Check history was recorded
        luffy_history = self.db_manager.get_character_history(existing_char_url)
        self.assertEqual(len(luffy_history), 1)
        self.assertEqual(luffy_history[0]['value_change'], 25)
        
        # Test character manager maintenance
        success = self.char_manager.maintain_character_histories(2)
        self.assertTrue(success)

def run_tests():
    """Run all character manager tests"""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(TestCharacterManager))
    suite.addTest(unittest.makeSuite(TestCharacterManagerIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    print("Running Character Manager Tests...")
    success = run_tests()
    
    if success:
        print("\n✓ All Character Manager tests passed!")
    else:
        print("\n✗ Some Character Manager tests failed!")
    
    exit(0 if success else 1)