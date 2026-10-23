# Procedura dhe konkurrenca

Analiza përdor eksportet e APP-së për **2016–2025** (277,764 procedura), sipas scope-it të planit të grupit.

Kodi: [`src/procedure_competition/prepare.py`](../src/procedure_competition/prepare.py) · Raportet: [`reports/procedure_competition/`](../reports/procedure_competition/)

Ekzekutimi nga rrënja e repository-t; mund të zgjedhësh intervalin e viteve:

```powershell
python -m src.procedure_competition.prepare "C:\rruga\te\CSV-te" 2016 2020
python -m src.procedure_competition.prepare "C:\rruga\te\CSV-te" 2021 2025
```

Skripti pret një CSV për secilin vit të intervalit. Nëse gjenden disa eksporte për një vit, zgjidhet eksporti me datën më të re `Gjeneruar_me_DDMMYYYY`; nëse zgjedhja mbetet e paqartë, ekzekutimi ndalet. Të dhënat e papërpunuara lexohen si tekst; skedarët burimorë nuk ndryshohen. Rezultatet ruhen veçmas në nënfolder sipas intervalit, p.sh. `reports/procedure_competition/2016_2020/`. Dataset-i i pastruar ka po aq rreshta sa hyrja.

## Atributet dhe trajtimi

| Atributet                                                               | Tipi / trajtimi                                                                                                                                                  |
| ----------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Autoriteti_kontraktues`                                                | Kategorik nominal; hiqen hapësirat e tepërta, mungesat ruhen si bosh.                                                                                            |
| `Objekti_i_prokurimit`, `Arsyeja_e_anullimit`                           | Tekst; normalizohen hapësirat, mungesat nuk plotësohen me tekst të hamendësuar.                                                                                  |
| `Lloji_i_procedures`, `Tipi_i_kontrates`, `Lloji_i_marreveshjes_kuader` | Kategorik nominal; pastrohen hapësirat, vlerat bosh mbeten mungesa.                                                                                              |
| `Anulluar`, `Pezulluar`                                                 | `Po`/`Jo` kthehen në boolean `True`/`False`; vlerat e tjera ose bosh bëhen missing dhe numërohen te kontrolli i formatit.                                        |
| `Numri_i_ofertave_te_dorezuara`, `Numri_i_ofertave_te_kualifikuara`     | Numra të plotë; vlerat jo numerike bëhen missing. Asnjë rresht nuk hiqet për numër negativ ose mospërputhje, vetëm raportohet.                                   |
| `Kodet_CPV`                                                             | Teksti burimor ruhet; nxirren kodet 8-shifrore në rendin e paraqitjes. Shtohen numri i kodeve, kodi i parë dhe dy shifrat e para të kodit të parë si ndarje CPV. |

Nuk ishte dhënë tabelë/reference e veçantë CPV. Prandaj integrimi këtu nxjerr kodet dhe përshkrimin e tyre nga qeliza e APP-së; nuk bën lookup të jashtëm të përshkrimeve zyrtare.

Vetitë e krijuara janë `cpv_count`, `primary_cpv_code`, `primary_cpv_division`, `offers_missing`, `no_submitted_offers`, `qualified_offer_share`, `single_bidder`, `no_qualified_offers`, `competition_band`, `is_framework_agreement`, `has_cancellation_reason` dhe `cancelled_without_reason`. Pjesëtimi i ofertave të kualifikuara me ofertat e dorëzuara lihet missing kur numri i dorëzuar është zero ose mungon. `cancelled_without_reason` shënon vetëm procedurat e anuluara që nuk kanë arsye anulimi. `is_framework_agreement` është `True` kur lloji i marrëveshjes kuadër është i plotësuar dhe `False` kur fusha burimore është bosh.

`competition_band` e ndan numrin e ofertave të dorëzuara në katër grupe: `No offers`, `Single offer`, `2-3 offers` dhe `4+ offers`. Vlera mbetet missing kur numri i ofertave mungon ose është negativ.

Vlerat që mungojnë nuk plotësohen me kategori ose numra të hamendësuar. Hapësirat dhe boshllëqet normalizohen, ndërsa mungesat ruhen me tipe nullable. Politika dhe numri i mungesave para/pas pastrimit dokumentohen në `missing_values.csv`.

## Raportet dhe rezultatet

- `data_types.csv`: tipi konceptual, tipi në CSV, numri i vlerave unike dhe shembujt.
- `quality_checks.csv`: kompletësia, formati, konsistenca dhe kontrollet e vlefshmërisë para pastrimit.
- `quality_after.csv`: të njëjtat kontrolle pas normalizimit të tipeve dhe vlerave.
- `missing_values.csv`: mungesat para/pas pastrimit dhe trajtimi i përdorur për secilën kolonë.
- `competition_by_year.csv`: shpërndarja e grupeve të konkurrencës për secilin vit.
- `category_profile.csv`: frekuencat për llojin e procedurës/kontratës, marrëveshjen kuadër dhe statuset.
- `yearly_row_counts.csv`: numri i rreshtave sipas vitit.
- `preparation_summary.csv`: përmbledhja e përgatitjes dhe ruajtjes së rreshtave.
- `procedure_competition_clean.csv`: kolonat e pastruara dhe veçoritë e reja për integrim në hapin e pipeline-it final.

Në ekzekutimin me eksportet e 19.10.2026 u lexuan 277,764 procedura dhe u ruajtën të gjitha. U gjetën 216,076 procedura me së paku një kod CPV; 61,968 qeliza kishin më shumë se një kod. Marrëveshja kuadër mungon në 258,340 raste (93.0%), ndaj boshllëqet mbeten missing dhe nuk imputohen. Këto përmbledhje janë në raportet CSV; numrat rifreskohen kur skripti ekzekutohet me eksporte të reja.

Raportet e commit-uara janë ndarë në dy intervale të verifikueshme. Për 2016–2020 u ruajtën 151,007 nga 151,007 procedura. Për 2021–2025 u ruajtën 126,757 nga 126,757 procedura: 124,164 kishin së paku një kod CPV, 39,880 kishin disa kode CPV dhe 387 procedura të anuluara nuk kishin arsye anulimi. Në këtë interval, 16,556 procedura kishin vetëm një ofertë, 17,490 nuk kishin oferta të kualifikuara dhe 11,241 ishin marrëveshje kuadër. Shuma e dy intervaleve është 277,764 procedura.
