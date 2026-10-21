# Koha dhe Integrimi

Kolonat: `Data_e_publikimit`, `Data_e_hapjes`, `Data_e_mbylljes`, `Numri_i_references`, `viti`

> Të dhënat: 10 skedarët vjetorë **2016–2025** (277,764 procedura).
> Kodi: [`src/time_integration/`](../src/time_integration/) · Rezultati: [`reports/time_integration/`](../reports/time_integration/)

## 1. Periudha e zgjedhjeve

Integrimi përfshin periudhat e zgjedhjeve (2017, 2021, 2023, 2024, 2025) për analizën e prokurimit gjatë periudhave elektorale.

| Viti | Lloji | Data |
|------|-------|------|
| 2017 | Presidenciale | 25 Qershor |
| 2021 | Lokale | 25 Prill |
| 2023 | Lokale | 14 Maj, 24 Shtator |
| 2024 | Lokale | 4 Gusht |
| 2025 | Parlamentare/Lokale | 11 Maj, 9 Nëntor |

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

**Gjetje kryesore:** 7,170 procedure (2.58%) kanë data të hapjes para datës së publikimit - logjikisht të pamundur. Këto kërkojnë pastrimin e mëtejshëm.

## 2.2 Vlerat e zbrazëta

Asnjë rresht nuk fshihet. Datat që mungojnë plotësohen me vlerësim logjik dhe çdo vlerë e plotësuar shënohet me kolonë `*_imputed`.

| Kolona | Mungesa | Metoda |
|---|---|---|
| `Data_e_hapjes` | 169 | Data e publikimit + mediana e vonesës publikim→hapje e vitit përkatës |
| `Data_e_mbylljes` | 1,092 | Data e hapjes + mediana e kohëzgjatjes hapje→mbyllje e vitit përkatës |
| `Data_e_publikimit`, `Numri_i_references` | 0 | Nuk kërkohet veprim |

- Mediana llogaritet sipas vitit (afatet ndryshojnë nga viti në vit) dhe përdor vetëm diferenca ≥ 0, ndaj data e plotësuar nuk mund të dalë para datës nga e cila rrjedh. Nëse një vit nuk ka diferenca të vlefshme, përdoret mediana globale.
- Pas plotësimit mbeten 0 mungesa dhe 277,764 rreshta (asnjë i fshirë).
- Kodi: `python -m src.time_integration.missing_values`

## 3. Raportet e gjeneruara

- **missing_summary.csv**: Mungesat para/pas plotësimit dhe numri i vlerave të plotësuara
- **missing_by_year.csv**: Përqindja e mungesave sipas vitit
- **data_types.csv**: Tipet e të dhënave për çdo kolonë
- **integration_summary.csv**: Përmbledhja e 277,764 procedurave
- **elections_mapping.csv**: Procedurat gjatë periudhave zgjedhore (13 total)
- **quality_checks.csv**: Kontrollet e cilësisë (17 kontrolle)