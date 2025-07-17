"""
Flask web application for One Piece Character Tracker
"""
import sqlite3
import os
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database configuration
DATABASE_PATH = 'one_piece_tracker.db'

def get_db_connection():
    """Get database connection with error handling"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
        return conn
    except sqlite3.Error as e:
        app.logger.error(f"Database connection error: {e}")
        return None

def init_db():
    """Initialize database if it doesn't exist"""
    if not os.path.exists(DATABASE_PATH):
        app.logger.warning(f"Database {DATABASE_PATH} not found. Web app will show empty data until data gathering script is run.")
        return False
    
    # Verify database has expected tables
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            expected_tables = ['characters', 'character_history', 'chapters']
            
            missing_tables = [table for table in expected_tables if table not in tables]
            if missing_tables:
                app.logger.warning(f"Missing database tables: {missing_tables}")
                return False
            return True
        except sqlite3.Error as e:
            app.logger.error(f"Database verification error: {e}")
            return False
        finally:
            conn.close()
    return False

def check_database_health():
    """Check if database is accessible and has data"""
    try:
        conn = get_db_connection()
        if not conn:
            return False, "Database connection failed"
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM characters")
        character_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM character_history")
        history_count = cursor.fetchone()[0]
        
        conn.close()
        
        if character_count == 0:
            return False, "No character data found. Please run the data gathering script first."
        
        return True, f"Database healthy: {character_count} characters, {history_count} history entries"
        
    except sqlite3.Error as e:
        app.logger.error(f"Database health check failed: {e}")
        return False, f"Database error: {str(e)}"
    except Exception as e:
        app.logger.error(f"Unexpected error in health check: {e}")
        return False, "Unexpected database error"

@app.route('/health')
def health_check():
    """Health check endpoint for deployment monitoring"""
    is_healthy, message = check_database_health()
    if is_healthy:
        return jsonify({'status': 'healthy', 'message': message}), 200
    else:
        return jsonify({'status': 'unhealthy', 'message': message}), 503

@app.route('/')
def index():
    """Main page showing character list"""
    try:
        # Check database health first
        is_healthy, health_message = check_database_health()
        if not is_healthy:
            return render_template('error.html', error=health_message)
        
        conn = get_db_connection()
        if not conn:
            return render_template('error.html', error="Database connection failed")
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT wiki_url, name, current_value, first_appearance 
            FROM characters 
            ORDER BY current_value DESC
        """)
        characters = cursor.fetchall()
        conn.close()
        
        # Handle empty results gracefully
        if not characters:
            return render_template('index.html', characters=[], 
                                 message="No character data available. Please run the data gathering script.")
        
        return render_template('index.html', characters=characters)
    
    except sqlite3.Error as e:
        app.logger.error(f"Database error in index route: {e}")
        return render_template('error.html', error="Failed to load character data. Please check if the database is accessible.")
    except Exception as e:
        app.logger.error(f"Unexpected error in index route: {e}")
        return render_template('error.html', error="An unexpected error occurred. Please try again later.")

@app.route('/api/characters')
def api_characters():
    """API endpoint to get all characters with optional filtering"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        # Get query parameters
        search = request.args.get('search', '').strip()
        sort_by = request.args.get('sort', 'value-desc')
        value_filter = request.args.get('value_range', 'all')
        chapter_filter = request.args.get('chapter_range', 'all')
        
        # Build base query
        query = """
            SELECT wiki_url, name, current_value, first_appearance 
            FROM characters 
            WHERE 1=1
        """
        params = []
        
        # Add search filter
        if search:
            query += " AND LOWER(name) LIKE ?"
            params.append(f"%{search.lower()}%")
        
        # Add value range filter
        if value_filter == 'high':
            query += " AND current_value >= 500"
        elif value_filter == 'medium':
            query += " AND current_value >= 100 AND current_value < 500"
        elif value_filter == 'low':
            query += " AND current_value >= 1 AND current_value < 100"
        elif value_filter == 'zero':
            query += " AND current_value <= 0"
        
        # Add chapter range filter
        if chapter_filter == 'early':
            query += " AND first_appearance <= 100"
        elif chapter_filter == 'pre-timeskip':
            query += " AND first_appearance > 100 AND first_appearance <= 597"
        elif chapter_filter == 'post-timeskip':
            query += " AND first_appearance > 597"
        
        # Add sorting
        if sort_by == 'value-asc':
            query += " ORDER BY current_value ASC"
        elif sort_by == 'name-asc':
            query += " ORDER BY name ASC"
        elif sort_by == 'name-desc':
            query += " ORDER BY name DESC"
        elif sort_by == 'chapter-asc':
            query += " ORDER BY first_appearance ASC"
        elif sort_by == 'chapter-desc':
            query += " ORDER BY first_appearance DESC"
        else:  # default: value-desc
            query += " ORDER BY current_value DESC"
        
        cursor = conn.cursor()
        cursor.execute(query, params)
        characters = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'characters': characters,
            'total': len(characters),
            'filters': {
                'search': search,
                'sort': sort_by,
                'value_range': value_filter,
                'chapter_range': chapter_filter
            }
        })
    
    except sqlite3.Error as e:
        app.logger.error(f"Database error in API: {e}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        app.logger.error(f"Unexpected error in API: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/character/<path:wiki_url>/history')
def api_character_history(wiki_url):
    """API endpoint to get character history data for charts"""
    try:
        # Validate wiki_url parameter
        if not wiki_url or not wiki_url.strip():
            return jsonify({'error': 'Invalid character URL'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = conn.cursor()
        
        # Get character info
        cursor.execute("""
            SELECT wiki_url, name, current_value, first_appearance 
            FROM characters 
            WHERE wiki_url = ?
        """, (wiki_url,))
        character = cursor.fetchone()
        
        if not character:
            conn.close()
            return jsonify({'error': 'Character not found', 'wiki_url': wiki_url}), 404
        
        # Get character history with cumulative values
        cursor.execute("""
            SELECT chapter_number, value_change, reasoning 
            FROM character_history 
            WHERE character_wiki_url = ? 
            ORDER BY chapter_number
        """, (wiki_url,))
        history_rows = cursor.fetchall()
        conn.close()
        
        # Calculate cumulative values for chart
        history_data = []
        cumulative_value = 0
        
        # Start with the character's starting value (first appearance)
        if history_rows:
            # Find the starting value by working backwards from current value
            total_changes = sum(row['value_change'] for row in history_rows)
            starting_value = character['current_value'] - total_changes
            cumulative_value = starting_value
            
            # Add starting point
            history_data.append({
                'chapter': character['first_appearance'],
                'value': starting_value,
                'change': 0,
                'reasoning': f"First appearance in Chapter {character['first_appearance']}"
            })
        else:
            # Character exists but has no history - just show starting point
            history_data.append({
                'chapter': character['first_appearance'],
                'value': character['current_value'],
                'change': 0,
                'reasoning': f"First appearance in Chapter {character['first_appearance']} (no value changes recorded)"
            })
            cumulative_value = character['current_value']
        
        # Add each change
        for row in history_rows:
            cumulative_value += row['value_change']
            history_data.append({
                'chapter': row['chapter_number'],
                'value': cumulative_value,
                'change': row['value_change'],
                'reasoning': row['reasoning']
            })
        
        return jsonify({
            'character': {
                'name': character['name'],
                'wiki_url': character['wiki_url'],
                'current_value': character['current_value'],
                'first_appearance': character['first_appearance']
            },
            'history': history_data
        })
    
    except sqlite3.Error as e:
        app.logger.error(f"Database error in character history API: {e}")
        return jsonify({'error': 'Database error occurred while fetching character history'}), 500
    except Exception as e:
        app.logger.error(f"Unexpected error in character history API: {e}")
        return jsonify({'error': 'Internal server error occurred'}), 500

@app.route('/charts')
def charts():
    """Charts page for comparing character histories"""
    try:
        # Check database health first
        is_healthy, health_message = check_database_health()
        if not is_healthy:
            return render_template('error.html', error=health_message)
        
        conn = get_db_connection()
        if not conn:
            return render_template('error.html', error="Database connection failed")
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT wiki_url, name, current_value, first_appearance 
            FROM characters 
            ORDER BY name ASC
        """)
        characters = cursor.fetchall()
        conn.close()
        
        # Handle empty results gracefully
        if not characters:
            return render_template('charts.html', characters=[], 
                                 message="No character data available for charts. Please run the data gathering script.")
        
        return render_template('charts.html', characters=characters)
    
    except sqlite3.Error as e:
        app.logger.error(f"Database error in charts route: {e}")
        return render_template('error.html', error="Failed to load character data for charts. Please check if the database is accessible.")
    except Exception as e:
        app.logger.error(f"Unexpected error in charts route: {e}")
        return render_template('error.html', error="An unexpected error occurred while loading charts. Please try again later.")

@app.route('/character/<path:wiki_url>')
def character_detail(wiki_url):
    """Character detail page"""
    try:
        conn = get_db_connection()
        if not conn:
            return render_template('error.html', error="Database connection failed")
        
        cursor = conn.cursor()
        
        # Get character info
        cursor.execute("""
            SELECT wiki_url, name, current_value, first_appearance 
            FROM characters 
            WHERE wiki_url = ?
        """, (wiki_url,))
        character = cursor.fetchone()
        
        if not character:
            conn.close()
            return render_template('error.html', error="Character not found"), 404
        
        # Get character history with chapter titles
        cursor.execute("""
            SELECT ch.chapter_number, ch.value_change, ch.reasoning, c.title as chapter_title
            FROM character_history ch
            LEFT JOIN chapters c ON ch.chapter_number = c.number
            WHERE ch.character_wiki_url = ? 
            ORDER BY ch.chapter_number
        """, (wiki_url,))
        history = cursor.fetchall()
        
        # Get navigation data - previous and next characters by current value
        cursor.execute("""
            SELECT wiki_url, name, current_value 
            FROM characters 
            WHERE current_value > ? 
            ORDER BY current_value ASC 
            LIMIT 1
        """, (character['current_value'],))
        next_character = cursor.fetchone()
        
        cursor.execute("""
            SELECT wiki_url, name, current_value 
            FROM characters 
            WHERE current_value < ? 
            ORDER BY current_value DESC 
            LIMIT 1
        """, (character['current_value'],))
        prev_character = cursor.fetchone()
        
        # Get related characters (characters that appear in same chapters)
        cursor.execute("""
            SELECT DISTINCT c.wiki_url, c.name, c.current_value
            FROM characters c
            JOIN character_history ch ON c.wiki_url = ch.character_wiki_url
            WHERE ch.chapter_number IN (
                SELECT chapter_number 
                FROM character_history 
                WHERE character_wiki_url = ?
            )
            AND c.wiki_url != ?
            ORDER BY c.current_value DESC
            LIMIT 5
        """, (wiki_url, wiki_url))
        related_characters = cursor.fetchall()
        
        # Calculate character statistics
        if history:
            total_changes = sum(h['value_change'] for h in history)
            positive_changes = sum(h['value_change'] for h in history if h['value_change'] > 0)
            negative_changes = sum(h['value_change'] for h in history if h['value_change'] < 0)
            chapter_span = max(h['chapter_number'] for h in history) - min(h['chapter_number'] for h in history) if len(history) > 1 else 0
            
            stats = {
                'total_changes': len(history),
                'total_value_change': total_changes,
                'positive_changes': positive_changes,
                'negative_changes': negative_changes,
                'chapter_span': chapter_span,
                'avg_change': round(total_changes / len(history), 1) if history else 0
            }
        else:
            stats = None
        
        conn.close()
        
        return render_template('character.html', 
                             character=character, 
                             history=history, 
                             next_character=next_character,
                             prev_character=prev_character,
                             related_characters=related_characters,
                             stats=stats)
    
    except sqlite3.Error as e:
        app.logger.error(f"Database error in character detail: {e}")
        return render_template('error.html', error="Failed to load character data")
    except Exception as e:
        app.logger.error(f"Unexpected error in character detail: {e}")
        return render_template('error.html', error="An unexpected error occurred")

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    app.logger.error(f"Internal server error: {error}")
    return render_template('error.html', error="Internal server error"), 500

if __name__ == '__main__':
    # Initialize database on startup
    db_initialized = init_db()
    if not db_initialized:
        app.logger.warning("Database initialization failed or incomplete")
    
    # Configure from environment
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5001))
    
    # Run the app
    app.logger.info(f"Starting One Piece Character Tracker on {host}:{port}")
    app.run(debug=debug_mode, host=host, port=port)