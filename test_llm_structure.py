#!/usr/bin/env python3
"""
Test script for LLM Analyzer structure and validation
Tests the LLM integration without making actual API calls
"""

import json
import logging
from llm_analyzer import LLMAnalyzer, LLMConfig, CharacterAnalysis

def setup_logging():
    """Configure logging for testing"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def test_llm_structure():
    """Test LLM analyzer structure and validation without API calls"""
    logger = setup_logging()
    
    try:
        # Test LLMConfig
        config = LLMConfig(
            model="gpt-4",
            temperature=0.3,
            max_tokens=1500,
            max_retries=2
        )
        logger.info("✓ LLMConfig created successfully")
        
        # Test prompt building without API calls
        # Create a mock analyzer (we'll test methods that don't require API)
        class MockLLMAnalyzer(LLMAnalyzer):
            def __init__(self, config):
                self.config = config
                # Skip API client initialization
            
            def _call_llm_with_retry(self, prompt):
                # Return mock response for testing
                return '''
                {
                  "character_changes": [
                    {
                      "wiki_url": "/wiki/Monkey_D._Luffy",
                      "name": "Monkey D. Luffy",
                      "value_change": 25,
                      "reasoning": "Defeated Arlong and showed incredible determination, major character development moment"
                    },
                    {
                      "wiki_url": "/wiki/Arlong",
                      "name": "Arlong",
                      "value_change": -30,
                      "reasoning": "Defeated by Luffy, lost his stronghold and reputation"
                    }
                  ],
                  "new_characters": [],
                  "analysis_summary": "Major victory for Luffy establishing him as a serious threat"
                }
                '''
        
        analyzer = MockLLMAnalyzer(config)
        logger.info("✓ Mock LLM Analyzer created successfully")
        
        # Test prompt building
        test_chapter_data = {
            'number': 95,
            'title': 'Arlong Park Arc - Final Battle',
            'summary': 'Luffy defeats Arlong in an epic battle.'
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
                        'reasoning': 'Inspired villagers',
                        'new_value': 125
                    }
                ]
            },
            {
                'name': 'Arlong',
                'wiki_url': '/wiki/Arlong',
                'current_value': 180,
                'exists_in_db': True,
                'recent_activity': []
            }
        ]
        
        test_market_context = {
            'total_characters': 25,
            'top_characters': [
                {'name': 'Dracule Mihawk', 'value': 800, 'wiki_url': '/wiki/Dracule_Mihawk'}
            ],
            'bottom_characters': [
                {'name': 'Coby', 'value': 15, 'wiki_url': '/wiki/Coby'}
            ],
            'recent_changes': [
                {'character': 'Luffy', 'chapter': 92, 'change': 10, 'reason': 'Inspired villagers', 'new_value': 125}
            ]
        }
        
        # Test prompt building
        prompt = analyzer._build_comprehensive_prompt(
            test_chapter_data, test_character_values, test_market_context
        )
        
        if prompt and len(prompt) > 100:
            logger.info("✓ Comprehensive prompt built successfully")
            logger.info(f"Prompt length: {len(prompt)} characters")
        else:
            logger.error("✗ Failed to build comprehensive prompt")
            return False
        
        # Test character context building
        char_context = analyzer._build_character_context(test_character_values)
        if "Monkey D. Luffy" in char_context and "Current Value: 125" in char_context:
            logger.info("✓ Character context built successfully")
        else:
            logger.error("✗ Failed to build character context")
            return False
        
        # Test market context building
        market_context_text = analyzer._build_market_context(test_market_context)
        if "Total Characters" in market_context_text and "Dracule Mihawk" in market_context_text:
            logger.info("✓ Market context built successfully")
        else:
            logger.error("✗ Failed to build market context")
            return False
        
        # Test JSON response parsing
        mock_response = '''
        {
          "character_changes": [
            {
              "wiki_url": "/wiki/Monkey_D._Luffy",
              "name": "Monkey D. Luffy",
              "value_change": 25,
              "reasoning": "Defeated Arlong and showed incredible determination"
            }
          ],
          "new_characters": [
            {
              "wiki_url": "/wiki/New_Character",
              "name": "New Character",
              "starting_value": 100,
              "reasoning": "Introduced as powerful new ally"
            }
          ],
          "analysis_summary": "Major developments in this chapter"
        }
        '''
        
        # Add new character to test data for validation
        test_character_values.append({
            'name': 'New Character',
            'wiki_url': '/wiki/New_Character',
            'current_value': None,
            'exists_in_db': False,
            'recent_activity': []
        })
        
        analysis = analyzer._parse_llm_response(mock_response, test_character_values)
        
        if analysis and isinstance(analysis, CharacterAnalysis):
            logger.info("✓ LLM response parsed successfully")
            logger.info(f"Character changes: {len(analysis.character_changes)}")
            logger.info(f"New characters: {len(analysis.new_characters)}")
            
            # Validate structure
            if analysis.character_changes:
                change = analysis.character_changes[0]
                required_fields = ['wiki_url', 'name', 'value_change', 'reasoning']
                if all(field in change for field in required_fields):
                    logger.info("✓ Character change structure validated")
                else:
                    logger.error("✗ Character change structure invalid")
                    return False
            
            if analysis.new_characters:
                new_char = analysis.new_characters[0]
                required_fields = ['wiki_url', 'name', 'starting_value', 'reasoning']
                if all(field in new_char for field in required_fields):
                    logger.info("✓ New character structure validated")
                else:
                    logger.error("✗ New character structure invalid")
                    return False
        else:
            logger.error("✗ Failed to parse LLM response")
            return False
        
        # Test JSON cleaning
        dirty_json = '''```json
        {
          "character_changes": [
            {
              "wiki_url": "/wiki/Test",
              "name": "Test",
              "value_change": 10,
              "reasoning": "Test reasoning"
            }
          ],
          "new_characters": [],
          "analysis_summary": "Test summary"
        }
        ```'''
        
        cleaned = analyzer._clean_json_response(dirty_json)
        try:
            json.loads(cleaned)
            logger.info("✓ JSON cleaning works correctly")
        except json.JSONDecodeError:
            logger.error("✗ JSON cleaning failed")
            return False
        
        # Test URL validation
        valid_urls = [
            "/wiki/Monkey_D._Luffy",
            "/wiki/Roronoa_Zoro",
            "https://onepiece.fandom.com/wiki/Nami"
        ]
        
        invalid_urls = [
            "/wiki/Category:Characters",
            "/wiki/File:Luffy.jpg",
            "/wiki/Template:Character",
            "not_a_wiki_url"
        ]
        
        for url in valid_urls:
            if not analyzer._is_valid_wiki_url(url):
                logger.error(f"✗ Valid URL rejected: {url}")
                return False
        
        for url in invalid_urls:
            if analyzer._is_valid_wiki_url(url):
                logger.error(f"✗ Invalid URL accepted: {url}")
                return False
        
        logger.info("✓ URL validation works correctly")
        
        logger.info("✓ All LLM analyzer structure tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"Error testing LLM analyzer structure: {e}")
        return False

if __name__ == "__main__":
    success = test_llm_structure()
    if success:
        print("\n🎉 LLM Analyzer structure test completed successfully!")
    else:
        print("\n❌ LLM Analyzer structure test failed!")
        exit(1)