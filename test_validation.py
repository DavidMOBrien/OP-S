#!/usr/bin/env python3
"""
Validation Tests for One Piece Character Tracker
Tests system with realistic sample data and validates results against expected outcomes
"""

import os
import json
import logging
import tempfile
from typing import Dict, List, Tuple
from database import DatabaseManager, CharacterChange
from character_manager import CharacterManager
from llm_analyzer import CharacterAnalysis

# Suppress logging during tests
logging.getLogger().setLevel(logging.CRITICAL)

class ValidationTestSuite:
    """Comprehensive validation tests with sample data"""
    
    def __init__(self):
        self.temp_db = None
        self.db_manager = None
        self.character_manager = None
        self.test_results = []
    
    def setup(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.db_manager = DatabaseManager(self.temp_db.name)
        self.character_manager = CharacterManager(self.db_manager)
        
        # Ensure clean database
        integrity = self.db_manager.validate_database_integrity()
        if not all(integrity.values()):
            raise Exception(f"Database setup failed: {integrity}")
    
    def teardown(self):
        """Clean up test environment"""
        if self.temp_db and os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def log_test_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details
        })
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
    
    def test_character_introduction_values(self):
        """Test that character starting values are realistic and properly scaled"""
        test_name = "Character Introduction Values"
        
        try:
            # Test different character types at different story points
            test_cases = [
                # Early story characters
                {
                    'character': {'name': 'Monkey D. Luffy', 'wiki_url': '/wiki/Monkey_D._Luffy'},
                    'chapter': 1,
                    'expected_range': (70, 120),  # Default 100 * 0.8 = 80
                    'description': 'Main character early introduction'
                },
                {
                    'character': {'name': 'Coby', 'wiki_url': '/wiki/Coby'},
                    'chapter': 1,
                    'expected_range': (70, 120),  # Default 100 * 0.8 = 80 (system doesn't detect weak characters by name)
                    'description': 'Regular character early introduction'
                },
                # Mid-story characters
                {
                    'character': {'name': 'Crocodile Shichibukai', 'wiki_url': '/wiki/Crocodile'},
                    'chapter': 200,
                    'expected_range': (500, 700),  # Shichibukai 600 * 1.0 = 600
                    'description': 'Shichibukai mid-story'
                },
                # Late-story characters
                {
                    'character': {'name': 'Kaido Yonko', 'wiki_url': '/wiki/Kaido'},
                    'chapter': 800,
                    'expected_range': (1000, 1000),  # Yonko 850 * 2.0 = 1700, but capped at 1000
                    'description': 'Yonko late-story introduction'
                }
            ]
            
            market_context = {
                'total_characters': 0,
                'top_characters': [],
                'bottom_characters': [],
                'recent_changes': []
            }
            
            all_passed = True
            details = []
            
            for case in test_cases:
                introduction = self.character_manager.calculate_starting_value(
                    case['character'], case['chapter'], market_context
                )
                
                min_val, max_val = case['expected_range']
                if min_val <= introduction.starting_value <= max_val:
                    details.append(f"✓ {case['description']}: {introduction.starting_value} (expected {min_val}-{max_val})")
                else:
                    details.append(f"✗ {case['description']}: {introduction.starting_value} (expected {min_val}-{max_val})")
                    all_passed = False
            
            self.log_test_result(test_name, all_passed, "; ".join(details))
            
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    def test_character_value_changes(self):
        """Test that character value changes are validated and adjusted appropriately"""
        test_name = "Character Value Changes"
        
        try:
            # Add test characters
            self.db_manager.add_character('/wiki/luffy', 'Monkey D. Luffy', 150, 1)
            self.db_manager.add_character('/wiki/weak_char', 'Weak Character', 30, 1)
            self.db_manager.add_character('/wiki/strong_char', 'Strong Character', 800, 1)
            
            test_cases = [
                # Valid changes
                {
                    'character': '/wiki/luffy',
                    'change': 25,
                    'reasoning': 'Defeated major boss in epic battle',
                    'should_be_valid': True,
                    'description': 'Valid moderate increase'
                },
                {
                    'character': '/wiki/luffy',
                    'change': -10,
                    'reasoning': 'Lost fight against stronger opponent',
                    'should_be_valid': True,
                    'description': 'Valid moderate decrease'
                },
                # Changes that should be adjusted
                {
                    'character': '/wiki/weak_char',
                    'change': 200,  # Too large for weak character
                    'reasoning': 'Minor appearance',
                    'should_be_adjusted': True,
                    'description': 'Excessive increase should be adjusted'
                },
                {
                    'character': '/wiki/strong_char',
                    'change': -500,  # Too large decrease
                    'reasoning': 'Lost badly',
                    'should_be_adjusted': True,
                    'description': 'Excessive decrease should be adjusted'
                }
            ]
            
            all_passed = True
            details = []
            
            for case in test_cases:
                validation = self.character_manager.validate_value_change(
                    case['character'], case['change'], case['reasoning'], 1
                )
                
                if case.get('should_be_valid', False):
                    if validation.is_valid:
                        details.append(f"✓ {case['description']}")
                    else:
                        details.append(f"✗ {case['description']} - incorrectly rejected")
                        all_passed = False
                
                elif case.get('should_be_adjusted', False):
                    if validation.adjusted_change != case['change']:
                        details.append(f"✓ {case['description']} - adjusted from {case['change']} to {validation.adjusted_change}")
                    else:
                        details.append(f"✗ {case['description']} - not adjusted")
                        all_passed = False
            
            self.log_test_result(test_name, all_passed, "; ".join(details))
            
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    def test_market_dynamics_calculation(self):
        """Test market dynamics calculation with various character distributions"""
        test_name = "Market Dynamics Calculation"
        
        try:
            # Add characters with different value ranges
            characters = [
                ('/wiki/char1', 'Weak Character 1', 25, 1),
                ('/wiki/char2', 'Weak Character 2', 40, 1),
                ('/wiki/char3', 'Mid Character 1', 150, 1),
                ('/wiki/char4', 'Mid Character 2', 200, 1),
                ('/wiki/char5', 'Strong Character 1', 500, 1),
                ('/wiki/char6', 'Strong Character 2', 600, 1),
                ('/wiki/char7', 'Top Character 1', 850, 1),
                ('/wiki/char8', 'Top Character 2', 900, 1),
            ]
            
            for url, name, value, chapter in characters:
                self.db_manager.add_character(url, name, value, chapter)
            
            # Calculate market dynamics
            dynamics = self.character_manager.calculate_market_dynamics()
            
            # Validate calculations
            expected_average = sum(char[2] for char in characters) / len(characters)
            
            checks = [
                (abs(dynamics.average_value - expected_average) < 1.0, f"Average value calculation: {dynamics.average_value:.1f} vs expected {expected_average:.1f}"),
                (dynamics.median_value > 0, f"Median value: {dynamics.median_value}"),
                (len(dynamics.value_distribution) > 0, f"Value distribution: {len(dynamics.value_distribution)} ranges"),
                (dynamics.top_tier_threshold > dynamics.mid_tier_threshold, f"Tier thresholds: top={dynamics.top_tier_threshold}, mid={dynamics.mid_tier_threshold}"),
            ]
            
            all_passed = all(check[0] for check in checks)
            details = [check[1] for check in checks]
            
            self.log_test_result(test_name, all_passed, "; ".join(details))
            
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    def test_character_progression_workflow(self):
        """Test complete character progression through multiple chapters"""
        test_name = "Character Progression Workflow"
        
        try:
            # Chapter 1: Introduce characters
            new_characters_ch1 = [
                {'wiki_url': '/wiki/luffy', 'name': 'Monkey D. Luffy', 'starting_value': 100, 'reasoning': 'Main character introduction'},
                {'wiki_url': '/wiki/zoro', 'name': 'Roronoa Zoro', 'starting_value': 90, 'reasoning': 'Strong fighter introduction'},
                {'wiki_url': '/wiki/nami', 'name': 'Nami', 'starting_value': 60, 'reasoning': 'Navigator introduction'},
            ]
            
            success = self.db_manager.process_character_changes(1, [], new_characters_ch1)
            if not success:
                raise Exception("Failed to process Chapter 1 characters")
            
            # Chapter 2: Character developments
            character_changes_ch2 = [
                CharacterChange('/wiki/luffy', 'Monkey D. Luffy', 25, 'Defeated major opponent'),
                CharacterChange('/wiki/zoro', 'Roronoa Zoro', 20, 'Impressive sword technique'),
                CharacterChange('/wiki/nami', 'Nami', -5, 'Captured by enemies'),
            ]
            
            success = self.db_manager.process_character_changes(2, character_changes_ch2, [])
            if not success:
                raise Exception("Failed to process Chapter 2 changes")
            
            # Chapter 3: More developments
            character_changes_ch3 = [
                CharacterChange('/wiki/luffy', 'Monkey D. Luffy', 15, 'Showed leadership'),
                CharacterChange('/wiki/nami', 'Nami', 30, 'Emotional backstory reveal and character development'),
            ]
            
            new_characters_ch3 = [
                {'wiki_url': '/wiki/sanji', 'name': 'Sanji', 'starting_value': 85, 'reasoning': 'Cook and fighter introduction'},
            ]
            
            success = self.db_manager.process_character_changes(3, character_changes_ch3, new_characters_ch3)
            if not success:
                raise Exception("Failed to process Chapter 3 changes")
            
            # Validate final state
            luffy = self.db_manager.get_character('/wiki/luffy')
            zoro = self.db_manager.get_character('/wiki/zoro')
            nami = self.db_manager.get_character('/wiki/nami')
            sanji = self.db_manager.get_character('/wiki/sanji')
            
            checks = [
                (luffy.current_value == 140, f"Luffy final value: {luffy.current_value} (expected 140)"),  # 100 + 25 + 15
                (zoro.current_value == 110, f"Zoro final value: {zoro.current_value} (expected 110)"),    # 90 + 20
                (nami.current_value == 85, f"Nami final value: {nami.current_value} (expected 85)"),      # 60 - 5 + 30
                (sanji.current_value == 85, f"Sanji final value: {sanji.current_value} (expected 85)"),   # Starting value
            ]
            
            # Check histories
            luffy_history = self.db_manager.get_character_history('/wiki/luffy')
            nami_history = self.db_manager.get_character_history('/wiki/nami')
            
            checks.extend([
                (len(luffy_history) == 2, f"Luffy history entries: {len(luffy_history)} (expected 2)"),
                (len(nami_history) == 2, f"Nami history entries: {len(nami_history)} (expected 2)"),
            ])
            
            all_passed = all(check[0] for check in checks)
            details = [check[1] for check in checks]
            
            self.log_test_result(test_name, all_passed, "; ".join(details))
            
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    def test_market_context_evolution(self):
        """Test that market context evolves correctly as characters are added and changed"""
        test_name = "Market Context Evolution"
        
        try:
            # Start with empty market
            initial_context = self.db_manager.get_current_market_context()
            if initial_context.total_characters != 0:
                raise Exception(f"Expected empty market, got {initial_context.total_characters} characters")
            
            # Add first batch of characters
            batch1 = [
                {'wiki_url': '/wiki/char1', 'name': 'Character 1', 'starting_value': 100, 'reasoning': 'First character'},
                {'wiki_url': '/wiki/char2', 'name': 'Character 2', 'starting_value': 200, 'reasoning': 'Second character'},
            ]
            
            self.db_manager.process_character_changes(1, [], batch1)
            
            context_after_batch1 = self.db_manager.get_current_market_context()
            
            # Add character changes
            changes = [
                CharacterChange('/wiki/char1', 'Character 1', 50, 'Major improvement'),
                CharacterChange('/wiki/char2', 'Character 2', -25, 'Minor setback'),
            ]
            
            self.db_manager.process_character_changes(2, changes, [])
            
            context_after_changes = self.db_manager.get_current_market_context()
            
            # Add more characters
            batch2 = [
                {'wiki_url': '/wiki/char3', 'name': 'Character 3', 'starting_value': 300, 'reasoning': 'Third character'},
            ]
            
            self.db_manager.process_character_changes(3, [], batch2)
            
            final_context = self.db_manager.get_current_market_context()
            
            # Validate evolution
            checks = [
                (context_after_batch1.total_characters == 2, f"After batch 1: {context_after_batch1.total_characters} characters"),
                (context_after_changes.total_characters == 2, f"After changes: {context_after_changes.total_characters} characters"),
                (final_context.total_characters == 3, f"Final: {final_context.total_characters} characters"),
                (len(final_context.recent_changes) > 0, f"Recent changes tracked: {len(final_context.recent_changes)}"),
                (len(final_context.top_characters) == 3, f"Top characters: {len(final_context.top_characters)}"),
            ]
            
            # Check that top character is correct
            if final_context.top_characters:
                top_char = final_context.top_characters[0]
                expected_top_value = 300  # Character 3
                checks.append((top_char['current_value'] == expected_top_value, f"Top character value: {top_char['current_value']} (expected {expected_top_value})"))
            
            all_passed = all(check[0] for check in checks)
            details = [check[1] for check in checks]
            
            self.log_test_result(test_name, all_passed, "; ".join(details))
            
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    def test_data_consistency_validation(self):
        """Test data consistency and integrity validation"""
        test_name = "Data Consistency Validation"
        
        try:
            # Add test data
            characters = [
                {'wiki_url': '/wiki/test1', 'name': 'Test Character 1', 'starting_value': 100, 'reasoning': 'Test'},
                {'wiki_url': '/wiki/test2', 'name': 'Test Character 2', 'starting_value': 200, 'reasoning': 'Test'},
            ]
            
            self.db_manager.process_character_changes(1, [], characters)
            
            # Add character changes
            changes = [
                CharacterChange('/wiki/test1', 'Test Character 1', 25, 'Test change'),
                CharacterChange('/wiki/test2', 'Test Character 2', -15, 'Test change'),
            ]
            
            self.db_manager.process_character_changes(2, changes, [])
            
            # Validate database integrity
            integrity = self.db_manager.validate_database_integrity()
            
            # Get all characters and verify consistency
            all_characters = self.db_manager.get_all_characters()
            
            consistency_checks = []
            
            for character in all_characters:
                # Check character history consistency
                history = self.db_manager.get_character_history(character.wiki_url)
                if history:
                    # Most recent history entry should match current value
                    latest_entry = history[0]  # DESC order
                    if latest_entry['new_value'] != character.current_value:
                        consistency_checks.append(f"History inconsistency for {character.name}: current={character.current_value}, history={latest_entry['new_value']}")
                
                # Check value bounds
                if character.current_value < 1 or character.current_value > 1000:
                    consistency_checks.append(f"Value out of bounds for {character.name}: {character.current_value}")
            
            # Check market context consistency
            market_context = self.db_manager.get_current_market_context()
            if market_context.total_characters != len(all_characters):
                consistency_checks.append(f"Market context character count mismatch: {market_context.total_characters} vs {len(all_characters)}")
            
            checks = [
                (all(integrity.values()), f"Database integrity: {integrity}"),
                (len(consistency_checks) == 0, f"Consistency issues: {consistency_checks}"),
                (len(all_characters) > 0, f"Characters in database: {len(all_characters)}"),
            ]
            
            all_passed = all(check[0] for check in checks)
            details = [check[1] for check in checks]
            
            self.log_test_result(test_name, all_passed, "; ".join(details))
            
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    def test_edge_cases_and_error_handling(self):
        """Test edge cases and error handling"""
        test_name = "Edge Cases and Error Handling"
        
        try:
            checks = []
            
            # Test empty database operations
            empty_market = self.db_manager.get_current_market_context()
            checks.append((empty_market.total_characters == 0, "Empty database market context"))
            
            # Test non-existent character operations
            non_existent = self.db_manager.get_character('/wiki/nonexistent')
            checks.append((non_existent is None, "Non-existent character returns None"))
            
            # Test invalid character addition
            invalid_add = self.db_manager.add_character('', '', 0, 0)
            checks.append((not invalid_add, "Invalid character addition rejected"))
            
            # Test character value validation with extreme values
            self.db_manager.add_character('/wiki/test_extreme', 'Test Character', 500, 1)
            
            extreme_validation = self.character_manager.validate_value_change(
                '/wiki/test_extreme', 1000, 'Extreme change', 1
            )
            checks.append((extreme_validation.adjusted_change < 1000, f"Extreme change adjusted: {extreme_validation.adjusted_change}"))
            
            # Test duplicate character handling
            duplicate_add = self.db_manager.add_character('/wiki/test_extreme', 'Duplicate', 100, 1)
            checks.append((not duplicate_add, "Duplicate character addition rejected"))
            
            # Test market dynamics with single character
            single_char_dynamics = self.character_manager.calculate_market_dynamics()
            checks.append((single_char_dynamics.average_value > 0, f"Single character dynamics: avg={single_char_dynamics.average_value}"))
            
            all_passed = all(check[0] for check in checks)
            details = []
            
            # Add pass/fail indicators to details
            for check_passed, check_desc in checks:
                status = "✓" if check_passed else "✗"
                details.append(f"{status} {check_desc}")
            
            self.log_test_result(test_name, all_passed, "; ".join(details))
            
        except Exception as e:
            self.log_test_result(test_name, False, f"Exception: {str(e)}")
    
    def run_single_test(self, test_method):
        """Run a single test with proper setup and teardown"""
        self.setup()
        try:
            test_method()
        finally:
            self.teardown()
    
    def run_all_validation_tests(self) -> bool:
        """Run all validation tests"""
        print("🔍 Running Validation Tests with Sample Data")
        print("=" * 60)
        
        # List of test methods to run
        test_methods = [
            self.test_character_introduction_values,
            self.test_character_value_changes,
            self.test_market_dynamics_calculation,
            self.test_character_progression_workflow,
            self.test_market_context_evolution,
            self.test_data_consistency_validation,
            self.test_edge_cases_and_error_handling,
        ]
        
        # Run each test with fresh database
        for test_method in test_methods:
            self.run_single_test(test_method)
        
        # Generate summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        
        print("\n" + "=" * 60)
        print("VALIDATION TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests < total_tests:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"❌ {result['test']}: {result['details']}")
        
        return passed_tests == total_tests

def main():
    """Main entry point for validation tests"""
    validator = ValidationTestSuite()
    success = validator.run_all_validation_tests()
    
    if success:
        print("\n🎉 All validation tests passed!")
        print("The system correctly handles sample data and maintains consistency.")
        return 0
    else:
        print("\n❌ Some validation tests failed!")
        print("Please review the issues before using the system.")
        return 1

if __name__ == "__main__":
    exit(main())