# One Piece Stock Tracker - Web Interface Design

## Design Philosophy
**Modernistic Simplicity with Stylized Detail**
- Clean, minimal layouts with intentional whitespace
- Subtle animations and micro-interactions
- Rich color gradients and depth through shadows
- Typography hierarchy that guides the eye
- Inspired by: Linear, Vercel, Arc Browser aesthetics

---

## Color Palette

### Primary Colors
```
Background:     #0F0F0F (Sophisticated dark gray-black)
Surface:        #1A1A1A (Elevated cards/panels)
Surface Light:  #252525 (Hover states)
Surface Border: #2A2A2A (Subtle borders)

Accent Primary: #FFFFFF (Pure white - highlights, titles, key elements)
Accent Bright:  #F5F5F5 (Off-white for secondary highlights)
Accent Positive:#10B981 (Green - stock gains)
Accent Negative:#EF4444 (Red - stock losses)
Accent Neutral: #71717A (Gray - unchanged)

Text Primary:   #F5F5F5 (Soft off-white)
Text Secondary: #A3A3A3 (Neutral 400)
Text Tertiary:  #737373 (Neutral 500)
```

### Gradients
```css
/* Hero gradient */
background: linear-gradient(135deg, #0F0F0F 0%, #1A1A1A 100%);

/* Card glow on hover */
box-shadow: 0 0 40px rgba(255, 255, 255, 0.05);

/* White accent glow */
box-shadow: 0 0 60px rgba(255, 255, 255, 0.08);

/* Stock gain glow */
text-shadow: 0 0 20px rgba(16, 185, 129, 0.4);

/* Stock loss glow */
text-shadow: 0 0 20px rgba(239, 68, 68, 0.4);
```

---

## Typography

### Font Stack
```css
/* Primary - Body Text */
font-family: 'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;

/* Display - Headings & Titles */
font-family: 'Space Grotesk', 'Geist', sans-serif;

/* Monospace (for stock values) */
font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', monospace;
```

**Font Sources:**
```html
<!-- Geist from Vercel -->
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700&display=swap" rel="stylesheet">

<!-- Space Grotesk from Google Fonts -->
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">

<!-- JetBrains Mono -->
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
```

### Hierarchy
```
H1 (Page Title):    48px, weight 700, tracking -0.02em
H2 (Section):       32px, weight 600, tracking -0.01em
H3 (Card Title):    24px, weight 600
Body Large:         18px, weight 400, line-height 1.6
Body:               16px, weight 400, line-height 1.5
Body Small:         14px, weight 400, line-height 1.4
Caption:            12px, weight 500, uppercase, tracking 0.05em
```

---

## Page Layouts

### 1. HOME / DASHBOARD
```
┌─────────────────────────────────────────────────────────────┐
│  SIDEBAR    │  MAIN CONTENT AREA                            │
│             │                                                │
│  One Piece  │  ┌──────────────────────────────────────┐    │
│  Stock      │  │  Current Market Overview              │    │
│  Tracker    │  │  ┌────────┐  ┌────────┐  ┌────────┐ │    │
│             │  │  │ Total  │  │ Active │  │  Avg   │ │    │
│  ◉ Market   │  │  │ Chars  │  │ Chaps  │  │ Stock  │ │    │
│  ○ Chapters │  │  │  117   │  │  217   │  │  65.2  │ │    │
│  ○ Chars    │  │  └────────┘  └────────┘  └────────┘ │    │
│             │  └──────────────────────────────────────┘    │
│  [Search]   │                                                │
│             │  Top 10 Characters                             │
│             │  ┌──────────────────────────────────────┐    │
│             │  │ 1. Roronoa Zoro    [▓▓▓▓▓▓▓] 652.3  │    │
│             │  │ 2. Tony Tony Chopp [▓▓▓▓▓▓▓] 628.2  │    │
│             │  │ 3. Miss Wednesday   [▓▓▓▓▓▓░] 480.8  │    │
│             │  │ ...                                   │    │
│             │  └──────────────────────────────────────┘    │
│             │                                                │
│             │  Recent Chapter Activity                       │
│             │  [Cards showing recent chapters...]            │
└─────────────────────────────────────────────────────────────┘
```

---

### 2. CHAPTER VIEW
**URL:** `/chapter/92`

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Back to Chapters                                              │
│                                                                   │
│  Chapter 92: "Luffy vs. Arlong"                                  │
│  Arc: Arlong Park Arc                                            │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Chapter Summary Stats                                   │   │
│  │  9 Characters Active  •  8 Gains  •  1 Loss             │   │
│  │  Biggest Gainer: Luffy (+116.4)  •  Biggest Loser: -    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│                                                                   │
│  CHARACTER STOCK PROGRESSIONS                                    │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Monkey D. Luffy                    115.4 → 231.8 (+116.4)│  │
│  │                                                           │   │
│  │  240┤                                                 ●   │   │
│  │  220┤                                             ●       │   │
│  │  200┤                                         ●           │   │
│  │  180┤                                     ●               │   │
│  │  160┤                                 ●                   │   │
│  │  140┤                             ●                       │   │
│  │  120┤  ●─────●─────●─────●───●                           │   │
│  │  100┤                                                     │   │
│  │     └──────────────────────────────────────────────────  │   │
│  │      1    2    3    4    5    6    7    8    9    10     │   │
│  │                                                           │   │
│  │  [Hover over any point to see action details]           │   │
│  │                                                           │   │
│  │  Actions (10):                                           │   │
│  │  1. [●] Challenges Arlong... → 1.03x                     │   │
│  │  2. [●] Uses finger shield... → 1.08x                    │   │
│  │  3. [●] Blocks Arlong's attack... → 1.05x                │   │
│  │  ...                                                      │   │
│  │  [Click to expand full reasoning]                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Arlong                             2291.1 → 2955.6 (+664.5)│ │
│  │  [Similar chart with 11 action points...]                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  [More character cards...]                                       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

**Key Design Elements:**
- Each character gets an **elevated card** with subtle shadow
- **Inline line chart** showing stock progression through actions
- Chart points are **clickable** to highlight corresponding action
- **Hover states** on chart points show exact values
- **Expandable section** for full LLM reasoning
- **Color coding**: Green for gains, red for losses on the summary line
- **Smooth animations** when expanding/collapsing actions

---

### 3. CHARACTER VIEW
**URL:** `/character/Monkey_D._Luffy`

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Back to Characters                                            │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  [Avatar/Icon]  Monkey D. Luffy                          │  │
│  │                                                            │  │
│  │  Current Stock: 165.3    First Appearance: Chapter 1     │  │
│  │  Market Rank: #9         Initial Value: 100.0            │  │
│  │                                                            │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐               │  │
│  │  │ Chapters │  │  Total   │  │  Best    │               │  │
│  │  │  Active  │  │  Change  │  │ Chapter  │               │  │
│  │  │   217    │  │  +65.3   │  │  Ch 93   │               │  │
│  │  └──────────┘  └──────────┘  └──────────┘               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│                                                                   │
│  STOCK HISTORY                                                   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  300┤                                                     │   │
│  │     │                                    ╱●               │   │
│  │  250┤                               ╱───╯                 │   │
│  │     │                          ╱───╯                      │   │
│  │  200┤                     ╱───╯                           │   │
│  │     │                ╱───╯         ●                      │   │
│  │  150┤           ╱───╯         ╱───╯                       │   │
│  │     │      ╱───╯        ╱────╯                            │   │
│  │  100┤  ●──╯       ╱────╯                                  │   │
│  │     │        ╱────╯                                       │   │
│  │   50┤   ╱───╯                                             │   │
│  │     │                                                     │   │
│  │     └──────────────────────────────────────────────────  │   │
│  │      0    25   50   75   100  125  150  175  200  217    │   │
│  │                    Chapter Number                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  [Hover over any point to see chapter summary & reasoning]      │
│  [Click point → Navigate to chapter view with full details]     │
│                                                                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│
│                                                                   │
│  CHAPTER ACTIVITY TIMELINE                                       │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Chapter 217  •  165.3 → 165.3 (0%)                     │    │
│  │  Final Multiplier: 1.02x  •  Confidence: 0.85           │    │
│  │  "Luffy's actions reflect his role as a leader..."      │    │
│  │  [View Detailed Analysis →]                             │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Chapter 216  •  154.7 → 162.5 (+5.0%)  ↑               │    │
│  │  Final Multiplier: 1.05x  •  Confidence: 0.90           │    │
│  │  "Luffy defeats Crocodile in an epic final battle..."   │    │
│  │  [View Detailed Analysis →]                             │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                   │
│  [More chapter cards in reverse chronological order...]         │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

**Key Design Elements:**
- **Hero section** with character stats and key metrics
- **Large, prominent chart** showing stock over entire history
- **Interactive points** with hover tooltips and click-to-navigate
- **Timeline cards** showing chapter-by-chapter performance
- **Expandable cards** to see full reasoning
- **Visual indicators**: ↑ for gains, ↓ for losses, → for neutral

---

## Component Specifications

### Stock Chart Component
```jsx
<StockChart
  data={chartData}
  height={300}
  showGrid={true}
  interactive={true}
  colorScheme={{
    line: "#A855F7",
    point: "#A855F7",
    pointHover: "#C084FC",
    gain: "#10B981",
    loss: "#EF4444"
  }}
  animations={{
    duration: 800,
    easing: "cubic-bezier(0.4, 0, 0.2, 1)"
  }}
  tooltip={{
    enabled: true,
    delay: 150,
    maxWidth: 400
  }}
/>
```

**Visual Details:**
- Line width: 2px
- Point radius: 4px (6px on hover)
- Grid lines: 1px solid rgba(255, 255, 255, 0.05)
- Gradient under line: subtle fade from color to transparent
- Smooth bezier curves between points
- **Tooltip appears above point with 150ms delay**

**Tooltip Design:**
```css
.chart-tooltip {
  position: absolute;
  background: linear-gradient(135deg, #2A2A2A 0%, #1A1A1A 100%);
  border: 1px solid rgba(168, 85, 247, 0.3);
  border-radius: 12px;
  padding: 16px;
  max-width: 400px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6),
              0 0 60px rgba(168, 85, 247, 0.2);
  pointer-events: none;
  z-index: 1000;
  animation: tooltipFadeIn 200ms ease-out;
}

@keyframes tooltipFadeIn {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Tooltip arrow pointing to the point */
.chart-tooltip::after {
  content: '';
  position: absolute;
  bottom: -6px;
  left: 50%;
  transform: translateX(-50%);
  width: 12px;
  height: 12px;
  background: #2A2A2A;
  border-right: 1px solid rgba(168, 85, 247, 0.3);
  border-bottom: 1px solid rgba(168, 85, 247, 0.3);
  transform: translateX(-50%) rotate(45deg);
}

.tooltip-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.tooltip-action-number {
  font-size: 12px;
  font-weight: 600;
  color: #71717A;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.tooltip-multiplier {
  font-family: 'JetBrains Mono', monospace;
  font-size: 18px;
  font-weight: 600;
}

.tooltip-multiplier.positive {
  color: #10B981;
  text-shadow: 0 0 10px rgba(16, 185, 129, 0.4);
}

.tooltip-multiplier.negative {
  color: #EF4444;
  text-shadow: 0 0 10px rgba(239, 68, 68, 0.4);
}

.tooltip-description {
  font-size: 14px;
  line-height: 1.5;
  color: #D1D5DB;
}

.tooltip-stock-values {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #A1A1AA;
}

.tooltip-stock-values span {
  font-family: 'JetBrains Mono', monospace;
  color: #FAFAFA;
  font-weight: 500;
}
```

### Character Card Component
```jsx
<CharacterCard
  character={characterData}
  variant="elevated" // or "flat"
  showChart={true}
  expandable={true}
/>
```

**Visual Details:**
```css
.character-card {
  background: linear-gradient(135deg, #1A1A1A 0%, #2A2A2A 100%);
  border-radius: 16px;
  border: 1px solid #333333;
  padding: 24px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.character-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4),
              0 0 60px rgba(168, 85, 247, 0.15);
  border-color: rgba(168, 85, 247, 0.3);
}
```

### Stock Value Display
```jsx
<StockValue
  value={165.3}
  change={+2.8}
  variant="large" // or "small"
  showPercentage={true}
/>
```

**Visual Details:**
```css
.stock-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 32px;
  font-weight: 600;
  background: linear-gradient(135deg, #10B981 0%, #34D399 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 0 30px rgba(16, 185, 129, 0.3);
}

.stock-change {
  font-size: 18px;
  font-weight: 500;
  color: #10B981;
}

.stock-change::before {
  content: "↑ ";
  font-size: 20px;
}
```

---

## Micro-Interactions

### 1. Chart Point Hover
```
- Point scales from 4px → 6px
- Crosshair lines appear (1px dashed rgba(255, 255, 255, 0.2))
- Tooltip fades in (150ms) above the point
- Corresponding action highlights in list below (if in Chapter View)
```

**Tooltip Content Examples:**

**Chapter View (Individual Actions):**
```
┌─────────────────────────────────────────┐
│ ACTION 3                     1.08x ↑    │
├─────────────────────────────────────────┤
│ Luffy uses his finger shield to block   │
│ Arlong's attack and bounces away from   │
│ the impact, demonstrating creativity    │
│ and resourcefulness.                     │
├─────────────────────────────────────────┤
│ Before: 115.4  →  After: 124.6          │
└─────────────────────────────────────────┘
```

**Character View (Chapter-Wide):**
```
┌─────────────────────────────────────────┐
│ CHAPTER 92                   2.01x ↑    │
├─────────────────────────────────────────┤
│ Luffy's actions reflect combat          │
│ effectiveness and emotional depth,      │
│ showcasing creativity and determination │
│ against Arlong. Strong performance with │
│ 10 impactful actions.                   │
├─────────────────────────────────────────┤
│ Before: 115.4  →  After: 231.8          │
│ Change: +116.4 (+100.9%)                │
│ Confidence: 0.90                        │
├─────────────────────────────────────────┤
│ Click to view detailed chapter analysis │
└─────────────────────────────────────────┘
```

### 2. Chapter Card Click
```
- Card briefly scales (scale: 0.98)
- Ripple effect from click point
- Page transition: slide left (400ms)
```

### 3. Expand Actions
```
- Smooth height animation (300ms ease-out)
- Actions fade in staggered (50ms delay each)
- Arrow icon rotates 180deg
```

### 4. Loading States
```
- Skeleton screens with shimmer effect
- Charts animate in from left to right
- Smooth fade-in for data (600ms)
```

---

## Responsive Breakpoints

```css
/* Mobile */
@media (max-width: 640px) {
  - Sidebar collapses to hamburger menu
  - Charts switch to smaller height (200px)
  - Cards stack vertically
  - Hide less important stats
}

/* Tablet */
@media (min-width: 641px) and (max-width: 1024px) {
  - Sidebar becomes overlay
  - 2-column grid for chapter cards
  - Maintain chart quality
}

/* Desktop */
@media (min-width: 1025px) {
  - Full sidebar
  - 3-column grid for chapter cards
  - Maximum chart detail
}
```

---

## Navigation Structure

```
/                        → Dashboard (market overview)
/chapters                → All chapters list
/chapter/:id             → Single chapter detail
/characters              → All characters list
/character/:id           → Single character detail
/character/:id/chapter/:chapterId → Character's detailed actions in specific chapter
```

---

## Technology Stack Recommendations

### Framework
```
- Next.js 14+ (App Router)
- React 18+
- TypeScript
```

### Charting
```
- Recharts or Victory (customizable, React-native)
- D3.js for complex interactions
- Framer Motion for animations
```

### Styling
```
- Tailwind CSS (with custom theme)
- CSS Modules for component styles
- clsx for conditional classes
```

### UI Components
```
- Radix UI (headless, accessible)
- Custom components for charts
- React Spring for physics-based animations
```

---

## Animation Principles

1. **Purposeful Motion**: Every animation serves a purpose
2. **Performance**: Use GPU-accelerated properties (transform, opacity)
3. **Consistency**: Same duration/easing for similar actions
4. **Feedback**: Immediate response to user actions
5. **Delight**: Subtle surprises (particles on big gains?)

### Example Timing
```
- Micro: 150-250ms (hover, click)
- Small: 300-400ms (expand, collapse)
- Medium: 500-700ms (page transitions)
- Large: 800-1200ms (data loading, complex animations)
```

---

## Accessibility

- WCAG 2.1 AA compliant
- Keyboard navigation for all interactions
- Focus visible on all interactive elements
- Screen reader friendly labels
- Reduced motion mode for users with vestibular disorders
- High contrast mode support

---

## Special Features to Consider

### 1. Comparison Mode
- Select multiple characters
- Overlay their stock charts
- Side-by-side chapter performance

### 2. Arc View
- Group chapters by story arc
- Aggregate stats per arc
- Arc-level winners/losers

### 3. Search & Filters
- Fuzzy search for characters/chapters
- Filter by stock range, change %, tier
- Sort by various metrics

### 4. Bookmarks/Favorites
- Save favorite characters
- Bookmark interesting chapters
- Export data as CSV/JSON

### 5. Dark/Light Mode Toggle
- Smooth theme transition
- Persistent preference
- System preference detection

---

## Next Steps

1. Set up Next.js project with TypeScript
2. Configure Tailwind with custom theme
3. Build component library (Button, Card, Chart base)
4. Create API routes for data fetching
5. Implement Chapter View first (most complex)
6. Add Character View
7. Build Dashboard
8. Polish animations and micro-interactions
9. Responsive testing
10. Performance optimization

---

*Design inspired by Linear, Vercel, Arc Browser, and modern data visualization best practices.*

