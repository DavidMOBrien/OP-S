"""Main script for generating offline One Piece stock data."""

import argparse
import sys
from typing import List, Dict, Optional
from dotenv import load_dotenv
from database import Database
from wiki_crawler import WikiCrawler
from llm_analyzer import LLMAnalyzer

# Load environment variables from .env file
load_dotenv()


class DataGenerator:
    """Orchestrates the offline data generation process."""
    
    def __init__(self, db_path: str = "one_piece_stocks.db",
                 openai_api_key: Optional[str] = None,
                 openai_model: str = "gpt-5-nano-2025-08-07",
                 crawler_delay: float = 1.0,
                 verbose: bool = True):
        """
        Initialize the data generator.
        
        Args:
            db_path: Path to SQLite database
            openai_api_key: OpenAI API key
            openai_model: OpenAI model to use
            crawler_delay: Delay between wiki requests
            verbose: If True, print prompts and responses
        """
        self.db = Database(db_path)
        self.crawler = WikiCrawler(delay=crawler_delay)
        self.analyzer = LLMAnalyzer(api_key=openai_api_key, model=openai_model)
        self.verbose = verbose
        
    def initialize(self):
        """Initialize the database schema."""
        print("Initializing database...")
        with self.db as db:
            db.initialize_schema()
        print("Database initialized successfully")
        
    def build_market_context(self, chapter_id: int, 
                            characters_in_chapter: List[Dict]) -> Dict:
        """
        Build market context for LLM analysis.
        
        Args:
            chapter_id: Current chapter being processed
            characters_in_chapter: List of character dicts from wiki
            
        Returns:
            Market context dict
        """
        with self.db as db:
            # Get previous chapter for context
            prev_chapter = chapter_id - 1 if chapter_id > 1 else None
            
            # Get top 10 stocks
            top_ten = db.get_top_stocks(up_to_chapter=prev_chapter, limit=10)
            
            # Get market statistics
            stats = db.get_market_statistics(up_to_chapter=prev_chapter)
            
            # Categorize characters as existing or new
            existing_characters = []
            new_characters = []
            
            # Collect past 3 changes for characters in this chapter (for market context)
            chapter_character_history = []
            
            for char in characters_in_chapter:
                char_id = char['character_id']
                
                # Check if character appeared in PREVIOUS chapters (not just exists in DB)
                if prev_chapter and db.character_exists(char_id):
                    # Check if they have any history before this chapter
                    current_stock = db.calculate_current_stock(char_id, prev_chapter)
                    
                    # Only mark as existing if they have stock from previous chapters
                    if current_stock > 0:
                        recent_history = db.get_character_history(char_id, 
                                                                  up_to_chapter=prev_chapter,
                                                                  limit=3)
                        
                        existing_characters.append({
                            'character_id': char_id,
                            'name': char['name'],
                            'href': char['href'],
                            'current_stock': current_stock,
                            'recent_history': recent_history
                        })
                        
                        # Add to chapter character history for market context
                        if recent_history:
                            for event in recent_history[:3]:
                                stock_after = event.get('current_stock', 0)
                                delta = event.get('stock_change', 0)
                                description = event.get('description', '') or event.get('reasoning', '')
                                is_first_appearance = event.get('is_first_appearance', False)
                                
                                if stock_after > 0:
                                    if is_first_appearance and delta == 0:
                                        # First appearance - show as "new"
                                        chapter_character_history.append({
                                            'character_name': char['name'],
                                            'chapter_id': event['chapter_id'],
                                            'multiplier': None,  # Indicates new character
                                            'initial_value': stock_after,
                                            'reasoning': description
                                        })
                                    else:
                                        # Existing character (could be delta=0 for 1.00x multiplier)
                                        stock_before = stock_after - delta
                                        if stock_before > 0 and delta != 0:
                                            multiplier = stock_after / stock_before
                                        elif delta == 0:
                                            # delta==0 for existing means 1.00x multiplier (inactive/meeting expectations)
                                            multiplier = 1.00
                                        else:
                                            continue  # Skip invalid data
                                            
                                        chapter_character_history.append({
                                            'character_name': char['name'],
                                            'chapter_id': event['chapter_id'],
                                            'multiplier': multiplier,
                                            'reasoning': description
                                        })
                    else:
                        # No stock from previous chapters = new
                        new_characters.append({
                            'character_id': char_id,
                            'name': char['name'],
                            'href': char['href']
                        })
                else:
                    # New character
                    new_characters.append({
                        'character_id': char_id,
                        'name': char['name'],
                        'href': char['href']
                    })
                    
        return {
            'top_ten': top_ten,
            'statistics': stats,
            'existing_characters': existing_characters,
            'new_characters': new_characters,
            'chapter_character_history': chapter_character_history
        }
        
    def process_chapter(self, chapter_data: Dict) -> bool:
        """
        Process a single chapter.
        
        Args:
            chapter_data: Chapter data from crawler
            
        Returns:
            True if successful, False otherwise
        """
        chapter_id = chapter_data['chapter_id']
        
        print(f"\nProcessing Chapter {chapter_id}: {chapter_data['title']}")
        print(f"Arc: {chapter_data.get('arc_name', 'Unknown')}")
        print(f"Characters found: {len(chapter_data['characters'])}")
        
        # Check if already processed
        with self.db as db:
            if db.is_chapter_processed(chapter_id):
                print(f"Chapter {chapter_id} already processed, skipping...")
                return True
                
            # Save chapter to database
            db.save_chapter(
                chapter_id=chapter_id,
                title=chapter_data['title'],
                url=chapter_data['url'],
                raw_description=chapter_data['raw_description'],
                arc_name=chapter_data.get('arc_name')
            )
        
        # Build market context
        print("Building market context...")
        market_context = self.build_market_context(chapter_id, chapter_data['characters'])
        
        print(f"Existing characters: {len(market_context['existing_characters'])}")
        print(f"New characters: {len(market_context['new_characters'])}")
        
        # Analyze with LLM
        print("Analyzing with LLM...")
        try:
            stock_changes = self.analyzer.analyze_chapter(
                chapter_data, 
                market_context,
                verbose=self.verbose
            )
        except Exception as e:
            print(f"\n❌ CRITICAL ERROR: LLM analysis failed after all retries")
            print(f"Error: {e}")
            print(f"\n🛑 HALTING RUN - Chapter {chapter_id} could not be processed")
            raise  # Re-raise to halt the entire run
        
        if not stock_changes:
            print("⚠️  Warning: No stock changes returned from LLM")
            return False
            
        print(f"✅ Received {len(stock_changes)} stock change events")
        
        # Per-character analysis already validated, no need for batch validation
        validated_changes = stock_changes
        
        if self.verbose:
            print("\n" + "="*80)
            print("📊 VALIDATED STOCK CHANGES")
            print("="*80)
            for change in validated_changes:
                char_id = self.crawler.extract_character_id_from_href(change['character_href'])
                with self.db as db:
                    is_new = not db.character_exists(char_id)
                
                print(f"\n{change['character_name']}:")
                if is_new:
                    print(f"  Initial Stock Value: {change['stock_change']:.1f}")
                else:
                    print(f"  Final Multiplier: {change['stock_change']:.2f}x")
                    # Show action breakdown if available
                    if 'actions' in change and change['actions']:
                        print(f"  Actions breakdown:")
                        for i, action in enumerate(change['actions'], 1):
                            print(f"    {i}. {action['description']}")
                            print(f"       → {action['multiplier']:.2f}x")
                print(f"  Confidence: {change['confidence']:.2f}")
                print(f"  Reasoning: {change['reasoning']}")
            print("="*80 + "\n")
        
        # Save to database
        character_reasonings = {}  # Store chapter-level reasonings for update_stock_history
        
        with self.db as db:
            for change in validated_changes:
                # Extract character ID from href
                char_id = self.crawler.extract_character_id_from_href(change['character_href'])
                
                # Store the chapter-level reasoning for this character
                if 'reasoning' in change:
                    character_reasonings[char_id] = change['reasoning']
                
                # Check if this is a first appearance
                is_new = not db.character_exists(char_id)
                
                if is_new:
                    # For new characters, stock_change IS their initial value
                    initial_value = change['stock_change']
                    
                    # Skip characters with very low initial stock (likely insignificant background characters)
                    # They can be properly introduced later if they become important
                    if initial_value < 10:
                        if self.verbose:
                            print(f"  ⏭️  Skipping {change['character_name']} (stock {initial_value:.1f} too low, likely insignificant)")
                        continue
                        
                    db.save_character(
                        character_id=char_id,
                        canonical_name=change['character_name'],
                        href=change['character_href'],
                        first_appearance_chapter=chapter_id,
                        initial_stock_value=initial_value
                    )
                    print(f"  New character: {change['character_name']} starting at {initial_value:.1f}")
                    
                    # For new characters, save a market event with 0 change (initial value is stored separately)
                    db.save_market_event(
                        chapter_id=chapter_id,
                        character_id=char_id,
                        character_href=change['character_href'],
                        stock_change=0,  # Initial value is in the character record
                        confidence_score=change['confidence'],
                        description=change['reasoning'],
                        is_first_appearance=True
                    )
                else:
                    # For existing characters, stock_change is a MULTIPLIER
                    multiplier = change['stock_change']
                    
                    # Validate multiplier range (0.05 to 5.0)
                    if multiplier < 0.05 or multiplier > 5.0:
                        print(f"  WARNING: {change['character_name']} has invalid multiplier {multiplier:.2f}, clamping to valid range")
                        multiplier = max(0.05, min(5.0, multiplier))
                    
                    current_stock = db.calculate_current_stock(char_id, chapter_id - 1)
                    
                    # Save individual actions as market events
                    if 'actions' in change and change['actions']:
                        # Calculate per-action stock changes
                        running_stock = current_stock
                        STOCK_FLOOR = 10.0  # Minimum stock to prevent death spirals
                        
                        for action in change['actions']:
                            action_multiplier = action['multiplier']
                            new_stock = running_stock * action_multiplier
                            
                            # Enforce stock floor
                            if new_stock < STOCK_FLOOR:
                                new_stock = STOCK_FLOOR
                                if self.verbose:
                                    print(f"    ⚠️  {change['character_name']} hit stock floor: {new_stock:.1f}")
                            
                            action_delta = new_stock - running_stock
                            
                            db.save_market_event(
                                chapter_id=chapter_id,
                                character_id=char_id,
                                character_href=change['character_href'],
                                stock_change=action_delta,
                                confidence_score=change['confidence'],
                                description=action['description'],
                                is_first_appearance=False
                            )
                            
                            running_stock = new_stock
                    else:
                        # Fallback: no individual actions, save one event with total change
                        STOCK_FLOOR = 10.0  # Minimum stock to prevent death spirals
                        new_stock = current_stock * multiplier
                        
                        # Enforce stock floor
                        if new_stock < STOCK_FLOOR:
                            new_stock = STOCK_FLOOR
                            if self.verbose:
                                print(f"    ⚠️  {change['character_name']} hit stock floor: {new_stock:.1f}")
                        
                        delta = new_stock - current_stock
                        
                        db.save_market_event(
                            chapter_id=chapter_id,
                            character_id=char_id,
                            character_href=change['character_href'],
                            stock_change=delta,
                            confidence_score=change['confidence'],
                            description=change.get('reasoning', 'No description available'),
                            is_first_appearance=False
                        )
                    
                    # Log the change
                    final_stock = current_stock * multiplier
                    if final_stock < 10.0:
                        final_stock = 10.0
                    delta = final_stock - current_stock
                    print(f"  {change['character_name']}: {current_stock:.1f} × {multiplier:.2f} = {final_stock:.1f} ({delta:+.1f})")
            
            # Update stock history with chapter-level reasonings
            print("Updating stock history...")
            db.update_stock_history(chapter_id, character_reasonings)
            
            # Save market context
            print("Saving market context...")
            db.save_market_context(chapter_id)
            
            # Mark chapter as processed
            db.mark_chapter_processed(chapter_id)
            
        print(f"Chapter {chapter_id} processed successfully")
        return True
        
    def generate_data(self, start_chapter: int = 1,
                     end_chapter: Optional[int] = None,
                     max_chapters: Optional[int] = None,
                     skip_crawl: bool = False,
                     chapter_list: Optional[List[int]] = None):
        """
        Generate stock data for chapters.
        
        Args:
            start_chapter: First chapter to process
            end_chapter: Last chapter to process
            max_chapters: Maximum number of chapters
            skip_crawl: Skip crawling, use existing data in DB
            chapter_list: Specific list of chapters to process
        """
        if skip_crawl:
            print("Skipping web crawl, using existing chapter data...")
            with self.db as db:
                cursor = db.conn.cursor()
                if chapter_list:
                    placeholders = ','.join('?' * len(chapter_list))
                    cursor.execute(f"""
                        SELECT chapter_id FROM chapters 
                        WHERE chapter_id IN ({placeholders})
                        ORDER BY chapter_id
                    """, chapter_list)
                else:
                    cursor.execute("""
                        SELECT chapter_id FROM chapters 
                        WHERE chapter_id >= ?
                        ORDER BY chapter_id
                    """, (start_chapter,))
                    
                chapter_ids = [row['chapter_id'] for row in cursor.fetchall()]
                
            if not chapter_ids:
                print("No chapters found in database. Please crawl first.")
                return
                
            print(f"Found {len(chapter_ids)} chapters in database")
            
            for chapter_id in chapter_ids:
                with self.db as db:
                    chapter_info = db.get_chapter(chapter_id)
                    
                if not chapter_info:
                    print(f"Warning: Chapter {chapter_id} not found in database")
                    continue
                    
                # Mock character data (would need to be stored separately for skip_crawl)
                chapter_data = {
                    'chapter_id': chapter_info['chapter_id'],
                    'title': chapter_info['title'],
                    'url': chapter_info['url'],
                    'raw_description': chapter_info['raw_description'],
                    'arc_name': chapter_info['arc_name'],
                    'characters': []  # This would need to be stored/retrieved
                }
                
                self.process_chapter(chapter_data)
        else:
            # Crawl chapters from wiki
            print(f"Crawling chapters from wiki...")
            chapters_data = self.crawler.crawl_chapters(
                start_chapter=start_chapter,
                end_chapter=end_chapter,
                max_chapters=max_chapters
            )
            
            if not chapters_data:
                print("No chapters crawled")
                return
                
            print(f"\nProcessing {len(chapters_data)} chapters...")
            
            for i, chapter_data in enumerate(chapters_data, 1):
                print(f"\n{'='*80}")
                print(f"Progress: {i}/{len(chapters_data)}")
                print(f"{'='*80}")
                
                try:
                    success = self.process_chapter(chapter_data)
                    
                    if not success:
                        print(f"❌ Failed to process chapter {chapter_data['chapter_id']}")
                        if not self.verbose:
                            print("💡 Tip: Use --verbose flag to see what went wrong")
                        try:
                            response = input("Continue with next chapter? (y/n): ")
                            if response.lower() != 'y':
                                print("Stopping data generation")
                                break
                        except KeyboardInterrupt:
                            print("\n\n⚠️  Interrupted by user. Stopping data generation.")
                            break
                except Exception as e:
                    # Critical error (e.g., LLM failed all retries) - halt immediately
                    print(f"\n⛔ FATAL ERROR - Halting entire run")
                    print(f"Error: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    print(f"Run stopped at chapter {chapter_data['chapter_id']}")
                    return
                        
        print("\n" + "="*80)
        print("Data generation complete!")
        print("="*80)
        
        # Print summary
        with self.db as db:
            stats = db.get_market_statistics()
            top_ten = db.get_top_stocks(limit=10)
            
            print(f"\nMarket Summary:")
            print(f"Total characters: {stats['total_characters']}")
            print(f"Average stock value: {stats['average']:.1f}")
            print(f"Median stock value: {stats['median']:.1f}")
            print(f"\nTop 10 Stocks:")
            for i, stock in enumerate(top_ten, 1):
                print(f"{i:2d}. {stock['character_name']:<30s} {stock['stock_value']:>8.1f}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate offline One Piece character stock data'
    )
    parser.add_argument(
        '--start', type=int, default=1,
        help='First chapter to process (default: 1)'
    )
    parser.add_argument(
        '--end', type=int, default=None,
        help='Last chapter to process (default: all)'
    )
    parser.add_argument(
        '--max', type=int, default=None,
        help='Maximum number of chapters to process'
    )
    parser.add_argument(
        '--chapters', type=str, default=None,
        help='Comma-separated list of specific chapters to process (e.g., "1,2,5,10")'
    )
    parser.add_argument(
        '--db', type=str, default='one_piece_stocks.db',
        help='Database path (default: one_piece_stocks.db)'
    )
    parser.add_argument(
        '--model', type=str, default='gpt-4o-mini',
        help='OpenAI model to use (default: gpt-4o-mini)'
    )
    parser.add_argument(
        '--delay', type=float, default=1.0,
        help='Delay between wiki requests in seconds (default: 1.0)'
    )
    parser.add_argument(
        '--init', action='store_true',
        help='Initialize database schema'
    )
    parser.add_argument(
        '--skip-crawl', action='store_true',
        help='Skip web crawling, use existing chapter data in database'
    )
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Print prompts and LLM responses to console for monitoring'
    )
    
    args = parser.parse_args()
    
    # Parse chapter list if provided
    chapter_list = None
    if args.chapters:
        try:
            chapter_list = [int(c.strip()) for c in args.chapters.split(',')]
        except ValueError:
            print("Error: --chapters must be comma-separated integers")
            sys.exit(1)
    
    # Verbose is now always on by default, but flag still works to disable it
    verbose = True if not hasattr(args, 'quiet') else not args.quiet
    if args.verbose:
        verbose = True
    
    # Create generator
    generator = DataGenerator(
        db_path=args.db,
        openai_model=args.model,
        crawler_delay=args.delay,
        verbose=verbose
    )
    
    # Initialize if requested
    if args.init:
        generator.initialize()
        print("Database initialized. Run without --init to generate data.")
        return
        
    # Generate data
    generator.generate_data(
        start_chapter=args.start,
        end_chapter=args.end,
        max_chapters=args.max,
        skip_crawl=args.skip_crawl,
        chapter_list=chapter_list
    )


if __name__ == "__main__":
    main()

