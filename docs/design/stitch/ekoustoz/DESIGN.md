---
name: Ekoustoz
colors:
  surface: '#e7fff3'
  surface-dim: '#a8e7cd'
  surface-bright: '#e7fff3'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#cbffe8'
  surface-container: '#bbfbe1'
  surface-container-high: '#b6f6db'
  surface-container-highest: '#b0f0d6'
  on-surface: '#002117'
  on-surface-variant: '#3c4a42'
  inverse-surface: '#003829'
  inverse-on-surface: '#befee3'
  outline: '#6c7a71'
  outline-variant: '#bbcabf'
  surface-tint: '#006c49'
  primary: '#006c49'
  on-primary: '#ffffff'
  primary-container: '#10b981'
  on-primary-container: '#00422b'
  inverse-primary: '#4edea3'
  secondary: '#855300'
  on-secondary: '#ffffff'
  secondary-container: '#fea619'
  on-secondary-container: '#684000'
  tertiary: '#006591'
  on-tertiary: '#ffffff'
  tertiary-container: '#23acf1'
  on-tertiary-container: '#003d59'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#6ffbbe'
  primary-fixed-dim: '#4edea3'
  on-primary-fixed: '#002113'
  on-primary-fixed-variant: '#005236'
  secondary-fixed: '#ffddb8'
  secondary-fixed-dim: '#ffb95f'
  on-secondary-fixed: '#2a1700'
  on-secondary-fixed-variant: '#653e00'
  tertiary-fixed: '#c9e6ff'
  tertiary-fixed-dim: '#89ceff'
  on-tertiary-fixed: '#001e2f'
  on-tertiary-fixed-variant: '#004c6e'
  background: '#e7fff3'
  on-background: '#002117'
  surface-variant: '#b0f0d6'
typography:
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '800'
    lineHeight: 40px
  headline-xl-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 26px
    fontWeight: '800'
    lineHeight: 32px
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 30px
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '700'
    lineHeight: 26px
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '500'
    lineHeight: 24px
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 22px
  body-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '700'
    lineHeight: 18px
  label-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
  label-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 14px
rounded:
  sm: 0.5rem
  DEFAULT: 1rem
  md: 1.5rem
  lg: 2rem
  xl: 3rem
  full: 9999px
spacing:
  gutter: 1rem
  margin: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1rem
  space-xl: 1.5rem
---

## Brand & Style

This design system is tailored for an eco-educational Telegram Mini App experience aimed at Uzbek youth, school students aged 10–15, teachers, and their families. The aesthetic marries environmental mindfulness with approachable, tactile gamification. 

### Visual Philosophy
- **Approachable Gamification**: Friendly, uplifting, and rewarding without feeling childish. Interfaces prioritize clear progress metrics, vibrant achievement tokens, streak mechanics, and tactile feedback.
- **Eco-Modern Tactility**: Clean sustainability expressed through soft organic surfaces, leafy verdant accents, and subtle layered elevation rather than rustic, distressed metaphors.
- **Telegram Native Ergonomics**: Optimized for compact webview viewports (390px base width) with instantaneous micro-interactions, low visual friction, thumb-driven reach zones, and safe-area resilience.

## Colors

The palette leverages a fresh emerald core anchored by high-energy gamification accents and pedagogical cues. Waste categories and educational streams rely on semantic role assignments.

### Functional Palette Roles
- **Primary (`#10B981`)**: Leaf/Emerald Green representing eco-action, verified status, active task completions, and brand surfaces. Darker steps (`#059669`, `#047857`) serve button presses and heavy contrast requirements.
- **Secondary (`#F59E0B`)**: Amber/Gold for gamification dynamics: streaks, point tallies, star ratings, and celebratory badges.
- **Tertiary (`#0EA5E9`)**: Sky Blue denoting quizzes, educational modules, hints, and instructional steps.
- **Neutral Core (`#064E3B`, `#0F172A`)**: Deep forest green and midnight slate for high-legibility typography, maintaining gentle readability in natural light without harsh pure-black contrast.
- **Surface & Canvas (`#F0FDF4`, `#F9FAFB`, `#FFFFFF`)**: Light sage and crisp canvas backdrops that provide high contrast for cards and indicators.

### Category Accent Tokens
- **Plastic**: `#0284C7` (Ocean Azure)
- **Glass**: `#10B981` (Emerald Jade)
- **Paper & Cardboard**: `#D97706` (Craft Amber)
- **Textile**: `#8B5CF6` (Bright Violet)
- **Organic**: `#84CC16` (Sprout Lime)

## Typography

Typography prioritizes quick readability across multilingual contexts (Uzbek Latin/Cyrillic and Russian). Using Plus Jakarta Sans across all roles provides a welcoming, rounded, and contemporary feel suitable for school-age students and educators.

### Type Rules
- **Base Body Floor**: Core reading copy never drops below 15px/16px to accommodate rapid scanning and younger readers.
- **Numbers & Scores**: Level counts, streak indicators, and eco-points leverage `800` weight to stand out within dense badge layouts.
- **Letter Spacing**: Use default or slightly generous spacing (`+0.01em` on labels) to prevent optical crowding in Cyrillic glyphs.

## Layout & Spacing

Layouts follow a single-column, fluid grid optimized for Telegram Web App container dimensions (standard 390px reference frame).

### Layout Rules
- **Canvas Margins**: Fixed `1rem` (16px) left/right gutters on mobile to maximize horizontal touch area.
- **Viewport Resilience**: Bottom views must respect Telegram's Main Button overlay and native swipe-to-close gestures by incorporating an automatic bottom safe-area offset (`24px` + safe-inset).
- **Rhythm**: Component spacing relies on strict multiples of 4px/8px, keeping compact card clusters readable without vertical scroll bloat.

## Elevation & Depth

This system avoids heavy drop shadows, opting for soft, tinted ambient diffusions that simulate clean daylight over lush eco-surfaces.

### Elevation Levels
- **Level 0 (Flat)**: Background canvas (`#F9FAFB` or soft `#F0FDF4`).
- **Level 1 (Card Default)**: Surface color `#FFFFFF` with a 1px solid border in `#E5E7EB` or `#DCFCE7`, backed by `0 2px 8px -2px rgba(6, 78, 59, 0.05)`.
- **Level 2 (Interactive & Floating)**: Elevated quiz options and floating stat chips use `0 8px 18px -4px rgba(6, 78, 59, 0.10)`.
- **Level 3 (Modals & Sheets)**: Telegram bottom drawer containers use `0 -4px 24px -2px rgba(15, 23, 42, 0.12)`.

## Shapes

The interface embraces pill and bulbous organic corner radii to deliver an approachable, friendly, and gamified feel.

### Corner Application
- **Buttons & Chips**: Fully pill-shaped (`rounded-full`, 9999px) to invite direct fingertip tapping.
- **Cards & Banners**: Generously rounded (`rounded-2xl` at 1.5rem to `rounded-3xl` at 2rem) for an inviting, tactile profile.
- **Input Fields & Small Badges**: Scaled down to `1rem` to preserve structural balance against full-width elements.

## Components

### Buttons
- **Primary CTA**: Height of 52px (minimum 48px), pill-shaped, vibrant `#10B981` background, crisp white bold text. Includes a 2px downward tactile shadow (`box-shadow: 0 4px 0 #047857`) that compresses slightly on active press.
- **Secondary / Action**: Pale emerald background (`#ECFDF5`), `#047857` text, no outline, giving a soft, low-pressure alternative.
- **Gamified Boost Button**: Amber gradient fill (`#F59E0B` to `#D97706`), pill-shaped, paired with streak icons.

### Badges & Streak Counters
- **Flame Streak Counter**: Compact pill with `#FEF3C7` background, `#D97706` text, holding an animated flame icon and bold numeric counter.
- **Category Badge**: Pill tag featuring category-specific background tints at 15% opacity with full-contrast matching solid text (e.g., Organic uses `#F7FEE7` background with `#4D7C0F` text).

### Level & Progress Bars
- **Height**: 12px track, pill-radius ends.
- **Track**: Light neutral surface (`#E5E7EB` or `#DCFCE7`).
- **Indicator Fill**: Solid `#10B981` with an inner glossy white highlight along the top edge for a playful physical aesthetic.

### Cards
- **Challenge Card**: White background, 24px radius, 16px internal padding. Left-aligned visual category icon with a progress badge pinned to the top right.
- **Quiz Choice Card**: Interactive tile with 20px radius, 1.5px border in `#E5E7EB`. Shifts to a thick 2px `#10B981` border with light `#ECFDF5` background on selection.

### Form Inputs
- **Text & Code Entry**: 50px height, 16px radius, filled background `#F3F4F6`, borderless by default. Transitions to a 2px border in `#10B981` with `#FFFFFF` background upon focus.

### Lists & Activity Rows
- **Leaderboard / Task Rows**: Framed as separate cards or separated by soft divider bands within a 24px card. Icons sit in 40px rounded squircle containers with light contextual tints.