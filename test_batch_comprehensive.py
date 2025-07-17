#!/usr/bin/env python3
"""
Comprehensive integration tests for batch processing
Tests end-to-end processing with sample chapters and validates results
"""

import unittest
import tempfile
import os
import json
import logging
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from database import DatabaseManager, CharacterChange
from character_manager import CharacterManager
from llm_analyzer import LLMAnalyzer, LLMConfig, CharacterAnalysis
from wiki_crawler import WikiCrawler
from batch_processor import BatchProcessor

# Suppress logging during tests
logging.getLogger().setLevel(logging.CRITICAL)

class TestBatchProcessingIntegration(unittest.TestCase):
    """Comprehensive integration tests for batch processing"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Create temporary log directory
        self.temp_log_dir = tempfile.mkdtemp()
        
        # Initialize components
        self.db_manager = DatabaseManager(self.temp_db.name)
        self.character_manager = CharacterManager(self.db_manager)
        
        # Sample chapter data for testing
        self.sample_chapters = [
            {
                'number': 1,
                'title': 'Romance Dawn',
                'summary': '''Monkey D. Luffy begins his journey as a pirate after eating the Gomu Gomu no Mi. 
                He demonstrates his rubber powers and shows determination to become the Pirate King. 
                He meets Coby, a cowardly boy forced to work on Alvida's pirate ship, and helps him escape.''',
                'characters': [
                    {'name': 'Monkey D. Luffy', 'wiki_url': '/wiki/Monkey_D._Luffy'},
                    {'name': 'Coby', 'wiki_url': '/wiki/Coby'},
                    {'name': 'Alvida', 'wiki_url': '/wiki/Alvida'}
                ],
                'next_chapter_url': '/wiki/Chapter_2'
            },
            {
                'number': 2,
                'title': 'They Call Him "Straw Hat Luffy"',
                'summary': '''Luffy arrives at Shells Town and learns about Roronoa Zoro, a famous pirate hunter 
                who is being held captive by Captain Morgan. Luffy decides to recruit Zoro to his crew. 
                He meets Rika, a young girl who tells him about Zoro's situation.''',
                'characters': [
                    {'name': 'Monkey D. Luffy', 'wiki_url': '/wiki/Monkey_D._Luffy'},
                    {'name': 'Roronoa Zoro', 'wiki_url': '/wiki/Roronoa_Zoro'},
                    {'name': 'Morgan', 'wiki_url': '/wiki/Morgan'},
                    {'name': 'Rika', 'wiki_url': '/wiki/Rika'}
                ],
                'next_chapter_url': '/wiki/Chapter_3'
            },
            {
                'number': 3,
                'title': 'Enter Zoro: Pirate Hunter',
                'summary': '''Luffy meets Zoro and offers to free him if he joins his crew. Zoro initially refuses 
                but agrees after Luffy helps him. They work together to defeat Captain Morgan and his son Helmeppo. 
                Zoro officially joins Luffy's crew as his first mate.''',
                'characters': [
                    {'name': 'Monkey D. Luffy', 'wiki_url': '/wiki/Monkey_D._Luffy'},
                    {'name': 'Roronoa Zoro', 'wiki_url': '/wiki/Roronoa_Zoro'},
                    {'name': 'Morgan', 'wiki_url': '/wiki/Morgan'},
                    {'name': 'Helmeppo', 'wiki_url': '/wiki/Helmeppo'}
                ],
                'next_chapter_url': '/wiki/Chapter_4'
            }
        ]
    
    def tearDown(self):
        """Clean up test environment"""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
        
        # Clean up log directory
        import shutil
        if os.path.exists(self.temp_log_dir):
            shutil.rmtree(self.temp_log_dir)
    
    def create_mock_llm_analyzer(self):
        """Create a mock LLM analyzer that returns realistic responses"""
        class MockLLMAnalyzer:
            def __init__(self, config):
                self.config = config
                self.call_count = 0
            
            def analyze_chapter(self, chapter_data, chapter_character_values, market_context):
                self.call_count += 1
                chapter_num = chapter_data['number']
                
                character_changes = []
                new_characters = []
                
                # Generate realistic responses based on chapter content
                for char in chapter_character_values:
                    if char['exists_in_db']:
                        # Existing character - add value change based on chapter
                        if chapter_num == 1 and char['name'] == 'Monkey D. Luffy':
                            character_changes.append({
                                'wiki_url': char['wiki_url'],
                                'name': char['name'],
                                'value_change': 25,
                                'reasoning': 'Demonstrated Devil Fruit powers and determination to become Pirate King'
                            })
                        elif chapter_num == 2 and char['name'] == 'Monkey D. Luffy':
                            character_changes.append({
                                'wiki_url': char['wiki_url'],
                                'name': char['name'],
                                'value_change': 15,
                                'reasoning': 'Showed leadership by deciding to recruit Zoro'
                            })
                        elif chapter_num == 3 and char['name'] == 'Roronoa Zoro':
                            character_changes.append({
                                'wiki_url': char['wiki_url'],
                                'name': char['name'],
                                'value_change': 30,
                                'reasoning': 'Joined the crew and helped defeat Captain Morgan'
                            })
                    else:
                        # New character - set starting value
                        starting_values = {
                            'Monkey D. Luffy': 100,
                            'Coby': 25,
                            'Alvida': 80,
                            'Roronoa Zoro': 90,
                            'Morgan': 60,
                            'Rika': 15,
                            'Helmeppo': 20
                        }
                        
                        starting_value = starting_values.get(char['name'], 50)
                        new_characters.append({
                            'wiki_url': char['wiki_url'],
                            'name': char['name'],
                            'starting_value': starting_value,
                            'reasoning': f'Introduction of {char["name"]} in Chapter {chapter_num}'
                        })
                
                return CharacterAnalysis(
                    character_changes=character_changes,
                    new_characters=new_characters,
                    analysis_reasoning=f'Analysis of Chapter {chapter_num} completed successfully'
                )
        
        return MockLLMAnalyzer(LLMConfig())
    
    def create_mock_crawler(self):
        """Create a mock crawler that returns sample chapter data"""
        class MockCrawler:
            def __init__(self, rate_limit=0):
                self.rate_limit = rate_limit
                self.chapters = {
                    "https://onepiece.fandom.com/wiki/Chapter_1": self.sample_chapters[0],
                    "https://onepiece.fandom.com/wiki/Chapter_2": self.sample_chapters[1],
                    "https://onepiece.fandom.com/wiki/Chapter_3": self.sample_chapters[2]
                }
            
            def scrape_chapter_page(self, chapter_url):
                return self.chapters.get(chapter_url)
        
        return MockCrawler()
    
    def test_single_chapter_processing_workflow(self):
        """Test processing a single chapter through the complete workflow"""
        # Create mock components
        mock_crawler = self.create_mock_crawler()
        mock_llm = self.create_mock_llm_analyzer()
        
        # Process Chapter 1
        chapter_data = mock_crawler.scrape_chapter_page("https://onepiece.fandom.com/wiki/Chapter_1")
        self.assertIsNotNone(chapter_data)
        
        # Get character values (should all be new)
        chapter_character_values = []
        for char in chapter_data['characters']:
            current_value = self.db_manager.get_character_current_value(char['wiki_url'])
            recent_activity = self.db_manager.get_character_recent_activity(char['wiki_url'], 5)
            chapter_character_values.append({
                'name': char['name'],
                'wiki_url': char['wiki_url'],
                'current_value': current_value,
                'exists_in_db': current_value is not None,
                'recent_activity': recent_activity
            })
        
        # All characters should be new
        new_character_count = sum(1 for char in chapter_character_values if not char['exists_in_db'])
        self.assertEqual(new_character_count, len(chapter_character_values))
        
        # Get market context (should be empty)
        market_context = self.db_manager.get_current_market_context()
        self.assertEqual(market_context.total_characters, 0)
        
        # Analyze with LLM
        analysis_result = mock_llm.analyze_chapter(
            chapter_data, 
            chapter_character_values, 
            {
                'total_characters': market_context.total_characters,
                'top_characters': market_context.top_characters,
                'bottom_characters': market_context.bottom_characters,
                'recent_changes': market_context.recent_changes
            }
        )
        
        self.assertIsNotNone(analysis_result)
        self.assertGreater(len(analysis_result.new_characters), 0)
        
        # Process character changes
        character_changes = [CharacterChange(
            wiki_url=change['wiki_url'],
            name=change['name'],
            value_change=change['value_change'],
            reasoning=change['reasoning']
        ) for change in analysis_result.character_changes]
        
        success = self.db_manager.process_character_changes(
            chapter_data['number'],
            character_changes,
            analysis_result.new_characters
        )
        
        self.assertTrue(success)
        
        # Verify characters were added
        all_characters = self.db_manager.get_all_characters()
        self.assertGreater(len(all_characters), 0)
        
        # Verify specific characters
        luffy = self.db_manager.get_character('/wiki/Monkey_D._Luffy')
        self.assertIsNotNone(luffy)
        self.assertEqual(luffy.name, 'Monkey D. Luffy')
        
        # Mark chapter as processed
        self.db_manager.add_chapter(chapter_data['number'], chapter_data['title'], '')
        self.db_manager.mark_chapter_processed(chapter_data['number'])
        
        # Verify chapter was marked as processed
        self.assertTrue(self.db_manager.is_chapter_processed(1))
    
    def test_sequential_chapter_processing(self):
        """Test processing multiple chapters in sequence"""
        mock_crawler = self.create_mock_crawler()
        mock_llm = self.create_mock_llm_analyzer()
        
        processed_chapters = []
        
        # Process chapters 1-3 in sequence
        for i in range(1, 4):
            chapter_url = f"https://onepiece.fandom.com/wiki/Chapter_{i}"
            chapter_data = mock_crawler.scrape_chapter_page(chapter_url)
            
            self.assertIsNotNone(chapter_data, f"Failed to get data for Chapter {i}")
            
            # Get current character values and market context
            chapter_character_values = []
            for char in chapter_data['characters']:
                current_value = self.db_manager.get_character_current_value(char['wiki_url'])
                recent_activity = self.db_manager.get_character_recent_activity(char['wiki_url'], 5)
                chapter_character_values.append({
                    'name': char['name'],
                    'wiki_url': char['wiki_url'],
                    'current_value': current_value,
                    'exists_in_db': current_value is not None,
                    'recent_activity': recent_activity
                })
            
            market_context = self.db_manager.get_current_market_context()
            
            # Analyze chapter
            analysis_result = mock_llm.analyze_chapter(
                chapter_data,
                chapter_character_values,
                {
                    'total_characters': market_context.total_characters,
                    'top_characters': market_context.top_characters,
                    'bottom_characters': market_context.bottom_characters,
                    'recent_changes': market_context.recent_changes
                }
            )
            
            self.assertIsNotNone(analysis_result, f"LLM analysis failed for Chapter {i}")
            
            # Process changes
            character_changes = [CharacterChange(
                wiki_url=change['wiki_url'],
                name=change['name'],
                value_change=change['value_change'],
                reasoning=change['reasoning']
            ) for change in analysis_result.character_changes]
            
            success = self.db_manager.process_character_changes(
                chapter_data['number'],
                character_changes,
                analysis_result.new_characters
            )
            
            self.assertTrue(success, f"Failed to process changes for Chapter {i}")
            
            # Mark as processed
            self.db_manager.add_chapter(chapter_data['number'], chapter_data['title'], '')
            self.db_manager.mark_chapter_processed(chapter_data['number'])
            
            processed_chapters.append(i)
        
        # Verify all chapters were processed
        for chapter_num in processed_chapters:
            self.assertTrue(self.db_manager.is_chapter_processed(chapter_num))
        
        # Verify character progression
        luffy = self.db_manager.get_character('/wiki/Monkey_D._Luffy')
        self.assertIsNotNone(luffy)
        
        # Luffy should have gained value from chapters 1 and 2
        luffy_history = self.db_manager.get_character_history('/wiki/Monkey_D._Luffy')
        self.assertGreaterEqual(len(luffy_history), 1)  # At least one change
        
        # Zoro should exist and have value from chapter 3
        zoro = self.db_manager.get_character('/wiki/Roronoa_Zoro')
        self.assertIsNotNone(zoro)
        
        # Verify market context evolution
        final_market_context = self.db_manager.get_current_market_context()
        self.assertGreater(final_market_context.total_characters, 0)
        self.assertGreater(len(final_market_context.recent_changes), 0)
    
    def test_character_value_progression_validation(self):
        """Test that character values progress realistically"""
        mock_crawler = self.create_mock_crawler()
        mock_llm = self.create_mock_llm_analyzer()
        
        # Process first chapter
        chapter_1_data = mock_crawler.scrape_chapter_page("https://onepiece.fandom.com/wiki/Chapter_1")
        
        # Get initial character values
        chapter_character_values = []
        for char in chapter_1_data['characters']:
            chapter_character_values.append({
                'name': char['name'],
                'wiki_url': char['wiki_url'],
                'current_value': None,
                'exists_in_db': False,
                'recent_activity': []
            })
        
        # Analyze and process
        analysis_1 = mock_llm.analyze_chapter(
            chapter_1_data,
            chapter_character_values,
            {'total_characters': 0, 'top_characters': [], 'bottom_characters': [], 'recent_changes': []}
        )
        
        self.db_manager.process_character_changes(1, [], analysis_1.new_characters)
        self.db_manager.add_chapter(1, chapter_1_data['title'], '')
        self.db_manager.mark_chapter_processed(1)
        
        # Get Luffy's initial value
        luffy_initial = self.db_manager.get_character('/wiki/Monkey_D._Luffy')
        initial_value = luffy_initial.current_value
        
        # Process second chapter
        chapter_2_data = mock_crawler.scrape_chapter_page("https://onepiece.fandom.com/wiki/Chapter_2")
        
        # Get updated character values
        chapter_character_values = []
        for char in chapter_2_data['characters']:
            current_value = self.db_manager.get_character_current_value(char['wiki_url'])
            recent_activity = self.db_manager.get_character_recent_activity(char['wiki_url'], 5)
            chapter_character_values.append({
                'name': char['name'],
                'wiki_url': char['wiki_url'],
                'current_value': current_value,
                'exists_in_db': current_value is not None,
                'recent_activity': recent_activity
            })
        
        market_context = self.db_manager.get_current_market_context()
        
        analysis_2 = mock_llm.analyze_chapter(
            chapter_2_data,
            chapter_character_values,
            {
                'total_characters': market_context.total_characters,
                'top_characters': market_context.top_characters,
                'bottom_characters': market_context.bottom_characters,
                'recent_changes': market_context.recent_changes
            }
        )
        
        # Process changes
        character_changes = [CharacterChange(
            wiki_url=change['wiki_url'],
            name=change['name'],
            value_change=change['value_change'],
            reasoning=change['reasoning']
        ) for change in analysis_2.character_changes]
        
        self.db_manager.process_character_changes(2, character_changes, analysis_2.new_characters)
        
        # Verify Luffy's value increased
        luffy_updated = self.db_manager.get_character('/wiki/Monkey_D._Luffy')
        self.assertGreater(luffy_updated.current_value, initial_value)
        
        # Verify history was recorded
        luffy_history = self.db_manager.get_character_history('/wiki/Monkey_D._Luffy')
        self.assertEqual(len(luffy_history), 1)
        self.assertEqual(luffy_history[0]['chapter_number'], 2)
        self.assertGreater(luffy_history[0]['value_change'], 0)
    
    def test_market_dynamics_evolution(self):
        """Test that market dynamics evolve correctly over time"""
        mock_crawler = self.create_mock_crawler()
        mock_llm = self.create_mock_llm_analyzer()
        
        # Track market dynamics over multiple chapters
        market_snapshots = []
        
        for i in range(1, 4):
            chapter_url = f"https://onepiece.fandom.com/wiki/Chapter_{i}"
            chapter_data = mock_crawler.scrape_chapter_page(chapter_url)
            
            # Get current market state
            market_context = self.db_manager.get_current_market_context()
            market_snapshots.append({
                'chapter': i,
                'total_characters': market_context.total_characters,
                'top_characters': len(market_context.top_characters),
                'recent_changes': len(market_context.recent_changes)
            })
            
            # Process chapter
            chapter_character_values = []
            for char in chapter_data['characters']:
                current_value = self.db_manager.get_character_current_value(char['wiki_url'])
                recent_activity = self.db_manager.get_character_recent_activity(char['wiki_url'], 5)
                chapter_character_values.append({
                    'name': char['name'],
                    'wiki_url': char['wiki_url'],
                    'current_value': current_value,
                    'exists_in_db': current_value is not None,
                    'recent_activity': recent_activity
                })
            
            analysis_result = mock_llm.analyze_chapter(
                chapter_data,
                chapter_character_values,
                {
                    'total_characters': market_context.total_characters,
                    'top_characters': market_context.top_characters,
                    'bottom_characters': market_context.bottom_characters,
                    'recent_changes': market_context.recent_changes
                }
            )
            
            character_changes = [CharacterChange(
                wiki_url=change['wiki_url'],
                name=change['name'],
                value_change=change['value_change'],
                reasoning=change['reasoning']
            ) for change in analysis_result.character_changes]
            
            self.db_manager.process_character_changes(i, character_changes, analysis_result.new_characters)
            self.db_manager.add_chapter(i, chapter_data['title'], '')
            self.db_manager.mark_chapter_processed(i)
        
        # Verify market growth
        self.assertEqual(market_snapshots[0]['total_characters'], 0)  # Chapter 1 starts empty
        self.assertGreater(market_snapshots[1]['total_characters'], 0)  # Chapter 2 has characters
        self.assertGreaterEqual(market_snapshots[2]['total_characters'], market_snapshots[1]['total_characters'])  # Chapter 3 maintains or grows
        
        # Verify recent changes tracking
        final_market = self.db_manager.get_current_market_context()
        self.assertGreater(len(final_market.recent_changes), 0)
    
    def test_data_consistency_validation(self):
        """Test data consistency and validation throughout processing"""
        mock_crawler = self.create_mock_crawler()
        mock_llm = self.create_mock_llm_analyzer()
        
        # Process all sample chapters
        for i in range(1, 4):
            chapter_url = f"https://onepiece.fandom.com/wiki/Chapter_{i}"
            chapter_data = mock_crawler.scrape_chapter_page(chapter_url)
            
            chapter_character_values = []
            for char in chapter_data['characters']:
                current_value = self.db_manager.get_character_current_value(char['wiki_url'])
                recent_activity = self.db_manager.get_character_recent_activity(char['wiki_url'], 5)
                chapter_character_values.append({
                    'name': char['name'],
                    'wiki_url': char['wiki_url'],
                    'current_value': current_value,
                    'exists_in_db': current_value is not None,
                    'recent_activity': recent_activity
                })
            
            market_context = self.db_manager.get_current_market_context()
            
            analysis_result = mock_llm.analyze_chapter(
                chapter_data,
                chapter_character_values,
                {
                    'total_characters': market_context.total_characters,
                    'top_characters': market_context.top_characters,
                    'bottom_characters': market_context.bottom_characters,
                    'recent_changes': market_context.recent_changes
                }
            )
            
            character_changes = [CharacterChange(
                wiki_url=change['wiki_url'],
                name=change['name'],
                value_change=change['value_change'],
                reasoning=change['reasoning']
            ) for change in analysis_result.character_changes]
            
            self.db_manager.process_character_changes(i, character_changes, analysis_result.new_characters)
            self.db_manager.add_chapter(i, chapter_data['title'], '')
            self.db_manager.mark_chapter_processed(i)
            
            # Validate database integrity after each chapter
            integrity = self.db_manager.validate_database_integrity()
            self.assertTrue(all(integrity.values()), f"Database integrity failed after Chapter {i}: {integrity}")
        
        # Final consistency checks
        all_characters = self.db_manager.get_all_characters()
        
        # Check that all characters have valid values
        for character in all_characters:
            self.assertGreater(character.current_value, 0)
            self.assertLessEqual(character.current_value, 1000)
            self.assertGreater(character.first_appearance, 0)
            self.assertLessEqual(character.first_appearance, 3)
        
        # Check that character histories are consistent
        for character in all_characters:
            history = self.db_manager.get_character_history(character.wiki_url)
            if history:
                # Last history entry should match current value
                last_entry = history[0]  # Most recent (DESC order)
                self.assertEqual(last_entry['new_value'], character.current_value)
        
        # Check market context consistency
        market_context = self.db_manager.get_current_market_context()
        self.assertEqual(market_context.total_characters, len(all_characters))
        
        # Check that top characters are actually the highest valued
        if market_context.top_characters:
            top_values = [char['current_value'] for char in market_context.top_characters]
            self.assertEqual(top_values, sorted(top_values, reverse=True))

def run_comprehensive_tests():
    """Run all comprehensive integration tests"""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestBatchProcessingIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    print("Running Comprehensive Integration Tests...")
    success = run_comprehensive_tests()
    
    if success:
        print("\n✓ All comprehensive integration tests passed!")
        print("✓ Single chapter processing workflow validated")
        print("✓ Sequential chapter processing validated")
        print("✓ Character value progression validated")
        print("✓ Market dynamics evolution validated")
        print("✓ Data consistency validation passed")
    else:
        print("\n✗ Some comprehensive integration tests failed!")
    
    exit(0 if success else 1)