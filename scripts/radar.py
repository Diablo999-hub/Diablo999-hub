"""Draw a skill radar as light/dark SVGs from a small JSON file.

    python scripts/radar.py --data assets/skills.json -o assets/radar

Writes assets/radar-dark.svg and assets/radar-light.svg.
"""
import argparse
import json
import math
from xml.sax.saxutils import escape

THEMES = {
    "dark": dict(grid="#27324a", axis="#27324a", text="#c9d4e5",
                 fill="#35e0f0", fill_op="0.20", stroke="#35e0f0", dot="#ff4fd8"),
    "light": dict(grid="#d5dce8", axis="#d5dce8", text="#1b2433",
                  fill="#0a7f8c", fill_op="0.16", stroke="#0a7f8c", dot="#b4157f"),
}
W, H, R = 520, 400, 130
CX, CY = W / 2, H / 2 + 6


def pt(i, n, r):
    a = -math.pi / 2 + 2 * math.pi * i / n
    return CX + r * math.cos(a), CY + r * math.sin(a)


def build(axes, t):
    n = len(axes)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        'role="img" aria-label="Skill radar chart">',
        '<style>text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,"DejaVu Sans Mono",monospace}</style>',
    ]
    for ring in (25, 50, 75, 100):
        pts = " ".join("%.1f,%.1f" % pt(i, n, R * ring / 100) for i in range(n))
        out.append(f'<polygon points="{pts}" fill="none" stroke="{t["grid"]}" stroke-width="1"/>')
    for i in range(n):
        x, y = pt(i, n, R)
        out.append(f'<line x1="{CX}" y1="{CY}" x2="{x:.1f}" y2="{y:.1f}" stroke="{t["axis"]}" stroke-width="1"/>')
    pts = [pt(i, n, R * a["value"] / 100) for i, a in enumerate(axes)]
    poly = " ".join("%.1f,%.1f" % p for p in pts)
    out.append(
        f'<polygon points="{poly}" fill="{t["fill"]}" fill-opacity="{t["fill_op"]}" '
        f'stroke="{t["stroke"]}" stroke-width="2" stroke-linejoin="round"/>'
    )
    for x, y in pts:
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{t["dot"]}"/>')
    for i, a in enumerate(axes):
        x, y = pt(i, n, R + 22)
        anchor = "middle" if abs(x - CX) < 8 else ("start" if x > CX else "end")
        dy = -4 if y < CY - 5 else (14 if y > CY + 5 else 4)
        out.append(
            f'<text x="{x:.1f}" y="{y + dy:.1f}" text-anchor="{anchor}" font-size="13" '
            f'fill="{t["text"]}">{escape(a["label"])}</text>'
        )
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("-o", "--out", required=True, help="output prefix")
    args = ap.parse_args()
    axes = json.load(open(args.data, encoding="utf-8"))["axes"]
    for name, theme in THEMES.items():
        with open(f"{args.out}-{name}.svg", "w", encoding="utf-8") as f:
            f.write(build(axes, theme))
    print("ok")

