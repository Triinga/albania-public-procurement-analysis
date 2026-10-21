# Vlerat dhe fituesit

Kolonat: `Fondi_limit`, `Vlera_e_fituesit`, `Vlera_e_fituesit_ne_lidhjen_e_kontrates`, `Lidhja_e_kontrates_me_TVSH`, `Fituesi`, `NIPT_i_fituesit`

> Të dhënat: 10 skedarët vjetorë **2016–2025** (277,764 procedura). Kodi ekzekutohet nga rrënja e repo-s me `python -m <moduli> <dosja_me_csv>`.
>
> | Hapi | Kodi | Rezultatet |
> |---|---|---|
> | 1. Tipet e të dhënave | [`src/values_winners/data_types.py`](../src/values_winners/data_types.py) | [`data_types.csv`](../reports/values_winners/data_types.csv) |
> | 2. Kualiteti i të dhënave | [`src/values_winners/quality.py`](../src/values_winners/quality.py) | [`quality_checks.csv`](../reports/values_winners/quality_checks.csv), [`shared_references.csv`](../reports/values_winners/shared_references.csv), [`invalid_nipt.csv`](../reports/values_winners/invalid_nipt.csv), [`winner_inconsistencies.csv`](../reports/values_winners/winner_inconsistencies.csv), [`winner_names.csv`](../reports/values_winners/winner_names.csv) |
> | 3. Pastrimi | [`src/values_winners/cleaning.py`](../src/values_winners/cleaning.py) | [`cleaning_summary.csv`](../reports/values_winners/cleaning_summary.csv) |
> | 4. Vlerat e zbrazëta | [`src/values_winners/missing_values.py`](../src/values_winners/missing_values.py) | [`missing_summary.csv`](../reports/values_winners/missing_summary.csv), [`missing_by_year.csv`](../reports/values_winners/missing_by_year.csv), [`missing_winner_by_cancellation.csv`](../reports/values_winners/missing_winner_by_cancellation.csv), [`missing_fund_by_procedure_type.csv`](../reports/values_winners/missing_fund_by_procedure_type.csv), [`missing_value_vs_winner.csv`](../reports/values_winners/missing_value_vs_winner.csv), [`missing_strategies.csv`](../reports/values_winners/missing_strategies.csv) |
>
> Të dhënat e pastruara ruhen te `data/processed/` (jashtë git-it).

## 1. Tipet e të dhënave

**Objekti** i të dhënave është një procedurë prokurimi (tender). Çdo rresht është një procedurë; kolonat e mëposhtme janë atributet e saj që lidhen me vlerat dhe fituesin.

| Atributi | Përshkrimi | Kategoria | Tipi | Diskret / i vazhdueshëm | Tipi në CSV | Vlera unike | Shembuj |
|---|---|---|---|---|---|---|---|
| `Fondi_limit` | Vlera maksimale e parashikuar për procedurën (lekë) | Numerik | Ratio | I vazhdueshëm | tekst | 102,064 | `741,600.00` |
| `Vlera_e_fituesit` | Vlera e ofertës fituese (lekë) | Numerik | Ratio | I vazhdueshëm | tekst | 70,706 | `390,000.00` |
| `Vlera_e_fituesit_ne_lidhjen_e_kontrates` | Vlera e kontratës së lidhur (lekë) | Numerik | Ratio | I vazhdueshëm | tekst | 37,018 | `2,252,232.00` |
| `Lidhja_e_kontrates_me_TVSH` | A përfshin kontrata TVSH | Kategorik | Binar | Diskret | tekst | 2 | `Jo`, `Po` |
| `Fituesi` | Emri i operatorit ekonomik fitues | Kategorik | Nominal | Diskret | tekst | 8,269 | `ALTEC SHPK` |
| `NIPT_i_fituesit` | Numri unik i identifikimit të fituesit | Kategorik | Nominal (identifikues) | Diskret | tekst | 8,305 | `K57923807W` |

**Pse këto tipe:**
- Vlerat në lekë janë **ratio**: kanë zero absolute (0 lekë do të thotë mungesë vlere), prandaj raportet kanë kuptim (p.sh. një fond është dy herë më i madh se tjetri). Janë **të vazhdueshme**, sepse mund të marrin çdo vlerë, edhe me presje dhjetore.
- **TVSH** ka vetëm dy vlera (Po/Jo), pra është **binar**. Është **simetrik**, sepse të dyja vlerat kanë rëndësi njësoj.
- **Fituesi** dhe **NIPT** janë **nominale**: janë emra/kode pa renditje. NIPT-i është **identifikues**: çdo vlerë i përket një kompanie, prandaj nuk përdoret si veti në analizë, por për të lidhur dhe njësuar fituesit.

**Tipi në CSV nuk përputhet me tipin real:** të gjitha kolonat ruhen si **tekst**. Vlerat numerike shkruhen me presje si ndarës i mijësheve (`"741,600.00"`) dhe TVSH si `Po`/`Jo`. Konvertimi në tipin e saktë bëhet në hapin e pastrimit.

## 2. Kualiteti i të dhënave

Në Pjesën I problemet vetëm **identifikohen dhe dokumentohen**. Asnjë rresht nuk ndryshohet ose fshihet këtu: pastrimi bëhet në hapin e pastrimit, ndërsa vlerat e pamundura dhe përjashtuesit trajtohen në Pjesën II. Kontrollet ndahen sipas dimensioneve të kualitetit nga leksioni (duplikatet, kompletësia, interpretueshmëria/formati, saktësia, konsistenca).

Për kontrollin e duplikateve lexohen të 21 kolonat. Kolona `Anulluar` (nga pjesa e procedurave dhe konkurrencës) përdoret vetëm për kontrollin "procedurë e anuluar me fitues".

### 2.1 Duplikatet (unike)

| Kontrolli | Rreshta | % |
|---|---|---|
| Rreshta krejtësisht të njëjtë (të 21 kolonat) | 0 | 0.00 |
| `Numri_i_references` i përdorur nga më shumë se një procedurë | 14 (7 referenca) | 0.01 |
| Nga këto: e njëjta referencë, fitues i ndryshëm | 10 | 71.4 e tyre |

**Vërejtje:**
- Nuk ka **asnjë rresht të dyfishtë**: secila procedurë shfaqet vetëm një herë në 10 vitet.
- **7 numra reference** përdoren nga dy procedura secili. Nuk janë kopje: procedurat i përkasin autoriteteve të ndryshme dhe kanë fond e fitues të ndryshëm (p.sh. `REF-20571-09-19-2024`: Spitali Skrapar dhe Agjencia Kombëtare e Planifikimit të Territorit). Pra `Numri_i_references` **nuk është çelës plotësisht unik**. Kur bashkohen tabelat, procedura duhet identifikuar me referencën bashkë me autoritetin. Lista: [`shared_references.csv`](../reports/values_winners/shared_references.csv).

### 2.2 Kompletësia

| Kolona | Mungon | % |
|---|---|---|
| `Fondi_limit` | 25,564 | 9.2 |
| `Vlera_e_fituesit` | 57,382 | 20.7 |
| `Vlera_e_fituesit_ne_lidhjen_e_kontrates` | 226,259 | **81.5** |
| `Lidhja_e_kontrates_me_TVSH` | 0 | 0.0 |
| `Fituesi` | 53,894 | 19.4 |
| `NIPT_i_fituesit` | 53,880 | 19.4 |

**Vërejtje:** Të gjitha kolonat, përveç TVSH-së, kanë vlera që mungojnë; `Vlera_e_fituesit_ne_lidhjen_e_kontrates` është pothuajse bosh. Analiza e hollësishme e mungesave dhe strategjia e trajtimit bëhen në hapin e vlerave të zbrazëta.

### 2.3 Formati (interpretueshmëria)

| Kontrolli | Rreshta | % |
|---|---|---|
| Shumat jo në formatin APP `1,234.56` (të tri kolonat) | 0 | 0.00 |
| `NIPT_i_fituesit` me hapësira/rreshta të rinj (`\n`) tepër | 7,946 | 3.55 |
| `Fituesi` me hapësira/rreshta të rinj tepër | 21,523 | 9.61 |
| Disa fitues/NIPT në një qelizë (fitues të përbashkët, konsorcium) | 169 | 0.08 |
| NIPT i vetëm që nuk është në formatin shqiptar `K12345678A` | 244 | 0.11 |

**Vërejtje:**
- Shumat janë të gjitha në të njëjtin format tekst (`"741,600.00"`). Konvertimi në numër (heqja e presjes) funksionon për të gjitha vlerat.
- Shumica e NIPT-eve "të pavlefshme" janë në fakt të sakta, por kanë `\n` ose hapësira në fund (p.sh. `'K31503045V\n'`). Pas heqjes së tyre mbeten vetëm **244 rreshta** (79 NIPT të ndryshëm) jashtë formatit shqiptar. Këta janë kryesisht **kompani të huaja** me numër TVSH të vendit të tyre (p.sh. `SI24635812` Slloveni, `HR33116950552` Kroaci), plus disa gabime shtypi (p.sh. `21406043R`, `L61727452J-OE`). Lista: [`invalid_nipt.csv`](../reports/values_winners/invalid_nipt.csv).
- **Konsorciumet** ruhen si disa emra dhe NIPT në të njëjtën qelizë, të ndarë me `\n`. Në pastrim duhet vendosur nëse ndahen në disa fitues apo mbahen si një fitues i përbashkët.

### 2.4 Saktësia (vlera logjikisht të pamundura)

| Kolona | Kontrolli | Rreshta | % e vlerave |
|---|---|---|---|
| `Fondi_limit` | = 0 | 13,329 | 5.29 |
| `Fondi_limit` | mes 0 dhe 1 lek | 3,394 | 1.35 |
| `Vlera_e_fituesit` | = 0 | 37 | 0.02 |
| `Vlera_e_fituesit` | mes 0 dhe 1 lek | 19 | 0.01 |
| `Vlera_e_fituesit_ne_lidhjen_e_kontrates` | = 0 | 112 | 0.22 |
| `Vlera_e_fituesit_ne_lidhjen_e_kontrates` | mes 0 dhe 1 lek | 6 | 0.01 |
| `Vlera_e_fituesit` | mbi fondin limit (fondi > 0) | 8,571 | 4.18 |
| `Fondi_limit` | fondi 0, por ka vlerë fituese | 13,234 | 99.29 e fondeve 0 |

**Vërejtje:**
- **Fondi 0 ose 1 lek** nuk është fond real. Pothuajse të gjitha procedurat me fond 0 (99.3%) kanë vlerë fituese, pra fondi ka shumë gjasa të mos jetë publikuar, ose 0/1 është përdorur si **vlerë e paracaktuar** (si "1 janar" te datëlindjet në leksion). Këto janë **mungesa të maskuara** (*disguised missing data*), jo vlera të vërteta.
- **Vlera e fituesit mbi fondin limit** nuk duhet të ndodhë, sepse fondi limit është vlera maksimale e lejuar.
- Këto raste vetëm identifikohen këtu. Trajtimi i tyre (fshirje, zëvendësim, flag) i takon **Pjesës II**.

### 2.5 Konsistenca

| Kontrolli | Rreshta | % |
|---|---|---|
| Procedurë e anuluar (`Anulluar = Po`) me fitues | 27,707 | 37.7 e të anuluarave |
| Procedurë e anuluar me vlerë fituese | 27,618 | 37.6 e të anuluarave |
| NIPT pa emër fituesi | 14 | 0.01 |
| Vlera në kontratë ≠ vlera e fituesit (kur ekzistojnë të dyja) | 26,749 | 51.9 |
| Emra fituesish me disa NIPT | 30 emra | – |
| NIPT me emrin e shkruar në disa mënyra | 861 NIPT | – |

**Vërejtje:**
- Mbi një e treta e procedurave të anuluara kanë fitues dhe vlerë fituese. Ka gjasa që anulimi të ketë ndodhur **pas** shpalljes së fituesit (p.sh. pas ankimit). Për analizat e vlerës, këto procedura nuk duhet të numërohen si kontrata të lidhura. Kjo koordinohet me pjesën e procedurave dhe konkurrencës (kolona `Anulluar`).
- Vlera në kontratë ndryshon nga vlera e fituesit te gjysma e rasteve. Kjo mund të jetë normale (negociata, TVSH, kontrata në disa lote), prandaj s'është domosdoshmërisht gabim. Nevojitet kontroll para se të mbahet vetëm njëra kolonë.
- **Emrat e fituesve janë jokonsistentë.** I njëjti NIPT shfaqet me emrin e shkruar në disa mënyra (861 NIPT), kryesisht nga hapësirat dhe `\n`. Disa emra (30) kanë disa NIPT, p.sh. persona fizikë me të njëjtin emër ose kompani të ndryshme me emër të njëjtë. Shembujt: [`winner_inconsistencies.csv`](../reports/values_winners/winner_inconsistencies.csv).
- Numri i emrave unikë bie nga **8,269** (bruto) në **7,438** pas heqjes së hapësirave dhe në **7,422** pas normalizimit (shkronja të mëdha, pa pikësim). Prandaj **NIPT-i** (i pastruar) duhet të jetë çelësi për identifikimin e fituesit, jo emri. Njësimi i fituesve bëhet në hapin e pastrimit.

## 3. Pastrimi

Pastrimi rregullon problemet e **formatit** dhe të **konsistencës** që u gjetën te kualiteti. Vlerat logjikisht të pamundura (p.sh. vlera e fituesit mbi fondin) **nuk ndryshohen** këtu: ato i takojnë Pjesës II.

| Kolona | Hapi | Para | Pas |
|---|---|---|---|
| `Fondi_limit`, `Vlera_e_fituesit`, `Vlera_e_fituesit_ne_lidhjen_e_kontrates` | Tekst (`"741,600.00"`) → numër | tekst | `float` (të gjitha vlerat u konvertuan, asnjë nuk humbi) |
| `Lidhja_e_kontrates_me_TVSH` | `Po`/`Jo` → boolean | `Jo` 251,197 · `Po` 26,567 | `False` 251,197 · `True` 26,567 |
| `NIPT_i_fituesit` | Heqja e hapësirave dhe `\n`, shkronja të mëdha | 8,305 të ndryshëm | **7,444** |
| `Fituesi` | Heqja e hapësirave dhe `\n`, shkronja të mëdha, **një emër për çdo NIPT** | 8,269 të ndryshëm | **7,403** |

**Vendimet:**
- **Fitues të përbashkët (konsorciume):** emrat dhe NIPT-et që ishin në rreshta të veçantë brenda qelizës bashkohen me ` | ` (p.sh. `ALBANIAN TELECOMMUNICATIONS UNION | ABISSNET | ...`). Mbahen si **një fitues i përbashkët**, sepse kontrata është fituar bashkërisht.
- **Një emër për çdo NIPT:** kur i njëjti NIPT shfaqet me emra të shkruar ndryshe, merret emri që përdoret më shpesh me atë NIPT. Pas pastrimit, **asnjë NIPT nuk ka më shumë se një emër** (para pastrimit: 861).
- Emrat që kanë disa NIPT (p.sh. persona fizikë me të njëjtin emër) **nuk bashkohen**, sepse janë subjekte të ndryshme. Prandaj ka pak më shumë NIPT (7,444) se emra (7,403).
- NIPT-et e huaja (p.sh. `SI24635812`) mbahen siç janë, sepse janë të vlefshme në vendin e tyre.

## 4. Vlerat e zbrazëta

### 4.1 Identifikimi

| Kolona | Mungon (bruto) | % | Mungon (me mungesat e maskuara) | % |
|---|---|---|---|---|
| `Fondi_limit` | 25,564 | 9.20 | **42,287** | **15.22** |
| `Vlera_e_fituesit` | 57,382 | 20.66 | 57,382 | 20.66 |
| `Vlera_e_fituesit_ne_lidhjen_e_kontrates` | 226,259 | 81.46 | 226,259 | 81.46 |
| `Lidhja_e_kontrates_me_TVSH` | 0 | 0.00 | 0 | 0.00 |
| `Fituesi` | 53,894 | 19.40 | 53,894 | 19.40 |
| `NIPT_i_fituesit` | 53,880 | 19.40 | 53,880 | 19.40 |

**Mungesat e maskuara:** fondet **0 ose ≤ 1 lek** (16,723) nuk janë shuma reale, por vlera të paracaktuara kur fondi nuk publikohet. Ato shënohen si **mungesë** (`NaN`). Me to, mungesa e fondit rritet nga 9.2% në 15.2%.

### 4.2 Nga vijnë mungesat

**Sipas vitit (%):**

| Viti | Procedura | Fondi_limit | Vlera_e_fituesit | Vlera në kontratë | Fituesi | NIPT |
|---|---|---|---|---|---|---|
| 2016 | 33,375 | 12.4 | 19.8 | 85.9 | 19.8 | 19.8 |
| 2017 | 31,769 | 9.5 | 17.6 | **47.7** | 17.7 | 17.7 |
| 2018 | 33,880 | 12.8 | 22.6 | 80.4 | **26.8** | **26.8** |
| 2019 | 28,313 | 19.0 | 18.7 | 84.9 | 23.2 | 23.2 |
| 2020 | 23,670 | 11.3 | 18.3 | 83.8 | 18.6 | 18.6 |
| 2021 | 22,653 | 13.0 | 19.7 | 86.4 | 16.0 | 15.9 |
| 2022 | 26,034 | 17.7 | 24.5 | 88.2 | 19.1 | 19.1 |
| 2023 | 25,137 | 19.9 | 20.9 | 88.8 | 16.4 | 16.4 |
| 2024 | 27,466 | 19.6 | 24.0 | 87.2 | 18.0 | 18.0 |
| 2025 | 25,467 | 19.0 | 20.6 | 88.5 | 15.6 | 15.6 |

**Fituesi sipas anulimit:**

| Procedura | Gjithsej | Pa fitues | % |
|---|---|---|---|
| Jo e anuluar | 204,341 | 8,178 | 4.0 |
| E anuluar | 73,423 | 45,716 | **62.3** |

**Fondi sipas llojit të procedurës** (llojet kryesore):

| Lloji i procedurës | Procedura | Pa fond | % |
|---|---|---|---|
| Small Value | 183,329 | 27,330 | 14.9 |
| Purchase Tickets | 17,766 | 14,842 | **83.5** |
| Negotiated without Notice | 5,307 | 44 | 0.8 |
| Open Local | 21,980 | 43 | 0.2 |
| Request for Proposals | 25,549 | 10 | 0.0 |

**Vlera e fituesit krahasuar me fituesin:**

| Rasti | Rreshta |
|---|---|
| Ka fitues, mungon vlera | 6,583 |
| Mungon fituesi, ka vlerë | 3,095 |
| Mungojnë të dyja | 50,799 |

**Vërejtje (lloji i mungesës):**
- **Fituesi/NIPT:** 84.8% e procedurave pa fitues janë **të anuluara**. Mungesa ka shpjegim (procedura nuk përfundoi me fitues), pra është **MAR** (*Missing At Random*, e lidhur me një kolonë tjetër), jo gabim.
- **Fondi:** mungesa përqendrohet te **blerja e biletave** (83.5%), ku fondi zakonisht nuk publikohet. Edhe kjo është **MAR**.
- **Vlera e fituesit:** në shumicën e rasteve mungon bashkë me fituesin (50,799). Vetëm 6,583 procedura kanë fitues pa vlerë.
- **Vlera në kontratë:** mungon te 81.5%, por te 2017 vetëm te 47.7%. Mungesa varet nga mënyra e plotësimit të fushës ndër vite.
- Mungesat sipas vitit janë të qëndrueshme; nuk ka një vit që i shkakton ato.

### 4.3 Krahasimi i strategjive

| Kolona | Strategjia | Rreshta që mbeten | Mbeten bosh | Mediana | Mesatarja |
|---|---|---|---|---|---|
| `Fondi_limit` | Origjinali (me `NaN`) | 277,764 | 42,287 | 390,000 | 9,150,130 |
| | Fshirje e rreshtave | 235,477 | 0 | 390,000 | 9,150,130 |
| | Imputim me medianë | 277,764 | 0 | 390,000 | 7,816,482 |
| | Imputim me medianë sipas llojit të procedurës | 277,764 | 0 | 263,277 | 7,789,469 |
| | `NaN` + flag për mungesën | 277,764 | 42,287 | 390,000 | 9,150,130 |
| `Vlera_e_fituesit` | Origjinali (me `NaN`) | 277,764 | 57,382 | 234,900 | 163,343,337 |
| | Fshirje e rreshtave | 220,382 | 0 | 234,900 | 163,343,337 |
| | Imputim me medianë | 277,764 | 0 | 234,900 | 129,647,507 |
| | Imputim me medianë sipas llojit të procedurës | 277,764 | 0 | 250,000 | 131,019,235 |
| | `NaN` + flag për mungesën | 277,764 | 57,382 | 234,900 | 163,343,337 |

**Çfarë tregon krahasimi:**
- **Fshirja** humb 15–21% të procedurave. Për analizat e vlerës kjo do të hiqte kryesisht procedurat e anuluara dhe blerjet e biletave, pra e shtrembëron pamjen e prokurimit.
- **Imputimi me medianë** mbush të gjitha vlerat, por e ul mesataren dhe krijon shuma artificiale për procedura që nuk kanë pasur fond ose fitues. Me medianë sipas llojit të procedurës, mediana e fondit ndryshon (390,000 → 263,277), sepse shumica e mungesave janë te procedurat e vogla.
- **`NaN` + flag** nuk shpik vlera dhe ruan të gjitha procedurat.

### 4.4 Strategjia e zgjedhur

| Kolona | Trajtimi | Pse |
|---|---|---|
| `Fondi_limit` | 0 / ≤ 1 lek → `NaN`; mbetet `NaN` + flag `Fondi_limit_missing` | Mungesa ka shpjegim (bileta, fond i papublikuar); një fond i shpikur do të prishte llogaritjen e kursimit |
| `Vlera_e_fituesit` | Mbetet `NaN` + flag `Vlera_e_fituesit_missing` | Shumica mungon sepse nuk ka fitues; imputimi do të krijonte kontrata që nuk ekzistojnë |
| `Fituesi`, `NIPT_i_fituesit` | Mbetet `NaN` + flag `Fituesi_missing` | Procedura pa fitues (kryesisht të anuluara) janë informacion, jo gabim |
| `Vlera_e_fituesit_ne_lidhjen_e_kontrates` | Nuk imputohet | Mungon te 81.5%; kandidate për heqje te zgjedhja e vetive |
| `Lidhja_e_kontrates_me_TVSH` | – | Nuk ka mungesa |

Rezultati ruhet te `data/processed/values_winners_missing_handled.csv`.
