import { NextResponse } from 'next/server';
import { getAllCharacters } from '@/lib/database';

export async function GET() {
  try {
    const characters = getAllCharacters();
    return NextResponse.json(characters);
  } catch (error) {
    console.error('Error fetching characters:', error);
    return NextResponse.json({ error: 'Failed to fetch characters' }, { status: 500 });
  }
}

