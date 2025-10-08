# One Piece Stock Tracker - Web Interface

A sophisticated web interface for exploring character stock values throughout the One Piece manga series.

## Features

- **Home Dashboard**: Overview of top performers and recent chapters
- **Character View**: Historical stock progression with interactive charts
- **Chapter View**: Detailed action-by-action breakdown within chapters
- **Interactive Charts**: Hover over points to see descriptions and stock changes
- **Modern Design**: Sophisticated dark theme with stylized grays and white accents

## Getting Started

### Prerequisites

- Node.js 18+ installed
- The main One Piece Stock Tracker database (`one_piece_stocks.db`) in the parent directory

### Installation

```bash
# Install dependencies
npm install
```

### Development

```bash
# Run the development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Production

```bash
# Build for production
npm run build

# Start production server
npm start
```

## Project Structure

```
web/
├── app/                      # Next.js App Router
│   ├── api/                  # API routes
│   │   ├── characters/       # Character endpoints
│   │   └── chapters/         # Chapter endpoints
│   ├── character/[name]/     # Character detail pages
│   ├── chapter/[id]/         # Chapter detail pages
│   ├── characters/           # Characters list page
│   ├── chapters/             # Chapters list page
│   ├── layout.tsx            # Root layout with navigation
│   ├── page.tsx              # Home page
│   └── globals.css           # Global styles
├── components/
│   └── charts/               # Chart components
│       ├── ChapterChart.tsx  # Individual actions chart
│       └── CharacterChart.tsx # Historical progression chart
├── lib/
│   └── database.ts           # SQLite database utilities
└── public/                   # Static assets
```

## Design System

### Colors

- **Background**: #0F0F0F (sophisticated dark gray-black)
- **Surface**: #1A1A1A (elevated cards/panels)
- **Accent**: #FFFFFF (white highlights and titles)
- **Positive**: #10B981 (stock gains)
- **Negative**: #EF4444 (stock losses)

### Typography

- **Headings**: Space Grotesk
- **Body**: System fonts
- **Monospace**: JetBrains Mono (stock values)

## Technologies

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Database**: Better-SQLite3
- **Charts**: Custom SVG-based interactive charts

## API Routes

- `GET /api/characters` - Get all characters
- `GET /api/characters/[name]` - Get character details and history
- `GET /api/chapters` - Get all chapters
- `GET /api/chapters/[number]` - Get chapter details and events
- `GET /api/chapters/[number]/character/[name]` - Get character events in a chapter

## License

Same as parent project

