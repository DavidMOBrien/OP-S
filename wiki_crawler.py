"""Wiki crawler for One Piece chapter data."""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Tuple, Optional
import time
import re
from urllib.parse import urljoin, urlparse


class WikiCrawler:
    """Crawls One Piece Wiki for chapter information."""
    
    BASE_URL = "https://onepiece.fandom.com"
    
    def __init__(self, delay: float = 1.0):
        """
        Initialize the crawler.
        
        Args:
            delay: Delay between requests in seconds (be respectful)
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OnePieceStockTracker/1.0 (Educational Project)'
        })
        
    def get_chapter_list_page(self, start_chapter: int = 1) -> str:
        """Get the chapter list page URL."""
        # One Piece wiki chapter list
        return f"{self.BASE_URL}/wiki/Chapters"
        
    def fetch_chapter_urls(self, max_chapters: Optional[int] = None) -> List[Tuple[int, str]]:
        """
        Fetch list of chapter URLs.
        
        Since One Piece wiki uses predictable URLs (/wiki/Chapter_1, /wiki/Chapter_2, etc.),
        we generate them directly instead of scraping a chapter list page.
        
        Returns:
            List of (chapter_number, url) tuples
        """
        chapters = []
        
        # One Piece has 1100+ chapters as of 2024
        # Generate URLs for chapters 1 through max_chapters (or a reasonable default)
        default_max = max_chapters if max_chapters else 1100
        
        for chapter_num in range(1, default_max + 1):
            url = f"{self.BASE_URL}/wiki/Chapter_{chapter_num}"
            chapters.append((chapter_num, url))
            
        return chapters
        
    def extract_character_id_from_href(self, href: str) -> str:
        """
        Extract character ID from wiki href.
        
        Example: /wiki/Monkey_D._Luffy -> Monkey_D._Luffy
        """
        # Remove /wiki/ prefix and any query parameters
        path = urlparse(href).path
        character_id = path.replace('/wiki/', '')
        return character_id
        
    def fetch_chapter_data(self, chapter_url: str, chapter_num: int) -> Dict:
        """
        Fetch data for a single chapter.
        
        Returns:
            Dict with:
                - chapter_id: int
                - title: str
                - url: str
                - raw_description: str
                - arc_name: str (if available)
                - characters: List[Dict] with character_id, name, href
        """
        time.sleep(self.delay)  # Be respectful to the server
        
        response = self.session.get(chapter_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title_elem = soup.find('h1', class_='page-header__title')
        title = title_elem.text.strip() if title_elem else f"Chapter {chapter_num}"
        
        # Extract arc name (usually in an infobox or breadcrumb)
        arc_name = None
        # Try to find arc in infobox
        infobox = soup.find('aside', class_='portable-infobox')
        if infobox:
            arc_section = infobox.find('div', {'data-source': 'arc'})
            if arc_section:
                arc_link = arc_section.find('a')
                if arc_link:
                    arc_name = arc_link.text.strip()
                    
        # If not found, try breadcrumbs
        if not arc_name:
            breadcrumbs = soup.find('nav', class_='fandom-community-header__local-navigation')
            if breadcrumbs:
                links = breadcrumbs.find_all('a')
                for link in links:
                    text = link.text.strip()
                    if 'Arc' in text or 'Saga' in text:
                        arc_name = text
                        break
        
        # Extract chapter summary/description
        # Prioritize "Long Summary" over "Short Summary"
        content_div = soup.find('div', class_='mw-parser-output')
        
        description_parts = []
        if content_div:
            # Look for "Long Summary" heading first
            long_summary_found = False
            for heading in content_div.find_all(['h2', 'h3']):
                heading_text = heading.get_text(strip=True).lower()
                if 'long summary' in heading_text:
                    long_summary_found = True
                    # Get all paragraphs after "Long Summary" until next heading
                    next_elem = heading.find_next_sibling()
                    while next_elem and next_elem.name not in ['h2', 'h3']:
                        if next_elem.name == 'p':
                            text = next_elem.get_text(strip=True)
                            if text and len(text) > 20:
                                description_parts.append(text)
                        next_elem = next_elem.find_next_sibling()
                    break
            
            # If no "Long Summary" found, fall back to any "Summary" section
            if not long_summary_found:
                for heading in content_div.find_all(['h2', 'h3']):
                    heading_text = heading.get_text(strip=True).lower()
                    if 'summary' in heading_text and 'short' not in heading_text:
                        # Get paragraphs after this heading
                        next_elem = heading.find_next_sibling()
                        while next_elem and next_elem.name not in ['h2', 'h3']:
                            if next_elem.name == 'p':
                                text = next_elem.get_text(strip=True)
                                if text and len(text) > 20:
                                    description_parts.append(text)
                            next_elem = next_elem.find_next_sibling()
                        break
            
            # If still no summary found, get initial paragraphs
            if not description_parts:
                for elem in content_div.children:
                    if elem.name == 'p':
                        text = elem.get_text(strip=True)
                        if text and len(text) > 20:
                            description_parts.append(text)
                    elif elem.name in ['h2', 'h3']:
                        break
                        
        raw_description = ' '.join(description_parts)
        
        # Extract characters from the "Characters" section in Quick Reference
        # This gives us a cleaner list than scraping all links
        characters = []
        character_hrefs_seen = set()
        
        # First, try to find the "Characters" heading in Quick Reference section
        characters_section = None
        if content_div:
            # Look for h2/h3 with "Characters" text
            for heading in content_div.find_all(['h2', 'h3', 'h4']):
                if 'characters' in heading.get_text().lower():
                    characters_section = heading
                    break
        
        # If we found the characters section, extract links from there
        if characters_section:
            # Get the next element(s) after the heading until we hit another heading
            current = characters_section.find_next_sibling()
            while current and current.name not in ['h2', 'h3', 'h4']:
                # Find all character links in this section
                char_links = current.find_all('a', href=re.compile(r'^/wiki/[^:]+$'))
                
                for link in char_links:
                    href = link.get('href')
                    
                    # Skip file/category/template links
                    if any(skip in href for skip in ['File:', 'Category:', 'Template:', 'Help:', 'Special:']):
                        continue
                    
                    # Check if we've already seen this character
                    if href in character_hrefs_seen:
                        continue
                        
                    character_hrefs_seen.add(href)
                    
                    character_id = self.extract_character_id_from_href(href)
                    character_name = link.get_text(strip=True)
                    
                    if character_name and len(character_name) > 1:
                        characters.append({
                            'character_id': character_id,
                            'name': character_name,
                            'href': href
                        })
                
                current = current.find_next_sibling()
        
        # Fallback: if no characters section found, use summary text only
        # and apply stricter filtering
        if not characters and content_div:
            # Look for character links only in Short/Long Summary sections
            summary_found = False
            for heading in content_div.find_all(['h2', 'h3']):
                heading_text = heading.get_text().lower()
                if 'summary' in heading_text:
                    summary_found = True
                    # Get paragraphs after this heading
                    current = heading.find_next_sibling()
                    while current and current.name not in ['h2', 'h3']:
                        if current.name == 'p':
                            char_links = current.find_all('a', href=re.compile(r'^/wiki/[^:]+$'))
                            
                            for link in char_links:
                                href = link.get('href')
                                
                                # Much stricter filtering for fallback method
                                skip_patterns = [
                                    'Chapter', 'Episode', 'Arc', 'Saga', 'Volume',
                                    'Devil_Fruit', 'Marine', 'Pirate', 'Grand_Line',
                                    'East_Blue', 'New_World', 'Haki', 'Gomu_Gomu',
                                    'Jolly_Roger', 'File:', 'Category:', 'Template:',
                                    'Help:', 'Special:', 'Village', 'Bar', 'Island',
                                    'Sea_King', 'Cover_Page', 'Color_Spread'
                                ]
                                
                                if any(pattern in href for pattern in skip_patterns):
                                    continue
                                
                                # Skip if already seen
                                if href in character_hrefs_seen:
                                    continue
                                    
                                character_hrefs_seen.add(href)
                                
                                character_id = self.extract_character_id_from_href(href)
                                character_name = link.get_text(strip=True)
                                
                                # Additional filter: skip very short names (likely not characters)
                                if character_name and len(character_name) > 2:
                                    characters.append({
                                        'character_id': character_id,
                                        'name': character_name,
                                        'href': href
                                    })
                        
                        current = current.find_next_sibling()
                    
                    if summary_found:
                        break
        
        return {
            'chapter_id': chapter_num,
            'title': title,
            'url': chapter_url,
            'raw_description': raw_description,
            'arc_name': arc_name,
            'characters': characters
        }
        
    def crawl_chapters(self, start_chapter: int = 1, 
                      end_chapter: Optional[int] = None,
                      max_chapters: Optional[int] = None) -> List[Dict]:
        """
        Crawl multiple chapters.
        
        Args:
            start_chapter: First chapter to crawl
            end_chapter: Last chapter to crawl (inclusive)
            max_chapters: Maximum number of chapters to crawl
            
        Returns:
            List of chapter data dicts
        """
        print("Generating chapter URLs...")
        
        # Determine the range of chapters to process
        if max_chapters:
            # If max_chapters is specified, go from start_chapter to start_chapter + max_chapters - 1
            end = start_chapter + max_chapters - 1
            if end_chapter and end_chapter < end:
                end = end_chapter
            chapter_urls = self.fetch_chapter_urls(max_chapters=end)
        else:
            # Generate URLs for the specified range
            chapter_urls = self.fetch_chapter_urls(max_chapters=end_chapter if end_chapter else 1100)
        
        # Filter by range
        chapter_urls = [
            (num, url) for num, url in chapter_urls
            if num >= start_chapter and (not end_chapter or num <= end_chapter)
        ]
        
        # Apply max_chapters limit after filtering by range
        if max_chapters:
            chapter_urls = chapter_urls[:max_chapters]
        
        print(f"Will process {len(chapter_urls)} chapters (Chapter {chapter_urls[0][0]} to Chapter {chapter_urls[-1][0]})")
        
        chapters_data = []
        for i, (chapter_num, url) in enumerate(chapter_urls, 1):
            try:
                print(f"Crawling chapter {chapter_num} ({i}/{len(chapter_urls)})...")
                data = self.fetch_chapter_data(url, chapter_num)
                chapters_data.append(data)
            except Exception as e:
                print(f"Error crawling chapter {chapter_num}: {e}")
                continue
                
        return chapters_data
        
    def test_single_chapter(self, chapter_num: int) -> Dict:
        """Test crawling a single chapter."""
        url = f"{self.BASE_URL}/wiki/Chapter_{chapter_num}"
        return self.fetch_chapter_data(url, chapter_num)


if __name__ == "__main__":
    # Test the crawler
    crawler = WikiCrawler(delay=1.0)
    
    # Test with a single chapter
    print("Testing with Chapter 1...")
    data = crawler.test_single_chapter(1)
    
    print(f"\nChapter: {data['title']}")
    print(f"Arc: {data['arc_name']}")
    print(f"Description length: {len(data['raw_description'])} chars")
    print(f"Characters found: {len(data['characters'])}")
    print("\nFirst 5 characters:")
    for char in data['characters'][:5]:
        print(f"  - {char['name']} ({char['character_id']})")

