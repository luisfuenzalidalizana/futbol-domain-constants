#!/usr/bin/env python3
"""
Generador de constantes multi-lenguaje — versión standalone para usarse
como git submodule desde cualquier repo consumidor.

Uso típico (ejecutado DESDE la raíz del repo que lo consume, con el
submódulo montado en vendor/domain-constants):

    # Backend FastAPI
    python3 vendor/domain-constants/generate_constants.py \\
        --json vendor/domain-constants/domain_constants.json \\
        --python-out app/core/constants.py

    # Backend Node
    python3 vendor/domain-constants/generate_constants.py \\
        --json vendor/domain-constants/domain_constants.json \\
        --ts-out constants/index.ts

    # Ambos a la vez (si algún día conviven en el mismo repo)
    python3 vendor/domain-constants/generate_constants.py \\
        --json vendor/domain-constants/domain_constants.json \\
        --python-out app/core/constants.py \\
        --ts-out constants/index.ts

Regla de oro: domain_constants.json es la ÚNICA fuente editable a mano
en TODO el sistema. Los .py / .ts que este script genera llevan un
header "AUTO-GENERADO" y nunca se editan directamente.

Regla de oro de dominio: estos códigos quedan persistidos en PostgreSQL
(Match.status, TeamFormation.position, Player.status, etc.).
Nunca reutilices ni renumeres un código existente; solo se agrega al final.
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_JSON = HERE / "domain_constants.json"

NUMERIC_GROUPS = [
    ("matchPeriods", "MatchPeriod"),
    ("matchEvents", "MatchEvent"),
    ("matchStatus", "MatchStatus"),
    ("tacticalFormations", "TacticalFormation"),
    ("playerPositions", "PlayerPosition"),
    ("playerStatus", "PlayerStatus"),
]


def sanitize(raw: str) -> str:
    name = re.sub(r"[^0-9A-Za-z]+", "_", raw.strip()).strip("_").upper()
    if not name:
        name = "UNKNOWN"
    if name[0].isdigit():
        name = f"F_{name}"
    return name


def labels_const_name(enum_name: str) -> str:
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", enum_name).upper()
    return f"{snake}_LABELS"


def load_source(path: Path) -> dict:
    if not path.exists():
        sys.exit(f"No se encontró el JSON fuente: {path}")
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def build_numeric_group(data: dict, key: str):
    items, seen = [], set()
    for str_code, label in data[key].items():
        code = int(str_code)
        base = sanitize(label)
        name = base
        i = 2
        while name in seen:
            name = f"{base}_{i}"
            i += 1
        seen.add(name)
        items.append((name, code, label))
    items.sort(key=lambda t: t[1])
    return items


def build_season_types(data: dict):
    items = [
        (payload["code"], int(str_code), payload["label"])
        for str_code, payload in data["seasonTypes"].items()
    ]
    items.sort(key=lambda t: t[1])
    return items


def build_ui_colors(data: dict):
    return list(data["uiColors"].items())


def render_python(data: dict, source_label: str) -> str:
    now = datetime.now(timezone.utc).isoformat()
    lines = [
        '"""', "AUTO-GENERADO — NO EDITAR A MANO.",
        f"Fuente: {source_label}", f"Generado: {now}",
        "Para actualizar: editar domain_constants.json en el repo",
        "futbol-domain-constants y correr generate_constants.py",
        '"""',
        "from enum import Enum, IntEnum",
        "from typing import Dict, TypedDict",
        "", "",
    ]
    for json_key, enum_name in NUMERIC_GROUPS:
        items = build_numeric_group(data, json_key)
        lines.append(f"class {enum_name}(IntEnum):")
        for name, code, _label in items:
            lines.append(f"    {name} = {code}")
        lines.append("")
        labels_name = labels_const_name(enum_name)
        lines.append(f"{labels_name}: Dict[int, str] = {{")
        for _name, code, label in items:
            lines.append(f"    {code}: {label!r},")
        lines.append("}")
        lines.append("")
        lines.append("")

    season_items = build_season_types(data)
    lines.append("class SeasonType(IntEnum):")
    for name, code, _label in season_items:
        lines.append(f"    {name} = {code}")
    lines.append("")
    lines.append("SEASON_TYPE_LABELS: Dict[int, str] = {")
    for _name, code, label in season_items:
        lines.append(f"    {code}: {label!r},")
    lines.append("}")
    lines.append("")
    lines.append("")

    ui_colors = build_ui_colors(data)
    lines.append("class MatchColor(str, Enum):")
    for key, _meta in ui_colors:
        lines.append(f"    {key.upper()} = {key!r}")
    lines.append("")
    lines.append("")
    lines.append("class UIColorMeta(TypedDict):")
    lines.append("    text: str")
    lines.append("    bg: str")
    lines.append("    label: str")
    lines.append("")
    lines.append("")
    lines.append("MATCH_COLOR_UI: Dict[str, UIColorMeta] = {")
    for key, meta in ui_colors:
        lines.append(
            "    %r: {'text': %r, 'bg': %r, 'label': %r},"
            % (key, meta["text"], meta["bg"], meta["label"])
        )
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def render_typescript(data: dict, source_label: str) -> str:
    now = datetime.now(timezone.utc).isoformat()
    lines = [
        "/**", " * AUTO-GENERADO — NO EDITAR A MANO.",
        f" * Fuente: {source_label}", f" * Generado: {now}",
        " * Para actualizar: editar domain_constants.json en el repo",
        " * futbol-domain-constants y correr generate_constants.py",
        " */", "",
    ]
    for json_key, enum_name in NUMERIC_GROUPS:
        items = build_numeric_group(data, json_key)
        lines.append(f"export enum {enum_name} {{")
        for name, code, _label in items:
            lines.append(f"  {name} = {code},")
        lines.append("}")
        lines.append("")
        labels_name = labels_const_name(enum_name)
        lines.append(f"export const {labels_name}: Record<number, string> = {{")
        for _name, code, label in items:
            lines.append(f"  {code}: {json.dumps(label, ensure_ascii=False)},")
        lines.append("};")
        lines.append("")

    season_items = build_season_types(data)
    lines.append("export enum SeasonType {")
    for name, code, _label in season_items:
        lines.append(f"  {name} = {code},")
    lines.append("}")
    lines.append("")
    lines.append("export const SEASON_TYPE_LABELS: Record<number, string> = {")
    for _name, code, label in season_items:
        lines.append(f"  {code}: {json.dumps(label, ensure_ascii=False)},")
    lines.append("};")
    lines.append("")

    ui_colors = build_ui_colors(data)
    keys = [k for k, _ in ui_colors]
    lines.append("export type MatchColorKey =")
    for i, k in enumerate(keys):
        suffix = ";" if i == len(keys) - 1 else ""
        lines.append(f"  | {json.dumps(k)}{suffix}")
    lines.append("")
    lines.append("export interface UIColorMeta {")
    lines.append("  text: string;")
    lines.append("  bg: string;")
    lines.append("  label: string;")
    lines.append("}")
    lines.append("")
    lines.append("export const MATCH_COLOR_UI: Record<MatchColorKey, UIColorMeta> = {")
    for key, meta in ui_colors:
        lines.append(
            "  %s: { text: %s, bg: %s, label: %s },"
            % (
                json.dumps(key), json.dumps(meta["text"]),
                json.dumps(meta["bg"]), json.dumps(meta["label"], ensure_ascii=False),
            )
        )
    lines.append("};")
    lines.append("")
    lines.append("export const MATCH_COLOR_KEYS = Object.keys(MATCH_COLOR_UI) as MatchColorKey[];")
    lines.append("")
    lines.append("export function isValidMatchColor(value: string): value is MatchColorKey {")
    lines.append("  return (MATCH_COLOR_KEYS as string[]).includes(value);")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", default=str(DEFAULT_JSON), help="Ruta al JSON fuente (default: junto a este script)")
    parser.add_argument("--python-out", help="Ruta de salida del archivo Python (omitir para no generarlo)")
    parser.add_argument("--ts-out", help="Ruta de salida del archivo TypeScript (omitir para no generarlo)")
    args = parser.parse_args()

    if not args.python_out and not args.ts_out:
        parser.error("especifica --python-out y/o --ts-out")

    json_path = Path(args.json)
    data = load_source(json_path)
    source_label = "domain_constants.json (repo futbol-domain-constants)"

    if args.python_out:
        out = Path(args.python_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_python(data, source_label), encoding="utf-8")
        print(f"OK  {out}")

    if args.ts_out:
        out = Path(args.ts_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_typescript(data, source_label), encoding="utf-8")
        print(f"OK  {out}")


if __name__ == "__main__":
    main()
