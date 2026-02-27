# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

This is a GitHub profile README repo (`toqitahamid/toqitahamid`). It renders a neofetch-style terminal card as the GitHub profile page using SVG with live stats updated daily via GitHub Actions.

## Architecture

**`dark_mode.svg` / `light_mode.svg`** — Neofetch-style terminal cards (dark/light theme). The README uses a `<picture>` element with `prefers-color-scheme` to switch between them. Both SVGs share identical structure but use different color palettes. They contain SMIL `<animate>` elements (no JS — GitHub sanitizes it out). Dynamic stat values are identified by `id` attributes on `<tspan>` elements.

**`today.py`** — Python script that fetches live GitHub stats and injects them into both SVGs:
- Uses GitHub GraphQL API for repos, stars, commits, followers
- Uses GitHub REST API (`/stats/contributors`) for lines of code (additions/deletions)
- Updates SVG elements by matching `id` attributes with regex substitution
- Dynamic element IDs: `repos_data`, `stars_data`, `commits_data`, `followers_data`, `loc_data`, `loc_add_data`, `loc_del_data`

**`.github/workflows/update.yaml`** — Runs `today.py` daily at 4am UTC, on push to master, and on manual dispatch. Commits updated SVGs back to the repo.

## Running Locally

```bash
pip install -r requirements.txt
ACCESS_TOKEN=<github-pat> USER_NAME=toqitahamid python today.py
```

Requires a GitHub PAT with repo read access. The script modifies `dark_mode.svg` and `light_mode.svg` in place.

## Key Constraints

- SVGs must not use JavaScript or CSS animations — GitHub only allows SMIL `<animate>` elements
- Both SVGs must have matching `id` attributes on stat elements for `today.py` to update them
- When adding new stats, update: both SVGs (add tspan with id), `today.py` (fetch + inject), and the `update_svg` regex pattern expects the format `id="name">value</tspan>`
- The GitHub Actions bot auto-commits updated SVGs, so always `git pull --rebase` before pushing to avoid divergence
