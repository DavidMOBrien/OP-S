# One Piece Character Stock Tracker

A system that tracks One Piece character "stock" values across chapters, analyzing their narrative importance, achievements, and setbacks using LLM analysis of wiki chapter summaries.

## Overview

This project has two main components:

1. **Offline Data Generation**: Scrapes One Piece wiki chapters, uses an LLM to analyze character performance, and tracks stock value changes over time
2. **Web Interface** (Coming Soon): View and compare character stock trajectories

## How It Works

### Stock Mechanics

- Each character starts with an **initial stock value** when first introduced, determined by the LLM based on how they're presented and the current market scale
- Every chapter, the LLM analyzes what happens and assigns **stock changes** (deltas) to each character
- A character's **current stock value** = initial value + sum of all changes
- Stock values have a **floor of 0** (cannot go negative)
- There are **NO CAPS** on how much stock can change - big moments create big moves!

### The "Market"

The system tracks a dynamic market of character stocks that evolves naturally:
- Early series: Characters might be in the 100-300 range
- Mid series: Top characters might reach 500-1,500
- Late series: Major characters could reach 2,000+

This happens organically as the stakes increase and major events occur.

### LLM Analysis

The LLM analyzes each chapter with:
- **Top 10 stocks market-wide** for context
- **Market statistics** (average, median, total characters)
- **Each character's recent history** (last 3 chapters of changes)
- **Strict information boundary**: Only uses knowledge up to the current chapter

Example: When Kuro is first introduced as a butler, he starts with a modest value (~95). When it's later revealed he's actually Captain Kuro, a legendary pirate, his stock skyrockets (+180 or more).

## Installation

### Prerequisites

- Python 3.8+
- OpenAI API key

### Setup

1. Clone the repository:
```bash
cd one-piece-stocks
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure your OpenAI API key:

Create a `.env` file:
```bash
cp .env.template .env
```

Then edit `.env` and add your actual API key:
```
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

## Usage

### Initialize the Database

First time setup:
```bash
python generate_offline_data.py --init
```

### Generate Stock Data

**Process first 10 chapters (recommended for testing):**
```bash
python generate_offline_data.py --max 10
```

**Process specific range:**
```bash
python generate_offline_data.py --start 1 --end 50
```

**Process specific chapters:**
```bash
python generate_offline_data.py --chapters "1,5,10,25,50"
```

**Process all available chapters:**
```bash
python generate_offline_data.py --start 1
```

**Use a different model:**
```bash
python generate_offline_data.py --max 10 --model gpt-4o
# or
python generate_offline_data.py --max 10 --model gpt-4o-mini
```

### Options

```
--start N         First chapter to process (default: 1)
--end N           Last chapter to process (default: all)
--max N           Maximum number of chapters to process
--chapters "X,Y"  Process specific chapters (comma-separated)
--db PATH         Database path (default: one_piece_stocks.db)
--model NAME      OpenAI model (default: gpt-4o)
--delay N         Delay between wiki requests in seconds (default: 1.0)
--init            Initialize database schema
--skip-crawl      Skip web crawling, use existing data
--verbose, -v     Print prompts and LLM responses for monitoring
```

## Architecture

### Data Flow

```
1. Wiki Crawler
   ↓ (scrapes chapter summaries + character links)
2. Database Storage
   ↓ (builds market context)
3. LLM Analyzer
   ↓ (analyzes chapter, outputs stock changes)
4. Database Storage
   ↓ (updates stock history, market context)
5. Next Chapter
```

### Database Schema

**chapters**: Chapter metadata (title, URL, description, arc)
**characters**: Character info (name, href, first appearance, initial value)
**market_events**: Stock change events (character, chapter, delta, reasoning)
**character_stock_history**: Computed cumulative values per chapter
**market_context**: Market snapshots (top 10, statistics per chapter)

### Character Identification

Characters are identified by their **wiki href** (e.g., `/wiki/Monkey_D._Luffy`). This automatically handles:
- Name variations (Luffy, Straw Hat Luffy, Monkey D. Luffy all link to same page)
- Consistent tracking across chapters
- No manual character list needed

## Design Philosophy

### No Artificial Constraints

- Stock changes are **unbounded** - the LLM decides impact based on narrative weight
- Initial values are **dynamic** - determined by how characters are introduced and current market scale
- The market **evolves naturally** - stakes and values grow as the story progresses

### Information Boundary

The LLM only uses information available up to the current chapter:
- A character introduced as minor stays minor until revelations occur
- Future knowledge doesn't influence past assessments
- Creates authentic "stock market" feel with surprises

### Progressive Growth

Processing 1000+ chapters progressively:
- No recalibration needed
- Each chapter builds on the last
- Natural scaling as stakes increase
- Characters can have dramatic rises or falls

## Examples

### Chapter 1 (Beginning of Series)
- Market: Empty (first chapter)
- Luffy introduced: Starting value ~150
- Shanks introduced: Starting value ~200 (established pirate)

### Chapter 50 (After major arc)
- Top stocks: Luffy (450), Zoro (380), Mihawk (350)...
- Market average: ~180
- New villain introduced: Starting value ~250 (based on reputation)

### Chapter 500 (Mid-series)
- Top stocks: Luffy (2,450), Admirals (1,800+)...
- Market average: ~520
- Major power-up moment: Luffy +200

## File Structure

```
one-piece-stocks/
├── database.py              # Database operations
├── wiki_crawler.py          # Wiki scraping
├── llm_analyzer.py          # LLM analysis with prompt
├── generate_offline_data.py # Main orchestration script
├── requirements.txt         # Python dependencies
├── config.example.py        # Configuration template
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Future Work

- **Web Interface**: View character trajectories, compare stocks, see market history
- **Advanced Analytics**: Trend analysis, correlation between characters, arc-level insights
- **Optimization**: Batch processing, caching, parallel LLM calls
- **Enhanced Parsing**: Better character detection, more detailed event extraction

## Cost Considerations

Using OpenAI APIs (default: gpt-5-nano-2025-08-07):
- **gpt-5-nano-2025-08-07**: Default model (check OpenAI pricing for latest rates)
- **gpt-4o**: ~$0.01-0.015 per chapter (good quality, well-tested)
- **gpt-4o-mini**: ~$0.0005-0.001 per chapter (budget option)

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Areas of interest:
- Improved character detection from wiki parsing
- Better prompt engineering for consistent analysis
- Web interface development
- Additional data sources beyond wiki summaries

## Disclaimer

This is a fan project for educational purposes. One Piece is © Eiichiro Oda. Wiki content is from the One Piece Wiki (Fandom).

