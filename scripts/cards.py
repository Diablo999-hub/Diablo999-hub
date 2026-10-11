"""Self-hosted GitHub stat cards (no third-party stats services).

    python scripts/cards.py --user Diablo999-hub --out assets
    python scripts/cards.py --user Diablo999-hub --out assets --demo   # fake numbers, offline

Writes:
    assets/card-stats-{dark,light}.svg   stars, repos, followers, contributions, streaks
    assets/card-langs-{dark,light}.svg   most-used languages by bytes (own, non-fork repos)

Reads GITHUB_TOKEN from the environment. With a token it uses GraphQL and can
read the contribution calendar; without one it falls back to the public REST
API and the contribution tiles show a dash.
"""
import argparse
import datetime as dt
import json
import os
import urllib.request
from xml.sax.saxutils import escape

THEMES = {
    "dark": dict(bg="#0a1020", border="#27324a", text="#c9d4e5", muted="#7f8da6",
                 accent="#35e0f0", accent2="#ff4fd8", track="#16203a"),
    "light": dict(bg="#f6f8fb", border="#d5dce8", text="#1b2433", muted="#5b6980",
                  accent="#0a7f8c", accent2="#b4157f", track="#e6ebf2"),
}
FONT = 'ui-monospace,SFMono-Regular,Menlo,Consolas,"DejaVu Sans Mono",monospace'
API = "https://api.github.com"

QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


# --------------------------------------------------------------------------- #
# Data
# --------------------------------------------------------------------------- #
def _req(url, token, body=None):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-cards"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def streaks(days):
    """days: list of (date_str, count) sorted ascending. Returns (current, longest)."""
    longest = run = 0
    for _, c in days:
        run = run + 1 if c > 0 else 0
        longest = max(longest, run)
    today = dt.date.today().isoformat()
    cur = 0
    seq = list(days)
    # A zero for today doesn't break the streak yet: the day isn't over.
    if seq and seq[-1][0] >= today and seq[-1][1] == 0:
        seq = seq[:-1]
    for _, c in reversed(seq):
        if c == 0:
            break
        cur += 1
    return cur, longest


def fetch_graphql(user, token):
    res = _req(f"{API}/graphql", token, {"query": QUERY, "variables": {"login": user}})
    if "errors" in res:
        raise RuntimeError(res["errors"])
    u = res["data"]["user"]
    repos = u["repositories"]["nodes"]
    langs = {}
    for r in repos:
        for e in r["languages"]["edges"]:
            name = e["node"]["name"]
            size, color = langs.get(name, (0, e["node"]["color"]))
            langs[name] = (size + e["size"], color or "#888888")
    cal = u["contributionsCollection"]["contributionCalendar"]
    days = [(d["date"], d["contributionCount"]) for w in cal["weeks"] for d in w["contributionDays"]]
    cur, longest = streaks(days)
    return dict(
        stars=sum(r["stargazerCount"] for r in repos),
        repos=u["repositories"]["totalCount"],
        followers=u["followers"]["totalCount"],
        contributions=cal["totalContributions"],
        current=cur,
        longest=longest,
        langs=langs,
    )


def fetch_rest(user, token):
    info = _req(f"{API}/users/{user}", token)
    repos = [r for r in _req(f"{API}/users/{user}/repos?per_page=100&type=owner", token) if not r["fork"]]
    langs = {}
    for r in repos:
        for name, size in _req(r["languages_url"], token).items():
            langs[name] = (langs.get(name, (0, None))[0] + size, None)
    return dict(
        stars=sum(r["stargazers_count"] for r in repos),
        repos=len(repos),
        followers=info["followers"],
        contributions=None, current=None, longest=None,
        langs=langs,
    )


def demo():
    return dict(stars=12, repos=14, followers=9, contributions=318, current=4, longest=17,
                langs={"Python": (412000, "#3572A5"), "Jupyter Notebook": (250000, "#DA5B0B"),
                       "Shell": (38000, "#89e051"), "HTML": (30000, "#e34c26"),
                       "Java": (22000, "#b07219"), "C++": (9000, "#f34b7d")})


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
FALLBACK_COLORS = ["#35e0f0", "#ff4fd8", "#8b7cf6", "#f5c542", "#4ade80", "#fb7185", "#60a5fa", "#7f8da6"]


def fmt(v):
    if v is None:
        return "—"
    return f"{v / 1000:.1f}k" if v >= 10000 else str(v)


def frame(w, h, t, title, subtitle, label):
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
        f'role="img" aria-label="{escape(label)}">',
        f"<style>text{{font-family:{FONT}}}"
        ".f{animation:f .6s ease-out both}@keyframes f{from{opacity:0;transform:translateY(4px)}}"
        "@media (prefers-reduced-motion:reduce){.f{animation:none}}</style>",
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="10" fill="{t["bg"]}" stroke="{t["border"]}"/>',
        f'<text x="24" y="36" font-size="15" fill="{t["accent2"]}">$</text>'
        f'<text x="40" y="36" font-size="15" fill="{t["text"]}">{escape(title)}</text>',
        f'<text x="{w - 24}" y="36" font-size="12" text-anchor="end" fill="{t["muted"]}">{escape(subtitle)}</text>',
        f'<line x1="24" y1="50" x2="{w - 24}" y2="50" stroke="{t["border"]}"/>',
    ]


def stats_svg(s, t, user):
    w, h = 480, 210
    tiles = [
        ("stars", s["stars"]), ("public repos", s["repos"]), ("followers", s["followers"]),
        ("contribs (1y)", s["contributions"]), ("current streak", s["current"]),
        ("longest streak", s["longest"]),
    ]
    out = frame(w, h, t, f"netstat --user {user}", "live · auto-refreshed", "GitHub statistics")
    col_w = (w - 48) / 3
    for i, (label, value) in enumerate(tiles):
        cx = 24 + col_w * (i % 3) + col_w / 2
        y = 100 + 68 * (i // 3)
        color = t["accent"] if i < 3 else t["accent2"]
        out.append(
            f'<g class="f" style="animation-delay:{0.08 * i:.2f}s">'
            f'<text x="{cx:.1f}" y="{y}" text-anchor="middle" font-size="26" font-weight="700" fill="{color}">{fmt(value)}</text>'
            f'<text x="{cx:.1f}" y="{y + 22}" text-anchor="middle" font-size="12" fill="{t["muted"]}">{escape(label)}</text></g>'
        )
    out.append("</svg>")
    return "\n".join(out)


def langs_svg(langs, t, top):
    items = sorted(langs.items(), key=lambda kv: -kv[1][0])[:top]
    total = sum(v[0] for _, v in items) or 1
    rows = (len(items) + 1) // 2
    w, h = 480, 104 + 26 * max(rows, 1)
    out = frame(w, h, t, "du -sh ./languages", "by bytes · own repos", "Most used languages")
    bar_x, bar_w, bar_y = 24, w - 48, 70
    out.append(f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="10" rx="5" fill="{t["track"]}"/>')
    out.append(f'<clipPath id="c"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="10" rx="5"/></clipPath><g clip-path="url(#c)">')
    x = bar_x
    colors = []
    for i, (name, (size, color)) in enumerate(items):
        color = color or FALLBACK_COLORS[i % len(FALLBACK_COLORS)]
        colors.append(color)
        seg = bar_w * size / total
        out.append(f'<rect x="{x:.1f}" y="{bar_y}" width="{seg + 0.5:.1f}" height="10" fill="{color}"/>')
        x += seg
    out.append("</g>")
    for i, ((name, (size, _)), color) in enumerate(zip(items, colors)):
        cx = 24 + (w - 48) / 2 * (i % 2)
        y = 112 + 26 * (i // 2)
        pct = 100 * size / total
        out.append(
            f'<g class="f" style="animation-delay:{0.06 * i:.2f}s">'
            f'<circle cx="{cx + 6:.1f}" cy="{y - 4}" r="5" fill="{color}"/>'
            f'<text x="{cx + 18:.1f}" y="{y}" font-size="13" fill="{t["text"]}">{escape(name)}</text>'
            f'<text x="{cx + (w - 48) / 2 - 16:.1f}" y="{y}" font-size="13" text-anchor="end" fill="{t["muted"]}">{pct:.1f}%</text></g>'
        )
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", required=True)
    ap.add_argument("--out", default="assets")
    ap.add_argument("--top", type=int, default=6, help="languages to show")
    ap.add_argument("--ignore", default="", help='comma-separated languages to skip, e.g. "Jupyter Notebook,HTML"')
    ap.add_argument("--demo", action="store_true", help="render with fake numbers, no network")
    a = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN", "")
    if a.demo:
        stats = demo()
    else:
        try:
            if not token:
                raise RuntimeError("no token")
            stats = fetch_graphql(a.user, token)
        except Exception as e:  # noqa: BLE001 - any failure means "try REST"
            print(f"GraphQL unavailable ({e}); falling back to REST")
            stats = fetch_rest(a.user, token)

    ignore = {s.strip() for s in a.ignore.split(",") if s.strip()}
    langs = {k: v for k, v in stats["langs"].items() if k not in ignore}

    for name, theme in THEMES.items():
        with open(os.path.join(a.out, f"card-stats-{name}.svg"), "w", encoding="utf-8") as f:
            f.write(stats_svg(stats, theme, a.user))
        with open(os.path.join(a.out, f"card-langs-{name}.svg"), "w", encoding="utf-8") as f:
            f.write(langs_svg(langs, theme, a.top))
    print("ok", {k: v for k, v in stats.items() if k != "langs"})

