"""Database operations for One Piece Stock Tracker."""

import sqlite3
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json


class Database:
    """Handles all database operations for the stock tracker."""
    
    def __init__(self, db_path: str = "one_piece_stocks.db"):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """Connect to the database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        
    def initialize_schema(self):
        """Create all necessary tables."""
        cursor = self.conn.cursor()
        
        # Chapters table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chapters (
                chapter_id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                raw_description TEXT,
                arc_name TEXT,
                processed_timestamp TEXT,
                processed BOOLEAN DEFAULT 0
            )
        """)
        
        # Characters table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS characters (
                character_id TEXT PRIMARY KEY,
                canonical_name TEXT NOT NULL,
                href TEXT NOT NULL UNIQUE,
                first_appearance_chapter INTEGER,
                initial_stock_value REAL,
                FOREIGN KEY (first_appearance_chapter) REFERENCES chapters(chapter_id)
            )
        """)
        
        # Market activity events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                chapter_id INTEGER NOT NULL,
                character_id TEXT NOT NULL,
                character_href TEXT NOT NULL,
                stock_change REAL NOT NULL,
                confidence_score REAL NOT NULL,
                description TEXT,
                is_first_appearance BOOLEAN DEFAULT 0,
                FOREIGN KEY (chapter_id) REFERENCES chapters(chapter_id),
                FOREIGN KEY (character_id) REFERENCES characters(character_id)
            )
        """)
        
        # Character stock history (computed/cached for performance)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS character_stock_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id TEXT NOT NULL,
                chapter_id INTEGER NOT NULL,
                cumulative_stock_value REAL NOT NULL,
                chapter_change REAL NOT NULL,
                market_rank INTEGER,
                FOREIGN KEY (character_id) REFERENCES characters(character_id),
                FOREIGN KEY (chapter_id) REFERENCES chapters(chapter_id),
                UNIQUE(character_id, chapter_id)
            )
        """)
        
        # Market context table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_context (
                chapter_id INTEGER PRIMARY KEY,
                top_ten_stocks TEXT,  -- JSON array
                active_characters TEXT,  -- JSON array
                arc_name TEXT,
                average_stock_value REAL,
                median_stock_value REAL,
                total_characters INTEGER,
                FOREIGN KEY (chapter_id) REFERENCES chapters(chapter_id)
            )
        """)
        
        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_market_events_chapter 
            ON market_events(chapter_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_market_events_character 
            ON market_events(character_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stock_history_character 
            ON character_stock_history(character_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stock_history_chapter 
            ON character_stock_history(chapter_id)
        """)
        
        self.conn.commit()
        
    def save_chapter(self, chapter_id: int, title: str, url: str, 
                     raw_description: str, arc_name: str = None):
        """Save chapter information."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO chapters 
            (chapter_id, title, url, raw_description, arc_name)
            VALUES (?, ?, ?, ?, ?)
        """, (chapter_id, title, url, raw_description, arc_name))
        self.conn.commit()
        
    def get_chapter(self, chapter_id: int) -> Optional[Dict]:
        """Get chapter information."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM chapters WHERE chapter_id = ?
        """, (chapter_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
        
    def mark_chapter_processed(self, chapter_id: int):
        """Mark a chapter as processed."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE chapters 
            SET processed = 1, processed_timestamp = ?
            WHERE chapter_id = ?
        """, (datetime.now().isoformat(), chapter_id))
        self.conn.commit()
        
    def is_chapter_processed(self, chapter_id: int) -> bool:
        """Check if a chapter has been processed."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT processed FROM chapters WHERE chapter_id = ?
        """, (chapter_id,))
        row = cursor.fetchone()
        return row['processed'] == 1 if row else False
        
    def save_character(self, character_id: str, canonical_name: str, 
                      href: str, first_appearance_chapter: int,
                      initial_stock_value: float):
        """Save a new character."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO characters 
            (character_id, canonical_name, href, first_appearance_chapter, initial_stock_value)
            VALUES (?, ?, ?, ?, ?)
        """, (character_id, canonical_name, href, first_appearance_chapter, initial_stock_value))
        self.conn.commit()
        
    def get_character(self, character_id: str) -> Optional[Dict]:
        """Get character information."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM characters WHERE character_id = ?
        """, (character_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
        
    def character_exists(self, character_id: str) -> bool:
        """Check if a character exists."""
        return self.get_character(character_id) is not None
        
    def save_market_event(self, chapter_id: int, character_id: str,
                         character_href: str, stock_change: float,
                         confidence_score: float, description: str,
                         is_first_appearance: bool = False):
        """Save a market event."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO market_events 
            (chapter_id, character_id, character_href, stock_change, 
             confidence_score, description, is_first_appearance)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (chapter_id, character_id, character_href, stock_change,
              confidence_score, description, is_first_appearance))
        self.conn.commit()
        
    def get_character_history(self, character_id: str, 
                             up_to_chapter: int = None,
                             limit: int = 3) -> List[Dict]:
        """Get recent history for a character with cumulative stock values."""
        cursor = self.conn.cursor()
        
        if up_to_chapter:
            cursor.execute("""
                SELECT me.*, c.chapter_id, c.title as chapter_title
                FROM market_events me
                JOIN chapters c ON me.chapter_id = c.chapter_id
                WHERE me.character_id = ? AND me.chapter_id <= ?
                ORDER BY me.chapter_id DESC
                LIMIT ?
            """, (character_id, up_to_chapter, limit))
        else:
            cursor.execute("""
                SELECT me.*, c.chapter_id, c.title as chapter_title
                FROM market_events me
                JOIN chapters c ON me.chapter_id = c.chapter_id
                WHERE me.character_id = ?
                ORDER BY me.chapter_id DESC
                LIMIT ?
            """, (character_id, limit))
            
        history = [dict(row) for row in cursor.fetchall()]
        
        # Add cumulative stock value AFTER each event
        for event in history:
            event['current_stock'] = self.calculate_current_stock(character_id, event['chapter_id'])
        
        return history
        
    def calculate_current_stock(self, character_id: str, 
                               up_to_chapter: int = None) -> float:
        """Calculate cumulative stock value for a character (floor at 0)."""
        cursor = self.conn.cursor()
        
        # Get initial value
        character = self.get_character(character_id)
        if not character:
            return 0.0
            
        initial_value = character['initial_stock_value']
        
        # Sum all changes up to this chapter
        if up_to_chapter:
            cursor.execute("""
                SELECT SUM(stock_change) as total_change
                FROM market_events
                WHERE character_id = ? AND chapter_id <= ?
            """, (character_id, up_to_chapter))
        else:
            cursor.execute("""
                SELECT SUM(stock_change) as total_change
                FROM market_events
                WHERE character_id = ?
            """, (character_id,))
            
        row = cursor.fetchone()
        total_change = row['total_change'] if row['total_change'] else 0.0
        
        # Floor at 0
        return max(0.0, initial_value + total_change)
        
    def get_top_stocks(self, up_to_chapter: int = None, limit: int = 10) -> List[Dict]:
        """Get top N stocks by current value."""
        # Get all characters
        cursor = self.conn.cursor()
        
        if up_to_chapter:
            cursor.execute("""
                SELECT DISTINCT character_id 
                FROM market_events 
                WHERE chapter_id <= ?
            """, (up_to_chapter,))
        else:
            cursor.execute("""
                SELECT DISTINCT character_id 
                FROM market_events
            """)
            
        character_ids = [row['character_id'] for row in cursor.fetchall()]
        
        # Calculate current stock for each
        stocks = []
        for char_id in character_ids:
            value = self.calculate_current_stock(char_id, up_to_chapter)
            character = self.get_character(char_id)
            stocks.append({
                'character_id': char_id,
                'character_name': character['canonical_name'],
                'stock_value': value
            })
            
        # Sort and return top N
        stocks.sort(key=lambda x: x['stock_value'], reverse=True)
        return stocks[:limit]
        
    def get_market_statistics(self, up_to_chapter: int = None) -> Dict:
        """Get market-wide statistics."""
        cursor = self.conn.cursor()
        
        if up_to_chapter:
            cursor.execute("""
                SELECT DISTINCT character_id 
                FROM market_events 
                WHERE chapter_id <= ?
            """, (up_to_chapter,))
        else:
            cursor.execute("""
                SELECT DISTINCT character_id 
                FROM market_events
            """)
            
        character_ids = [row['character_id'] for row in cursor.fetchall()]
        
        if not character_ids:
            return {
                'average': 0.0,
                'median': 0.0,
                'total_characters': 0
            }
        
        # Calculate all stock values
        stock_values = [
            self.calculate_current_stock(char_id, up_to_chapter)
            for char_id in character_ids
        ]
        
        stock_values.sort()
        n = len(stock_values)
        
        return {
            'average': sum(stock_values) / n if n > 0 else 0.0,
            'median': stock_values[n // 2] if n > 0 else 0.0,
            'total_characters': n
        }
        
    def save_market_context(self, chapter_id: int):
        """Save market context snapshot for a chapter."""
        cursor = self.conn.cursor()
        
        # Get previous chapter
        prev_chapter = chapter_id - 1 if chapter_id > 1 else None
        
        # Get top 10 stocks
        top_ten = self.get_top_stocks(up_to_chapter=prev_chapter, limit=10)
        
        # Get statistics
        stats = self.get_market_statistics(up_to_chapter=prev_chapter)
        
        # Get active characters (characters in this chapter)
        cursor.execute("""
            SELECT DISTINCT character_id 
            FROM market_events 
            WHERE chapter_id = ?
        """, (chapter_id,))
        active_characters = [row['character_id'] for row in cursor.fetchall()]
        
        # Get arc name from chapter
        chapter = self.get_chapter(chapter_id)
        arc_name = chapter['arc_name'] if chapter else None
        
        # Save context
        cursor.execute("""
            INSERT OR REPLACE INTO market_context
            (chapter_id, top_ten_stocks, active_characters, arc_name,
             average_stock_value, median_stock_value, total_characters)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (chapter_id, json.dumps(top_ten), json.dumps(active_characters),
              arc_name, stats['average'], stats['median'], stats['total_characters']))
        
        self.conn.commit()
        
    def update_stock_history(self, chapter_id: int):
        """Update stock history for all characters after processing a chapter."""
        cursor = self.conn.cursor()
        
        # Get all characters with events in this chapter
        cursor.execute("""
            SELECT DISTINCT character_id, stock_change
            FROM market_events
            WHERE chapter_id = ?
        """, (chapter_id,))
        
        for row in cursor.fetchall():
            character_id = row['character_id']
            chapter_change = row['stock_change']
            
            # Calculate cumulative value
            cumulative_value = self.calculate_current_stock(character_id, chapter_id)
            
            # Get market rank
            top_stocks = self.get_top_stocks(up_to_chapter=chapter_id, limit=999999)
            rank = next((i + 1 for i, s in enumerate(top_stocks) 
                        if s['character_id'] == character_id), None)
            
            # Save to history
            cursor.execute("""
                INSERT OR REPLACE INTO character_stock_history
                (character_id, chapter_id, cumulative_stock_value, 
                 chapter_change, market_rank)
                VALUES (?, ?, ?, ?, ?)
            """, (character_id, chapter_id, cumulative_value, chapter_change, rank))
            
        self.conn.commit()
        
    def get_all_characters_in_chapter(self, chapter_id: int) -> List[str]:
        """Get all character IDs that appear in a chapter."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT character_id 
            FROM market_events 
            WHERE chapter_id = ?
        """, (chapter_id,))
        return [row['character_id'] for row in cursor.fetchall()]

