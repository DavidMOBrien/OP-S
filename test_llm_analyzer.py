#!/usr/bin/env python3
"""
Test script for LLM Analyzer
Tests the LLM integration with sample data
"""

import os
import logging
from dotenv import load_dotenv
from llm_analyzer import LLMAnalyzer, LLMConfig

def setup_logging():
    """Configure logging for testing"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def test_llm_analyzer():
    """Test the LLM analyzer with sample chapter data"""
    logger = setup_logging()
    
    # Load environment variables
    load_dotenv()
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error("OPENAI_API_KEY not found in environment variables")
        logger.info("Please create a .env file with your OpenAI API key:")
        logger.info("OPENAI_API_KEY=your_api_key_here")
        return False
    
    try:
        # Create LLM analyzer with test configuration
        config = LLMConfig(
            model="gpt-4",
            temperature=0.3,
            max_tokens=1500,
            max_retries=2
        )
        
        analyzer = LLMAnalyzer(api_key=api_key, config=config)
        logger.info("LLM Analyzer initialized successfully")
        
        # Test with sample chapter data
        test_chapter_data = {
            'number': 95,
            'title': 'Arlong Park Arc - Final Battle',
            'summary': '''Luffy faces off against Arlong in the final battle of the Arlong Park arc. 
            Despite being severely beaten, Luffy shows incredible determination and refuses to give up. 
            He destroys Arlong Park with his Gomu Gomu no Ono attack, finally defeating Arlong and 
            freeing Nami and the villagers from his tyranny. This victory establishes Luffy as a 
            serious threat and shows his unwavering loyalty to his crew members.'''
        }
        
        test_character_values = [
            {
                'name': 'Monkey D. Luffy',
                'wiki_url': '/wiki/Monkey_D._Luffy',
                'current_value': 125,
                'exists_in_db': True,
                'recent_activity': [
                    {
                        'chapter': 92,
                        'value_change': 10,
                        'reasoning': 'Inspired villagers to fight back against Arlong',
                        'new_value': 125
                    },
                    {
                        'chapter': 90,
                        'value_change': -5,
                        'reasoning': 'Got beaten badly by Arlong initially',
                        'new_value': 115
                    }
                ]
            },
            {
                'name': 'Arlong',
                'wiki_url': '/wiki/Arlong',
                'current_value': 180,
                'exists_in_db': True,
                'recent_activity': [
                    {
                        'chapter': 92,
                        'value_change': 15,
                        'reasoning': 'Dominated Luffy in their first encounter',
                        'new_value': 180
                    }
                ]
            },
            {
                'name': 'Nami',
                'wiki_url': '/wiki/Nami',
                'current_value': 85,
                'exists_in_db': True,
                'recent_activity': [
                    {
                        'chapter': 93,
                        'value_change': 20,
                        'reasoning': 'Emotional backstory reveal and character development',
                        'new_value': 85
                    }
                ]
            }
        ]
        
        test_market_context = {
            'total_characters': 25,
            'top_characters': [
                {'name': 'Dracule Mihawk', 'value': 800, 'wiki_url': '/wiki/Dracule_Mihawk'},
                {'name': 'Shanks', 'value': 750, 'wiki_url': '/wiki/Shanks'},
                {'name': 'Smoker', 'value': 300, 'wiki_url': '/wiki/Smoker'},
                {'name': 'Arlong', 'value': 180, 'wiki_url': '/wiki/Arlong'},
                {'name': 'Monkey D. Luffy', 'value': 125, 'wiki_url': '/wiki/Monkey_D._Luffy'}
            ],
            'bottom_characters': [
                {'name': 'Coby', 'value': 15, 'wiki_url': '/wiki/Coby'},
                {'name': 'Helmeppo', 'value': 12, 'wiki_url': '/wiki/Helmeppo'},
                {'name': 'Villager A', 'value': 8, 'wiki_url': '/wiki/Villager_A'}
            ],
            'recent_changes': [
                {'character': 'Nami', 'chapter': 93, 'change': 20, 'reason': 'Backstory reveal', 'new_value': 85},
                {'character': 'Arlong', 'chapter': 92, 'change': 15, 'reason': 'Dominated Luffy', 'new_value': 180},
                {'character': 'Luffy', 'chapter': 92, 'change': 10, 'reason': 'Inspired villagers', 'new_value': 125}
            ]
        }
        
        logger.info("Starting LLM analysis test...")
        
        # Analyze the chapter
        result = analyzer.analyze_chapter(test_chapter_data, test_character_values, test_market_context)
        
        if result:
            logger.info("✓ LLM Analysis completed successfully!")
            
            print("\n" + "="*60)
            print("LLM ANALYSIS RESULTS")
            print("="*60)
            
            print(f"\nChapter {test_chapter_data['number']}: {test_chapter_data['title']}")
            print(f"Analysis Summary: {result.analysis_reasoning}")
            
            if result.character_changes:
                print(f"\nCharacter Value Changes ({len(result.character_changes)}):")
                for change in result.character_changes:
                    print(f"  • {change['name']}: {change['value_change']:+d} points")
                    print(f"    Reasoning: {change['reasoning']}")
                    print(f"    Wiki URL: {change['wiki_url']}")
                    print()
            else:
                print("\nNo character value changes identified.")
            
            if result.new_characters:
                print(f"New Characters Introduced ({len(result.new_characters)}):")
                for new_char in result.new_characters:
                    print(f"  • {new_char['name']}: {new_char['starting_value']} points")
                    print(f"    Reasoning: {new_char['reasoning']}")
                    print(f"    Wiki URL: {new_char['wiki_url']}")
                    print()
            else:
                print("No new characters introduced.")
            
            print("="*60)
            
            # Validate the response structure
            validation_passed = True
            
            # Check character changes format
            for change in result.character_changes:
                required_fields = ['wiki_url', 'name', 'value_change', 'reasoning']
                for field in required_fields:
                    if field not in change:
                        logger.error(f"Missing field '{field}' in character change")
                        validation_passed = False
                
                # Check if wiki_url is valid format
                if not change['wiki_url'].startswith('/wiki/'):
                    logger.error(f"Invalid wiki URL format: {change['wiki_url']}")
                    validation_passed = False
                
                # Check if value_change is reasonable
                if abs(change['value_change']) > 100:
                    logger.warning(f"Large value change detected: {change['value_change']}")
            
            # Check new characters format
            for new_char in result.new_characters:
                required_fields = ['wiki_url', 'name', 'starting_value', 'reasoning']
                for field in required_fields:
                    if field not in new_char:
                        logger.error(f"Missing field '{field}' in new character")
                        validation_passed = False
            
            if validation_passed:
                logger.info("✓ Response validation passed!")
                return True
            else:
                logger.error("✗ Response validation failed!")
                return False
        else:
            logger.error("✗ LLM Analysis failed!")
            return False
            
    except Exception as e:
        logger.error(f"Error testing LLM analyzer: {e}")
        return False

if __name__ == "__main__":
    success = test_llm_analyzer()
    if success:
        print("\n🎉 LLM Analyzer test completed successfully!")
    else:
        print("\n❌ LLM Analyzer test failed!")
        exit(1)