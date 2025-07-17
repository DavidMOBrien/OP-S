#!/usr/bin/env python3
"""
Single Chapter Processor for One Piece Character Tracker
Processes chapters one at a time, maintaining market context dependencies
"""

import os
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv

from wiki_crawler import WikiCrawler
from database import DatabaseManager, CharacterChange
from llm_analyzer import LLMAnalyzer, LLMConfig

class ChapterProcessor:
    """Processes One Piece chapters individually with market context"""
    
    def __init__(self, rate_limit: float = 1.0):
        """Initialize the chapter processor"""
        self.rate_limit = rate_limit
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.db_manager = None
        self.crawler = None
        self.llm_analyzer = None
        
    def initialize(self):
        """Initialize all processing components"""
        # Load environment
        load_dotenv()
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found. Please set it in your .env file.")
        
        # Initialize components
        self.db_manager = DatabaseManager()
        self.crawler = WikiCrawler(rate_limit=self.rate_limit)
        
        config = LLMConfig(
            model="gpt-4",
            temperature=0.3,
            max_tokens=3000,
            max_retries=3
        )
        self.llm_analyzer = LLMAnalyzer(api_key=api_key, config=config)
        
        self.logger.info("Chapter processor initialized successfully")
    
    def get_chapter_character_values(self, chapter_characters):
        """Get current values and recent activity for characters in a chapter"""
        character_values = []
        for char in chapter_characters:
            current_value = self.db_manager.get_character_current_value(char['wiki_url'])
            recent_activity = self.db_manager.get_character_recent_activity(char['wiki_url'], last_n_chapters=5)
            character_values.append({
                'name': char['name'],
                'wiki_url': char['wiki_url'],
                'current_value': current_value,
                'exists_in_db': current_value is not None,
                'recent_activity': recent_activity
            })
        return character_values
    
    def process_chapter(self, chapter_num: int) -> bool:
        """
        Process a single chapter with full market context dependency
        
        IMPORTANT: This method relies on the current market state in the database.
        Chapters must be processed in sequential order to maintain proper market context.
        """
        if not self.db_manager or not self.crawler or not self.llm_analyzer:
            raise RuntimeError("Processor not initialized. Call initialize() first.")
        
        self.logger.info(f"Processing Chapter {chapter_num}...")
        
        # Check if already processed
        if self.db_manager.is_chapter_processed(chapter_num):
            self.logger.info(f"Chapter {chapter_num} already processed")
            return True
        
        # Step 1: Crawl chapter data
        chapter_url = f"https://onepiece.fandom.com/wiki/Chapter_{chapter_num}"
        chapter_data = self.crawler.scrape_chapter_page(chapter_url)
        
        if not chapter_data:
            self.logger.error(f"Failed to crawl Chapter {chapter_num}")
            return False
        
        self.logger.info(f"✓ Crawled Chapter {chapter_num}: {chapter_data['title']}")
        self.logger.info(f"  Summary length: {len(chapter_data['summary'])} characters")
        self.logger.info(f"  Characters found: {len(chapter_data['characters'])}")
        
        # Step 2: Get CURRENT market context (this is why order matters!)
        chapter_character_values = self.get_chapter_character_values(chapter_data['characters'])
        market_context = self.db_manager.get_current_market_context()
        market_context_dict = {
            'total_characters': market_context.total_characters,
            'top_characters': market_context.top_characters,
            'bottom_characters': market_context.bottom_characters,
            'recent_changes': market_context.recent_changes
        }
        
        self.logger.info(f"✓ Market context: {market_context.total_characters} characters in database")
        
        # Step 3: Analyze with LLM using current market state
        analysis_result = self.llm_analyzer.analyze_chapter(
            chapter_data, chapter_character_values, market_context_dict
        )
        
        if not analysis_result:
            self.logger.error(f"LLM analysis failed for Chapter {chapter_num}")
            return False
        
        self.logger.info(f"✓ LLM analysis completed")
        self.logger.info(f"  Character changes: {len(analysis_result.character_changes)}")
        self.logger.info(f"  New characters: {len(analysis_result.new_characters)}")
        
        # Step 4: Update database (this changes the market context for next chapter!)
        if analysis_result.character_changes or analysis_result.new_characters:
            character_changes = [CharacterChange(
                wiki_url=change['wiki_url'],
                name=change['name'],
                value_change=change['value_change'],
                reasoning=change['reasoning']
            ) for change in analysis_result.character_changes]
            
            success = self.db_manager.process_character_changes(
                chapter_num,
                character_changes,
                analysis_result.new_characters
            )
            
            if not success:
                self.logger.error(f"Failed to store changes for Chapter {chapter_num}")
                return False
            
            self.logger.info(f"✓ Character changes stored")
        
        # Step 5: Mark chapter as processed
        self.db_manager.add_chapter(chapter_num, chapter_data['title'], chapter_data.get('wiki_url', ''))
        self.db_manager.mark_chapter_processed(chapter_num)
        
        self.logger.info(f"✓ Chapter {chapter_num} processing completed successfully")
        return True
    
    def get_next_chapter_to_process(self) -> int:
        """Get the next chapter number that needs processing"""
        last_processed = self.db_manager.get_last_processed_chapter()
        return (last_processed or 0) + 1
    
    def process_next_chapter(self) -> bool:
        """Process the next chapter in sequence"""
        next_chapter = self.get_next_chapter_to_process()
        self.logger.info(f"Next chapter to process: {next_chapter}")
        return self.process_chapter(next_chapter)


def main():
    """Example usage of single chapter processing"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    processor = ChapterProcessor()
    processor.initialize()
    
    # Process next chapter in sequence
    success = processor.process_next_chapter()
    
    if success:
        print("✓ Chapter processed successfully!")
    else:
        print("✗ Chapter processing failed!")


if __name__ == "__main__":
    main()