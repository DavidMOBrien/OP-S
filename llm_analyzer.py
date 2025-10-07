"""LLM analyzer for character stock changes - PER CHARACTER APPROACH."""

import json
from typing import List, Dict, Optional
from openai import OpenAI
import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

# Load environment variables from .env file
load_dotenv()


class LLMAnalyzer:
    """Analyzes chapters using LLM to extract stock changes."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini", log_dir: str = "llm_logs"):
        """
        Initialize the analyzer.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use (gpt-4o-mini, gpt-4o, etc.)
            log_dir: Directory to save LLM interaction logs
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY env var")
            
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        
        # Create timestamped subfolder for this run
        run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir = Path(log_dir) / run_timestamp
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def _save_character_log(self, character_name: str, chapter_id: int, char_type: str,
                           system_prompt: str, user_prompt: str, response: str, success: bool):
        """
        Save LLM interaction log for a character.
        
        Args:
            character_name: Name of the character
            chapter_id: Chapter number
            char_type: 'NEW' or 'EXISTING'
            system_prompt: System prompt sent
            user_prompt: User prompt sent
            response: LLM response
            success: Whether the call succeeded
        """
        # Sanitize character name for filesystem
        safe_char_name = "".join(c if c.isalnum() or c in (' ', '_', '-') else '_' for c in character_name)
        safe_char_name = safe_char_name.replace(' ', '_')
        
        # Create character subfolder
        char_dir = self.log_dir / safe_char_name
        char_dir.mkdir(exist_ok=True)
        
        # Create log file
        status = "SUCCESS" if success else "FAILED"
        filename = f"chapter_{chapter_id:03d}_{char_type}_{status}.txt"
        filepath = char_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write(f"CHARACTER: {character_name}\n")
            f.write(f"CHAPTER: {chapter_id}\n")
            f.write(f"TYPE: {char_type}\n")
            f.write(f"STATUS: {status}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Model: {self.model}\n")
            f.write("="*80 + "\n\n")
            
            f.write("SYSTEM PROMPT:\n")
            f.write("-"*80 + "\n")
            f.write(system_prompt)
            f.write("\n\n")
            
            f.write("USER PROMPT:\n")
            f.write("-"*80 + "\n")
            f.write(user_prompt)
            f.write("\n\n")
            
            f.write("LLM RESPONSE:\n")
            f.write("-"*80 + "\n")
            f.write(response)
            f.write("\n\n")
            
            f.write("="*80 + "\n")
        
    def filter_characters(self, characters: List[Dict], chapter_data: Dict, verbose: bool = False) -> List[Dict]:
        """
        Use LLM to filter out generic groups, locations, etc.
        
        Args:
            characters: List of character dicts with name and href
            chapter_data: Chapter information
            verbose: Print debug info
            
        Returns:
            List of valid named individual characters
        """
        system_prompt = """You filter One Piece character lists to remove NOISE and IRRELEVANT characters.

REMOVE:
- Generic groups: "Pirates", "Marines", "Straw Hat Pirates", "Buggy's Crew"
- Locations: "Orange Town", "Shells Town", "East Blue"
- Military ranks: "Captain", "Lieutenant", "Seaman Recruit"
- Generic terms: "Villagers", "Townsfolk", "Citizens", "Animals"
- **Background/cover story characters**: Characters ONLY mentioned briefly or in cover stories/flashbacks but NOT present in THIS chapter's main events
- **Passive mentions**: Characters only talked ABOUT but who don't appear or take action

KEEP:
- Named individuals who APPEAR and DO SOMETHING in this chapter: "Monkey D. Luffy", "Roronoa Zoro", "Buggy", "Nami"
- Even minor named characters IF they have a scene or action: "Rika", "Helmeppo", "Koby"

Read the chapter summary carefully to determine who actually appears vs. who is just mentioned!

Return JSON: {"keep": ["name1", "name2", ...]}
"""

        # Build character list
        char_list = "\n".join([f"- {c['name']} ({c['href']})" for c in characters])
        
        user_prompt = f"""Chapter {chapter_data['chapter_id']}: {chapter_data['title']}

CHAPTER SUMMARY:
{chapter_data.get('raw_description', '')}

Characters extracted from wiki:
{char_list}

Which are NAMED INDIVIDUALS who ACTUALLY APPEAR and DO SOMETHING in this chapter (not just mentioned, not just in cover stories)?
Return JSON: {{"keep": ["exact name from list", ...]}}"""

        if verbose:
            print(f"\n🔍 FILTERING {len(characters)} characters...")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            keep_names = set(result.get('keep', []))
            
            # Filter characters
            filtered = [c for c in characters if c['name'] in keep_names]
            
            if verbose:
                removed = [c['name'] for c in characters if c['name'] not in keep_names]
                print(f"✅ Kept {len(filtered)} valid characters")
                if removed:
                    print(f"🗑️  Removed: {', '.join(removed)}")
            
            return filtered
            
        except Exception as e:
            print(f"⚠️  Filter failed ({e}), keeping all characters")
            return characters
    
    def analyze_new_character(self, character: Dict, chapter_data: Dict, 
                            market_context: Dict, verbose: bool = False, max_retries: int = 3) -> Dict:
        """
        Get initial stock value for a NEW character.
        
        Args:
            character: Character dict with name and href
            chapter_data: Chapter information
            market_context: Market state (for scaling)
            verbose: Print debug info
            max_retries: Number of retry attempts
            
        Returns:
            Dict with character_name, character_href, stock_change (integer), confidence, reasoning
        """
        system_prompt = """You assign INITIAL STOCK VALUES to new One Piece characters based on COMPREHENSIVE EVALUATION.

🎯 **EVALUATION CRITERIA** (ALL weighted EQUALLY - not just fights!):
1. **Character Moments & Growth** - Emotional depth, character development, compelling dialogue, moral choices, relationships
2. **Fight Performance** - Wins, losses, power displays, techniques (but fighting is just ONE aspect!)
3. **Writing Quality** - How well written/portrayed, dialogue quality, scene presence
4. **Aura/Presence** - Commanding energy, intimidation, charisma, "main character energy", how they're talked about by others
5. **Visual Design & Aesthetics** - Cool designs, attractive appearance, iconic looks (yes, Nami bikini counts!)
6. **Narrative Weight** - Plot importance, thematic relevance, setup for future arcs
7. **Threat/Hype** - Being built up as dangerous, mentioned with fear/respect, anticipated arrival
8. **Comparative Context** - How they compare to OTHER characters' past debuts (see "PAST CHANGES" below)

⚖️ **CRITICAL MINDSET** (BE BOLD - NO FAVORITISM!):
- **Character moments = Combat moments** - A powerful emotional scene is as valuable as winning a fight
- **BE HARSH ON HERO MISTAKES**: If a hero is cowardly, makes dumb choices, fails their team, whines, regresses, or fumbles a situation → PUNISH THEM! No excuses!
  - Heroes getting captured due to carelessness = NEGATIVE stock
  - Heroes being indecisive or weak-willed = NEGATIVE stock
  - Heroes failing to protect someone = NEGATIVE stock
- **CELEBRATE VILLAIN SUCCESS**: Villain being threatening, intimidating, clever, successfully executing schemes, or advancing their goals = POSITIVE stock!
  - Villain successfully capturing the hero = POSITIVE for villain
  - Villain's reputation/hype growing = POSITIVE for villain
  - Villain dominating a scene = POSITIVE for villain
- **Role fulfillment > Alignment**: A villain being effective at being evil = stock UP. A hero fumbling = stock DOWN.
- **Being hyped/anticipated is POSITIVE** - If other characters fear/mention a villain, that's a strength!

📊 **SCALING (use "PAST CHANGES" as reference for consistency):**
- **Arc villains**: Should rival current top heroes (look at protagonist's stock AND market average)
  - Early series (market avg 30-50): Arc villain = 40-70
  - Mid series (market avg 100-200): Arc villain = 100-200+
  - The market grows, so should new threats!
- **Henchmen**: 30-60% of their boss's value
- **Allies/Supporting cast**: Based on narrative importance, scale to current market level
- **Cameos/Minor**: 10-30, but can be higher if market average is very high

⚠️ **IMPORTANT**: New characters should be scaled to the CURRENT market level!
A villain introduced at Chapter 50 should be much stronger than one at Chapter 1 if the stakes have grown!

Return JSON: {"stock_value": <integer 10-200>, "confidence": 0-1, "reasoning": "..."}"""

        # Get context
        protag_stock = 100  # default
        if market_context.get('top_ten'):
            protag_stock = market_context['top_ten'][0]['stock_value']
        
        stats = market_context.get('statistics', {})
        market_avg = stats.get('average', 50)
        
        # Build top stocks list
        top_stocks_text = ""
        if market_context.get('top_ten'):
            top_stocks_text = "\nTOP 10 STOCKS (from previous chapters):\n"
            for i, char in enumerate(market_context['top_ten'][:10], 1):
                top_stocks_text += f"  {i}. {char['character_name']}: {char['stock_value']:.0f}\n"
        
        # Build chapter character history
        chapter_history_text = ""
        if market_context.get('chapter_character_history'):
            chapter_history_text = "\nPAST CHANGES FOR CHARACTERS IN THIS CHAPTER (last 3 changes per character):\n"
            for hist in market_context['chapter_character_history'][:15]:  # Limit to 15 entries
                if hist.get('multiplier') is None:
                    # New character
                    chapter_history_text += f"  • {hist['character_name']} (Ch.{hist['chapter_id']}): NEW at {hist.get('initial_value', 0):.0f} → {hist.get('reasoning', '')}\n"
                else:
                    # Existing character with multiplier
                    chapter_history_text += f"  • {hist['character_name']} (Ch.{hist['chapter_id']}): {hist['multiplier']:.2f}x → {hist.get('reasoning', '')}\n"
        
        user_prompt = f"""NEW CHARACTER: {character['name']}
Chapter {chapter_data['chapter_id']}: {chapter_data['title']}

MARKET CONTEXT (from previous chapters):
📊 PERCENTILES: p10={stats.get('p10', 0):.0f} | p25={stats.get('p25', 0):.0f} | p33={stats.get('p33', 0):.0f} | p50={stats.get('p50', 0):.0f} | p66={stats.get('p66', 0):.0f} | p75={stats.get('p75', 0):.0f} | p90={stats.get('p90', 0):.0f} | p99={stats.get('p99', 0):.0f}
- Protagonist stock: {protag_stock:.0f} | Average: {market_avg:.0f} | Median: {stats.get('median', 0):.0f}
- Total characters: {stats.get('total_characters', 0)}
{top_stocks_text}
{chapter_history_text}

CHAPTER SUMMARY:
{chapter_data['raw_description']}

What initial stock value for {character['name']}?
⚠️ SCALE TO CURRENT MARKET PERCENTILES: Arc villains should target p75-p90 range. Henchmen around p33-p50. Minor characters below p33.
Return JSON: {{"stock_value": <integer>, "confidence": 0-1, "reasoning": "..."}}"""

        for attempt in range(1, max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7
                )
                
                content = response.choices[0].message.content
                result = json.loads(content)
                
                stock_value = int(result['stock_value'])
                confidence = float(result['confidence'])
                reasoning = result['reasoning']
                
                # Validate and clamp to minimum of 1
                if stock_value < 1:
                    stock_value = 1  # Default to minimum stock
                if stock_value > 10000:
                    raise ValueError(f"Stock value out of range: {stock_value}")
                
                if confidence < 0 or confidence > 1:
                    confidence = max(0, min(1, confidence))
                
                # Save log
                self._save_character_log(character['name'], chapter_data['chapter_id'], 
                                        'NEW', system_prompt, user_prompt, content, True)
                
                return {
                    'character_name': character['name'],
                    'character_href': character['href'],
                    'stock_change': stock_value,
                    'confidence': confidence,
                    'reasoning': reasoning
                }
                
            except Exception as e:
                # Save failed log
                self._save_character_log(character['name'], chapter_data['chapter_id'],
                                        'NEW', system_prompt, user_prompt, 
                                        f"Error: {e}", False)
                
                if attempt >= max_retries:
                    print(f"❌ Failed to analyze NEW {character['name']}: {e}")
                    # Return default
                    return {
                        'character_name': character['name'],
                        'character_href': character['href'],
                        'stock_change': int(market_avg),
                        'confidence': 0.3,
                        'reasoning': f"Failed analysis, using market average ({e})"
                    }
        
    def analyze_existing_character(self, character: Dict, chapter_data: Dict, 
                                  market_context: Dict, verbose: bool = False, max_retries: int = 3) -> Dict:
        """
        Get stock multiplier for an EXISTING character.
        
        Args:
            character: Character dict with name, href, current_stock, recent_history
            chapter_data: Chapter information
            market_context: Market state
            verbose: Print debug info
            max_retries: Number of retry attempts
            
        Returns:
            Dict with character_name, character_href, stock_change (decimal multiplier), confidence, reasoning
        """
        system_prompt = """You assign STOCK MULTIPLIERS to existing One Piece characters based on COMPREHENSIVE EVALUATION.

🎯 **EVALUATION CRITERIA** (ALL weighted EQUALLY - not just fights!):
1. **Character Moments & Growth** - Emotional depth, development arcs, compelling dialogue, moral choices, relationships formed/broken
2. **Fight Performance** - Wins, losses, battle progress, power displays (but fighting is just ONE aspect!)
3. **Writing Quality** - How well written/portrayed, dialogue quality, scene presence this chapter
4. **Aura/Presence** - Commanding energy, intimidation factor, charisma, being talked about/feared by others
5. **Visual Moments** - Cool scenes, intimidating shots, attractive appearances, iconic moments
6. **Narrative Weight** - Plot importance, thematic relevance, setup for future events
7. **Role Fulfillment** - How well they execute their narrative role (hero being inspiring, villain being threatening)
8. **Comparative Context** - How their actions compare to OTHER characters in similar situations (see "PAST CHANGES")

⚖️ **CRITICAL MINDSET** (BE BOLD - NO PROTAGONIST BIAS!):
- **Character moments = Combat moments** - Emotional scene with great writing is AS valuable as winning a fight
- **BE HARSH ON HERO MISTAKES**: When heroes mess up, GET CAPTURED due to carelessness, make DUMB DECISIONS, are COWARDLY, WHINE, or FUMBLE → PUNISH THEM with negative multipliers! Don't coddle the protagonists!
  - Getting captured by villains due to carelessness = 0.70-0.85x (not just 0.95x!)
  - Making poor strategic choices that hurt the team = 0.80-0.90x
  - Being indecisive or showing weakness = 0.85-0.95x
- **CELEBRATE VILLAIN EFFECTIVENESS**: When villains are THREATENING, successfully CAPTURE heroes, INTIMIDATE others, execute CLEVER SCHEMES, or advance their goals → REWARD THEM with positive multipliers!
  - Villain successfully capturing protagonist = 1.15-1.30x (they're doing their job!)
  - Villain's hype/reputation growing = 1.10-1.20x
  - Villain dominating a scene with presence = 1.10-1.25x
- **Absence vs. Defeat are DIFFERENT**:
  - **Not appearing but being mentioned/hyped** = INACTIVE (1.0) or small positive if threat is building
  - **Actually losing/being defeated** = NEGATIVE multiplier
  - **Don't punish for absence!**
- **Net outcome matters** - Focus on chapter's END result, not every micro-moment
- **Heroic sacrifice = GAIN**, **Wise restraint = STRENGTH**, **Strategic deception = INTELLIGENCE**

🎚️ **EXPECTATION SCALING** (CRITICAL - prevents exponential growth!):
**Higher stock = MUCH higher expectations = VERY hard to gain, EASY to lose**

**Use PERCENTILES (see "MARKET CONTEXT" below) - NOT average!**

- **Top 10% (p90+)**: 🚫 **EXTREME RESTRICTIONS**
  - Meeting expectations = **0.98-1.00x** (neutral to slight LOSS)
  - Good performance = 1.00-1.02x (barely positive)
  - ONLY **LEGENDARY** moments justify 1.05x+ (defeating arc villain, transcendent moment)
  - Defeats are DEVASTATING = 0.30-0.50x

- **Top 25% (p75-p90)**: ⚠️ **VERY HIGH RESTRICTIONS**
  - Meeting expectations = 0.99-1.01x (nearly neutral)
  - Strong performance = 1.01-1.05x
  - Major victories = 1.05-1.15x
  - Defeats are harsh = 0.50-0.70x

- **Top 50% (p50-p75)**: ⚡ **MODERATE RESTRICTIONS**
  - Meeting expectations = 1.00-1.02x
  - Good performance = 1.02-1.08x
  - Strong victories = 1.08-1.20x
  - Defeats = 0.60-0.80x

- **Top 66% (p33-p50)**: ✓ **STANDARD SCALING**
  - Meeting expectations = 1.00-1.05x
  - Good moments = 1.05-1.15x
  - Strong victories = 1.15-1.30x

- **Bottom 33% (p0-p33)**: 🔥 **MODEST UNDERDOG BONUS**
  - Meeting expectations = 1.00-1.08x
  - Good performance = 1.08-1.18x
  - Strong showing = 1.18-1.30x (not 1.40x!)
  - Major upsets possible but rare = 1.35x max

**The market RESISTS growth at the top! Exponential compounding is the enemy!**

📊 **MULTIPLIER RANGES:**
- **Inactive**: 1.0 (not in chapter OR mentioned positively but no direct action)
- **Small negative**: 0.90-0.98 (minor stumbles, overshadowed, small setbacks)
- **Small positive**: 1.02-1.10 (good moments, minor wins, solid character beats)
- **Medium negative**: 0.70-0.89 (meaningful failures, being outclassed, poor decisions)
- **Medium positive**: 1.11-1.30 (strong showing, important wins/moments, great character work)
- **Major defeat**: 0.40-0.69 (devastating loss, humiliation, arc villain defeated)
- **Major victory**: 1.31-1.70 (defeating major threat, transcendent character moment, epic win)
- **Catastrophic**: 0.10-0.39 (complete annihilation, total failure)
- **Legendary**: 1.71-3.00 (defeating arc villain, legendary moment, peak performance)

🔍 **USE "PAST CHANGES" AS CALIBRATION:**
- See how OTHER characters were valued for similar actions/moments
- Maintain consistency across characters and chapters
- Scale appropriately: bigger moments = bigger multipliers

📝 **OUTPUT FORMAT - MULTI-ACTION ARRAY:**
Characters do MULTIPLE things in a chapter. Track each significant action/moment separately!

Return JSON with an ARRAY of actions:
{
  "actions": [
    {
      "description": "Detailed description of what happened (e.g., 'Captures Luffy and taunts him publicly')",
      "multiplier": 1.15
    },
    {
      "description": "Another action (e.g., 'Gets outsmarted by Nami and loses the treasure')",
      "multiplier": 0.85
    }
  ],
  "confidence": 0.85,
  "reasoning": "Overall summary of how these actions combine"
}

**IMPORTANT**: 
- List actions in CHRONOLOGICAL ORDER (beginning → end of chapter)
- Each action gets its own multiplier
- Final stock = current_stock × (action1_mult × action2_mult × ... × actionN_mult)
- This creates a TUG-OF-WAR effect! Gaining upper hand then losing still affects stock!"""

        # Format recent history
        history_text = ""
        if character.get('recent_history'):
            history_text = "\nRECENT HISTORY (previous chapters only):\n"
            for event in character['recent_history'][:3]:
                # Calculate multiplier from history
                stock_after = event.get('current_stock', 0)
                delta = event.get('stock_change', 0)
                if stock_after > 0 and delta != 0:
                    stock_before = stock_after - delta
                    if stock_before > 0:
                        multiplier = stock_after / stock_before
                        history_text += f"- Ch. {event['chapter_id']}: {multiplier:.2f}x → {event['description']}\n"
                    else:
                        history_text += f"- Ch. {event['chapter_id']}: {event['description']}\n"
                else:
                    history_text += f"- Ch. {event['chapter_id']}: {event['description']}\n"
        
        # Build top stocks list
        stats = market_context.get('statistics', {})
        market_avg = stats.get('average', 50)
        
        top_stocks_text = ""
        if market_context.get('top_ten'):
            top_stocks_text = "\nTOP 10 STOCKS (from previous chapters):\n"
            for i, char in enumerate(market_context['top_ten'][:10], 1):
                top_stocks_text += f"  {i}. {char['character_name']}: {char['stock_value']:.0f}\n"
        
        # Build chapter character history
        chapter_history_text = ""
        if market_context.get('chapter_character_history'):
            chapter_history_text = "\nPAST CHANGES FOR CHARACTERS IN THIS CHAPTER (last 3 changes per character):\n"
            for hist in market_context['chapter_character_history'][:15]:  # Limit to 15 entries
                if hist.get('multiplier') is None:
                    # New character
                    chapter_history_text += f"  • {hist['character_name']} (Ch.{hist['chapter_id']}): NEW at {hist.get('initial_value', 0):.0f} → {hist.get('reasoning', '')}\n"
                else:
                    # Existing character with multiplier
                    chapter_history_text += f"  • {hist['character_name']} (Ch.{hist['chapter_id']}): {hist['multiplier']:.2f}x → {hist.get('reasoning', '')}\n"
        
        # Calculate percentile-based expectation tier
        current_stock = character['current_stock']
        p90 = stats.get('p90', market_avg * 2)
        p75 = stats.get('p75', market_avg * 1.5)
        p50 = stats.get('p50', market_avg)
        p33 = stats.get('p33', market_avg * 0.8)
        
        if current_stock >= p90:
            expectation_tier = "🚫 TOP 10% (p90+) - EXTREME RESTRICTIONS! Meeting expectations = 0.98-1.00x, good = 1.00-1.02x, ONLY legendary = 1.05x+"
        elif current_stock >= p75:
            expectation_tier = "⚠️ TOP 25% (p75-p90) - VERY HIGH RESTRICTIONS! Meeting = 0.99-1.01x, strong = 1.01-1.05x, major wins = 1.05-1.15x"
        elif current_stock >= p50:
            expectation_tier = "⚡ TOP 50% (p50-p75) - MODERATE RESTRICTIONS! Meeting = 1.00-1.02x, good = 1.02-1.08x, strong = 1.08-1.20x"
        elif current_stock >= p33:
            expectation_tier = "✓ TOP 66% (p33-p50) - STANDARD SCALING! Meeting = 1.00-1.05x, good = 1.05-1.15x, strong = 1.15-1.30x"
        else:
            expectation_tier = "🔥 BOTTOM 33% (p0-p33) - MODEST UNDERDOG BONUS! Meeting = 1.00-1.08x, good = 1.08-1.18x, strong = 1.18-1.30x"
        
        user_prompt = f"""EXISTING CHARACTER: {character['name']}
Current stock: {character['current_stock']:.1f}
Expectation tier: {expectation_tier}

Chapter {chapter_data['chapter_id']}: {chapter_data['title']}

MARKET CONTEXT (from previous chapters):
📊 PERCENTILES: p10={stats.get('p10', 0):.0f} | p25={stats.get('p25', 0):.0f} | p33={stats.get('p33', 0):.0f} | p50={stats.get('p50', 0):.0f} | p66={stats.get('p66', 0):.0f} | p75={stats.get('p75', 0):.0f} | p90={stats.get('p90', 0):.0f} | p99={stats.get('p99', 0):.0f}
- Average: {market_avg:.0f} | Median: {stats.get('median', 0):.0f}
- Total characters: {stats.get('total_characters', 0)}
{top_stocks_text}
{chapter_history_text}
{history_text}
CHAPTER SUMMARY:
{chapter_data['raw_description']}

What actions/moments did {character['name']} have in this chapter?
⚠️ REMEMBER: 
- Apply EXPECTATION SCALING based on their tier above!
- List ALL significant actions chronologically
- Each action gets its own multiplier
Return JSON: {{"actions": [{{"description": "...", "multiplier": X.XX}}, ...], "confidence": 0-1, "reasoning": "..."}}"""

        for attempt in range(1, max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7
                )
                
                content = response.choices[0].message.content
                result = json.loads(content)
                
                # Parse actions array
                actions = result.get('actions', [])
                if not actions:
                    raise ValueError("No actions returned")
                
                # Validate and calculate final multiplier
                final_multiplier = 1.0
                for action in actions:
                    mult = float(action['multiplier'])
                    if mult < 0.05 or mult > 5.0:
                        raise ValueError(f"Action multiplier out of range: {mult}")
                    final_multiplier *= mult
                
                confidence = float(result['confidence'])
                if confidence < 0 or confidence > 1:
                    confidence = max(0, min(1, confidence))
                
                reasoning = result['reasoning']
                
                # Save log
                self._save_character_log(character['name'], chapter_data['chapter_id'],
                                        'EXISTING', system_prompt, user_prompt, content, True)
                
                return {
                    'character_name': character['name'],
                    'character_href': character['href'],
                    'stock_change': final_multiplier,
                    'actions': actions,  # Include individual actions
                    'confidence': confidence,
                    'reasoning': reasoning
                }
                
            except Exception as e:
                # Save failed log
                self._save_character_log(character['name'], chapter_data['chapter_id'],
                                        'EXISTING', system_prompt, user_prompt,
                                        f"Error: {e}", False)
                
                if attempt >= max_retries:
                    print(f"❌ Failed to analyze EXISTING {character['name']}: {e}")
                    # Return neutral
                    return {
                        'character_name': character['name'],
                        'character_href': character['href'],
                        'stock_change': 1.0,
                        'actions': [{'description': 'Failed analysis', 'multiplier': 1.0}],
                        'confidence': 0.3,
                        'reasoning': f"Failed analysis, using neutral (1.0) ({e})"
                    }
    
    def analyze_chapter(self, chapter_data: Dict, market_context: Dict,
                       temperature: float = 0.7, verbose: bool = False, max_retries: int = 3) -> List[Dict]:
        """
        Analyze a chapter and get stock changes (NEW APPROACH: per-character calls).
        
        Args:
            chapter_data: Chapter information
            market_context: Market state before this chapter
            temperature: LLM temperature (unused, kept for compatibility)
            verbose: If True, print progress
            max_retries: Maximum number of attempts per character
            
        Returns:
            List of stock change dicts
        """
        # Step 1: Filter characters
        all_chars = market_context.get('existing_characters', []) + market_context.get('new_characters', [])
        filtered_chars = self.filter_characters(all_chars, chapter_data, verbose=verbose)
        
        # Split into new and existing based on filtered list
        filtered_hrefs = {c['href'] for c in filtered_chars}
        existing_chars = [c for c in market_context.get('existing_characters', []) if c['href'] in filtered_hrefs]
        new_chars = [c for c in market_context.get('new_characters', []) if c['href'] in filtered_hrefs]
        
        if verbose:
            print(f"📊 {len(existing_chars)} existing + ⭐ {len(new_chars)} new = {len(filtered_chars)} total")
        
        # Step 2: Analyze each character separately
        results = []
        
        for char in existing_chars:
            if verbose:
                print(f"  📊 {char['name']}... ", end='', flush=True)
            result = self.analyze_existing_character(char, chapter_data, market_context, verbose=False, max_retries=max_retries)
            results.append(result)
            if verbose:
                actions = result.get('actions', [])
                print(f"{result['stock_change']:.2f}x ({len(actions)} action{'s' if len(actions) != 1 else ''})")
                # Print each action
                for i, action in enumerate(actions, 1):
                    print(f"       {i}. {action.get('description', 'No description')} → {action.get('multiplier', 1.0):.2f}x")
                print(f"     └─ {result.get('reasoning', 'No reasoning provided')}")
        
        for char in new_chars:
            if verbose:
                print(f"  ⭐ {char['name']}... ", end='', flush=True)
            result = self.analyze_new_character(char, chapter_data, market_context, verbose=False, max_retries=max_retries)
            results.append(result)
            if verbose:
                print(f"{result['stock_change']:.0f}")
                print(f"     └─ {result.get('reasoning', 'No reasoning provided')}")
        
        return results


if __name__ == "__main__":
    # Test the analyzer
    analyzer = LLMAnalyzer()
    
    # Test with mock data
    chapter_data = {
        'chapter_id': 1,
        'title': 'Romance Dawn',
        'arc_name': 'Romance Dawn Arc',
        'raw_description': 'Monkey D. Luffy, a young boy, dreams of becoming the Pirate King...'
    }
    
    market_context = {
        'top_ten': [],
        'statistics': {'average': 0, 'median': 0, 'total_characters': 0},
        'existing_characters': [],
        'new_characters': [
            {'name': 'Monkey D. Luffy', 'href': '/wiki/Monkey_D._Luffy'},
            {'name': 'Shanks', 'href': '/wiki/Shanks'}
        ]
    }
    
    print("Testing new per-character approach...")
    results = analyzer.analyze_chapter(chapter_data, market_context, verbose=True)
    print(f"\nResults: {results}")
