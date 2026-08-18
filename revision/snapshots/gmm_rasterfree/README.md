# K als freier Parameter im GMM (Biais' ursprüngliche Momentbedingung)

Rein diagnostisch, **kein Eingriff in die Produktions-Pipeline**. Die
Zwei-Parameter-Klassen liegen in `_gmm_freek.py`; `src/pfd` ist unberührt.
Datenbasis ist der publizierte Frame `C_normalized/wide_imputed.h5`
(183.210 Serien, 24 Bookmaker), Code-Stand mit Exponenten-Fix `d8d26bc`.

## Ausgangspunkt

Die Produktionsfassung schätzt nur `gamma` (`k_params=1`) und unterstellt
`K = 0`. Begründet wird das damit, dass die terminale Größe der beobachtete
Ausgang `omega` sei, der Proxy-Fehler also verschwinde.

**Die Vorprüfung (`_prep.py`) widerlegt das:**

| | |
|---|---:|
| `E[(P − omega)²]` | 0,211090 |
| `E[P(1−P)]` (irreduzible Bernoulli-Varianz) | 0,217611 |
| Anteil am Gesamtfehler | **103 %** |

Zerlegt man mit der wahren Gewinnwahrscheinlichkeit `q`:
`E[(P−omega)²] = E[(P−q)²] + E[q(1−q)]`. Gerade *weil* die Realisation statt
der Wahrscheinlichkeit eingesetzt wird, entsteht ein Bodensatz, und er ist
mit ~0,21 praktisch die ganze gemessene Größe. Das Zerfallssignal darüber
beträgt ~0,001.

## Was gerechnet wurde

Momentbedingung wie im auskommentierten Papertext (Z. 466–468):

```
E[(p_t − w)² − (tau2/tau1)^(2g) (p_t−1 − w)² − K(1 − (tau2/tau1)^(2g))] = 0
```

Drei Zugänge, weil sich sofort zeigte, dass K schwach identifiziert ist:
(A) K auf einem Gitter **festgehalten**, `gamma` eindimensional geschätzt;
(B) K frei, zwei Parameter, 9 Startwerte; (C) K frei, aber auf das zulässige
Intervall `(0; 0,25)` reparametrisiert (`K = 0,25·logistic(kappa)`) — eine
Bernoulli-Restvarianz kann weder negativ noch größer als 0,25 sein.

## Ergebnis: K lässt sich in diesem Momentsystem nicht freigeben

### (A) Profil über festes K, gepoolt

| K fest | gamma | SE | J (df 13) | p |
|---:|---:|---:|---:|---:|
| 0,00 | 0,004814 | 0,000434 | 58,50 | <0,001 |
| 0,05 | 0,006327 | 0,000575 | 59,63 | <0,001 |
| 0,10 | 0,009186 | 0,000850 | 62,01 | <0,001 |
| 0,15 | 0,016326 | 0,001621 | 69,60 | <0,001 |
| 0,20 | 0,020587 | 0,008428 | 172,21 | <0,001 |
| 0,25 | −0,021358 | 0,001880 | 49,71 | <0,001 |

`gamma` ist **extrem empfindlich gegenüber K**: Faktor 4,3 zwischen K = 0 und
K = 0,20, Vorzeichenwechsel bei K = 0,25. Die K-Null-Annahme ist also alles
andere als harmlos — sie bestimmt die Größenordnung des publizierten Werts.
Der J-Test verwirft gepoolt bei **jedem** K.

### (B)/(C) K frei — die Schätzung entgleist

| | gamma | K | J | konvergiert | Streuung gamma |
|---|---:|---:|---:|---:|---:|
| unbeschränkt | **2,5979** | 0,20494 | 328,0 | 9/9 | 2,8e−06 |
| auf (0; 0,25) | **2,5979** | 0,20494 | 328,0 | 3/3 | 1,6e−06 |
| Referenz K = 0 | 0,0048 | – | 58,5 | – | – |

`gamma = 2,6` ist als Konvergenzrate sinnlos (publiziert: 0,005). Beide
Varianten laufen auf denselben Punkt, aus allen Startwerten, mit einer
Streuung von 1e−06 — **es ist kein numerisches Problem, sondern ein echtes
Optimum eines schlecht gestellten Problems.** Der J-Wert verschlechtert sich
dabei von 58,5 auf 328,0.

Je Bookmaker dasselbe Bild: `gamma` mit freiem K erreicht Werte bis
**139,3** (Betway) und 63,2 (BetVictor), drei Bookmaker konvergieren gar
nicht (Betfair, Dafabet, Marathonbet). Mittel 12,45.

| | Mittel | Median | Spanne | negativ |
|---|---:|---:|---:|---:|
| K = 0 (Produktion) | 0,005396 | 0,005748 | [0,00138; 0,01240] | 0 |
| K = 0,20 fest | 0,958 | 0,077 | [−0,538; 17,75] | 7 |
| K frei auf (0; 0,25) | 12,451 | 2,932 | [0,0039; 139,34] | 0 |

Rangkorrelation zur Produktionsfassung: **0,137** (K = 0,20 fest) und
**0,227** (K frei) — die Bookmaker-Ordnung löst sich vollständig auf.
J-Test verworfen: K = 0 in 1/24, K frei in **5/24** — die Überidentifikation
wird durch den zusätzlichen Parameter **schlechter**, nicht besser.

## Warum: der K-Koeffizient verschwindet, wenn gamma klein ist

Der Schlüssel steht in einer Zeile der Ausgabe:

```
K-Koeffizienten (1 − r): 0,001124 / 0,001267  bei gamma = 0,005
```

Bei `gamma = 0,005` sind die Zerfallsfaktoren `r₁ = 0,8936^0,01 = 0,99888`
und `r₂ = 0,8810^0,01 = 0,99873`. Der Term, mit dem K überhaupt in die
Momentbedingung eingeht, ist `(1 − r) ≈ 0,0011`. K trägt damit
`0,2 × 0,0011 ≈ 0,0002` zu einer Momentbedingung bei, deren übrige Terme in
der Größenordnung **0,2** liegen — ein Beitrag von 0,1 %.

Damit K sich überhaupt bemerkbar macht, muss `gamma` groß genug werden, dass
`(1 − r)` substanziell ist. Genau das tut der Schätzer: bei `gamma = 2,6` ist
`r₁ = 0,8936^5,2 = 0,562`, also `(1 − r₁) = 0,438` und `K(1 − r₁) = 0,09` —
jetzt vergleichbar mit der Skala der Momentbedingung. **Der Schätzer tauscht
ein absurdes gamma gegen ein plausibles K.**

Das ist strukturell und nicht durch andere Stützstellen zu beheben: `2·gamma`
steht im Exponenten, und jedes Verhältnis hoch 0,01 liegt bei 1. **K ist
unidentifizierbar, solange gamma klein ist** — unabhängig von `incr`.

Bemerkenswert ist, dass die K-Schätzungen selbst dennoch den richtigen Ort
treffen: Median **0,19994**, Mittel 0,18101 — genau der Bodensatz aus der
Vorprüfung (0,211). Das Modell *findet* K, kann es aber nur um den Preis
eines entgleisten gamma unterbringen.

## Die eigentliche Diagnose: ein skalares K kann den Bodensatz nicht abbilden

Biais setzt als terminale Größe den **Schlusspreis** `p_T` ein; `K = E[phi²]`
ist dort die Varianz des Proxy-Fehlers `phi = p_T − v` — klein und plausibel
über Beobachtungen konstant. Unser Paper hat `p_T` durch die **Realisation**
`omega` ersetzt und gleichzeitig K gestrichen, beides mit derselben
Begründung.

Die Ersetzung erzeugt aber einen Bodensatz `q_i(1−q_i)`, der

1. **groß** ist (~0,21 statt ~0), und
2. **über Beobachtungen stark variiert** — mit `P` zwischen 0,027 und 0,972
   liegt `q(1−q)` zwischen 0,026 und 0,25.

Ein **skalarer** Parameter K kann eine über Matches heterogene Größe nicht
darstellen. Deshalb repariert Biais' ursprüngliche Formulierung den Fehler
nicht: sie ist für einen konstanten Proxy-Fehler gebaut, nicht für eine
beobachtungsabhängige Bernoulli-Varianz.

Im Code ist die Alternative übrigens noch sichtbar:
`_create_gmm_data.py:46` enthält auskommentiert
`# endog = df[f"OddsMvt{n_per - 1}"]` — die Schlusspreis-Fassung.

## Konsequenz

- **`K = 0` freizugeben ist kein gangbarer Weg.** Es verschlechtert die
  Überidentifikation, zerstört die Bookmaker-Ordnung und liefert sinnlose
  Werte.
- **Die publizierte Zahl bleibt trotzdem an einer nicht testbaren Annahme
  aufgehängt.** Das Profil zeigt: `gamma` läuft von 0,0048 (K = 0) auf
  0,0206 (K = 0,20). Die Daten können innerhalb dieses Rahmens nicht
  entscheiden, welcher Wert gilt.
- **Der saubere Ausweg wäre der Wechsel der terminalen Größe** zurück auf den
  Schlusspreis, wie bei Biais — dann ist K klein, homogen und die
  Momentbedingung wohlgestellt. Das ist eine Spezifikationsentscheidung,
  keine Diagnostik, und **noch nicht gerechnet**.

## Nachtrag: warum die Stützstellen bei 46 statt 50 beginnen

Quelle: `_support_shift.py`, `_check50.py`, `support_shift_gamma.csv`,
`support_shift_ffill.csv`.

### Es ist eine Indexierungs-Altlast, keine Modellentscheidung

Commit `d175c70` („Code processings", 02.07.2024) stellte die terminale Größe
um und verschob dabei den Offset:

```diff
-    endog = df[f"OddsMvt{n_per - 1}"].to_numpy()      # = OddsMvt50
+    # TODO
+    endog = df["Match"].to_numpy()
+    # endog = df[f"OddsMvt{n_per - 1}"].to_numpy()

-    for i in range(1, 6):
-        p = df[f"OddsMvt{n_per - (1 + i * incr)}"]    # 45/40/35/30/25
+    for i in range(1, 6):  # TODO 0 + ...
+        p = df[f"OddsMvt{n_per - (0 + i * incr)}"]    # 46/41/36/31/26
```

Solange `endog = OddsMvt50` galt, **mussten** die Stützstellen darunter
liegen — sonst wäre `(p_50 − p_50)² ≡ 0`. Mit `endog = Match` fällt diese
Notwendigkeit weg, `OddsMvt50` wird verwendbar. Der Commit hat den Offset nur
um einen Rasterschritt verschoben (von `1 + i·incr` auf `0 + i·incr`) und
**zwei `# TODO`-Marker hinterlassen**, einen auf der `endog`-Zeile und einen
auf der Schleife. Eine Begründung ist nirgends dokumentiert. Die aktuelle
Fassung lässt `OddsMvt47` bis `OddsMvt50` ungenutzt, also die letzten 8 % des
Fensters.

### Stützstellen und Zerfallsfaktoren

| Variante | Spalten | tau | Faktoren |
|---|---|---|---|
| **A** (aktuell) | 46/41/36/31/26 | [47, 42, 37] | 0,89362 / 0,88095 |
| **B** (voll) | 50/45/40/35/30 | [51, 46, 41] | 0,90196 / 0,89130 |

Die Faktoren rücken näher an 1; `gamma` müsste in B um den Faktor **1,090**
größer sein, um denselben Zerfall abzubilden.

### Ist OddsMvt50 sauberer oder problematischer?

Beides — je nach Frage. **Wertmäßig ist `OddsMvt50` unbedenklich:** in beiden
Fensterregimen ist es zu **100,00 %** identisch mit dem letzten tatsächlich
beobachteten Preis der Serie (`_check50.py`). Es ist der echte Schlusspreis,
kein erfundener Wert.

**Zeitlich ist es unter V1 problematisch:** dort liegt die Zelle am
Matchup-Ende, also für rund 90 % der Serien *später* als der letzte eigene
Quote. Der Preis ist echt, aber ihm wird ein `tau = 51` zugeschrieben, das
eine längere verstrichene Zeit unterstellt als tatsächlich vergangen ist.
Unter V2 stimmen Wert und Zeitpunkt.

Zum Vergleich `OddsMvt46`: identisch mit dem letzten echten Preis in 32,36 %
(V1) bzw. 10,69 % (V2) der Serien — es ist also meist ein echter
Zwischenpreis, aber unter V1 in einem knappen Drittel der Fälle bereits der
eingefrorene Schlusswert.

### gamma über beide Varianten und beide Fenster

| | A 46/41/36 | B 50/45/40 |
|---|---:|---:|
| **V1 matchweit** | **0,005396** (sig 16/24, neg 0, J verw. 1/24) | 0,003026 (sig 4/24, neg 3, J verw. 1/24) |
| **V2 serieneigen** | 0,002671 (sig 7/24, neg 2, J verw. 2/24) | **0,003474** (sig 7/24, neg 1, **J verw. 0/24**) |

Die vier Zellen spannen einen **Faktor 2** auf, allein aus Indexierung und
Fensterwahl. Auffällig: drei der vier Zellen liegen zwischen 0,0027 und
0,0035; der Ausreißer nach oben ist **die publizierte Fassung V1|A mit
0,0054**.

Unter V1 senkt der Wechsel auf B `gamma` von 0,0054 auf 0,0030 und die Zahl
signifikanter Bookmaker von 16 auf 4 — und das, obwohl B rein mechanisch ein
um 9 % *größeres* `gamma` erzeugen müsste. Der reale Effekt ist also noch
größer als die Differenz zeigt.

Rangkorrelationen (Spearman): V1|B ↔ V2|B **0,700** — der höchste Wert im
Feld. Mit der vollen Stützstellenreihe stimmen die beiden Fensterregime in
der Bookmaker-Ordnung deutlich besser überein. Die publizierte Fassung V1|A
korreliert mit den übrigen nur zwischen 0,35 und 0,46.

### Einordnung

**V2|B ist die einzige Zelle, in der alle fünf Stützstellen beobachtete
Preise zu korrekten Zeitpunkten sind**, die letzte davon der echte
Schlusspreis. Sie hat zugleich die beste Überidentifikation (0 von 24
Verwerfungen) und liefert `gamma = 0,003474`.

Das ist keine Empfehlung zur Umstellung, sondern der Befund, dass die
publizierte Zahl in genau der Zelle liegt, die von allen vieren die meisten
Artefakte enthält.

## Dateien

- `_prep.py` — Vorklärung: Zeitachse, Verteilung von log[(P−omega)²],
  Bodensatz K, Jensen-Lücke
- `_gmm_freek.py` — Profil über festes K, K frei (unbeschränkt und
  beschränkt), gepoolt und je Bookmaker, Cluster-Sandwich auf Matchup
- `freek_profile_pooled.csv` — Profil gepoolt
- `gmm_freek_by_bookie.csv` — je Bookmaker, alle Varianten
- `freek_starts_pooled_*.csv` — alle Startwerte, zur Konvergenzprüfung
