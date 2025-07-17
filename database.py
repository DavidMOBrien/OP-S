"""
Database module for One Piece Character Tracker
Handles SQLite database operations with market context support
"""

import sqlite3
import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Character:
    wiki_url: str
    name: str
    current_value: int
    first_appearance: int

@dataclass
class CharacterChange:
    wiki_url: str
    name: str
    value_change: int
    reasoning: str

@dataclass
class MarketContext:
    recent_changes: List[Dict]
    top_characters: List[Dict]
    bottom_characters: List[Dict]
    total_characters: int

class DatabaseManager:
    def __init__(self, db_path: str = "one_piece_tracker.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory for dict-like access"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database with all required tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Characters table (using wiki_url as unique identifier)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS characters (
                    wiki_url TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    current_value INTEGER NOT NULL,
                    first_appearance INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Character history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS character_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    character_wiki_url TEXT NOT NULL,
                    chapter_number INTEGER NOT NULL,
                    value_change INTEGER NOT NULL,
                    new_value INTEGER NOT NULL,
                    reasoning TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (character_wiki_url) REFERENCES characters(wiki_url),
                    UNIQUE(character_wiki_url, chapter_number)
                )
            """)
            
            # Chapters table (for tracking processed chapters)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chapters (
                    number INTEGER PRIMARY KEY,
                    title TEXT,
                    wiki_url TEXT,
                    processed BOOLEAN DEFAULT FALSE,
                    processed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Market context cache (for LLM analysis)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_snapshots (
                    chapter_number INTEGER PRIMARY KEY,
                    top_characters TEXT NOT NULL,
                    bottom_characters TEXT NOT NULL,
                    recent_changes TEXT NOT NULL,
                    total_characters INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chapter_number) REFERENCES chapters(number)
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_character_history_chapter ON character_history(chapter_number)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_character_history_url ON character_history(character_wiki_url)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_characters_value ON characters(current_value DESC)")
            
            conn.commit()
            logger.info("Database initialized successfully")   
 # Character management functions
    def add_character(self, wiki_url: str, name: str, starting_value: int, first_appearance: int) -> bool:
        """Add a new character to the database"""
        # Validate input parameters
        if not wiki_url or not wiki_url.strip():
            logger.warning("Cannot add character: wiki_url is empty")
            return False
        
        if not name or not name.strip():
            logger.warning("Cannot add character: name is empty")
            return False
        
        if starting_value <= 0:
            logger.warning(f"Cannot add character: invalid starting_value {starting_value}")
            return False
        
        if first_appearance <= 0:
            logger.warning(f"Cannot add character: invalid first_appearance {first_appearance}")
            return False
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO characters (wiki_url, name, current_value, first_appearance)
                    VALUES (?, ?, ?, ?)
                """, (wiki_url, name, starting_value, first_appearance))
                conn.commit()
                logger.info(f"Added new character: {name} with starting value {starting_value}")
                return True
        except sqlite3.IntegrityError:
            logger.warning(f"Character {name} ({wiki_url}) already exists")
            return False
        except Exception as e:
            logger.error(f"Error adding character {name}: {e}")
            return False
    
    def get_character(self, wiki_url: str) -> Optional[Character]:
        """Get character by wiki URL"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT wiki_url, name, current_value, first_appearance
                    FROM characters WHERE wiki_url = ?
                """, (wiki_url,))
                row = cursor.fetchone()
                if row:
                    return Character(
                        wiki_url=row['wiki_url'],
                        name=row['name'],
                        current_value=row['current_value'],
                        first_appearance=row['first_appearance']
                    )
                return None
        except Exception as e:
            logger.error(f"Error getting character {wiki_url}: {e}")
            return None
    
    def get_character_current_value(self, wiki_url: str) -> Optional[int]:
        """Get current value for a character by wiki URL"""
        character = self.get_character(wiki_url)
        return character.current_value if character else None
    
    def update_character_value(self, wiki_url: str, new_value: int) -> bool:
        """Update character's current value"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE characters 
                    SET current_value = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE wiki_url = ?
                """, (new_value, wiki_url))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating character value for {wiki_url}: {e}")
            return False
    
    def get_all_characters(self) -> List[Character]:
        """Get all characters ordered by current value descending"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT wiki_url, name, current_value, first_appearance
                    FROM characters ORDER BY current_value DESC
                """)
                return [Character(
                    wiki_url=row['wiki_url'],
                    name=row['name'],
                    current_value=row['current_value'],
                    first_appearance=row['first_appearance']
                ) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting all characters: {e}")
            return []
    
    # Character history functions
    def add_character_change(self, wiki_url: str, chapter_number: int, 
                           value_change: int, new_value: int, reasoning: str) -> bool:
        """Add a character value change to history"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO character_history 
                    (character_wiki_url, chapter_number, value_change, new_value, reasoning)
                    VALUES (?, ?, ?, ?, ?)
                """, (wiki_url, chapter_number, value_change, new_value, reasoning))
                conn.commit()
                logger.info(f"Added character change for {wiki_url}: {value_change} in chapter {chapter_number}")
                return True
        except sqlite3.IntegrityError:
            logger.warning(f"Character change already exists for {wiki_url} in chapter {chapter_number}")
            return False
        except Exception as e:
            logger.error(f"Error adding character change: {e}")
            return False
    
    def get_character_history(self, wiki_url: str, limit: Optional[int] = None) -> List[Dict]:
        """Get character's value change history"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                query = """
                    SELECT chapter_number, value_change, new_value, reasoning, created_at
                    FROM character_history 
                    WHERE character_wiki_url = ?
                    ORDER BY chapter_number DESC
                """
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor.execute(query, (wiki_url,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting character history for {wiki_url}: {e}")
            return []
    
    def get_character_recent_activity(self, wiki_url: str, last_n_chapters: int = 5) -> List[Dict]:
        """Get character's recent activity for LLM context"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT chapter_number, value_change, new_value, reasoning
                    FROM character_history 
                    WHERE character_wiki_url = ?
                    ORDER BY chapter_number DESC
                    LIMIT ?
                """, (wiki_url, last_n_chapters))
                
                return [{
                    'chapter': row['chapter_number'],
                    'value_change': row['value_change'],
                    'reasoning': row['reasoning'],
                    'new_value': row['new_value']
                } for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting recent activity for {wiki_url}: {e}")
            return []   
 # Chapter management functions
    def add_chapter(self, number: int, title: str, wiki_url: str) -> bool:
        """Add a chapter to the database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO chapters (number, title, wiki_url, processed)
                    VALUES (?, ?, ?, FALSE)
                """, (number, title, wiki_url))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding chapter {number}: {e}")
            return False
    
    def mark_chapter_processed(self, chapter_number: int) -> bool:
        """Mark a chapter as processed"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE chapters 
                    SET processed = TRUE, processed_at = CURRENT_TIMESTAMP
                    WHERE number = ?
                """, (chapter_number,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error marking chapter {chapter_number} as processed: {e}")
            return False
    
    def is_chapter_processed(self, chapter_number: int) -> bool:
        """Check if a chapter has been processed"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT processed FROM chapters WHERE number = ?", (chapter_number,))
                row = cursor.fetchone()
                return bool(row and row['processed'])
        except Exception as e:
            logger.error(f"Error checking if chapter {chapter_number} is processed: {e}")
            return False
    
    def get_last_processed_chapter(self) -> Optional[int]:
        """Get the highest chapter number that has been processed"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT MAX(number) as last_chapter 
                    FROM chapters WHERE processed = TRUE
                """)
                row = cursor.fetchone()
                return row['last_chapter'] if row and row['last_chapter'] else None
        except Exception as e:
            logger.error(f"Error getting last processed chapter: {e}")
            return None
    
    # Market context functions for LLM analysis
    def get_top_characters(self, limit: int = 10) -> List[Dict]:
        """Get top characters by current value"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name, current_value, wiki_url
                    FROM characters 
                    ORDER BY current_value DESC 
                    LIMIT ?
                """, (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting top characters: {e}")
            return []
    
    def get_bottom_characters(self, limit: int = 10) -> List[Dict]:
        """Get bottom characters by current value"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name, current_value, wiki_url
                    FROM characters 
                    ORDER BY current_value ASC 
                    LIMIT ?
                """, (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting bottom characters: {e}")
            return []
    
    def get_recent_character_changes(self, last_n_chapters: int = 5) -> List[Dict]:
        """Get recent character changes across all characters"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT c.name, ch.chapter_number, ch.value_change, ch.reasoning, ch.new_value
                    FROM character_history ch
                    JOIN characters c ON ch.character_wiki_url = c.wiki_url
                    WHERE ch.chapter_number > (
                        SELECT COALESCE(MAX(chapter_number) - ?, 0) 
                        FROM character_history
                    )
                    ORDER BY ch.chapter_number DESC, ABS(ch.value_change) DESC
                """, (last_n_chapters,))
                
                return [{
                    'character': row['name'],
                    'chapter': row['chapter_number'],
                    'change': row['value_change'],
                    'reason': row['reasoning'],
                    'new_value': row['new_value']
                } for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting recent character changes: {e}")
            return []
    
    def get_character_count(self) -> int:
        """Get total number of characters in database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM characters")
                row = cursor.fetchone()
                return row['count'] if row else 0
        except Exception as e:
            logger.error(f"Error getting character count: {e}")
            return 0
    
    def get_current_market_context(self, last_n_chapters: int = 5) -> MarketContext:
        """Get comprehensive market context for LLM analysis"""
        return MarketContext(
            recent_changes=self.get_recent_character_changes(last_n_chapters),
            top_characters=self.get_top_characters(10),
            bottom_characters=self.get_bottom_characters(10),
            total_characters=self.get_character_count()
        )
    
    # Market snapshot caching functions
    def save_market_snapshot(self, chapter_number: int, market_context: MarketContext) -> bool:
        """Save market context snapshot for a chapter"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO market_snapshots 
                    (chapter_number, top_characters, bottom_characters, recent_changes, total_characters)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    chapter_number,
                    json.dumps(market_context.top_characters),
                    json.dumps(market_context.bottom_characters),
                    json.dumps(market_context.recent_changes),
                    market_context.total_characters
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving market snapshot for chapter {chapter_number}: {e}")
            return False
    
    def get_market_snapshot(self, chapter_number: int) -> Optional[MarketContext]:
        """Get cached market context for a chapter"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT top_characters, bottom_characters, recent_changes, total_characters
                    FROM market_snapshots WHERE chapter_number = ?
                """, (chapter_number,))
                row = cursor.fetchone()
                
                if row:
                    return MarketContext(
                        recent_changes=json.loads(row['recent_changes']),
                        top_characters=json.loads(row['top_characters']),
                        bottom_characters=json.loads(row['bottom_characters']),
                        total_characters=row['total_characters']
                    )
                return None
        except Exception as e:
            logger.error(f"Error getting market snapshot for chapter {chapter_number}: {e}")
            return None 
   # Batch operations for efficiency
    def process_character_changes(self, chapter_number: int, character_changes: List[CharacterChange], 
                                new_characters: List[Dict]) -> bool:
        """Process multiple character changes and new characters in a single transaction"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Add new characters first
                for new_char in new_characters:
                    try:
                        cursor.execute("""
                            INSERT INTO characters (wiki_url, name, current_value, first_appearance)
                            VALUES (?, ?, ?, ?)
                        """, (new_char['wiki_url'], new_char['name'], 
                             new_char['starting_value'], chapter_number))
                        logger.info(f"Added new character: {new_char['name']} with value {new_char['starting_value']}")
                    except sqlite3.IntegrityError:
                        logger.warning(f"Character {new_char['name']} already exists, skipping")
                
                # Process character changes
                for change in character_changes:
                    # Get current value
                    cursor.execute("SELECT current_value FROM characters WHERE wiki_url = ?", 
                                 (change.wiki_url,))
                    row = cursor.fetchone()
                    
                    if row:
                        current_value = row['current_value']
                        new_value = current_value + change.value_change
                        
                        # Update character's current value
                        cursor.execute("""
                            UPDATE characters 
                            SET current_value = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE wiki_url = ?
                        """, (new_value, change.wiki_url))
                        
                        # Add to history
                        cursor.execute("""
                            INSERT OR IGNORE INTO character_history 
                            (character_wiki_url, chapter_number, value_change, new_value, reasoning)
                            VALUES (?, ?, ?, ?, ?)
                        """, (change.wiki_url, chapter_number, change.value_change, 
                             new_value, change.reasoning))
                        
                        logger.info(f"Updated {change.name}: {current_value} -> {new_value} ({change.value_change:+d})")
                    else:
                        logger.warning(f"Character {change.name} not found for update")
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error processing character changes for chapter {chapter_number}: {e}")
            return False
    
    # Utility functions for data validation and cleanup
    def validate_database_integrity(self) -> Dict[str, bool]:
        """Validate database integrity and return status"""
        results = {
            'characters_table': False,
            'character_history_table': False,
            'chapters_table': False,
            'market_snapshots_table': False,
            'foreign_key_constraints': False
        }
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if all tables exist
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name IN ('characters', 'character_history', 'chapters', 'market_snapshots')
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                results['characters_table'] = 'characters' in tables
                results['character_history_table'] = 'character_history' in tables
                results['chapters_table'] = 'chapters' in tables
                results['market_snapshots_table'] = 'market_snapshots' in tables
                
                # Check foreign key constraints
                cursor.execute("PRAGMA foreign_key_check")
                fk_violations = cursor.fetchall()
                results['foreign_key_constraints'] = len(fk_violations) == 0
                
                if fk_violations:
                    logger.warning(f"Foreign key violations found: {fk_violations}")
                
        except Exception as e:
            logger.error(f"Error validating database integrity: {e}")
        
        return results
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        stats = {
            'total_characters': 0,
            'total_history_entries': 0,
            'total_chapters': 0,
            'processed_chapters': 0,
            'market_snapshots': 0
        }
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM characters")
                stats['total_characters'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM character_history")
                stats['total_history_entries'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM chapters")
                stats['total_chapters'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM chapters WHERE processed = TRUE")
                stats['processed_chapters'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM market_snapshots")
                stats['market_snapshots'] = cursor.fetchone()[0]
                
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
        
        return stats

# Convenience function to create database manager instance
def create_database_manager(db_path: str = "one_piece_tracker.db") -> DatabaseManager:
    """Create and return a DatabaseManager instance"""
    return DatabaseManager(db_path)

if __name__ == "__main__":
    # Test the database setup
    db = create_database_manager()
    
    # Validate database integrity
    integrity = db.validate_database_integrity()
    print("Database Integrity Check:")
    for check, status in integrity.items():
        print(f"  {check}: {'✓' if status else '✗'}")
    
    # Show database stats
    stats = db.get_database_stats()
    print("\nDatabase Statistics:")
    for stat, value in stats.items():
        print(f"  {stat}: {value}")
    
    print("\nDatabase setup completed successfully!")