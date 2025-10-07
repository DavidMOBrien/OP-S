"""Example usage of the One Piece Stock Tracker system."""

from database import Database
from wiki_crawler import WikiCrawler
from llm_analyzer import LLMAnalyzer


def example_database_queries():
    """Example queries you can run on the database after generating data."""
    print("="*80)
    print("Example Database Queries")
    print("="*80)
    
    with Database() as db:
        # Get top 10 stocks
        print("\n📈 Top 10 Current Stocks:")
        top_stocks = db.get_top_stocks(limit=10)
        for i, stock in enumerate(top_stocks, 1):
            print(f"{i:2d}. {stock['character_name']:<30s} {stock['stock_value']:>8.1f}")
        
        # Get market statistics
        print("\n📊 Market Statistics:")
        stats = db.get_market_statistics()
        print(f"Total Characters: {stats['total_characters']}")
        print(f"Average Stock: {stats['average']:.1f}")
        print(f"Median Stock: {stats['median']:.1f}")
        
        # Get specific character history
        print("\n📖 Character History Example (if Luffy exists):")
        if db.character_exists("Monkey_D._Luffy"):
            history = db.get_character_history("Monkey_D._Luffy", limit=5)
            luffy = db.get_character("Monkey_D._Luffy")
            current = db.calculate_current_stock("Monkey_D._Luffy")
            
            print(f"\nLuffy's Current Stock: {current:.1f}")
            print(f"Initial Value: {luffy['initial_stock_value']:.1f}")
            print(f"First Appearance: Chapter {luffy['first_appearance_chapter']}")
            print("\nRecent Changes:")
            for event in history:
                print(f"  Ch. {event['chapter_id']}: {event['stock_change']:+.1f} - {event['description'][:60]}...")


def example_crawl_single_chapter():
    """Example: Crawl a single chapter to see the data."""
    print("\n" + "="*80)
    print("Example: Crawling Chapter 1")
    print("="*80)
    
    crawler = WikiCrawler(delay=1.0)
    
    try:
        data = crawler.test_single_chapter(1)
        
        print(f"\n📚 Chapter: {data['title']}")
        print(f"🏴‍☠️ Arc: {data['arc_name']}")
        print(f"📝 Description length: {len(data['raw_description'])} characters")
        print(f"\n👥 Characters found ({len(data['characters'])}):")
        
        for i, char in enumerate(data['characters'][:10], 1):
            print(f"  {i}. {char['name']} ({char['character_id']})")
            
        if len(data['characters']) > 10:
            print(f"  ... and {len(data['characters']) - 10} more")
            
        print("\n📖 First 200 characters of description:")
        print(data['raw_description'][:200] + "...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Note: Make sure you have internet connection to access the wiki.")


def example_prompt_preview():
    """Example: See what the LLM prompt looks like."""
    print("\n" + "="*80)
    print("Example: LLM Prompt Preview")
    print("="*80)
    
    # This requires an API key, so we'll just show the structure
    print("\nThe LLM analyzer uses a two-part prompt:")
    print("\n1. SYSTEM PROMPT: Defines the rules and task")
    print("2. USER PROMPT: Provides chapter data and market context")
    print("\nFor a real example, check llm_analyzer.py or run the test at the bottom")
    print("of that file with: python llm_analyzer.py")


def main():
    """Run examples."""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                   One Piece Stock Tracker - Examples                       ║
╚════════════════════════════════════════════════════════════════════════════╝

This script demonstrates how to use the system components.
""")
    
    print("\n1. Testing Wiki Crawler (requires internet)")
    print("2. Testing Database Queries (requires generated data)")
    print("3. Prompt Preview")
    
    choice = input("\nSelect example to run (1-3, or 'all'): ").strip()
    
    if choice == '1' or choice == 'all':
        example_crawl_single_chapter()
        
    if choice == '2' or choice == 'all':
        try:
            example_database_queries()
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("You may need to generate data first with: python generate_offline_data.py --max 10")
            
    if choice == '3' or choice == 'all':
        example_prompt_preview()
        
    print("\n" + "="*80)
    print("Examples complete!")
    print("\nNext steps:")
    print("1. Initialize database: python generate_offline_data.py --init")
    print("2. Generate data: python generate_offline_data.py --max 5")
    print("3. Query results: Use example_database_queries() function above")
    print("="*80)


if __name__ == "__main__":
    main()

