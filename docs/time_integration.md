# Koha dhe Integrimi

Kolonat: `Data_e_publikimit`, `Data_e_hapjes`, `Data_e_mbylljes`, `Numri_i_references`, `viti`

> Të dhënat: 10 skedarët vjetorë **2016–2025** (277,764 procedura).
> Kodi: [`src/time_integration/`](../src/time_integration/) · Rezultati: [`reports/time_integration/`](../reports/time_integration/)

## 1. Periudha e zgjedhjeve

Integrimi përfshin zgjedhjet kombëtare në Shqipëri për analizën e prokurimit gjatë periudhave elektorale. Burimi: [Komisioni Qendror i Zgjedhjeve (KQZ)](https://kqz.gov.al).

| Viti | Lloji | Data |
|------|-------|------|
| 2015 | Vendore | 21 Qershor |
| 2017 | Parlamentare | 25 Qershor |
| 2019 | Vendore | 30 Qershor |
| 2021 | Parlamentare | 25 Prill |
| 2023 | Vendore | 14 Maj |
| 2025 | Parlamentare | 11 Maj |

- Zgjedhjet e 2015 janë para periudhës së të dhënave, por mbahen që procedurat e fillimit të 2016 ta kenë zgjedhjet më të afërta të sakta.
- Zgjedhjet e pjesshme (p.sh. për kryetarin e Kukësit më 24.09.2023) nuk përfshihen, sepse nuk prekin gjithë vendin.
- Presidenti zgjidhet nga Kuvendi, prandaj nuk ka zgjedhje presidenciale me votë popullore.

## 2. Tipet e të dhënave

| Atributi | Përshkrimi | Kategoria | Tipi | Vlera unike |
|---|---|---|---|---|
| `Data_e_publikimit` | Data e publikimit të procedurave | Kategorik | Datetime | 3,320 |
| `Data_e_hapjes` | Data e hapjes të kërkesave | Kategorik | Datetime | 3,353 |
| `Data_e_mbylljes` | Data e mbylljes të kërkesave | Kategorik | Datetime | 3,193 |
| `Numri_i_references` | Numri referues i procedurave | Numerik | Count | 277,757 |

## 2.1 Kualiteti i të dhënave

Kontrollet e cilësisë identifikojnë probleme në tre dimensione:

### Kompletësia (Missing Values)
- `Data_e_publikimit`: 0 mungesa (0%)
- `Data_e_hapjes`: 169 mungesa (0.06%)
- `Data_e_mbylljes`: 1,092 mungesa (0.39%)
- `Numri_i_references`: 0 mungesa (0%)

### Formati (Vlefshmëria e të dhënave)
- Të gjitha datat janë në format të duhur DD.MM.YYYY ✅
- Nuk ka rastra të panevojshme ose shenja të gabimit

### Saktësia (Konsistenca logjike)

| Kontrolli | Rreshta | % | Rëndësia |
|---|---|---|---|
| Data e hapjes PARA publikimit | 7,170 | 2.58% | 🔴 Serioz |
| Mbyllja PARA hapjes | 5 | 0.00% | 🟢 Minimal |
| Mbyllja PARA publikimit | 245 | 0.09% | 🟢 Minimal |
| Data në të ardhmen | 0 | 0% | ✅ Në rregull |
| Hapje = Mbyllje (e njëjta ditë) | 16,037 | 5.8% | 🟡 Mesatar |

**Gjetje kryesore:** 7,170 procedure (2.58%) kanë data të hapjes para datës së publikimit - logjikisht të pamundur. Këto trajtohen te pastrimi (2.2).

## 2.2 Pastrimi

Problemet e saktësisë nga 2.1 rregullohen pa fshirë asnjë rresht. Për të vendosur **cila** nga dy datat në konflikt është e gabuar, përdoret data e regjistrimit të procedurës që ndodhet në fund të `Numri_i_references` (`REF-xxxxx-MM-DD-YYYY`). Kjo datë nuk është asnjëherë pas datës së publikimit (0 raste), pra është pika më e besueshme e fillimit.

| Problemi | Rreshta | Cila datë është e gabuar | Veprimi | Flamuri |
|---|---|---|---|---|
| Hapja para publikimit, por pas regjistrimit | 7,110 | Publikimi (i regjistruar me vonesë, zakonisht 1–3 ditë, kryesisht 2016–2020) | `Data_e_publikimit` = `Data_e_hapjes` | `Data_e_publikimit_corrected` |
| Hapja para regjistrimit ose pas mbylljes | 65 | Hapja (p.sh. hapje 11 vjet para publikimit) | Bëhet mungesë, plotësohet si te 2.3 | `Data_e_hapjes_invalid` |
| Mbyllja para regjistrimit ose pas datës së eksportit (19.10.2026) | 6 | Mbyllja (gabime shtypi në muaj/vit, p.sh. `2100-11-02` në vend të `2017-11-02`, `2007` në vend të `2017`) | Bëhet mungesë, plotësohet si te 2.3 | `Data_e_mbylljes_invalid` |

Kontrollet e renditjes së datave para dhe pas pastrimit (pas plotësimit të mungesave):

| Kontrolli | Para | Pas |
|---|---|---|
| Publikimi para regjistrimit | 0 | 0 |
| Hapja para publikimit | 7,170 | **0** |
| Mbyllja para hapjes | 5 | **0** |
| Mbyllja para publikimit | 263 | **0** |
| Mbyllja pas datës së eksportit | 1 | **0** |
| Kohëzgjatja e tenderit > 365 ditë | 5 | 4 |

- Kohëzgjatja maksimale bie nga 30,316 në 440 ditë. 4 tenderat mbi 365 ditë (405–440 ditë) janë të mundshëm dhe mbahen.
- Hapja dhe mbyllja në të njëjtën ditë (16,037) nuk konsiderohet gabim, sepse ndodh te procedurat me vlerë të vogël, dhe mbetet e pandryshuar.
- 276 procedura kanë datë publikimi në vitin pasues të skedarit (p.sh. regjistruar më 30.12.2016, publikuar më 04.01.2017). Kjo nuk është gabim, prandaj `year` mbetet viti i skedarit.
- 7 referenca përdoren nga dy procedura të autoriteteve të ndryshme (shih [values_winners.md](values_winners.md)). Nuk janë kopje dhe nuk fshihen.
- Kodi: `python -m src.time_integration.cleaning`

## 2.3 Vlerat e zbrazëta

Asnjë rresht nuk fshihet. Datat që mungojnë plotësohen me vlerësim logjik dhe çdo vlerë e plotësuar shënohet me kolonë `*_imputed`.

| Kolona | Mungesa | Metoda |
|---|---|---|
| `Data_e_hapjes` | 169 | Data e publikimit + mediana e vonesës publikim→hapje e vitit përkatës |
| `Data_e_mbylljes` | 1,092 | Data e hapjes + mediana e kohëzgjatjes hapje→mbyllje e vitit përkatës |
| `Data_e_publikimit`, `Numri_i_references` | 0 | Nuk kërkohet veprim |

- Mediana llogaritet sipas vitit (afatet ndryshojnë nga viti në vit) dhe përdor vetëm diferenca ≥ 0, ndaj data e plotësuar nuk mund të dalë para datës nga e cila rrjedh. Nëse një vit nuk ka diferenca të vlefshme, përdoret mediana globale.
- Një datë hapjeje e plotësuar nuk mund të dalë pas një date mbylljeje të njohur; në atë rast merr datën e mbylljes.
- E njëjta metodë plotëson edhe datat që pastrimi (2.2) i shënon si të gabuara.
- Pas plotësimit mbeten 0 mungesa dhe 277,764 rreshta (asnjë i fshirë).
- Kodi: `python -m src.time_integration.missing_values`

## 2.4 Krijimi i vetive kohore, zgjedhore dhe COVID

Vetitë krijohen mbi datat e pastruara (2.2) dhe të plotësuara (2.3), pa fshirë asnjë rresht (277,764). Pas pastrimit, diferencat në ditë nuk janë asnjëherë negative.

| Vetia | Grupi | Përkufizimi |
|---|---|---|
| `muaji_publikimit` | Kohore | Muaji i `Data_e_publikimit` (1–12) |
| `tremujori_publikimit` | Kohore | Tremujori i `Data_e_publikimit` (1–4) |
| `dita_e_javes_publikimit` | Kohore | Dita e javës (0 = e hënë, 6 = e diel) |
| `ditet_publikim_hapje` | Kohore | `Data_e_hapjes` − `Data_e_publikimit` (ditë) |
| `kohezgjatja_e_tenderit` | Kohore | `Data_e_mbylljes` − `Data_e_hapjes` (ditë) |
| `zgjedhjet_me_te_aferta` | Zgjedhore | Data e zgjedhjeve më afër datës së publikimit |
| `ditet_nga_zgjedhjet` | Zgjedhore | `Data_e_publikimit` − `zgjedhjet_me_te_aferta` (< 0 = para zgjedhjeve, > 0 = pas) |
| `periudha_covid` | COVID | Para COVID (< 11.03.2020), Gjatë COVID (11.03.2020 – 31.12.2021), Pas COVID |

**Gjetjet kryesore:**
- `ditet_publikim_hapje`: mediana 0 ditë (hapja zakonisht ditën e publikimit), 75% ≤ 1 ditë, maksimumi 213 ditë.
- `kohezgjatja_e_tenderit`: mediana 1 ditë, 75% ≤ 9 ditë, maksimumi 440 ditë (para pastrimit 30,316).
- `ditet_nga_zgjedhjet`: vlerat shkojnë nga −374 deri në 486 ditë, mediana −16; zgjedhjet mbahen afërsisht çdo 2 vjet (vendore dhe parlamentare me radhë), ndaj çdo procedurë është brenda ~1 viti nga zgjedhjet më të afërta.
- `periudha_covid`: 2020 ndahet në 4,103 procedura para dhe 19,567 gjatë COVID; 2021 është tërësisht gjatë COVID. Pak rreshta (p.sh. 3 në 2017) kanë datë publikimi jashtë vitit të skedarit.
- Janari dhe gushti kanë vazhdimisht më pak procedura; tetori dhe dhjetori më shumë.

Diskretizimi dhe binarizimi i këtyre vetive bëhen në hapin pasues.

- Kodi: `python -m src.time_integration.features`
- Dataset-i me vetitë ruhet në `data/processed/time_features.csv` (jo në git).

## 3. Raportet e gjeneruara

- **missing_summary.csv**: Mungesat para/pas plotësimit dhe numri i vlerave të plotësuara
- **missing_by_year.csv**: Përqindja e mungesave sipas vitit
- **data_types.csv**: Tipet e të dhënave për çdo kolonë
- **integration_summary.csv**: Përmbledhja e 277,764 procedurave
- **elections_mapping.csv**: Procedurat e publikuara ditën e zgjedhjeve (9 total)
- **quality_checks.csv**: Kontrollet e cilësisë (17 kontrolle)
- **cleaning_summary.csv**: Problemet e datave, veprimi dhe numri i rreshtave të rregulluar
- **date_order_checks.csv**: Kontrollet e renditjes së datave para dhe pas pastrimit
- **features_summary.csv**: Vetitë e krijuara, përkufizimi dhe numri i vlerave negative
- **features_profile.csv**: Shpërndarja e vetive në ditë (mesatarja, kuartilet, min/max)
- **covid_periods_by_year.csv**: Procedurat sipas periudhës COVID dhe vitit
- **procedures_by_month.csv**: Procedurat sipas muajit të publikimit dhe vitit