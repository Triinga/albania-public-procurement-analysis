# Koha dhe Integrimi

Kolonat: `Data_e_publikimit`, `Data_e_hapjes`, `Data_e_mbylljes`, `Numri_i_references`, `viti`

> Të dhënat: 10 skedarët vjetorë **2016–2025** (277,764 procedura).
> Kodi: [`src/time_integration/`](../src/time_integration/) · Rezultati: [`reports/time_integration/`](../reports/time_integration/)

## 1. Periudha e zgjedhjeve

Integrimi përfshin zgjedhjet kombëtare në Shqipëri për analizën e prokurimit gjatë periudhave elektorale. Burimi: [Komisioni Qendror i Zgjedhjeve (KQZ)](https://kqz.gov.al/subjektet-zgjedhore).

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
| `Data_e_publikimit` | Data e publikimit të procedurës | Numerik | Interval (datë) | 3,320 |
| `Data_e_hapjes` | Data e hapjes së procedurës | Numerik | Interval (datë) | 3,353 |
| `Data_e_mbylljes` | Data e mbylljes së procedurës | Numerik | Interval (datë) | 3,193 |
| `Numri_i_references` | Numri referues i procedurës (`REF-xxxxx-MM-DD-YYYY`) | Kategorik | Nominal (identifikues) | 277,757 |
| `viti` | Viti i skedarit vjetor (nga emri i skedarit, kolona `year`) | Numerik | Interval | 10 |

- **Datat dhe viti janë numerike në shkallë intervale:** diferenca mes dy datave ka kuptim (p.sh. kohëzgjatja e tenderit në ditë), por nuk ka zero absolute, ndaj raporti mes tyre nuk ka kuptim. Në CSV ruhen si tekst `DD.MM.YYYY` dhe konvertohen në datë.
- **`Numri_i_references` është identifikues nominal:** është tekst, nuk numëron asgjë dhe veprimet aritmetike nuk kanë kuptim. Data në fund të tij (data e regjistrimit) përdoret te pastrimi (2.2).

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

**Kontrollet e vetive:**
- Të gjitha vetitë kanë vlerë për çdo rresht (277,764) dhe asnjë diferencë në ditë nuk është negative ([`features_summary.csv`](../reports/time_integration/features_summary.csv)).
- Kufiri i COVID-it ndan vitin 2020 në 4,103 procedura para dhe 19,567 gjatë COVID; 2021 është tërësisht gjatë COVID ([`covid_periods_by_year.csv`](../reports/time_integration/covid_periods_by_year.csv)).

Analiza e shpërndarjes së këtyre vetive (statistikat përmbledhëse, ndryshimet sipas muajve etj.) i takon Pjesës II.

## 2.5 Diskretizimi dhe binarizimi

### Diskretizimi

**`kategoria_e_kohezgjatjes`** (nga `kohezgjatja_e_tenderit`). U krahasuan tri metoda me 5 grupe:

| Metoda | Rezultati | Pse (nuk) përdoret |
|---|---|---|
| Equal width | 277,191 rreshta (99.8%) në grupin e parë (0–88 ditë) | Shpërndarja është shumë e anshme (maksimumi 440, mediana 1), ndaj grupet e tjera janë pothuajse bosh |
| Equal frequency | Vetëm 4 grupe; grupi i parë (0–1 ditë) ka 162,177 rreshta | 53% e tenderave zgjasin saktësisht 1 ditë, kuantilet përsëriten dhe grupet bashkohen |
| **Kufij të zgjedhur** ✅ | Grupe me kuptim dhe të gjitha të populluara | Përdoret |

| Grupi | Ditë | Rreshta |
|---|---|---|
| E njëjta ditë | 0 | 16,076 |
| 1-3 ditë | 1–3 | 182,232 |
| 4-14 ditë | 4–14 | 44,686 |
| 15-30 ditë | 15–30 | 24,344 |
| Mbi 30 ditë | > 30 | 10,426 |

**`afersia_me_zgjedhjet`** (nga `Data_e_publikimit` dhe `zgjedhjet_me_te_aferta`). Dritarja bazohet te **periudha parazgjedhore prej 4 muajsh** para ditës së votimit, kur Kodi Zgjedhor (neni 91, paragrafi 4) kufizon përdorimin e burimeve publike. P.sh. për zgjedhjet e 11.05.2025 kufizimet nisën më 11.01.2025. Muajt llogariten si muaj kalendarikë (jo si numër ditësh). E njëjta gjatësi përdoret pas zgjedhjeve, si periudhë krahasimi.

| Grupi | Data e publikimit |
|---|---|
| Mbi 4 muaj para | Para (zgjedhjet − 4 muaj) |
| Periudha parazgjedhore (4 muaj) | Nga (zgjedhjet − 4 muaj) deri në ditën e votimit, përfshirë |
| Deri 4 muaj pas | Pas ditës së votimit deri në (zgjedhjet + 4 muaj) |
| Mbi 4 muaj pas | Pas (zgjedhjet + 4 muaj) |

Vitet pa zgjedhje (2016, 2018, 2022, 2024) bien pothuajse tërësisht jashtë periudhës parazgjedhore. Përjashtim është 2020: 292 procedura të fundit të dhjetorit janë brenda 4 muajve para zgjedhjeve të 25.04.2021. Shpërndarja sipas vitit: [`election_proximity_by_year.csv`](../reports/time_integration/election_proximity_by_year.csv).

### Binarizimi

| Vetia | Përkufizimi | Rreshta me 1 | % |
|---|---|---|---|
| `gjate_covid` | `periudha_covid` = Gjatë COVID | 42,198 | 15.2 |
| `periudhe_parazgjedhore` | Publikuar në 4 muajt para zgjedhjeve, përfshirë ditën e votimit (neni 91/4) | 47,804 | 17.2 |
| `publikim_ne_fundjave` | Publikuar të shtunën ose të dielën | 2,781 | 1.0 |
| `publikim_ne_dhjetor` | Publikuar në dhjetor (fundi i vitit buxhetor) | 25,623 | 9.2 |
| `hapje_mbyllje_e_njejta_dite` | `kohezgjatja_e_tenderit` = 0 | 16,076 | 5.8 |

Flamujt e pastrimit dhe të plotësimit (`Data_e_publikimit_corrected`, `Data_e_hapjes_invalid`, `Data_e_mbylljes_invalid`, `Data_e_hapjes_imputed`, `Data_e_mbylljes_imputed`) kthehen gjithashtu nga True/False në 1/0.

- Kodi: `python -m src.time_integration.features`
- Dataset-i me vetitë ruhet në `data/processed/time_features.csv` (jo në git).

## 2.6 Mostrimi

Mostra merr **10%** të procedurave (~27,777 nga 277,764), pa zëvendësim dhe me seed fiks (`42`), ndaj çdo ekzekutim jep të njëjtën mostër. U krahasuan tri metoda:

| Metoda | Përshkrimi |
|---|---|
| Rastësore e thjeshtë | 10% e rreshtave zgjidhen rastësisht nga i gjithë dataset-i |
| E shtresëzuar sipas vitit | 10% nga çdo vit |
| **E shtresëzuar sipas vitit dhe afërsisë me zgjedhjet** ✅ | 10% nga çdo kombinim viti × `afersia_me_zgjedhjet` (40 shtresa) |

Një seed i vetëm mund ta favorizojë rastësisht njërën metodë, prandaj secila metodë u përsërit me **50 seed-e** dhe u mat devijimi më i madh nga dataset-i i plotë (në pikë përqindjeje, pp):

| Variabli | Rastësore | Sipas vitit | **Sipas vitit + zgjedhjeve** |
|---|---|---|---|
| `year` | 0.32 | 0.01 | **0.01** |
| `periudha_covid` | 0.32 | 0.06 | **0.05** |
| `afersia_me_zgjedhjet` | 0.31 | 0.32 | **0.00** |
| `periudhe_parazgjedhore` | 0.15 | 0.17 | **0.00** |
| `kategoria_e_kohezgjatjes` | 0.27 | 0.30 | 0.31 |
| `publikim_ne_dhjetor` | 0.14 | 0.15 | 0.12 |
| `hapje_mbyllje_e_njejta_dite` | 0.10 | 0.09 | 0.12 |

*(mesatarja e 50 seed-eve; rasti më i keq gjendet te `sampling_max_deviation.csv`)*

**Zgjedhja:** mostra e shtresëzuar sipas **vitit dhe afërsisë me zgjedhjet**. Ajo ruan saktësisht përqindjen e çdo viti dhe të periudhave zgjedhore, që janë boshti i integrimit (10 vite + zgjedhjet), dhe ruan edhe periudhat COVID. Për variablat jashtë shtresave, të tri metodat kanë luhatje të ngjashme e të vogla (< 0.35 pp mesatarisht), ndaj shtresëzimi nuk humb asgjë. Mesatarja dhe mediana e vetive në ditë mbeten të afërta me dataset-in e plotë (p.sh. kohëzgjatja mesatare 6.04 → 6.12 ditë, mediana 1 → 1).

Funksionet e mostrimit janë të përgjithshme ([`src/common/sampling.py`](../src/common/sampling.py)), që pipeline-i final t'i zbatojë mbi dataset-in e integruar.

- Kodi: `python -m src.time_integration.sampling`
- Mostra ruhet në `data/processed/time_sample.csv` (jo në git).

## 2.7 Dataset-i i integruar

Dataset-i i integruar bashkon në një tabelë kolonat e përgatitura të **të tri pjesëve** të grupit për të 10 vitet (2016–2025), bashkë me integrimin e zgjedhjeve (KQZ) dhe të ndarjeve CPV.

| Pjesa | Përgatitja (kodi i secilit) | Kolona |
|---|---|---|
| Çelësi | `Numri_i_references`, `Autoriteti_kontraktues`, `year` | 3 |
| Vlerat dhe fituesit (Marigona Hamiti) | Pastrimi, vlerat e zbrazëta, vetitë, diskretizimi, binarizimi | 15 |
| Koha dhe integrimi (Semine Muharremi) | Pastrimi i datave, vlerat e zbrazëta, vetitë kohore/zgjedhore/COVID, diskretizimi, binarizimi | 23 |
| Procedura dhe konkurrenca (Tringa Baftiu) | Pastrimi, integrimi CPV, vetitë e konkurrencës | 23 |
| **Gjithsej** | | **64** |

**Si bashkohen pjesët:**
- Të tri pjesët përgatiten nga i njëjti lexim i të dhënave raw, secila me kodin e vet, pa e kopjuar atë. Kështu, një ndryshim te pastrimi i një pjese kalon automatikisht në dataset-in e integruar.
- Një procedurë identifikohet nga **referenca bashkë me autoritetin kontraktues**, sepse referenca vetëm përdoret nga 7 çifte procedurash (shih [values_winners.md](values_winners.md)).
- Bashkimi bëhet mbi vlerat **origjinale** të çelësit. Pjesa e procedurave e pastron emrin e autoritetit (hapësirat), dhe bashkimi mbi emrin e pastruar mund të humbiste përputhje. Në dataset mbahet emri i **pastruar**.
- Çdo bashkim kontrollohet të jetë **një-me-një**, çdo rresht duhet të gjejë çiftin e vet dhe viti duhet të jetë i njëjtë në të tri pjesët.

| Kontrolli | Rezultati |
|---|---|
| Rreshta raw (10 skedarë) | 277,764 |
| Rreshta të integruar | 277,764 |
| Rreshta të humbur ose të dyfishuar | **0** |
| Çelësa të përsëritur | **0** |
| Vitet | 2016–2025 |

Ky dataset nuk përmban ende transformimin dhe PCA-në, që janë hapat e mbetur të pjesës së vlerave dhe fituesve. Ato i shtohen te dataset-i përfundimtar (`prokurimi_final.csv`).

- Kodi: `python -m src.time_integration.integrated_dataset`
- Dataset-i ruhet në `data/processed/prokurimi_integruar.csv` (~155 MB, jo në git).
- Lista e kolonave, me burimin, tipin dhe përqindjen e mungesave: [`integrated_columns.csv`](../reports/time_integration/integrated_columns.csv).

## 3. Raportet e gjeneruara

- **missing_summary.csv**: Mungesat para/pas plotësimit dhe numri i vlerave të plotësuara
- **missing_by_year.csv**: Përqindja e mungesave sipas vitit
- **data_types.csv**: Tipet e të dhënave për çdo kolonë
- **quality_checks.csv**: Kontrollet e cilësisë (17 kontrolle)
- **cleaning_summary.csv**: Problemet e datave, veprimi dhe numri i rreshtave të rregulluar
- **date_order_checks.csv**: Kontrollet e renditjes së datave para dhe pas pastrimit
- **features_summary.csv**: Vetitë e krijuara, përkufizimi dhe numri i vlerave negative
- **covid_periods_by_year.csv**: Procedurat sipas periudhës COVID dhe vitit
- **discretization_duration.csv**: Krahasimi equal width / equal frequency / kufij të zgjedhur për kohëzgjatjen
- **election_proximity_by_year.csv**: Procedurat sipas afërsisë me zgjedhjet dhe vitit
- **binary_summary.csv**: Numri dhe përqindja e vlerave 1 për çdo veti binare
- **sampling_sizes.csv**: Madhësia e çdo mostre dhe seed-i
- **sampling_comparison.csv**: Përqindja e çdo vlere në dataset-in e plotë dhe në secilën mostër
- **sampling_max_deviation.csv**: Devijimi më i madh nga dataset-i i plotë (mesatarja dhe rasti më i keq në 50 seed-e)
- **sampling_numeric.csv**: Mesatarja dhe mediana e vetive në ditë, dataset i plotë kundrejt mostrave
- **integrated_summary.csv**: Kontrollet e dataset-it të integruar (rreshta, çelësa, kolona sipas pjesës)
- **integrated_columns.csv**: Çdo kolonë e dataset-it të integruar me burimin, personin, tipin dhe mungesat
- **integrated_rows_by_year.csv**: Procedurat e dataset-it të integruar sipas vitit