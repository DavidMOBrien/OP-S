import Link from 'next/link';
import { getTopCharacters, getAllChapters } from '@/lib/database';

export const dynamic = 'force-dynamic';

export default async function Home() {
  const topCharacters = await getTopCharacters(10);
  const chapters = await getAllChapters();
  const latestChapter = chapters[chapters.length - 1];

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <section className="text-center py-12">
        <h1 className="font-heading text-6xl font-bold mb-4 bg-gradient-to-br from-accent-primary to-text-secondary bg-clip-text text-transparent">
          One Piece Stock Tracker
        </h1>
        <p className="text-xl text-text-secondary max-w-2xl mx-auto">
          Analyzing character performance through narrative. Track stock values, witness epic rises and devastating falls.
        </p>
        <div className="mt-8 flex gap-4 justify-center">
          <Link href="/characters" className="btn-primary">
            Browse Characters
          </Link>
          <Link href="/chapters" className="btn-secondary">
            View Chapters
          </Link>
        </div>
      </section>

      {/* Stats */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card text-center">
          <div className="text-4xl font-mono font-bold text-accent-primary mb-2">
            {topCharacters.length}
          </div>
          <div className="text-sm text-text-secondary">Characters Tracked</div>
        </div>
        <div className="card text-center">
          <div className="text-4xl font-mono font-bold text-accent-primary mb-2">
            {chapters.length}
          </div>
          <div className="text-sm text-text-secondary">Chapters Analyzed</div>
        </div>
        <div className="card text-center">
          <div className="text-4xl font-mono font-bold text-accent-primary mb-2">
            Ch {latestChapter?.chapter_id || 0}
          </div>
          <div className="text-sm text-text-secondary">Latest Chapter</div>
        </div>
      </section>

      {/* Top Characters */}
      <section>
        <div className="flex items-baseline justify-between mb-6">
          <h2 className="font-heading text-3xl font-bold text-accent-primary">
            Top Performers
          </h2>
          <Link href="/characters" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
            View All →
          </Link>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {topCharacters.map((character, index) => (
            <Link
              key={character.character_id}
              href={`/character/${encodeURIComponent(character.character_id)}`}
              className="card group"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="font-mono text-2xl font-bold text-text-tertiary">
                      #{index + 1}
                    </span>
                    <h3 className="font-heading text-xl font-semibold text-accent-primary group-hover:drop-shadow-[0_0_10px_rgba(255,255,255,0.3)] transition-all">
                      {character.canonical_name}
                    </h3>
                  </div>
                  <div className="text-sm text-text-secondary">
                    First appeared: Chapter {character.first_appearance_chapter}
                  </div>
                </div>
                
                <div className="text-right">
                  <div className="font-mono text-3xl font-bold text-accent-primary">
                    {(character.current_stock || character.initial_stock_value).toFixed(1)}
                  </div>
                  <div className="text-xs text-text-tertiary mt-1">
                    from {character.initial_stock_value.toFixed(1)}
                  </div>
                  <div className={`text-sm font-mono font-medium mt-1 ${
                    (character.current_stock || character.initial_stock_value) >= character.initial_stock_value
                      ? 'text-accent-positive'
                      : 'text-accent-negative'
                  }`}>
                    {(character.current_stock || character.initial_stock_value) >= character.initial_stock_value ? '↑' : '↓'} 
                    {Math.abs((((character.current_stock || character.initial_stock_value) - character.initial_stock_value) / character.initial_stock_value) * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Recent Chapters */}
      <section>
        <div className="flex items-baseline justify-between mb-6">
          <h2 className="font-heading text-3xl font-bold text-accent-primary">
            Recent Chapters
          </h2>
          <Link href="/chapters" className="text-sm text-text-secondary hover:text-text-primary transition-colors">
            View All →
          </Link>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {chapters.slice(-6).reverse().map((chapter) => (
            <Link
              key={chapter.chapter_id}
              href={`/chapter/${chapter.chapter_id}`}
              className="card group"
            >
              <div className="flex items-center gap-3 mb-2">
                <span className="font-mono text-lg font-bold text-accent-primary">
                  Ch {chapter.chapter_id}
                </span>
              </div>
              <h3 className="text-base font-medium text-text-primary group-hover:text-accent-primary transition-colors">
                {chapter.title}
              </h3>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}

