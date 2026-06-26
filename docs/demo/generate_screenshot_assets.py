from __future__ import annotations

import json
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEMO_DATA = ROOT / "docs" / "demo" / "reboundiq_demo_persona.json"


PALETTE = [
    ("#14b8a6", "#0f766e"),
    ("#f59e0b", "#92400e"),
    ("#60a5fa", "#1d4ed8"),
    ("#a78bfa", "#6d28d9"),
    ("#34d399", "#047857"),
    ("#f472b6", "#be185d"),
    ("#f87171", "#b91c1c"),
    ("#22d3ee", "#0e7490"),
    ("#c4b5fd", "#7c3aed"),
]


def _text(x: int, y: int, value: str, *, size: int = 18, color: str = "#e5e7eb", weight: int = 500) -> str:
    return (
        f'<text x="{x}" y="{y}" fill="{color}" font-family="Inter, Segoe UI, Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}">{escape(value)}</text>'
    )


def _pill(x: int, y: int, value: str, color: str) -> str:
    width = max(128, len(value) * 8 + 28)
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="34" rx="8" fill="{color}" opacity="0.22" '
        f'stroke="{color}" stroke-opacity="0.55"/>'
        + _text(x + 14, y + 22, value, size=13, color="#f8fafc", weight=600)
    )


def render_screenshot(item: dict, index: int) -> str:
    accent, deep = PALETTE[index % len(PALETTE)]
    highlights = item.get("highlights", [])
    cards = []
    for card_index, label in enumerate(highlights[:3]):
        x = 64 + card_index * 270
        cards.append(
            f'<rect x="{x}" y="274" width="240" height="142" rx="10" fill="#111827" stroke="#273449"/>'
        )
        cards.append(_text(x + 18, 310, f"0{card_index + 1}", size=16, color=accent, weight=800))
        cards.append(_text(x + 18, 352, label[:34], size=18, color="#f9fafb", weight=700))
        cards.append(
            f'<rect x="{x + 18}" y="378" width="{150 + (card_index * 24)}" height="10" rx="5" fill="{accent}" opacity="0.72"/>'
        )
    cards_svg = "\n".join(cards)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="960" height="600" viewBox="0 0 960 600" role="img" aria-labelledby="title desc">
  <title id="title">{escape(item["workflow"])} screenshot</title>
  <desc id="desc">Synthetic ReboundIQ demo screenshot for {escape(item["route"])}.</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#020617"/>
      <stop offset="0.62" stop-color="#111827"/>
      <stop offset="1" stop-color="{deep}"/>
    </linearGradient>
  </defs>
  <rect width="960" height="600" fill="url(#bg)"/>
  <rect x="32" y="32" width="896" height="536" rx="18" fill="#050816" stroke="#1f2937"/>
  <rect x="32" y="32" width="896" height="54" rx="18" fill="#0b1120"/>
  <circle cx="64" cy="59" r="7" fill="#ef4444"/>
  <circle cx="88" cy="59" r="7" fill="#f59e0b"/>
  <circle cx="112" cy="59" r="7" fill="#22c55e"/>
  <rect x="152" y="47" width="362" height="24" rx="8" fill="#111827" stroke="#273449"/>
  {_text(168, 64, "localhost:3000" + item["route"], size=12, color="#94a3b8", weight=500)}
  <rect x="64" y="122" width="240" height="34" rx="8" fill="{accent}" opacity="0.18" stroke="{accent}" stroke-opacity="0.5"/>
  {_text(80, 145, "ReboundIQ local-first demo", size=14, color="#d1fae5", weight=700)}
  {_text(64, 208, item["headline"], size=38, color="#ffffff", weight=800)}
  {_text(64, 242, item["workflow"], size=18, color="#cbd5e1", weight=600)}
  {_pill(704, 132, "Local AI", accent)}
  {_pill(704, 178, "No auto-send", "#f59e0b")}
  {cards_svg}
  <rect x="64" y="466" width="832" height="58" rx="12" fill="#0f172a" stroke="#243244"/>
  {_text(88, 502, "Planning guidance only. Review employment, immigration, tax, and financial decisions with qualified professionals.", size=15, color="#cbd5e1", weight=600)}
</svg>
"""


def main() -> None:
    data = json.loads(DEMO_DATA.read_text(encoding="utf-8"))
    for index, item in enumerate(data["screenshots"]):
        output = ROOT / item["path"]
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_screenshot(item, index), encoding="utf-8")


if __name__ == "__main__":
    main()
