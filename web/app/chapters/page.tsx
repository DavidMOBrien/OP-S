import Link from 'next/link';
import { getAllChapters, getCharactersInChapter } from '@/lib/database';

export const dynamic = 'force-dynamic';

export default async function ChaptersPage() {
  const chapters = await getAllChapters();
  
  // Fetch character counts for all chapters
  const chaptersWithCounts = await Promise.all(
    chapters.map(async (chapter) => {
      const charactersInChapter = await getCharactersInChapter(chapter.chapter_id);
      return {
        ...chapter,
        characterCount: charactersInChapter.length
      };
    })
  );
  
  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-heading text-5xl font-bold text-accent-primary mb-4">
          All Chapters
        </h1>
        <p className="text-xl text-text-secondary">
          {chapters.length} chapters analyzed
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {chaptersWithCounts.map((chapter) => (
          <Link
            key={chapter.chapter_id}
            href={`/chapter/${chapter.chapter_id}`}
            className="card group"
          >
            <div className="flex items-center gap-3 mb-3">
              <span className="font-mono text-xl font-bold text-accent-primary">
                Ch {chapter.chapter_id}
              </span>
            </div>
            
            <h3 className="text-base font-medium text-text-primary group-hover:text-accent-primary transition-colors mb-3">
              {chapter.title}
            </h3>
            
              <div className="flex items-center justify-between pt-3 border-t border-surface-border text-xs text-text-tertiary">
                <span>{chapter.characterCount} characters</span>
                {chapter.processed_timestamp && (
                  <span>
                    {new Date(chapter.processed_timestamp).toLocaleDateString()}
                  </span>
                )}
              </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
