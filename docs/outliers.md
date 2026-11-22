# Detektimi i përjashtuesve (Faza II)

> Kodi: [`src/common/outliers.py`](../src/common/outliers.py) (i përbashkët), [`src/outliers/amounts_time.py`](../src/outliers/amounts_time.py) (Semine), [`src/outliers/competition_winners.py`](../src/outliers/competition_winners.py) (Tringa) · Ekzekutimi: `python -m src.outliers.amounts_time`, `python -m src.outliers.competition_winners` · Raportet: [`reports/outliers/`](../reports/outliers/)

## 1. Metoda (e përbashkët për të dyja pjesët)

Dy metoda, njëra mbi tjetrën:
- **IQR**: jashtë `[Q1 - 1.5×IQR, Q3 + 1.5×IQR]`.
- **Z-score i fortë (MAD)**: `|0.6745 × (x - mediana) / MAD| > 3.5` (pragu standard Iglewicz & Hoaglin).

Të dyja llogariten **globalisht** dhe **brenda `Lloji_i_procedures`** (procedurat e vogla "Small Value" dhe ato të mëdha kanë shkallë krejt të ndryshme; një prag global do të shënonte pothuajse çdo procedurë të madhe si përjashtuese, edhe pse është e vërtetë). Shumat dhe kohëzgjatjet llogariten mbi **shkallën log** (`log(1+x)`), sepse janë të zhdrejtuara djathtas; `ditet_nga_zgjedhjet` mbetet në shkallën origjinale sepse ka vlera negative.

### `outlier_status`

Çdo rresht i shënuar nga të paktën një metodë merr një nga tre vlerat (`src.common.outliers.outlier_status`):

| Statusi | Kushti |
|---|---|
| **gabim** | Vlera është e pamundur vetë (jashtë çdo shkalle statistikore) — p.sh. shumë qindra herë më e madhe se shuma më e madhe reale, ose kohëzgjatje negative |
| **e vërtetë por e rrallë** | IQR dhe MAD bien dakord që vlera del jashtë shpërndarjes, dhe nuk është e pamundur |
| **e pasigurt** | IQR dhe MAD nuk bien dakord (vetëm njëra e shënon) |
| *(bosh)* | Nuk është shënuar nga asnjëra metodë |

Asnjë rresht nuk fshihet apo ndryshohet; `outlier_status` shtohet si kolonë e re.

## 2. Pjesa e Semine: shumat dhe koha

Kolonat: `Fondi_limit`, `Vlera_e_fituesit`, `Vlera_e_fituesit_ne_lidhjen_e_kontrates` (log), `ditet_publikim_hapje`, `kohezgjatja_e_tenderit` (log), `ditet_nga_zgjedhjet` (shkallë origjinale).

### 2.1 Pragu i "gabim" për shumat

| Kolona | Max real | Vlera mbi 100 miliardë lekë |
|---|---|---|
| `Fondi_limit` | 39.3 miliardë | 0 |
| `Vlera_e_fituesit` | 35,000 miliardë | 1 |
| `Vlera_e_fituesit_ne_lidhjen_e_kontrates` | 35,000 miliardë | 1 |

Shkalla midis shumës më të madhe reale (~39 miliardë) dhe vlerave "35,000 miliardë" (të njohura tashmë si të pamundura te Faza I, `docs/values_winners.md`) është ~900×, pra **100 miliardë lekë** (~1 miliard euro) e ndan qartë njërën grup nga tjetri, pa prekur asnjë shumë reale, pavarësisht sa e madhe. Të njëjtin prag (me kuptim: kohëzgjatje negative ose mbi 10 vjet) e përdor edhe për kohën.

### 2.2 Kontrolli i 26,749 rasteve: vlera e kontratës ≠ vlera e fituesit

Raporti `ratio = vlera_kontrate / vlera_fituese` mbi 51,503 rastet kur të dyja ekzistojnë tregon një model shumë të pastër:

| Percentili | Raporti |
|---|---|
| 1%–10% | 1.00 |
| 50% (mediana) | **1.20** |
| 90%–99% | 1.20 |
| Maksimumi | 1.2028 |

Pothuajse të gjitha rastet janë raporti **1.0** (pa ndryshim) ose **1.2** (+20%, pikërisht TVSH-ja shqiptare) — pra dallimi është **i rregullt**, siç parashikohej te Faza I. Prandaj: **brenda [0.75, 1.25] = e rregullt** (bandë e gjerë, me hapësirë edhe për negociata apo lote, edhe pse në praktikë mbulon vetëm modelin TVSH). Nga 26,749 rastet, **122 bien jashtë** këtij brezi — nga këto, 110 kanë vlerë kontrate **0** përballë një vlere fituese reale (kontratë e paregjistruar, jo thjesht shkallë tjetër). Këto 122 shkojnë për shqyrtim në Pjesën II, nuk fshihen.

### 2.3 Kontrolli i 13 publikimeve të vonuara

Rillogaritur drejt nga dataset-i final (jo nga lista e para-pastrimit): përputhet saktësisht me `docs/time_integration.md` (223 mbeten pas pastrimit, 210 janar–shkurt normale + **13** me vonesë më të madhe). Lista e plotë me ditët e vonesës: [`late_publications_phase2.csv`](../reports/outliers/late_publications_phase2.csv).

## 3. Si vazhdon Tringa

Për pjesën e saj (oferta, `cpv_count`, kontratat për fitues — detektim univariant, plus detektimi multivariant mbi 9 vetitë e PCA-së me distancën Mahalanobis), e njëjta logjikë:
1. Përdor `src.common.outliers.detect` (dhe `outlier_status`) në vend të një metode të re — kështu emërtimi i flag-eve mbetet i njëjtë për të dy pjesët.
2. Globalisht **dhe** brenda `Lloji_i_procedures`, njësoj.
3. Për "gabim", gjej pragun nga vetë të dhënat (si në 2.1: krahaso vlerën më të madhe reale të kuptimtë me vlerat qartazi të pamundura), jo një numër i hamendësuar.
4. Rezultatet te `reports/outliers/`, një skedar për çdo kontroll.

## 4. Pjesa e Tringës: konkurrenca, procedurat dhe fituesit

> Kodi: [`src/outliers/competition_winners.py`](../src/outliers/competition_winners.py) · Ekzekutimi: `python -m src.outliers.competition_winners` · Raportet: [`reports/outliers/`](../reports/outliers/) (skedarët `competition_*`, `winners_*`, `consistency_*`, `multivariate_*`) · Flag-et: `data/processed/outliers_competition_winners.csv` (një rresht për procedurë, me çelësat `Numri_i_references`, `Autoriteti_kontraktues`, `year`)

Përdoren të njëjtat metoda (`src.common.outliers.detect`, `outlier_status`), të njëjtat tre vlera të statusit dhe e njëjta shkallë (log) si në seksionin 2.

### 4.1 Detektimi univariant: ofertat dhe `cpv_count`

Kolonat: `Numri_i_ofertave_te_dorezuara`, `Numri_i_ofertave_te_kualifikuara`, `cpv_count`. Për `cpv_count`, vlera **0** do të thotë që kodi CPV mungon (22% e procedurave), jo "zero kode". Prandaj nuk trajtohet si vlerë në detektim.

**Vlerat e pamundura ("gabim")** u kërkuan me rregulla logjike, jo me prag statistikor: oferta të kualifikuara më shumë se të dorëzuara, numra negativë dhe `qualified_offer_share` jashtë [0, 1]. **Asnjë rast** nuk u gjet ([`competition_impossible_values.csv`](../reports/outliers/competition_impossible_values.csv)). Pra numrat e ofertave janë konsistentë mes tyre. Maksimumi prej 103 ofertash është i besueshëm.

| Kolona | gabim | e vërtetë por e rrallë | e pasigurt |
|---|---|---|---|
| `Numri_i_ofertave_te_dorezuara` | 0 | 559 | 1,099 |
| `Numri_i_ofertave_te_kualifikuara` | 0 | 1,054 | 1,696 |
| `cpv_count` | 0 | 21 | 13,017 |

### 4.2 Mënjanimi i zbulimeve jo të sakta te numrat

**(a) Pragu global kundrejt pragut brenda llojit të procedurës** ([`competition_global_vs_group.csv`](../reports/outliers/competition_global_vs_group.csv)):

| Kolona | Globalisht | Brenda llojit | Vetëm globalisht (zbulim jo i saktë) | Vetëm brenda llojit (i fshehur nga shkalla globale) |
|---|---|---|---|---|
| Oferta të dorëzuara | 0 | 1,658 | 0 | 1,658 |
| Oferta të kualifikuara | 1 | 2,750 | 0 | 2,749 |
| `cpv_count` | 14,784 | 13,038 | **1,746** | 0 |

Shkalla e procedurave ndryshon shumë: "Small Value" ka medianë 9 oferta, ndërsa "Negotiated without Notice" ka 1 ([`competition_count_spread.csv`](../reports/outliers/competition_count_spread.csv)). Pragu global (≈140 oferta) dominohet nga "Small Value" (66% e rreshtave), prandaj **nuk gjen asnjë** përjashtues. Brenda llojit, p.sh. te "Open Local" (pragu ≈19 oferta), dalin procedura me shumë më shumë oferta se zakonisht për atë lloj. Në drejtimin tjetër, 1,746 procedura me shumë kode CPV dalin përjashtuese vetëm globalisht, por janë normale për llojin e tyre: këto janë **zbulime jo të sakta** dhe hiqen. Prandaj statusi përcaktohet nga flag-et **brenda llojit**. Flag-et globale ruhen vetëm për krahasim.

**(b) Shpërndarje zero (numra diskretë).** Kur më shumë se gjysma e një grupi ka të njëjtën vlerë, IQR ose MAD bëhet 0. P.sh. `cpv_count` ka Q1 = mediana = 1, pra MAD = 0, dhe te "Purchase Tickets" edhe IQR = 0. Atëherë metoda do të shënonte **çdo** vlerë tjetër si përjashtuese, edhe 2 kode CPV. Në këto grupe metoda nuk e gjykon dot shpërndarjen dhe nuk shënon asgjë (`drop_zero_spread`, njësoj si `mad_zscore_outliers` kur MAD = 0). Kjo shpjegon pse `cpv_count` ka shumë raste "e pasigurt": vetëm IQR mund të gjykojë dhe të dyja metodat nuk bien kurrë dakord, prandaj ato nuk i quajmë gabime.

### 4.3 Fituesit: kontratat për fitues dhe NIPT-et

Një rresht për çdo fitues (7,444 NIPT). Numri i kontratave është shumë i zhdrejtuar: mediana është 4, ndërsa maksimumi 5,762 (AMADEUS, bileta udhëtimi).

| Statusi (kontrata për fitues) | Fitues |
|---|---|
| gabim | 5 |
| e vërtetë por e rrallë | 53 |
| e pasigurt | 58 |

**Të vërtetë apo gabim?** Për çdo fitues me shumë kontrata kontrollohet numri i autoriteteve dhe i viteve ([`winners_top_contracts.csv`](../reports/outliers/winners_top_contracts.csv)). Të 50 fituesit më të mëdhenj fitojnë te **27 deri 791 autoritete** dhe në 7–10 vite. P.sh. INFOSOFT OFFICE ka 4,002 kontrata te 791 autoritete. Kjo nuk është gabim regjistrimi, por furnitorë realë të mëdhenj (bileta, sigurime, barna, kancelari). Prandaj mbeten "e vërtetë por e rrallë" dhe nuk përjashtohen nga analiza.

**NIPT-et jashtë formatit shqiptar** `[A-Z]\d{8}[A-Z]` ([`winners_nipt_review.csv`](../reports/outliers/winners_nipt_review.csv)):

| Klasa | Fitues | Kontrata | Statusi | Arsyeja |
|---|---|---|---|---|
| Konsorcium (të gjithë NIPT-et e vlefshëm) | 158 | 166 | – | Fitues i përbashkët i rregullt |
| Kompani e huaj (numër TVSH, p.sh. `SI…`, `HR…`, `ATU…`) | 14 | 38 | e vërtetë por e rrallë | Numri i TVSH-së së vendit të tyre |
| Gabim shtypi (`21406043R`, `L61727452J-OE`) | 5 | 31 | gabim | NIPT shqiptar me shkronjë që mungon ose shtesë (si te Faza I) |
| Vetëm shifra / format tjetër | 60 | 175 | e pasigurt | Mund të jetë regjistër i huaj, por nuk vërtetohet |
| Konsorcium me NIPT të pavlefshëm | 3 | 3 | e pasigurt | – |

### 4.4 Rastet e Fazës I: anulimet kontradiktore dhe fituesit pa oferta të kualifikuara

([`consistency_review.csv`](../reports/outliers/consistency_review.csv), sipas vitit: [`consistency_review_by_year.csv`](../reports/outliers/consistency_review_by_year.csv))

| Rasti | Procedura | Statusi |
|---|---|---|
| E anuluar, por me vlerë kontrate, **viti 2017** | 3,466 | gabim |
| E anuluar, por me vlerë kontrate, vite të tjera | 11 | e pasigurt |
| Arsyeja "asnjë ofertë", por ka oferta të kualifikuara **dhe** fitues | 1,380 | gabim |
| Arsyeja "asnjë ofertë", ka oferta, por **asnjë të kualifikuar** dhe pa fitues | 162 | **zbulim jo i saktë** |
| Arsyeja "asnjë ofertë", ka oferta të kualifikuara, pa fitues | 35 | e pasigurt |
| Fitues me 0 oferta të kualifikuara, procedura e anuluar | 72 | e vërtetë por e rrallë |
| Fitues me 0 oferta të kualifikuara, procedura **jo** e anuluar | 2 | gabim |

Arsyetimi:
- **3,466 nga 3,477** anulimet "me kontratë të lidhur" janë nga **2017**: 3,466 në 2017, 6 në 2016, 2 në 2018, 2 në 2020 dhe 1 në 2021. Sjellja reale e autoriteteve nuk ndryshon kështu nga viti në vit. Kjo është gabim sistematik i eksportit të vitit 2017, ku fusha e anulimit ose e kontratës është mbushur gabim. Rastet e tjera (11) mund të jenë anulime të pjesshme (lote), prandaj mbeten "e pasigurt".
- **"Asnjë ofertë" me oferta**: kur ka oferta të kualifikuara dhe fitues, arsyeja kundërshton dy fusha të tjera, pra është gabim. Kur ka oferta, por asnjë të kualifikuar dhe pa fitues, arsyeja është përdorur në kuptimin "asnjë ofertë e vlefshme". Procedura është konsistente, dhe detektimi i Fazës I ishte **zbulim jo i saktë**.
- **74 fituesit me 0 oferta të kualifikuara**: 72 janë anuluar më pas, që do të thotë se ofertuesi i renditur u skualifikua dhe procedura u mbyll. Pra janë konsistente. Vetëm 2 mbeten pa anulim dhe janë gabim.

Përfundimi: nga 5,054 kontradiktat, **4,846 janë gabime**, **162 nuk janë kontradikta** dhe **46 mbeten të pasigurta**. Kolonat `outlier_status_konsistenca` dhe `arsye_konsistenca` shtohen te flag-et.

### 4.5 Detektimi multivariant: distanca Mahalanobis

Llogaritet mbi 9 vetitë e PCA-së (`src.values_winners.pca.feature_matrix`: fondi, vlera, dy kohëzgjatje, ditët nga zgjedhjet, dy numra ofertash, pjesa e kualifikuar, `cpv_count`; log + z-score), për 201,837 procedura që i kanë të gjitha vetitë:

$$D^2(x) = (x - \mu)^\top \Sigma^{-1} (x - \mu)$$

- **Pse Mahalanobis dhe jo z-score për secilën kolonë:** merr parasysh korrelacionet. Një procedurë me fond të madh **dhe** vlerë fituese të vogël mund të jetë normale në secilën kolonë veç e veç, por e pazakontë në kombinim, sepse fondi dhe vlera kanë korrelacion 0.99.
- **Pragu:** χ² me 9 shkallë lirie, 99.9% → **D² > 27.877**.
- **Mënjanimi i efektit maskues:** mesatarja dhe kovarianca e zakonshme tërhiqen nga vetë përjashtuesit dhe i bëjnë ata të duken më afër. Prandaj vlerësohen në dy hapa: (1) pa gabimet e njohura të shumave (shih më poshtë); (2) përsëri, pa përjashtuesit e hapit të parë. Ky është një version i thjeshtë i idesë së kovariancës robuste (MCD).
- **Gabimet e njohura të shumave:** pragu i Semines (> 100 miliardë lekë), vlerat ≤ 1 lek dhe **vlera fituese ≥ 100 herë ose ≤ 1/100 e fondit limit**. Rregulli i fundit doli nga vetë detektimi: në versionin e parë, histogrami i D² kishte një grumbull të dytë të ndarë (D² ≈ 250–800, ~5,700 procedura, të klasifikuara gabimisht si "e vërtetë por e rrallë"). Këto procedura kishin raport vlerë/fond ≈ 0.0001 ose ≈ 1000. Shpërndarja e raportit ([`value_fund_ratio.csv`](../reports/outliers/value_fund_ratio.csv)) e tregon qartë:

  | Raporti vlerë fituese / fond | Procedura |
  |---|---|
  | 0.1 – 3.2 (zona normale) | 194,365 (96.3%) |
  | 10 – 100 | 204 |
  | **316 – 1,000** (vlerë e shënuar në lekë, fondi në mijëra, ose anasjelltas) | **1,340** |
  | ≥ 100 gjithsej | 1,614 |
  | ≤ 1/100 | 4,323 |

  Asnjë fitues nuk fiton realisht me 1,000 herë fondin, dhe as me 1% të tij. Kulmi te saktësisht ×1000 tregon gabim njësie. Pa këtë rregull, këto procedura do të dilnin "e vërtetë por e rrallë", pra si zbulime jo të sakta në drejtimin tjetër, ku gabimi merret për vlerë reale. Rregulli i përket edhe pjesës së shumave (5,178 rastet "vlera mbi fondin"), prandaj duhet të përdoret e njëjta logjikë edhe aty.
- **Globalisht dhe brenda llojit të procedurës**, njësoj si te univariantja. Llojet me më pak se 1,000 rreshta përdorin flag-un global.

| | Procedura |
|---|---|
| Gabime të njohura (shuma/numra) mes 201,837 procedurave | 5,985 |
| Përjashtues globalisht | 13,838 |
| Përjashtues brenda llojit | 14,358 |
| Vetëm globalisht (zbulim jo i saktë nga shkalla) | 1,185 |
| Vetëm brenda llojit (i fshehur nga shkalla globale) | 1,705 |
| **gabim** (përjashtues + gabim i njohur) | 5,985 |
| **e vërtetë por e rrallë** (të dyja e shënojnë) | 6,668 |
| **e pasigurt** (vetëm njëra e shënon) | 2,890 |

Të **5,985** gabimet e njohura dalin përjashtuese edhe nga Mahalanobis (100%), pra metoda i gjen gabimet që dihen pa iu thënë paraprakisht.

**Interpretimi i numrit të përjashtuesve:** me shpërndarje normale shumëdimensionale do të prisnim 0.1% mbi prag (~200 procedura), ndërsa gjejmë 6.9%. Kjo **nuk** do të thotë 6.9% gabime. Tregon që të dhënat nuk janë normale: numrat e ofertave janë diskretë, shumat kanë bisht të gjatë edhe pas log-ut dhe `qualified_offer_share` grumbullohet në 0 dhe 1. Prandaj pragu χ² përdoret si **kriter seleksionimi**. Vendimi përfundimtar merret nga kombinimi global/grup dhe nga gabimet e njohura, jo vetëm nga D².

**Cila veti e shtyn përjashtuesin** (veçoria me |z| më të madh, [`multivariate_drivers.csv`](../reports/outliers/multivariate_drivers.csv)): `Vlera_e_fituesit` (4,676), `qualified_offer_share` (3,171), `Fondi_limit` (2,849), `kohezgjatja_e_tenderit` (1,533). Shumat dominojnë, prandaj flag-et e shumave të Semines dhe ky flag multivariant plotësojnë njëri-tjetrin.

**Kontrolli me KNN (metoda e ushtrimeve):** në një mostër prej 20,000 procedurash llogaritet distanca mesatare nga 5 fqinjët më të afërt dhe merret e njëjta pjesë (6.76%) si përjashtuese ([`multivariate_knn_check.csv`](../reports/outliers/multivariate_knn_check.csv)). **42.0%** e përjashtuesve të Mahalanobis i gjen edhe KNN. Nëse metodat do të ishin të pavarura, do të prisnim 6.76%, pra përputhja është ≈6.2 herë më e madhe se rastësia. Korrelacioni Spearman mes D² dhe distancës KNN është 0.49. Dy metoda me ide të ndryshme (distanca nga qendra kundrejt dendësisë lokale) tregojnë kryesisht të njëjtat procedura. Dallimi vjen nga përjashtuesit lokalë, që KNN i gjen e Mahalanobis jo.

### 4.6 Flag-et që i jap për dataset-in final

Skedari `data/processed/outliers_competition_winners.csv` ka të njëjtën renditje rreshtash si `prokurimi_final.csv`:

| Kolona | Vlerat |
|---|---|
| `outlier_status_ofertat_dorezuara`, `outlier_status_ofertat_kualifikuara`, `outlier_status_cpv_count` | gabim / e vërtetë por e rrallë / e pasigurt / bosh |
| `outlier_status_fituesi` | statusi i fituesit (kontrata për fitues dhe NIPT) |
| `nipt_klasa` | klasa e NIPT-it (seksioni 4.3) |
| `outlier_status_konsistenca`, `arsye_konsistenca` | rishikimi i seksionit 4.4 |
| `mahalanobis_d2`, `outlier_status_multivariant` | seksioni 4.5 |

Asnjë rresht nuk fshihet. Analiza vendos vetë çfarë përjashton: p.sh. në eksplorim statistikat llogariten për "të gjitha" dhe "pa gabimet" ([`docs/exploration.md`](exploration.md)).
