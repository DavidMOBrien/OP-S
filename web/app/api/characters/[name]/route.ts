import { NextResponse } from 'next/server';
import { getCharacter, getCharacterHistory } from '@/lib/database';

export async function GET(
  request: Request,
  { params }: { params: { name: string } }
) {
  try {
    const characterName = decodeURIComponent(params.name);
    const character = getCharacter(characterName);
    
    if (!character) {
      return NextResponse.json({ error: 'Character not found' }, { status: 404 });
    }
    
    const history = getCharacterHistory(characterName);
    
    return NextResponse.json({ character, history });
  } catch (error) {
    console.error('Error fetching character:', error);
    return NextResponse.json({ error: 'Failed to fetch character' }, { status: 500 });
  }
}

