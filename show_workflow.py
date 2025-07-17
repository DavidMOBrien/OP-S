#!/usr/bin/env python3
"""
Script to demonstrate the exact LLM workflow and processing
"""

from llm_analyzer import LLMAnalyzer, LLMConfig, CharacterAnalysis
import json

# Create mock analyzer to show response processing
class MockLLMAnalyzer(LLMAnalyzer):
    def __init__(self, config):
        self.config = config
    
    def show_response_processing(self):
        # This is what the LLM would typically respond with
        mock_llm_response = '''```json
{
  "character_changes": [
    {
      "wiki_url": "/wiki/Monkey_D._Luffy",
      "name": "Monkey D. Luffy",
      "value_change": 35,
      "reasoning": "Major victory against Arlong, a 20 million bounty fishman. Showed incredible determination and willpower, destroyed Arlong Park, and established himself as a serious threat. This is a defining moment that proves his strength."
    },
    {
      "wiki_url": "/wiki/Arlong",
      "name": "Arlong",
      "value_change": -25,
      "reasoning": "Defeated by Luffy despite being the arc's main antagonist. Lost his stronghold, crew scattered, and reputation destroyed. Major loss for a character who was previously dominant."
    },
    {
      "wiki_url": "/wiki/Nami",
      "name": "Nami",
      "value_change": 15,
      "reasoning": "Finally freed from Arlong's control and officially joins the Straw Hat crew. Character development moment as she learns to trust and rely on her friends."
    }
  ],
  "new_characters": [],
  "analysis_summary": "Major power shift as Luffy defeats his first major antagonist, establishing the Straw Hats as a legitimate crew. Arlong's defeat marks the end of his reign of terror."
}
```'''
        
        # Sample character data for validation
        chapter_character_values = [
            {
                'name': 'Monkey D. Luffy',
                'wiki_url': '/wiki/Monkey_D._Luffy',
                'current_value': 125,
                'exists_in_db': True,
                'recent_activity': []
            },
            {
                'name': 'Arlong',
                'wiki_url': '/wiki/Arlong',
                'current_value': 180,
                'exists_in_db': True,
                'recent_activity': []
            },
            {
                'name': 'Nami',
                'wiki_url': '/wiki/Nami',
                'current_value': 85,
                'exists_in_db': True,
                'recent_activity': []
            }
        ]
        
        print('=' * 80)
        print('RAW LLM RESPONSE:')
        print('=' * 80)
        print(mock_llm_response)
        print()
        
        print('=' * 80)
        print('PROCESSING STEPS:')
        print('=' * 80)
        
        # Step 1: Clean the response
        print('STEP 1: Cleaning JSON response...')
        cleaned = self._clean_json_response(mock_llm_response)
        print('✓ Removed markdown formatting')
        print('✓ Extracted pure JSON')
        print()
        
        # Step 2: Parse JSON
        print('STEP 2: Parsing JSON...')
        try:
            data = json.loads(cleaned)
            print('✓ JSON parsed successfully')
            print(f'✓ Found {len(data.get("character_changes", []))} character changes')
            print(f'✓ Found {len(data.get("new_characters", []))} new characters')
        except Exception as e:
            print(f'✗ JSON parsing failed: {e}')
            return
        print()
        
        # Step 3: Validate and process
        print('STEP 3: Validating character changes...')
        character_changes = data.get('character_changes', [])
        validated_changes = self._validate_character_changes(character_changes, chapter_character_values)
        
        for i, change in enumerate(validated_changes):
            print(f'✓ Change {i+1}: {change["name"]} {change["value_change"]:+d}')
            print(f'  - Wiki URL: {change["wiki_url"]}')
            print(f'  - Reasoning: {change["reasoning"][:60]}...')
        print()
        
        # Step 4: Show final result
        print('STEP 4: Final processed result...')
        
        analysis = CharacterAnalysis(
            character_changes=validated_changes,
            new_characters=data.get('new_characters', []),
            analysis_reasoning=data.get('analysis_summary', '')
        )
        
        print(f'✓ Analysis complete!')
        print(f'  - Character changes: {len(analysis.character_changes)}')
        print(f'  - New characters: {len(analysis.new_characters)}')
        print(f'  - Summary: {analysis.analysis_reasoning}')
        print()
        
        print('=' * 80)
        print('DATABASE STORAGE:')
        print('=' * 80)
        print('The validated changes would then be stored in the database:')
        for change in analysis.character_changes:
            current_val = next(c['current_value'] for c in chapter_character_values if c['wiki_url'] == change['wiki_url'])
            new_val = current_val + change['value_change']
            print(f'• {change["name"]}: {current_val} → {new_val} ({change["value_change"]:+d})')
        print()

if __name__ == "__main__":
    config = LLMConfig()
    analyzer = MockLLMAnalyzer(config)
    analyzer.show_response_processing()