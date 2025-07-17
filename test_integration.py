#!/usr/bin/env python3
"""
Integration test for the complete LLM workflow
Tests the full pipeline: wiki crawler -> database -> LLM analyzer -> database storage
"""

import logging
from database import DatabaseManager
from wiki_crawler import WikiCrawler
from llm_analyzer import LLMAnalyzer, LLMConfig, CharacterAnalysis

def setup_logging():
    """Configure logging for testing"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def get_chapter_character_values(db_manager, chapter_characters):
    """Get current values and recent activity for characters in a chapter"""
    character_values = []
    for char in chapter_characters:
        current_value = db_manager.get_character_current_value(char['wiki_url'])
        recent_activity = db_manager.get_character_recent_activity(char['wiki_url'], last_n_chapters=5)
        character_values.append({
            'name': char['name'],
            'wiki_url': char['wiki_url'],
            'current_value': current_value,
            'exists_in_db': current_value is not None,
            'recent_activity': recent_activity
        })
    return character_values

def test_complete_integration():
    """Test the complete integration without API calls"""
    logger = setup_logging()
    
    try:
        # Initialize components
        logger.info("Initializing components...")
        
        # Database
        db_manager = DatabaseManager("test_integration.db")
        logger.info("✓ Database initialized")
        
        # Wiki crawler
        crawler = WikiCrawler(rate_limit=0.5)
        logger.info("✓ Wiki crawler initialized")
        
        # Mock LLM analyzer (to avoid API calls)
        class MockLLMAnalyzer:
            def __init__(self, config):
                self.config = config
            
            def analyze_chapter(self, chapter_data, chapter_character_values, market_context):
                # Return realistic mock analysis
                character_changes = []
                new_characters = []
                
                # Process characters based on whether they exist in DB
                for char in chapter_character_values:
                    if char['exists_in_db']:
                        # Existing character - add a small change
                        character_changes.append({
                            'wiki_url': char['wiki_url'],
                            'name': char['name'],
                            'value_change': 10,
                            'reasoning': f"Character development moment for {char['name']} in this chapter"
                        })
                    else:
                        # New character - set starting value
                        new_characters.append({
                            'wiki_url': char['wiki_url'],
                            'name': char['name'],
                            'starting_value': 50,
                            'reasoning': f"Introduction of {char['name']} as new character"
                        })
                
                return CharacterAnalysis(
                    character_changes=character_changes[:3],  # Limit to 3 changes
                    new_characters=new_characters[:3],  # Limit to 3 new characters
                    analysis_reasoning="Mock analysis for integration testing"
                )
        
        config = LLMConfig(model="gpt-4", temperature=0.3)
        llm_analyzer = MockLLMAnalyzer(config)
        logger.info("✓ Mock LLM analyzer initialized")
        
        # Test the complete workflow
        logger.info("Testing complete workflow...")
        
        # Step 1: Crawl a chapter
        logger.info("Step 1: Crawling chapter data...")
        chapter_data = crawler.test_single_chapter()
        
        if not chapter_data:
            logger.error("✗ Failed to crawl chapter data")
            return False
        
        logger.info(f"✓ Crawled Chapter {chapter_data['number']}: {chapter_data['title']}")
        logger.info(f"  Found {len(chapter_data['characters'])} characters")
        
        # Step 2: Get character values from database
        logger.info("Step 2: Getting character values from database...")
        chapter_character_values = get_chapter_character_values(db_manager, chapter_data['characters'])
        
        existing_chars = sum(1 for char in chapter_character_values if char['exists_in_db'])
        new_chars = len(chapter_character_values) - existing_chars
        
        logger.info(f"✓ Character analysis: {existing_chars} existing, {new_chars} new")
        
        # Step 3: Get market context
        logger.info("Step 3: Getting market context...")
        market_context = db_manager.get_current_market_context()
        market_context_dict = {
            'total_characters': market_context.total_characters,
            'top_characters': market_context.top_characters,
            'bottom_characters': market_context.bottom_characters,
            'recent_changes': market_context.recent_changes
        }
        
        logger.info(f"✓ Market context: {market_context.total_characters} total characters")
        
        # Step 4: Analyze with LLM
        logger.info("Step 4: Analyzing with LLM...")
        analysis_result = llm_analyzer.analyze_chapter(
            chapter_data, chapter_character_values, market_context_dict
        )
        
        if not analysis_result:
            logger.error("✗ LLM analysis failed")
            return False
        
        logger.info(f"✓ LLM analysis completed:")
        logger.info(f"  Character changes: {len(analysis_result.character_changes)}")
        logger.info(f"  New characters: {len(analysis_result.new_characters)}")
        
        # Step 5: Store results in database
        logger.info("Step 5: Storing results in database...")
        
        # Convert analysis results to database format
        from database import CharacterChange
        character_changes = []
        for change in analysis_result.character_changes:
            character_changes.append(CharacterChange(
                wiki_url=change['wiki_url'],
                name=change['name'],
                value_change=change['value_change'],
                reasoning=change['reasoning']
            ))
        
        success = db_manager.process_character_changes(
            chapter_data['number'],
            character_changes,
            analysis_result.new_characters
        )
        
        if not success:
            logger.error("✗ Failed to store character changes")
            return False
        
        logger.info("✓ Character changes stored successfully")
        
        # Add chapter to database first, then mark as processed
        db_manager.add_chapter(chapter_data['number'], chapter_data['title'], chapter_data.get('wiki_url', ''))
        db_manager.mark_chapter_processed(chapter_data['number'])
        logger.info("✓ Chapter marked as processed")
        
        # Step 6: Verify data was stored correctly
        logger.info("Step 6: Verifying stored data...")
        
        # Check if characters were added
        all_characters = db_manager.get_all_characters()
        logger.info(f"✓ Total characters in database: {len(all_characters)}")
        
        # Check if chapter was marked as processed
        is_processed = db_manager.is_chapter_processed(chapter_data['number'])
        if is_processed:
            logger.info("✓ Chapter processing status verified")
        else:
            logger.error("✗ Chapter processing status incorrect")
            return False
        
        # Check market context after changes
        updated_market_context = db_manager.get_current_market_context()
        logger.info(f"✓ Updated market context: {updated_market_context.total_characters} characters")
        
        # Step 7: Test market context functionality
        logger.info("Step 7: Testing market context functionality...")
        
        if updated_market_context.total_characters > 0:
            top_chars = db_manager.get_top_characters(5)
            bottom_chars = db_manager.get_bottom_characters(5)
            recent_changes = db_manager.get_recent_character_changes(5)
            
            logger.info(f"✓ Top characters: {len(top_chars)}")
            logger.info(f"✓ Bottom characters: {len(bottom_chars)}")
            logger.info(f"✓ Recent changes: {len(recent_changes)}")
            
            if top_chars:
                logger.info(f"  Highest valued: {top_chars[0]['name']} ({top_chars[0]['current_value']})")
            if recent_changes:
                logger.info(f"  Latest change: {recent_changes[0]['character']} ({recent_changes[0]['change']:+d})")
        
        # Step 8: Test second chapter processing (to test existing character updates)
        logger.info("Step 8: Testing second chapter processing...")
        
        # Simulate processing the same chapter again (should update existing characters)
        analysis_result_2 = llm_analyzer.analyze_chapter(
            chapter_data, 
            get_chapter_character_values(db_manager, chapter_data['characters']),
            {
                'total_characters': updated_market_context.total_characters,
                'top_characters': updated_market_context.top_characters,
                'bottom_characters': updated_market_context.bottom_characters,
                'recent_changes': updated_market_context.recent_changes
            }
        )
        
        if analysis_result_2:
            logger.info("✓ Second analysis completed (testing existing character updates)")
            logger.info(f"  Character changes: {len(analysis_result_2.character_changes)}")
            logger.info(f"  New characters: {len(analysis_result_2.new_characters)}")
        
        logger.info("✓ Complete integration test passed!")
        return True
        
    except Exception as e:
        logger.error(f"Integration test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_complete_integration()
    if success:
        print("\n🎉 Complete integration test passed!")
        print("✓ Wiki crawler working")
        print("✓ Database operations working")
        print("✓ LLM analyzer structure working")
        print("✓ Market context system working")
        print("✓ Character value tracking working")
        print("✓ End-to-end workflow working")
    else:
        print("\n❌ Integration test failed!")
        exit(1)