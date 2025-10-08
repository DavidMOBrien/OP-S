import { queryDatabase } from './python-bridge';

export interface Character {
  character_id: string;
  canonical_name: string;
  href: string;
  first_appearance_chapter: number;
  initial_stock_value: number;
  current_stock?: number;
  last_chapter?: number;
}

export interface Chapter {
  chapter_id: number;
  title: string;
  url: string;
  raw_description?: string;
  arc_name?: string;
  processed: number;
  processed_timestamp?: string;
}

export interface MarketEvent {
  event_id: number;
  chapter_id: number;
  character_id: string;
  character_href: string;
  stock_change: number;
  confidence_score: number;
  description: string;
}

export interface CharacterStockHistory {
  character_id: string;
  chapter_id: number;
  cumulative_stock_value: number;
  chapter_change: number;
  market_rank?: number;
  chapter_description?: string;
}

export async function getAllCharacters(): Promise<Character[]> {
  // Get all characters with their latest stock values
  const result = await queryDatabase(`
    SELECT 
      c.*,
      COALESCE(
        (SELECT cumulative_stock_value 
         FROM character_stock_history csh 
         WHERE csh.character_id = c.character_id 
         ORDER BY chapter_id DESC LIMIT 1),
        c.initial_stock_value
      ) as current_stock,
      (SELECT MAX(chapter_id) 
       FROM character_stock_history csh 
       WHERE csh.character_id = c.character_id) as last_chapter
    FROM characters c
    ORDER BY current_stock DESC
  `);
  return result as Character[];
}

export async function getCharacter(characterId: string): Promise<Character | undefined> {
  const result = await queryDatabase(`
    SELECT 
      c.*,
      COALESCE(
        (SELECT cumulative_stock_value 
         FROM character_stock_history csh 
         WHERE csh.character_id = c.character_id 
         ORDER BY chapter_id DESC LIMIT 1),
        c.initial_stock_value
      ) as current_stock,
      (SELECT MAX(chapter_id) 
       FROM character_stock_history csh 
       WHERE csh.character_id = c.character_id) as last_chapter
    FROM characters c
    WHERE c.character_id = '${characterId.replace(/'/g, "''")}'
  `);
  return result[0] as Character | undefined;
}

export async function getAllChapters(): Promise<Chapter[]> {
  const result = await queryDatabase(
    'SELECT * FROM chapters WHERE processed = 1 ORDER BY chapter_id ASC'
  );
  return result as Chapter[];
}

export async function getChapter(chapterNumber: number): Promise<Chapter | undefined> {
  const result = await queryDatabase(
    `SELECT * FROM chapters WHERE chapter_id = ${chapterNumber}`
  );
  return result[0] as Chapter | undefined;
}

export async function getChapterEvents(chapterNumber: number): Promise<MarketEvent[]> {
  const result = await queryDatabase(`
    SELECT * FROM market_events
    WHERE chapter_id = ${chapterNumber}
    ORDER BY event_id ASC
  `);
  return result as MarketEvent[];
}

export async function getCharacterHistory(characterId: string): Promise<CharacterStockHistory[]> {
  const result = await queryDatabase(`
    SELECT 
      csh.*,
      csh.chapter_reasoning as chapter_description
    FROM character_stock_history csh
    WHERE csh.character_id = '${characterId.replace(/'/g, "''")}'
    ORDER BY csh.chapter_id ASC
  `);
  return result as CharacterStockHistory[];
}

export async function getCharacterChapterEvents(characterId: string, chapterNumber: number): Promise<MarketEvent[]> {
  const result = await queryDatabase(`
    SELECT *
    FROM market_events
    WHERE character_id = '${characterId.replace(/'/g, "''")}' AND chapter_id = ${chapterNumber}
    ORDER BY event_id ASC
  `);
  return result as MarketEvent[];
}

export async function getCharacterChapterReasoning(characterId: string, chapterNumber: number): Promise<string | null> {
  const result = await queryDatabase(`
    SELECT chapter_reasoning
    FROM character_stock_history
    WHERE character_id = '${characterId.replace(/'/g, "''")}' AND chapter_id = ${chapterNumber}
  `);
  return result.length > 0 ? result[0].chapter_reasoning : null;
}

export async function getTopCharacters(limit: number = 10): Promise<Character[]> {
  const result = await queryDatabase(`
    SELECT 
      c.*,
      COALESCE(
        (SELECT cumulative_stock_value 
         FROM character_stock_history csh 
         WHERE csh.character_id = c.character_id 
         ORDER BY chapter_id DESC LIMIT 1),
        c.initial_stock_value
      ) as current_stock,
      (SELECT MAX(chapter_id) 
       FROM character_stock_history csh 
       WHERE csh.character_id = c.character_id) as last_chapter
    FROM characters c
    ORDER BY current_stock DESC
    LIMIT ${limit}
  `);
  return result as Character[];
}

export async function getCharactersInChapter(chapterNumber: number): Promise<Character[]> {
  const result = await queryDatabase(`
    SELECT DISTINCT 
      c.*,
      COALESCE(
        (SELECT cumulative_stock_value 
         FROM character_stock_history csh 
         WHERE csh.character_id = c.character_id 
         AND csh.chapter_id = ${chapterNumber}),
        c.initial_stock_value
      ) as current_stock
    FROM characters c
    JOIN market_events me ON c.character_id = me.character_id
    WHERE me.chapter_id = ${chapterNumber}
    ORDER BY current_stock DESC
  `);
  return result as Character[];
}
