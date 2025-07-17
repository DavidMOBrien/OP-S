#!/usr/bin/env python3
"""
Test script for the wiki crawler
"""

import logging
from wiki_crawler import WikiCrawler

def test_chronological_navigation():
    """Test crawling multiple chapters in sequence"""
    logging.basicConfig(level=logging.INFO)
    
    crawler = WikiCrawler(rate_limit=0.5)  # Faster for testing
    
    # Test crawling first 3 chapters
    chapters = crawler.crawl_chapters(max_chapters=3)
    
    print(f"\nCrawled {len(chapters)} chapters:")
    for chapter in chapters:
        print(f"Chapter {chapter['number']}: {chapter['title']}")
        print(f"  Characters: {len(chapter['characters'])}")
        print(f"  Summary length: {len(chapter['summary'])} chars")
        print(f"  Next URL: {chapter['next_chapter_url']}")
        print()

if __name__ == "__main__":
    test_chronological_navigation()