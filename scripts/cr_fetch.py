#!/usr/bin/env python3
"""Costa Rica: SINALEVI / SCIJ (Sistema Costarricense de Información Jurídica, Procuraduría
General de la República, https://sinalevi.go.cr/ — formerly pgrweb.go.cr/scij).

1. list:     selective search by year (types: 1 Constitución Política, 8 Ley), all results,
             -> $RAW/list.json (IdFichaNorma, number, name, date, state, current version id)
2. texts:    full consolidated text of the current version of each norm
             (POST /ResultadosNormativa/_CargarTextoCompleto) -> $RAW/html/<id>.html
3. convert:  -> constitucion/, leyes/<thousands>/ley-<n>.md

One request at a time, 1 s apart (robots.txt: none).
"""
import html as htmlmod
import json
import os
import re
import sys
import time
from datetime import date

import requests
import yaml
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cr_textmd as T  # noqa: E402

RAW = os.environ.get("RAW", "/Users/magicaltux/projects/lawcodex/_raw/cr")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "LawCodex/1.0 (+https://github.com/LawCodex)"
SITE = "https://sinalevi.go.cr"
TODAY = date.today().isoformat()
TYPES = {1: "Constitución Política", 8: "Ley"}

MODEL = {"TipoBusqueda": 2, "TipoNorma": 0, "ListaTipoNorma": "8", "CantidadResultados": -1, "Orden": 0,
         "Descendente": False, "Pagina": 1, "Texto": "", "AnnioDesde": 2020, "AnnioHasta": 2020, "DescTipoNorma": None,
         "Filtro": 0, "TextoCompleto": False, "Versiones": 0, "Numero": -1, "Nombre": None,
         "FechaDesde": "0001-01-01T00:00:00", "FechaHasta": "0001-01-01T00:00:00", "FechaDesdeString": None,
         "FechaHastaString": None, "AnnioDesdeAprobacion": 0, "AnnioHastaAprobacion": 0, "EnteEmisor": 0,
         "NumeroGaceta": 0, "FechaHastaGaceta": "0001-01-01T00:00:00", "FechaDesdeGaceta": "0001-01-01T00:00:00",
         "FechaHastaGacetaString": None, "FechaDesdeGacetaString": None, "AnnioDesdeGaceta": 0, "AnnioHastaGaceta": 0,
         "AnnioColeccion": 0, "SemestreColeccion": 0, "TomoColeccion": 0, "NumeroBoletin": 0,
         "FechaDesdeBoletin": "0001-01-01T00:00:00", "FechaHastaBoletin": "0001-01-01T00:00:00",
         "FechaDesdeBoletinString": None, "FechaHastaBoletinString": None, "AnnioDesdeBoletin": 0,
         "AnnioHastaBoletin": 0, "VetoOSello": 0, "NormasHistoricas": True, "BusquedaXDescriptor": False,
         "RamaDerecho": 0, "DescRamaDerecho": None, "TipoTexto": None, "TipoDescriptor": None, "IdRamaDerecho": 0,
         "ListaRamaDerecho": None, "TerminoGenerico": None, "DescDescriptor": None, "IdDescriptor": 0,
         "NombreNorma": None}

s = requests.Session()
s.headers["User-Agent"] = UA
s.headers["X-Requested-With"] = "XMLHttpRequest"
_last = [0.0]


def post(path, data):
    for k in range(5):
        w = 1.0 - (time.time() - _last[0])
        if w > 0:
            time.sleep(w)
        _last[0] = time.time()
        try:
            r = s.post(SITE + path, data=data, timeout=(30, 600))
            if r.status_code == 200:
                return r.json()
            print("HTTP", r.status_code, path, data.get("idFichaNorma", ""), file=sys.stderr, flush=True)
        except (requests.RequestException, ValueError) as e:
            print("ERR", path, e, file=sys.stderr, flush=True)
        time.sleep(10 * (k + 1))
    return None


def build_list():
    rows = {}
    for t in TYPES:
        for y in range(1821, date.today().year + 1):
            m = dict(MODEL, ListaTipoNorma=str(t), AnnioDesde=y, AnnioHasta=y)
            d = post("/ResultadosNormativa/_RecargarResultados", {"busquedaNormativa": json.dumps(m)})
            h = (d or {}).get("html", "")
            mm = re.search(r'"data":\{"Data":(\[.*?\]),"Total":(\d+)', h, re.S)
            if not mm:
                continue
            for r in json.loads(mm.group(1)):
                rows[r["IdFichaNorma"]] = {k: r.get(k) for k in (
                    "IdFichaNorma", "NumeroNormativa", "IdSubNumeroNormativa", "NombreNormativa", "stringFechaNormativa",
                    "IdTipoNorma", "NombreTipoNorma", "DescEnteEmisor", "IdVersionNorma", "VersionNorma", "EstadoNorma")}
            print(t, y, len(rows), flush=True)
    json.dump(sorted(rows.values(), key=lambda r: r["IdFichaNorma"]), open(os.path.join(RAW, "list.json"), "w"),
              ensure_ascii=False, indent=0)
    print("listed", len(rows))


def usuales():
    """IdFichaNorma of SINALEVI's "Normas usuales" (commonly used norms, by branch of law)."""
    p = os.path.join(RAW, "usuales.json")
    if os.path.exists(p):
        return set(json.load(open(p)))
    h = post("/BusquedaAvanzada/_GetFormularioBusqueda", {"idBusqueda": "4", "idTipo": "1"})["html"]
    ramas = json.loads(re.search(r'"dataSource":(\[.*?\])', h[h.find("RamaDerecho"):]).group(1))
    ids = set()
    for r in ramas:
        m = dict(MODEL, TipoBusqueda=4, ListaTipoNorma=None, AnnioDesde=0, AnnioHasta=0, NormasHistoricas=False,
                 RamaDerecho=r["IdRamaDerecho"], IdRamaDerecho=r["IdRamaDerecho"])
        d = post("/ResultadosNormativa/_RecargarResultados", {"busquedaNormativa": json.dumps(m)})
        ids |= {int(x) for x in re.findall(r'"IdFichaNorma":(\d+)', (d or {}).get("html", ""))}
    json.dump(sorted(ids), open(p, "w"))
    return ids


def texts(workers=3):
    """Full texts, in priority order: Constitution and "normas usuales", then laws in force
    (newest first), then repealed laws. Up to 3 parallel connections, each paced at 1 req/s."""
    import threading
    from concurrent.futures import ThreadPoolExecutor
    d = os.path.join(RAW, "html")
    os.makedirs(d, exist_ok=True)
    rows = json.load(open(os.path.join(RAW, "list.json")))
    us = usuales()

    def prio(r):
        vig = (r.get("EstadoNorma") or "").lower().startswith("vigente")
        return (0 if r["IdTipoNorma"] == 1 or r["IdFichaNorma"] in us else (1 if vig else 2), -(r["NumeroNormativa"] or 0))
    rows.sort(key=prio)
    local = threading.local()

    def worker(r):
        p = os.path.join(d, f"{r['IdFichaNorma']}.json")
        if os.path.exists(p):
            return
        if not hasattr(local, "s"):
            local.s = requests.Session()
            local.s.headers.update({"User-Agent": UA, "X-Requested-With": "XMLHttpRequest"})
            local.last = 0.0

        def lpost(data):
            for k in range(5):
                w = 1.0 - (time.time() - local.last)
                if w > 0:
                    time.sleep(w)
                local.last = time.time()
                try:
                    x = local.s.post(SITE + "/ResultadosNormativa/_CargarTextoCompleto", data=data, timeout=(30, 600))
                    if x.status_code == 200:
                        return x.json()
                except (requests.RequestException, ValueError) as e:
                    print("ERR", r["IdFichaNorma"], e, file=sys.stderr, flush=True)
                time.sleep(10 * (k + 1))
            return None
        res = lpost({"idFichaNorma": str(r["IdFichaNorma"]), "version": str(r["IdVersionNorma"]), "busqueda": ""})
        if res and res.get("redireccionar"):
            m = re.search(r"param2=(\d+)", res.get("direccion", ""))
            if m:
                res = lpost({"idFichaNorma": str(r["IdFichaNorma"]), "version": m.group(1), "busqueda": ""})
        if res and res.get("html"):
            json.dump({"html": res["html"]}, open(p, "w"), ensure_ascii=False)

    n = 0
    with ThreadPoolExecutor(workers) as ex:
        for _ in ex.map(worker, rows):
            n += 1
            if n % 200 == 0:
                print("texts", n, len(rows), flush=True)
    print("texts done", n)


BLOCK_TAGS = ("p", "h1", "h2", "h3", "h4", "h5", "h6", "li")


def html_blocks(h):
    soup = BeautifulSoup(h, "lxml")
    for t in soup(["style", "script", "input", "button", "head"]):
        t.decompose()
    for a in soup.select("a.enlaceFicha"):
        a.decompose()
    for e in soup.select("#h2UltimaVersion, #h2IrUltimaVersion, #divVersionAnterior, #divVersionSiguiente, h1#h1-Size"):
        e.decompose()
    out = []
    for el in soup.find_all(list(BLOCK_TAGS) + ["table"]):
        if el.find_parent("table") is not None:
            continue
        if el.name == "table":
            rows = []
            for tr in el.find_all("tr"):
                cells = [re.sub(r"\s+", " ", td.get_text(" ", strip=True)).replace("|", "\\|") for td in tr.find_all(["td", "th"])]
                if any(cells):
                    rows.append(cells)
            if rows:
                w = max(len(r) for r in rows)
                rows = [r + [""] * (w - len(r)) for r in rows]
                md = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * w] + ["| " + " | ".join(r) + " |" for r in rows[1:]]
                out.append(("table", "\n".join(md)))
            continue
        if el.find(list(BLOCK_TAGS)) is not None:
            continue
        txt = el.get_text(" ", strip=True).replace("\xa0", " ")
        txt = re.sub(r"\s+", " ", txt).strip()
        if txt and not re.fullmatch(r"Versión de la Norma: \d+ de \d+|Anterior|Siguiente", txt):
            out.append(("p", txt))
    return out


def convert():
    rows = json.load(open(os.path.join(RAW, "list.json")))
    n = 0
    for r in rows:
        p = os.path.join(RAW, "html", f"{r['IdFichaNorma']}.json")
        if not os.path.exists(p):
            continue
        blocks = html_blocks(json.load(open(p))["html"])
        # tables are emitted verbatim; other blocks go through heading/article detection
        parts, buf = [], []
        for kind, txt in blocks:
            if kind == "table":
                if buf:
                    parts.append(T.blocks_to_md(buf))
                    buf = []
                parts.append(txt)
            else:
                buf.append(txt)
        if buf:
            parts.append(T.blocks_to_md(buf))
        md = "\n\n".join(x for x in parts if x.strip()).replace("\r", "")
        num = r["NumeroNormativa"]
        sub = r.get("IdSubNumeroNormativa") or "0"
        fecha = r.get("stringFechaNormativa") or ""
        m = re.match(r"(\d{2})/(\d{2})/(\d{4})", fecha)
        iso = f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None
        name = (r.get("NombreNormativa") or "").strip()
        if r["IdTipoNorma"] == 1:
            yr = iso[:4] if iso else "s-f"
            if yr == "1949":
                out = os.path.join(REPO, "constitucion", "constitucion-politica-1949.md")
                title = "Constitución Política de la República de Costa Rica"
            else:
                out = os.path.join(REPO, "constitucion", "historicas", f"{yr}-id{r['IdFichaNorma']}.md")
                title = f"{name} ({yr})" if name else f"Constitución ({yr})"
            typ, ident = "constitution", name or "Constitución Política"
        else:
            numtxt = f"{num}" + (f"-{sub}" if sub not in ("0", "", None) else "")
            # old laws were numbered per year, so numbers repeat: shard by year, keep the SCIJ id in the name
            out = os.path.join(REPO, "leyes", iso[:4] if iso else "sin-fecha", f"ley-{numtxt}-id{r['IdFichaNorma']}.md")
            title = f"Ley N° {numtxt} — {name}"
            typ, ident = ("code" if name.lower().startswith("código") else "act"), f"Ley N° {numtxt}"
        est = (r.get("EstadoNorma") or "").lower()
        front = {"title": title, "identifier": ident, "scij_id": r["IdFichaNorma"], "type": typ, "jurisdiction": "cr",
                 "language": "es", "date": iso, "status": "in_force" if est.startswith("vigente") else (
                     "repealed" if est.startswith("derogad") else "unknown"),
                 "version": (r.get("VersionNorma") or "").replace("Versión de la norma: ", ""),
                 "source": f"{SITE}/ResultadosNormativa/Informacion?param1={r['IdFichaNorma']}&param2={r['IdVersionNorma']}&param3=1",
                 "retrieved": TODAY}
        fm = yaml.safe_dump(front, allow_unicode=True, sort_keys=False, width=1000).strip()
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "w", encoding="utf-8").write("\n".join(["---", fm, "---", "", f"# {title}", "",
                                                          f"> SCIJ: {r.get('EstadoNorma')}; {r.get('VersionNorma')}.", "", md, ""]))
        n += 1
    print("converted", n)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd in ("list", "all"):
        build_list()
    if cmd in ("texts", "all"):
        texts()
    if cmd in ("convert", "all"):
        convert()
