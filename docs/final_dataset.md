# Dataset-i përfundimtar i Pjesës I

`prokurimi_final.csv` bashkon punën e të tri pjesëve në një tabelë të vetme, gati për analizën e Pjesës II dhe vizualizimin e Pjesës III.

> Kodi: [`src/final/final_dataset.py`](../src/final/final_dataset.py) · Ekzekutimi: `python -m src.final.final_dataset` · Raportet: [`reports/final/`](../reports/final/)
>
> Dataset-i ruhet te `data/processed/prokurimi_final.csv` (~218 MB, jashtë git-it).

## 1. Si ndërtohet

| Hapi | Çfarë bën | Burimi |
|---|---|---|
| 1. Dataset-i i integruar | Të tri pjesët e përgatitura, të bashkuara një-me-një (64 kolona) | [`time_integration.md`](time_integration.md#27-dataset-i-i-integruar) |
| 2. Konsistenca mes pjesëve | Kolona të reja për statusin e tenderit dhe për tenderët e anuluar që kanë fitues (6 kolona) | Seksioni 2 më poshtë |
| 3. Transformimi | Shumat: log, min-max, z-score (9 kolona) | [`values_winners.md`](values_winners.md#6-transformimi) |
| 4. PCA | Komponentët që shpjegojnë ≥ 90% të variancës (6 kolona) | [`values_winners.md`](values_winners.md#8-reduktimi-i-dimensionit-pca) |
| 5. Kolonat konstante | Hiqen kolonat me të njëjtën vlerë në çdo rresht | Seksioni 3 më poshtë |

| Kontrolli | Rezultati |
|---|---|
| Rreshta (procedura) | **277,764**, të njëjtë me skedarët raw; asnjë i humbur ose i dyfishuar |
| Kolona në dataset-in e integruar | 64 |
| Kolona të shtuara | 21 (6 konsistencë, 9 transformim, 6 PCA) |
| Kolona të hequra | 1 (`offers_missing`, konstante) |
| **Kolona në dataset-in përfundimtar** | **84** |
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

**Vendimi:** asnjë rresht nuk fshihet dhe asnjë vlerë origjinale nuk ndryshohet (`Anulluar`, `Fituesi`, `Vlera_e_fituesit` mbeten siç vijnë nga APP-ja; si në leksion: të dhënat nuk fshihen). Prania e fituesit **nuk** konsiderohet provë e mjaftueshme që kontrata u nënshkrua. Shtohen 6 kolona:

| Kolona | Përkufizimi |
|---|---|
| `kontrate_e_lidhur` | 1 nëse ka fitues **dhe** nuk është e anuluar (196,163) |
| `flag_kontrate_anuluar` | 1 nëse është e anuluar, por ka **vlerë kontrate të lidhur** (`Vlera_e_fituesit_ne_lidhjen_e_kontrates`) |
| `flag_pa_oferte_kontradikte` | 1 nëse është e anuluar me arsyen që **nuk u paraqit asnjë ofertë**, ndërkohë që `Numri_i_ofertave_te_dorezuara` > 0 |
| `anulim_kontradiktor` | 1 nëse vlen të paktën njëri nga dy flag-et |
| `arsye_kontradikte` | Lloji i kundërshtimit: kontratë e lidhur, asnjë ofertë, ose të dyja |
| `statusi_analitik` | Një status analitik për çdo tender (tabela më poshtë) |

**Kontrolli i numrave** (llogariten nga kodi mbi kolonat reale, jo të vendosur me dorë):

| Kontrolli | Rezultati |
|---|---|
| Anuluar me vlerë kontrate | 3,477 |
| Arsyeja «asnjë ofertë», por ka oferta | 2,001 |
| Mbivendosja e dy kategorive | 424 |
| Raste kontradiktore unike | **5,054** |

Arsyet «asnjë ofertë **e përshtatshme**» ose «**e vlefshme**» **nuk** llogariten si kontradiktë: ofertat ekzistonin, por asnjë nuk u pranua.

### `statusi_analitik`

Rregullat zbatohen me radhë; vlen rregulli i parë që plotësohet:

| # | Statusi | Rregulli | Procedura |
|---|---|---|---|
| 1 | **Kontradiktor** | `anulim_kontradiktor = 1` | 5,054 |
| 2 | **Jo e lidhur** | E anuluar, pa kontradiktë | 68,369 |
| 3 | **Kontratë e konfirmuar** | Jo e anuluar, me vlerë kontrate të lidhur | 48,028 |
| 4 | **Me fitues, kontratë e pakonfirmuar** | Jo e anuluar, me fitues, pa vlerë kontrate | 150,174 |
| 5 | **Pa kontratë të konfirmuar** | Jo e anuluar, pa fitues, pa vlerë kontrate | 6,139 |
| | **Gjithsej** | | **277,764** |

**Kujdes në interpretim:**
- **Mungesa e vlerës së kontratës nuk do të thotë mungesë kontrate.** Fusha `Vlera_e_fituesit_ne_lidhjen_e_kontrates` mungon te **81.5%** e tenderëve (por vetëm te 47.7% në 2017), pra varet nga mënyra si plotësohet, jo nga lidhja e kontratës. Prandaj ajo nuk përdoret si kusht i detyrueshëm: përndryshe 150,174 tenderë me fitues do të dilnin "pa kontratë". Ata dallohen si **të pakonfirmuar**, jo si të palidhur.
- **`kontrate_e_lidhur` është klasifikim operacional**, i bazuar në statusin e tenderit (ka fitues dhe nuk është i anuluar), **jo dëshmi e pavarur** e nënshkrimit të kontratës. Nëse përdoret në analizë, rezultatet **nuk** duhen paraqitur si numër i kontratave të konfirmuara; numri i kontratave të konfirmuara është ai i statusit **Kontratë e konfirmuar** (48,028).
- **"Pa kontratë të konfirmuar"**: tenderë jo të anuluar dhe pa fitues. Mund të jenë ende të papërfunduar në datën e eksportit, prandaj nuk pohohet që kontrata nuk u lidh.
- **2,039** tenderë jo të anuluar kanë vlerë kontrate, por nuk kanë emër fituesi. Ata janë **Kontratë e konfirmuar** (vlera e kontratës është prova), por kanë `kontrate_e_lidhur = 0`, sepse ky rregull kërkon fitues.

**Si përdoren në pjesët e tjera:**
- **Pjesa II:** analizat e parave (shuma, kursimi, pjesa e tregut) përjashtojnë statuset **Jo e lidhur** dhe **Kontradiktor**; rastet **Kontradiktor** shqyrtohen te **mënjanimi i zbulimeve jo të sakta**, duke përdorur `arsye_kontradikte` për llojin e kundërshtimit.
- **Pjesa III:** tenderët e shpallur, kontratat e konfirmuara, tenderët e anuluar dhe rastet kontradiktore paraqiten veçmas.

Numrat: [`final_consistency.csv`](../reports/final/final_consistency.csv), [`final_status.csv`](../reports/final/final_status.csv).

Gjithashtu, **74** procedura kanë fitues, por 0 oferta të kualifikuara. Edhe këto mbeten siç janë dhe kontrollohen në Pjesën II.

## 3. Kolonat konstante

Një kolonë që ka të njëjtën vlerë në çdo rresht nuk mbart informacion, prandaj hiqet:

| Kolona | Pse |
|---|---|
| `offers_missing` | `False` në çdo rresht: numri i ofertave nuk mungon asnjëherë |

Lista: [`final_dropped_columns.csv`](../reports/final/final_dropped_columns.csv).
