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

## 3. Raportet e gjeneruara

- **data_types.csv**: Tipet e të dhënave për çdo kolonë
- **integration_summary.csv**: Përmbledhja e 277,764 procedurave
- **elections_mapping.csv**: Procedurat gjatë periudhave zgjedhore (13 total)