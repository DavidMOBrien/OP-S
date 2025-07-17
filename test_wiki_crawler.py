#!/usr/bin/env python3
"""
Unit tests for Wiki Crawler module
Tests web scraping functionality, character extraction, and error handling
"""

import unittest
import logging
from unittest.mock import Mock, patch, MagicMock
from wiki_crawler import WikiCrawler

# Suppress logging during tests
logging.getLogger().setLevel(logging.CRITICAL)

class TestWikiCrawler(unittest.TestCase):
    """Test cases for WikiCrawler functionality"""
    
    def setUp(self):
        """Set up test crawler"""
        self.crawler = WikiCrawler(rate_limit=0)  # No rate limiting for tests
    
    def test_crawler_initialization(self):
        """Test crawler initialization"""
        self.assertIsNotNone(self.crawler.session)
        self.assertEqual(self.crawler.rate_limit, 0)
        self.assertIn('User-Agent', self.crawler.session.headers)
    
    @patch('wiki_crawler.requests.Session.get')
    def test_successful_chapter_scraping(self, mock_get):
        """Test successful chapter scraping with mock data"""
        # Mock HTML response
        mock_html = """
        <html>
            <head><title>Chapter 1 | One Piece Wiki | Fandom</title></head>
            <body>
                <h1 class="page-header__title">Chapter 1</h1>
                <div class="mw-parser-output">
                    <p>Monkey D. Luffy begins his journey as a pirate. He demonstrates his rubber powers 
                    and shows determination to become the Pirate King. He meets Coby and helps him escape 
                    from Alvida's ship.</p>
                    
                    <div class="portable-infobox">
                        <div data-source="characters">
                            <div class="pi-data-value">
                                <a href="/wiki/Monkey_D._Luffy" title="Monkey D. Luffy">Monkey D. Luffy</a>,
                                <a href="/wiki/Coby" title="Coby">Coby</a>,
                                <a href="/wiki/Alvida" title="Alvida">Alvida</a>
                            </div>
                        </div>
                    </div>
                    
                    <a href="/wiki/Chapter_2" title="Chapter 2">Next Chapter</a>
                </div>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test scraping
        result = self.crawler.scrape_chapter_page("https://onepiece.fandom.com/wiki/Chapter_1")
        
        # Verify results
        self.assertIsNotNone(result)
        self.assertEqual(result['number'], 1)
        self.assertEqual(result['title'], 'Chapter 1')
        self.assertIn('Luffy', result['summary'])
        self.assertGreater(len(result['characters']), 0)
        
        # Check character extraction
        character_names = [char['name'] for char in result['characters']]
        self.assertIn('Monkey D. Luffy', character_names)
        self.assertIn('Coby', character_names)
        self.assertIn('Alvida', character_names)
        
        # Check wiki URLs
        for char in result['characters']:
            self.assertTrue(char['wiki_url'].startswith('/wiki/'))
    
    @patch('wiki_crawler.requests.Session.get')
    def test_chapter_scraping_with_minimal_content(self, mock_get):
        """Test chapter scraping with minimal content"""
        mock_html = """
        <html>
            <head><title>Chapter 999 | One Piece Wiki | Fandom</title></head>
            <body>
                <h1 class="page-header__title">Chapter 999</h1>
                <div class="mw-parser-output">
                    <p>Short chapter summary.</p>
                </div>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.crawler.scrape_chapter_page("https://onepiece.fandom.com/wiki/Chapter_999")
        
        self.assertIsNotNone(result)
        self.assertEqual(result['number'], 999)
        self.assertEqual(result['title'], 'Chapter 999')
        self.assertEqual(result['summary'], 'Short chapter summary.')
        self.assertEqual(len(result['characters']), 0)  # No characters found
    
    @patch('wiki_crawler.requests.Session.get')
    def test_network_error_handling(self, mock_get):
        """Test handling of network errors"""
        # Test connection error
        mock_get.side_effect = Exception("Connection failed")
        
        result = self.crawler.scrape_chapter_page("https://onepiece.fandom.com/wiki/Chapter_1")
        self.assertIsNone(result)
        
        # Test HTTP error
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.side_effect = None
        mock_get.return_value = mock_response
        
        result = self.crawler.scrape_chapter_page("https://onepiece.fandom.com/wiki/Chapter_1")
        self.assertIsNone(result)
    
    def test_chapter_number_extraction(self):
        """Test chapter number extraction from URLs"""
        test_cases = [
            ("https://onepiece.fandom.com/wiki/Chapter_1", 1),
            ("https://onepiece.fandom.com/wiki/Chapter_100", 100),
            ("https://onepiece.fandom.com/wiki/Chapter_1000", 1000),
            ("https://onepiece.fandom.com/wiki/Chapter_1001", 1001),
        ]
        
        for url, expected_number in test_cases:
            number = self.crawler._extract_chapter_number(url)
            self.assertEqual(number, expected_number)
        
        # Test invalid URLs
        invalid_urls = [
            "https://onepiece.fandom.com/wiki/SomeOtherPage",
            "https://example.com/Chapter_1",
            "invalid_url",
            ""
        ]
        
        for url in invalid_urls:
            number = self.crawler._extract_chapter_number(url)
            self.assertIsNone(number)
    
    def test_character_extraction_methods(self):
        """Test different character extraction methods"""
        # Test infobox extraction
        infobox_html = """
        <div class="portable-infobox">
            <div data-source="characters">
                <div class="pi-data-value">
                    <a href="/wiki/Luffy" title="Luffy">Luffy</a>,
                    <a href="/wiki/Zoro" title="Zoro">Zoro</a>
                </div>
            </div>
        </div>
        """
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(infobox_html, 'html.parser')
        characters = self.crawler._extract_characters_from_infobox(soup)
        
        self.assertEqual(len(characters), 2)
        self.assertEqual(characters[0]['name'], 'Luffy')
        self.assertEqual(characters[0]['wiki_url'], '/wiki/Luffy')
        
        # Test content extraction
        content_html = """
        <div class="mw-parser-output">
            <p><a href="/wiki/Monkey_D._Luffy" title="Monkey D. Luffy">Luffy</a> fights 
            <a href="/wiki/Arlong" title="Arlong">Arlong</a> in this chapter.</p>
        </div>
        """
        
        soup = BeautifulSoup(content_html, 'html.parser')
        characters = self.crawler._extract_characters_from_content(soup)
        
        self.assertGreaterEqual(len(characters), 2)
        character_names = [char['name'] for char in characters]
        self.assertIn('Monkey D. Luffy', character_names)
        self.assertIn('Arlong', character_names)
    
    def test_character_filtering(self):
        """Test character filtering logic"""
        test_characters = [
            {'name': 'Monkey D. Luffy', 'wiki_url': '/wiki/Monkey_D._Luffy'},
            {'name': 'Category:Characters', 'wiki_url': '/wiki/Category:Characters'},  # Should be filtered
            {'name': 'File:Luffy.png', 'wiki_url': '/wiki/File:Luffy.png'},  # Should be filtered
            {'name': 'Roronoa Zoro', 'wiki_url': '/wiki/Roronoa_Zoro'},
            {'name': 'Template:Infobox', 'wiki_url': '/wiki/Template:Infobox'},  # Should be filtered
            {'name': 'Sanji', 'wiki_url': '/wiki/Sanji'},
        ]
        
        filtered_characters = self.crawler._filter_characters(test_characters)
        
        # Should only have the actual character pages
        self.assertEqual(len(filtered_characters), 3)
        character_names = [char['name'] for char in filtered_characters]
        self.assertIn('Monkey D. Luffy', character_names)
        self.assertIn('Roronoa Zoro', character_names)
        self.assertIn('Sanji', character_names)
        self.assertNotIn('Category:Characters', character_names)
        self.assertNotIn('File:Luffy.png', character_names)
        self.assertNotIn('Template:Infobox', character_names)
    
    def test_duplicate_character_removal(self):
        """Test removal of duplicate characters"""
        test_characters = [
            {'name': 'Monkey D. Luffy', 'wiki_url': '/wiki/Monkey_D._Luffy'},
            {'name': 'Luffy', 'wiki_url': '/wiki/Monkey_D._Luffy'},  # Same URL, different name
            {'name': 'Roronoa Zoro', 'wiki_url': '/wiki/Roronoa_Zoro'},
            {'name': 'Roronoa Zoro', 'wiki_url': '/wiki/Roronoa_Zoro'},  # Exact duplicate
            {'name': 'Sanji', 'wiki_url': '/wiki/Sanji'},
        ]
        
        deduplicated = self.crawler._remove_duplicate_characters(test_characters)
        
        # Should have 3 unique characters (by wiki_url)
        self.assertEqual(len(deduplicated), 3)
        
        # Check that we kept the first occurrence of each URL
        wiki_urls = [char['wiki_url'] for char in deduplicated]
        self.assertEqual(len(set(wiki_urls)), 3)  # All unique URLs
    
    def test_summary_extraction_and_cleaning(self):
        """Test summary extraction and cleaning"""
        test_html = """
        <div class="mw-parser-output">
            <p>This is the first paragraph of the chapter summary.</p>
            <p>This is the second paragraph with more details.</p>
            <div class="navbox">Navigation content to ignore</div>
            <p>This is the third paragraph.</p>
            <table class="infobox">Infobox content to ignore</table>
            <p>Final paragraph of the summary.</p>
        </div>
        """
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(test_html, 'html.parser')
        summary = self.crawler._extract_chapter_summary(soup)
        
        # Should extract all paragraph text
        self.assertIn('first paragraph', summary)
        self.assertIn('second paragraph', summary)
        self.assertIn('third paragraph', summary)
        self.assertIn('Final paragraph', summary)
        
        # Should not include navigation or infobox content
        self.assertNotIn('Navigation content', summary)
        self.assertNotIn('Infobox content', summary)
        
        # Should be properly formatted
        self.assertGreater(len(summary), 50)  # Should have substantial content
    
    def test_next_chapter_link_extraction(self):
        """Test extraction of next chapter links"""
        test_html = """
        <div class="mw-parser-output">
            <p>Chapter content here.</p>
            <div class="chapter-navigation">
                <a href="/wiki/Chapter_2" title="Chapter 2">Next Chapter</a>
            </div>
        </div>
        """
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(test_html, 'html.parser')
        next_url = self.crawler._extract_next_chapter_url(soup)
        
        self.assertEqual(next_url, '/wiki/Chapter_2')
        
        # Test when no next chapter link exists
        no_next_html = """
        <div class="mw-parser-output">
            <p>Final chapter content.</p>
        </div>
        """
        
        soup = BeautifulSoup(no_next_html, 'html.parser')
        next_url = self.crawler._extract_next_chapter_url(soup)
        self.assertIsNone(next_url)
    
    @patch('wiki_crawler.time.sleep')
    def test_rate_limiting(self, mock_sleep):
        """Test rate limiting functionality"""
        crawler_with_limit = WikiCrawler(rate_limit=1.0)
        
        # Mock successful response
        with patch('wiki_crawler.requests.Session.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "<html><body><h1>Test</h1></body></html>"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # Make two requests
            crawler_with_limit.scrape_chapter_page("https://onepiece.fandom.com/wiki/Chapter_1")
            crawler_with_limit.scrape_chapter_page("https://onepiece.fandom.com/wiki/Chapter_2")
            
            # Should have called sleep once (after first request)
            mock_sleep.assert_called_with(1.0)
    
    def test_error_recovery_and_logging(self):
        """Test error recovery and logging functionality"""
        # Test with invalid HTML
        with patch('wiki_crawler.requests.Session.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "Invalid HTML content"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = self.crawler.scrape_chapter_page("https://onepiece.fandom.com/wiki/Chapter_1")
            
            # Should handle gracefully and return None or minimal data
            if result is not None:
                # If it returns something, it should at least have basic structure
                self.assertIn('number', result)
                self.assertIn('title', result)
                self.assertIn('summary', result)
                self.assertIn('characters', result)

class TestWikiCrawlerIntegration(unittest.TestCase):
    """Integration tests for WikiCrawler with real data structure"""
    
    def setUp(self):
        """Set up integration test crawler"""
        self.crawler = WikiCrawler(rate_limit=0)
    
    def test_chapter_data_structure_validation(self):
        """Test that scraped data has the expected structure"""
        # Mock a complete chapter response
        with patch('wiki_crawler.requests.Session.get') as mock_get:
            mock_html = """
            <html>
                <head><title>Chapter 1 | One Piece Wiki | Fandom</title></head>
                <body>
                    <h1 class="page-header__title">Chapter 1</h1>
                    <div class="mw-parser-output">
                        <p>Complete chapter summary with multiple sentences. 
                        This includes character interactions and plot development.</p>
                        
                        <div class="portable-infobox">
                            <div data-source="characters">
                                <div class="pi-data-value">
                                    <a href="/wiki/Monkey_D._Luffy" title="Monkey D. Luffy">Monkey D. Luffy</a>,
                                    <a href="/wiki/Coby" title="Coby">Coby</a>
                                </div>
                            </div>
                        </div>
                        
                        <a href="/wiki/Chapter_2" title="Chapter 2">Chapter 2</a>
                    </div>
                </body>
            </html>
            """
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = mock_html
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = self.crawler.scrape_chapter_page("https://onepiece.fandom.com/wiki/Chapter_1")
            
            # Validate complete data structure
            self.assertIsInstance(result, dict)
            
            # Required fields
            required_fields = ['number', 'title', 'summary', 'characters', 'next_chapter_url']
            for field in required_fields:
                self.assertIn(field, result)
            
            # Data types
            self.assertIsInstance(result['number'], int)
            self.assertIsInstance(result['title'], str)
            self.assertIsInstance(result['summary'], str)
            self.assertIsInstance(result['characters'], list)
            
            # Character structure
            for character in result['characters']:
                self.assertIsInstance(character, dict)
                self.assertIn('name', character)
                self.assertIn('wiki_url', character)
                self.assertIsInstance(character['name'], str)
                self.assertIsInstance(character['wiki_url'], str)
                self.assertTrue(character['wiki_url'].startswith('/wiki/'))
            
            # Content quality
            self.assertGreater(len(result['summary']), 20)  # Substantial summary
            self.assertGreater(len(result['characters']), 0)  # At least one character

def run_crawler_tests():
    """Run all crawler tests"""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestWikiCrawler))
    suite.addTest(unittest.makeSuite(TestWikiCrawlerIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    print("Running Wiki Crawler Tests...")
    success = run_crawler_tests()
    
    if success:
        print("\n✓ All Wiki Crawler tests passed!")
    else:
        print("\n✗ Some Wiki Crawler tests failed!")
    
    exit(0 if success else 1)