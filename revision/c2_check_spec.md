# C2 – Prüfspezifikation für die Normalisierung

Festgeschrieben **vor** der Umsetzung von C2, damit die Kriterien nicht
nachträglich an das Ergebnis angepasst werden können.

**Gegenstand:** C2 schaltet `estimation.normalize` von `False` auf `True`,
d. h. `OddsMvt` wird von der rohen einseitigen impliziten Wahrscheinlichkeit
`p_own` auf die margenbereinigte Größe `p_own / (p_own + p_other)` umgestellt
(`filter_and_shape.py`, Block "Calculate implied probabilities").

**Vergleichsbasis:** `revision/snapshots/C1_refactor` (bit-identisch zu
`B_match_fix`, per Gate verifiziert). Nicht `A_baseline` – nur so ist der
gemessene Unterschied der isolierte Normalisierungseffekt.

**Zweck dieser Prüfung:** ausschließen, dass ein Kompositionseffekt als
Normalisierungseffekt erscheint. Die sample-definierenden Filter (Marge,
Bookmaker-Quantil, `ts_dur`) operieren sämtlich auf Rohgrößen und sind daher
von der Normalisierung unberührt. Es gibt aber zwei nachgelagerte Stellen, an
denen die Gruppenmenge doch kippen kann.

## 1. Kompositionsstellen

### 1.1 Gruppen mit Varianz 0 in `OddsMvt`

`resample_and_impute.py:96-97` und `:125-126` verwerfen Gruppen, deren
`OddsMvt`-Serie keine Varianz hat. Eine Gruppe, deren Home-Preis konstant
blieb, während sich der Away-Preis bewegte, hat rohe Varianz 0, aber
normalisierte Varianz > 0 – und umgekehrt. Die verworfene Menge kann sich
also in beide Richtungen ändern.

### 1.2 Gruppen mit `|RtrnOpnCls| = 0`

`bookmaker_accuracy.py:88` verwirft Gruppen ohne Open-to-Close-Bewegung.
Derselbe Mechanismus: eine rein margengetriebene Bewegung kann roh sichtbar
und normalisiert null sein, oder umgekehrt.

## 2. Auszuweisen je Kompositionsstelle

Nicht nur Anzahlen, sondern die **Differenzmengen**:

- die konkreten `GroupId`, die gegenüber C1 **herausfallen**
- die konkreten `GroupId`, die **neu hinzukommen**
- beide Mengen **aufgeschlüsselt nach Bookmaker**, jeweils absolut und als
  Anteil an den Gruppen des betreffenden Bookmakers

## 3. Erwartung

Die Aufschlüsselung soll ausschließen, dass **margenstarke Bookmaker
überproportional betroffen** sind. Wäre die Betroffenheit systematisch mit dem
Margenniveau korreliert, verschöbe sich die Stichprobe entlang genau der
Dimension, die normalisiert werden soll – der gemessene Effekt wäre dann
teilweise Komposition und nicht Messgrößenänderung. Bezugspunkt sind die
bookmaker-spezifischen Margen aus der Diagnose in
`references/specs/open_questions.md` (4,90 % Pinnacle bis 8,33 % Interwetten,
Spread ~3,4 pp).

## 4. Assertions (müssen zwischen C1 und C2 identisch sein)

Alle vier folgen daraus, dass die betroffenen Größen auf Rohquoten berechnet
werden; sie sind daher harte Bedingungen, kein Erwartungswert:

1. **`IsFav` zeilenweise identisch.** Die Zuordnung vergleicht
   `OddsMvtHome` gegen `OddsMvtAway` (`filter_and_shape.py:74-88`). Da
   `p_norm > 0.5 ⟺ p_h > p_a ⟺ dez_h < dez_a` eine monotone Transformation
   derselben Zeile ist, muss das Ergebnis exakt gleich bleiben.
2. **`n_obs` identisch** (Zeilen vor Filterung).
3. **`n_groups` identisch.**
4. **Margen-Filter-Ausschluss identisch** (`:58-59`, `0 <= Margin <= 0.15`)
   **und `ts_dur`-Filter identisch** (`:107-110`).

Schlägt eine dieser Assertions fehl, ist die C2-Umsetzung fehlerhaft – nicht
das Ergebnis interessant.
