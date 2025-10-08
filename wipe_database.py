"""Script to completely wipe all data from the database."""

import sqlite3
import sys

def wipe_database(db_path: str = "one_piece_stocks.db"):
    """Wipe all data from all tables in the database."""
    print(f"⚠️  WARNING: This will DELETE ALL DATA from {db_path}")
    print("Tables to be wiped:")
    print("  - chapters")
    print("  - characters")
    print("  - market_events")
    print("  - character_stock_history")
    print("  - market_context")
    print()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get table names to verify
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"Found {len(tables)} tables in database: {', '.join(tables)}")
    print()
    
    # Delete all data from each table
    tables_to_wipe = ['market_events', 'character_stock_history', 'market_context', 'characters', 'chapters']
    
    for table in tables_to_wipe:
        if table in tables:
            cursor.execute(f"DELETE FROM {table}")
            deleted = cursor.rowcount
            print(f"✅ Deleted {deleted} rows from {table}")
        else:
            print(f"⚠️  Table {table} does not exist (skipping)")
    
    conn.commit()
    
    # Verify all tables are empty
    print("\n🔍 Verifying tables are empty...")
    all_empty = True
    for table in tables_to_wipe:
        if table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"❌ ERROR: {table} still has {count} rows!")
                all_empty = False
            else:
                print(f"✅ {table}: 0 rows")
    
    conn.close()
    
    if all_empty:
        print("\n✅ SUCCESS: All tables have been completely wiped!")
    else:
        print("\n❌ ERROR: Some tables still have data!")
        sys.exit(1)

if __name__ == "__main__":
    wipe_database()

