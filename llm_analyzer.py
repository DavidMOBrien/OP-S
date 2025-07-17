#!/usr/bin/env python3
"""
LLM Analyzer for One Piece Character Tracker
Integrates with OpenAI API to analyze character value changes with market context
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import openai
from openai import OpenAI
import re
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class CharacterAnalysis:
    """Result of LLM character analysis"""
    character_changes: List[Dict]
    new_characters: List[Dict]
    analysis_reasoning: str

@dataclass
class LLMConfig:
    """Configuration for LLM analysis"""
    model: str = "gpt-4"
    temperature: float = 0.3
    max_tokens: int = 2000
    max_retries: int = 3
    base_retry_delay: float = 1.0
    max_retry_delay: float = 60.0

class LLMAnalyzer:
    """Analyzes One Piece chapters using LLM with market context"""
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[LLMConfig] = None, log_dir: str = "llm_logs"):
        """Initialize the LLM analyzer"""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.config = config or LLMConfig()
        
        # Setup logging directory
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different types of logs
        (self.log_dir / "prompts").mkdir(exist_ok=True)
        (self.log_dir / "responses").mkdir(exist_ok=True)
        (self.log_dir / "errors").mkdir(exist_ok=True)
        
        logger.info(f"Initialized LLM analyzer with model: {self.config.model}")
        logger.info(f"LLM logs will be saved to: {self.log_dir.absolute()}")
    
    def analyze_chapter(self, chapter_data: Dict, chapter_character_values: List[Dict], 
                       market_context: Dict) -> Optional[CharacterAnalysis]:
        """Analyze a chapter with full market context"""
        chapter_num = chapter_data['number']
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Check if custom prompt is provided
            if 'custom_prompt' in chapter_data:
                prompt = chapter_data['custom_prompt']
                logger.info(f"Using custom prompt for Chapter {chapter_num}")
            else:
                # Build standard prompt
                prompt = self._build_comprehensive_prompt(
                    chapter_data, chapter_character_values, market_context
                )
            
            # Log the prompt
            self._log_prompt(chapter_num, prompt, timestamp)
            
            logger.info(f"Analyzing Chapter {chapter_num} with {len(chapter_character_values)} characters")
            
            # Call LLM with retry logic
            response = self._call_llm_with_retry(prompt, chapter_num, timestamp)
            if not response:
                error_msg = f"Failed to get LLM response for Chapter {chapter_num}"
                logger.error(error_msg)
                self._log_error(chapter_num, error_msg, timestamp)
                return None
            
            # Log the response
            self._log_response(chapter_num, response, timestamp)
            
            # Parse and validate response
            analysis = self._parse_llm_response(response, chapter_character_values)
            if not analysis:
                error_msg = f"Failed to parse LLM response for Chapter {chapter_num}"
                logger.error(error_msg)
                self._log_error(chapter_num, error_msg, timestamp)
                return None
            
            # Log successful analysis
            self._log_analysis_result(chapter_num, analysis, timestamp)
            
            logger.info(f"Successfully analyzed Chapter {chapter_num}: "
                       f"{len(analysis.character_changes)} changes, {len(analysis.new_characters)} new characters")
            
            return analysis
            
        except Exception as e:
            error_msg = f"Error analyzing Chapter {chapter_num}: {e}"
            logger.error(error_msg)
            self._log_error(chapter_num, error_msg, timestamp, str(e))
            return None
    
    def _build_comprehensive_prompt(self, chapter_data: Dict, chapter_character_values: List[Dict], 
                                  market_context: Dict) -> str:
        """Build comprehensive prompt with market context and character information"""
        
        # Build character context section
        character_context = self._build_character_context(chapter_character_values)
        
        # Build market context section
        market_context_text = self._build_market_context(market_context)
        
        # Main prompt template
        prompt = f"""You are analyzing One Piece manga chapters to determine character value changes in a stock market-like system. Your analysis should consider fights, powerups, character development, aura moments, and narrative importance.

CHAPTER INFORMATION:
Chapter {chapter_data['number']}: {chapter_data.get('title', 'Unknown Title')}

CHAPTER SUMMARY:
{chapter_data['summary']}

{character_context}

{market_context_text}

ANALYSIS GUIDELINES:

1. VALUE SCALING: Late-game characters should have significantly higher values than early-game characters
   - Early main characters (Luffy, Zoro, Sanji): 50-200 range initially
   - Mid-tier characters (Captains, Vice Admirals): 300-600 range
   - Top-tier characters (Yonko, Admirals): 700-1000+ range
   - Legendary figures (Roger, Whitebeard): 900-1000+ range

2. MAJOR VALUE INCREASES (+15 to +50):
   FIGHTS & VICTORIES:
   - Defeating a major antagonist or boss-level opponent
   - Winning against someone with higher bounty/status
   - Overcoming seemingly impossible odds in battle
   - First time defeating a specific type of opponent (Logia, etc.)
   - Protecting crew/friends through combat prowess
   
   POWERUPS & ABILITIES:
   - Awakening new Devil Fruit abilities or advanced techniques
   - Learning advanced Haki (Conqueror's, Future Sight, etc.)
   - Mastering new fighting styles or weapons
   - Unlocking transformation forms (Gear 2/3/4, Monster Point, etc.)
   - Combining abilities in innovative ways
   
   AURA & HYPE MOMENTS:
   - Displaying Conqueror's Haki that affects multiple people
   - Making dramatic entrances that shift battle momentum
   - Intimidating powerful opponents through presence alone
   - Moments that make other characters acknowledge their strength
   - Epic one-liners or declarations that become iconic
   
   CHARACTER DEVELOPMENT:
   - Major backstory reveals that recontextualize their importance
   - Moments of incredible willpower or determination
   - Sacrificing for others or showing true leadership
   - Overcoming personal trauma or character flaws
   - Making difficult moral choices that define them

3. MODERATE VALUE INCREASES (+5 to +15):
   COMBAT PERFORMANCE:
   - Winning fights against equal or slightly weaker opponents
   - Showing new techniques or improved skills
   - Holding their own against stronger opponents
   - Clever tactical victories using intelligence over raw power
   - Teamwork moments that showcase their abilities
   
   NARRATIVE IMPORTANCE:
   - Advancing the plot through their actions
   - Revealing important information or connections
   - Taking on leadership roles or responsibilities
   - Moments of competence that help the crew/allies
   - Cool design moments or outfit changes that enhance their image
   
   HYPE BUILDING:
   - Teasing future power or importance
   - Other characters commenting on their potential
   - Surviving dangerous situations through skill
   - Small displays of advanced abilities

4. MAJOR VALUE DECREASES (-15 to -50):
   DEFEATS & FAILURES:
   - Losing to opponents they were expected to beat
   - Being completely overwhelmed or humiliated in battle
   - Failing to protect someone important to them
   - Major strategic blunders that cost their side
   - Being revealed as weaker than previously thought
   
   FRAUD MOMENTS:
   - Abilities being revealed as less impressive than hyped
   - Relying too heavily on others instead of own strength
   - Backing down from fights they should take
   - Being exposed as having inflated reputation
   - Losing credibility through poor decision-making
   
   CHARACTER REGRESSION:
   - Acting against their established principles
   - Showing cowardice in crucial moments
   - Betraying allies or friends
   - Making decisions that harm their crew/cause
   - Displaying incompetence in their area of expertise

5. MODERATE VALUE DECREASES (-5 to -15):
   MINOR SETBACKS:
   - Losing fights against stronger opponents (expected losses)
   - Making tactical mistakes that don't have major consequences
   - Moments of weakness or vulnerability
   - Being outshined by other characters in their specialty
   - Small displays of incompetence or poor judgment
   
   DISAPPOINTING MOMENTS:
   - Not living up to built-up expectations
   - Missing opportunities to shine or contribute
   - Being sidelined when they should be important
   - Showing less growth than expected
   - Design changes that make them less cool/intimidating

6. SPECIAL CONSIDERATIONS:
   DESIGN & AESTHETICS:
   - New outfits, weapons, or visual upgrades can add +3 to +8
   - Outfits with poor design can have negative effects
   - Intimidating new forms or appearances boost value
   - Poor design choices or downgrades can reduce value
   
   BOUNTY REVEALS:
   - Higher than expected bounties: +10 to +25
   - Lower than expected bounties: -5 to -15
   - First bounty reveals for new characters set baseline expectations
   
   CREW DYNAMICS:
   - Joining a powerful crew: +5 to +15
   - Being kicked out or leaving a crew: -10 to -25
   - Becoming a captain or leader: +10 to +20
   
   WORLD BUILDING IMPACT:
   - Being connected to major historical events: +5 to +20
   - Having important bloodlines or heritage revealed: +10 to +30
   - Being involved in world-changing events: +15 to +40

7. NEW CHARACTER STARTING VALUES:
   - Consider their introduction context and immediate impact
   - Scale appropriately to current story progression and power levels
   - Late-game introductions should have higher starting values
   - Factor in their design, abilities, and narrative role

8. MARKET AWARENESS:
   - Consider recent market trends and character trajectories
   - Ensure value changes make sense in current market context
   - Avoid extreme swings unless justified by major story events
   - Balance hype with actual demonstrated abilities

RESPONSE FORMAT:
Respond with valid JSON only. No additional text or explanations outside the JSON.

{{
  "character_changes": [
    {{
      "wiki_url": "/wiki/Character_Name",
      "name": "Character Name",
      "value_change": 25,
      "reasoning": "Detailed explanation of why this change occurred based on chapter events"
    }}
  ],
  "new_characters": [
    {{
      "wiki_url": "/wiki/New_Character",
      "name": "New Character Name", 
      "starting_value": 150,
      "reasoning": "Explanation of starting value based on power level and narrative importance"
    }}
  ],
  "analysis_summary": "Brief summary of key market movements and reasoning"
}}

Only include characters that had significant moments or were newly introduced in this chapter. Do not include characters with no meaningful changes."""

        return prompt
    
    def _build_character_context(self, chapter_character_values: List[Dict]) -> str:
        """Build character context section for the prompt"""
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
                    for activity in recent_activity[:3]:  # Show last 3 activities
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
        """Build market context section for the prompt"""
        context_lines = ["CURRENT MARKET CONTEXT:"]
        
        # Total characters
        total_chars = market_context.get('total_characters', 0)
        context_lines.append(f"Total Characters in Database: {total_chars}")
        
        # Top characters
        top_chars = market_context.get('top_characters', [])
        if top_chars:
            context_lines.append("\nTop 5 Highest Valued Characters:")
            for char in top_chars[:5]:
                context_lines.append(f"  {char['name']}: {char['value']} points")
        
        # Bottom characters
        bottom_chars = market_context.get('bottom_characters', [])
        if bottom_chars:
            context_lines.append("\nLowest 5 Valued Characters:")
            for char in bottom_chars[:5]:
                context_lines.append(f"  {char['name']}: {char['value']} points")
        
        # Recent changes
        recent_changes = market_context.get('recent_changes', [])
        if recent_changes:
            context_lines.append("\nRecent Market Activity (Last 5 Chapters):")
            for change in recent_changes[:10]:  # Show top 10 recent changes
                context_lines.append(f"  Chapter {change['chapter']}: {change['character']} "
                                   f"{change['change']:+d} ({change['reason']}) -> {change['new_value']}")
        
        return "\n".join(context_lines)
    
    def _log_prompt(self, chapter_num: int, prompt: str, timestamp: str):
        """Log the prompt sent to LLM"""
        try:
            prompt_file = self.log_dir / "prompts" / f"chapter_{chapter_num:04d}_{timestamp}.txt"
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(f"Chapter: {chapter_num}\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"Prompt Length: {len(prompt)} characters\n")
                f.write("=" * 80 + "\n")
                f.write(prompt)
            logger.debug(f"Logged prompt for Chapter {chapter_num} to {prompt_file}")
        except Exception as e:
            logger.warning(f"Failed to log prompt for Chapter {chapter_num}: {e}")
    
    def _log_response(self, chapter_num: int, response: str, timestamp: str):
        """Log the response from LLM"""
        try:
            # Save pure JSON response
            response_file = self.log_dir / "responses" / f"chapter_{chapter_num:04d}_{timestamp}.json"
            with open(response_file, 'w', encoding='utf-8') as f:
                f.write(response)
            
            # Save metadata separately
            metadata_file = self.log_dir / "responses" / f"chapter_{chapter_num:04d}_{timestamp}_metadata.txt"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                f.write(f"Chapter: {chapter_num}\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"Response Length: {len(response)} characters\n")
                f.write("=" * 80 + "\n")
            
            logger.debug(f"Logged response for Chapter {chapter_num} to {response_file}")
        except Exception as e:
            logger.warning(f"Failed to log response for Chapter {chapter_num}: {e}")
    
    def _log_error(self, chapter_num: int, error_msg: str, timestamp: str, exception_details: str = ""):
        """Log errors during processing"""
        try:
            error_file = self.log_dir / "errors" / f"chapter_{chapter_num:04d}_{timestamp}.txt"
            with open(error_file, 'w', encoding='utf-8') as f:
                f.write(f"Chapter: {chapter_num}\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"Error: {error_msg}\n")
                if exception_details:
                    f.write(f"Exception Details: {exception_details}\n")
                f.write("=" * 80 + "\n")
            logger.debug(f"Logged error for Chapter {chapter_num} to {error_file}")
        except Exception as e:
            logger.warning(f"Failed to log error for Chapter {chapter_num}: {e}")
    
    def _log_analysis_result(self, chapter_num: int, analysis: CharacterAnalysis, timestamp: str):
        """Log the final analysis result"""
        try:
            result_file = self.log_dir / "responses" / f"chapter_{chapter_num:04d}_{timestamp}_analysis.json"
            result_data = {
                "chapter": chapter_num,
                "timestamp": timestamp,
                "character_changes": analysis.character_changes,
                "new_characters": analysis.new_characters,
                "analysis_summary": analysis.analysis_reasoning
            }
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Logged analysis result for Chapter {chapter_num} to {result_file}")
        except Exception as e:
            logger.warning(f"Failed to log analysis result for Chapter {chapter_num}: {e}")

    def _call_llm_with_retry(self, prompt: str, chapter_num: int = 0, timestamp: str = "") -> Optional[str]:
        """Call LLM API with exponential backoff retry logic"""
        retry_delay = self.config.base_retry_delay
        
        for attempt in range(self.config.max_retries):
            try:
                logger.debug(f"LLM API call attempt {attempt + 1}/{self.config.max_retries}")
                
                response = self.client.chat.completions.create(
                    model=self.config.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert One Piece analyst who understands character power scaling, narrative importance, and market dynamics. Respond only with valid JSON."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens
                )
                
                content = response.choices[0].message.content
                if content:
                    logger.debug("Successfully received LLM response")
                    return content.strip()
                else:
                    logger.warning("Empty response from LLM")
                    
            except openai.RateLimitError as e:
                logger.warning(f"Rate limit error (attempt {attempt + 1}): {e}")
                if attempt < self.config.max_retries - 1:
                    logger.info(f"Waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, self.config.max_retry_delay)
                    continue
                else:
                    logger.error("Max retries reached for rate limit error")
                    return None
                    
            except openai.APIError as e:
                logger.warning(f"API error (attempt {attempt + 1}): {e}")
                if attempt < self.config.max_retries - 1:
                    logger.info(f"Waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, self.config.max_retry_delay)
                    continue
                else:
                    logger.error("Max retries reached for API error")
                    return None
                    
            except Exception as e:
                logger.error(f"Unexpected error calling LLM (attempt {attempt + 1}): {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, self.config.max_retry_delay)
                    continue
                else:
                    logger.error("Max retries reached for unexpected error")
                    return None
        
        return None
    
    def _parse_llm_response(self, response: str, chapter_character_values: List[Dict]) -> Optional[CharacterAnalysis]:
        """Parse and validate LLM JSON response"""
        try:
            # Clean the response - remove any markdown formatting
            cleaned_response = self._clean_json_response(response)
            
            # Parse JSON
            data = json.loads(cleaned_response)
            
            # Validate required fields
            if not isinstance(data, dict):
                logger.error("LLM response is not a JSON object")
                return None
            
            character_changes = data.get('character_changes', [])
            new_characters = data.get('new_characters', [])
            analysis_summary = data.get('analysis_summary', '')
            
            # Validate character changes
            validated_changes = self._validate_character_changes(character_changes, chapter_character_values)
            
            # Validate new characters
            validated_new_characters = self._validate_new_characters(new_characters, chapter_character_values)
            
            return CharacterAnalysis(
                character_changes=validated_changes,
                new_characters=validated_new_characters,
                analysis_reasoning=analysis_summary
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Raw response: {response}")
            return None
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return None
    
    def _clean_json_response(self, response: str) -> str:
        """Clean LLM response to extract valid JSON"""
        # Remove markdown code blocks
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*$', '', response)
        
        # Remove any text before the first {
        json_start = response.find('{')
        if json_start > 0:
            response = response[json_start:]
        
        # Remove any text after the last }
        json_end = response.rfind('}')
        if json_end > 0:
            response = response[:json_end + 1]
        
        return response.strip()
    
    def _validate_character_changes(self, character_changes: List[Dict], 
                                  chapter_character_values: List[Dict]) -> List[Dict]:
        """Validate and filter character changes"""
        validated_changes = []
        chapter_wiki_urls = {char['wiki_url'] for char in chapter_character_values}
        
        for change in character_changes:
            if not isinstance(change, dict):
                logger.warning("Invalid character change format (not dict)")
                continue
            
            # Required fields
            wiki_url = change.get('wiki_url', '').strip()
            name = change.get('name', '').strip()
            value_change = change.get('value_change')
            reasoning = change.get('reasoning', '').strip()
            
            # Validate required fields
            if not wiki_url or not name or value_change is None or not reasoning:
                logger.warning(f"Missing required fields in character change: {change}")
                continue
            
            # Validate value change is numeric
            try:
                value_change = int(value_change)
            except (ValueError, TypeError):
                logger.warning(f"Invalid value_change for {name}: {value_change}")
                continue
            
            # Validate reasonable value change range
            if abs(value_change) > 100:
                logger.warning(f"Extreme value change for {name}: {value_change}, capping at ±100")
                value_change = max(-100, min(100, value_change))
            
            # Validate wiki URL format
            if not self._is_valid_wiki_url(wiki_url):
                logger.warning(f"Invalid wiki URL format for {name}: {wiki_url}")
                continue
            
            # Check if character was actually in the chapter
            if wiki_url not in chapter_wiki_urls:
                logger.warning(f"Character {name} not found in chapter character list, skipping")
                continue
            
            validated_changes.append({
                'wiki_url': wiki_url,
                'name': name,
                'value_change': value_change,
                'reasoning': reasoning
            })
        
        return validated_changes
    
    def _validate_new_characters(self, new_characters: List[Dict], 
                               chapter_character_values: List[Dict]) -> List[Dict]:
        """Validate and filter new character introductions"""
        validated_new_characters = []
        new_character_urls = {char['wiki_url'] for char in chapter_character_values 
                             if not char.get('exists_in_db', True)}
        
        for new_char in new_characters:
            if not isinstance(new_char, dict):
                logger.warning("Invalid new character format (not dict)")
                continue
            
            # Required fields
            wiki_url = new_char.get('wiki_url', '').strip()
            name = new_char.get('name', '').strip()
            starting_value = new_char.get('starting_value')
            reasoning = new_char.get('reasoning', '').strip()
            
            # Validate required fields
            if not wiki_url or not name or starting_value is None or not reasoning:
                logger.warning(f"Missing required fields in new character: {new_char}")
                continue
            
            # Validate starting value is numeric and reasonable
            try:
                starting_value = int(starting_value)
            except (ValueError, TypeError):
                logger.warning(f"Invalid starting_value for {name}: {starting_value}")
                continue
            
            if starting_value < 1 or starting_value > 1000:
                logger.warning(f"Unreasonable starting value for {name}: {starting_value}, adjusting")
                starting_value = max(1, min(1000, starting_value))
            
            # Validate wiki URL format
            if not self._is_valid_wiki_url(wiki_url):
                logger.warning(f"Invalid wiki URL format for new character {name}: {wiki_url}")
                continue
            
            # Check if character was actually identified as new in the chapter
            if wiki_url not in new_character_urls:
                logger.warning(f"New character {name} not found in chapter new character list, skipping")
                continue
            
            validated_new_characters.append({
                'wiki_url': wiki_url,
                'name': name,
                'starting_value': starting_value,
                'reasoning': reasoning
            })
        
        return validated_new_characters
    
    def _is_valid_wiki_url(self, url: str) -> bool:
        """Validate wiki URL format"""
        if not url:
            return False
        
        # Should contain /wiki/ and be a reasonable character page
        if '/wiki/' not in url:
            return False
        
        # Should not be category, file, or other non-character pages
        invalid_patterns = [
            '/wiki/Category:', '/wiki/File:', '/wiki/Template:', 
            '/wiki/Help:', '/wiki/Special:', '/wiki/User:'
        ]
        
        for pattern in invalid_patterns:
            if pattern in url:
                return False
        
        return True
    
    def test_analysis(self, test_chapter_data: Dict = None) -> Optional[CharacterAnalysis]:
        """Test the LLM analysis with sample data"""
        if not test_chapter_data:
            test_chapter_data = {
                'number': 1,
                'title': 'Romance Dawn',
                'summary': 'Luffy begins his journey as a pirate and meets Coby. He demonstrates his rubber powers and shows determination to become the Pirate King.'
            }
        
        test_character_values = [
            {
                'name': 'Monkey D. Luffy',
                'wiki_url': '/wiki/Monkey_D._Luffy',
                'current_value': None,
                'exists_in_db': False,
                'recent_activity': []
            },
            {
                'name': 'Coby',
                'wiki_url': '/wiki/Coby',
                'current_value': None,
                'exists_in_db': False,
                'recent_activity': []
            }
        ]
        
        test_market_context = {
            'total_characters': 0,
            'top_characters': [],
            'bottom_characters': [],
            'recent_changes': []
        }
        
        logger.info("Testing LLM analysis with sample data")
        return self.analyze_chapter(test_chapter_data, test_character_values, test_market_context)


def create_llm_analyzer(api_key: Optional[str] = None, config: Optional[LLMConfig] = None) -> LLMAnalyzer:
    """Create and return an LLMAnalyzer instance"""
    return LLMAnalyzer(api_key, config)


if __name__ == "__main__":
    # Test the LLM analyzer
    logging.basicConfig(level=logging.INFO)
    
    try:
        analyzer = create_llm_analyzer()
        result = analyzer.test_analysis()
        
        if result:
            print("LLM Analysis Test Results:")
            print(f"Character Changes: {len(result.character_changes)}")
            for change in result.character_changes:
                print(f"  {change['name']}: {change['value_change']:+d} - {change['reasoning']}")
            
            print(f"New Characters: {len(result.new_characters)}")
            for new_char in result.new_characters:
                print(f"  {new_char['name']}: {new_char['starting_value']} - {new_char['reasoning']}")
            
            print(f"Analysis Summary: {result.analysis_reasoning}")
        else:
            print("LLM analysis test failed")
            
    except Exception as e:
        print(f"Error testing LLM analyzer: {e}")