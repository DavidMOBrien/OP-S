#!/usr/bin/env python3
"""
Character Management System for One Piece Character Tracker
Handles character identification, value scaling, market dynamics, and validation
"""

import logging
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime
import re
import math

logger = logging.getLogger(__name__)

@dataclass
class CharacterIntroduction:
    """Data for a new character introduction"""
    wiki_url: str
    name: str
    starting_value: int
    reasoning: str
    chapter_number: int

@dataclass
class ValueChangeValidation:
    """Result of value change validation"""
    is_valid: bool
    adjusted_change: int
    validation_notes: List[str]

@dataclass
class MarketDynamics:
    """Current market state and dynamics"""
    average_value: float
    median_value: float
    value_distribution: Dict[str, int]  # ranges like "0-50", "51-100", etc.
    recent_volatility: float
    top_tier_threshold: int
    mid_tier_threshold: int

class CharacterManager:
    """Manages character identification, scaling, and market dynamics"""
    
    def __init__(self, database_manager):
        """Initialize character manager with database connection"""
        self.db = database_manager
        
        # Character tier thresholds (will be dynamically adjusted)
        self.tier_thresholds = {
            'legendary': 900,    # Roger, Whitebeard level
            'top_tier': 700,     # Yonko, Admiral level
            'high_tier': 500,    # Vice Admiral, Strong Captain level
            'mid_tier': 300,     # Captain, Strong Fighter level
            'low_tier': 100,     # Competent Fighter level
            'weak': 50           # Civilian, Weak Fighter level
        }
        
        # Value change limits by tier
        self.change_limits = {
            'legendary': {'max_increase': 50, 'max_decrease': 30},
            'top_tier': {'max_increase': 60, 'max_decrease': 40},
            'high_tier': {'max_increase': 70, 'max_decrease': 50},
            'mid_tier': {'max_increase': 80, 'max_decrease': 60},
            'low_tier': {'max_increase': 100, 'max_decrease': 80},
            'weak': {'max_increase': 150, 'max_decrease': 100}
        }
        
        logger.info("Character Manager initialized")
    
    def identify_character_duplicates(self, character_list: List[Dict]) -> Dict[str, List[Dict]]:
        """Identify potential duplicate characters using wiki URLs and name similarity"""
        duplicates = {}
        seen_urls = set()
        
        for char in character_list:
            wiki_url = char.get('wiki_url', '').strip()
            name = char.get('name', '').strip()
            
            if not wiki_url or not name:
                continue
            
            # Check for exact URL duplicates
            if wiki_url in seen_urls:
                if wiki_url not in duplicates:
                    duplicates[wiki_url] = []
                duplicates[wiki_url].append(char)
            else:
                seen_urls.add(wiki_url)
        
        # Check for name-based duplicates (different URLs, similar names)
        name_groups = self._group_similar_names(character_list)
        for group in name_groups:
            if len(group) > 1:
                # Multiple characters with similar names - potential duplicates
                urls = [char['wiki_url'] for char in group]
                key = f"similar_names_{hash(tuple(sorted(urls)))}"
                duplicates[key] = group
        
        if duplicates:
            logger.warning(f"Found {len(duplicates)} potential duplicate groups")
            for key, chars in duplicates.items():
                logger.warning(f"Duplicate group {key}: {[c['name'] for c in chars]}")
        
        return duplicates
    
    def _group_similar_names(self, character_list: List[Dict]) -> List[List[Dict]]:
        """Group characters with similar names"""
        groups = []
        processed = set()
        
        for i, char1 in enumerate(character_list):
            if i in processed:
                continue
            
            name1 = char1.get('name', '').strip()
            if not name1:
                continue
            
            group = [char1]
            processed.add(i)
            
            for j, char2 in enumerate(character_list[i+1:], i+1):
                if j in processed:
                    continue
                
                name2 = char2.get('name', '').strip()
                if not name2:
                    continue
                
                # Check for name similarity
                if self._are_names_similar(name1, name2):
                    group.append(char2)
                    processed.add(j)
            
            if len(group) > 1:
                groups.append(group)
        
        return groups
    
    def _are_names_similar(self, name1: str, name2: str) -> bool:
        """Check if two character names are similar enough to be duplicates"""
        # Normalize names
        norm1 = self._normalize_name(name1)
        norm2 = self._normalize_name(name2)
        
        # Exact match after normalization
        if norm1 == norm2:
            return True
        
        # Check if one is a substring of the other (for nicknames)
        if norm1 in norm2 or norm2 in norm1:
            return True
        
        # Check for common variations
        variations = [
            (r'\bD\.\s*', 'D. '),  # "D." spacing variations
            (r'\s+', ' '),          # Multiple spaces
            (r'["\']', ''),         # Quotes
        ]
        
        for pattern, replacement in variations:
            norm1_var = re.sub(pattern, replacement, norm1)
            norm2_var = re.sub(pattern, replacement, norm2)
            if norm1_var == norm2_var:
                return True
        
        return False
    
    def _normalize_name(self, name: str) -> str:
        """Normalize character name for comparison"""
        # Convert to lowercase, remove extra spaces and punctuation
        normalized = re.sub(r'[^\w\s]', '', name.lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized
    
    def calculate_starting_value(self, character_info: Dict, chapter_number: int, 
                               market_context: Dict) -> CharacterIntroduction:
        """Calculate appropriate starting value for a new character"""
        name = character_info.get('name', '')
        wiki_url = character_info.get('wiki_url', '')
        
        # Base starting value calculation
        base_value = self._calculate_base_starting_value(character_info, chapter_number, market_context)
        
        # Apply chapter progression scaling
        scaled_value = self._apply_chapter_scaling(base_value, chapter_number)
        
        # Apply market context adjustments
        final_value = self._apply_market_context_scaling(scaled_value, market_context)
        
        # Ensure reasonable bounds
        final_value = max(1, min(1000, final_value))
        
        reasoning = self._generate_starting_value_reasoning(
            character_info, chapter_number, base_value, scaled_value, final_value
        )
        
        return CharacterIntroduction(
            wiki_url=wiki_url,
            name=name,
            starting_value=final_value,
            reasoning=reasoning,
            chapter_number=chapter_number
        )
    
    def _calculate_base_starting_value(self, character_info: Dict, chapter_number: int, 
                                     market_context: Dict) -> int:
        """Calculate base starting value based on character information"""
        name = character_info.get('name', '').lower()
        
        # Character type detection based on name patterns
        if any(title in name for title in ['admiral', 'fleet admiral']):
            return 800  # Admiral level
        elif any(title in name for title in ['yonko', 'emperor', 'four emperors']):
            return 850  # Yonko level
        elif any(title in name for title in ['shichibukai', 'warlord']):
            return 600  # Warlord level
        elif any(title in name for title in ['vice admiral']):
            return 500  # Vice Admiral level
        elif any(title in name for title in ['captain', 'commodore']):
            return 300  # Captain level
        elif any(title in name for title in ['commander', 'division commander']):
            return 400  # Commander level
        elif any(title in name for title in ['supernova', 'worst generation']):
            return 350  # Supernova level
        elif any(title in name for title in ['revolutionary']):
            return 250  # Revolutionary level
        elif any(word in name for word in ['king', 'prince', 'princess']):
            return 200  # Royalty level
        elif any(word in name for word in ['doctor', 'dr.']):
            return 150  # Professional level
        elif any(word in name for word in ['giant']):
            return 180  # Giant race bonus
        elif any(word in name for word in ['fishman', 'fish-man']):
            return 120  # Fishman bonus
        elif any(word in name for word in ['mink']):
            return 110  # Mink bonus
        else:
            return 100  # Default starting value
    
    def _apply_chapter_scaling(self, base_value: int, chapter_number: int) -> int:
        """Apply scaling based on story progression"""
        # Early chapters (1-100): Lower scaling
        if chapter_number <= 100:
            scaling_factor = 0.8
        # East Blue to Alabasta (101-200): Normal scaling
        elif chapter_number <= 200:
            scaling_factor = 1.0
        # Sky Island to Water 7 (201-400): Slight increase
        elif chapter_number <= 400:
            scaling_factor = 1.2
        # Thriller Bark to Marineford (401-600): Higher scaling
        elif chapter_number <= 600:
            scaling_factor = 1.5
        # Post-timeskip (601-800): Much higher scaling
        elif chapter_number <= 800:
            scaling_factor = 2.0
        # New World advanced (801-1000): Very high scaling
        elif chapter_number <= 1000:
            scaling_factor = 2.5
        # Wano and beyond (1000+): Maximum scaling
        else:
            scaling_factor = 3.0
        
        return int(base_value * scaling_factor)
    
    def _apply_market_context_scaling(self, scaled_value: int, market_context: Dict) -> int:
        """Apply market context adjustments to starting value"""
        total_characters = market_context.get('total_characters', 0)
        top_characters = market_context.get('top_characters', [])
        
        # If market is empty, use base value
        if total_characters == 0:
            return scaled_value
        
        # Get current market average from top characters
        if top_characters:
            top_values = [char.get('current_value', char.get('value', 0)) for char in top_characters[:5]]
            market_average = sum(top_values) / len(top_values) if top_values else scaled_value
            
            # Adjust based on market average
            if scaled_value > market_average * 0.8:
                # High-tier character, ensure they're competitive
                return max(scaled_value, int(market_average * 0.9))
            elif scaled_value < market_average * 0.2:
                # Low-tier character, don't inflate too much
                return min(scaled_value, int(market_average * 0.3))
        
        return scaled_value
    
    def _generate_starting_value_reasoning(self, character_info: Dict, chapter_number: int,
                                         base_value: int, scaled_value: int, final_value: int) -> str:
        """Generate reasoning for starting value calculation"""
        name = character_info.get('name', '')
        
        reasoning_parts = [
            f"New character introduction in Chapter {chapter_number}."
        ]
        
        # Base value reasoning
        if base_value >= 800:
            reasoning_parts.append("Identified as top-tier character (Admiral/Yonko level).")
        elif base_value >= 600:
            reasoning_parts.append("Identified as high-tier character (Warlord/Commander level).")
        elif base_value >= 300:
            reasoning_parts.append("Identified as mid-tier character (Captain/Officer level).")
        elif base_value >= 150:
            reasoning_parts.append("Identified as competent fighter or professional.")
        else:
            reasoning_parts.append("Standard character introduction value.")
        
        # Scaling reasoning
        if scaled_value != base_value:
            scaling_factor = scaled_value / base_value
            if scaling_factor >= 2.0:
                reasoning_parts.append(f"Significant power scaling applied for late-story introduction ({scaling_factor:.1f}x).")
            elif scaling_factor >= 1.5:
                reasoning_parts.append(f"Moderate power scaling applied ({scaling_factor:.1f}x).")
            elif scaling_factor < 1.0:
                reasoning_parts.append(f"Early-story scaling applied ({scaling_factor:.1f}x).")
        
        # Final adjustments
        if final_value != scaled_value:
            if final_value > scaled_value:
                reasoning_parts.append("Market context adjustment increased value to remain competitive.")
            else:
                reasoning_parts.append("Market context adjustment prevented overvaluation.")
        
        return " ".join(reasoning_parts)
    
    def validate_value_change(self, character_wiki_url: str, proposed_change: int, 
                            reasoning: str, chapter_number: int) -> ValueChangeValidation:
        """Validate and potentially adjust a proposed value change"""
        validation_notes = []
        
        # Get current character info
        character = self.db.get_character(character_wiki_url)
        if not character:
            return ValueChangeValidation(
                is_valid=False,
                adjusted_change=0,
                validation_notes=["Character not found in database"]
            )
        
        current_value = character.current_value
        new_value = current_value + proposed_change
        
        # Determine character tier
        tier = self._get_character_tier(current_value)
        limits = self.change_limits[tier]
        
        # Check change magnitude limits
        adjusted_change = proposed_change
        if proposed_change > limits['max_increase']:
            adjusted_change = limits['max_increase']
            validation_notes.append(f"Capped increase from {proposed_change} to {adjusted_change} for {tier} tier")
        elif proposed_change < -limits['max_decrease']:
            adjusted_change = -limits['max_decrease']
            validation_notes.append(f"Capped decrease from {proposed_change} to {adjusted_change} for {tier} tier")
        
        # Check for unrealistic new values
        adjusted_new_value = current_value + adjusted_change
        if adjusted_new_value < 1:
            adjusted_change = 1 - current_value
            validation_notes.append("Prevented value from going below 1")
        elif adjusted_new_value > 1000:
            adjusted_change = 1000 - current_value
            validation_notes.append("Prevented value from exceeding 1000")
        
        # Check for consistency with recent changes
        recent_activity = self.db.get_character_recent_activity(character_wiki_url, 3)
        if recent_activity:
            recent_changes = [activity['value_change'] for activity in recent_activity]
            
            # Check for excessive volatility
            if len(recent_changes) >= 2:
                recent_volatility = sum(abs(change) for change in recent_changes[-2:])
                if abs(adjusted_change) > 50 and recent_volatility > 100:
                    adjusted_change = int(adjusted_change * 0.7)  # Reduce by 30%
                    validation_notes.append("Reduced change due to recent high volatility")
            
            # Check for unrealistic reversals
            if recent_changes and len(recent_changes) >= 1:
                last_change = recent_changes[0]
                if (last_change > 20 and adjusted_change < -20) or (last_change < -20 and adjusted_change > 20):
                    # Large reversal - reduce magnitude
                    adjusted_change = int(adjusted_change * 0.8)
                    validation_notes.append("Reduced change magnitude due to recent large reversal")
        
        # Validate reasoning quality
        reasoning_score = self._evaluate_reasoning_quality(reasoning)
        if reasoning_score < 0.5 and abs(adjusted_change) > 20:
            adjusted_change = int(adjusted_change * 0.8)
            validation_notes.append("Reduced change due to weak reasoning")
        
        is_valid = abs(adjusted_change) <= max(limits['max_increase'], limits['max_decrease'])
        
        return ValueChangeValidation(
            is_valid=is_valid,
            adjusted_change=adjusted_change,
            validation_notes=validation_notes
        )
    
    def _get_character_tier(self, current_value: int) -> str:
        """Determine character tier based on current value"""
        if current_value >= self.tier_thresholds['legendary']:
            return 'legendary'
        elif current_value >= self.tier_thresholds['top_tier']:
            return 'top_tier'
        elif current_value >= self.tier_thresholds['high_tier']:
            return 'high_tier'
        elif current_value >= self.tier_thresholds['mid_tier']:
            return 'mid_tier'
        elif current_value >= self.tier_thresholds['low_tier']:
            return 'low_tier'
        else:
            return 'weak'
    
    def _evaluate_reasoning_quality(self, reasoning: str) -> float:
        """Evaluate the quality of reasoning for a value change (0.0 to 1.0)"""
        if not reasoning or len(reasoning.strip()) < 10:
            return 0.0
        
        score = 0.0
        reasoning_lower = reasoning.lower()
        
        # Check for specific event types (higher quality)
        high_quality_indicators = [
            'defeated', 'victory', 'powerup', 'awakening', 'haki',
            'transformation', 'sacrifice', 'leadership', 'development',
            'backstory', 'reveal', 'bounty', 'intimidation', 'epic'
        ]
        
        medium_quality_indicators = [
            'fight', 'battle', 'technique', 'ability', 'strength',
            'performance', 'moment', 'display', 'showed', 'boss', 'major'
        ]
        
        low_quality_indicators = [
            'appeared', 'mentioned', 'present', 'seen'
        ]
        
        # Score based on indicators (allow multiple matches)
        high_matches = sum(1 for indicator in high_quality_indicators if indicator in reasoning_lower)
        medium_matches = sum(1 for indicator in medium_quality_indicators if indicator in reasoning_lower)
        low_matches = sum(1 for indicator in low_quality_indicators if indicator in reasoning_lower)
        
        score += high_matches * 0.25
        score += medium_matches * 0.15
        score += low_matches * 0.05
        
        # Length bonus (more detailed reasoning)
        if len(reasoning) > 50:
            score += 0.15
        if len(reasoning) > 100:
            score += 0.1
        
        # Base score for having any reasoning
        score += 0.1
        
        return min(1.0, score)
    
    def calculate_market_dynamics(self) -> MarketDynamics:
        """Calculate current market dynamics and statistics"""
        all_characters = self.db.get_all_characters()
        
        if not all_characters:
            return MarketDynamics(
                average_value=100.0,
                median_value=100.0,
                value_distribution={},
                recent_volatility=0.0,
                top_tier_threshold=700,
                mid_tier_threshold=300
            )
        
        values = [char.current_value for char in all_characters]
        
        # Calculate basic statistics
        average_value = sum(values) / len(values)
        sorted_values = sorted(values)
        median_value = sorted_values[len(sorted_values) // 2]
        
        # Calculate value distribution
        distribution_ranges = [
            (0, 50), (51, 100), (101, 200), (201, 300), (301, 500),
            (501, 700), (701, 900), (901, 1000)
        ]
        
        value_distribution = {}
        for min_val, max_val in distribution_ranges:
            count = sum(1 for val in values if min_val <= val <= max_val)
            range_key = f"{min_val}-{max_val}"
            value_distribution[range_key] = count
        
        # Calculate recent volatility
        recent_volatility = self._calculate_recent_volatility()
        
        # Update tier thresholds based on current distribution
        top_tier_threshold = max(700, int(sorted_values[int(len(sorted_values) * 0.9)]))
        mid_tier_threshold = max(300, int(sorted_values[int(len(sorted_values) * 0.6)]))
        
        return MarketDynamics(
            average_value=average_value,
            median_value=median_value,
            value_distribution=value_distribution,
            recent_volatility=recent_volatility,
            top_tier_threshold=top_tier_threshold,
            mid_tier_threshold=mid_tier_threshold
        )
    
    def _calculate_recent_volatility(self) -> float:
        """Calculate recent market volatility based on character changes"""
        recent_changes = self.db.get_recent_character_changes(10)  # Last 10 chapters
        
        if not recent_changes:
            return 0.0
        
        # Calculate average absolute change
        total_change = sum(abs(change['change']) for change in recent_changes)
        return total_change / len(recent_changes)
    
    def update_tier_thresholds(self, market_dynamics: MarketDynamics):
        """Update tier thresholds based on current market dynamics"""
        # Calculate thresholds based on market distribution
        top_tier = market_dynamics.top_tier_threshold
        mid_tier = market_dynamics.mid_tier_threshold
        
        # Ensure proper ordering by calculating from top down
        self.tier_thresholds['legendary'] = max(900, int(top_tier * 1.2))
        self.tier_thresholds['top_tier'] = max(700, top_tier)
        self.tier_thresholds['high_tier'] = max(500, int((top_tier + mid_tier) / 2))
        self.tier_thresholds['mid_tier'] = max(300, mid_tier)
        self.tier_thresholds['low_tier'] = max(100, int(mid_tier * 0.4))
        self.tier_thresholds['weak'] = max(50, int(mid_tier * 0.2))
        
        # Ensure proper ordering (each tier should be higher than the next)
        thresholds = ['legendary', 'top_tier', 'high_tier', 'mid_tier', 'low_tier', 'weak']
        for i in range(len(thresholds) - 1):
            current = thresholds[i]
            next_tier = thresholds[i + 1]
            if self.tier_thresholds[current] <= self.tier_thresholds[next_tier]:
                self.tier_thresholds[current] = self.tier_thresholds[next_tier] + 50
        
        logger.info(f"Updated tier thresholds: {self.tier_thresholds}")
    
    def maintain_character_histories(self, chapter_number: int) -> bool:
        """Maintain character histories and clean up old data if needed"""
        try:
            # Get database stats
            stats = self.db.get_database_stats()
            
            # If we have too many history entries, consider cleanup
            max_history_entries = 50000  # Reasonable limit
            if stats['total_history_entries'] > max_history_entries:
                logger.warning(f"History entries ({stats['total_history_entries']}) approaching limit")
                # Could implement cleanup logic here if needed
            
            # Validate data integrity
            integrity = self.db.validate_database_integrity()
            if not all(integrity.values()):
                logger.error(f"Database integrity issues detected: {integrity}")
                return False
            
            # Update market snapshot for this chapter
            market_context = self.db.get_current_market_context()
            success = self.db.save_market_snapshot(chapter_number, market_context)
            
            if success:
                logger.info(f"Maintained character histories for chapter {chapter_number}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error maintaining character histories: {e}")
            return False
    
    def get_character_recommendations(self, chapter_characters: List[Dict], 
                                   market_context: Dict) -> Dict[str, List[str]]:
        """Get recommendations for character analysis"""
        recommendations = {
            'focus_characters': [],
            'watch_characters': [],
            'new_introductions': [],
            'potential_duplicates': []
        }
        
        # Check for duplicates
        duplicates = self.identify_character_duplicates(chapter_characters)
        if duplicates:
            recommendations['potential_duplicates'] = list(duplicates.keys())
        
        # Identify characters to focus on
        for char in chapter_characters:
            wiki_url = char.get('wiki_url', '')
            name = char.get('name', '')
            
            if not wiki_url or not name:
                continue
            
            # Check if character exists in database
            existing_char = self.db.get_character(wiki_url)
            
            if not existing_char:
                recommendations['new_introductions'].append(name)
            else:
                # Check recent activity
                recent_activity = self.db.get_character_recent_activity(wiki_url, 3)
                if recent_activity:
                    recent_volatility = sum(abs(activity['value_change']) for activity in recent_activity)
                    if recent_volatility > 50:
                        recommendations['watch_characters'].append(name)
                
                # Check if character is in top/bottom tiers
                if (existing_char.current_value >= 700 or existing_char.current_value <= 50):
                    recommendations['focus_characters'].append(name)
        
        return recommendations

# Convenience function to create character manager
def create_character_manager(database_manager) -> CharacterManager:
    """Create and return a CharacterManager instance"""
    return CharacterManager(database_manager)

if __name__ == "__main__":
    # Test the character manager
    from database import create_database_manager
    
    db = create_database_manager()
    char_manager = create_character_manager(db)
    
    # Test market dynamics calculation
    market_dynamics = char_manager.calculate_market_dynamics()
    print("Market Dynamics:")
    print(f"  Average Value: {market_dynamics.average_value:.1f}")
    print(f"  Median Value: {market_dynamics.median_value:.1f}")
    print(f"  Recent Volatility: {market_dynamics.recent_volatility:.1f}")
    print(f"  Value Distribution: {market_dynamics.value_distribution}")
    
    # Test starting value calculation
    test_character = {
        'name': 'Test Admiral',
        'wiki_url': '/wiki/Test_Admiral'
    }
    
    market_context = {
        'total_characters': 10,
        'top_characters': [{'name': 'Top Char', 'current_value': 800}],
        'bottom_characters': [{'name': 'Bottom Char', 'current_value': 50}],
        'recent_changes': []
    }
    
    introduction = char_manager.calculate_starting_value(test_character, 500, market_context)
    print(f"\nTest Character Introduction:")
    print(f"  Name: {introduction.name}")
    print(f"  Starting Value: {introduction.starting_value}")
    print(f"  Reasoning: {introduction.reasoning}")
    
    print("\nCharacter Manager setup completed successfully!")