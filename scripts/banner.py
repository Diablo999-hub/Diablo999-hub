"""Generate the nmap-style banner (assets/banner-dark.svg / banner-light.svg).

    python scripts/banner.py -o assets/banner

Edit the constants below, then re-run.
"""
import argparse
from xml.sax.saxutils import escape

NAME = "Mario Martínez"
SUBTITLE = "Jr. cybersecurity & data · I learn by breaking things first"
CMD = "nmap -sV --open mario"
HOST = "Host is up. Open to work: trainee / junior roles"
ROWS = [  # port, service, version
    ("22/tcp", "cloud", "AWS · Docker · IAM least-privilege"),
    ("80/tcp", "data", "Python · Pandas · SQL · scikit-learn"),
    ("443/tcp", "offensive", "Nmap · Metasploit · Hack The Box"),
    ("8080/tcp", "learning", "always on"),
]

THEMES = {
    "dark": dict(bg="#0a1020", text="#c9d4e5", muted="#7f8da6", open="#35e0f0", prompt="#ff4fd8", rule="#27324a"),
    "light": dict(bg="#f6f8fb", text="#1b2433", muted="#5b6980", open="#0a7f8c", prompt="#b4157f", rule="#d5dce8"),
}
W = 900
X = (40, 150, 235, 360)  # columns: port, state, service, version


def build(t):
    y0 = 140
    rows_y = [y0 + 98 + 28 * i for i in range(len(ROWS))]
    last = rows_y[-1] + 40
    H = last + 28
    css = (
        'text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"DejaVu Sans Mono",monospace}'
        ".l{animation:in .5s ease-out backwards}"
        "@keyframes in{from{opacity:0;transform:translateY(4px)}}"
        ".c{animation:blink 1s steps(1) 6}"
        "@keyframes blink{50%{opacity:0}}"
        "@media (prefers-reduced-motion:reduce){.l,.c{animation:none}}"
    )
    o = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" '
        f'aria-label="{escape(NAME)}: {escape(SUBTITLE)}">',
        f"<style>{css}</style>",
        f'<rect width="{W}" height="{H}" rx="10" fill="{t["bg"]}"/>',
        f'<text x="40" y="62" font-size="34" font-weight="700" fill="{t["text"]}">{escape(NAME)}</text>',
        f'<text x="40" y="90" font-size="15" fill="{t["muted"]}">{escape(SUBTITLE)}</text>',
        f'<line x1="40" y1="108" x2="{W - 40}" y2="108" stroke="{t["rule"]}"/>',
    ]
    d = 0.4
    o.append(
        f'<g class="l" style="animation-delay:{d}s">'
        f'<text x="40" y="{y0}" font-size="15" fill="{t["prompt"]}">$</text>'
        f'<text x="60" y="{y0}" font-size="15" fill="{t["text"]}">{escape(CMD)}</text></g>'
    )
    d += 0.5
    o.append(
        f'<g class="l" style="animation-delay:{d}s">'
        f'<text x="40" y="{y0 + 28}" font-size="15" fill="{t["muted"]}">{escape(HOST)}</text></g>'
    )
    d += 0.5
    hy = y0 + 66
    heads = "".join(
        f'<text x="{x}" y="{hy}" font-size="13" fill="{t["muted"]}">{h}</text>'
        for x, h in zip(X, ("PORT", "STATE", "SERVICE", "VERSION"))
    )
    o.append(f'<g class="l" style="animation-delay:{d}s">{heads}</g>')
    for (port, svc, ver), y in zip(ROWS, rows_y):
        d += 0.35
        o.append(
            f'<g class="l" style="animation-delay:{d:.2f}s">'
            f'<text x="{X[0]}" y="{y}" font-size="15" fill="{t["text"]}">{port}</text>'
            f'<text x="{X[1]}" y="{y}" font-size="15" fill="{t["open"]}">open</text>'
            f'<text x="{X[2]}" y="{y}" font-size="15" fill="{t["text"]}">{svc}</text>'
            f'<text x="{X[3]}" y="{y}" font-size="15" fill="{t["muted"]}">{escape(ver)}</text></g>'
        )
    d += 0.4
    o.append(
        f'<g class="l" style="animation-delay:{d:.2f}s">'
        f'<text x="40" y="{last}" font-size="15" fill="{t["prompt"]}">$</text>'
        f'<rect class="c" style="animation-delay:{d + 0.5:.2f}s" x="58" y="{last - 13}" '
        f'width="9" height="17" fill="{t["prompt"]}"/></g>'
    )
    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", required=True, help="output prefix")
    a = ap.parse_args()
    for name, theme in THEMES.items():
        with open(f"{a.out}-{name}.svg", "w", encoding="utf-8") as f:
            f.write(build(theme))
    print("ok")

