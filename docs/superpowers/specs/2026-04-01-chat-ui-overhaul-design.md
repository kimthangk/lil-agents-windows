# Chat UI Overhaul — Design Spec

**Date:** 2026-04-01
**Author:** Thanakorn Angkasirisan
**Status:** Approved

---

## Goal

Bring the chat popover and character feedback up to parity with the original macOS lil-agents in terms of aesthetics and feel. Three deliverables: (1) polished character-specific chat popover with markdown rendering, (2) thinking bubble above the character while waiting for a response.

## Architecture

Two files change materially: `chat_popover.py` (full rewrite of UI and rendering) and `walker_character.py` (add thinking bubble). `main.py` gets minor updates to pass character name and color into the popover. A new `pip` dependency `markdown` is added to `requirements.txt`.

**Tech Stack:** PyQt6, Python `markdown` library

---

## Section 1: Chat Popover — Layout & Visual Style

### Character-specific accent colors
- Bruce: `#a6e3a1` (green, Catppuccin Mocha green)
- Jazz: `#fab387` (orange, Catppuccin Mocha peach)

Accent color is used for:
- Left border of the header bar (3px solid strip)
- Character name label in message bubbles
- Input field border when focused
- Inline code background tint

### Layout
```
┌─────────────────────────────────┐
│ ● Bruce            claude ▾  ✕ │  ← header
├─────────────────────────────────┤
│                                 │
│  You: hey                       │
│                                 │
│  Bruce: Here's an example:      │
│  ┌─────────────────────────┐    │
│  │ print("hello")          │    │  ← code block
│  └─────────────────────────┘    │
│                                 │
├─────────────────────────────────┤
│ Thinking...            [▋]      │  ← status + streaming cursor
│ ┌─────────────────────────────┐ │
│ │ Message...                  │ │  ← input
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

Size: 460×400px. Dark base: Catppuccin Mocha (`#1e1e2e`).

### Header
- Left accent dot (●) in character color
- Character name (e.g. "Bruce") in white, bold
- Provider combo box on the right
- Close button (✕) far right, `setDefault(False)`, `setAutoDefault(False)`

---

## Section 2: Markdown Rendering

### Streaming phase
- Raw text is appended to `QTextEdit` as it arrives, monospace font
- A blinking cursor character `▋` is appended at the end of the current response and removed on each new chunk (simulates live output)
- Status label shows `"Thinking..."` until first chunk arrives, then clears

### Render-on-finish phase
When `finished` signal fires:
1. The raw streamed text for the current response is stored in `_raw_response`
2. Convert `_raw_response` → HTML using `markdown.markdown(text, extensions=['fenced_code', 'nl2br'])`
3. Apply character-accent CSS for code backgrounds inline
4. Replace the streamed raw text block with the rendered HTML using `QTextCursor` (find the block by stored cursor position, select it, replace)
5. Re-enable input, focus input field

### Supported markdown elements
- `**bold**`, `*italic*`
- `# H1`, `## H2`, `### H3` (font-size scaled to fit small popover)
- `` `inline code` `` — monospace, slight accent-tinted background
- ` ```fenced code blocks``` ` — monospace, `#181825` background, full width
- `-` / `1.` lists
- Paragraph spacing

### CSS injected into QTextEdit
Applied via `document().setDefaultStyleSheet()`:
```css
code { font-family: Consolas, monospace; background: #313244; padding: 1px 4px; }
pre  { background: #181825; padding: 8px; margin: 4px 0; }
h1, h2, h3 { color: #cdd6f4; margin: 4px 0; }
p    { margin: 2px 0; }
ul, ol { margin: 2px 0; padding-left: 16px; }
```
Accent color applied to `code` background per-character at runtime.

---

## Section 3: Thinking Bubble

### Widget
`ThinkingBubble(QWidget)` — a child of the overlay container (same parent as the character labels).

### Appearance
- Pill-shaped, rounded corners (border-radius: 10px)
- Background: `#1e1e2e`, border: 1.5px solid `<character accent color>`
- Text: accent color, Consolas 9pt
- Size: auto-fit to text, min-width 60px, height 24px
- Positioned: centered above the character's head, 6px gap

### Behavior
- **Show:** when `session.send()` is called — `character.show_thinking()`
- **Phrase rotation:** random phrase from list every 3–5s using `QTimer`
- **Hide condition 1:** when `session.finished` fires and popover is open — just hide silently
- **Hide condition 2:** when `session.finished` fires and popover is NOT open — show `"done!"` in accent color for 2s then hide
- **Never shown** when popover is open (redundant with status label)

### Phrase list (from original Swift source)
`"hmm..."`, `"thinking..."`, `"one sec..."`, `"ok hold on"`, `"let me check"`, `"working on it"`, `"almost..."`, `"bear with me"`, `"on it!"`, `"gimme a sec"`, `"brb"`, `"processing..."`, `"hang tight"`, `"just a moment"`, `"figuring it out"`, `"crunching..."`, `"reading..."`, `"looking..."`, `"cooking..."`, `"vibing..."`, `"digging in"`, `"connecting dots"`, `"give me a sec"`, `"don't rush me"`, `"calculating..."`, `"assembling..."`

### API added to WalkerCharacter
```python
def show_thinking(self) -> None: ...   # start bubble + phrase rotation
def hide_thinking(self, done=False) -> None: ...  # hide (done=True shows "done!" first)
```

---

## Changes by File

| File | Change |
|------|--------|
| `chat_popover.py` | Full rewrite — character name/color params, markdown rendering, streaming cursor, improved layout |
| `walker_character.py` | Add `ThinkingBubble` widget + `show_thinking()` / `hide_thinking()` methods |
| `main.py` | Pass `name` and `accent_color` to `ChatPopover`; call `character.show_thinking()` / `hide_thinking()` on session events |
| `requirements.txt` | Add `markdown>=3.5` |

---

## Out of Scope
- Conversation history persistence across popover open/close
- Sound effects
- Multiple themes
- Link clicking
- Tool use display
