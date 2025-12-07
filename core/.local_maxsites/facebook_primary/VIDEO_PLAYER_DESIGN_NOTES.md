# Facebook Mobile Video Player Design - 2025

## Overview
This document describes the actual Facebook mobile video player design when clicking on a video post (not Reels) in 2025.

## Key Design Elements

### 1. Fullscreen Vertical Display
- When user clicks a video post, it opens in **fullscreen vertical format**
- Black background (#000)
- Video takes up entire screen
- Immersive viewing experience

### 2. Top Bar (Gradient Overlay)
- **Position**: Fixed at top with gradient background
- **Height**: ~60px
- **Content**:
  - User avatar (circular, 36px)
  - User name (bold, white)
  - Post time (lighter, smaller)
  - Close button (X) on right side
- **Background**: `linear-gradient(to bottom, rgba(0,0,0,0.7), transparent)`

### 3. Bottom Controls Bar (Gradient Overlay)
- **Position**: Fixed at bottom with gradient background
- **Height**: ~120px
- **Components**:
  - Progress bar/slider (with handle)
  - Play/Pause button (large, blue)
  - Rewind 10s button
  - Forward 10s button
  - Time display (current / total)
  - Fullscreen button
- **Background**: `linear-gradient(to top, rgba(0,0,0,0.8), transparent)`

### 4. Side Action Buttons
- **Position**: Right side, vertical stack
- **Buttons**:
  - Like (👍) - Blue when active
  - Comment (💬)
  - Share (📤)
- **Design**: Circular buttons with counts below
- **Background**: `rgba(0,0,0,0.6)` with border

### 5. Auto-Hide Controls
- Controls automatically hide after 3 seconds of inactivity
- Tap video to show/hide controls
- Smooth fade in/out transitions

### 6. Video Controls Features
- **Progress Bar**: Clickable, shows current position
- **Play/Pause**: Large button, easy to tap
- **Skip Controls**: 10 seconds forward/backward
- **Time Display**: Current time / Total duration
- **Fullscreen**: For horizontal videos

## Color Scheme
- Background: `#000` (black)
- Primary Blue: `#1877F2` (Facebook blue)
- Text: `#fff` (white)
- Secondary Text: `rgba(255,255,255,0.8)` (semi-transparent white)
- Overlay: `rgba(0,0,0,0.6-0.8)` (semi-transparent black)

## Typography
- Font: System fonts (-apple-system, BlinkMacSystemFont, Segoe UI, Roboto)
- User Name: 15px, font-weight: 600
- Post Time: 13px, lighter weight
- Time Display: 14px

## Interactions
1. **Click video post** → Opens fullscreen player
2. **Tap video** → Toggle play/pause
3. **Tap controls area** → Show/hide controls
4. **Swipe up** → Next video (if available)
5. **Swipe down** → Close player
6. **Click X** → Close player

## Differences from Current Design

### Current Design (index.php):
- Sensitive Content Modal (warning)
- "See Video" button
- Connecting Modal
- Iframe Modal with login

### Actual Facebook 2025 Design:
- Direct fullscreen video player
- No warning modals
- Immediate video playback
- Native video controls
- Social actions (like, comment, share)

## Implementation Notes
- Video should autoplay when opened
- Controls should auto-hide after 3 seconds
- Smooth transitions for all UI elements
- Responsive to touch gestures
- Dark theme throughout

