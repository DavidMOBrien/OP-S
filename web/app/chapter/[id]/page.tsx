import { notFound } from 'next/navigation';
import Link from 'next/link';
import { getChapter, getChapterEvents, getCharactersInChapter, getCharacterChapterEvents, getCharacterChapterReasoning } from '@/lib/database';
import ChapterChart from '@/components/charts/ChapterChart';

export const dynamic = 'force-dynamic';

export default async function ChapterPage({ 
  params,
  searchParams,
}: { 
  params: { id: string };
  searchParams: { character?: string };
}) {
  const chapterNumber = parseInt(params.id);
  const chapter = await getChapter(chapterNumber);
  
  if (!chapter) {
    notFound();
  }
  
  const characters = await getCharactersInChapter(chapterNumber);
  const selectedCharacter = searchParams.character ? decodeURIComponent(searchParams.character) : characters[0]?.character_id;
  
  // Get events for selected character
  const events = selectedCharacter 
    ? await getCharacterChapterEvents(selectedCharacter, chapterNumber)
    : [];
  
  // Get chapter-level reasoning for selected character
  const chapterReasoning = selectedCharacter
    ? await getCharacterChapterReasoning(selectedCharacter, chapterNumber)
    : null;
  
  const character = characters.find(c => c.character_id === selectedCharacter);
  
  // Calculate total change from events
  const totalChange = events.length > 0 
    ? events.reduce((sum, e) => sum + e.stock_change, 0)
    : 0;
  const startingStock = character?.current_stock ? character.current_stock - totalChange : 0;
  const percentChange = startingStock > 0 ? (totalChange / startingStock) * 100 : 0;
  
  // Transform events for chart - calculate cumulative stock values
  let cumulativeStock = startingStock;
  const chartData = [
    // Add starting point
    {
      action: 0,
      value: startingStock,
      mult: 1.0,
      desc: `Starting stock for this chapter`,
    },
    // Then add all events
    ...events.map((event, index) => {
      const prevStock = cumulativeStock;
      cumulativeStock += event.stock_change;
      const mult = prevStock > 0 ? (cumulativeStock / prevStock) : 1;
      return {
        action: index + 1,
        value: cumulativeStock,
        mult: mult,
        desc: event.description,
      };
    })
  ];
  
  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <Link
          href="/chapters"
          className="text-sm text-text-secondary hover:text-text-primary transition-colors mb-3 inline-block"
        >
          ← Back to Chapters
        </Link>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h1 className="font-heading text-5xl font-bold text-accent-primary">
                Chapter {chapter.chapter_id}
              </h1>
              {chapter.arc_name && (
                <span className="text-sm text-text-tertiary px-3 py-1 rounded-full bg-surface-light border border-surface-border">
                  {chapter.arc_name}
                </span>
              )}
            </div>
            <p className="text-xl text-text-secondary">
              {chapter.title}
            </p>
          </div>
          
          {character && events.length > 0 && (
            <div className="text-right">
              <div className="text-sm text-text-tertiary mb-1">Stock Change</div>
              <div className={`font-mono text-4xl font-bold ${
                totalChange >= 0 ? 'text-accent-positive' : 'text-accent-negative'
              }`}>
                {totalChange >= 0 ? '↑' : '↓'} {Math.abs(totalChange).toFixed(1)}
              </div>
              <div className={`font-mono text-lg font-medium ${
                totalChange >= 0 ? 'text-accent-positive' : 'text-accent-negative'
              }`}>
                ({totalChange >= 0 ? '+' : ''}{percentChange.toFixed(1)}%)
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Character Selector */}
      <div className="card">
        <h2 className="font-heading text-xl font-semibold text-accent-primary mb-4">
          Characters in this Chapter
        </h2>
        <div className="flex flex-wrap gap-2">
          {characters.map((char) => (
            <Link
              key={char.character_id}
              href={`/chapter/${chapterNumber}?character=${encodeURIComponent(char.character_id)}`}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                char.character_id === selectedCharacter
                  ? 'bg-accent-primary text-background'
                  : 'bg-surface-light text-text-primary hover:bg-surface border border-surface-border hover:border-white/20'
              }`}
            >
              {char.canonical_name}
            </Link>
          ))}
        </div>
      </div>

      {selectedCharacter && events.length > 0 && (
        <>
          {/* Character Stock Overview */}
          <div className="card">
            <div className="flex items-start justify-between mb-6 pb-6 border-b border-surface-border">
              <div>
                <h2 className="font-heading text-3xl font-bold text-accent-primary mb-2">
                  {character?.canonical_name || selectedCharacter}
                </h2>
                <p className="text-text-secondary">
                  {events.length} {events.length === 1 ? 'action' : 'actions'} in this chapter
                </p>
              </div>
              
              <div className="text-right">
                <div className="font-mono text-4xl font-bold text-accent-primary">
                  {character?.current_stock?.toFixed(1) || '0.0'}
                </div>
                <div className="text-sm text-text-tertiary mt-1">
                  {totalChange >= 0 ? '+' : ''}{totalChange.toFixed(1)} change
                </div>
              </div>
            </div>
            
            {chartData.length > 0 && <ChapterChart data={chartData} />}
            
            <div className="mt-6 flex items-center gap-6 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-accent-positive"></div>
                <span className="text-text-secondary">Stock Gain</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-accent-negative"></div>
                <span className="text-text-secondary">Stock Loss</span>
              </div>
            </div>
          </div>

          {/* Chapter-Level Reasoning */}
          {chapterReasoning && (
            <div className="card">
              <h2 className="font-heading text-xl font-semibold text-accent-primary mb-4">
                Chapter Analysis
              </h2>
              <p className="text-sm text-text-secondary leading-relaxed">
                {chapterReasoning}
              </p>
            </div>
          )}

          {/* Action List */}
          <div className="card">
            <h2 className="font-heading text-2xl font-semibold text-accent-primary mb-6">
              Detailed Actions
            </h2>
            
            <div className="space-y-3">
              {events.map((event, eventIndex) => {
                // chartData has a starting point at index 0, so actual actions start at index 1
                const chartIndex = eventIndex + 1;
                const dataPoint = chartData[chartIndex];
                if (!dataPoint) return null;
                
                const prevValue = chartData[chartIndex - 1].value;
                const changePercent = prevValue > 0 ? (event.stock_change / prevValue) * 100 : 0;
                
                return (
                  <div
                    key={event.event_id}
                    className="p-4 rounded-lg bg-surface-light border border-surface-border hover:border-white/10 transition-all"
                  >
                    <div className="flex items-start gap-4">
                      <div className="flex-shrink-0">
                        <span className="font-mono text-sm font-semibold text-text-tertiary">
                          Action {eventIndex + 1}
                        </span>
                      </div>
                      
                      <div className="flex-1">
                        <p className="text-text-primary leading-relaxed mb-3">
                          {event.description}
                        </p>
                        
                        <div className="flex items-center justify-between text-sm">
                          <div className="flex items-center gap-4 text-text-secondary">
                            <span>
                              {prevValue.toFixed(1)} → <span className="font-mono text-text-primary font-medium">{dataPoint.value.toFixed(1)}</span>
                            </span>
                            <span>
                              <span className={`font-mono font-medium ${
                                event.stock_change >= 0 ? 'text-accent-positive' : 'text-accent-negative'
                              }`}>
                                {event.stock_change >= 0 ? '+' : ''}{event.stock_change.toFixed(1)}
                              </span>
                            </span>
                            <span>
                              Confidence: <span className="font-mono text-text-primary font-medium">{event.confidence_score.toFixed(2)}</span>
                            </span>
                          </div>
                          
                          <div className={`font-mono text-base font-semibold ${
                            event.stock_change >= 0 ? 'text-accent-positive' : 'text-accent-negative'
                          }`}>
                            {event.stock_change >= 0 ? '↑' : '↓'} {Math.abs(changePercent).toFixed(1)}%
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}

      {selectedCharacter && events.length === 0 && (
        <div className="card text-center py-12">
          <p className="text-text-secondary">
            No detailed actions found for this character in this chapter.
          </p>
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-between items-center">
        {chapterNumber > 1 ? (
          <Link
            href={`/chapter/${chapterNumber - 1}`}
            className="btn-secondary"
          >
            ← Previous Chapter
          </Link>
        ) : (
          <div></div>
        )}
        
        <Link
          href={`/chapter/${chapterNumber + 1}`}
          className="btn-secondary"
        >
          Next Chapter →
        </Link>
      </div>
    </div>
  );
}

