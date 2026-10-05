"""Gera os cards SVG do perfil (stats, linguagens, streak e atividade) no tema aranha.

Roda no GitHub Actions com o GITHUB_TOKEN. Sem dependências externas.
Uso local de teste: python scripts/generate_cards.py --demo
"""
import json
import os
import sys
import urllib.request
from datetime import date, timedelta
from xml.sax.saxutils import escape

USER = os.environ.get("GH_USER", "josue-menezes")
OUT = os.path.join(os.path.dirname(__file__), "..", "assets")
IGNORE_REPOS = {USER}  # o repo do perfil não entra na conta das linguagens

BG = "#0B1426"
BORDER = "#22304F"
RED = "#E62429"
BLUE = "#3B6BF0"
TEXT = "#C9D6FF"
MUTED = "#7F8BB0"
WHITE = "#FFFFFF"
FONT = "'Segoe UI', Ubuntu, 'Helvetica Neue', Arial, sans-serif"

QUERY = """
query($login: String!) {
  user(login: $login) {
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      nodes {
        name
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
    pullRequests { totalCount }
    issues { totalCount }
    contributionsCollection {
      totalCommitContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def fetch():
    token = os.environ["GITHUB_TOKEN"]
    body = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if "errors" in data:
        sys.exit(f"Erro na API do GitHub: {data['errors']}")
    u = data["data"]["user"]
    repos = [r for r in u["repositories"]["nodes"] if r["name"] not in IGNORE_REPOS]
    langs = {}
    for r in repos:
        for e in r["languages"]["edges"]:
            n = e["node"]["name"]
            prev = langs.get(n, (0, e["node"]["color"] or MUTED))
            langs[n] = (prev[0] + e["size"], prev[1])
    cal = u["contributionsCollection"]["contributionCalendar"]
    days = [(d["date"], d["contributionCount"]) for w in cal["weeks"] for d in w["contributionDays"]]
    return {
        "stars": sum(r["stargazerCount"] for r in repos),
        "repos": len(repos),
        "commits": u["contributionsCollection"]["totalCommitContributions"],
        "prs": u["pullRequests"]["totalCount"],
        "issues": u["issues"]["totalCount"],
        "total": cal["totalContributions"],
        "langs": langs,
        "days": days,
    }


def demo():
    import random
    random.seed(3)
    today = date.today()
    days = [((today - timedelta(days=i)).isoformat(), random.choice([0, 0, 1, 2, 3, 5, 8]))
            for i in range(364, -1, -1)]
    return {
        "stars": 2, "repos": 5, "commits": 120, "prs": 4, "issues": 1,
        "total": sum(c for _, c in days),
        "langs": {"TypeScript": (52000, "#3178c6"), "JavaScript": (31000, "#f1e05a"),
                  "CSS": (18000, "#663399"), "HTML": (12000, "#e34c26"),
                  "Python": (8000, "#3572A5"), "Java": (5000, "#b07219")},
        "days": days,
    }


def frame(w, h, inner):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
        f'<style>text{{font-family:{FONT}}}</style>'
        f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="10" fill="{BG}" stroke="{BORDER}"/>'
        f'<rect x="0.5" y="0.5" width="4" height="{h-1}" rx="2" fill="{RED}"/>'
        f'{inner}</svg>'
    )


def web_corner(w):
    """Pequena teia decorativa no canto superior direito."""
    import math
    cx, cy, parts = w - 1, 1, []
    angs = [math.radians(a) for a in range(95, 181, 17)]
    for t in angs:
        parts.append(f'<line x1="{cx}" y1="{cy}" x2="{cx+70*math.cos(t):.1f}" y2="{cy+70*math.sin(t):.1f}"/>')
    for r in (20, 38, 56):
        pts = " ".join(f"{cx+r*math.cos(t):.1f},{cy+r*math.sin(t):.1f}" for t in angs)
        parts.append(f'<polyline points="{pts}" fill="none"/>')
    return f'<g stroke="{RED}" stroke-width="0.8" opacity="0.35">{"".join(parts)}</g>'


def stats_card(d):
    rows = [("★", "Total de estrelas", d["stars"]),
            ("⎇", "Commits (último ano)", d["commits"]),
            ("⇄", "Pull requests", d["prs"]),
            ("!", "Issues", d["issues"]),
            ("▣", "Repositórios", d["repos"])]
    inner = [web_corner(495),
             f'<text x="25" y="38" fill="{RED}" font-size="18" font-weight="700">Estatísticas do GitHub</text>']
    for i, (ic, label, val) in enumerate(rows):
        y = 75 + i * 25
        inner.append(f'<rect x="27" y="{y-10}" width="9" height="9" rx="2" fill="none" stroke="{BLUE}" stroke-width="2" transform="rotate(45 31.5 {y-5.5})"/>'
                     f'<text x="50" y="{y}" fill="{TEXT}" font-size="14" font-weight="600">{label}:</text>'
                     f'<text x="250" y="{y}" fill="{WHITE}" font-size="14" font-weight="700">{val}</text>')
    # anel com total de contribuições
    import math
    r, cx, cy = 48, 395, 110
    circ = 2 * math.pi * r
    pct = min(d["total"] / 365, 1)
    inner.append(
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{BORDER}" stroke-width="8"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{RED}" stroke-width="8" stroke-linecap="round"'
        f' stroke-dasharray="{circ*pct:.1f} {circ:.1f}" transform="rotate(-90 {cx} {cy})"/>'
        f'<text x="{cx}" y="{cy+4}" text-anchor="middle" fill="{WHITE}" font-size="24" font-weight="800">{d["total"]}</text>'
        f'<text x="{cx}" y="{cy+22}" text-anchor="middle" fill="{MUTED}" font-size="10">contribuições</text>')
    return frame(495, 200, "".join(inner))


def langs_card(d):
    total = sum(s for s, _ in d["langs"].values()) or 1
    top = sorted(d["langs"].items(), key=lambda kv: -kv[1][0])[:6]
    inner = [web_corner(495),
             f'<text x="25" y="38" fill="{RED}" font-size="18" font-weight="700">Linguagens mais usadas</text>',
             '<clipPath id="bar"><rect x="25" y="58" width="445" height="10" rx="5"/></clipPath>',
             '<g clip-path="url(#bar)">']
    x = 25.0
    for name, (size, color) in top:
        w = 445 * size / total
        inner.append(f'<rect x="{x:.1f}" y="58" width="{w+0.5:.1f}" height="10" fill="{color}"/>')
        x += w
    inner.append(f'<rect x="{x:.1f}" y="58" width="{470-x:.1f}" height="10" fill="{BORDER}"/></g>')
    for i, (name, (size, color)) in enumerate(top):
        cx = 30 + (i % 2) * 225
        cy = 100 + (i // 2) * 30
        inner.append(f'<circle cx="{cx}" cy="{cy-4}" r="5" fill="{color}"/>'
                     f'<text x="{cx+12}" y="{cy}" fill="{TEXT}" font-size="14" font-weight="600">{escape(name)}'
                     f'<tspan fill="{MUTED}" font-weight="400"> {100*size/total:.1f}%</tspan></text>')
    return frame(495, 200, "".join(inner))


def streaks(days):
    today = date.today().isoformat()
    longest = cur = run = 0
    for _, c in days:
        run = run + 1 if c > 0 else 0
        longest = max(longest, run)
    # streak atual: conta de trás pra frente; hoje sem commit ainda não quebra
    seq = list(days)
    if seq and seq[-1][0] == today and seq[-1][1] == 0:
        seq = seq[:-1]
    for _, c in reversed(seq):
        if c > 0:
            cur += 1
        else:
            break
    return cur, longest


def streak_card(d):
    cur, longest = streaks(d["days"])
    import math
    w, h = 990, 170
    inner = [web_corner(w),
             f'<line x1="330" y1="35" x2="330" y2="135" stroke="{BORDER}"/>',
             f'<line x1="660" y1="35" x2="660" y2="135" stroke="{BORDER}"/>']

    def block(cx, big, label, sub, color=WHITE):
        return (f'<text x="{cx}" y="80" text-anchor="middle" fill="{color}" font-size="34" font-weight="800">{big}</text>'
                f'<text x="{cx}" y="112" text-anchor="middle" fill="{TEXT}" font-size="15" font-weight="600">{label}</text>'
                f'<text x="{cx}" y="132" text-anchor="middle" fill="{MUTED}" font-size="12">{sub}</text>')

    inner.append(block(165, d["total"], "Contribuições", "último ano"))
    r = 38
    inner.append(f'<circle cx="495" cy="68" r="{r}" fill="none" stroke="{RED}" stroke-width="5"/>'
                 f'<text x="495" y="80" text-anchor="middle" fill="{WHITE}" font-size="32" font-weight="800">{cur}</text>'
                 f'<text x="495" y="130" text-anchor="middle" fill="{TEXT}" font-size="15" font-weight="600">Sequência atual</text>'
                 f'<text x="495" y="150" text-anchor="middle" fill="{MUTED}" font-size="12">dias seguidos</text>'
                 # aranha pendurada no anel
                 f'<line x1="495" y1="0" x2="495" y2="{68-r}" stroke="{TEXT}" stroke-width="0.8" opacity="0.6"/>')
    inner.append(block(825, longest, "Maior sequência", "último ano", RED))
    return frame(w, h, "".join(inner))


def activity_card(d):
    days = d["days"][-31:]
    w, h = 990, 300
    l, r, t, b = 60, 30, 60, 50
    pw, ph = w - l - r, h - t - b
    mx = max([c for _, c in days] + [4])
    pts = []
    for i, (_, c) in enumerate(days):
        x = l + pw * i / (len(days) - 1)
        y = t + ph - ph * c / mx
        pts.append((x, y))
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"{l},{t+ph} {line} {l+pw},{t+ph}"
    inner = [web_corner(w),
             f'<text x="25" y="38" fill="{RED}" font-size="18" font-weight="700">Atividade nos últimos 31 dias</text>',
             '<defs><linearGradient id="ag" x1="0" y1="0" x2="0" y2="1">'
             f'<stop offset="0" stop-color="{RED}" stop-opacity="0.45"/><stop offset="1" stop-color="{RED}" stop-opacity="0"/>'
             '</linearGradient></defs>']
    for k in range(5):
        y = t + ph * k / 4
        val = round(mx * (4 - k) / 4)
        inner.append(f'<line x1="{l}" y1="{y:.1f}" x2="{l+pw}" y2="{y:.1f}" stroke="{BORDER}" stroke-dasharray="3 4"/>'
                     f'<text x="{l-12}" y="{y+4:.1f}" text-anchor="end" fill="{MUTED}" font-size="11">{val}</text>')
    inner.append(f'<polygon points="{area}" fill="url(#ag)"/>'
                 f'<polyline points="{line}" fill="none" stroke="{RED}" stroke-width="2.5" stroke-linejoin="round"/>')
    for i, ((x, y), (ds, c)) in enumerate(zip(pts, days)):
        inner.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{BG}" stroke="{BLUE}" stroke-width="2"/>')
        if i % 3 == 0 or i == len(days) - 1:
            inner.append(f'<text x="{x:.1f}" y="{t+ph+22}" text-anchor="middle" fill="{MUTED}" font-size="11">{ds[8:10]}/{ds[5:7]}</text>')
    return frame(w, h, "".join(inner))


def main():
    d = demo() if "--demo" in sys.argv else fetch()
    os.makedirs(OUT, exist_ok=True)
    for name, fn in [("stats", stats_card), ("languages", langs_card),
                     ("streak", streak_card), ("activity", activity_card)]:
        with open(os.path.join(OUT, f"{name}.svg"), "w", encoding="utf-8") as f:
            f.write(fn(d))
    print("Cards gerados em assets/")


if __name__ == "__main__":
    main()
