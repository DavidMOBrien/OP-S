#!/usr/bin/env python3
"""
Simple database query script for the web interface.
Usage: python3 query_database.py "SQL_QUERY"
"""

import sys
import json
from database import Database

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No query provided"}))
        sys.exit(1)
    
    query = sys.argv[1]
    db = Database("one_piece_stocks.db")
    
    try:
        # Execute the query using the Database class method
        import sqlite3
        conn = sqlite3.connect("one_piece_stocks.db")
        cursor = conn.cursor()
        cursor.execute(query)
        
        # Fetch results
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        # Convert to list of dicts
        result = []
        for row in rows:
            row_dict = {}
            for i, col in enumerate(columns):
                row_dict[col] = row[i]
            result.append(row_dict)
        
        conn.close()
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()

