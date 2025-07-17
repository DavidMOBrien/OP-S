#!/usr/bin/env python3
"""
Offline Data Generation for One Piece Character Tracker
Generates data for chapters 1-100 using mock components (no API calls or web scraping)
"""

import os
import sys
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from database import DatabaseManager, CharacterChange
from character_manager import CharacterManager
from llm_analyzer import CharacterAnalysis

def setup_logging():
    """Set up logging for offline data generation"""
    log_dir = Path("offline_generation_logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"offline_generation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

def clean_existing_data():
    """Clean all existing databases and logs"""
    logger = logging.getLogger(__name__)
    
    files_to_remove = [
        "one_piece_tracker.db",
        "test_integration.db",
        "one_piece_tracker.log",
        "processing_progress.json"
    ]
    
    dirs_to_clean = [
        "logs",
        "llm_logs", 
        "corrected_logs",
        "test_batch_logs",
        "batch_logs"
    ]
    
    # Remove database files
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Removed {file_path}")
    
    # Clean log directories
    for dir_path in dirs_to_clean:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
            logger.info(f"Cleaned directory {dir_path}")
    
    logger.info("✓ All existing data cleaned")

class MockChapterData:
    """Generates realistic mock chapter data for One Piece"""
    
    def __init__(self):
        # Define character introductions by chapter ranges
        self.character_introductions = {
            # Romance Dawn Arc (Chapters 1-7)
            1: [
                {'name': 'Monkey D. Luffy', 'wiki_url': '/wiki/Monkey_D._Luffy'},
                {'name': 'Coby', 'wiki_url': '/wiki/Coby'},
                {'name': 'Alvida', 'wiki_url': '/wiki/Alvida'}
            ],
            2: [
                {'name': 'Roronoa Zoro', 'wiki_url': '/wiki/Roronoa_Zoro'},
                {'name': 'Morgan', 'wiki_url': '/wiki/Morgan'},
                {'name': 'Helmeppo', 'wiki_url': '/wiki/Helmeppo'}
            ],
            3: [
                {'name': 'Rika', 'wiki_url': '/wiki/Rika'}
            ],
            # Orange Town Arc (Chapters 8-21)
            8: [
                {'name': 'Buggy', 'wiki_url': '/wiki/Buggy'},
                {'name': 'Nami', 'wiki_url': '/wiki/Nami'}
            ],
            9: [
                {'name': 'Cabaji', 'wiki_url': '/wiki/Cabaji'},
                {'name': 'Mohji', 'wiki_url': '/wiki/Mohji'}
            ],
            # Syrup Village Arc (Chapters 22-41)
            23: [
                {'name': 'Usopp', 'wiki_url': '/wiki/Usopp'},
                {'name': 'Kaya', 'wiki_url': '/wiki/Kaya'}
            ],
            24: [
                {'name': 'Kuro', 'wiki_url': '/wiki/Kuro'},
                {'name': 'Jango', 'wiki_url': '/wiki/Jango'}
            ],
            # Baratie Arc (Chapters 42-68)
            43: [
                {'name': 'Sanji', 'wiki_url': '/wiki/Sanji'},
                {'name': 'Zeff', 'wiki_url': '/wiki/Zeff'}
            ],
            44: [
                {'name': 'Don Krieg', 'wiki_url': '/wiki/Don_Krieg'},
                {'name': 'Gin', 'wiki_url': '/wiki/Gin'}
            ],
            50: [
                {'name': 'Dracule Mihawk', 'wiki_url': '/wiki/Dracule_Mihawk'}
            ],
            # Arlong Park Arc (Chapters 69-95)
            69: [
                {'name': 'Arlong', 'wiki_url': '/wiki/Arlong'},
                {'name': 'Nojiko', 'wiki_url': '/wiki/Nojiko'}
            ],
            70: [
                {'name': 'Hatchan', 'wiki_url': '/wiki/Hatchan'},
                {'name': 'Kuroobi', 'wiki_url': '/wiki/Kuroobi'}
            ],
            # Loguetown Arc (Chapters 96-100)
            96: [
                {'name': 'Smoker', 'wiki_url': '/wiki/Smoker'},
                {'name': 'Tashigi', 'wiki_url': '/wiki/Tashigi'}
            ],
            98: [
                {'name': 'Dragon', 'wiki_url': '/wiki/Dragon'}
            ]
        }
        
        # Define major story beats for character value changes
        self.story_beats = {
            1: {'luffy': 25, 'reason': 'Demonstrated Devil Fruit powers and declared dream to become Pirate King'},
            3: {'zoro': 30, 'luffy': 15, 'reason': 'Zoro joined crew, Luffy showed leadership'},
            8: {'nami': 20, 'buggy': 15, 'reason': 'Nami showed navigation skills, Buggy revealed as Devil Fruit user'},
            17: {'luffy': 20, 'zoro': 15, 'buggy': -10, 'reason': 'Luffy and Zoro defeated Buggy'},
            27: {'usopp': 25, 'luffy': 10, 'reason': 'Usopp showed courage, Luffy gained new crew member'},
            39: {'luffy': 20, 'usopp': 15, 'kuro': -25, 'reason': 'Defeated Kuro, Usopp proved himself'},
            52: {'zoro': -15, 'mihawk': 40, 'reason': 'Zoro lost to Mihawk but showed honor'},
            57: {'sanji': 30, 'luffy': 15, 'reason': 'Sanji joined crew with impressive fighting skills'},
            66: {'luffy': 25, 'sanji': 20, 'krieg': -30, 'reason': 'Defeated Don Krieg'},
            90: {'nami': 35, 'luffy': 20, 'reason': 'Nami backstory revealed, emotional character development'},
            94: {'luffy': 40, 'arlong': -35, 'reason': 'Luffy defeated Arlong in epic battle'},
            100: {'luffy': 30, 'smoker': 25, 'dragon': 50, 'reason': 'Loguetown climax, Dragon appearance'}
        }
    
    def get_chapter_data(self, chapter_num: int) -> Dict:
        """Generate mock chapter data"""
        # Get characters that appear in this chapter
        characters = []
        
        # Add newly introduced characters
        if chapter_num in self.character_introductions:
            characters.extend(self.character_introductions[chapter_num])
        
        # Add existing main characters based on story progression
        main_characters = []
        if chapter_num >= 1:
            main_characters.append({'name': 'Monkey D. Luffy', 'wiki_url': '/wiki/Monkey_D._Luffy'})
        if chapter_num >= 2:
            main_characters.append({'name': 'Roronoa Zoro', 'wiki_url': '/wiki/Roronoa_Zoro'})
        if chapter_num >= 8:
            main_characters.append({'name': 'Nami', 'wiki_url': '/wiki/Nami'})
        if chapter_num >= 23:
            main_characters.append({'name': 'Usopp', 'wiki_url': '/wiki/Usopp'})
        if chapter_num >= 43:
            main_characters.append({'name': 'Sanji', 'wiki_url': '/wiki/Sanji'})
        
        # Add main characters if they're not already in the new introductions
        existing_urls = {char['wiki_url'] for char in characters}
        for char in main_characters:
            if char['wiki_url'] not in existing_urls:
                characters.append(char)
        
        # Generate chapter title and summary
        arc_info = self._get_arc_info(chapter_num)
        
        return {
            'number': chapter_num,
            'title': f"Chapter {chapter_num}",
            'summary': f"Chapter {chapter_num} of the {arc_info['name']}. {arc_info['description']}",
            'characters': characters,
            'next_chapter_url': f'/wiki/Chapter_{chapter_num + 1}' if chapter_num < 100 else None
        }
    
    def _get_arc_info(self, chapter_num: int) -> Dict:
        """Get arc information for a chapter"""
        if 1 <= chapter_num <= 7:
            return {'name': 'Romance Dawn Arc', 'description': 'Luffy begins his pirate journey and recruits Zoro.'}
        elif 8 <= chapter_num <= 21:
            return {'name': 'Orange Town Arc', 'description': 'The crew encounters Buggy the Clown and Nami joins temporarily.'}
        elif 22 <= chapter_num <= 41:
            return {'name': 'Syrup Village Arc', 'description': 'Usopp joins the crew after the battle against Captain Kuro.'}
        elif 42 <= chapter_num <= 68:
            return {'name': 'Baratie Arc', 'description': 'Sanji joins the crew and Zoro faces Mihawk.'}
        elif 69 <= chapter_num <= 95:
            return {'name': 'Arlong Park Arc', 'description': 'The crew helps Nami defeat Arlong and his fishman pirates.'}
        elif 96 <= chapter_num <= 100:
            return {'name': 'Loguetown Arc', 'description': 'The crew visits the town where Gold Roger was executed.'}
        else:
            return {'name': 'East Blue Saga', 'description': 'Early adventures in the East Blue.'}

class MockLLMAnalyzer:
    """Mock LLM analyzer that generates realistic character analysis"""
    
    def __init__(self, mock_data: MockChapterData):
        self.mock_data = mock_data
        self.logger = logging.getLogger(__name__)
    
    def analyze_chapter(self, chapter_data: Dict, chapter_character_values: List[Dict], 
                       market_context: Dict) -> CharacterAnalysis:
        """Generate realistic character analysis based on story beats"""
        chapter_num = chapter_data['number']
        
        character_changes = []
        new_characters = []
        
        # Process new character introductions
        for char in chapter_character_values:
            if not char['exists_in_db']:
                starting_value = self._calculate_starting_value(char['name'], chapter_num)
                new_characters.append({
                    'wiki_url': char['wiki_url'],
                    'name': char['name'],
                    'starting_value': starting_value,
                    'reasoning': f'Introduction of {char["name"]} in Chapter {chapter_num}'
                })
        
        # Process character value changes based on story beats
        if chapter_num in self.mock_data.story_beats:
            beat = self.mock_data.story_beats[chapter_num]
            reason = beat['reason']
            
            for char in chapter_character_values:
                if char['exists_in_db']:
                    char_key = char['name'].lower().split()[-1]  # Use last name as key
                    if char_key in beat and isinstance(beat[char_key], int):
                        character_changes.append({
                            'wiki_url': char['wiki_url'],
                            'name': char['name'],
                            'value_change': beat[char_key],
                            'reasoning': reason
                        })
        
        analysis_summary = f"Chapter {chapter_num} analysis: {len(character_changes)} value changes, {len(new_characters)} new characters"
        
        self.logger.info(f"Generated analysis for Chapter {chapter_num}: {len(character_changes)} changes, {len(new_characters)} new")
        
        return CharacterAnalysis(
            character_changes=character_changes,
            new_characters=new_characters,
            analysis_reasoning=analysis_summary
        )
    
    def _calculate_starting_value(self, name: str, chapter_num: int) -> int:
        """Calculate starting value based on character importance and story progression"""
        name_lower = name.lower()
        
        # Major characters get higher starting values
        if 'luffy' in name_lower:
            return min(100 + chapter_num, 150)
        elif any(x in name_lower for x in ['zoro', 'sanji', 'nami', 'usopp']):
            return min(80 + chapter_num, 120)
        elif any(x in name_lower for x in ['mihawk', 'dragon']):
            return min(800 + chapter_num * 2, 900)
        elif any(x in name_lower for x in ['smoker', 'arlong', 'krieg', 'kuro']):
            return min(200 + chapter_num, 300)
        elif any(x in name_lower for x in ['buggy']):
            return min(150 + chapter_num, 200)
        else:
            # Regular characters
            return min(50 + chapter_num // 2, 100)

def generate_offline_data(start_chapter: int = 1, end_chapter: int = 100):
    """Generate offline data for specified chapter range"""
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting offline data generation for chapters {start_chapter}-{end_chapter}")
    
    # Initialize components
    db_manager = DatabaseManager()
    character_manager = CharacterManager(db_manager)
    mock_data = MockChapterData()
    mock_llm = MockLLMAnalyzer(mock_data)
    
    logger.info("✓ Components initialized")
    
    # Track progress
    processed_chapters = 0
    failed_chapters = []
    
    try:
        for chapter_num in range(start_chapter, end_chapter + 1):
            logger.info(f"Processing Chapter {chapter_num}...")
            
            try:
                # Generate mock chapter data
                chapter_data = mock_data.get_chapter_data(chapter_num)
                
                # Get character values from database
                chapter_character_values = []
                for char in chapter_data['characters']:
                    current_value = db_manager.get_character_current_value(char['wiki_url'])
                    recent_activity = db_manager.get_character_recent_activity(char['wiki_url'], 5)
                    chapter_character_values.append({
                        'name': char['name'],
                        'wiki_url': char['wiki_url'],
                        'current_value': current_value,
                        'exists_in_db': current_value is not None,
                        'recent_activity': recent_activity
                    })
                
                # Get market context
                market_context = db_manager.get_current_market_context()
                market_context_dict = {
                    'total_characters': market_context.total_characters,
                    'top_characters': market_context.top_characters,
                    'bottom_characters': market_context.bottom_characters,
                    'recent_changes': market_context.recent_changes
                }
                
                # Analyze with mock LLM
                analysis_result = mock_llm.analyze_chapter(
                    chapter_data, chapter_character_values, market_context_dict
                )
                
                # Process character changes
                character_changes = [CharacterChange(
                    wiki_url=change['wiki_url'],
                    name=change['name'],
                    value_change=change['value_change'],
                    reasoning=change['reasoning']
                ) for change in analysis_result.character_changes]
                
                success = db_manager.process_character_changes(
                    chapter_num, character_changes, analysis_result.new_characters
                )
                
                if not success:
                    raise Exception("Failed to process character changes")
                
                # Mark chapter as processed
                db_manager.add_chapter(chapter_num, chapter_data['title'], '')
                db_manager.mark_chapter_processed(chapter_num)
                
                processed_chapters += 1
                
                # Log progress every 10 chapters
                if chapter_num % 10 == 0:
                    logger.info(f"✓ Processed {processed_chapters} chapters (up to Chapter {chapter_num})")
                    
                    # Show current market state
                    current_market = db_manager.get_current_market_context()
                    if current_market.top_characters:
                        top_char = current_market.top_characters[0]
                        logger.info(f"  Current market leader: {top_char['name']} ({top_char['current_value']})")
                
            except Exception as e:
                logger.error(f"Failed to process Chapter {chapter_num}: {e}")
                failed_chapters.append(chapter_num)
                continue
    
    except KeyboardInterrupt:
        logger.info("Generation interrupted by user")
    
    # Final summary
    logger.info("=" * 60)
    logger.info("OFFLINE DATA GENERATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Chapters processed successfully: {processed_chapters}")
    logger.info(f"Chapters failed: {len(failed_chapters)}")
    
    if failed_chapters:
        logger.info(f"Failed chapters: {failed_chapters}")
    
    # Show final market state
    final_market = db_manager.get_current_market_context()
    logger.info(f"Total characters in database: {final_market.total_characters}")
    
    if final_market.top_characters:
        logger.info("Top 5 characters:")
        for i, char in enumerate(final_market.top_characters[:5], 1):
            logger.info(f"  {i}. {char['name']}: {char['current_value']}")
    
    # Database stats
    stats = db_manager.get_database_stats()
    logger.info(f"Database statistics:")
    logger.info(f"  Total characters: {stats['total_characters']}")
    logger.info(f"  Total history entries: {stats['total_history_entries']}")
    logger.info(f"  Processed chapters: {stats['processed_chapters']}")
    
    logger.info("✓ Offline data generation completed!")
    
    return processed_chapters == (end_chapter - start_chapter + 1)

def main():
    """Main entry point"""
    logger = setup_logging()
    
    print("🚀 One Piece Character Tracker - Offline Data Generation")
    print("=" * 60)
    print("This will generate data for chapters 1-100 using mock components")
    print("No API calls or web scraping will be performed")
    print()
    
    # Confirm clean start
    response = input("Clean all existing data and start fresh? (y/N): ").strip().lower()
    if response in ['y', 'yes']:
        clean_existing_data()
        print("✓ Existing data cleaned")
    else:
        print("⚠️  Continuing with existing data (may cause conflicts)")
    
    print()
    
    # Generate data
    try:
        success = generate_offline_data(1, 100)
        
        if success:
            print("\n🎉 Offline data generation completed successfully!")
            print("✓ All 100 chapters processed")
            print("✓ Character values and market dynamics generated")
            print("✓ Database populated with realistic One Piece data")
            print("\nYou can now:")
            print("- Explore the database with show_workflow.py")
            print("- Run analysis on the generated data")
            print("- Use the data for testing and development")
        else:
            print("\n⚠️  Data generation completed with some failures")
            print("Check the logs for details on failed chapters")
        
    except Exception as e:
        logger.error(f"Data generation failed: {e}")
        print(f"\n❌ Data generation failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())