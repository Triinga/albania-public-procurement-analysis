# Vlerat dhe fituesit

Kolonat: `Fondi_limit`, `Vlera_e_fituesit`, `Vlera_e_fituesit_ne_lidhjen_e_kontrates`, `Lidhja_e_kontrates_me_TVSH`, `Fituesi`, `NIPT_i_fituesit`

> Të dhënat: 10 skedarët vjetorë **2016–2025** (277,764 procedura). Kodi ekzekutohet nga rrënja e repo-s me `python -m <moduli> <dosja_me_csv>`.
>
> | Hapi | Kodi | Rezultatet |
> |---|---|---|
> | 1. Tipet e të dhënave | [`src/values_winners/data_types.py`](../src/values_winners/data_types.py) | [`data_types.csv`](../reports/values_winners/data_types.csv) |
> | 2. Kualiteti i të dhënave | [`src/values_winners/quality.py`](../src/values_winners/quality.py) | [`quality_checks.csv`](../reports/values_winners/quality_checks.csv), [`shared_references.csv`](../reports/values_winners/shared_references.csv), [`invalid_nipt.csv`](../reports/values_winners/invalid_nipt.csv), [`winner_inconsistencies.csv`](../reports/values_winners/winner_inconsistencies.csv), [`winner_names.csv`](../reports/values_winners/winner_names.csv) |

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
