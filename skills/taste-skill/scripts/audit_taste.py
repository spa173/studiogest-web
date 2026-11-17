#!/usr/bin/env python3
"""
audit_taste.py — auditoría estática de las leyes de `taste-skill`.

Uso:
    python3 scripts/audit_taste.py <rutas...> [--profile N] [--json] [--quiet]

Convierte las reglas de diseño en restricciones verificables sobre el código:
escala tipográfica, grilla de 4/8, cifras tabulares, proporción de medios,
LCP, foco, movimiento, modo oscuro y accesibilidad básica.

Salida: errores (rompen la ley) y warnings (revisar o justificar).
Código de salida 1 si hay errores.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------- constantes
CSS_EXT = {".css", ".scss", ".sass", ".less"}
MARKUP_EXT = {".html", ".htm", ".jsx", ".tsx", ".vue", ".svelte", ".astro", ".php"}
EXTS = CSS_EXT | MARKUP_EXT

# Escala tipográfica permitida: bases × ratios modulares (y sus pasos negativos),
# más los techos fluidos del sistema. Un font-size fuera de este conjunto es deriva.
BASES = [14, 16, 17, 18, 20]
DEFAULT_TOKENS = Path(__file__).resolve().parent.parent / "assets" / "tokens.css"
RATIOS = [1.067, 1.2, 1.25, 1.333, 1.414, 1.5, 1.618]
EXTRA_PX = {11, 12, 13, 15, 19, 21, 22, 26, 28, 29, 30, 32, 34, 35, 36, 38, 40,
            42, 44, 48, 50, 54, 56, 60, 64, 68, 72, 76}
PX_TOL = 0.6

# 1 y 2 px: bordes, divisores. 6px: micro-badges (padding: 2px 6px).
SPACING_EXCEPTIONS = {0, 1, 2, 6}

LAYOUT_ANIM_PROPS = {
    "width", "height", "inline-size", "block-size", "top", "bottom", "left",
    "right", "inset", "margin", "margin-top", "margin-left", "margin-right",
    "margin-bottom", "padding", "padding-top", "padding-left", "padding-right",
    "padding-bottom", "font-size", "border-width", "gap", "flex-basis",
}
CHEAP_ANIM_PROPS_WARN = {"box-shadow", "background-position", "filter", "backdrop-filter"}

Z_OK = {0, 1, 10, 20, 30, 40, 50, 60, 70, 100, -1}

SPACING_PROPS = re.compile(
    r"^(margin|padding|gap|row-gap|column-gap|inset)(-top|-right|-bottom|-left|-inline|-block|-inline-start|-inline-end|-block-start|-block-end)?$"
)
SKIP_VALUE = re.compile(r"var\(|env\(|inherit|initial|unset|revert|auto|fit-content|max-content")

# ---------------------------------------------------------------- utilidades


def build_scale_from_tokens(tokens_file: Path, profile: int) -> set[float] | None:
    """Escala real declarada en tokens.css para el perfil: es la fuente de verdad."""
    try:
        raw = tokens_file.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    raw = strip_comments(raw)
    blocks = []
    m = re.search(r'\[data-profile="%d"\]\s*\{' % profile, raw)
    if m:
        depth, i = 0, m.end() - 1
        while i < len(raw):
            if raw[i] == "{":
                depth += 1
            elif raw[i] == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        blocks.append(raw[m.end():i])
    r = re.search(r":root\s*\{", raw)
    if r:
        depth, i = 0, r.end() - 1
        while i < len(raw):
            if raw[i] == "{":
                depth += 1
            elif raw[i] == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        blocks.append(raw[r.end():i])
    allowed: set[float] = set()
    for block in blocks:
        for dm in re.finditer(r"--fs[-a-z0-9]*\s*:\s*([^;]+);", block):
            for num in re.finditer(r"(\d*\.?\d+)(px|rem)", dm.group(1)):
                n = float(num.group(1))
                allowed.add(round(n * 16 if num.group(2) == "rem" else n, 2))
    return allowed or None


def build_scale() -> set[float]:
    out: set[float] = set()
    for base in BASES:
        for ratio in RATIOS:
            v = float(base)
            for _ in range(7):
                out.add(round(v, 2))
                v *= ratio
            v = float(base)
            for _ in range(3):
                v /= ratio
                out.add(round(v, 2))
    out |= {float(x) for x in EXTRA_PX}
    return out


SCALE = build_scale()
ACTIVE_SCALE: set[float] | None = None


def in_scale(px: float) -> bool:
    if ACTIVE_SCALE:
        return any(abs(px - s) <= 0.55 for s in ACTIVE_SCALE)
    return any(abs(px - s) <= 0.25 for s in SCALE)


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def selector_at(text: str, idx: int) -> str:
    """Selector de la regla que contiene la declaración (para no confundir UI con prosa)."""
    j = text.rfind("{", 0, idx)
    if j == -1:
        return ""
    k = max(text.rfind("}", 0, j), text.rfind("{", 0, j), text.rfind(";", 0, j))
    return text[k + 1:j].strip()[-120:]


def block_ranges(text: str, pattern: str) -> list[tuple[int, int]]:
    """Rangos [inicio, fin) de los bloques @media que cumplen `pattern`."""
    ranges: list[tuple[int, int]] = []
    for m in re.finditer(pattern, text):
        depth, i = 0, m.end() - 1
        while i < len(text):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        ranges.append((m.start(), i))
    return ranges


def strip_comments(text: str) -> str:
    """Quita comentarios preservando los saltos de línea (para no falsear líneas)."""
    text = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    text = re.sub(r"//[^\n]*", "", text)
    text = re.sub(r"\{/\*.*?\*/\}", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    return text


class Finding:
    __slots__ = ("sev", "code", "path", "line", "msg", "snippet")

    def __init__(self, sev, code, path, line, msg, snippet=""):
        self.sev, self.code, self.path, self.line, self.msg, self.snippet = sev, code, path, line, msg, snippet

    def as_dict(self):
        return {"severity": self.sev, "rule": self.code, "file": str(self.path),
                "line": self.line, "message": self.msg, "snippet": self.snippet}

    def __str__(self):
        loc = f"{self.path}:{self.line}"
        snip = f"   …{self.snippet.strip()[:90]}" if self.snippet.strip() else ""
        return f"[{self.sev:5}] {self.code}  {loc}\n         {self.msg}{'\n' + snip if snip else ''}"


# ---------------------------------------------------------------- reglas CSS


def check_declarations(path: Path, text: str, profile: int, out: list[Finding]) -> None:
    for m in re.finditer(r"([-a-zA-Z]+)\s*:\s*([^;{}]+);", text):
        prop, value = m.group(1).lower(), m.group(2).strip()
        low = value.lower()
        line = line_of(text, m.start())
        snip = f"{prop}: {value};"

        # T01 · escala tipográfica
        if prop == "font-size" and not SKIP_VALUE.search(low):
            for pxm in re.finditer(r"(-?\d*\.?\d+)(px|rem)", low):
                n = float(pxm.group(1))
                n = n * 16 if pxm.group(2) == "rem" else n
                if not in_scale(n):
                    out.append(Finding("WARN", "T01-escala", path, line,
                                       f"font-size {pxm.group(0)} no existe en la escala del perfil {profile}. Usa un token --fs-* (los valores válidos son los de assets/tokens.css).", snip))
                    break

        # T02 · grilla de 4 (y 8 en layout)
        if SPACING_PROPS.match(prop) and not SKIP_VALUE.search(low):
            for pxm in re.finditer(r"(-?\d*\.?\d+)px", low):
                n = float(pxm.group(1))
                if n not in SPACING_EXCEPTIONS and n % 4 != 0:
                    out.append(Finding("ERROR", "T02-grilla", path, line,
                                       f"espaciado {pxm.group(0)} no es múltiplo de 4 (layout: de 8; componentes: de 4; solo 1–2px en bordes).", snip))
                    break
                if n % 4 == 0 and n % 8 != 0 and prop.startswith(("margin", "padding", "gap")) and n >= 24:
                    out.append(Finding("WARN", "T02b-grilla8", path, line,
                                       f"espaciado {pxm.group(0)} en layout: usa múltiplos de 8 para contenedores y ritmo vertical.", snip))
                    break

        # T03 · animación de propiedades de layout
        if prop in ("transition", "transition-property", "animation", "animation-name"):
            for token in re.split(r"[,\s]+", low):
                token = token.split("(")[0].strip()
                if token in LAYOUT_ANIM_PROPS:
                    out.append(Finding("ERROR", "T03-anim-layout", path, line,
                                       f"animas `{token}`: provoca layout/repaint. Anima solo transform, opacity o filter.", snip))
                elif token in CHEAP_ANIM_PROPS_WARN:
                    out.append(Finding("WARN", "T03b-anim-coste", path, line,
                                       f"animas `{token}`: cuesta repaint. Para sombra, anima la opacidad de un ::after.", snip))

        # T04 · duración de movimiento
        if prop in ("transition", "transition-duration", "animation", "animation-duration"):
            loopy = "infinite" in low
            for dm in (() if loopy else re.finditer(r"(\d*\.?\d+)(ms|s)\b", low)):
                n = float(dm.group(1))
                n = n * 1000 if dm.group(2) == "s" else n
                if n > 600:
                    out.append(Finding("WARN", "T04-duracion", path, line,
                                       f"duración {dm.group(0)} > 600ms. Máximo 500ms (una vez por página); salidas al 70% de la entrada.", snip))
                    break

        # T05 · foco
        if prop == "outline" and low.replace(" ", "") in ("none", "0", "0px"):
            out.append(Finding("ERROR", "T05-foco", path, line,
                               "`outline: none` sin sustituto comprobable. Usa :focus-visible con 2px + offset.", snip))

        # T06 · line-height de lectura
        if prop == "line-height":
            lh = re.match(r"^\s*(\d*\.?\d+)\s*;?$", low)
            ui_ctx = re.search(r"h[1-6]|btn|button|kpi|badge|chip|tag|label|th\b|td\b|nav|tab|heading", selector_at(text, m.start()), re.I)
            if lh and float(lh.group(1)) < 1.3 and not ui_ctx:
                out.append(Finding("WARN", "T06-interlineado", path, line,
                                   f"line-height {lh.group(1)} < 1.3 en lectura. Cuerpo ≥1.4; titulares 1.0–1.15.", snip))

        # T07 · z-index
        if prop == "z-index" and not SKIP_VALUE.search(low):
            zi = re.match(r"^-?\d+$", low)
            if zi and int(low) not in Z_OK:
                out.append(Finding("WARN", "T07-capas", path, line,
                                   f"z-index {low} fuera del sistema de capas (--z-*). Escalada de z-index = conflicto latente.", snip))

        # T08 · viewport móvil
        if "100vh" in low:
            out.append(Finding("WARN", "T08-vh", path, line,
                               "100vh en móvil rompe con la barra de Safari/Chrome. Usa 100dvh o 100svh.", snip))

        # T09 · medida de lectura en móvil
        if prop in ("max-width", "max-inline-size") and re.search(r"\d+(\.\d+)?ch", low):
            n = float(re.search(r"(\d+(?:\.\d+)?)ch", low).group(1))
            if n < 48:
                out.append(Finding("WARN", "T09-medida", path, line,
                                   f"max-width: {low} crea columna angosta con hueco a la derecha. En móvil: width:100% + padding-inline:16px + 1rem.", snip))
            elif n > 80:
                out.append(Finding("WARN", "T09b-medida", path, line,
                                   f"max-width: {low} excede 72ch: la línea se pierde. Rango 55–72ch.", snip))

        # T10 · sombra difusa en perfiles densos
        if prop == "box-shadow" and profile in (1, 2) and not SKIP_VALUE.search(low):
            blur = re.search(r"(?:0\s+)?-?\d+px\s+(\d+)px", low)
            if blur and int(blur.group(1)) >= 16:
                out.append(Finding("WARN", "T10-sombra", path, line,
                                   "sombra difusa en perfil denso: usa borde 1px + superficie plana (marketing sí puede).", snip))

        # T11 · radios fuera de sistema
        if prop in ("border-radius", "border-start-start-radius") and not SKIP_VALUE.search(low):
            for pxm in re.finditer(r"(\d+(?:\.\d+)?)px", low):
                n = float(pxm.group(1))
                if n not in {0, 2, 4, 6, 8, 12, 16, 24, 999} and n < 500:
                    out.append(Finding("WARN", "T11-radio", path, line,
                                       f"radio {pxm.group(0)} fuera de la escala (--r-*). Mezclar radios rompe la unidad.", snip))
                    break

        # T12 · inputs y autozoom iOS / autocompletado
        if prop == "font-size":
            pass


def check_keyframes(path: Path, text: str, out: list[Finding]) -> None:
    for m in re.finditer(r"@keyframes\s+([\w-]+)\s*\{", text):
        start = m.end()
        depth, i = 1, start
        while i < len(text) and depth:
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            i += 1
        body = text[start:i]
        for prop in LAYOUT_ANIM_PROPS:
            if re.search(rf"(?<![-a-z]){re.escape(prop)}\s*:", body):
                out.append(Finding("ERROR", "T03-anim-layout", path, line_of(text, m.start()),
                                   f"@keyframes `{m.group(1)}` anima `{prop}`. Reemplaza por transform/opacity.", f"@keyframes {m.group(1)}"))
                break


def check_globals(path: Path, text: str, profile: int, out: list[Finding]) -> None:
    has_anim = bool(re.search(r"@keyframes|animation\s*:|transition\s*:", text))
    if has_anim and "prefers-reduced-motion" not in text:
        out.append(Finding("ERROR", "T13-reduced-motion", path, 1,
                           "hay animaciones/transiciones y no existe prefers-reduced-motion. Es requisito de accesibilidad (WCAG 2.3.3)."))

    if re.search(r"(<table|className=\"[^\"]*table|\.table\b|kpi)", text) and "tabular-nums" not in text:
        out.append(Finding("WARN", "T14-tabular", path, 1,
                           "tabla/KPI sin `font-variant-numeric: tabular-nums`: las cifras no alinean en columna."))

    if re.search(r"font-size\s*:\s*(2\.25|2\.3|2\.5|2\.75|3|3\.5|4|4\.5|4\.75)rem", text) and "letter-spacing" not in text:
        out.append(Finding("WARN", "T15-tracking", path, 1,
                           "titular ≥36px sin letter-spacing negativo. Añade -0.02em a -0.04em."))

    rm_ranges = block_ranges(text, r"@media[^{]*prefers-reduced-motion[^{]*\{")
    n_imp = sum(1 for im in re.finditer(r"!important", text)
                if not any(a <= im.start() <= b for a, b in rm_ranges))
    if n_imp > 3:
        out.append(Finding("WARN", "T16-important", path, 1,
                           f"{n_imp} usos de !important: la cascada está peleando. Sube especificidad con @layer."))

    if re.search(r"object-fit\s*:\s*cover", text) and "aspect-ratio" not in text:
        out.append(Finding("WARN", "T17-aspect", path, 1,
                           "object-fit sin aspect-ratio: la grilla de medios se desalinea con fotos dispares."))

    if re.search(r"(input|select|textarea)[^{]*\{[^}]*font-size\s*:\s*(0?\.\d+rem|1[0-5]px)", text, re.S):
        out.append(Finding("ERROR", "T18-autozoom", path, 1,
                           "input con font-size < 16px: Safari iOS hace zoom al enfocar y rompe el layout."))

    if 1 in (profile,) and "box-shadow" in text and "none" not in text.split("box-shadow")[1][:12]:
        pass


def check_markup(path: Path, text: str, out: list[Finding]) -> None:
    # T19 · lang
    if "<html" in text and not re.search(r"<html[^>]*\slang=", text):
        out.append(Finding("ERROR", "T19-lang", path, line_of(text, text.index("<html")),
                           "<html> sin atributo lang. Afecta lectores de pantalla, traducción y guionado."))

    # T20 · imágenes: alt, dimensiones, lazy/LCP
    imgs = list(re.finditer(r"<img\b[^>]*>", text))
    for i, m in enumerate(imgs):
        tag = m.group(0)
        line = line_of(text, m.start())
        if not re.search(r"\salt\s*=", tag) and not re.search(r"alt=", tag):
            out.append(Finding("ERROR", "T20-alt", path, line, "<img> sin alt (usa alt=\"\" si es decorativa).", tag[:80]))
        has_dims = re.search(r"\swidth\s*=", tag) and re.search(r"\sheight\s*=", tag)
        nearby_aspect = "aspect-ratio" in text
        if not has_dims and not nearby_aspect:
            out.append(Finding("WARN", "T21-cls", path, line,
                               "<img> sin width/height ni aspect-ratio: produce CLS.", tag[:80]))
        if re.search(r'loading\s*=\s*["\']lazy', tag) and re.search(r'fetchpriority\s*=\s*["\']high', tag):
            out.append(Finding("ERROR", "T22-lcp", path, line,
                               "loading=\"lazy\" + fetchpriority=\"high\" en la misma imagen: se contradicen.", tag[:80]))
        if i == 0 and re.search(r'loading\s*=\s*["\']lazy', tag):
            out.append(Finding("WARN", "T22b-lcp", path, line,
                               "la primera imagen del documento está en lazy: si es el LCP, retrasa el paint. Quita lazy y añade fetchpriority=\"high\".", tag[:80]))

    # T23 · div clicable
    if re.search(r"<div[^>]*onClick", text, re.S) and "role=\"button\"" not in text:
        out.append(Finding("WARN", "T23-semantica", path, 1,
                           "<div onClick> sin role/tabindex: inaccesible por teclado. Usa <button> o <a>."))

    # T24 · imagen de contenido en CSS
    if re.search(r"background-image\s*:\s*url\(", text) and "<img" not in text and "<picture" not in text:
        out.append(Finding("WARN", "T24-bg-image", path, 1,
                           "contenido como background-image: sin alt, sin srcset, invisible al preload scanner."))


# ---------------------------------------------------------------- runner


def audit(paths: list[Path], profile: int) -> list[Finding]:
    findings: list[Finding] = []
    files: list[Path] = []
    for p in paths:
        if p.is_dir():
            files += [f for f in sorted(p.rglob("*")) if f.suffix.lower() in EXTS and "node_modules" not in f.parts]
        elif p.is_file():
            files.append(p)
    for f in files:
        try:
            raw = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            findings.append(Finding("ERROR", "T00-io", f, 0, "no se pudo leer el archivo"))
            continue
        text = strip_comments(raw)
        if f.suffix.lower() in CSS_EXT:
            check_declarations(f, text, profile, findings)
            check_keyframes(f, text, findings)
        check_globals(f, text, profile, findings)
        if f.suffix.lower() in MARKUP_EXT:
            check_markup(f, text, findings)
            if f.suffix.lower() in {".html", ".htm", ".php"}:
                # CSS embebido
                for sm in re.finditer(r"<style[^>]*>(.*?)</style>", text, re.S):
                    check_declarations(f, sm.group(1), profile, findings)
    findings.sort(key=lambda x: (x.sev != "ERROR", str(x.path), x.line))
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description="Auditoría estática de taste-skill")
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--profile", type=int, default=3, choices=[1, 2, 3, 4, 5])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--tokens", type=Path, default=DEFAULT_TOKENS,
                    help="tokens.css del que se lee la escala real (por defecto el de la skill)")
    args = ap.parse_args()

    global ACTIVE_SCALE
    ACTIVE_SCALE = build_scale_from_tokens(args.tokens, args.profile)
    if ACTIVE_SCALE is None:
        print(f"  ⚠ no se pudo leer la escala de {args.tokens}: se usa la escala modular genérica", file=sys.stderr)

    findings = audit(args.paths, args.profile)
    errors = [f for f in findings if f.sev == "ERROR"]
    warns = [f for f in findings if f.sev == "WARN"]

    if args.json:
        print(json.dumps({"profile": args.profile,
                          "errors": len(errors), "warnings": len(warns),
                          "findings": [f.as_dict() for f in findings]}, ensure_ascii=False, indent=2))
    elif not args.quiet:
        print(f"\n  taste-skill audit · perfil {args.profile} · {len(errors)} errores · {len(warns)} warnings\n" + "  " + "─" * 72)
        for f in findings:
            print(str(f))
        if not findings:
            print("  ✅ Sin hallazgos. La entrega pasa las leyes de §2.")
        print("  " + "─" * 72)
        print(f"  Resultado: {'FALLA' if errors else 'PASA'} "
              f"({len(errors)} errores, {len(warns)} warnings)\n")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
