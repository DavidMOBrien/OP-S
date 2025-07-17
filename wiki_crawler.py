#!/usr/bin/env python3
"""
One Piece Wiki Crawler
Scrapes chapter data from the One Piece wiki with chronological navigation
"""

import requests
import time
import logging
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from urllib.parse import urljoin
import re

logger = logging.getLogger(__name__)

class WikiCrawler:
    """Crawler for One Piece wiki chapter data"""
    
    def __init__(self, base_url: str = "https://onepiece.fandom.com", rate_limit: float = 1.0):
        """Initialize the wiki crawler"""
        self.base_url = base_url
        self.rate_limit = rate_limit
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def scrape_chapter_page(self, chapter_url: str) -> Optional[Dict]:
        """Scrape a single chapter page for data"""
        max_retries = 3
        retry_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Scraping chapter: {chapter_url} (attempt {attempt + 1}/{max_retries})")
                
                time.sleep(self.rate_limit)
                response = self.session.get(chapter_url, timeout=30)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                chapter_number = self._extract_chapter_number(chapter_url, soup)
                if not chapter_number:
                    logger.warning(f"Could not extract chapter number from {chapter_url}")
                    return None
                    
                chapter_title = self._extract_chapter_title(soup)
                chapter_summary = self._extract_chapter_summary(soup)
                characters = self._extract_characters(soup)
                next_chapter_url = self._find_next_chapter_url(soup)
                
                chapter_data = {
                    'number': chapter_number,
                    'title': chapter_title,
                    'summary': chapter_summary,
                    'characters': characters,
                    'next_chapter_url': next_chapter_url,
                    'wiki_url': chapter_url
                }
                
                logger.info(f"Successfully scraped Chapter {chapter_number}: {chapter_title}")
                logger.info(f"Found {len(characters)} characters")
                
                return chapter_data
                
            except requests.exceptions.Timeout as e:
                logger.warning(f"Timeout for {chapter_url} (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                return None
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed for {chapter_url} (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                return None
                
            except Exception as e:
                logger.error(f"Unexpected error scraping {chapter_url}: {e}")
                return None
        
        return None
    
    def _extract_chapter_number(self, url: str, soup: BeautifulSoup) -> Optional[int]:
        """Extract chapter number from URL or page content"""
        url_match = re.search(r'/wiki/Chapter_(\d+)', url)
        if url_match:
            return int(url_match.group(1))
            
        title_element = soup.find('h1', class_='page-header__title')
        if title_element:
            title_text = title_element.get_text()
            title_match = re.search(r'Chapter (\d+)', title_text)
            if title_match:
                return int(title_match.group(1))
                
        return None
    
    def _extract_chapter_title(self, soup: BeautifulSoup) -> str:
        """Extract chapter title from the page"""
        title_element = soup.find('h1', class_='page-header__title')
        if title_element:
            return title_element.get_text().strip()
            
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text()
            title_text = re.sub(r'\s*\|\s*One Piece Wiki.*$', '', title_text)
            return title_text.strip()
            
        return "Unknown Title"   
 
    def _extract_chapter_summary(self, soup: BeautifulSoup) -> str:
        """Extract comprehensive chapter summary from the page"""
        summary_parts = []
        
        content_area = soup.find('div', class_='mw-parser-output')
        if not content_area:
            logger.warning("Could not find main content area")
            return "No summary available"
        
        # Get all paragraphs and relevant content
        paragraphs = content_area.find_all('p')
        
        # Also look for div content that might contain story details
        content_divs = content_area.find_all('div', recursive=False)
        
        # Process paragraphs first
        for p in paragraphs:
            text = p.get_text().strip()
            if not text:
                continue
                
            # Skip navigation and metadata sections
            skip_phrases = [
                'navigation', 'categories', 'see also', 'references', 'external links',
                'chapter info', 'volume:', 'chapter:', 'japanese title', 'romanized title',
                'viz title', 'release date', 'cover page', 'short summary'
            ]
            
            if any(skip_phrase in text.lower() for skip_phrase in skip_phrases):
                continue
                
            # Skip very short paragraphs that are likely metadata
            if len(text) < 20:
                continue
                
            summary_parts.append(text)
            
            # NO LIMIT - get the complete chapter content
        
        # If we don't have enough content, try div elements
        if len(' '.join(summary_parts)) < 200:
            for div in content_divs:
                div_text = div.get_text().strip()
                if div_text and len(div_text) > 50:
                    # Skip divs that are clearly navigation or metadata
                    if not any(skip_phrase in div_text.lower() for skip_phrase in skip_phrases):
                        summary_parts.append(div_text)
                        # NO LIMIT - get complete content
        
        summary = ' '.join(summary_parts)
        
        # Clean up the summary
        summary = summary.replace('\n', ' ').replace('\t', ' ')
        # Remove multiple spaces
        import re
        summary = re.sub(r'\s+', ' ', summary)
        
        logger.info(f"Extracted summary length: {len(summary)} characters")
        
        return summary.strip() if summary.strip() else "No summary available"
    
    def _extract_characters(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract character list with their wiki URLs from the Characters box"""
        characters = []
        seen_urls = set()
        
        # First, try to find the CharTable (character table)
        char_table = soup.find('table', class_='CharTable')
        if char_table:
            logger.info("Found CharTable, extracting characters from it")
            characters = self._extract_from_char_table(char_table, seen_urls)
        
        # If no CharTable found, look for other character containers
        if not characters:
            logger.info("No CharTable found, looking for other character containers")
            characters = self._extract_from_general_content(soup, seen_urls)
        
        # Remove duplicates based on character name
        unique_characters = []
        seen_names = set()
        
        for char in characters:
            name_lower = char['name'].lower()
            if name_lower not in seen_names:
                unique_characters.append(char)
                seen_names.add(name_lower)
        
        logger.info(f"Extracted {len(unique_characters)} unique characters")
        return unique_characters
    
    def _extract_from_char_table(self, char_table: BeautifulSoup, seen_urls: set) -> List[Dict[str, str]]:
        """Extract characters specifically from the CharTable"""
        characters = []
        
        # Get all links from the character table
        links = char_table.find_all('a', href=True)
        
        for link in links:
            href = link.get('href')
            if not href:
                continue
                
            # Convert relative URLs to absolute
            if href.startswith('/'):
                full_url = urljoin(self.base_url, href)
            else:
                full_url = href
            
            # Only include character links, skip category/general links
            if self._is_character_link_strict(href, link.get_text()):
                if full_url not in seen_urls:
                    character_name = link.get_text().strip()
                    if character_name:
                        characters.append({
                            'name': character_name,
                            'wiki_url': full_url
                        })
                        seen_urls.add(full_url)
        
        return characters
    
    def _extract_from_general_content(self, soup: BeautifulSoup, seen_urls: set) -> List[Dict[str, str]]:
        """Fallback method to extract characters from general content"""
        characters = []
        
        content_area = soup.find('div', class_='mw-parser-output')
        if not content_area:
            return characters
        
        links = content_area.find_all('a', href=True)
        
        for link in links:
            href = link.get('href')
            if not href:
                continue
                
            if href.startswith('/'):
                full_url = urljoin(self.base_url, href)
            else:
                full_url = href
            
            if self._is_character_link(href, link.get_text()):
                if full_url not in seen_urls:
                    character_name = link.get_text().strip()
                    if character_name:
                        characters.append({
                            'name': character_name,
                            'wiki_url': full_url
                        })
                        seen_urls.add(full_url)
        
        return characters
    
    def _is_character_link_strict(self, href: str, link_text: str) -> bool:
        """Determine if a link is a character page (strict version for CharTable)"""
        if not href or not link_text:
            return False
            
        # Skip certain types of links
        skip_patterns = [
            r'/wiki/Category:', r'/wiki/File:', r'/wiki/Template:', r'/wiki/Help:',
            r'/wiki/Special:', r'/wiki/User:', r'/wiki/Talk:', r'#'
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, href):
                return False
        
        if not ('/wiki/' in href):
            return False
            
        # Skip common non-character pages (more strict)
        non_character_patterns = [
            r'Chapter_\d+', r'Episode_\d+', r'Volume_\d+', r'Arc', r'Saga',
            r'Island', r'Sea', r'Ocean', r'Devil_Fruit', r'Haki',
            r'We_Are!', r'Episode_of_', r'Jolly_Roger', r'Gomu_Gomu_no_Mi',
            r'Pirate', r'Marine', r'Animal_Species', r'Location', r'Ship',
            r'Weapon', r'Technique', r'Organization', r'Government'
        ]
        
        for pattern in non_character_patterns:
            if re.search(pattern, href, re.IGNORECASE):
                return False
        
        # Skip very short names or common words
        if len(link_text.strip()) < 3:
            return False
            
        # Skip generic category words
        skip_words = [
            'pirates', 'citizens', 'animals', 'outlaws', 'others',
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'
        ]
        if link_text.lower().strip() in skip_words:
            return False
        
        # Must have at least one capital letter (proper names)
        if not re.search(r'[A-Z]', link_text):
            return False
            
        return True
    
    def _is_character_link(self, href: str, link_text: str) -> bool:
        """Determine if a link is likely a character page"""
        if not href or not link_text:
            return False
            
        # Skip certain types of links
        skip_patterns = [
            r'/wiki/Category:', r'/wiki/File:', r'/wiki/Template:', r'/wiki/Help:',
            r'/wiki/Special:', r'/wiki/User:', r'/wiki/Talk:', r'#'
        ]
        
        for pattern in skip_patterns:
            if re.search(pattern, href):
                if 'onepiece.fandom.com/wiki/' not in href:
                    return False
        
        if not ('/wiki/' in href):
            return False
            
        # Skip common non-character pages
        non_character_patterns = [
            r'Chapter_\d+', r'Episode_\d+', r'Volume_\d+', r'Arc$', r'Saga$',
            r'Island$', r'Sea$', r'Ocean$', r'Devil_Fruit', r'Haki',
            r'We_Are!', r'Episode_of_', r'Jolly_Roger', r'Gomu_Gomu_no_Mi'
        ]
        
        for pattern in non_character_patterns:
            if re.search(pattern, href, re.IGNORECASE):
                return False
        
        if len(link_text.strip()) < 3:
            return False
            
        skip_words = [
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'we are!', 'episode of luffy', 'jolly roger', 'gomu gomu no mi'
        ]
        if link_text.lower().strip() in skip_words:
            return False
        
        if not re.search(r'[A-Z]', link_text):
            return False
            
        return True
    
    def _find_next_chapter_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Find the URL for the next chapter"""
        next_patterns = [r'next\s*chapter', r'chapter\s*\d+', r'→', r'next']
        
        links = soup.find_all('a', href=True)
        
        for link in links:
            link_text = link.get_text().lower().strip()
            href = link.get('href')
            
            for pattern in next_patterns:
                if re.search(pattern, link_text, re.IGNORECASE):
                    if '/wiki/Chapter_' in href:
                        if href.startswith('/'):
                            return urljoin(self.base_url, href)
                        return href
        
        # Look for navigation boxes
        nav_boxes = soup.find_all(['div', 'table'], class_=re.compile(r'nav|navigation', re.IGNORECASE))
        
        for nav_box in nav_boxes:
            nav_links = nav_box.find_all('a', href=True)
            for link in nav_links:
                href = link.get('href')
                if '/wiki/Chapter_' in href:
                    link_text = link.get_text().strip()
                    if any(word in link_text.lower() for word in ['next', '→', 'chapter']):
                        if href.startswith('/'):
                            return urljoin(self.base_url, href)
                        return href
        
        # Look for sequential chapter numbers
        current_chapter = self._extract_chapter_number("", soup)
        if current_chapter:
            next_chapter_num = current_chapter + 1
            for link in links:
                href = link.get('href')
                if f'/wiki/Chapter_{next_chapter_num}' in href:
                    if href.startswith('/'):
                        return urljoin(self.base_url, href)
                    return href
        
        return None
    
    def crawl_chapters(self, start_url: str = "https://onepiece.fandom.com/wiki/Chapter_1", 
                      max_chapters: Optional[int] = None) -> List[Dict]:
        """Crawl chapters starting from the given URL"""
        chapters = []
        current_url = start_url
        chapters_processed = 0
        
        logger.info(f"Starting chapter crawl from: {start_url}")
        
        while current_url and (max_chapters is None or chapters_processed < max_chapters):
            try:
                chapter_data = self.scrape_chapter_page(current_url)
                
                if chapter_data:
                    chapters.append(chapter_data)
                    chapters_processed += 1
                    
                    logger.info(f"Processed chapter {chapters_processed}: Chapter {chapter_data['number']}")
                    
                    current_url = chapter_data.get('next_chapter_url')
                    
                    if not current_url:
                        logger.info("No next chapter URL found, ending crawl")
                        break
                else:
                    logger.warning(f"Failed to scrape chapter data from {current_url}")
                    break
                    
            except KeyboardInterrupt:
                logger.info("Crawl interrupted by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error during crawl: {e}")
                break
        
        logger.info(f"Crawl completed. Processed {len(chapters)} chapters")
        return chapters
    
    def test_single_chapter(self, chapter_url: str = "https://onepiece.fandom.com/wiki/Chapter_1") -> Dict:
        """Test the crawler on a single chapter for debugging"""
        logger.info(f"Testing single chapter: {chapter_url}")
        return self.scrape_chapter_page(chapter_url)


def main():
    """Test the wiki crawler"""
    logging.basicConfig(level=logging.INFO)
    
    crawler = WikiCrawler()
    chapter_data = crawler.test_single_chapter()
    
    if chapter_data:
        print(f"Chapter {chapter_data['number']}: {chapter_data['title']}")
        print(f"Summary length: {len(chapter_data['summary'])} characters")
        print(f"Characters found: {len(chapter_data['characters'])}")
        print(f"Next chapter URL: {chapter_data['next_chapter_url']}")
        
        print("\nCharacters:")
        for char in chapter_data['characters'][:10]:
            print(f"  - {char['name']}: {char['wiki_url']}")
    else:
        print("Failed to scrape chapter data")


if __name__ == "__main__":
    main()