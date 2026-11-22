# Eksplorimi i të dhënave (Faza II)

> Statistika përmbledhëse (univariante) dhe statistika multivariante. Çdo pjesë e shkruan seksionin e vet: Semine për shumat dhe kohën, Tringa për konkurrencën, procedurat dhe fituesit.

## 1. Pjesa e Semines: shumat dhe koha

*(Shtohet nga Semine.)*

## 2. Pjesa e Tringës: konkurrenca, procedurat dhe fituesit

> Kodi: [`src/exploration/competition_winners.py`](../src/exploration/competition_winners.py) · Ekzekutimi: `python -m src.outliers.competition_winners`, pastaj `python -m src.exploration.competition_winners` · Raportet: [`reports/exploration/`](../reports/exploration/)

Eksplorimi përdor flag-et e detektimit ([`docs/outliers.md`](outliers.md), seksioni 4): statistikat jepen për **të gjitha** procedurat dhe **pa gabimet** (`outlier_status = gabim` në cilëndo kolonë të kësaj pjese). Kështu shihet sa ndikojnë gabimet, pa fshirë asnjë rresht.

### 2.1 Tabela frekuencash ([`frequencies.csv`](../reports/exploration/frequencies.csv))

| Kolona | Kategoria më e shpeshtë | Vërejtje |
|---|---|---|
| `Lloji_i_procedures` | Small Value 66.0% | 13 lloje. 5 më të mëdhatë mbulojnë 95% |
| `Tipi_i_kontrates` | Supplies 60.4% | Services 33.4%, Works 6.2% |
| `competition_band` | 4+ oferta 60.6% | 1 ofertë 13.4%, asnjë ofertë 9.3% |
| `statusi_analitik` | Me fitues, kontratë e pakonfirmuar 54.1% | Kontradiktor 1.8% (shih rishikimin te `docs/outliers.md` 4.4) |
| `primary_cpv_division_name` | (mungon CPV) 22.2% | Pastaj barna dhe pajisje mjekësore 9.1%, transport 7.5% |

### 2.2 Statistika përmbledhëse ([`summary_statistics.csv`](../reports/exploration/summary_statistics.csv))

| Kolona | Mesatarja | Mediana | Dev. std. | Q1 | Q3 | Max | Asimetria | Kurtoza |
|---|---|---|---|---|---|---|---|---|
| Oferta të dorëzuara | 8.46 | 5 | 8.75 | 2 | 13 | 103 | 1.42 | 1.92 |
| Oferta të kualifikuara | 5.90 | 3 | 7.15 | 1 | 8 | 94 | 1.87 | 3.97 |
| `qualified_offer_share` | 0.71 | 0.86 | 0.33 | 0.50 | 1.00 | 1 | −0.77 | −0.76 |
| `cpv_count` | 1.42 | 1 | 2.05 | 1 | 1 | 79 | 6.35 | 82.1 |
| `nr_fituesve` | 1.003 | 1 | 0.17 | 1 | 1 | 35 | 99.1 | 12,689 |

Interpretimi:
- **Asimetri pozitive te numrat:** mesatarja është mbi medianë (8.5 kundrejt 5 oferta). Bishti i djathtë (deri 103 oferta) e tërheq mesataren lart, prandaj për këto kolona **mediana dhe IQR** e përshkruajnë më mirë procedurën tipike. Kjo është edhe arsyeja pse detektimi bëhet mbi shkallën log.
- **`qualified_offer_share`** ka asimetri negative: 44% e procedurave kanë të gjitha ofertat të kualifikuara (vlera 1).
- **`cpv_count` dhe `nr_fituesve`** janë pothuajse konstante (Q1 = Q3 = 1). Kurtoza shumë e madhe tregon që pak raste (marrëveshje kuadër me deri 35 fitues, procedura me deri 79 kode CPV) e mbajnë gjithë variancën. Për to devijimi standard nuk ka kuptim si masë e "shpërndarjes tipike".
- **Pa gabimet** (266,969 procedura) statistikat ndryshojnë pak: mesatarja e ofertave kalon nga 8.46 në 8.42. Gabimet e kësaj pjese janë gabime **konsistence** (anulime kontradiktore) dhe gabime **shkalle në shuma** (vlera ×1000 ose ×1/1000 e fondit), jo numra ekstremë ofertash. Prandaj nuk e shtrembërojnë shpërndarjen e numrave.

### 2.3 Krahasime sipas grupeve

**Sipas llojit të procedurës** ([`competition_by_procedure_type.csv`](../reports/exploration/competition_by_procedure_type.csv)):

| Lloji | Procedura | Mesatarja e ofertave | 1 ofertë % | Asnjë ofertë % | Anuluar % |
|---|---|---|---|---|---|
| Small Value | 183,329 | 11.3 | 8.0 | 4.6 | 26.1 |
| Request for Proposals | 25,549 | 2.5 | 26.8 | 22.6 | 33.6 |
| Open Local | 21,980 | 3.1 | 23.6 | 19.7 | 27.3 |
| Purchase Tickets | 17,766 | 4.3 | 5.3 | 2.1 | 11.9 |
| Open Simple | 16,725 | 2.3 | 30.9 | 21.2 | 29.6 |
| Negotiated without Notice | 5,307 | 0.8 | 50.3 | 36.0 | 41.6 |
| Open INT | 5,153 | 2.2 | 32.3 | 22.8 | 25.7 |

Procedurat e vogla ("Small Value") kanë mesatarisht 4–5 herë më shumë oferta se procedurat e hapura. Procedurat e hapura, që janë më të mëdha dhe më komplekse, kanë 24–32% raste me një ofertë të vetme. "Negotiated without Notice" ka natyrshëm konkurrencë të ulët (50% një ofertë), sepse është procedurë pa njoftim publik. Ky dallim i madh shkalle është i njëjti që e bën të nevojshëm detektimin **brenda llojit**.

**Sipas vitit** ([`competition_by_year.csv`](../reports/exploration/competition_by_year.csv)): mesatarja e ofertave rritet nga 7.3 (2016) në 10.4 (2025), dhe pjesa e anuluar bie nga 33% në 22%. Pjesa e ofertave të kualifikuara bie nga 0.87–0.88 (2016–2017) në 0.63–0.67 (2019–2025). Ky është ndryshim i nivelit nga 2018, jo rënie graduale, prandaj ka të ngjarë të lidhet me një ndryshim në rregullat e kualifikimit ose në mënyrën e regjistrimit, jo me sjelljen e ofertuesve. Duhet verifikuar para se të interpretohet si "cilësi më e ulët e ofertave".

**Sipas tipit të kontratës** ([`competition_by_contract_type.csv`](../reports/exploration/competition_by_contract_type.csv)): furnizimet (Supplies) kanë më shumë oferta (10.1) se shërbimet (5.8) dhe punimet (6.6). Shërbimet kanë pjesën më të lartë me një ofertë (16.2%).

### 2.4 Tabela kryqëzimi dhe forca e lidhjes

Për çdo tabelë jepet **Cramér's V** (0 = pa lidhje, 1 = lidhje e plotë), sepse me 277,764 rreshta testi χ² del gjithmonë "i rëndësishëm" (p ≈ 0) dhe nuk tregon sa e fortë është lidhja ([`crosstab_association.csv`](../reports/exploration/crosstab_association.csv)).

| Kryqëzimi | Cramér's V | Lidhja |
|---|---|---|
| Lloji i procedurës × `statusi_analitik` | 0.376 | mesatare–e fortë |
| Lloji i procedurës × `competition_band` | 0.303 | mesatare |
| Ndarja CPV (top 15) × `kategoria_e_fondit` | 0.211 | e dobët–mesatare |
| Tipi i kontratës × `competition_band` | 0.085 | shumë e dobët |

- **Lloji × konkurrenca** ([`crosstab_procedure_type_competition.csv`](../reports/exploration/crosstab_procedure_type_competition.csv)): te "Small Value" 75.9% kanë 4+ oferta, ndërsa te "Open Simple" vetëm 21.4%, me 30.9% një ofertë. Lloji i procedurës është faktori kryesor i konkurrencës.
- **Lloji × statusi** ([`crosstab_procedure_type_status.csv`](../reports/exploration/crosstab_procedure_type_status.csv)): procedurat e hapura kanë 51–57% "kontratë e konfirmuar", ndërsa "Small Value" vetëm 4.7%, sepse vlera e kontratës pothuajse nuk regjistrohet për to. 2.7% e "Small Value" janë kontradiktore, ku janë përqendruar gabimet e 2017.
- **CPV × kategoria e fondit** ([`crosstab_cpv_fund_category.csv`](../reports/exploration/crosstab_cpv_fund_category.csv)): p.sh. barnat kanë 24.6% fonde "të mëdha" dhe 39.2% "shumë të vogla". Sektori përcakton pjesërisht madhësinë e fondit.
- **Tipi i kontratës** lidhet shumë dobët me konkurrencën (V = 0.085): mesataret ndryshojnë (2.3), por shpërndarja nëpër bandat e konkurrencës është e ngjashme.

### 2.5 Përqendrimi i tregut

Indeksi Herfindahl-Hirschman: $HHI = \sum_i s_i^2$, ku $s_i$ është pjesa (%) e fituesit $i$ në vlerën e fituar (0–10,000). Pragjet sipas US DOJ/FTC Merger Guidelines (2023): < 1,000 i pa përqendruar, 1,000–1,800 mesatarisht i përqendruar, > 1,800 shumë i përqendruar. Llogaritet mbi procedurat jo të anuluara me fitues, pa shumat e pamundura (përfshirë gabimet e shkallës vlerë/fond, `docs/outliers.md` 4.5).

- **Në tërësi** ([`concentration_overall.csv`](../reports/exploration/concentration_overall.csv)): 6,567 fitues, HHI = 78, pra treg **i pa përqendruar**. 10 fituesit më të mëdhenj marrin 20.1% të vlerës, por vetëm 10.9% të kontratave, që do të thotë se fitojnë kontrata më të mëdha se mesatarja.
- **Sipas ndarjes CPV** ([`concentration_by_cpv.csv`](../reports/exploration/concentration_by_cpv.csv)): i vetmi treg **mesatarisht i përqendruar** është ai i **shërbimeve financiare dhe të sigurimeve**: HHI = 1,160, 164 fitues dhe 4 më të mëdhenjtë marrin 62% të vlerës. Kjo përputhet me natyrën e tregut, ku pak kompani sigurimesh (ALBSIG, SIGAL, INSIG etj.) mbulojnë gjithë sektorin publik. Tregjet e tjera janë të pa përqendruara (HHI 81–913).
- **Sipas vitit** ([`concentration_by_year.csv`](../reports/exploration/concentration_by_year.csv)): HHI është 80–125 çdo vit, me përjashtim të **2017 (914)** dhe **2021 (440)**. Shkaku janë dy kontrata të vetme reale: koncesioni PPP i **Rrugës së Arbrit** (33.6 miliardë lekë, 29% e vlerës së 2017) dhe **Tuneli i Llogarasë** (17 miliardë, 18% e 2021). HHI sipas **numrit të kontratave** mbetet i qëndrueshëm (26–63) në të gjitha vitet. Pra këto kulme nuk janë gabime dhe as përqendrim i tregut, por raste "të vërteta por të rralla" që e ndryshojnë treguesin e bazuar në vlerë. Për këtë arsye jepen të dy treguesit.

### 2.6 Korrelacioni: Pearson kundrejt Spearman, me dhe pa përjashtuesit

Llogaritet për ofertat, pjesën e kualifikuar, `cpv_count`, fondin, vlerën dhe kohëzgjatjen (shumat dhe kohëzgjatja në log për Pearson) ([`correlation_pairs.csv`](../reports/exploration/correlation_pairs.csv); matricat: [`correlation_pearson.csv`](../reports/exploration/correlation_pearson.csv), [`correlation_spearman.csv`](../reports/exploration/correlation_spearman.csv)):

| Çifti | Pearson (të gjitha) | Pearson (pa përjashtuesit multivariantë) | Spearman |
|---|---|---|---|
| Fondi – vlera fituese | 0.718 | **0.993** | 0.904 |
| Oferta të dorëzuara – të kualifikuara | 0.859 | 0.883 | 0.860 |
| Fondi – kohëzgjatja e tenderit | 0.598 | 0.671 | 0.457 |
| Vlera – kohëzgjatja | 0.432 | 0.678 | 0.409 |
| Oferta – kohëzgjatja | −0.324 | −0.314 | −0.333 |
| `qualified_offer_share` – `cpv_count` | −0.145 | −0.166 | −0.303 |
| Oferta – vlera fituese | −0.037 | −0.143 | −0.113 |

Interpretimi:
- **Ndikimi i përjashtuesve:** korrelacioni Pearson fond–vlerë rritet nga 0.72 në 0.99 kur hiqen përjashtuesit multivariantë. Rreth 6,000 procedura me gabim shkalle (vlera ×1000 ose ×1/1000 e fondit) e ulin fort Pearson. Spearman (0.90), që bazohet në rangje, ndikohet shumë më pak. Kjo tregon pse detektimi duhej bërë para analizës.
- **Konkurrenca dhe madhësia:** tenderët më të gjatë, që zakonisht janë më të mëdhenj, kanë **më pak** oferta (ρ ≈ −0.33). Lidhja mes numrit të ofertave dhe vlerës është e dobët (ρ ≈ −0.11).
- **Pearson ≠ Spearman** te `qualified_offer_share` (−0.15 kundrejt −0.30): lidhja nuk është lineare, sepse vlerat grumbullohen në 0 dhe 1, prandaj Spearman është masa e duhur.

### 2.7 Interpretimi i komponentëve të PCA-së ([`pca_interpretation.csv`](../reports/exploration/pca_interpretation.csv))

PCA nga Faza I (9 veti, 6 komponentë = 92% e variancës). Interpretimi bazohet në 3 ngarkesat (loadings) më të mëdha të secilit komponent:

| Komp. | Varianca % | Ngarkesat më të mëdha | Interpretimi |
|---|---|---|---|
| PC1 | 29.2 | kohëzgjatja (+0.50), fondi (+0.44), oferta të kualifikuara (−0.42) | **Madhësia/kompleksiteti kundrejt konkurrencës**: tender i madh dhe i gjatë, me pak oferta |
| PC2 | 18.5 | oferta të dorëzuara (−0.56), të kualifikuara (−0.48), vlera (−0.44) | **Shkalla e përgjithshme**: shumë oferta dhe shuma të mëdha bashkë (shenja negative) |
| PC3 | 14.5 | `qualified_offer_share` (−0.72), `cpv_count` (+0.57) | **Cilësia e ofertave**: pjesë e ulët e kualifikuar te procedurat me shumë kode CPV |
| PC4 | 11.4 | ditët nga zgjedhjet (−0.88) | **Afërsia me zgjedhjet** (thuajse vetëm një veti) |
| PC5 | 10.0 | ditët publikim–hapje (+0.85) | **Afati nga publikimi te hapja** |
| PC6 | 8.6 | `cpv_count` (+0.74), `qualified_offer_share` (+0.55) | Shumë kode CPV me pjesë të lartë të kualifikuar |

Dy komponentët e parë (48% e variancës) përshkruajnë **madhësinë** dhe **konkurrencën** e procedurës. Këtë e konfirmojnë edhe korrelacionet në 2.6: fondi, vlera dhe kohëzgjatja lëvizin bashkë, ndërsa numri i ofertave lëviz në drejtim të kundërt. PC4 dhe PC5 janë pothuajse veti të vetme kohore, pra nuk lidhen me pjesën tjetër. Kjo përputhet me korrelacionet afër 0 të tyre me ofertat dhe shumat.
