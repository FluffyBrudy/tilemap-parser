# Plan for Adding Examples to Webdocs

## Goal
Enhance the tilemap-parser webdocs with three downloadable examples:
1. Full Game Example (existing game-example)
2. Animation Only Example (sprite animation display)
3. Collision Only Example (collision detection without animation)

## Steps

### 1. Prepare Example Directories
- Ensure each example is self-contained with all necessary assets
- Create minimal, focused examples for animation-only and collision-only
- Verify all examples run correctly

### 2. Create Downloadable Packages
- Create zip archives for each example:
  - `full-game-example.zip`
  - `animation-example.zip`
  - `collision-example.zip`
- Place zips in `tilemap-parser/webdocs/public/examples/`

### 3. Update Webdocs
- Add new "Examples" section to sidebar navigation
- Create Examples page (`src/pages/Examples.tsx`) with:
  - Introduction and overview
  - Three example cards, each containing:
    * Title and description
    * Key features list
    * Code snippets highlighting core functionality
    * Download button linking to the corresponding zip
    * "View Source" link to GitHub directory
- Update `App.tsx` to route to the new Examples page
- Enhance styling for example cards and download buttons

### 4. Example Details

#### Full Game Example
- Based on existing `tilemap-parser/examples/game-example`
- Features: Complete game with player movement, animation, collision, rendering
- Key files to highlight: `src/game.py`, `test_game.py`, assets, data files

#### Animation Only Example
- New minimal example focusing solely on sprite animation
- Features: Load and play sprite animations without game logic or collision
- Key components: SpriteAnimationSet, AnimationPlayer, basic pygame loop
- Will include: Simple animation sheet, JSON animation data, Python script

#### Collision Only Example
- New minimal example focusing solely on collision detection
- Features: Demonstrate collision system without animation or complex rendering
- Key components: CollisionCache, CollisionRunner, TileLayerRenderer (for tilemap only)
- Will include: Tilemap JSON, collision data, simple debug rendering

### 5. Implementation Notes
- Keep examples as simple as possible while demonstrating core features
- Ensure all examples include clear README with run instructions
- Use consistent styling with existing webdocs
- Test all downloadable zips to ensure they contain complete, runnable examples
- Update webdocs build process if needed to include new assets

## Files to Create/Modify
- `tilemap-parser/webdocs/PLAN.md` (this file)
- `tilemap-parser/webdocs/src/pages/Examples.tsx` (new)
- `tilemap-parser/webdocs/src/App.tsx` (route addition)
- `tilemap-parser/webdocs/src/components/Sidebar.tsx` (navigation addition)
- `tilemap-parser/webdocs/public/examples/` (directory for zip files)
- Animation example source directory
- Collision example source directory

## Testing
- Verify each example zip extracts and runs correctly
- Test webdocs builds and links work
- Confirm download buttons function properly
- Ensure sidebar navigation updates correctly