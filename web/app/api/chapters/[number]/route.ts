import { NextResponse } from 'next/server';
import { getChapter, getChapterEvents, getCharactersInChapter } from '@/lib/database';

export async function GET(
  request: Request,
  { params }: { params: { number: string } }
) {
  try {
    const chapterNumber = parseInt(params.number);
    const chapter = getChapter(chapterNumber);
    
    if (!chapter) {
      return NextResponse.json({ error: 'Chapter not found' }, { status: 404 });
    }
    
    const events = getChapterEvents(chapterNumber);
    const characters = getCharactersInChapter(chapterNumber);
    
    return NextResponse.json({ chapter, events, characters });
  } catch (error) {
    console.error('Error fetching chapter:', error);
    return NextResponse.json({ error: 'Failed to fetch chapter' }, { status: 500 });
  }
}

