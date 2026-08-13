# futbol-domain-constants

Fuente única de constantes de dominio para el sistema de historial
futbolístico de la U. de Chile: `matchStatus`, `matchEvents`, `matchPeriods`,
`tacticalFormations`, `playerPositions`, `playerStatus`, `seasonTypes`,
`uiColors`.

Este repo se consume como **git submodule** desde:

- `history-udechile` (backend FastAPI) → montado en `vendor/domain-constants`
- `futbol-backend` (backend Node/TS) → montado en `vendor/domain-constants`

## Contenido

- `domain_constants.json` — la ÚNICA fuente editable a mano.
- `generate_constants.py` — genera `constants.py` (Python/IntEnum) y/o
  `constants.ts` (TypeScript/enum) a partir del JSON.

## Uso desde un repo consumidor

```bash
# Python (FastAPI)
python3 vendor/domain-constants/generate_constants.py \
  --json vendor/domain-constants/domain_constants.json \
  --python-out app/core/constants.py

# TypeScript (Node)
python3 vendor/domain-constants/generate_constants.py \
  --json vendor/domain-constants/domain_constants.json \
  --ts-out constants/index.ts
```

## Regla de oro

Estos códigos quedan persistidos en PostgreSQL. Nunca renumerar ni
reutilizar un código existente — solo agregar al final.
