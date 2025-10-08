import type { Metadata } from 'next';
import Link from 'next/link';
import './globals.css';

export const metadata: Metadata = {
  title: 'One Piece Stock Tracker',
  description: 'Track character stock values throughout One Piece',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <nav className="border-b border-surface-border bg-surface/50 backdrop-blur-sm sticky top-0 z-40">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <Link href="/" className="flex items-center gap-3 group">
                <h1 className="font-heading text-2xl font-bold text-accent-primary transition-all group-hover:drop-shadow-[0_0_20px_rgba(255,255,255,0.3)]">
                  One Piece Stock Tracker
                </h1>
              </Link>
              
              <div className="flex gap-4">
                <Link
                  href="/characters"
                  className="text-sm font-medium text-text-secondary hover:text-text-primary transition-colors"
                >
                  Characters
                </Link>
                <Link
                  href="/chapters"
                  className="text-sm font-medium text-text-secondary hover:text-text-primary transition-colors"
                >
                  Chapters
                </Link>
              </div>
            </div>
          </div>
        </nav>
        
        <main className="max-w-7xl mx-auto px-6 py-8">
          {children}
        </main>
        
        <footer className="border-t border-surface-border mt-20">
          <div className="max-w-7xl mx-auto px-6 py-8">
            <p className="text-sm text-text-tertiary text-center">
              One Piece Stock Tracker • Analyzing character performance through narrative
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}

