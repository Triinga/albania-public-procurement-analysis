# Vlerat dhe fituesit

Kolonat: `Fondi_limit`, `Vlera_e_fituesit`, `Vlera_e_fituesit_ne_lidhjen_e_kontrates`, `Lidhja_e_kontrates_me_TVSH`, `Fituesi`, `NIPT_i_fituesit`

> Të dhënat: 10 skedarët vjetorë **2016–2025** (277,764 procedura).
> Kodi: [`src/values_winners/data_types.py`](../src/values_winners/data_types.py) (ekzekutohet me `python -m src.values_winners.data_types <dosja_me_csv>`) · Rezultati: [`data_types.csv`](../reports/values_winners/data_types.csv)

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
