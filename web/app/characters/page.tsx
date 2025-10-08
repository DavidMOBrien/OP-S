import Link from 'next/link';
import { getAllCharacters } from '@/lib/database';

export const dynamic = 'force-dynamic';

export default async function CharactersPage() {
  const characters = await getAllCharacters();
  
  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-heading text-5xl font-bold text-accent-primary mb-4">
          All Characters
        </h1>
        <p className="text-xl text-text-secondary">
          {characters.length} characters tracked across the series
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {characters.map((character, index) => {
          const currentStock = character.current_stock || character.initial_stock_value;
          const totalChange = currentStock - character.initial_stock_value;
          const percentChange = (totalChange / character.initial_stock_value) * 100;
          
          return (
            <Link
              key={character.character_id}
              href={`/character/${encodeURIComponent(character.character_id)}`}
              className="card group"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-mono text-sm font-bold text-text-tertiary">
                      #{index + 1}
                    </span>
                  </div>
                  <h3 className="font-heading text-xl font-semibold text-accent-primary group-hover:drop-shadow-[0_0_10px_rgba(255,255,255,0.3)] transition-all">
                    {character.canonical_name}
                  </h3>
                  <div className="text-xs text-text-tertiary mt-1">
                    First appeared: Ch {character.first_appearance_chapter}
                  </div>
                </div>
                
                <div className="text-right">
                  <div className="font-mono text-2xl font-bold text-accent-primary">
                    {currentStock.toFixed(1)}
                  </div>
                </div>
              </div>
              
              <div className="flex items-center justify-between pt-3 border-t border-surface-border">
                <div className="text-xs text-text-tertiary">
                  Initial: {character.initial_stock_value.toFixed(1)}
                </div>
                <div className={`font-mono text-sm font-semibold ${
                  totalChange >= 0 ? 'text-accent-positive' : 'text-accent-negative'
                }`}>
                  {totalChange >= 0 ? '↑' : '↓'} {Math.abs(percentChange).toFixed(1)}%
                </div>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}

