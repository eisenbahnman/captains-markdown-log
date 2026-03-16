# Captain's Markdown Log

A TUI daily journal and task manager. Daily notes stored as `YYYY-MM-DD.md` files with two sections: **Logs** and **Todos**.

## Features

- Two-pane layout: Logs (left) and Todos (right)
- Inline markdown rendering: **bold**, *italic*, ~~strikethrough~~, ~underline~, ==highlight==, [links](url)
- Auto-timestamp on new log entries (HH:MM, 24h, CET/CEST)
- Auto-bullet on Enter in edit mode
- Tab/Shift+Tab to indent/dedent in edit mode
- Todo toggling with Space
- Navigate between days, jump to nearest existing entries
- Fullscreen any pane
- Resize panes with +/-
- Adapts to Textual themes (command palette: Ctrl+P)

## Keybindings

### Navigation

| Key | Action |
|-----|--------|
| `h` / `Left` | Previous day |
| `l` / `Right` | Next day |
| `[` | Jump to nearest previous entry |
| `]` | Jump to nearest next entry |
| `Tab` | Switch pane |

### Editing

| Key | Action |
|-----|--------|
| `e` | Enter edit mode |
| `Esc` | Save and exit edit mode |
| `Tab` | Indent (in edit mode) |
| `Shift+Tab` | Dedent (in edit mode) |

### Todos

| Key | Action |
|-----|--------|
| `j` / `Down` | Move cursor down |
| `k` / `Up` | Move cursor up |
| `Space` | Toggle todo |

### Other

| Key | Action |
|-----|--------|
| `n` | Create daily file |
| `f` | Toggle fullscreen pane |
| `+` / `-` | Resize panes |
| `Ctrl+P` | Command palette |
| `q` | Quit |

## File Format

```markdown
## Logs

- 09:30 Morning standup notes
    - Follow up on deployment
- 14:00 Review PR #42

## Todos

- [x] Ship feature
- [ ] Write tests
    - [ ] Unit tests
    - [ ] Integration tests
```

## Configuration

Config lives at `~/.config/captains-markdown-log/config.toml`. Created automatically on first run.

```toml
logs_dir = "/home/user/captains-markdown-log"
```
