# diff-tree-view

A terminal UI diff viewer for **jujutsu** and **git**, inspired by the VCS panel
in VS Code. Run `dff` inside a repo and get an interactive, keyboard-driven
review experience — tree on the left, rich diff on the right. Inline comment
workflow and copy-as-prompt are **[ ] TODO** and not shipped yet.

Status: **planning / pre-alpha**. This README doubles as the roadmap.

## Implementation Snapshot (2026-04-21)

- [x] VCS backends: `jj` / `git` detect + list changes + load file sides.
- [x] Tree + diff core UI: grouped change tree, stats, split/unified toggle, wrap toggle.
- [x] Auto-refresh watcher + manual `r` reload.
- [x] Transparent theme + terminal light/dark auto-detect.
- [ ] TODO: full responsive layout (`>=140` / `100-139` / `<100` with tab switch).
- [ ] TODO: review workflow (line selection, comment bar, copy-as-prompt).
- [ ] TODO: config loading chain (TOML/env/flags) and key rebinds.
- [ ] TODO: help overlay (`?`), open-in-editor (`e`), conflict-focused review UI.

---

## Why

`jj diff` and `git diff` are great, but reviewing a multi-file change in a
pager means scrolling through flat output with no structure. Existing TUIs
like `lazygit` and `jjui` are fantastic at branch/change operations but treat
diff viewing as secondary. `dff` is the opposite: it is a **dedicated diff
reviewer**, with a file tree, collapsible unchanged regions, side-by-side /
unified modes, responsive layout, and a PR-style commenting flow.

---

## Features

### Visual design

The aesthetic follows [`jjui`](https://github.com/idursun/jjui) and other
minimalist CLIs (zellij, starship): **no Unicode box borders, no "boxed
button" widgets**. Regions are separated by three things only —

1. **Background shade deltas** — a panel's boundary is a thin strip of
   `$surface` over the transparent terminal background, not a `┌─┐` box.
2. **Reverse-color "pill" labels** — section headers, mode indicators,
   and the single colored button (`[ copy ]`) are rendered as solid-
   background padded text (`background: $primary; color: $background;
   padding: 0 1`), not bordered widgets.
3. **Inline symbols** — jj-style graph chars (`@`, `◆`, `○`, `│`, `├`,
   `└`) for the change tree; `▸` / `▾` for comment entries and fold
   markers; middle-dot `·` as the status-bar separator.

Concretely this means, in TCSS: everything gets `border: none;` by
default, no `Static` is wrapped in a `Container` just to get an outline,
and the entire chrome fits within the transparent-background story —
the terminal wallpaper shows through except under pills and overlays.

Wide layout (terminal width `>= 140`), full review session:

```
 CHANGES                                 src/app.py  M +12 -3                split
 @  xmzynnxm  tidy logs                  ────────────────────────────────────────
 │    M  src/app.py     +12 -3            10  def setup():      │ 10  def setup():
 │    M  src/cli.py     +5  -2            11-   import os       │
 │    A  tests/test.py  +25               12-   import sys      │ 12+ import pathlib
 ○  4f2c6a  refactor parser              ··· 236 hidden lines ▾ ···················
 ○  8b1d9e  wip: notes                   250  def main():       │ 250 def main():
 ◆  root()                                 …

 COMMENTS  2                                                             [ copy ]
 ▸ src/app.py   R11-12  pathlib would be more consistent?
 ▸ src/cli.py   L40     missing try/except around subprocess

 comment  ›  src/app.py R11-12 (RIGHT, added)          Enter submit · Esc cancel
 ›  pathlib would be more consistent?_

 dff   ↑↓ nav  ·  space select  ·  c comment  ·  y copy  ·  m mode  ·  ? more  ·  q quit
```

Notes on the mockup:

- `CHANGES`, `src/app.py ... split`, `COMMENTS 2`, `comment`, and `dff`
  are **pills** — solid background, padded text, no border.
- The only horizontal rule (`────`) is a single-line `Rule`/`Static`
  tinted `$foreground 20%`; it's optional and can be hidden.
- Panel separation between tree and diff is a 1-column gap plus a faint
  `$surface 50%` stripe — not a vertical `│`.
- `@ ◆ ○ │` in the tree are the jj graph characters, printed literally.
  git mode substitutes `●` for `Staged` and `○` for `Unstaged`.
- Middle-dot `·` between status-bar hints, styled `$foreground 40%`.

### VCS backends

- **jujutsu** — show the chain of changes from trunk to `@` (default
  revset `trunk()..@`, configurable). Each change is a group in the tree.
- **git** — show `Staged` and `Unstaged` groups, each with its own file list.
- Auto-detect which backend to use based on `.jj` / `.git` in the repo.
- Explicit override via `--backend jj|git` or config.

### Change tree (left panel)

- Groups:
  - jj: one group per change in the revset range.
  - git: `Staged` and `Unstaged`.
- Files nested under a **real directory tree** (like the VS Code Explorer),
  with single-child directories optionally collapsed.
- Per-file badges: `M` / `A` / `D` / `R` status and `+N -N` line stats.
- Per-group summary: file count and aggregate `+N -N`.
- Glob-based ignore list (lock files, `dist/**`, etc. shown but de-emphasized).
- Keyboard navigation: `j/k` or arrow keys, `J/K` for next/prev change.

### Diff view (right panel)

Built on top of
[`textual-diff-view`](https://github.com/batrachianai/textual-diff-view).

- **Side-by-side** and **unified** modes, toggleable with `m`.
- **Word wrap** for long lines (native to `DiffView`, has dedicated
  wrap/no-wrap compose paths in both split and unified modes); toggled
  at runtime with `w`, default from `ui.word_wrap`.
- **Character-level diff highlighting** inside `replace` hunks — changed
  substrings are tinted more strongly than the line-level background, so
  you can see exactly which part of a line moved. Native to `DiffView`.
- **Syntax highlighting** via Textual's `highlight` module (language is
  auto-detected from the filename).
- **Theme-aware** — follows the active Textual theme (default: `textual-ansi`),
  so added/removed/gutter colors match your terminal palette.
- **Transparent background** — by default the app uses `textual-ansi` and sets
  `Screen` and every major container to `background: transparent`, so the
  terminal's own background (including any translucent terminal effect) shows
  through. Only overlays (completion popup, help, confirm dialogs) keep a
  solid `$surface` background. Can be turned off with `ui.transparent = false`.
- **Collapsible unchanged regions** (VS Code-style): contiguous unchanged
  lines are folded into a `N hidden lines` marker; click or press `Enter`
  to expand. Context size and "always expand if small" threshold are
  configurable.
- Synchronized scrolling in split mode.
- Line numbers from both `before` and `after` sides.

### Live auto-refresh (file watcher)

Both the change tree and the currently-open diff are kept **live**. You never
need to quit and relaunch `dff` after editing, staging, or running `jj`/`git`
commands in another terminal.

- A background watcher (based on [`watchfiles`](https://github.com/samuelcolvin/watchfiles), Rust-backed, asyncio-native) observes:
  - The **working tree** (respecting `.gitignore` / `.jjignore`) — catches
    edits to tracked files.
  - **`.git/index`**, **`.git/HEAD`**, `.git/refs/**` — catches `git add`,
    commits, branch switches.
  - **`.jj/`** internal state — catches `jj squash`, `jj new`, `jj abandon`,
    working-copy snapshot changes.
- Events are **debounced** (default 150 ms) so a burst of writes only
  triggers one reload.
- On event: re-run the backend's `list_changes()` + refresh stats; if the
  currently selected file changed, re-render its diff in-place. Scroll
  position and the set of expanded fold regions are preserved across
  refreshes where possible.
- **[ ] TODO**: preserve and re-anchor review comments across refreshes. The
  current build has no in-session comment store yet.
- Manual `r` still works for forcing a reload.
- Disable with `[vcs] watch = false`, or tune with `[vcs.watch] debounce_ms`
  and `[vcs.watch] extra_ignore_globs`.

### Responsive layout

Status: **[ ] TODO** (planned behavior below; current app only auto-forces unified mode when diff panel width is too narrow for split).

Like a responsive web page, `dff` reflows based on terminal width:

| Width        | Layout                                       |
|--------------|----------------------------------------------|
| `>= 140`     | Tree + **split** diff + comment bar          |
| `100 – 140`  | Tree + **unified** diff + comment bar        |
| `< 100`      | Single panel, `Tab` switches tree / diff     |

Breakpoints are configurable.

### Line selection & commenting

Status: **[ ] TODO** (spec below is target behavior; not shipped in the current build).

PR-review workflow without leaving the terminal.

#### LEFT vs RIGHT (which side you're commenting on)

Every comment is anchored to a **side**, matching how GitHub / GitLab /
Gerrit / Sublime Merge model review comments:

- **LEFT**  = the *removed* / *before* version (what the `-` lines show).
- **RIGHT** = the *added*   / *after*  version (what the `+` lines show).
- A comment spanning both sides of the same hunk is labelled `hunk-level`.

How side is determined:

- **Split mode**: the focused column. `h` / `l` (or `Tab`) switches column
  focus; clicking a column focuses it.
- **Unified mode**: by the line prefix — `-` → LEFT, `+` → RIGHT. For a
  context line (` `), default side is RIGHT (the usual "comment on the new
  code" intent); press `[` to force LEFT, `]` to force RIGHT before opening
  the comment.

A selection must belong to a single side. If you drag across sides in split
mode, `dff` asks whether to split it into two comments or abort
(`comment.cross_side = ask | split | reject`).

#### User flow

1. **Select** — mouse click-drag, or `Space` to start/extend a line
   selection (`Shift+↑/↓` to grow). The gutter shows a live tag like
   `L11-12 (LEFT, removed)` or `R8-11 (RIGHT, added)`.
2. **Press `c`** — the bottom comment bar focuses, prefilled with the
   anchor: `src/app.py R8-11 (RIGHT, added)`.
3. **Type** — `Enter` submits (adds to the in-session `CommentStore`),
   `Shift+Enter` or `Ctrl+J` inserts a newline, `Esc` cancels.
4. **Manage** — focus the comment list (`g c`), then `Enter` jumps to the
   anchor (opens the file, expands folds, scrolls to the lines), `e`
   edits, `d` deletes.
5. **Export** — `y` (or click `[copy]`) serializes all comments as a
   markdown prompt and puts it on the clipboard.
6. **Live re-anchoring** — when the watcher refreshes, each comment is
   re-anchored via the new hunk map using `(side, line_range,
   content_hash)`. Shifts are followed automatically; if the commented
   content no longer exists the comment is marked `stale` (dimmed).

#### Exported prompt format

Designed so Claude understands the LEFT / RIGHT distinction without
ambiguity — the side label is spelled out, and the quoted lines are a
real fenced `diff` block:

```markdown
# Code review comments for z9a7 "tidy logs"

> Diff sides: **LEFT** = removed (before), **RIGHT** = added (after).

## src/app.py

### L8-10 (LEFT, removed)
```diff
- import os
- import sys
- from pathlib import Path
```
> Why not drop the whole block?

### R9-11 (RIGHT, added)
```diff
+ import pathlib
+ from typing import Annotated
```
> Does the typing import belong here?

### L9-10 ↔ R8-11 (hunk-level)
> Overall refactor is fine but please split into two commits.
```

Whether code snippets are embedded (the fenced `diff` blocks) is
controlled by `comment.include_code_snippet`. The whole template is
overridable via `comment.templates.custom.path` (Jinja).

### Configuration

Status: **[ ] TODO** (design target below; currently only in-code `UISettings` defaults are wired).

TOML, loaded in this order (later overrides earlier):

1. Built-in defaults
2. `~/.config/dff/config.toml`
3. `./.dff.toml` (project-local)
4. Environment variables (`DFF_UI_THEME=...`)
5. CLI flags

Configurable areas:

- **`[ui]`** — theme, default diff mode, word wrap, line numbers, syntax
  highlighting on/off, transparent background on/off, responsive breakpoints.
- **`[fold]`** — enabled, context lines, "always expand if small" threshold.
- **`[tree]`** — group by change vs directory, show stats, collapse single-
  child dirs, ignore globs.
- **`[vcs.jj]`** — default revset, `--ignore-working-copy`, whether `@` is
  split out as its own row.
- **`[vcs.git]`** — show staged / unstaged, whether to merge them into one
  "Working" group.
- **`[performance]`** — max file lines before falling back to plain text,
  max files per change, parallel subprocess count.
- **`[vcs.watch]`** — enabled, debounce interval (ms), extra ignore globs,
  whether `.git/` and `.jj/` internal state are watched.
- **`[comment]`** — clipboard vs file export, include code snippet in
  prompt, custom Jinja prompt template, `cross_side` behavior
  (`ask | split | reject`), default context-line side
  (`context_side = right | left`).
- **`[keys]`** — every key binding is rebindable.
- **`[integrations]`** — `$EDITOR` for `e` key.

A fully-commented `config.example.toml` ships with the project.

### Keybindings

`[ ]` rows are TODO / planned, not currently implemented.

| Status | Key       | Action                                |
|--------|-----------|---------------------------------------|
| [x]    | `j` / `k` | Next / previous item in tree          |
| [x]    | `J` / `K` | Next / previous change group          |
| [x]    | `Enter`   | Expand/collapse tree node             |
| [ ]    | `Enter`   | Expand fold marker in diff            |
| [ ]    | `Space`   | Toggle line selection (diff)          |
| [ ]    | `[` / `]` | Force comment side to LEFT / RIGHT    |
| [ ]    | `h` / `l` | Switch focused column (split mode)    |
| [ ]    | `c`       | Start a comment on current selection  |
| [ ]    | `g c`     | Focus the comment list                |
| [ ]    | `Esc`     | Cancel comment input / clear selection|
| [ ]    | `y`       | Copy all comments as prompt           |
| [x]    | `m`       | Toggle split / unified                |
| [ ]    | `Tab`     | (narrow) switch tree ↔ diff panel     |
| [x]    | `r`       | Force refresh (normally automatic)    |
| [x]    | `w` / `z` | Toggle word wrap                      |
| [x]    | `d` / `u` | Scroll diff half-page down / up       |
| [x]    | `f` / `b` | Scroll diff page down / up            |
| [ ]    | `e`       | Open current file in `$EDITOR`        |
| [ ]    | `?`       | Help overlay                          |
| [x]    | `q`       | Quit                                  |

---

## Installation

Requires Python 3.14+.

```bash
uv tool install diff-tree-view  # once published
# or for development:
uv sync
uv run dff
```

Runtime deps: `textual`, `textual-diff-view`, `watchfiles`, `typer`.
`pyperclip` is declared but not wired up yet (reserved for the v0.2
comment export flow).

---

## Usage

```bash
dff                          # auto-detect jj or git, show default revset
dff --backend jj --rev '@'   # explicit jj backend + revset
dff --backend git            # force git
dff --version
```

`--mode`, `--staged`, and help overlay (`?`) are **[ ] TODO** and not available yet.

---

## Architecture

```
src/diff_tree_view/
  cli.py                       Typer CLI; --backend / --rev / --version
  app.py                       Textual App; composes tree + diff + status bar
  config.py                    UISettings dataclass (TOML loader planned)
  theme.py                     TreeThemeTokens + built-in DARK / LIGHT palettes
  terminal.py                  OSC-11 background probe → auto dark / light

  vcs/
    base.py                    Protocol: Backend, BackendError
    detect.py                  Picks jj vs git; walks up to repo root
    jj.py                      subprocess: jj log / diff --summary / file show
    git.py                     subprocess: git diff --name-status / show
    watcher.py                 watchfiles-based async iterator;
                               debounced events drive App._refresh_changes()

  widgets/
    change_tree.py             Tree widget with VS Code-style grouping
    diff_panel.py              Header + TransparentDiffView (subclass of
                               textual-diff-view that blanks the split-mode
                               hatch and pulls colors from TreeThemeTokens)
    status_bar.py              Single-line hint bar (• separators)

  app.tcss                     Global stylesheet. Rules:
                               * { scrollbar-background: ansi_default } so the
                               terminal backdrop shows through scrollbar
                               tracks; App.-transparent / App.-opaque toggle
                               the Screen + panel backgrounds; all tree cursor
                               / guide / highlight classes are flattened to
                               `transparent` + `text-style: none`.

  models/
    change.py                  Change, FileChange, FileSides, HunkStats
```

Planned but not yet implemented: `layout.py` (responsive breakpoints),
`widgets/collapsible_diff.py`, `widgets/line_selection.py`,
`widgets/comment_bar.py`, `models/comment.py`, `prompt.py`.

### Transparent background — how it works

Three pieces, combined:

1. **Theme** — `App.theme = "textual-ansi"` in `app.py`. ANSI theme keeps
   palette decisions on the terminal side instead of forcing a light/dark
   surface.
2. **Global TCSS** — `app.tcss` toggles between `App.-transparent` and
   `App.-opaque` based on `UISettings.transparent_background`. In
   transparent mode, `Screen`, `#app-shell`, `#panes`, `#diff-body`,
   `ChangeTree`, `DiffPanel`, `DiffHeader`, and `#status-bar` are all set
   to `background: transparent`; the diff surface explicitly uses
   `ansi_default` so Rich emits `[49m` instead of flattening
   `rgba(0,0,0,0)` to solid black. All scrollbar tracks use
   `scrollbar-background: ansi_default` for the same reason.
3. **Tree cursor & guides** — `.tree--cursor`, `.tree--guides-*`, and the
   hover/highlight classes are flattened to `background: transparent`
   with `text-style: none`, so Textual's default theme-colored hover /
   selection rectangles never paint over the terminal wallpaper.

`TransparentDiffView` further substitutes the diagonal-hatch "missing
line" marker with blank space and pulls diff-add / diff-remove background
shades (`diff_add_bg` / `diff_remove_bg` / `diff_add_char_bg` /
`diff_remove_char_bg`) from the active `TreeThemeTokens`. Those tokens
ship in two built-in palettes (`DARK` / `LIGHT`) and are picked
automatically via `terminal.detect_tree_theme_name()` (OSC-11 query).

### VCS command cheatsheet

**jj**

- Changes in revset:
  `jj log -r '<revset>' --no-graph --ignore-working-copy -T '<template>'`
- Files in a change with status:
  `jj diff -r <id> --summary --ignore-working-copy`
- File content (before / after):
  `jj file show -r <id>- <path>` / `jj file show -r <id> <path>`

**git**

- Staged file list: `git diff --cached --name-status`
- Unstaged file list: `git diff --name-status`
- Content:
  - `HEAD:<path>` (before staged) / `:<path>` (staged index) / worktree file (after unstaged)

---

## Roadmap

### v0.1 — MVP

- [x] Project scaffold (uv, Textual app skeleton, CLI)
- [x] VCS backend abstraction + auto-detect
- [x] jj backend (read-only)
- [x] git backend (read-only)
- [x] Change tree widget with stats and M/A/D/R
- [x] Integrate `textual-diff-view` (split + unified, wrap toggle)
- [ ] Responsive layout (split / unified / tabs)
- [x] File watcher (`watchfiles`) auto-refresh for tree + diff
- [ ] Minimal config: `[ui]`, `[vcs.jj.revset]`, `[vcs.watch]`, `[keys]`, `[comment.clipboard]`

### v0.2 — Review workflow

- [ ] Collapsible unchanged regions (extend `DiffView`)
- [ ] Line selection (mouse + `Space`)
- [ ] Comment bar with in-session store
- [ ] Copy-as-prompt (markdown, clipboard)
- [ ] Custom Jinja prompt template
- [ ] `[fold]`, `[performance]` config sections

### v0.3 — Polish

- [ ] Open-in-editor (`e`)
- [ ] Help overlay (`?`)
- [ ] Ignore-globs with de-emphasized rendering
- [ ] Large-file fallback (plain text, no highlighting)
- [ ] Refresh (`r`) without reloading the app

### Later

- [ ] Write support for comments (persist to `.dff/reviews/*.md`)
- [ ] Watch mode (auto-refresh on file change)
- [ ] Jump to parent change / child change in jj
- [ ] Inline comment rendering next to the diff (not just at the bottom)

---

## Non-goals

- **Not a VCS operations tool.** No commit, squash, rebase, push. Use `jj`,
  `git`, `jjui`, or `lazygit` for that. `dff` is read-only reviewing.
- **Not a merge conflict resolver.**
- **Not a PR client.** `dff` does not know about GitHub / GitLab. It only
  produces prompts / markdown you can paste elsewhere.

---

## Development

```bash
uv sync
uv run dff                   # run against current repo
uv run pytest                # tests
uv run ruff check .
uv run ruff format .
```

---

## Credits

- [`textual`](https://github.com/Textualize/textual) — the TUI framework.
- [`textual-diff-view`](https://github.com/batrachianai/textual-diff-view) —
  the diff rendering widget.
- [`jjui`](https://github.com/idursun/jjui) — reference for how to drive
  `jj` from a TUI.
- VS Code — the UX reference for the file tree and inline fold markers.

---

## License

TBD.
