# Albania Public Procurement Analysis

Analizë e prokurimit publik në Shqipëri për vitet **2016–2025** (277,764 procedura), e integruar me zgjedhjet kombëtare dhe periudhën COVID-19.

Projekt grupor (Grupi 13) për lëndën **Përgatitja dhe vizualizimi i të dhënave**. Projekti ka 3 faza; ky repository përmban **Fazën I: përgatitjen e të dhënave** (mbledhja, tipet, kualiteti, integrimi, agregimi, mostrimi, pastrimi, vlerat e zbrazëta, krijimi i vetive, diskretizimi, binarizimi, transformimi, zgjedhja e vetive dhe reduktimi i dimensionit me PCA).

Rezultati përfundimtar është **`prokurimi_final.csv`** (277,764 procedura × 84 kolona), i përshkruar te [docs/final_dataset.md](docs/final_dataset.md). Hapat shpjegohen një nga një te notebook-u [notebooks/01_parapercesimi.ipynb](notebooks/01_parapercesimi.ipynb).

## Anëtarët dhe ndarja e punës

| Anëtari | Pjesa | Kolonat | Dokumentimi |
|---|---|---|---|
| Marigona Hamiti | Vlerat dhe fituesit | `Fondi_limit`, `Vlera_e_fituesit`, `Vlera_e_fituesit_ne_lidhjen_e_kontrates`, `Lidhja_e_kontrates_me_TVSH`, `Fituesi`, `NIPT_i_fituesit` | [docs/values_winners.md](docs/values_winners.md) |
| Semine Muharremi | Koha dhe integrimi | `Data_e_publikimit`, `Data_e_hapjes`, `Data_e_mbylljes`, `Numri_i_references`, `viti` | [docs/time_integration.md](docs/time_integration.md) |
| Tringa Baftiu | Procedura dhe konkurrenca | `Autoriteti_kontraktues`, `Objekti_i_prokurimit`, `Lloji_i_procedures`, `Tipi_i_kontrates`, `Lloji_i_marreveshjes_kuader`, `Anulluar`, `Arsyeja_e_anullimit`, `Pezulluar`, ofertat, `Kodet_CPV` | [docs/procedure_competition.md](docs/procedure_competition.md) |

## Mbledhja e të dhënave

### Burimi kryesor: Agjencia e Prokurimit Publik (APP)

| | |
|---|---|
| **Burimi** | Agjencia e Prokurimit Publik e Shqipërisë (APP) |
| **Faqja** | [Eksportimi i procedurave të publikuara](https://www.app.gov.al/eksportimi-i-procedurave-te-publikuara/) |
| **Çfarë u shkarkua** | Një skedar CSV për çdo vit, 2016–2025 (10 skedarë), me 21 kolona për procedurë |
| **Data e eksportit** | 19.10.2026 (shihet në emrin e skedarit: `Gjeneruar_me_19102026`) |
| **Madhësia** | 277,764 procedura, ~85 MB |
| **Kopja e grupit** | [Google Drive](https://drive.google.com/drive/folders/13KJ_SU6EgI5bSg2fhqaC3aZEcLcJkuGo?usp=drive_link) (dosja `data_raw`) |
| **Emri i skedarëve** | `Procedurat_e_prokurimit_-_viti_<VITI>_-_Gjeneruar_me_19102026.csv` |

- **Objekti** i të dhënave është një procedurë prokurimi (tender): çdo rresht është një procedurë.
- **Viti 2026 përjashtohet**, sepse në datën e eksportit nuk ishte i plotë.
- Të 10 skedarët bashkohen në një tabelë dhe secilit rresht i shtohet kolona `year` (viti i skedarit); kolonat lexohen si tekst që të ruhet formati origjinal ([`src/common/data_loading.py`](src/common/data_loading.py)).
- Nëse për një vit ka disa eksporte, p.sh. `... (1).csv` nga një shkarkim i dyfishtë, kopjet anashkalohen.

### Burimet shtesë për integrim

| Burimi | Përdorimi | Ku |
|---|---|---|
| [Komisioni Qendror i Zgjedhjeve (KQZ)](https://kqz.gov.al/rezultate-zgjedhore) | Datat e zgjedhjeve kombëtare 2015–2025, për vetitë zgjedhore dhe periudhën parazgjedhore | [`src/time_integration/elections.py`](src/time_integration/elections.py) |
| [Fjalori i përbashkët i prokurimit (CPV 2008)](https://ted.europa.eu/en/simap/cpv), [Rregullorja (EC) Nr. 213/2008](https://eur-lex.europa.eu/eli/reg/2008/213/oj) | Emrat e 45 ndarjeve CPV (2 shifrat e para të kodit) | [`data/reference/cpv_divisions.csv`](data/reference/cpv_divisions.csv) |

## Struktura e repository-t

```
├── data/
│   ├── raw/          # 10 CSV-të e APP-së (jo në git, ndahen në Google Drive)
│   ├── processed/    # dataset-et e gjeneruara nga skriptet (jo në git)
│   └── reference/    # tabelat ndihmëse (ndarjet CPV)
├── docs/             # dokumentimi i secilës pjesë dhe i dataset-it përfundimtar
├── notebooks/        # notebook-u që tregon hapat e Fazës I
├── reports/          # tabelat e rezultateve (CSV të vogla), një folder për secilën pjesë
└── src/
    ├── common/                 # funksione të përbashkëta (leximi, kualiteti, mungesat, vetitë, transformimi, PCA, mostrimi)
    ├── values_winners/         # vlerat dhe fituesit (+ transformimi, agregimi, PCA)
    ├── time_integration/       # koha dhe integrimi (+ dataset-i i integruar, mostrimi)
    ├── procedure_competition/  # procedura dhe konkurrenca (+ CPV, encoding, zgjedhja e vetive)
    └── final/                  # dataset-i përfundimtar
```

Të dhënat raw dhe dataset-et e gjeneruara nuk ruhen në git, sepse janë të mëdha dhe rikrijohen nga kodi. Në git ruhen vetëm kodi, dokumentimi dhe raportet.

## Si ekzekutohet

**1. Instalimi** (Python 3.11+):

```bash
pip install -r requirements.txt
```

**2. Të dhënat:** shkarkoni 10 skedarët CSV nga [Google Drive i grupit](https://drive.google.com/drive/folders/13KJ_SU6EgI5bSg2fhqaC3aZEcLcJkuGo?usp=drive_link) (dosja `data_raw`) ose nga faqja e APP-së, dhe vendosini në `data/raw/` pa ua ndryshuar emrat. Dataset-i i integruar i gatshëm (`prokurimi_integruar.csv`) gjendet në të njëjtin Drive, te dosja `data_processed`.

**3. Dataset-i përfundimtar.** Mjafton **një komandë**, nga rrënja e repository-t:

```bash
python -m src.final.final_dataset
```

Skripti i bën vetë të gjithë hapat e Fazës I për të tri pjesët (pastrimin, vlerat e zbrazëta, vetitë, integrimin e zgjedhjeve dhe CPV, transformimin dhe PCA-në), ndaj nuk duhet ekzekutuar asnjë skript tjetër më parë. Zgjat rreth 1 minutë dhe krijon `data/processed/prokurimi_final.csv` (277,764 rreshta × 84 kolona, ~218 MB). Përshkrimi i kolonave: [`reports/final/final_columns.csv`](reports/final/final_columns.csv).

Nëse duhet vetëm dataset-i i integruar, pa transformimin dhe PCA-në (64 kolona, ~155 MB): `python -m src.time_integration.integrated_dataset`.

**4. Notebook-u** (opsional, për të parë hapat dhe rezultatet):

```bash
jupyter notebook notebooks/01_parapercesimi.ipynb
```

**5. Hapat e veçantë** (opsionale: për të rigjeneruar raportet e secilës pjesë). Çdo skript pranon si argument opsional dosjen me CSV-të (parazgjedhja: `data/raw/`):

```bash
# Vlerat dhe fituesit
python -m src.values_winners.data_types
python -m src.values_winners.quality
python -m src.values_winners.cleaning
python -m src.values_winners.missing_values
python -m src.values_winners.features
python -m src.values_winners.transformation
python -m src.values_winners.aggregation
python -m src.values_winners.pca

# Koha dhe integrimi
python -m src.time_integration.data_types
python -m src.time_integration.quality
python -m src.time_integration.cleaning
python -m src.time_integration.missing_values
python -m src.time_integration.features
python -m src.time_integration.sampling
python -m src.time_integration.integrated_dataset

# Procedura dhe konkurrenca (dosja dhe intervali i viteve)
python -m src.procedure_competition.prepare data/raw 2016 2025

# Dataset-i përfundimtar
python -m src.final.final_dataset
```

Raportet ruhen te `reports/<pjesa>/`. Dataset-et e gjeneruara ruhen te `data/processed/`; për procedurat dhe konkurrencën, te `reports/procedure_competition/<intervali>/` (edhe këto jashtë git-it).
