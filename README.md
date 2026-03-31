# lil agents for Windows

Tiny AI companions that live above your Windows taskbar.

**Bruce** and **Jazz** walk back and forth just above your taskbar. Click one to open an AI chat. They walk, they think, they vibe.

Supports **Claude Code** and **Google Gemini** CLIs.

> **Original idea, character design, and animations by [Ryan Stephen](https://github.com/ryanstephen/lil-agents).**
> This is an unofficial Windows port built with Python and PyQt6. The original macOS app can be found at [lilagents.xyz](https://lilagents.xyz).

---

## features

- Animated characters walk above the taskbar with synchronized movement
- Transparent background — characters appear to walk directly on your desktop
- Click a character to open a chat popover and talk to an AI
- Switch between Claude and Gemini from the chat header
- Slash commands in the chat: `/clear`, `/copy`, `/help`
- Thinking status indicator while your agent responds
- System tray icon — right-click to quit

## requirements

- Windows 10 or 11
- At least one supported CLI installed and authenticated:
  - [Claude Code](https://docs.anthropic.com/en/docs/claude-code) — `npm install -g @anthropic-ai/claude-code` then `claude login`
  - [Google Gemini CLI](https://github.com/google-gemini/gemini-cli) — `npm install -g @google/gemini-cli` then `gemini auth`

## running from source

```bash
# Install dependencies
pip install -r requirements.txt

# Convert assets from original .mov files (requires ffmpeg)
python tools/convert_assets.py --mov-dir /path/to/lil-agents/LilAgents

# Run
python main.py
```

**Dependencies:** Python 3.11+, PyQt6

## building the .exe

```bash
pip install -r requirements-dev.txt
python -m PyInstaller lil_agents.spec
# Output: dist/LilAgents.exe
```

## usage

Once running, Bruce and Jazz appear above your taskbar.

- **Click a character** to open the chat
- **Type your message** and press Enter
- **Switch AI provider** using the dropdown in the chat header
- **Close the chat** with the ✕ button or Esc
- **Quit the app** by right-clicking the tray icon (near the clock, bottom-right)

### chat commands

| Command  | Description                        |
|----------|------------------------------------|
| `/clear` | Clear the conversation             |
| `/copy`  | Copy the last response to clipboard |
| `/help`  | Show available commands            |

## privacy

Lil Agents for Windows runs entirely on your machine and sends no data anywhere.

- **Animations and positioning** are handled locally using bundled GIF assets and the Windows taskbar API.
- **AI conversations** are handled by the CLI tool you choose (Claude or Gemini) running as a local subprocess. Lil Agents does not intercept, store, or transmit your chat content. Any data sent to the provider is governed by their respective terms and privacy policies.
- **No accounts, no analytics, no telemetry** in the app itself.

## credits

- **Original concept, character design, and animations:** [Ryan Stephen](https://github.com/ryanstephen/lil-agents) — [lilagents.xyz](https://lilagents.xyz)
- **Windows port:** built with Python + PyQt6

## license

MIT License. See [LICENSE](LICENSE) for details.
