"""Gera os SVGs animados fixos do perfil (topo, barras de seção e rodapé) no tema aranha.

Não depende da API do GitHub: rode uma vez quando quiser mudar textos.
Uso: python scripts/generate_animated.py
"""
import base64
import io
import os
from xml.sax.saxutils import escape

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(ROOT, "assets")

BG = "#0B1426"
BORDER = "#22304F"
RED = "#E62429"
BLUE = "#3B6BF0"
TEXT = "#C9D6FF"
MUTED = "#7F8BB0"
MONO = "'JetBrains Mono','Fira Code',Consolas,'Courier New',monospace"
SANS = "'Segoe UI',Ubuntu,'Helvetica Neue',Arial,sans-serif"
CHAR_W = 0.6  # largura média de um caractere monoespaçado, em "em"

SPIDER = """<g fill="{c}">
  <ellipse cx="0" cy="6" rx="7" ry="9"/><circle cx="0" cy="-5" r="5"/>
  <g stroke="{c}" stroke-width="2" fill="none" stroke-linecap="round">
    <path d="M-5 0 L-14 -8 L-18 -2"/><path d="M-6 4 L-17 2 L-21 9"/><path d="M-6 9 L-16 13 L-18 21"/><path d="M-4 13 L-11 21 L-11 28"/>
    <path d="M5 0 L14 -8 L18 -2"/><path d="M6 4 L17 2 L21 9"/><path d="M6 9 L16 13 L18 21"/><path d="M4 13 L11 21 L11 28"/>
  </g>
  <circle cx="-2" cy="-6" r="1.3" fill="#fff"/><circle cx="2" cy="-6" r="1.3" fill="#fff"/>
</g>"""


def spider(color=RED, scale=1.0):
    return f'<g transform="scale({scale})">{SPIDER.format(c=color)}</g>'


def web(cx, cy, r, rings=5, spokes=10, color=TEXT, opacity=0.35, cls="draw"):
    """Teia radial desenhada com animação de traço."""
    import math
    parts = []
    for i in range(spokes):
        a = 2 * math.pi * i / spokes
        parts.append(f'<line x1="{cx}" y1="{cy}" x2="{cx + r * math.cos(a):.1f}" y2="{cy + r * math.sin(a):.1f}"/>')
    for k in range(1, rings + 1):
        rr = r * k / rings
        pts = " ".join(f"{cx + rr * math.cos(2 * math.pi * i / spokes):.1f},{cy + rr * math.sin(2 * math.pi * i / spokes):.1f}" for i in range(spokes))
        parts.append(f'<polygon points="{pts}"/>')
    return f'<g class="{cls}" fill="none" stroke="{color}" stroke-opacity="{opacity}" stroke-width="1.2" pathLength="1">{"".join(parts)}</g>'


def banner_data_uri(width=1000, height=330):
    from PIL import Image
    im = Image.open(os.path.join(OUT, "banner.jpg")).convert("RGB")
    scale = max(width / im.width, height / im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    left, top = (im.width - width) // 2, (im.height - height) // 2
    im = im.crop((left, top, left + width, top + height))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=72, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def typed(text, x, y, size, color, begin, dur, font=MONO, weight="400", ident="t"):
    """Texto que aparece letra a letra (máscara que cresce em degraus)."""
    width = len(text) * size * CHAR_W + 4
    steps = max(len(text), 1)
    return (f'<clipPath id="{ident}"><rect x="{x}" y="{y - size}" width="0" height="{size * 1.5}">'
            f'<animate attributeName="width" from="0" to="{width:.0f}" begin="{begin}s" dur="{dur}s" calcMode="discrete" '
            f'values="{";".join(f"{width * i / steps:.0f}" for i in range(steps + 1))}" fill="freeze"/></rect></clipPath>'
            f'<text x="{x}" y="{y}" font-family="{font}" font-size="{size}" font-weight="{weight}" fill="{color}" clip-path="url(#{ident})">{escape(text)}</text>')


# ---------------------------------------------------------------- topo
def header():
    W, H = 1000, 330
    roles = ["Software Developer", "Java  |  Python  |  React  |  Oracle", "Estudante de ADS na FIAP"]
    cycle = 12  # segundos para mostrar os 3 subtítulos
    role_svg = []
    for i, role in enumerate(roles):
        s, e = i / len(roles), (i + 1) / len(roles)
        if i == 0:
            kt, vals = f"0;{e - 0.02:.3f};{e:.3f};0.98;1", "1;1;0;0;1"
        elif e >= 1:
            kt, vals = f"0;{s:.3f};{s + 0.02:.3f};0.98;1", "0;0;1;1;0"
        else:
            kt, vals = f"0;{s:.3f};{s + 0.02:.3f};{e - 0.02:.3f};{e:.3f};1", "0;0;1;1;0;0"
        role_svg.append(f'<text x="64" y="232" font-family="{MONO}" font-size="21" fill="{TEXT}" opacity="{1 if i == 0 else 0}">'
                        f'<tspan fill="{RED}">&gt;</tspan> {escape(role)}'
                        f'<animate attributeName="opacity" dur="{cycle}s" begin="3.6s" repeatCount="indefinite" keyTimes="{kt}" values="{vals}"/></text>')

    lights = "".join(
        f'<circle cx="{x}" cy="{y}" r="1.6" fill="#ffd27a"><animate attributeName="opacity" values="0.2;1;0.2" dur="{d}s" begin="{b}s" repeatCount="indefinite"/></circle>'
        for x, y, d, b in [(560, 300, 3.1, 0), (610, 288, 4.3, 1), (655, 305, 2.7, 0.5), (720, 296, 3.7, 2), (782, 310, 4.9, 1.4), (845, 292, 3.3, 0.8), (905, 306, 2.9, 2.2)])

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<style>
.draw *{{stroke-dasharray:1;stroke-dashoffset:1;animation:draw 3.5s ease-out forwards}}
@keyframes draw{{to{{stroke-dashoffset:0}}}}
.blink{{animation:blink 1s steps(1) infinite}} @keyframes blink{{50%{{opacity:0}}}}
.drop{{animation:drop 5s ease-in-out infinite}} @keyframes drop{{0%,100%{{transform:translate(905px,96px)}}50%{{transform:translate(905px,150px)}}}}
.thread{{animation:thread 5s ease-in-out infinite}} @keyframes thread{{0%,100%{{transform:scaleY(1)}}50%{{transform:scaleY(1.6)}}}}
.glow{{animation:glow 3s ease-in-out infinite}} @keyframes glow{{50%{{opacity:.55}}}}
.line{{transform-origin:left;transform:scaleX(0);animation:grow 1.4s ease-out 2.8s forwards}} @keyframes grow{{to{{transform:scaleX(1)}}}}
</style>
<defs>
  <linearGradient id="shade" x1="0" x2="1"><stop offset="0" stop-color="{BG}" stop-opacity=".96"/><stop offset=".55" stop-color="{BG}" stop-opacity=".78"/><stop offset="1" stop-color="{BG}" stop-opacity=".25"/></linearGradient>
  <linearGradient id="bottom" x1="0" y1="0" x2="0" y2="1"><stop offset=".6" stop-color="{BG}" stop-opacity="0"/><stop offset="1" stop-color="{BG}" stop-opacity=".9"/></linearGradient>
  <clipPath id="card"><rect width="{W}" height="{H}" rx="14"/></clipPath>
</defs>
<g clip-path="url(#card)">
  <image href="{banner_data_uri(W, H)}" width="{W}" height="{H}" preserveAspectRatio="xMidYMid slice"/>
  <rect width="{W}" height="{H}" fill="url(#shade)"/><rect width="{W}" height="{H}" fill="url(#bottom)"/>
  {lights}
  {web(1000, 0, 190, rings=6, spokes=12, opacity=0.4)}
  <g transform-origin="905px 0px" class="thread"><line x1="905" y1="0" x2="905" y2="96" stroke="{TEXT}" stroke-opacity=".7" stroke-width="1.2"/></g>
  <g class="drop">{spider(RED, 1.6)}</g>

  <rect x="0" y="0" width="{W}" height="38" fill="{BG}" fill-opacity=".85"/>
  <circle cx="26" cy="19" r="6" fill="{RED}"/><circle cx="46" cy="19" r="6" fill="{BLUE}"/><circle cx="66" cy="19" r="6" fill="{TEXT}" fill-opacity=".6"/>
  <text x="{W / 2}" y="24" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{MUTED}">josue@fiap: ~/teia</text>
  <text x="{W - 24}" y="24" text-anchor="end" font-family="{MONO}" font-size="13" fill="{RED}"><tspan class="glow">●</tspan> online</text>

  <text x="64" y="104" font-family="{MONO}" font-size="15" fill="{MUTED}">$ whoami</text>
  {typed("Josué Menezes", 64, 170, 54, "#FFFFFF", 0.6, 1.8, font=SANS, weight="800", ident="nome")}
  <rect x="64" y="186" width="380" height="4" rx="2" fill="{RED}" class="line"/>
  <g>{''.join(role_svg)}</g>
  <rect x="64" y="246" width="12" height="3" fill="{RED}" class="blink"/>
  <text x="64" y="292" font-family="{MONO}" font-size="13" fill="{MUTED}">São Paulo · BR  ·  <tspan fill="{RED}">🕸</tspan> construindo uma teia de projetos</text>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="{BORDER}"/>
</svg>"""


# ---------------------------------------------------------------- barras de seção
def section(command, ident):
    W, H = 1000, 58
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<style>
.blink{{animation:blink 1s steps(1) infinite}} @keyframes blink{{50%{{opacity:0}}}}
.scan{{animation:scan 6s linear infinite}} @keyframes scan{{from{{transform:translateX(-300px)}}to{{transform:translateX(1100px)}}}}
.ok{{opacity:0;animation:ok .6s ease-out 1.6s forwards}} @keyframes ok{{to{{opacity:1}}}}
.swing{{transform-origin:46px 0;animation:swing 3s ease-in-out infinite}} @keyframes swing{{0%,100%{{transform:rotate(-8deg)}}50%{{transform:rotate(8deg)}}}}
</style>
<defs>
  <linearGradient id="bg{ident}" x1="0" x2="1"><stop offset="0" stop-color="#13213F"/><stop offset="1" stop-color="{BG}"/></linearGradient>
  <linearGradient id="sweep{ident}" x1="0" x2="1"><stop offset="0" stop-color="{RED}" stop-opacity="0"/><stop offset=".5" stop-color="{RED}" stop-opacity=".18"/><stop offset="1" stop-color="{RED}" stop-opacity="0"/></linearGradient>
  <clipPath id="c{ident}"><rect width="{W}" height="{H}" rx="10"/></clipPath>
</defs>
<g clip-path="url(#c{ident})">
  <rect width="{W}" height="{H}" fill="url(#bg{ident})"/>
  <rect class="scan" width="260" height="{H}" fill="url(#sweep{ident})"/>
  <rect width="5" height="{H}" fill="{RED}"/>
  <g class="swing"><line x1="46" y1="0" x2="46" y2="20" stroke="{TEXT}" stroke-opacity=".6"/><g transform="translate(46 28)">{spider(RED, 0.75)}</g></g>
  <text x="78" y="36" font-family="{MONO}" font-size="20" font-weight="700" fill="{RED}">&gt;</text>
  {typed(command, 100, 36, 20, "#FFFFFF", 0.2, 1.2, weight="700", ident=f"cmd{ident}")}
  <rect x="{100 + len(command) * 20 * CHAR_W + 8:.0f}" y="22" width="11" height="18" fill="{RED}" class="blink"/>
  <text x="{W - 24}" y="34" text-anchor="end" font-family="{MONO}" font-size="14" fill="{BLUE}" class="ok">[ ok ]</text>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="none" stroke="{BORDER}"/>
</svg>"""


# ---------------------------------------------------------------- rodapé
def footer():
    W, H = 1000, 150

    def wave(y, amp, color, op, dur, rev=False):
        d = f"M0 {y} " + " ".join(f"Q{x + 62.5} {y - amp} {x + 125} {y} T{x + 250} {y}" for x in range(0, 2000, 250)) + f" V{H} H0 Z"
        frm, to = ("-1000", "0") if rev else ("0", "-1000")
        return (f'<path d="{d}" fill="{color}" fill-opacity="{op}">'
                f'<animateTransform attributeName="transform" type="translate" from="{frm} 0" to="{to} 0" dur="{dur}s" repeatCount="indefinite"/></path>')

    skyline = "M0 150 V112 H40 V96 H70 V118 H110 V84 H150 V108 H190 V70 H210 V60 H230 V70 H250 V104 H300 V90 H340 V114 H390 V78 H430 V100 H480 V88 H520 V116 H560 V74 H600 V102 H650 V92 H690 V112 H740 V80 H780 V106 H830 V94 H870 V118 H920 V86 H960 V108 H1000 V150 Z"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<style>
.swing{{transform-origin:500px 0;animation:swing 4s ease-in-out infinite}} @keyframes swing{{0%,100%{{transform:rotate(-14deg)}}50%{{transform:rotate(14deg)}}}}
.fade{{animation:fade 4s ease-in-out infinite}} @keyframes fade{{50%{{opacity:.5}}}}
</style>
<defs><clipPath id="f"><rect width="{W}" height="{H}" rx="14"/></clipPath></defs>
<g clip-path="url(#f)">
  <rect width="{W}" height="{H}" fill="{BG}"/>
  {wave(92, 18, BLUE, .25, 14)}
  {wave(104, 14, RED, .3, 10, rev=True)}
  <path d="{skyline}" fill="#060B17"/>
  <g class="swing"><line x1="500" y1="0" x2="500" y2="58" stroke="{TEXT}" stroke-opacity=".7"/><g transform="translate(500 66)">{spider(RED, 1.2)}</g></g>
  <text x="{W / 2}" y="128" text-anchor="middle" font-family="{MONO}" font-size="15" fill="{TEXT}" class="fade">obrigado pela visita · volte sempre pra ver a teia crescer</text>
</g>
</svg>"""


def main():
    files = {
        "header.svg": header(),
        "sec-sobre.svg": section("cat sobre_mim.txt", "a"),
        "sec-tech.svg": section("ls ./tecnologias", "b"),
        "sec-stats.svg": section("git log --stats", "c"),
        "sec-atividade.svg": section("tail -f atividade.log", "d"),
        "sec-projetos.svg": section("ls ./projetos", "e"),
        "footer.svg": footer(),
    }
    for name, svg in files.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"ok {name} ({len(svg) // 1024} KB)")


if __name__ == "__main__":
    main()
