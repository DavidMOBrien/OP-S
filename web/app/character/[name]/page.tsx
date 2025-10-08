import { notFound } from 'next/navigation';
import Link from 'next/link';
import { getCharacter, getCharacterHistory } from '@/lib/database';
import CharacterChart from '@/components/charts/CharacterChart';

export const dynamic = 'force-dynamic';

export default async function CharacterPage({ params }: { params: { name: string } }) {
  const characterId = decodeURIComponent(params.name);
  const character = await getCharacter(characterId);
  
  if (!character) {
    notFound();
  }
  
  const history = await getCharacterHistory(characterId);
  
  // Transform history for chart
  const chartData = history.map(h => ({
    chapter: h.chapter_id,
    value: h.cumulative_stock_value,
    change: h.chapter_change,
    description: h.chapter_description || 'No detailed actions recorded for this chapter',
  }));
  
  // Calculate stats
  const currentStock = character.current_stock || character.initial_stock_value;
  const totalChange = currentStock - character.initial_stock_value;
  const percentChange = (totalChange / character.initial_stock_value) * 100;
  const highestStock = history.length > 0 ? Math.max(...history.map(h => h.cumulative_stock_value)) : currentStock;
  const lowestStock = history.length > 0 ? Math.min(...history.map(h => h.cumulative_stock_value)) : character.initial_stock_value;
  
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <Link
            href="/characters"
            className="text-sm text-text-secondary hover:text-text-primary transition-colors mb-3 inline-block"
          >
            ← Back to Characters
          </Link>
          <h1 className="font-heading text-5xl font-bold text-accent-primary mb-2">
            {character.canonical_name}
          </h1>
          <p className="text-text-secondary">
            First appeared in Chapter {character.first_appearance_chapter} • {history.length} chapters
          </p>
        </div>
        
        <div className="text-right">
          <div className="text-sm text-text-tertiary mb-1">Current Stock</div>
          <div className="font-mono text-5xl font-bold text-accent-primary mb-2">
            {currentStock.toFixed(1)}
          </div>
          <div className={`font-mono text-lg font-semibold ${
            totalChange >= 0 ? 'text-accent-positive' : 'text-accent-negative'
          }`}>
            {totalChange >= 0 ? '↑' : '↓'} {Math.abs(totalChange).toFixed(1)} ({totalChange >= 0 ? '+' : ''}{percentChange.toFixed(1)}%)
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="text-xs text-text-tertiary uppercase tracking-wider mb-2">Initial Stock</div>
          <div className="font-mono text-2xl font-semibold text-text-primary">
            {character.initial_stock_value.toFixed(1)}
          </div>
        </div>
        <div className="card">
          <div className="text-xs text-text-tertiary uppercase tracking-wider mb-2">Highest</div>
          <div className="font-mono text-2xl font-semibold text-accent-positive">
            {highestStock.toFixed(1)}
          </div>
        </div>
        <div className="card">
          <div className="text-xs text-text-tertiary uppercase tracking-wider mb-2">Lowest</div>
          <div className="font-mono text-2xl font-semibold text-accent-negative">
            {lowestStock.toFixed(1)}
          </div>
        </div>
        <div className="card">
          <div className="text-xs text-text-tertiary uppercase tracking-wider mb-2">Appearances</div>
          <div className="font-mono text-2xl font-semibold text-text-primary">
            {history.length}
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="card">
        <div className="mb-6 pb-6 border-b border-surface-border">
          <h2 className="font-heading text-2xl font-semibold text-accent-primary mb-2">
            Stock History
          </h2>
          <p className="text-sm text-text-secondary">
            Click on any point to view detailed chapter analysis
          </p>
        </div>
        
        <CharacterChart data={chartData} characterName={character.character_id} />
        
        <div className="mt-6 flex items-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-accent-positive"></div>
            <span className="text-text-secondary">Stock Gain</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-accent-negative"></div>
            <span className="text-text-secondary">Stock Loss</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-accent-primary"></div>
            <span className="text-text-secondary">Hover for Details</span>
          </div>
        </div>
      </div>

      {/* Chapter List */}
      <div className="card">
        <h2 className="font-heading text-2xl font-semibold text-accent-primary mb-6">
          Chapter Appearances
        </h2>
        
        <div className="space-y-2 max-h-[600px] overflow-y-auto">
          {history.map((h) => {
            const change = h.chapter_change;
            const changePercent = (h.cumulative_stock_value - h.chapter_change) > 0 
              ? (change / (h.cumulative_stock_value - h.chapter_change)) * 100 
              : 0;
            
            return (
              <Link
                key={h.chapter_id}
                href={`/chapter/${h.chapter_id}?character=${encodeURIComponent(character.character_id)}`}
                className="block p-4 rounded-lg bg-surface-light hover:bg-surface transition-colors border border-transparent hover:border-white/10"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-4">
                    <span className="font-mono text-sm font-semibold text-text-tertiary">
                      Ch {h.chapter_id}
                    </span>
                    <span className="font-mono text-lg font-semibold text-text-primary">
                      {h.cumulative_stock_value.toFixed(1)}
                    </span>
                  </div>
                  
                  <div className={`font-mono text-sm font-medium ${
                    change >= 0 ? 'text-accent-positive' : 'text-accent-negative'
                  }`}>
                    {change >= 0 ? '↑' : '↓'} {Math.abs(change).toFixed(1)} ({change >= 0 ? '+' : ''}{changePercent.toFixed(1)}%)
                  </div>
                </div>
                
                {h.chapter_description && (
                  <p className="text-sm text-text-secondary leading-relaxed line-clamp-2">
                    {h.chapter_description}
                  </p>
                )}
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}

