import { NextResponse } from 'next/server';
import { getAllChapters } from '@/lib/database';

export async function GET() {
  try {
    const chapters = getAllChapters();
    return NextResponse.json(chapters);
  } catch (error) {
    console.error('Error fetching chapters:', error);
    return NextResponse.json({ error: 'Failed to fetch chapters' }, { status: 500 });
  }
}

