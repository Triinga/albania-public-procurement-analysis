# Detektimi i përjashtuesve (Faza II)

> Kodi: [`src/common/outliers.py`](../src/common/outliers.py) (i përbashkët), [`src/outliers/amounts_time.py`](../src/outliers/amounts_time.py) (Semine) · Ekzekutimi: `python -m src.outliers.amounts_time` · Raportet: [`reports/outliers/`](../reports/outliers/)

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
