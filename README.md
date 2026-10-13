# LawCodex — Costa Rica (cr)

Costa Rican legislation as Markdown, from **SINALEVI / SCIJ** (Sistema Costarricense de
Información Jurídica — Sistema Nacional de Legislación Vigente) of the **Procuraduría General
de la República** (https://sinalevi.go.cr/, formerly pgrweb.go.cr/scij): the **Constitución
Política (1949)** and the **laws (leyes)**, each in its **current consolidated version** as
maintained by the Procuraduría (*"última versión de la norma"*, with the amendment notes
"Así reformado por…").

Part of [LawCodex](https://github.com/LawCodex): one public repository per jurisdiction.

Retrieved: **2026-10-13**. Language: Spanish (`es`).

Status: **full** (all laws listed by SINALEVI, current consolidated versions)

## What is covered

| Category | Directory | Files |
|---|---|---|
| Constitución Política de la República de Costa Rica (1949, consolidated) and historical constitutions listed by SINALEVI | `constitucion/` | 15 |
| Laws (leyes), by year of the law | `leyes/<year>/ley-<n>-id<scij>.md` | 21,263 |

SINALEVI lists 21,263 laws (15,933 in force, 5,304 repealed, others annulled/unspecified).
Texts were fetched in priority order: the Constitution and SINALEVI's *Normas usuales* (the
commonly used norms per branch of law: codes and main statutes), then laws in force from the
newest number down, then repealed laws. All 21,263 laws listed (in force and repealed) are included.

Front matter: `identifier` (Ley N°), `scij_id` (SINALEVI's IdFichaNorma), `status`
(`in_force` = *Vigente*, `repealed` = *Derogada*), `version` ("n de m": version number of the
consolidated text), `date` (date of the law).

## What is NOT covered

- Executive decrees (decretos ejecutivos), regulations, international treaties (SINALEVI has
  them; not collected).

## Source

SINALEVI (Procuraduría General de la República): selective search by year and type (Ley,
Constitución Política) through `/ResultadosNormativa/_RecargarResultados`, full text of the
current version through `/ResultadosNormativa/_CargarTextoCompleto`. Each file's `source` is
the norm's SINALEVI page.

## Copyright

Under Costa Rica's Ley N° 6683 sobre Derechos de Autor y Derechos Conexos, official texts
(laws, decrees, judicial decisions) may be freely reproduced; consolidation notes are those of
the Procuraduría General de la República.

## Regenerate

```
python3 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt
RAW=/path/to/scratch .venv/bin/python scripts/cr_fetch.py all
```

No robots.txt on sinalevi.go.cr; up to 3 parallel connections at 1 request/s each.
