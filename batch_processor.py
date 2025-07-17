#!/usr/bin/env python3
"""
Batch Processor for One Piece Character Tracker
Processes chapters sequentially with error recovery and comprehensive logging
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from wiki_crawler import WikiCrawler
from database import DatabaseManager, CharacterChange
from llm_analyzer import LLMAnalyzer, LLMConfig

class BatchProcessor:
    """Processes One Piece chapters in batch with error recovery"""
    
    def __init__(self, 
                 start_chapter: int = 1,
                 end_chapter: Optional[int] = None,
                 rate_limit: float = 2.0,
                 log_dir: str = "batch_logs"):
        """Initialize the batch processor"""
        
        # Setup logging
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup batch-specific logging
        log_file = self.log_dir / f"batch_processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.start_chapter = start_chapter
        self.end_chapter = end_chapter
        self.rate_limit = rate_limit
        
        # Progress tracking
        self.progress_file = self.log_dir / "progress.json"
        self.error_log_file = self.log_dir / "errors.json"
        
        self.logger.info(f"Batch processor initialized: chapters {start_chapter} to {end_chapter or 'end'}")
        self.logger.info(f"Logs will be saved to: {self.log_dir.absolute()}")
    
    def load_environment(self):
        """Load and validate environment variables"""
        load_dotenv()
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found. Please set it in your .env file.")
        
        self.logger.info("Environment variables loaded successfully")
        return api_key
    
    def initialize_components(self, api_key: str):
        """Initialize all processing components with error checking"""
        try:
            # Database
            self.db_manager = DatabaseManager()
            
            # Validate database integrity
            integrity = self.db_manager.validate_database_integrity()
            if not all(integrity.values()):
                failed_checks = [k for k, v in integrity.items() if not v]
                raise RuntimeError(f"Database integrity check failed: {failed_checks}")
            
            self.logger.info("✓ Database initialized and validated")
            
            # Wiki crawler
            self.crawler = WikiCrawler(rate_limit=self.rate_limit)
            self.logger.info("✓ Wiki crawler initialized")
            
            # LLM analyzer
            config = LLMConfig(
                model="gpt-4",
                temperature=0.3,
                max_tokens=3000,  # Increased for longer summaries
                max_retries=3
            )
            self.llm_analyzer = LLMAnalyzer(api_key=api_key, config=config, log_dir=str(self.log_dir / "llm_logs"))
            self.logger.info("✓ LLM analyzer initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise
    
    def get_last_successful_chapter(self) -> int:
        """Get the last successfully processed chapter for recovery"""
        try:
            if self.progress_file.exists():
                with open(self.progress_file, 'r') as f:
                    progress = json.load(f)
                    last_chapter = progress.get('last_successful_chapter', self.start_chapter - 1)
                    self.logger.info(f"Recovery: Last successful chapter was {last_chapter}")
                    return last_chapter
            else:
                self.logger.info("No previous progress found, starting from beginning")
                return self.start_chapter - 1
        except Exception as e:
            self.logger.warning(f"Could not read progress file: {e}")
            return self.start_chapter - 1
    
    def save_progress(self, chapter_num: int, status: str, error_msg: str = ""):
        """Save processing progress for recovery"""
        try:
            progress = {
                'last_attempted_chapter': chapter_num,
                'last_successful_chapter': chapter_num if status == 'success' else self.get_last_successful_chapter(),
                'timestamp': datetime.now().isoformat(),
                'status': status,
                'error': error_msg
            }
            
            with open(self.progress_file, 'w') as f:
                json.dump(progress, f, indent=2)
                
        except Exception as e:
            self.logger.warning(f"Could not save progress: {e}")
    
    def log_error(self, chapter_num: int, error_type: str, error_msg: str, details: Dict = None):
        """Log detailed error information"""
        try:
            error_entry = {
                'chapter': chapter_num,
                'timestamp': datetime.now().isoformat(),
                'error_type': error_type,
                'error_message': error_msg,
                'details': details or {}
            }
            
            # Load existing errors
            errors = []
            if self.error_log_file.exists():
                with open(self.error_log_file, 'r') as f:
                    errors = json.load(f)
            
            # Add new error
            errors.append(error_entry)
            
            # Save updated errors
            with open(self.error_log_file, 'w') as f:
                json.dump(errors, f, indent=2)
                
        except Exception as e:
            self.logger.warning(f"Could not log error: {e}")
    
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
    
    def process_single_chapter(self, chapter_num: int) -> bool:
        """Process a single chapter with comprehensive error handling"""
        self.logger.info(f"Processing Chapter {chapter_num}...")
        
        try:
            # Step 1: Check if already processed
            if self.db_manager.is_chapter_processed(chapter_num):
                self.logger.info(f"Chapter {chapter_num} already processed, skipping")
                return True
            
            # Step 2: Crawl chapter data
            chapter_url = f"https://onepiece.fandom.com/wiki/Chapter_{chapter_num}"
            chapter_data = self.crawler.scrape_chapter_page(chapter_url)
            
            if not chapter_data:
                error_msg = f"Failed to crawl chapter data for Chapter {chapter_num}"
                self.logger.error(error_msg)
                self.log_error(chapter_num, "CRAWL_FAILED", error_msg)
                return False
            
            # Validate chapter data
            if not chapter_data.get('summary') or len(chapter_data['summary']) < 50:
                error_msg = f"Chapter {chapter_num} has insufficient summary content: {len(chapter_data.get('summary', ''))}"
                self.logger.error(error_msg)
                self.log_error(chapter_num, "INSUFFICIENT_SUMMARY", error_msg, {
                    'summary_length': len(chapter_data.get('summary', '')),
                    'summary_preview': chapter_data.get('summary', '')[:100]
                })
                return False
            
            if not chapter_data.get('characters'):
                error_msg = f"Chapter {chapter_num} has no characters identified"
                self.logger.error(error_msg)
                self.log_error(chapter_num, "NO_CHARACTERS", error_msg)
                return False
            
            self.logger.info(f"✓ Crawled Chapter {chapter_num}: {chapter_data['title']}")
            self.logger.info(f"  Summary length: {len(chapter_data['summary'])} characters")
            self.logger.info(f"  Characters found: {len(chapter_data['characters'])}")
            
            # Step 3: Get character values and market context
            chapter_character_values = self.get_chapter_character_values(chapter_data['characters'])
            market_context = self.db_manager.get_current_market_context()
            market_context_dict = {
                'total_characters': market_context.total_characters,
                'top_characters': market_context.top_characters,
                'bottom_characters': market_context.bottom_characters,
                'recent_changes': market_context.recent_changes
            }
            
            # Step 4: Analyze with LLM
            analysis_result = self.llm_analyzer.analyze_chapter(
                chapter_data, chapter_character_values, market_context_dict
            )
            
            if not analysis_result:
                error_msg = f"LLM analysis failed for Chapter {chapter_num}"
                self.logger.error(error_msg)
                self.log_error(chapter_num, "LLM_ANALYSIS_FAILED", error_msg)
                return False
            
            self.logger.info(f"✓ LLM analysis completed for Chapter {chapter_num}")
            self.logger.info(f"  Character changes: {len(analysis_result.character_changes)}")
            self.logger.info(f"  New characters: {len(analysis_result.new_characters)}")
            
            # Step 5: Store results in database
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
                    error_msg = f"Failed to store character changes for Chapter {chapter_num}"
                    self.logger.error(error_msg)
                    self.log_error(chapter_num, "DATABASE_STORAGE_FAILED", error_msg)
                    return False
                
                self.logger.info(f"✓ Character changes stored for Chapter {chapter_num}")
            
            # Step 6: Mark chapter as processed
            self.db_manager.add_chapter(chapter_num, chapter_data['title'], chapter_data.get('wiki_url', ''))
            self.db_manager.mark_chapter_processed(chapter_num)
            
            self.logger.info(f"✓ Chapter {chapter_num} processing completed successfully")
            return True
            
        except Exception as e:
            error_msg = f"Unexpected error processing Chapter {chapter_num}: {e}"
            self.logger.error(error_msg)
            self.log_error(chapter_num, "UNEXPECTED_ERROR", error_msg, {'exception': str(e)})
            return False
    
    def run_batch_processing(self):
        """Run the complete batch processing workflow"""
        try:
            # Load environment and initialize components
            api_key = self.load_environment()
            self.initialize_components(api_key)
            
            # Determine starting point for recovery
            last_successful = self.get_last_successful_chapter()
            current_chapter = max(last_successful + 1, self.start_chapter)
            
            self.logger.info(f"Starting batch processing from Chapter {current_chapter}")
            
            # Process chapters sequentially
            processed_count = 0
            failed_count = 0
            
            while True:
                # Check if we've reached the end
                if self.end_chapter and current_chapter > self.end_chapter:
                    self.logger.info(f"Reached end chapter {self.end_chapter}")
                    break
                
                # Process the chapter
                success = self.process_single_chapter(current_chapter)
                
                if success:
                    processed_count += 1
                    self.save_progress(current_chapter, 'success')
                    self.logger.info(f"Progress: {processed_count} chapters processed successfully")
                else:
                    failed_count += 1
                    self.save_progress(current_chapter, 'failed', f"Chapter {current_chapter} processing failed")
                    self.logger.error(f"Chapter {current_chapter} failed. Total failures: {failed_count}")
                    
                    # STOP on any error as requested
                    self.logger.error("Stopping batch processing due to error")
                    break
                
                # Rate limiting between chapters
                if self.rate_limit > 0:
                    time.sleep(self.rate_limit)
                
                current_chapter += 1
            
            # Final summary
            self.logger.info("="*60)
            self.logger.info("BATCH PROCESSING SUMMARY")
            self.logger.info("="*60)
            self.logger.info(f"Chapters processed successfully: {processed_count}")
            self.logger.info(f"Chapters failed: {failed_count}")
            self.logger.info(f"Last successful chapter: {current_chapter - 1 if success else last_successful}")
            
            if failed_count > 0:
                self.logger.info(f"Error details saved to: {self.error_log_file}")
                self.logger.info("To resume processing, run the batch processor again")
            
        except Exception as e:
            self.logger.error(f"Batch processing failed: {e}")
            raise


def main():
    """Main entry point for batch processing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch process One Piece chapters')
    parser.add_argument('--start', type=int, default=1, help='Starting chapter number')
    parser.add_argument('--end', type=int, help='Ending chapter number (optional)')
    parser.add_argument('--rate-limit', type=float, default=2.0, help='Delay between chapters in seconds')
    parser.add_argument('--log-dir', default='batch_logs', help='Directory for logs')
    
    args = parser.parse_args()
    
    processor = BatchProcessor(
        start_chapter=args.start,
        end_chapter=args.end,
        rate_limit=args.rate_limit,
        log_dir=args.log_dir
    )
    
    processor.run_batch_processing()


if __name__ == "__main__":
    main()