# BareBlocks website (GitHub Pages source)

The marketing site, documentation, brand kit, and listing copy for BareBlocks. This folder
**is** the published website — GitHub Pages serves it straight from `/docs`.

```
bareblocks/                     # repo root (vkfolio/bareblocks)
├── __init__.py, core/, ui/ …   # the add-on source
├── README.md  LICENSE
└── docs/                       # <- this folder = the website
    ├── index.html              # landing page
    ├── docs.html               # documentation
    ├── .nojekyll               # serve files as-is (no Jekyll)
    ├── css/style.css           # shared styles (light/violet theme)
    ├── assets/                 # renders + logo (hero, poster, blocks, trees, kit, favicon)
    ├── marketplace/            # superhive-listing.md (listing copy)
    └── BRAND.md                # colors, type, voice, logo
```

## Turn on GitHub Pages
Repo → **Settings ▸ Pages ▸ Build and deployment** → Source: **Deploy from a branch** →
Branch: **main**, Folder: **/docs** → Save. The site goes live at
**https://vkfolio.github.io/bareblocks/**.

## Preview locally
Static site, no build step. Open `index.html`, or serve the folder:

```
cd docs
python -m http.server 8080      # http://localhost:8080
```

## Still to set
| Placeholder | Where | Set to |
|-------------|-------|--------|
| `VIDEO_ID` | `index.html` (`#watch`) | your YouTube/Vimeo link, or swap in the commented `<iframe>` / self-hosted `<video controls poster="assets/poster.png" src="assets/demo.mp4">` |
| `[your email]` | `marketplace/superhive-listing.md` | support email |
| `maintainer` email | `../blender_manifest.toml` | your contact |

GitHub handle (`vkfolio`) and the Pages URL are already wired in. BareBlocks is **free and
open source (GPL-3.0)** — the site has no pricing; primary download is GitHub
[releases](https://github.com/vkfolio/bareblocks/releases/latest).
