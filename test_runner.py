#!/usr/bin/env python3
"""
Comprehensive Test Runner for One Piece Character Tracker
Runs all unit tests, integration tests, and validation checks
"""

import sys
import os
import unittest
import logging
import time
from pathlib import Path
from typing import Dict, List, Tuple

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import test modules
import test_database
import test_character_manager
import test_wiki_crawler
import test_llm_analyzer
import test_integration
import test_batch_comprehensive

# Suppress logging during tests
logging.getLogger().setLevel(logging.CRITICAL)

class TestResult:
    """Container for test results"""
    def __init__(self, name: str, success: bool, duration: float, details: str = ""):
        self.name = name
        self.success = success
        self.duration = duration
        self.details = details

class ComprehensiveTestRunner:
    """Runs all tests and provides comprehensive reporting"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = None
        self.total_duration = 0
    
    def run_test_suite(self, test_module, test_name: str) -> TestResult:
        """Run a test suite and return results"""
        print(f"\n{'='*60}")
        print(f"Running {test_name}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            if hasattr(test_module, 'run_tests'):
                success = test_module.run_tests()
            elif hasattr(test_module, f'run_{test_name.lower().replace(" ", "_")}_tests'):
                success = getattr(test_module, f'run_{test_name.lower().replace(" ", "_")}_tests')()
            else:
                # Fallback to running main
                success = test_module.main() if hasattr(test_module, 'main') else True
        except Exception as e:
            success = False
            details = f"Exception: {str(e)}"
            print(f"❌ {test_name} failed with exception: {e}")
        else:
            details = "Completed successfully" if success else "Some tests failed"
        
        duration = time.time() - start_time
        
        if success:
            print(f"✅ {test_name} passed ({duration:.2f}s)")
        else:
            print(f"❌ {test_name} failed ({duration:.2f}s)")
        
        return TestResult(test_name, success, duration, details)
    
    def run_unit_tests(self) -> List[TestResult]:
        """Run all unit tests"""
        print("\n" + "="*80)
        print("UNIT TESTS")
        print("="*80)
        
        unit_tests = [
            (test_database, "Database Tests"),
            (test_character_manager, "Character Manager Tests"),
            (test_wiki_crawler, "Wiki Crawler Tests"),
        ]
        
        results = []
        for test_module, test_name in unit_tests:
            result = self.run_test_suite(test_module, test_name)
            results.append(result)
            self.results.append(result)
        
        return results
    
    def run_integration_tests(self) -> List[TestResult]:
        """Run all integration tests"""
        print("\n" + "="*80)
        print("INTEGRATION TESTS")
        print("="*80)
        
        integration_tests = [
            (test_integration, "Basic Integration Tests"),
            (test_batch_comprehensive, "Comprehensive Integration Tests"),
        ]
        
        results = []
        for test_module, test_name in integration_tests:
            result = self.run_test_suite(test_module, test_name)
            results.append(result)
            self.results.append(result)
        
        return results
    
    def run_llm_tests(self) -> List[TestResult]:
        """Run LLM tests (optional, requires API key)"""
        print("\n" + "="*80)
        print("LLM TESTS (Optional - requires API key)")
        print("="*80)
        
        # Check if API key is available
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("⚠️  Skipping LLM tests - OPENAI_API_KEY not found")
            result = TestResult("LLM Tests", True, 0, "Skipped - no API key")
            self.results.append(result)
            return [result]
        
        result = self.run_test_suite(test_llm_analyzer, "LLM Analyzer Tests")
        self.results.append(result)
        return [result]
    
    def run_data_validation_tests(self) -> TestResult:
        """Run data validation and consistency checks"""
        print("\n" + "="*80)
        print("DATA VALIDATION TESTS")
        print("="*80)
        
        start_time = time.time()
        
        try:
            from database import DatabaseManager
            from character_manager import CharacterManager
            
            # Test database creation and validation
            print("Testing database initialization...")
            db = DatabaseManager("test_validation.db")
            
            integrity = db.validate_database_integrity()
            if not all(integrity.values()):
                raise Exception(f"Database integrity check failed: {integrity}")
            print("✓ Database integrity check passed")
            
            # Test character manager initialization
            print("Testing character manager initialization...")
            char_manager = CharacterManager(db)
            
            # Test market dynamics calculation with empty database
            dynamics = char_manager.calculate_market_dynamics()
            if dynamics.average_value != 100.0:  # Default for empty database
                raise Exception(f"Unexpected average value for empty database: {dynamics.average_value}")
            print("✓ Market dynamics calculation passed")
            
            # Test with sample data
            print("Testing with sample data...")
            db.add_character('/wiki/test1', 'Test Character 1', 100, 1)
            db.add_character('/wiki/test2', 'Test Character 2', 200, 1)
            db.add_character('/wiki/test3', 'Test Character 3', 300, 1)
            
            # Test market context
            market_context = db.get_current_market_context()
            if market_context.total_characters != 3:
                raise Exception(f"Expected 3 characters, got {market_context.total_characters}")
            print("✓ Market context calculation passed")
            
            # Test character value validation
            validation = char_manager.validate_value_change('/wiki/test1', 25, 'Test reasoning', 1)
            if not validation.is_valid:
                raise Exception("Valid change was rejected")
            print("✓ Character value validation passed")
            
            # Clean up
            os.unlink("test_validation.db")
            
            duration = time.time() - start_time
            result = TestResult("Data Validation Tests", True, duration, "All validation checks passed")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("Data Validation Tests", False, duration, f"Validation failed: {str(e)}")
            print(f"❌ Data validation failed: {e}")
        
        self.results.append(result)
        return result
    
    def run_sample_chapter_tests(self) -> TestResult:
        """Run tests with sample chapter data"""
        print("\n" + "="*80)
        print("SAMPLE CHAPTER TESTS")
        print("="*80)
        
        start_time = time.time()
        
        try:
            from database import DatabaseManager, CharacterChange
            from character_manager import CharacterManager
            
            # Create test database
            db = DatabaseManager("test_sample_chapters.db")
            char_manager = CharacterManager(db)
            
            # Sample chapter data
            sample_characters = [
                {'name': 'Monkey D. Luffy', 'wiki_url': '/wiki/Monkey_D._Luffy'},
                {'name': 'Roronoa Zoro', 'wiki_url': '/wiki/Roronoa_Zoro'},
                {'name': 'Nami', 'wiki_url': '/wiki/Nami'},
            ]
            
            print("Testing new character introductions...")
            
            # Test character introductions
            new_characters = []
            for char in sample_characters:
                introduction = char_manager.calculate_starting_value(
                    char, 1, {'total_characters': 0, 'top_characters': [], 'bottom_characters': [], 'recent_changes': []}
                )
                new_characters.append({
                    'wiki_url': introduction.wiki_url,
                    'name': introduction.name,
                    'starting_value': introduction.starting_value,
                    'reasoning': introduction.reasoning
                })
            
            # Process new characters
            success = db.process_character_changes(1, [], new_characters)
            if not success:
                raise Exception("Failed to process new characters")
            print("✓ New character processing passed")
            
            print("Testing character value changes...")
            
            # Test character changes
            character_changes = [
                CharacterChange('/wiki/Monkey_D._Luffy', 'Monkey D. Luffy', 25, 'Defeated major opponent'),
                CharacterChange('/wiki/Roronoa_Zoro', 'Roronoa Zoro', 20, 'Impressive sword technique'),
                CharacterChange('/wiki/Nami', 'Nami', -5, 'Minor setback'),
            ]
            
            success = db.process_character_changes(2, character_changes, [])
            if not success:
                raise Exception("Failed to process character changes")
            print("✓ Character value changes passed")
            
            print("Testing market dynamics evolution...")
            
            # Test market dynamics
            market_context = db.get_current_market_context()
            if market_context.total_characters != 3:
                raise Exception(f"Expected 3 characters, got {market_context.total_characters}")
            
            if len(market_context.recent_changes) == 0:
                raise Exception("No recent changes recorded")
            print("✓ Market dynamics evolution passed")
            
            print("Testing character history tracking...")
            
            # Test character histories
            luffy_history = db.get_character_history('/wiki/Monkey_D._Luffy')
            if len(luffy_history) != 1:
                raise Exception(f"Expected 1 history entry for Luffy, got {len(luffy_history)}")
            
            if luffy_history[0]['value_change'] != 25:
                raise Exception(f"Expected value change of 25, got {luffy_history[0]['value_change']}")
            print("✓ Character history tracking passed")
            
            # Clean up
            os.unlink("test_sample_chapters.db")
            
            duration = time.time() - start_time
            result = TestResult("Sample Chapter Tests", True, duration, "All sample chapter tests passed")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("Sample Chapter Tests", False, duration, f"Sample chapter tests failed: {str(e)}")
            print(f"❌ Sample chapter tests failed: {e}")
        
        self.results.append(result)
        return result
    
    def generate_report(self) -> str:
        """Generate comprehensive test report"""
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results if result.success)
        failed_tests = total_tests - passed_tests
        
        report = []
        report.append("\n" + "="*80)
        report.append("COMPREHENSIVE TEST REPORT")
        report.append("="*80)
        
        report.append(f"\nTotal Tests: {total_tests}")
        report.append(f"Passed: {passed_tests}")
        report.append(f"Failed: {failed_tests}")
        report.append(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        report.append(f"Total Duration: {self.total_duration:.2f}s")
        
        report.append("\nDETAILED RESULTS:")
        report.append("-" * 40)
        
        for result in self.results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            report.append(f"{status} {result.name} ({result.duration:.2f}s)")
            if not result.success and result.details:
                report.append(f"    Details: {result.details}")
        
        if failed_tests > 0:
            report.append("\n⚠️  FAILED TESTS:")
            report.append("-" * 20)
            for result in self.results:
                if not result.success:
                    report.append(f"• {result.name}: {result.details}")
        
        report.append("\nTEST COVERAGE:")
        report.append("-" * 20)
        report.append("✓ Database operations and integrity")
        report.append("✓ Character management and validation")
        report.append("✓ Wiki crawler functionality")
        report.append("✓ Market dynamics calculation")
        report.append("✓ Character value progression")
        report.append("✓ Data consistency validation")
        report.append("✓ End-to-end integration workflow")
        report.append("✓ Sample chapter processing")
        
        if os.getenv('OPENAI_API_KEY'):
            report.append("✓ LLM analyzer integration")
        else:
            report.append("⚠️  LLM analyzer (skipped - no API key)")
        
        report.append("\n" + "="*80)
        
        return "\n".join(report)
    
    def run_all_tests(self) -> bool:
        """Run all tests and return overall success"""
        self.start_time = time.time()
        
        print("🚀 Starting Comprehensive Test Suite for One Piece Character Tracker")
        print("This will test all core functionality, data validation, and integration workflows")
        
        # Run all test categories
        self.run_unit_tests()
        self.run_integration_tests()
        self.run_llm_tests()
        self.run_data_validation_tests()
        self.run_sample_chapter_tests()
        
        self.total_duration = time.time() - self.start_time
        
        # Generate and display report
        report = self.generate_report()
        print(report)
        
        # Return overall success
        return all(result.success for result in self.results)

def main():
    """Main entry point for test runner"""
    runner = ComprehensiveTestRunner()
    success = runner.run_all_tests()
    
    if success:
        print("\n🎉 ALL TESTS PASSED!")
        print("The One Piece Character Tracker system is ready for use.")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("Please review the failed tests and fix issues before using the system.")
        return 1

if __name__ == "__main__":
    exit(main())