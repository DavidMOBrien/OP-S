#!/usr/bin/env python3
"""
One Piece Character Tracker - Main Processing Workflow
Combines chronological wiki crawling, market-aware LLM analysis, and database storage
"""

import os
import sys
import argparse
import logging
import time
import json
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from pathlib import Path

class ProgressTracker:
    """Tracks processing progress and enables resumable processing"""
    
    def __init__(self, progress_file: str = "processing_progress.json"):
        self.progress_file = Path(progress_file)
        self.progress_data = self._load_progress()
        
    def _load_progress(self) -> Dict:
        """Load existing progress data"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            'last_processed_chapter': 0,
            'total_chapters_processed': 0,
            'processing_sessions': [],
            'failed_chapters': [],
            'market_snapshots': {}
        }
    
    def save_progress(self):
        """Save current progress to file"""
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(self.progress_data, f, indent=2)
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to save progress: {e}")
    
    def update_chapter_processed(self, chapter_number: int, success: bool = True):
        """Update progress after processing a chapter"""
        if success:
            self.progress_data['last_processed_chapter'] = max(
                self.progress_data['last_processed_chapter'], chapter_number
            )
            self.progress_data['total_chapters_processed'] += 1
            
            # Remove from failed chapters if it was there
            if chapter_number in self.progress_data['failed_chapters']:
                self.progress_data['failed_chapters'].remove(chapter_number)
        else:
            if chapter_number not in self.progress_data['failed_chapters']:
                self.progress_data['failed_chapters'].append(chapter_number)
        
        self.save_progress() 
   
    def start_session(self, start_chapter: int, end_chapter: Optional[int] = None):
        """Start a new processing session"""
        session = {
            'start_time': datetime.now().isoformat(),
            'start_chapter': start_chapter,
            'end_chapter': end_chapter,
            'chapters_processed': 0,
            'session_id': len(self.progress_data['processing_sessions'])
        }
        self.progress_data['processing_sessions'].append(session)
        self.save_progress()
        return session['session_id']
    
    def end_session(self, session_id: int, chapters_processed: int):
        """End a processing session"""
        if session_id < len(self.progress_data['processing_sessions']):
            session = self.progress_data['processing_sessions'][session_id]
            session['end_time'] = datetime.now().isoformat()
            session['chapters_processed'] = chapters_processed
            self.save_progress()
    
    def get_resume_chapter(self) -> int:
        """Get the chapter number to resume from"""
        return self.progress_data['last_processed_chapter'] + 1
    
    def should_skip_chapter(self, chapter_number: int) -> bool:
        """Check if a chapter should be skipped (already processed)"""
        return chapter_number <= self.progress_data['last_processed_chapter']

class MarketValidator:
    """Validates market consistency and character value progression"""
    
    def __init__(self, db_manager, character_manager):
        self.db = db_manager
        self.char_manager = character_manager
        self.logger = logging.getLogger(__name__)
    
    def validate_market_consistency(self, chapter_number: int) -> Dict[str, bool]:
        """Validate market consistency after processing a chapter"""
        validation_results = {
            'value_distribution_reasonable': True,
            'no_extreme_outliers': True,
            'tier_progression_logical': True,
            'recent_volatility_acceptable': True
        }
        
        try:
            # Get market dynamics
            market_dynamics = self.char_manager.calculate_market_dynamics()
            
            # Check value distribution
            total_chars = sum(market_dynamics.value_distribution.values())
            if total_chars > 0:
                # Check if too many characters are in extreme ranges
                extreme_high = market_dynamics.value_distribution.get('901-1000', 0)
                extreme_low = market_dynamics.value_distribution.get('0-50', 0)
                
                if extreme_high / total_chars > 0.1:  # More than 10% in legendary tier
                    validation_results['value_distribution_reasonable'] = False
                    self.logger.warning(f"Too many characters in legendary tier: {extreme_high}/{total_chars}")
                
                if extreme_low / total_chars > 0.3:  # More than 30% in weak tier
                    validation_results['value_distribution_reasonable'] = False
                    self.logger.warning(f"Too many characters in weak tier: {extreme_low}/{total_chars}")
            
            # Check for extreme outliers
            all_characters = self.db.get_all_characters()
            if all_characters:
                values = [char.current_value for char in all_characters]
                avg_value = sum(values) / len(values)
                
                for char in all_characters:
                    if char.current_value > avg_value * 5:  # 5x average is extreme
                        validation_results['no_extreme_outliers'] = False
                        self.logger.warning(f"Extreme outlier detected: {char.name} with value {char.current_value}")
                        break
            
            # Check recent volatility
            if market_dynamics.recent_volatility > 50:  # Average change > 50 points
                validation_results['recent_volatility_acceptable'] = False
                self.logger.warning(f"High market volatility: {market_dynamics.recent_volatility}")
            
            # Log validation summary
            passed_checks = sum(validation_results.values())
            total_checks = len(validation_results)
            self.logger.info(f"Market validation: {passed_checks}/{total_checks} checks passed")
            
        except Exception as e:
            self.logger.error(f"Error during market validation: {e}")
            # Set all validations to False on error
            validation_results = {key: False for key in validation_results}
        
        return validation_results 
   
    def log_market_changes(self, chapter_number: int, character_changes: List, new_characters: List):
        """Log comprehensive market changes for a chapter"""
        try:
            self.logger.info(f"=== MARKET CHANGES - CHAPTER {chapter_number} ===")
            
            if character_changes:
                self.logger.info(f"Character Value Changes ({len(character_changes)}):")
                for change in character_changes:
                    self.logger.info(f"  {change['name']}: {change['value_change']:+d} ({change['reasoning']})")
            
            if new_characters:
                self.logger.info(f"New Character Introductions ({len(new_characters)}):")
                for new_char in new_characters:
                    self.logger.info(f"  {new_char['name']}: {new_char['starting_value']} ({new_char['reasoning']})")
            
            # Get current market state
            market_context = self.db.get_current_market_context()
            self.logger.info(f"Market State: {market_context.total_characters} total characters")
            
            if market_context.top_characters:
                top_char = market_context.top_characters[0]
                self.logger.info(f"Market Leader: {top_char['name']} ({top_char['current_value']})")
            
            if market_context.recent_changes:
                recent_volatility = sum(abs(change['change']) for change in market_context.recent_changes[-5:])
                self.logger.info(f"Recent Market Volatility: {recent_volatility} points")
            
            self.logger.info("=" * 50)
            
        except Exception as e:
            self.logger.error(f"Error logging market changes: {e}")

def setup_comprehensive_logging(log_level: str = "INFO") -> logging.Logger:
    """Set up comprehensive logging with multiple handlers"""
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # Main log file
            logging.FileHandler(log_dir / 'one_piece_tracker.log'),
            # Market changes log
            logging.FileHandler(log_dir / 'market_changes.log'),
            # Console output
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Create specialized loggers
    market_logger = logging.getLogger('market_changes')
    market_handler = logging.FileHandler(log_dir / 'market_changes.log')
    market_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    market_logger.addHandler(market_handler)
    market_logger.setLevel(logging.INFO)
    
    progress_logger = logging.getLogger('progress')
    progress_handler = logging.FileHandler(log_dir / 'processing_progress.log')
    progress_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    progress_logger.addHandler(progress_handler)
    progress_logger.setLevel(logging.INFO)
    
    return logging.getLogger(__name__)

def load_environment_with_key():
    """Load environment variables and set the provided OpenAI API key"""
    # Set the provided API key directly as api_key
    os.environ['OPENAI_API_KEY'] = api_key
    
    # Also try to load from .env file for other settings
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # dotenv not available, continue with environment variables
    
    return api_key
def
 get_chapter_character_values(db_manager, chapter_characters, character_manager):
    """Get current values and recent activity for characters in a chapter"""
    logger = logging.getLogger(__name__)
    character_values = []
    
    # Check for duplicates
    duplicates = character_manager.identify_character_duplicates(chapter_characters)
    if duplicates:
        logger.warning(f"Found {len(duplicates)} potential duplicate groups in chapter characters")
    
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

def build_market_context(db_manager, chapter_number: int) -> Dict:
    """Build comprehensive market context before chapter analysis"""
    logger = logging.getLogger(__name__)
    
    try:
        # Get current market context
        market_context = db_manager.get_current_market_context()
        
        # Convert to dictionary format for LLM
        market_context_dict = {
            'total_characters': market_context.total_characters,
            'top_characters': market_context.top_characters,
            'bottom_characters': market_context.bottom_characters,
            'recent_changes': market_context.recent_changes
        }
        
        logger.info(f"Built market context for Chapter {chapter_number}: "
                   f"{market_context.total_characters} characters, "
                   f"{len(market_context.recent_changes)} recent changes")
        
        return market_context_dict
        
    except Exception as e:
        logger.error(f"Error building market context: {e}")
        return {
            'total_characters': 0,
            'top_characters': [],
            'bottom_characters': [],
            'recent_changes': []
        }

def process_character_changes_with_validation(db_manager, character_manager, chapter_number, 
                                            character_changes, new_characters):
    """Process character changes with validation through character manager"""
    logger = logging.getLogger(__name__)
    
    try:
        from database import CharacterChange
        
        # Convert to CharacterChange objects
        change_objects = [CharacterChange(
            wiki_url=change['wiki_url'],
            name=change['name'],
            value_change=change['value_change'],
            reasoning=change['reasoning']
        ) for change in character_changes]
        
        validated_changes = []
        validated_new_characters = []
        
        # Validate character changes
        for change in change_objects:
            validation = character_manager.validate_value_change(
                change.wiki_url, change.value_change, change.reasoning, chapter_number
            )
            
            if validation.is_valid:
                # Use adjusted change if different
                if validation.adjusted_change != change.value_change:
                    logger.info(f"Adjusted {change.name} change from {change.value_change} to {validation.adjusted_change}")
                    change.value_change = validation.adjusted_change
                
                validated_changes.append(change)
                
                if validation.validation_notes:
                    logger.info(f"Validation notes for {change.name}: {validation.validation_notes}")
            else:
                logger.warning(f"Rejected change for {change.name}: {validation.validation_notes}")
        
        # Process new characters with starting value calculation
        market_context = db_manager.get_current_market_context()
        market_context_dict = {
            'total_characters': market_context.total_characters,
            'top_characters': market_context.top_characters,
            'bottom_characters': market_context.bottom_characters,
            'recent_changes': market_context.recent_changes
        }
        
        for new_char in new_characters:
            # Calculate appropriate starting value
            introduction = character_manager.calculate_starting_value(
                new_char, chapter_number, market_context_dict
            )
            
            # Update the new character data with calculated values
            new_char['starting_value'] = introduction.starting_value
            new_char['reasoning'] = introduction.reasoning
            
            validated_new_characters.append(new_char)
            logger.info(f"Calculated starting value for {new_char['name']}: {introduction.starting_value}")
        
        # Process the validated changes
        success = db_manager.process_character_changes(
            chapter_number, validated_changes, validated_new_characters
        )
        
        if success:
            # Maintain character histories and market snapshots
            character_manager.maintain_character_histories(chapter_number)
            
            # Update market dynamics
            market_dynamics = character_manager.calculate_market_dynamics()
            character_manager.update_tier_thresholds(market_dynamics)
            
            logger.info(f"Market dynamics updated - Average: {market_dynamics.average_value:.1f}, "
                       f"Volatility: {market_dynamics.recent_volatility:.1f}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error processing character changes: {e}")
        return Falsedef p
rocess_single_chapter(chapter_url: str, crawler, db_manager, character_manager, 
                          llm_analyzer, progress_tracker, market_validator) -> bool:
    """Process a single chapter with full market context and validation"""
    logger = logging.getLogger(__name__)
    
    try:
        # Scrape chapter data
        logger.info(f"Scraping chapter: {chapter_url}")
        chapter_data = crawler.scrape_chapter_page(chapter_url)
        
        if not chapter_data:
            logger.error(f"Failed to scrape chapter data from {chapter_url}")
            return False
        
        chapter_number = chapter_data['number']
        
        # Check if already processed
        if progress_tracker.should_skip_chapter(chapter_number):
            logger.info(f"Chapter {chapter_number} already processed, skipping")
            return True
        
        # Add chapter to database
        db_manager.add_chapter(chapter_number, chapter_data['title'], chapter_url)
        
        # Build market context before analysis
        market_context = build_market_context(db_manager, chapter_number)
        
        # Get character values for this chapter
        chapter_character_values = get_chapter_character_values(
            db_manager, chapter_data['characters'], character_manager
        )
        
        logger.info(f"Processing Chapter {chapter_number}: {chapter_data['title']}")
        logger.info(f"Found {len(chapter_data['characters'])} characters in chapter")
        
        # Analyze with LLM
        analysis_result = llm_analyzer.analyze_chapter(
            chapter_data, chapter_character_values, market_context
        )
        
        if not analysis_result:
            logger.error(f"LLM analysis failed for Chapter {chapter_number}")
            progress_tracker.update_chapter_processed(chapter_number, success=False)
            return False
        
        # Process character changes with validation
        success = process_character_changes_with_validation(
            db_manager, character_manager, chapter_number,
            analysis_result.character_changes, analysis_result.new_characters
        )
        
        if success:
            # Log market changes
            market_validator.log_market_changes(
                chapter_number, analysis_result.character_changes, analysis_result.new_characters
            )
            
            # Validate market consistency
            validation_results = market_validator.validate_market_consistency(chapter_number)
            
            # Mark chapter as processed
            db_manager.mark_chapter_processed(chapter_number)
            progress_tracker.update_chapter_processed(chapter_number, success=True)
            
            logger.info(f"✓ Successfully processed Chapter {chapter_number}")
            return True
        else:
            logger.error(f"Failed to process character changes for Chapter {chapter_number}")
            progress_tracker.update_chapter_processed(chapter_number, success=False)
            return False
            
    except Exception as e:
        logger.error(f"Error processing chapter {chapter_url}: {e}")
        if 'chapter_number' in locals():
            progress_tracker.update_chapter_processed(chapter_number, success=False)
        return False

def create_argument_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser"""
    parser = argparse.ArgumentParser(
        description="One Piece Character Tracker - Main Processing Workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --start-chapter 1 --max-chapters 10    # Process chapters 1-10
  python main.py --resume                               # Resume from last processed chapter
  python main.py --validate-market                     # Validate current market state
  python main.py --chapter-range 50 100               # Process chapters 50-100
  python main.py --test-single 95                     # Test processing single chapter 95
        """
    )
    
    parser.add_argument('--start-chapter', type=int, default=1,
                       help='Chapter number to start processing from (default: 1)')
    
    parser.add_argument('--max-chapters', type=int,
                       help='Maximum number of chapters to process')
    
    parser.add_argument('--chapter-range', nargs=2, type=int, metavar=('START', 'END'),
                       help='Process chapters in specified range (inclusive)')
    
    parser.add_argument('--resume', action='store_true',
                       help='Resume processing from last processed chapter')
    
    parser.add_argument('--test-single', type=int, metavar='CHAPTER',
                       help='Test processing a single chapter')
    
    parser.add_argument('--validate-market', action='store_true',
                       help='Validate current market state and consistency')
    
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Set logging level (default: INFO)')
    
    parser.add_argument('--rate-limit', type=float, default=1.0,
                       help='Rate limit delay between requests in seconds (default: 1.0)')
    
    parser.add_argument('--dry-run', action='store_true',
                       help='Perform dry run without making changes to database')
    
    return parserdef 
main():
    """Main processing workflow entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_comprehensive_logging(args.log_level)
    logger.info("=" * 60)
    logger.info("One Piece Character Tracker - Main Processing Workflow")
    logger.info("=" * 60)
    
    try:
        # Load environment and API key
        api_key = load_environment_with_key()
        logger.info("Environment loaded with provided OpenAI API key")
        
        # Import required modules
        from wiki_crawler import WikiCrawler
        from database import DatabaseManager
        from llm_analyzer import LLMAnalyzer, LLMConfig
        from character_manager import CharacterManager
        
        # Initialize components
        logger.info("Initializing system components...")
        
        db_manager = DatabaseManager()
        logger.info("✓ Database initialized")
        
        character_manager = CharacterManager(db_manager)
        logger.info("✓ Character Manager initialized")
        
        crawler = WikiCrawler(rate_limit=args.rate_limit)
        logger.info(f"✓ Wiki Crawler initialized (rate limit: {args.rate_limit}s)")
        
        # Initialize LLM analyzer with provided API key
        config = LLMConfig(
            model="gpt-4",
            temperature=0.3,
            max_tokens=2000,
            max_retries=3
        )
        llm_analyzer = LLMAnalyzer(api_key=api_key, config=config)
        logger.info("✓ LLM Analyzer initialized")
        
        # Initialize progress tracker and market validator
        progress_tracker = ProgressTracker()
        market_validator = MarketValidator(db_manager, character_manager)
        logger.info("✓ Progress Tracker and Market Validator initialized")
        
        # Handle different command modes
        if args.validate_market:
            logger.info("Validating current market state...")
            validation_results = market_validator.validate_market_consistency(0)
            logger.info(f"Market validation results: {validation_results}")
            return
        
        if args.test_single:
            logger.info(f"Testing single chapter processing: Chapter {args.test_single}")
            chapter_url = f"https://onepiece.fandom.com/wiki/Chapter_{args.test_single}"
            success = process_single_chapter(
                chapter_url, crawler, db_manager, character_manager,
                llm_analyzer, progress_tracker, market_validator
            )
            logger.info(f"Single chapter test {'succeeded' if success else 'failed'}")
            return
        
        # Determine processing range
        if args.resume:
            start_chapter = progress_tracker.get_resume_chapter()
            logger.info(f"Resuming from Chapter {start_chapter}")
        elif args.chapter_range:
            start_chapter, end_chapter = args.chapter_range
            args.max_chapters = end_chapter - start_chapter + 1
            logger.info(f"Processing chapters {start_chapter} to {end_chapter}")
        else:
            start_chapter = args.start_chapter
            logger.info(f"Starting from Chapter {start_chapter}")
        
        # Start processing session
        session_id = progress_tracker.start_session(start_chapter, args.max_chapters)
        logger.info(f"Started processing session {session_id}")
        
        # Main processing loop
        current_chapter = start_chapter
        chapters_processed = 0
        consecutive_failures = 0
        max_consecutive_failures = 5
        
        try:
            while args.max_chapters is None or chapters_processed < args.max_chapters:
                chapter_url = f"https://onepiece.fandom.com/wiki/Chapter_{current_chapter}"
                
                logger.info(f"Processing Chapter {current_chapter} ({chapters_processed + 1}/{args.max_chapters or '∞'})")
                
                if args.dry_run:
                    logger.info(f"DRY RUN: Would process {chapter_url}")
                    success = True
                else:
                    success = process_single_chapter(
                        chapter_url, crawler, db_manager, character_manager,
                        llm_analyzer, progress_tracker, market_validator
                    )
                
                if success:
                    chapters_processed += 1
                    consecutive_failures = 0
                    logger.info(f"Progress: {chapters_processed} chapters processed successfully")
                else:
                    consecutive_failures += 1
                    logger.warning(f"Chapter {current_chapter} failed (consecutive failures: {consecutive_failures})")
                    
                    if consecutive_failures >= max_consecutive_failures:
                        logger.error(f"Too many consecutive failures ({consecutive_failures}), stopping")
                        break
                
                current_chapter += 1
                
                # Add delay between chapters to be respectful to the wiki
                if not args.dry_run:
                    time.sleep(args.rate_limit)
        
        except KeyboardInterrupt:
            logger.info("Processing interrupted by user")
        
        finally:
            # End processing session
            progress_tracker.end_session(session_id, chapters_processed)
            logger.info(f"Processing session {session_id} completed")
            logger.info(f"Total chapters processed: {chapters_processed}")
            
            # Final market validation
            if chapters_processed > 0:
                logger.info("Performing final market validation...")
                final_validation = market_validator.validate_market_consistency(current_chapter - 1)
                logger.info(f"Final market validation: {final_validation}")
        
        logger.info("=" * 60)
        logger.info("Main processing workflow completed")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Fatal error in main workflow: {e}")
        raise

if __name__ == "__main__":
    main()