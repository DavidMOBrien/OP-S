import { NextResponse } from 'next/server';
import { getCharacterChapterEvents } from '@/lib/database';

export async function GET(
  request: Request,
  { params }: { params: { number: string; name: string } }
) {
  try {
    const chapterNumber = parseInt(params.number);
    const characterName = decodeURIComponent(params.name);
    const events = getCharacterChapterEvents(characterName, chapterNumber);
    
    return NextResponse.json({ events });
  } catch (error) {
    console.error('Error fetching character chapter events:', error);
    return NextResponse.json({ error: 'Failed to fetch events' }, { status: 500 });
  }
}

