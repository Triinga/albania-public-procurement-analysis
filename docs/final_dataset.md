# Dataset-i përfundimtar i Pjesës I

`prokurimi_final.csv` bashkon punën e të tri pjesëve në një tabelë të vetme, gati për analizën e Pjesës II dhe vizualizimin e Pjesës III.

> Kodi: [`src/final/final_dataset.py`](../src/final/final_dataset.py) · Ekzekutimi: `python -m src.final.final_dataset` · Raportet: [`reports/final/`](../reports/final/)
>
> Dataset-i ruhet te `data/processed/prokurimi_final.csv` (~209 MB, jashtë git-it).

## 1. Si ndërtohet

| Hapi | Çfarë bën | Burimi |
|---|---|---|
| 1. Dataset-i i integruar | Të tri pjesët e përgatitura, të bashkuara një-me-një (64 kolona) | [`time_integration.md`](time_integration.md#27-dataset-i-i-integruar) |
| 2. Konsistenca mes pjesëve | Dy kolona të reja për tenderët e anuluar që kanë fitues | Seksioni 2 më poshtë |
| 3. Transformimi | Shumat: log, min-max, z-score (9 kolona) | [`values_winners.md`](values_winners.md#6-transformimi) |
| 4. PCA | Komponentët që shpjegojnë ≥ 90% të variancës (6 kolona) | [`values_winners.md`](values_winners.md#8-reduktimi-i-dimensionit-pca) |
| 5. Kolonat konstante | Hiqen kolonat me të njëjtën vlerë në çdo rresht | Seksioni 3 më poshtë |

| Kontrolli | Rezultati |
|---|---|
| Rreshta (procedura) | **277,764**, të njëjtë me skedarët raw; asnjë i humbur ose i dyfishuar |
| Kolona në dataset-in e integruar | 64 |
| Kolona të shtuara | 17 (2 konsistencë, 9 transformim, 6 PCA) |
| Kolona të hequra | 1 (`offers_missing`, konstante) |
| **Kolona në dataset-in përfundimtar** | **80** |
| Procedura me komponentë PCA | 201,837 (të tjerat mbeten `NaN`, sepse PCA kërkon të gjitha vetitë) |

Lista e plotë e kolonave, me hapin ku u shtuan, tipin dhe mungesat: [`final_columns.csv`](../reports/final/final_columns.csv).

## 2. Konsistenca: tenderët e anuluar me fitues

Kur bashkohen kolonat e pjesëve, del një mospërputhje: **27,707 tenderë janë të anuluar (`Anulluar`), por kanë fitues (`Fituesi`)**.

**A është gabim kolona `Anulluar`?** Jo në shumicën e rasteve:
- 27,700 nga 27,707 kanë **arsye anulimi** të shkruar (p.sh. "dokumentet e tenderit përmbajnë gabime"). Një anulim i shënuar gabimisht nuk do të kishte arsye.
- 93% janë procedura **Small Value**. Fituesi i shpallur nuk do të thotë domosdoshmërisht që kontrata u lidh: tenderi mund të anulohet pas shpalljes (p.sh. pas ankimit).

Por disa raste kundërshtojnë vetveten:
- **3,477** janë të anuluar, por kanë **vlerë kontrate të lidhur**.
- **2,001** kanë arsyen "**nuk është paraqitur asnjë ofertë**" (p.sh. brenda afateve kohore), ndërkohë që kanë oferta të dorëzuara. Arsyet "asnjë ofertë **e përshtatshme**" ose "**e vlefshme**" nuk llogariten si kontradiktë, sepse ofertat ekzistonin, por asnjë nuk u pranua.

**Vendimi:** asnjë vlerë nuk ndryshohet ose fshihet (si në leksion: të dhënat nuk fshihen). Shtohen dy kolona:

| Kolona | Përkufizimi | Procedura me 1 |
|---|---|---|
| `kontrate_e_lidhur` | Ka fitues **dhe** nuk është e anuluar | **196,163** |
| `anulim_kontradiktor` | E anuluar, por ka vlerë kontrate të lidhur **ose** arsyeja thotë që nuk u paraqit asnjë ofertë, ndërkohë që ka oferta | **5,054** |

Disa procedura i kanë të dyja kontradiktat, prandaj 3,477 + 2,001 është më shumë se 5,054.

**Si përdoren:**
- Analizat e parave (shuma, kursimi, pjesa e tregut) në Pjesën II duhet të marrin vetëm `kontrate_e_lidhur = 1`, që të mos numërohen kontrata që nuk u lidhën.
- `anulim_kontradiktor = 1` shënon zbulime të dyshimta; si trajtohen vendoset te **mënjanimi i zbulimeve jo të sakta** në Pjesën II.

Gjithashtu, **74** procedura kanë fitues, por 0 oferta të kualifikuara. Edhe këto mbeten siç janë dhe kontrollohen në Pjesën II. Të gjitha numrat: [`final_consistency.csv`](../reports/final/final_consistency.csv).

## 3. Kolonat konstante

Një kolonë që ka të njëjtën vlerë në çdo rresht nuk mbart informacion, prandaj hiqet:

| Kolona | Pse |
|---|---|
| `offers_missing` | `False` në çdo rresht: numri i ofertave nuk mungon asnjëherë |

Lista: [`final_dropped_columns.csv`](../reports/final/final_dropped_columns.csv).
