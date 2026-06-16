# Design System — mimo-farmer Web UI (Neobrutalism)

## Overview

Tema visual mimo-farmer Web UI menggunakan **Neobrutalism** — style yang memadukan brutalism (raw, bold, honest) dengan modern typography dan color palette. Karakteristik utama: thick borders, solid shadows, high contrast colors, unapologetic design.

## Reference

- [Neobrutalism Components](https://www.neobrutalism.dev)
- Neobrutalism = brutalism + modern typography + bold colors + thick outlines

## Color Palette

### Primary Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `--bg` | `#f5f0e8` | Main background (warm cream) |
| `--bg-alt` | `#e8e0d0` | Alternate background |
| `--main` | `#5b8cff` | Primary actions, links, active states |
| `--main-foreground` | `#ffffff` | Text on main color |
| `--secondary` | `#ffb938` | Secondary actions, warnings, highlights |
| `--secondary-foreground` | `#1a1a1a` | Text on secondary color |
| `--border` | `#1a1a1a` | All borders (thick, black) |
| `--text` | `#1a1a1a` | Primary text |
| `--text-muted` | `#6b6b6b` | Secondary text |
| `--destructive` | `#ff4444` | Errors, danger, delete |
| `--success` | `#22c55e` | Success states |
| `--info` | `#5b8cff` | Info states |

### Accent Colors (for cards/categories)

| Token | Hex | Usage |
|-------|-----|-------|
| `--accent-1` | `#ff6b6b` | Card accent 1 |
| `--accent-2` | `#51cf66` | Card accent 2 |
| `--accent-3` | `#ffd43b` | Card accent 3 |
| `--accent-4` | `#cc5de8` | Card accent 4 |

## Typography

### Font Stack

```css
font-family: 'Inter', 'Space Grotesk', system-ui, -apple-system, sans-serif;
```

| Element | Font | Weight | Size | Line Height |
|---------|------|--------|------|-------------|
| H1 | Space Grotesk | 800 | 2.5rem (40px) | 1.1 |
| H2 | Space Grotesk | 700 | 2rem (32px) | 1.2 |
| H3 | Space Grotesk | 700 | 1.5rem (24px) | 1.3 |
| H4 | Inter | 600 | 1.25rem (20px) | 1.4 |
| Body | Inter | 400 | 1rem (16px) | 1.6 |
| Small | Inter | 400 | 0.875rem (14px) | 1.5 |
| Code | JetBrains Mono | 400 | 0.875rem (14px) | 1.6 |

## Borders & Shadows

### Borders

Semua elemen menggunakan border tebal hitam.

```css
--border-width: 3px;
--border-radius: 0px; /* atau 4px untuk sedikit round */
border: var(--border-width) solid var(--border);
```

### Shadows

Shadow solid tanpa blur, offset ke kanan-bawah.

```css
--shadow: 5px 5px 0px var(--border);
--shadow-sm: 3px 3px 0px var(--border);
--shadow-lg: 8px 8px 0px var(--border);
```

### Hover Effect

Shadow membesar saat hover, elemen sedikit bergeser.

```css
.element:hover {
  transform: translate(-2px, -2px);
  box-shadow: 7px 7px 0px var(--border);
}
```

### Active/Press Effect

Shadow hilang, elemen bergeser ke posisi shadow.

```css
.element:active {
  transform: translate(3px, 3px);
  box-shadow: none;
}
```

## Components

### Buttons

```css
/* Primary Button */
.btn-primary {
  background-color: var(--main);
  color: var(--main-foreground);
  border: 3px solid var(--border);
  box-shadow: var(--shadow);
  padding: 12px 24px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.1s ease;
}

.btn-primary:hover {
  transform: translate(-2px, -2px);
  box-shadow: 7px 7px 0px var(--border);
}

.btn-primary:active {
  transform: translate(3px, 3px);
  box-shadow: none;
}

/* Secondary Button */
.btn-secondary {
  background-color: var(--secondary);
  color: var(--secondary-foreground);
  /* same border/shadow pattern */
}

/* Destructive Button */
.btn-destructive {
  background-color: var(--destructive);
  color: white;
  /* same border/shadow pattern */
}
```

### Cards

```css
.card {
  background-color: white;
  border: 3px solid var(--border);
  box-shadow: var(--shadow);
  padding: 24px;
}

.card-header {
  border-bottom: 3px solid var(--border);
  padding-bottom: 16px;
  margin-bottom: 16px;
}
```

### Input Fields

```css
.input {
  background-color: white;
  border: 3px solid var(--border);
  box-shadow: var(--shadow-sm);
  padding: 10px 14px;
  font-size: 1rem;
  width: 100%;
}

.input:focus {
  outline: none;
  border-color: var(--main);
  box-shadow: 4px 4px 0px var(--main);
}
```

### Tables

```css
.table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  border: 3px solid var(--border);
}

.table th {
  background-color: var(--main);
  color: white;
  padding: 12px 16px;
  text-align: left;
  font-weight: 600;
  border-bottom: 3px solid var(--border);
}

.table td {
  padding: 10px 16px;
  border-bottom: 2px solid var(--border);
}

.table tr:hover td {
  background-color: #f0f0ff;
}
```

### Badges

```css
.badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border: 2px solid var(--border);
  font-size: 0.75rem;
  font-weight: 600;
}

.badge-success { background-color: var(--success); color: white; }
.badge-warning { background-color: var(--secondary); }
.badge-error   { background-color: var(--destructive); color: white; }
.badge-info    { background-color: var(--main); color: white; }
```

### Progress Bar

```css
.progress {
  height: 24px;
  background-color: white;
  border: 3px solid var(--border);
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background-color: var(--main);
  transition: width 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
  color: white;
}
```

## Layout

### Grid Background

Background menggunakan grid pattern halus.

```css
body {
  background-color: var(--bg);
  background-image:
    linear-gradient(rgba(0,0,0,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,0,0,0.03) 1px, transparent 1px);
  background-size: 20px 20px;
}
```

### Page Structure

```
┌─────────────────────────────────────────────────────────┐
│  ▰ mimo-farmer    [Dashboard] [Create] [Accounts] [⚙]  │ ← Navbar
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │
│  │ Total   │ │ Today   │ │ Balance │ │ Success │      │ ← Stats Cards
│  │ 142     │ │ 6       │ │ $324.32 │ │ 94.2%   │      │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘      │
│                                                         │
│  ┌──────────────────────────────┐ ┌───────────────┐    │
│  │                              │ │               │    │
│  │  Account Table               │ │ Recent        │    │ ← Main Content
│  │  (paginated)                 │ │ Activity      │    │
│  │                              │ │ Feed          │    │
│  │                              │ │               │    │
│  └──────────────────────────────┘ └───────────────┘    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Sidebar (optional, untuk Create page)

```
┌──────────┬──────────────────────────────────────────────┐
│          │                                              │
│ Mode:    │  ┌─────────────────────────────────────────┐ │
│ ○ Single │  │                                         │ │
│ ● Siklus │  │  Live Terminal Output                   │ │
│ ○ Cont.  │  │                                         │ │
│          │  │  [1/14] Navigating to signup... ✓       │ │
│ Referral:│  │  [2/14] Filling form... ✓               │ │
│ [______] │  │  [3/14] Solving CAPTCHA... ⏳           │ │
│          │  │  [4/14] Waiting OTP... ○                │ │
│ Fast:    │  │  ...                                    │ │
│ [  ON  ] │  │                                         │ │
│          │  └─────────────────────────────────────────┘ │
│ [CREATE] │                                              │
│          │  ┌─────────────────────────────────────────┐ │
│          │  │ Progress ████████░░░░░░░░░ 57%          │ │
│          │  └─────────────────────────────────────────┘ │
└──────────┴──────────────────────────────────────────────┘
```

## Iconography

Gunakan emoji atau simple SVG icons. Tidak perlu icon library berat.

| Action | Icon |
|--------|------|
| Create | ➕ |
| Export | 📥 |
| Delete | 🗑️ |
| Copy | 📋 |
| Search | 🔍 |
| Settings | ⚙️ |
| Success | ✅ |
| Error | ❌ |
| Warning | ⚠️ |
| Loading | ⏳ |
| Dashboard | 📊 |
| Account | 👤 |
| Balance | 💰 |
| API Key | 🔑 |

## Animations

Minimal, sesuai neobrutalism. Transitions cepat dan tegas.

```css
/* Hover transition */
transition: all 0.1s ease;

/* Loading spinner (simple rotate) */
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Progress bar fill */
.progress-bar {
  transition: width 0.3s ease;
}

/* Page transition */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
```

## Responsive Breakpoints

| Breakpoint | Width | Layout |
|------------|-------|--------|
| Mobile | < 640px | Single column, stacked |
| Tablet | 640-1024px | 2-column grid |
| Desktop | > 1024px | Full layout with sidebar |

## Page List

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/` | Stats overview + recent activity |
| Create | `/create` | Account creation form + live progress |
| Accounts | `/accounts` | Account table + search/filter/export |
| Settings | `/settings` | Configuration page |
| Batch Detail | `/batch/:id` | Single batch file detail |

## Dark Mode (Optional)

```css
[data-theme="dark"] {
  --bg: #1a1a2e;
  --bg-alt: #16213e;
  --text: #e0e0e0;
  --text-muted: #a0a0a0;
  --border: #e0e0e0;
  --main: #7b9fff;
  --secondary: #ffd666;
}
```

Shadow di dark mode menggunakan warna terang (white/gray) bukan hitam.
