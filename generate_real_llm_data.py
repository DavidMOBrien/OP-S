#!/usr/bin/env python3
"""
Real LLM Data Generation for One Piece Character Tracker
Uses actual OpenAI API calls with chronologically-aware prompts
"""

import os
import sys
import json
import logging
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from database import DatabaseManager, CharacterChange
from character_manager import CharacterManager
from llm_analyzer import LLMAnalyzer, LLMConfig, CharacterAnalysis
from wiki_crawler import WikiCrawler

def setup_logging():
    """Set up logging for real LLM data generation"""
    log_dir = Path("real_llm_generation_logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"real_llm_generation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
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
        "batch_logs",
        "offline_generation_logs",
        "real_llm_generation_logs"
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

class RealWikiChapterData:
    """Gets real chapter data from One Piece wiki"""   
 
    def __init__(self):
        self.wiki_crawler = WikiCrawler(rate_limit=1.0)  # 1 second delay between requests
        self.logger = logging.getLogger(__name__)
    
    def get_chapter_data(self, chapter_num: int) -> Dict:
        """Get real chapter data from wiki"""
        try:
            chapter_url = f"https://onepiece.fandom.com/wiki/Chapter_{chapter_num}"
            self.logger.info(f"🕷️  Crawling real wiki data from: {chapter_url}")
            
            # Use the real wiki crawler to get chapter data
            chapter_data = self.wiki_crawler.scrape_chapter_page(chapter_url)
            
            if chapter_data:
                self.logger.info(f"✓ Found {len(chapter_data.get('characters', []))} characters in Chapter {chapter_num}")
                for char in chapter_data.get('characters', [])[:5]:  # Log first 5 characters
                    self.logger.info(f"  - {char['name']} ({char['wiki_url']})")
                if len(chapter_data.get('characters', [])) > 5:
                    self.logger.info(f"  ... and {len(chapter_data.get('characters', [])) - 5} more characters")
                
                return chapter_data
            else:
                self.logger.warning(f"Failed to get chapter data from wiki for Chapter {chapter_num}")
                return self._get_fallback_chapter_data(chapter_num)
                
        except Exception as e:
            self.logger.error(f"Error crawling Chapter {chapter_num}: {e}")
            return self._get_fallback_chapter_data(chapter_num)
    
    def _get_fallback_chapter_data(self, chapter_num: int) -> Dict:
        """Fallback chapter data if wiki crawling fails"""
        return {
            'number': chapter_num,
            'title': f"Chapter {chapter_num}",
            'summary': f"Chapter {chapter_num} of One Piece manga.",
            'characters': [],
            'next_chapter_url': f'/wiki/Chapter_{chapter_num + 1}' if chapter_num < 1000 else None
        }

class ChronologicalLLMAnalyzer:
    """LLM analyzer that uses chronologically-aware prompts"""
    
    def __init__(self, api_key: str):
        self.config = LLMConfig(
            model="gpt-4",
            temperature=0.3,
            max_tokens=2000,
            max_retries=3
        )
        self.llm_analyzer = LLMAnalyzer(api_key=api_key, config=self.config, log_dir="real_llm_logs")
        self.logger = logging.getLogger(__name__)
    
    def analyze_chapter(self, chapter_data: Dict, chapter_character_values: List[Dict], 
                       market_context: Dict) -> Optional[CharacterAnalysis]:
        """Analyze chapter with chronologically-aware prompt"""
        chapter_num = chapter_data['number']
        
        # Build chronologically-aware prompt
        prompt = self._build_chronological_prompt(chapter_data, chapter_character_values, market_context)
        
        # Use the real LLM analyzer with our custom prompt
        return self._call_llm_with_custom_prompt(prompt, chapter_data, chapter_character_values, market_context)
    
    def _build_chronological_prompt(self, chapter_data: Dict, chapter_character_values: List[Dict], 
                                   market_context: Dict) -> str:
        """Build prompt that only uses knowledge available at this chapter"""
        chapter_num = chapter_data['number']
        
        # Build character context
        character_context = self._build_character_context(chapter_character_values)
        
        # Build market context
        market_context_text = self._build_market_context(market_context)
        
        # Chronological knowledge constraints
        knowledge_constraints = self._get_knowledge_constraints(chapter_num)
        
        prompt = f"""You are analyzing One Piece manga Chapter {chapter_num} to determine character value changes in a stock market-like system. 

CRITICAL: You are analyzing this as if Chapter {chapter_num} just came out in 1997-1999. You ONLY know information that was revealed up to and including Chapter {chapter_num}. Do not use any future knowledge.

{knowledge_constraints}

CHAPTER INFORMATION:
Chapter {chapter_num}: {chapter_data.get('title', 'Unknown Title')}

CHAPTER SUMMARY:
{chapter_data['summary']}

{character_context}

{market_context_text}

ANALYSIS GUIDELINES:

1. CHARACTER FILTERING:
   - ONLY analyze actual characters (people, creatures, beings)
   - DO NOT include places, locations, islands, ships, or objects
   - DO NOT include organizations unless they represent a specific person
   - Focus on named individuals who can take actions in the story

2. MARKET-DRIVEN VALUE SCALING:
   - Use CURRENT market state to determine ALL value changes
   - NO HARDCODED RANGES - let market velocity and context decide
   - Scale all changes relative to existing character values and recent market activity
   - Value changes should reflect the current "temperature" of the market

3. NARRATIVE CONTEXT IS EVERYTHING:
   - Value characters based on their CURRENT perceived role and threat level
   - A "butler" revealed as a deadly pirate captain should see DRAMATIC value increase
   - Characters beating protagonists should gain significant value
   - Characters being outmaneuvered or defeated should lose value proportionally

4. VILLAIN EFFECTIVENESS PRINCIPLE:
   - DO NOT punish villains for acting as effective antagonists
   - Successful villainy, intimidation, and threat display INCREASES value
   - Villains who dominate heroes, create fear, or demonstrate power should rise
   - Only punish villains when they fail, are defeated, or lose their threatening aura

5. DYNAMIC VALUE CHANGES:
   - MAJOR NARRATIVE SHIFTS: Use market velocity to determine scale (could be 2x, 5x, or 10x current average)
   - POWER REVEALS: When true identity/strength is revealed, scale based on gap between perception and reality
   - VICTORIES/DEFEATS: Scale based on opponent's current value and story impact
   - AURA MOMENTS: Characters gaining or losing narrative weight should see proportional changes

6. NO CHANGE ALLOWED:
   - Characters can maintain their current value if nothing significant happens
   - Background appearances without major story impact warrant no change
   - Don't force changes just to have activity

7. NEW CHARACTER STARTING VALUES:
   - Base entirely on IMMEDIATE portrayal and current market context
   - If they're introduced as a major threat when top character is 500, they could start at 600-1000+
   - If introduced as minor character, scale to current market's lower tier
   - Let their introduction impact determine their market entry point

8. MARKET MOMENTUM:
   - Early story: Changes may be smaller in absolute terms but significant in percentage
   - As story progresses: Absolute changes should grow with the established market scale
   - Legendary reveals should create market disruption regardless of timing
   - Power creep should be naturally reflected in valuations

9. CHRONOLOGICAL AWARENESS:
   - Only use information revealed up to Chapter {chapter_num}
   - Value based on CURRENT perception, not future knowledge
   - When characters are revealed to be more/less than they seemed, adjust dramatically

RESPONSE FORMAT:
Respond with valid JSON only. No additional text or explanations outside the JSON.

{{
  "character_changes": [
    {{
      "wiki_url": "/wiki/Character_Name",
      "name": "Character Name",
      "value_change": 25,
      "reasoning": "Detailed explanation based ONLY on what we know up to Chapter {chapter_num}"
    }}
  ],
  "new_characters": [
    {{
      "wiki_url": "/wiki/New_Character",
      "name": "New Character Name", 
      "starting_value": 80,
      "reasoning": "Starting value based ONLY on introduction and immediate context"
    }}
  ],
  "analysis_summary": "Brief summary of key developments in Chapter {chapter_num}"
}}

Only include characters that had significant moments or were newly introduced in this chapter."""

        return prompt
    
    def _get_knowledge_constraints(self, chapter_num: int) -> str:
        """Get knowledge constraints for this chapter"""
        constraints = [
            f"KNOWLEDGE CUTOFF: Chapter {chapter_num} (East Blue Saga)",
            "- The Grand Line is mentioned but largely unknown",
            "- Devil Fruits are rare and mysterious powers", 
            "- The World Government and Marines are the main authority",
            "- Pirates are generally seen as criminals and threats"
        ]
        
        if chapter_num >= 50:
            constraints.append("- The Seven Warlords of the Sea exist (Mihawk introduced)")
        
        if chapter_num >= 96:
            constraints.append("- Gold Roger was the previous Pirate King")
            constraints.append("- Loguetown is where Roger was born and executed")
        
        if chapter_num >= 98:
            constraints.append("- Dragon is a mysterious figure with unknown motives")
            constraints.append("- DO NOT assume Dragon is Luffy's father - this is not revealed yet!")
        
        # Add specific knowledge constraints
        forbidden_knowledge = [
            "- DO NOT use knowledge of Haki, Gear techniques, or advanced power systems",
            "- DO NOT reference the Four Emperors/Yonko system", 
            "- DO NOT use bounty amounts not yet revealed",
            "- DO NOT reference character relationships not yet established",
            "- DO NOT use power scaling from later arcs"
        ]
        
        constraints.extend(forbidden_knowledge)
        
        return "\n".join(constraints)
    
    def _build_character_context(self, chapter_character_values: List[Dict]) -> str:
        """Build character context section"""
        if not chapter_character_values:
            return "CHARACTERS IN CHAPTER: None identified"
        
        context_lines = ["CHARACTERS IN THIS CHAPTER:"]
        
        for char in chapter_character_values:
            name = char['name']
            wiki_url = char['wiki_url']
            current_value = char.get('current_value')
            exists_in_db = char.get('exists_in_db', False)
            recent_activity = char.get('recent_activity', [])
            
            if exists_in_db and current_value is not None:
                context_lines.append(f"\n{name} (Current Value: {current_value})")
                context_lines.append(f"  Wiki URL: {wiki_url}")
                
                if recent_activity:
                    context_lines.append("  Recent Activity:")
                    for activity in recent_activity[:3]:
                        context_lines.append(f"    Chapter {activity['chapter']}: {activity['value_change']:+d} "
                                           f"({activity['reasoning']}) -> {activity['new_value']}")
                else:
                    context_lines.append("  Recent Activity: None")
            else:
                context_lines.append(f"\n{name} (NEW CHARACTER - Not in database)")
                context_lines.append(f"  Wiki URL: {wiki_url}")
                context_lines.append("  This character needs a starting value based on their introduction")
        
        return "\n".join(context_lines)
    
    def _build_market_context(self, market_context: Dict) -> str:
        """Build market context section"""
        context_lines = ["CURRENT MARKET CONTEXT:"]
        
        total_chars = market_context.get('total_characters', 0)
        context_lines.append(f"Total Characters in Database: {total_chars}")
        
        top_chars = market_context.get('top_characters', [])
        if top_chars:
            context_lines.append("\nTop 5 Highest Valued Characters:")
            for char in top_chars[:5]:
                context_lines.append(f"  {char['name']}: {char['current_value']} points")
        
        recent_changes = market_context.get('recent_changes', [])
        if recent_changes:
            context_lines.append("\nRecent Market Activity:")
            for change in recent_changes[:5]:
                context_lines.append(f"  Chapter {change['chapter']}: {change['character']} "
                                   f"{change['change']:+d} -> {change['new_value']}")
        
        return "\n".join(context_lines)
    
    def _call_llm_with_custom_prompt(self, prompt: str, chapter_data: Dict, 
                                   chapter_character_values: List[Dict], 
                                   market_context: Dict) -> Optional[CharacterAnalysis]:
        """Call LLM with custom chronological prompt"""
        try:
            chapter_num = chapter_data['number']
            
            # Log the exact prompt being sent to LLM
            self.logger.info("=" * 80)
            self.logger.info(f"📝 PROMPT FOR CHAPTER {chapter_num}")
            self.logger.info("=" * 80)
            self.logger.info(prompt)
            self.logger.info("=" * 80)
            
            # Create a temporary modified chapter data for the LLM analyzer
            modified_chapter_data = chapter_data.copy()
            modified_chapter_data['custom_prompt'] = prompt
            
            # Call the real LLM analyzer
            result = self.llm_analyzer.analyze_chapter(
                modified_chapter_data, chapter_character_values, market_context
            )
            
            if result:
                self.logger.info(f"✅ LLM analysis completed for Chapter {chapter_num}: "
                               f"{len(result.character_changes)} changes, {len(result.new_characters)} new")
                
                # Log the LLM response
                self.logger.info(f"📊 LLM RESPONSE FOR CHAPTER {chapter_num}:")
                self.logger.info(f"Character Changes: {len(result.character_changes)}")
                for change in result.character_changes:
                    self.logger.info(f"  - {change['name']}: {change['value_change']:+d} ({change['reasoning']})")
                
                self.logger.info(f"New Characters: {len(result.new_characters)}")
                for new_char in result.new_characters:
                    self.logger.info(f"  - {new_char['name']}: {new_char['starting_value']} ({new_char['reasoning']})")
            else:
                self.logger.error(f"❌ LLM analysis returned no result for Chapter {chapter_num}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in LLM analysis for Chapter {chapter_data['number']}: {e}")
            return None

def generate_real_llm_data(start_chapter: int = 1, end_chapter: int = 100, api_key: str = None):
    """Generate data using real LLM analysis with chronological awareness"""
    logger = logging.getLogger(__name__)
    
    if not api_key:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or provide api_key parameter.")
    
    logger.info(f"Starting REAL LLM data generation for chapters {start_chapter}-{end_chapter}")
    logger.info("This will make actual OpenAI API calls - expect slower processing and API costs")
    
    # Initialize components
    db_manager = DatabaseManager()
    character_manager = CharacterManager(db_manager)
    chapter_data_generator = RealWikiChapterData()
    llm_analyzer = ChronologicalLLMAnalyzer(api_key)
    
    logger.info("✓ Components initialized with real LLM analyzer")
    
    # Track progress
    processed_chapters = 0
    failed_chapters = []
    total_api_calls = 0
    
    try:
        for chapter_num in range(start_chapter, end_chapter + 1):
            logger.info(f"Processing Chapter {chapter_num}...")
            
            try:
                # Generate chronologically-aware chapter data
                chapter_data = chapter_data_generator.get_chapter_data(chapter_num)
                
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
                
                # Analyze with REAL LLM (this makes API call)
                logger.info(f"Making OpenAI API call for Chapter {chapter_num}...")
                analysis_result = llm_analyzer.analyze_chapter(
                    chapter_data, chapter_character_values, market_context_dict
                )
                total_api_calls += 1
                
                if not analysis_result:
                    raise Exception("LLM analysis returned no result")
                
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
                    logger.info(f"  API calls made: {total_api_calls}")
                    
                    # Show current market state
                    current_market = db_manager.get_current_market_context()
                    if current_market.top_characters:
                        top_char = current_market.top_characters[0]
                        logger.info(f"  Current market leader: {top_char['name']} ({top_char['current_value']})")
                
                # Add delay between API calls to be respectful
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Failed to process Chapter {chapter_num}: {e}")
                failed_chapters.append(chapter_num)
                continue
    
    except KeyboardInterrupt:
        logger.info("Generation interrupted by user")
    
    # Final summary
    logger.info("=" * 60)
    logger.info("REAL LLM DATA GENERATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Chapters processed successfully: {processed_chapters}")
    logger.info(f"Chapters failed: {len(failed_chapters)}")
    logger.info(f"Total OpenAI API calls made: {total_api_calls}")
    
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
    
    logger.info("✓ Real LLM data generation completed!")
    
    return processed_chapters == (end_chapter - start_chapter + 1)

def main():
    """Main entry point"""
    logger = setup_logging()
    
    print("🤖 One Piece Character Tracker - REAL LLM Data Generation")
    print("=" * 60)
    print("This will use actual OpenAI API calls with chronologically-aware prompts")
    print("⚠️  WARNING: This will be SLOW and will cost money!")
    print("⚠️  Each chapter takes 5-10 seconds and costs ~$0.01-0.05")
    print("⚠️  100 chapters = ~10-15 minutes and ~$1-5 in API costs")
    print()
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found!")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your_api_key_here'")
        return 1
    
    print(f"✓ Found OpenAI API key: {api_key[:20]}...")
    print()
    
    # Confirm clean start
    response = input("Clean all existing data and start fresh? (y/N): ").strip().lower()
    if response in ['y', 'yes']:
        clean_existing_data()
        print("✓ Existing data cleaned")
    else:
        print("⚠️  Continuing with existing data (may cause conflicts)")
    
    print()
    
    # Confirm API usage
    response = input("Proceed with REAL LLM analysis? This will cost money! (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("Cancelled by user")
        return 0
    
    print()
    
    # Generate data
    try:
        success = generate_real_llm_data(1, 100, api_key)
        
        if success:
            print("\n🎉 Real LLM data generation completed successfully!")
            print("✓ All 100 chapters processed with actual AI analysis")
            print("✓ Character values based on chronologically-aware LLM decisions")
            print("✓ Database populated with realistic, AI-generated One Piece data")
            print("\nYou can now:")
            print("- Explore the database with show_workflow.py")
            print("- Analyze the AI-generated character progressions")
            print("- Compare with the mock data approach")
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