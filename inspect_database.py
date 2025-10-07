"""Utility script to inspect the generated stock data."""

import argparse
from database import Database
from typing import Optional


def print_market_summary(db: Database):
    """Print overall market summary."""
    print("\n" + "="*80)
    print("📊 MARKET SUMMARY")
    print("="*80)
    
    stats = db.get_market_statistics()
    top_stocks = db.get_top_stocks(limit=20)
    
    print(f"\nTotal Characters Tracked: {stats['total_characters']}")
    print(f"Average Stock Value: {stats['average']:.1f}")
    print(f"Median Stock Value: {stats['median']:.1f}")
    
    print(f"\n📈 Top 20 Stocks:")
    print(f"{'Rank':<6} {'Character':<35} {'Stock Value':>12}")
    print("-" * 80)
    for i, stock in enumerate(top_stocks, 1):
        print(f"{i:<6} {stock['character_name']:<35} {stock['stock_value']:>12.1f}")


def print_character_details(db: Database, character_id: str):
    """Print detailed information about a character."""
    print("\n" + "="*80)
    print(f"👤 CHARACTER DETAILS: {character_id}")
    print("="*80)
    
    character = db.get_character(character_id)
    if not character:
        print(f"❌ Character '{character_id}' not found")
        return
        
    current_stock = db.calculate_current_stock(character_id)
    history = db.get_character_history(character_id, limit=999999)
    
    print(f"\nCanonical Name: {character['canonical_name']}")
    print(f"First Appearance: Chapter {character['first_appearance_chapter']}")
    print(f"Initial Stock Value: {character['initial_stock_value']:.1f}")
    print(f"Current Stock Value: {current_stock:.1f}")
    print(f"Total Change: {current_stock - character['initial_stock_value']:+.1f}")
    print(f"Total Appearances: {len(history)}")
    
    if history:
        print(f"\n📈 Stock History:")
        print(f"{'Chapter':<10} {'Change':>10} {'Description':<50}")
        print("-" * 80)
        for event in reversed(history):  # Show oldest first
            desc = event['description'][:47] + "..." if len(event['description']) > 50 else event['description']
            print(f"{event['chapter_id']:<10} {event['stock_change']:>+10.1f} {desc:<50}")


def print_chapter_summary(db: Database, chapter_id: int):
    """Print summary of a specific chapter."""
    print("\n" + "="*80)
    print(f"📖 CHAPTER {chapter_id} SUMMARY")
    print("="*80)
    
    chapter = db.get_chapter(chapter_id)
    if not chapter:
        print(f"❌ Chapter {chapter_id} not found")
        return
        
    print(f"\nTitle: {chapter['title']}")
    print(f"Arc: {chapter['arc_name'] or 'Unknown'}")
    print(f"Processed: {'Yes' if chapter['processed'] else 'No'}")
    
    if chapter['processed']:
        # Get all events in this chapter
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT me.*, c.canonical_name
            FROM market_events me
            JOIN characters c ON me.character_id = c.character_id
            WHERE me.chapter_id = ?
            ORDER BY ABS(me.stock_change) DESC
        """, (chapter_id,))
        
        events = [dict(row) for row in cursor.fetchall()]
        
        print(f"\n💹 Stock Movements ({len(events)} characters):")
        print(f"{'Character':<30} {'Change':>10} {'New Value':>12} {'Confidence':>10}")
        print("-" * 80)
        
        for event in events:
            new_value = db.calculate_current_stock(event['character_id'], chapter_id)
            print(f"{event['canonical_name']:<30} {event['stock_change']:>+10.1f} "
                  f"{new_value:>12.1f} {event['confidence_score']:>10.2f}")
            
        # Show biggest movers
        if events:
            print("\n🚀 Biggest Movers:")
            gainers = [e for e in events if e['stock_change'] > 0]
            losers = [e for e in events if e['stock_change'] < 0]
            
            if gainers:
                top_gainer = gainers[0]
                print(f"  Biggest Gain: {top_gainer['canonical_name']} ({top_gainer['stock_change']:+.1f})")
                print(f"    Reason: {top_gainer['description']}")
                
            if losers:
                top_loser = losers[-1]
                print(f"  Biggest Loss: {top_loser['canonical_name']} ({top_loser['stock_change']:+.1f})")
                print(f"    Reason: {top_loser['description']}")


def print_top_movers(db: Database, up_to_chapter: Optional[int] = None, limit: int = 10):
    """Print characters with biggest recent movements."""
    print("\n" + "="*80)
    print("🚀 BIGGEST MOVERS (by last change)")
    print("="*80)
    
    cursor = db.conn.cursor()
    
    # Get most recent change for each character
    if up_to_chapter:
        cursor.execute("""
            SELECT 
                me.character_id,
                c.canonical_name,
                me.stock_change,
                me.chapter_id,
                me.description
            FROM market_events me
            JOIN characters c ON me.character_id = c.character_id
            WHERE me.chapter_id <= ? AND me.chapter_id IN (
                SELECT MAX(chapter_id) 
                FROM market_events 
                WHERE character_id = me.character_id AND chapter_id <= ?
            )
            ORDER BY ABS(me.stock_change) DESC
            LIMIT ?
        """, (up_to_chapter, up_to_chapter, limit))
    else:
        cursor.execute("""
            SELECT 
                me.character_id,
                c.canonical_name,
                me.stock_change,
                me.chapter_id,
                me.description
            FROM market_events me
            JOIN characters c ON me.character_id = c.character_id
            WHERE me.chapter_id IN (
                SELECT MAX(chapter_id) 
                FROM market_events 
                WHERE character_id = me.character_id
            )
            ORDER BY ABS(me.stock_change) DESC
            LIMIT ?
        """, (limit,))
        
    movers = [dict(row) for row in cursor.fetchall()]
    
    print(f"\n{'Character':<30} {'Chapter':>8} {'Change':>10} {'Description':<30}")
    print("-" * 80)
    
    for mover in movers:
        desc = mover['description'][:27] + "..." if len(mover['description']) > 30 else mover['description']
        print(f"{mover['canonical_name']:<30} {mover['chapter_id']:>8} "
              f"{mover['stock_change']:>+10.1f} {desc:<30}")


def list_all_characters(db: Database):
    """List all tracked characters."""
    print("\n" + "="*80)
    print("👥 ALL CHARACTERS")
    print("="*80)
    
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT 
            character_id,
            canonical_name,
            first_appearance_chapter,
            initial_stock_value
        FROM characters
        ORDER BY first_appearance_chapter, canonical_name
    """)
    
    characters = [dict(row) for row in cursor.fetchall()]
    
    print(f"\nTotal: {len(characters)} characters")
    print(f"\n{'Character':<35} {'First Ch.':>10} {'Initial':>10} {'Current':>10}")
    print("-" * 80)
    
    for char in characters:
        current = db.calculate_current_stock(char['character_id'])
        print(f"{char['canonical_name']:<35} {char['first_appearance_chapter']:>10} "
              f"{char['initial_stock_value']:>10.1f} {current:>10.1f}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Inspect One Piece stock data'
    )
    parser.add_argument(
        '--db', type=str, default='one_piece_stocks.db',
        help='Database path (default: one_piece_stocks.db)'
    )
    parser.add_argument(
        '--character', type=str,
        help='Show details for specific character (use character_id, e.g., Monkey_D._Luffy)'
    )
    parser.add_argument(
        '--chapter', type=int,
        help='Show summary for specific chapter'
    )
    parser.add_argument(
        '--movers', action='store_true',
        help='Show biggest recent movers'
    )
    parser.add_argument(
        '--list-all', action='store_true',
        help='List all characters'
    )
    parser.add_argument(
        '--summary', action='store_true',
        help='Show market summary (default if no other options)'
    )
    
    args = parser.parse_args()
    
    # If no specific option, show summary
    if not any([args.character, args.chapter, args.movers, args.list_all, args.summary]):
        args.summary = True
    
    with Database(args.db) as db:
        if args.summary:
            print_market_summary(db)
            
        if args.character:
            print_character_details(db, args.character)
            
        if args.chapter:
            print_chapter_summary(db, args.chapter)
            
        if args.movers:
            print_top_movers(db)
            
        if args.list_all:
            list_all_characters(db)
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()

