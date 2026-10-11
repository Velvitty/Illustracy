# Illustracy — 4. Algorithms and formulas (3/4): Regions · materials · tones · parts · inversion · storage · verification

[← README](../README.en.md#4-algorithms-and-formulas) · Section 4 [1](4-1-basics.en.md) · [2](4-2-background.en.md) · **3** · [4](4-4-rough-psd-tools.en.md) · [한국어](4-3-regions-layers.md)

---

## 4.6 Regions and materials

- **<mark>k-means</mark>** (4.2): the 𝑈 Lab of non-background $`\mathrm{known}`$ pixels into $`K = \max(2, \min(\text{number of colors}, \text{number of pixels}))`$ colors (number of colors default 18), at most 50,000 samples, <mark>k-means++</mark> initialization, at most 18 iterations,
  stopping when fewer than 0.1% of samples moved. Empty clusters are moved to the farthest sample. Every pixel gets the color number of the nearest center, and 4-connected components with the same number are region candidates.
  - **Note** — **Why**: Paint colors must be reduced to a fixed number of representative colors before areas painted in the same color can be grouped into regions. **How it works**: <mark>k-means</mark> alternates assignment and mean updates to reduce the sum of squared errors $`\sum\lVert x - \mu\rVert^2`$. <mark>k-means++</mark> draws each next center with probability proportional to the squared distance to the nearest chosen center, so initial centers do not bunch up and trap the result in a poor solution (within $`O(\log K)`$ of optimal in expectation). Stopping when fewer than 0.1% of samples move means it has nearly converged, and moving empty clusters to the farthest sample keeps all 𝐾 colors in use. Working in Lab keeps distances close to perceived color differences. **References**: [R22 Lloyd 1982](../README.en.md#r22) · [R23 Arthur · Vassilvitskii 2007](../README.en.md#r23) · [R7 CIE 2004](../README.en.md#r7)
- **Region keep condition**: $`A \ge \max(10, \mathrm{round}(12s^2))`$ and $`A \ge 0.75 \times \text{perimeter}`$ (removes thin smears; the perimeter follows the definition in 4.2, so a one-pixel strip has $`A/\text{perimeter} \approx 0.5`$).
  Discarded pixels and line pixels are filled with the number of the nearby region (background included). However, if a non-background $`\mathrm{known}`$ pixel received the background number and is more than 2.5px (<mark>chamfer distance</mark>) away
  from the background, the filling is done once more without the background number to give it the number of a nearby character region. In pictures with textured paper · fine brush marks, <mark>k-means</mark> breaks the paint into small pieces,
  35–39% of the picture's pixels were discarded and 8–12% received the background number, and places the background decision had left to the character became background (20 of 300 pixiv pictures by more than 1%, median 0.24%).
  The border within 2.5px is kept because of smearing in contact with the background (fixing the border too changed the found background of the 8 pictures with drawn outlines from 56.79 → 56.66% in pixel total).
  - **Note** — **Why**: Keeping one- or two-pixel smears and fragments along boundaries as regions would flood the parts with crumbs. **How it works**: The area threshold $`\max(10, \mathrm{round}(12s^2))`$ is an area, so it scales with the square $`s^2`$ of the size ratio. $`A \ge 0.75 \times \text{perimeter}`$ measures thinness by the area-to-perimeter ratio: a long strip of width 𝑤 has roughly $`A/\text{perimeter} \approx w/2`$, so strips narrower than about 1.5px drop out. Refilling only character pixels more than 2.5px (<mark>chamfer distance</mark>) from the background fixes wrong background labels in the middle of the character while leaving smears that touch the background alone. **References**: [R21 Borgefors 1986](../README.en.md#r21) · a rule set by this program
- **Undoing numbers smeared from gaps**: if there are gaps (4.5), the background is split into gaps 𝐺 and the rest 𝑂, and <mark>chamfer distances</mark> $`d_G,\ d_O`$ are measured. Among opaque non-background pixels (line pixels included),
  those that received the background number with $`d_G > 2.5`$ and $`d_G < d_O`$ (the nearest background is a gap) are filled once more without the background number to receive a nearby character number.
  This is done for both region numbers (above) and tone numbers (after the small-piece filling of 4.7). Lines have no region number and receive a nearby number, and when a gap puts the background number in the middle of a character,
  that number spreads far along the lines. A version that added only the gaps, without this undoing and the line-share condition (4.5), lost more character outside the gaps in 131 of the 198 changed pictures (more than 0.05%, up to 3.8%);
  after adding both, 49 pictures · up to 0.4% (11). Smearing on the non-gap background side is kept as before.
  - **Note** — **Why**: This keeps a gap (background) in the middle of the character from spreading along lines into the character through the label fill. **How it works**: <mark>Chamfer distances</mark> to the gap 𝐺 and to the rest of the background 𝑂 are measured separately, and only pixels whose nearest background is the gap ($`d_G < d_O`$) and lie more than 2.5px from it are refilled without the background label. Pixels right next to the gap stay; only far spreading is fixed. **References**: [R21 Borgefors 1986](../README.en.md#r21)
- **Region color**: each region uses the mean color of its $`\mathrm{known}`$ pixels (kept as LCh). Contacts are counted when two horizontally · vertically adjacent opaque pixels are in different regions;
  if either is $`\mathrm{inMask}`$, it is line-blocked length 𝑙, otherwise open length 𝑜.
- **Material grouping**: boundary pairs are looked at in order of open length, and merged when open length $`o \ge 3`$, open share $`o/(o + l) \ge 0.8 - 0.45m`$ (𝑚 = base color merge strength, default 0.5), and the relation below holds for both the two regions and the representative colors of the two groups (tolerance ×1.5).
  The representative color of a group is the color of the region with the most $`\mathrm{known}`$ pixels in the group, and merging attaches to the wider group (union-find).
  - **Note** — **Why**: Even if an artist paints one material (hair, clothes) in lit, shadow and highlight areas, those areas must be grouped as one material so base and shadow layers come out per material. **How it works**: The higher the open, line-free contact ratio $`o/(o + l)`$, the more likely the areas are shading of one object. The threshold $`0.8 - 0.45m`$ is linear in the merge strength 𝑚, falling as 𝑚 rises (0.575 by default). Groups are kept in a union-find structure, which merges two groups in nearly constant time, and representative colors are compared using the group's largest region. **References**: [R30 Tarjan 1975](../README.en.md#r30) · a rule set by this program

```math
\mathrm{shadeRelated}(c_1,c_2)=
\begin{cases}
\text{true} & \Delta E<\varepsilon_s\\
|L_1-L_2|<3\varepsilon_s & C_1<12,\ C_2<12\\
|h_1-h_2|<\varepsilon_h,\ \ 0.3< C_1/C_2<3.3 & C_1\ge 12,\ C_2\ge 12\\
\text{rules below} & \text{only one side achromatic}
\end{cases}
\qquad \varepsilon_h=14+40m,\ \ \varepsilon_s=5+12m
```

**Note** — **Why**: Shading of one material changes lightness and chroma but keeps nearly the same hue. This property decides whether two colors are shades of the same material. **How it works**: Close colors ($`\Delta E < \varepsilon_s`$) are always the same material. If both are achromatic ($`C < 12`$), hue means nothing, so only the lightness difference is checked. If both are chromatic, the LCh hue-angle difference $`< \varepsilon_h`$ and a chroma ratio of 0.3–3.3 are checked (a shadow may change chroma, but not by several times). The tolerances are linear in the merge strength 𝑚: $`\varepsilon_h = 34^\circ`$ and $`\varepsilon_s = 11`$ at the default. **References**: [R7 CIE 2004](../README.en.md#r7) · [R10 Fairchild 2013](../README.en.md#r10) · a rule set by this program

If only one side is achromatic (𝑛: the side with $`C < 12`$, 𝑐: the other), the following is checked.

- If $`C_n \ge 4`$ (the hue is recognizable), $`\lvert h_n - h_c\rvert < \varepsilon_h`$ and $`C_n/C_c > 0.2`$ are required (pale skin is not a highlight of blue hair).
- $`L_n \ge L_c`$ (highlight): $`L_n > L_c + 8`$ and $`L_n > 70`$ (mid gray is not a highlight).
- $`L_n < L_c`$ (desaturated shadow): $`C_n \ge 4,\ L_c - L_n \ge 4,\ L_n \ge 30`$ (same brightness but different saturation means a different material; very dark colors are where shadows of many materials converge).
  - **Note** — **Why**: When an achromatic and a chromatic color meet, the achromatic one may be a highlight (white light), a desaturated shadow, or a different material altogether, so the case is handled separately. **How it works**: If the achromatic side has enough chroma to show a hue ($`C_n \ge 4`$), the hues must match. A lighter achromatic color counts as a highlight only if bright enough ($`L > 70`$ and more than 8 lighter), and a darker one as a desaturated shadow only if some color remains and it is not too dark ($`L \ge 30`$). Very dark colors are where shadows of many materials converge, so they are not grouped. **References**: [R7 CIE 2004](../README.en.md#r7) · a rule set by this program

- **Crossing brush grain**: for each line-blocked boundary pixel pair, the colors on both sides outside the line are gathered: the first painted pixels met within $`w + 3`$ steps (𝑤 = maximum line width) in the pair's direction (horizontal · vertical), each in its own region.
  For each region pair, if both means have $`C \ge 12`$ and $`\Delta E < 0.55 \varepsilon_s`$ (default 6), the boundary is grain drawn over the paint.
  If at least half of the line-boundary length measured on both sides across the whole picture is grain, the measured length of grain boundaries is moved to the open length, and grouping proceeds as above.
  White · gray · black and desaturated shadows are colors shared by many materials, so they are not counted as grain even if both sides are the same.
  - **Note** — **Why**: Brush strokes drawn over paint (hair strands, cloth folds) are detected as lines and split one material in two, so when both sides of such a line have the same color the line is crossed. **How it works**: On each side of a line boundary, the first painted color within the line-width limit + 3 steps is collected and the means compared. $`\Delta E < 0.55\varepsilon_s`$ (6 by default) with both sides chromatic means a stroke on the same paint. It is used only when strokes make up at least half of the measured boundaries in the picture, so pictures where outlines happen to separate equal colors do not get materials merged wrongly. **References**: a rule set by this program

## 4.7 Tones, base color, shadow, highlight

- For each material, <mark>k-means</mark> with the number of tones $`k = \min(6, \max(1, \lfloor n/40\rfloor))`$ (𝑛 = number of pixels in the material) (at most 6000 samples, the mean if $`k = 1`$); centers with $`\Delta E < 8`$ become one. Pixels get the nearest tone.
  - **Note** — **Why**: The shading steps within one material (lit side, first and second shadow, highlight) must be split into a few tones before layers can be made. **How it works**: The tone count $`\min(6, \max(1, \lfloor n/40\rfloor))`$ gives each tone at least 40 pixels and caps the count at 6. After <mark>k-means</mark>, centers with $`\Delta E < 8`$ are merged so tones that look nearly the same are not split in two. **References**: [R22 Lloyd 1982](../README.en.md#r22) · [R7 CIE 2004](../README.en.md#r7)
- Tones also discard small pieces with the same keep condition as regions ($`A \ge \max(10, \mathrm{round}(12s^2))`$, $`A \ge 0.75 \times \text{perimeter}`$) and fill them by label filling.
- For each tone, the mean $`\bar t`$, the **bright-side mean** $`t^{up}`$ (pixels with $`\mathrm{lum} \ge \mathrm{lum}(\bar t) - 0.01`$), and the **dark-side mean** $`t^{lo}`$ ($`\mathrm{lum} \le \mathrm{lum}(\bar t) + 0.01`$) are found. Tones without samples convert the Lab of the <mark>k-means</mark> center back to sRGB (4.1).
  - **Note** — **Why**: A single representative color per tone cannot separate the lighter and darker parts within it, so lighter-side and darker-side means are kept. **How it works**: Only pixels above or below the tone mean's lightness $`\mathrm{lum}`$ (4.0) are averaged (the ±0.01 overlap keeps flat tones from having empty samples); without samples the <mark>k-means</mark> center is converted back from Lab to sRGB (4.1). Fragment cleanup uses the same area and perimeter conditions as regions. **References**: [R9 ITU-R BT.601](../README.en.md#r9) · [R6 IEC 1999](../README.en.md#r6)
- **Base color**: among tones with at least 75% of the area of the widest tone, the tone whose bright-side mean has the largest $`L^*`$ → base color 𝐹 = that tone's bright-side mean.
  Going from wide materials, if another tone (10% or more of the material) is $`\Delta E < 7`$ from a base color decided earlier (the closest one), the base is switched to that tone (the same material split by lines). If the current base color is closer than that, it is kept.
  - **Note** — **Why**: This is the rule that sets a material's base color. **How it works**: Among the large tones, the one whose lighter-side mean is brightest becomes the base. **References**: a rule set by this program
- **Lit-side base color**: in a material whose base tone 𝑏 has a bright-side mean with $`C \ge 12`$, if another tone 𝑡 of the same material satisfies all of the following, the base tone becomes the one among them whose bright-side mean has the largest $`L^*`$ (before the matching of same materials split by lines).
  - its area is at least 35% of the widest tone of the material, and $`L^*_t > L^*_b`$
  - the current base color can be made from 𝑡 by multiply: $`b^{up}_c \le t^{up}_c + 0.03`$ in every channel, and the brightness ratio $`0.45 \le \mathrm{lum}(b^{up}) / \mathrm{lum}(t^{up}) \le 0.93`$
  - $`C_t \ge 12`$, hue angle difference below 30°, and HSV saturation ($`(\max - \min)/\max`$) $`S_t \ge 0.8 S_b - 0.02`$ (a brighter tone that lost much saturation is a highlight · light bloom)

  This is not done for white · gray materials ($`C < 12`$): from color alone, whether the paler side is the lit surface or another material (gray hair next to white clothes) cannot be told.

  **Note** — **Why**: This is an auxiliary rule for choosing the base tone. **How it works**: It checks by channel comparison and lightness ratio whether the current base can be made by multiplying another tone. **References**: a rule set by this program
- **Splitting colors off white · gray materials**: in a material whose base color has $`C < 12`$, the tones that are not the base tone, have an area of at least $`\max(50, 0.0002N)`$, and whose mean color has $`C \ge 25`$ are gathered,
  and those connected by $`\mathrm{shadeRelated}`$ (4.6, default tolerances) become new materials. The base color of a new material follows the same rule (among tones with at least 75% of the widest tone's area, the tone whose bright-side mean has the largest $`L^*`$).
  When only one side is achromatic, material grouping treats the achromatic side as a highlight if it is more than 8 brighter (4.6), so a white surface and a colored surface touching without a line were grouped into one material whose base color was the wide white tone.
  The tone map is unchanged, so the background · character decision does not change.
  - **Note** — **Why**: This rule separates colored tones mixed into a white or grey material. **How it works**: High-chroma tones connected by the shading relation (4.6) become a new material. **References**: a rule set by this program
- **Shadow tones**: for the shadow threshold $`\eta_s`$ (default 0.5) (tones that are not the base, $`\mathrm{lum}(F) > 0.01`$)

  $`\displaystyle \frac{\mathrm{lum}(\bar t)}{\mathrm{lum}(F)}<0.86+0.12\,\eta_s \quad\Rightarrow\quad g_c=\min\!\left(1,\frac{t^{up}_c}{F_c}\right)\quad(g_c=1\text{ if }F_c\le0.004)`$

  𝑔 is the multiply color of that tone. Dividing by the bright-side mean leaves the darker pixels inside the tone to the shading layer (4.10).
  - **Note** — **Why**: Artists usually lay shadows as multiply layers over the base, so a shadow tone must be turned into "the color to multiply the base by" to be reusable as a layer. **How it works**: A tone darker than $`0.86 + 0.12\eta_s`$ (0.92 by default) times the base lightness is a shadow. Multiply gives $`F_c \cdot g_c = t_c`$, so $`g_c = t_c / F_c`$, clipped at 1 because multiply only darkens. Dividing by the lighter-side mean $`t^{up}`$ leaves the tone's darker pixels for the shading layer (4.10). With $`F_c \le 0.004`$ the division is unstable, so 1 is used. **References**: [R1 Porter · Duff 1984](../README.en.md#r1) · [R3 ISO 32000-1 2008](../README.en.md#r3)
- **1st / 2nd**: the part's shadow tones (tones with a channel $`g_c < 0.998`$) are ordered by $`\mathrm{lum}(g)`$ descending; if the difference between first and last is 0.07 or more and the largest gap between neighbors is 0.04 or more, they are split there.

  $`\displaystyle sh^1_c=q_8\!\left(\frac{\sum_{t\in\text{1st}}n_t\,g_{t,c}}{\sum_{t\in\text{1st}}n_t}\right),\qquad sh^2_c=q_8\!\left(\frac{\sum_{t\in\text{2nd}}n_t\min\!\big(1,\ g_{t,c}/\max(sh^1_c,10^{-3})\big)}{\sum_{t\in\text{2nd}}n_t}\right),\qquad q_8(x)=\frac{\mathrm{round}(255\,\mathrm{clamp}(x))}{255}`$

  $`n_t`$ is the tone's area (at least 1).
  - **Note** — **Why**: Splitting shadows into a first (wide, light) and second (narrow, dark) layer matches how artists paint and lets each layer be edited separately. **How it works**: Shadow lightnesses are sorted, and if the first and last differ by 0.07 or more and the largest gap is 0.04 or more, they are split at that gap (a 1-D natural break). The first shadow is the area-weighted mean. The second is multiplied on top of the first, so from $`F \cdot sh^1 \cdot sh^2 = F \cdot g`$ the mean of $`sh^2 = g / sh^1`$ is taken. $`q_8`$ rounds in advance to the 8-bit value to be stored, so the inversion later (4.9) matches the stored values exactly. **References**: [R1 Porter · Duff 1984](../README.en.md#r1) · a rule set by this program
- **Highlight**: among non-shadow tones, $`\mathrm{lum}(F) < 0.995`$ and $`1 - (1 - \mathrm{lum}(t^{lo}))/(1 - \mathrm{lum}(F)) > 0.12`$ (even the dark side is more than 12% brighter than the base color by screen).
  If the maximum channel of the tone mean is 0.85 or more and the value above exceeds 0.35, it is a sparkle candidate,
  and connected pieces of that tone with area $`3\pi r_s^2`$ or less ($`r_s = \max(4, \mathrm{round}(7s))`$ or the setting) are sparkle pixels (the area of 3 circles of radius $`r_s`$).
  - **Note** — **Why**: Highlights are tones laid lighter over the base, so they get their own layer, and small very bright pieces among them are split off as sparkles. **How it works**: $`1 - (1 - \mathrm{lum}(t^{lo}))/(1 - \mathrm{lum}(F))`$ solves for the screen amount that turns the base into the tone's darker-side lightness; above 0.12 even the tone's darker side is clearly laid on lighter. The sparkle size limit $`3\pi r_s^2`$ is the area of three circles of radius $`r_s`$. **References**: [R3 ISO 32000-1 2008](../README.en.md#r3)

## 4.8 Part cleanup

$`\mathrm{minPart} = \max(64, 0.0015N)`$. At first, one material is one part; a part's area is its number of opaque pixels, and its representative color is the base color of the widest material in the part.
The boundary length between parts is the number of horizontally · vertically adjacent pixel pairs spanning the two parts.

1. Parts with area $`\ge \mathrm{minPart}`$ are ordered by width, and every pair with representative colors $`\Delta E < 6`$ is merged.
   - **Note** — **Why**: Materials split too finely give too many layers, so small parts are merged into similar neighbors and parts of nearly the same color are combined. **How it works**: $`\mathrm{minPart} = \max(64, 0.0015N)`$ is 0.15% of the picture (at least 64px). A representative-color $`\Delta E < 6`$ looks similar side by side, so such parts count as one. **References**: [R7 CIE 2004](../README.en.md#r7) · a rule set by this program
2. Part boundaries are looked at from the longest; when the boundary is 8 pixels or more, 40% or more of the darker side's perimeter (sum of boundaries touching other parts), and the darker side is at most 1.5 times the area of the lighter side,
   if the brightness ratio $`r = \mathrm{lum}(\mathrm{dark})/\max(\mathrm{lum}(\mathrm{lit}), 10^{-3})`$ is 0.45–0.93, the darker side is not more than 0.03 brighter than the lighter side in any channel (a color that multiply can make),
   and the following holds, they are merged as a shadow. However, if $`r < 0.6`$ and the darker side is wide, 1% or more of the picture, they are not merged (light-catching brown hair and skin;
   in 25 test pictures · 48 synthetic pictures, apart from this case, all such dark surfaces merged as shadows were small surfaces under 0.3% of the picture). Then 1 is done once more.
   - **Note** — **Why**: Shadow areas detected separately because lines divide them are merged into their base part, so the lit side and the shadow of one material become one part. **How it works**: A lightness ratio 𝑟 of 0.45–0.93 and "no channel more than 0.03 brighter than the lit side" are the conditions for the dark side to be a multiply of the lit side (multiply only darkens each channel). A shared boundary of at least 40% of the dark side's perimeter means it is attached to the lit area. Chroma conditions split into two cases: if both are pale (chroma under 25), only the chroma difference and lightness ratio; otherwise a hue difference under 30° and a chroma ratio of 0.5–2. Excluding strong (𝑟 < 0.6) wide areas avoids cases such as lit brown hair against skin, where different materials look like a multiply pair. **References**: [R1 Porter · Duff 1984](../README.en.md#r1) · [R7 CIE 2004](../README.en.md#r7) · a rule set by this program
   - Both with saturation below 25 (like white hair ↔ light purple shadow): $`\lvert C_d - C_l\rvert < 18,\ r \ge 0.55`$, hue angle difference below 50° if the lighter side's saturation is 4 or more
   - Otherwise: both saturation 12 or more, hue angle difference below 30°, $`0.5 < C_d/C_l < 2`$
3. Parts below $`\mathrm{minPart}`$ (from the smallest material) are merged into the longest-touching neighbor with $`\Delta E < 30`$, or if none, the closest color among large parts with $`\Delta E < 20`$. If there is none either, they are merged into the longest-touching neighbor
   only when the area is below $`\mathrm{minKeep} = \max(64, 0.0001N)`$; larger parts are kept separately (merging into a differently colored neighbor turned the base color of pupils · hair ties · ties into the skin · hair color, so they vanished from the base color layer).
   - **Note** — **Why**: Merging small parts into very differently colored neighbors would erase the base colors of irises, hair ties and neckties, so they merge only into similar neighbors or stay separate. **How it works**: A stepwise rule: the longest-touching neighbor with $`\Delta E < 30`$, then the nearest large part with $`\Delta E < 20`$, and failing both, only crumbs below $`\mathrm{minKeep} = \max(64, 0.0001N)`$ are attached to a neighbor. **References**: [R7 CIE 2004](../README.en.md#r7) · a rule set by this program
4. While the number of parts that are not "small parts" exceeds the maximum number of parts $`\max(4, P)`$ (𝑃 default 32), the smallest part is merged into the closest color with $`\Delta E < 30`$ among touching parts, or if none, marked as a "small part".
   - **Note** — **Why**: Too many layers make the PSD hard to work with, so the part count is capped. **How it works**: The smallest part is repeatedly merged into a similar ($`\Delta E < 30`$) neighbor until the count is at most $`\max(4, P)`$ (greedy merging from the smallest). **References**: a rule set by this program

Finally, going through parts by width, if the 8-bit-rounded base color is $`\Delta E < 2.5`$ from a previous part, they are treated as one when making layers (a difference people hardly distinguish).

**Note** — **Why**: Splitting layers over color differences people can barely see only adds useless layers. **How it works**: $`\Delta E < 2.5`$ is about the size of a just-noticeable CIELAB difference (about 2.3). Comparing after 8-bit rounding judges by the values that will be stored. **References**: [R8 Mahy et al. 1994](../README.en.md#r8)

### Character splitting

Character splitting and part names use the faces for names · folders (9 of face finding in 4.5, adjusted score).

1. **Character faces**: among faces scoring 11.5 or more (and the top-scoring face), the group with the largest vote $`\sum(\text{score} - 10)^2`$ where every pair satisfies the following.
   - **Note** — **Why**: In a picture with several characters, which faces belong to different characters must be decided before per-character folders can be made, without one character's fake faces (knees, hands) becoming another character. **How it works**: The vote $`\max(0, \text{score} - 10)^2`$ is a squared weight, small near the threshold and large for sure faces (score 11 → 1 vote, 14 → 16 votes). Among groups whose every pair is similar in size and height and lies outside each other's head and body areas, the one with the largest vote total is chosen; checking all $`2^8 = 256`$ subsets of up to 8 candidates is exhaustive, so the best group is always found. **References**: a rule set by this program
   - Size (eye distance) ratio 0.5–2 (the found size wavers between 0.67 and 1.18 times the eye distance marked by a person)
   - Within $`4d`$ vertically in each other's face frame (similar height)
   - Outside each other's head ellipse · body column (the same shape as the zone probability in 4.5)
   Candidates are up to 8 in score order, and all subsets up to $`2^8`$ are examined (a group of two or more is adopted only if it beats the single top face in vote total). If only one face remains, there is no split.
   $`\max(0, \text{score} - 10)^2`$ gives much larger votes to sure faces than to faces near the threshold (score 11 gives 1 vote, 14 gives 16).
2. **Seeds**: for each face, painted pixels within $`10d`$ horizontally · vertically of the center that fall only in one character's head ellipse or body column. Pixels in two or more zones are removed from the seeds.
   - **Note** — **Why**: Growth must start from pixels that surely belong to each character for the boundaries to come out right. **How it works**: Seeds are pixels in only one character's head ellipse or body column; pixels where two characters' areas overlap are ambiguous and excluded. **References**: a rule set by this program
3. **Spreading**: from the seeds (distance 0), it spreads along paint · line pixels with 4-neighbors, and characters are decided by the shortest distance with a step cost $`1 + \mathrm{round}(30\,{\alpha_q}^2)`$ for entering pixel 𝑞 (𝛼 = line alpha).
   The costs are integers, so a bucket queue (32 buckets reused in rotation; enough since a step costs 31 or less) is used instead of <mark>Dijkstra</mark>. A dark line ($`\alpha = 1`$) costs 31 steps for one cell and is hard to cross.
   Unreached pixels (detached pieces, background) are filled with the nearest character by 4-neighbor <mark>breadth-first search</mark>.
   - **Note** — **Why**: Where two characters touch, the dark outline between them is the boundary. Splitting characters by shortest distance with lines made costly to cross makes the boundary follow the lines. **How it works**: The entry cost $`1 + \mathrm{round}(30\alpha^2)`$ grows with the square of the line alpha, so a solid line costs 31 steps and going around is cheaper. Each pixel goes to the character of the seed nearest in path cost. Costs are integers 1–31, so instead of <mark>Dijkstra</mark> a bucket queue cycling through 32 buckets indexed by distance (Dial's method) does it in $`O(V + E)`$. **References**: [R28 Dijkstra 1959](../README.en.md#r28) · [R29 Dial 1969](../README.en.md#r29)
4. Characters taking less than 5% of the character-side pixels are removed and 1–3 are redone.
5. Part pieces under 64 pixels in a character are moved to the character with the most of that part (so the tips of a neighboring character's parts do not become crumb layers).
6. For each character, [Line art] · [Effects] · [Painting] containing only its pixels are made. Characters do not share pixels, so the composite is the same as with one folder.

### Naming

For each character face (the group of 1 above), part pixels are counted per zone in the face frame $`(u, v)`$ at the original resolution (unit 𝑑, within $`3.6d`$ horizontally · vertically of the center).
When zones overlap, a pixel is counted in only one, in the order eye cell → skin → bangs → above → torso (the eye area separately). "Painted" is the share of the zone's pixels that are parts (non-background paint).
Fake faces of knees · hands · clothing patterns · background decorations put names on the wrong things because their cells sit on clothes · ribbons · props, so they are not used.

| Zone | Range |
|---|---|
| Eye cell | $`0.25 \le \lvert u\rvert \le 0.75,\ \lvert v\rvert \le 0.22`$ |
| Eye area (hair candidate decision) | $`0.2 \le \lvert u\rvert \le 0.8,\ \lvert v\rvert \le 0.35`$ |
| Skin (nose bridge · cheeks) | $`\lvert u\rvert \le 0.15,\ 0.1 \le v \le 0.5`$ or $`0.3 \le \lvert u\rvert \le 0.7,\ 0.35 \le v \le 0.7`$ |
| Bangs | $`\lvert u\rvert \le 0.8,\ -0.9 \le v \le -0.45`$ |
| Above (above the forehead · crown) | $`\lvert u\rvert \le 0.8,\ -1.6 \le v < -0.9`$ |
| Torso center | $`\lvert u\rvert \le 0.8,\ 2 \le v \le 3.5`$ |

**Note** — **Why**: What is painted at fixed places on the face reveals the skin, hair and eye parts. **How it works**: The cells are in face-frame coordinates (units of the eye distance 𝑑), so the same places are examined regardless of face size or tilt. Overlapping cells count each pixel in only one place in a fixed order, so no pixel votes twice. **References**: a rule set by this program

1. **Skin vote**: when the skin zone is at least half painted with parts, the widest part taking 35% or more of it.
2. **Hair candidates**: parts that are not the skin part, have an area of $`0.3d^2`$ or more (pieces like shadows on the whites of the eyes drop out), and have at least half their pixels outside the eye area (pupils drop out).
   - **Note** — **Why**: This keeps small pieces such as shadows on the eye white, and the irises, from being named hair. **How it works**: The area threshold $`0.3d^2`$ scales with the square of the eye distance, matching face size. **References**: a rule set by this program
3. **Hair vote**: when the bangs zone is at least half painted, the widest part with 40% or more of the candidate pixels and the next part with 30% or more (hair color + sheen).
   If the candidate pixels are under 25% of the bangs zone (forehead showing), the same selection is done in the zone above (when 10% or more of that zone is candidates).
   When the bangs are finely split into several colored parts and none can be chosen, the zone above is not looked at (the zone above often has hats).
4. **Skin and hair in one part**: if both zones are more than half painted and the skin part covers 80% or more of the bangs zone and 90% or more of the zone above (pale face + light hair),
   that part also gets the hair vote.
5. **Clothes mark**: parts covering 25% or more of the torso center.
6. **Eyes**: parts where the pixels inside the eye cells of character faces scoring 12 or more (excluding that face's skin · hair-vote parts), summed over all faces, are 30 pixels or more and at least half the part's area.
7. Parts that received votes are named, but
   - not if more than two thirds of their pixels are outside $`6d`$ from the character face center ($`(x - c_x)^2 + (y - c_y)^2 > 36d^2`$, counting one in every three pixels and multiplying by 3) (parts of one color with the floor · props).
     Long hair and the leg skin of full-body pictures can be more than half outside $`6d`$.
     - **Note** — **Why**: If floor or props share a color with a part near the face and were merged into it, naming that part skin or hair would be wrong. **How it works**: $`(x - c_x)^2 + (y - c_y)^2 > 36d^2`$ states "outside the circle of radius $`6d`$" without a square root. Counting every third pixel and multiplying by 3 is sampling to save time. **References**: a rule set by this program
   - not if they received both the skin vote and the hair vote.
   - "Skin" only for warm colors, "hair" only when there is no clothes mark. Names are looked at in the order skin → hair → eyes.
     With $`\mathrm{mx} = \max,\ \mathrm{mn} = \min`$ of the base color $`(r, g, b)`$ (0–1), a warm color ($`\mathrm{skinLike}`$) is

     $`\displaystyle mx=r\ \wedge\ mx\ge0.55\ \wedge\ \big(mx-mn\ge0.07\,mx\ \vee\ \text{pale skin}\big)\ \wedge\ \big(g\ge b-0.02\ \vee\ b-g<0.35\,(r-\min(g,b))\big)`$

     (the red channel is the brightest, saturation 7% or more, and the last term admits pink and excludes purple · blue).
     **Pale skin** ($`\mathrm{mx} \ge 0.85`$, $`\mathrm{mx} - \mathrm{mn} \ge 0.025\mathrm{mx}`$) is called "skin" only when the part's area is at most $`12 d_\max^2`$ (𝑑 of the largest character face) and at most $`0.13N`$.
     Pale skin easily merges into one part with white clothes · white hair, and then its area becomes much larger than a face · hands · limbs.
     - **Note** — **Why**: Even at the face position, parts that are not skin-colored (blue hair, purple clothes) must not be called "skin", so the color must look like skin. **How it works**: The red channel is the brightest (skin leans R > G > B) and bright enough (≥ 0.55), and $`\mathrm{mx} - \mathrm{mn} \ge 0.07\mathrm{mx}`$ is an HSV saturation of at least 7%. The last term accepts only when blue does not exceed green by much, admitting pink and excluding purple and blue. Pale skin easily merges with white clothes or hair, so it is called skin only when its area is not excessive for the face size (at most $`12d_\max^2`$). **References**: [R31 Smith 1978](../README.en.md#r31) · a rule set by this program
8. Parts with a meaning name are not put into the "small parts" folder even if small.
9. **Detaching separated hair pieces**: for each part 𝑘 named "hair",
   - **Anchors**: for each anchor face (character faces, and all faces scoring 11 or more: other people not included in the character group · a second appearance of the same person),
     the pixels reached along 𝑘 with 4-neighbors from the 𝑘 pixels inside the head ellipse $`(u/2.2)^2 + ((v + 0.3)/2)^2 \le 1`$ are kept.
   - **Nearby pieces**: among the 4-connected pieces 𝑐 (area $`A_c`$) of the 𝑘 pixels not kept, pieces whose pixel count $`B_c`$ in the central body column $`\lvert u\rvert < 1 \land v > 1.5`$ of a character face is $`B_c \le 0.5 A_c`$ and
     that have at least one pixel with <mark>chamfer distance</mark> (4.2) to the kept pixels of $`2.5 d_\max`$ or less ($`d_\max`$ = 𝑑 of the largest character face) are kept.
     The distance is measured again from the kept pieces and repeated up to three times until no new piece is kept.
     - **Note** — **Why**: If a "hair" part contains same-colored objects apart from the head (props, clothing trim), the name is wrong, so they are split off. **How it works**: Pixels connected through the part to a face's head ellipse (anchors) are kept, and unconnected pieces are kept as hair if within a <mark>chamfer distance</mark> of $`2.5d_\max`$ of the kept hair (tied or flying hair). Pieces more than half inside the central body column are likely clothing and are not kept. Split-off pixels move to a new part with the same base color, so layer pixels do not change. **References**: [R21 Borgefors 1986](../README.en.md#r21) · a rule set by this program
   - Pixels not kept are moved to a new part with the same base color (no meaning name). So the layer pixels and the composite do not change.
   - If the new parts push the number of parts that are not "small parts" over the maximum number of parts, that many new parts are marked as "small parts", from the smallest.
10. The remaining parts get the color name of their base color. The 8-bit base color is converted to HSV ($`V = \mathrm{mx},\ S = (\mathrm{mx} - \mathrm{mn})/\mathrm{mx}`$, 𝐻 0–360°) and checked in order.

    | Condition | Name |
    |---|---|
    | $`V < 0.18`$ | black (검정) |
    | $`S < 0.1`$ | white (흰색) if $`V > 0.9`$, otherwise gray (회색) |
    | $`5^\circ \le H \le 45^\circ,\ 0.08 \le S \le 0.55,\ V \ge 0.7`$ (flesh tone) | beige (베이지) if $`S < 0.25`$, otherwise apricot (살구) |
    | $`H < 15^\circ`$ or $`H \ge 345^\circ`$ | $`V < 0.45`$ brown (갈색), $`S < 0.5 \land V > 0.8`$ pink (분홍), otherwise red (빨강) |
    | $`H < 40^\circ`$ | $`V < 0.6`$ brown, otherwise orange (주황) |
    | $`H < 65^\circ`$ | $`V < 0.5`$ brown, otherwise yellow (노랑) |
    | $`H < 160^\circ`$ · $`< 200^\circ`$ · $`< 255^\circ`$ · $`< 290^\circ`$ · otherwise | green (초록) · teal (청록) · blue (파랑) · purple (보라) · pink (분홍) |

    $`H = 60^\circ \times((g - b)/(\mathrm{mx} - \mathrm{mn}) \bmod 6)`$ ($`\mathrm{mx} = r`$), $`60^\circ \times((b - r)/(\mathrm{mx} - \mathrm{mn}) + 2)`$ ($`\mathrm{mx} = g`$), $`60^\circ \times((r - g)/(\mathrm{mx} - \mathrm{mn}) + 4)`$ ($`\mathrm{mx} = b`$).
    Flesh tones are called "beige · apricot", not "skin".
    Flesh-toned hair (blond · light brown) · flowers · trees · snacks · rooms are common, so calling a color "skin" without a face is mostly wrong (11).
    If several parts share a name, they are "name", "name 2", "name 3" … from the widest part.

    **Note** — **Why**: Color names on parts without a semantic name make them easy to find in the layer list. **How it works**: HSV unfolds the RGB cube onto a hue circle. 𝑉 is the largest channel, 𝑆 is $`(\mathrm{mx} - \mathrm{mn})/\mathrm{mx}`$, and 𝐻 picks a 60° sector by which channel is largest and the position within it from the difference of the other two (red 0°, green 120°, blue 240°). The table checks darkness, then achromatic, then skin tones, then hue ranges. **References**: [R31 Smith 1978](../README.en.md#r31) · a rule set by this program

## 4.9 Per-pixel inversion

For a pixel of part 𝑘 at tone level 𝑣, the painted color is

```math
x_c=F_c\cdot(sh^1_c)^{[v\ge1]}\cdot(sh^2_c)^{[v=2]}\qquad(x_c=\text{tone color for a highlight tone})
```

**Note** — **Why**: Inversion starts from "the painted color the layers produce". The tone step decides how many shadows multiply the base. **How it works**: $`[v \ge 1]`$ is the Iverson bracket, 1 when true; as an exponent it turns that multiplication into 1 (no multiply) when false. The lit side (𝑣 = 0) is 𝐹, first shadow $`F\cdot sh^1`$, second $`F\cdot sh^1\cdot sh^2`$. **References**: [R1 Porter · Duff 1984](../README.en.md#r1) · a rule set by this program

Compared with the restored color $`u = U_c`$, the remaining darkening 𝐷 and brightening 𝑆 are found. Brightening of 1/255 or less is treated as quantization noise.

```math
u\le x+\tfrac{1.2}{255}:\quad D_c=1-\mathrm{clamp}\!\left(\frac ux\right);\qquad
u> x+\tfrac{1.2}{255}:\quad S_c=\mathrm{clamp}\!\left(1-\frac{1-u}{1-x}\right)
```

Multiply gives $`x(1 - D) = u`$ and screen gives $`1 - (1 - x)(1 - S) = u`$, so both cases return exactly to the original.
If $`x \le 0.002`$ (almost black), $`D_c = 0`$, and if $`x \ge 0.9999`$ (white), $`S_c = 0`$, to avoid dividing by 0. $`d_\max = \max_c D_c,\ S_\max = \max_c S_c`$.
Highlight tone colors use the 8-bit-rounded value ($`q_8`$). The alpha of the base color · shadow layers is the original alpha 𝐴; sparkle pixels are painted on the base color side rather than as highlights and then taken out as brightening.

**Note** — **Why**: The remaining difference between the layered color and the original goes into multiply and screen layers, so combining all layers restores the original exactly. **How it works**: Solving multiply $`x(1 - D) = u`$ for 𝐷 gives $`D = 1 - u/x`$, and screen $`1 - (1 - x)(1 - S) = u`$ for 𝑆 gives $`S = 1 - (1 - u)/(1 - x)`$. A darker original uses multiply and a lighter one screen, so only one applies. 1.2/255 is a margin so only brightening larger than 8-bit rounding noise counts, and when 𝑥 is near 0 or 1 the value is set to 0 to avoid dividing by zero. **References**: [R1 Porter · Duff 1984](../README.en.md#r1) · [R3 ISO 32000-1 2008](../README.en.md#r3)

## 4.10 Gradient and shading

For $`d_\max = \max_c D_c`$, with the outside of the character set to 1,

```math
\mathrm{env}=G_{R/2}\big(\mathrm{erode}_R(d_{max})\big),\quad R=\max(8,\,\mathrm{round}(24s)),\qquad
f=\frac{\min(d_{max},\mathrm{env})}{d_{max}}\quad(d_{max}>0)
```

```math
D^{grad}_c=f\,D_c,\qquad D^{shade}_c=\mathrm{clamp}\!\left(1-\frac{1-D_c}{1-D^{grad}_c}\right)
\quad\Longrightarrow\quad (1-D^{grad}_c)(1-D^{shade}_c)=1-D_c
```

**Note** — **Why**: The remaining darkening mixes broad, slowly varying parts (atmosphere, large shading) with narrow brush touches. Splitting the broad part into a gradient layer and the rest into a shading layer makes it easier for artists to handle. **How it works**: Erosion with radius 𝑅 is the minimum over 𝑅, which removes narrow spikes of darkening and keeps the broad floor (lower envelope), then a Gaussian blur smooths it. 𝑓 multiplies all channels, so the gradient has the same color direction as the darkening. The rest is the inverted multiply so that $`(1 - D^{grad})(1 - D^{shade}) = 1 - D`$: multiplying the two layers reproduces the original darkening. **References**: [R15 Soille 2003](../README.en.md#r15) · [R1 Porter · Duff 1984](../README.en.md#r1)

(If $`D^{grad}_c \ge 0.9999`$, $`D^{shade}_c = 0`$.) The same 𝑓 multiplies every channel, so the gradient is a part of the darkening in the same color direction.

Erosion makes the lower envelope (the minimum darkening spread widely), and blurring smooths it.
If pixels with $`\min(d_\max, \mathrm{env}) > 12/255`$ are fewer than $`\max(24, 0.3\%\text{ of character pixels})`$, the gradient layer is not made ($`f = 0`$) and one shading layer remains.

**Note** — **Why**: No empty layer is made for pictures with almost no gradient. **How it works**: Fewer gradient pixels above 12/255 than 24 or 0.3% of the character means no layer. At $`D^{grad} \ge 0.9999`$ the division is unstable, so the shading is set to 0. **References**: a rule set by this program

## 4.11 Splitting brightening

Screen stacked in sequence is $`1 - \prod(1 - a_i)`$, so taking off a part with weight 𝑤,

```math
a=S\,w,\qquad S'=\mathrm{clamp}\!\left(1-\frac{1-S}{1-a}\right)\quad(S'=0\text{ if }a\ge0.9999)\qquad\Longrightarrow\qquad 1-(1-a)(1-S')=S
```

is repeated per channel to split in order ($`S^{(0)} = S,\ a_i = S^{(i-1)}w_i,\ S^{(i)} = S'`$).

**Note** — **Why**: Splitting one brightening into several screen layers (sparkle, rim light, reflected light, light) must still reproduce the original brightening exactly when combined. **How it works**: Screen combines as $`1 - \prod(1 - a_i)`$ regardless of order. Taking $`a = Sw`$ for weight 𝑤 and computing the remainder $`S'`$ by inverse screen makes $`1 - (1 - a)(1 - S') = S`$ an identity. Repeating per layer makes the screen combination of all layers equal the original 𝑆. **References**: [R3 ISO 32000-1 2008](../README.en.md#r3) · [R1 Porter · Duff 1984](../README.en.md#r1)

| Order | Layer | Weight 𝑤 |
|---|---|---|
| 1 | Sparkle (small pieces) | sparkle pixels, or among connected pieces with $`S > 3/255`$, area $`\le 3\pi r_s^2`$, maximum $`S > 0.25`$, mean $`\min_c U > 0.65`$, maximum top-hat $`> 0.12`$ |
| 2 | Rim light | $`\mathrm{smoothstep}(R_r, 0.4R_r, e) \cdot \mathrm{clamp}((S_\max - \bar O)/S_\max)`$ |
| 3 | Sparkle (thin gloss) | $`\mathrm{smoothstep}(0.08, 0.2, T) \cdot \mathrm{smoothstep}(0.55, 0.8, \min_c U_c)`$ |
| 4 | Reflected light | 1 for shadow pixels |
| 5 | Light | everything else |

**Note** — **Why**: Each kind of brightening looks different (sparkles small and bright, rim light at the silhouette edge, thin gloss as fine structure revealed by a top-hat, reflected light inside shadows), so weights come from those features. **How it works**: $`\mathrm{smoothstep}(R_r, 0.4R_r, e)`$ is smoothstep with its ends reversed: 1 within $`0.4R_r`$ of the edge, easing to 0 beyond $`R_r`$. $`(S_\max - \bar O)/S_\max`$ is the share of brightening above the interior average, close to 1 for light found only at the edge. Thin gloss multiplies two smoothsteps, of the top-hat 𝑇 and of paleness ($`\min_c U`$), so it is large only when both hold. **References**: [R47 Ebert et al. 2003](../README.en.md#r47) · [R15 Soille 2003](../README.en.md#r15) · a rule set by this program

- 𝑒 is the number of steps measured inward from the silhouette (character pixels with a non-character pixel among their 4-neighbors, $`e = 0`$), $`R_r = \max(4, \mathrm{round}(12s))`$.
  Pictures with neither background nor transparency have no silhouette, so no rim light is made.
  - **Note** — **Why**: Rim light clings to the silhouette edge, so how far inside the edge a pixel is must be known. **How it works**: 𝑒 is the step count of a 4-neighbor breadth-first search from the silhouette. $`R_r = \max(4, \mathrm{round}(12s))`$ is a length, so it is multiplied by the size ratio 𝑠. **References**: [R14 Gonzalez · Woods 2018](../README.en.md#r14) · a rule set by this program
- $`\bar O`$ is the local mean of the brightening inside the edge ($`e > R_r`$). With 𝑚 = the indicator of (character and $`e > R_r`$),

  $`\displaystyle \bar O=\begin{cases}\dfrac{G_{1.5R_r}(m\,S_{max})}{G_{1.5R_r}(m)} & G_{1.5R_r}(m)>0.02\\[4pt] 0 & \text{otherwise}\end{cases}`$

  Bright only at the edge ($`S_\max \gg \bar O`$) means rim light; similarly bright inside too means wide light.
  - **Note** — **Why**: Whether edge light is rim light or part of broad light is decided by comparing it with the average brightening further inside. **How it works**: $`G(mS)/G(m)`$ is a weighted average over only the pixels where the mask 𝑚 is 1 (normalized convolution), so near the edge the zeros outside (outside the character, the edge band) do not drag the average down. A denominator at or below 0.02 means almost no interior pixels nearby, so 0 is used. **References**: [R32 Knutsson · Westin 1993](../README.en.md#r32) · [R14 Gonzalez · Woods 2018](../README.en.md#r14)
- $`T = \mathrm{lum}(U) - \mathrm{open}(\mathrm{lum}(U))`$ (white top-hat, $`\mathrm{open}`$ = erosion then dilation with radius $`r_s`$): only bright structures thinner than the sparkle size remain.
  - **Note** — **Why**: Only bright strands thinner than the sparkle size, such as gloss on hair, must be picked out. **How it works**: Opening (erosion then dilation) removes bright structures thinner than the window, so the white top-hat, the original minus its opening, keeps only those thin bright structures. **References**: [R15 Soille 2003](../README.en.md#r15) · [R14 Gonzalez · Woods 2018](../README.en.md#r14)
- The "mean $`\min_c U`$" of a sparkle piece is the mean of $`\min(U_R, U_G, U_B)`$ over the piece's pixels (larger for paler colors).
- The values sent to layers are, per channel, sparkle $`1 - (1 - a_1)(1 - a_3)`$ (the two sparkles combined by screen), rim light $`a_2`$, reflected light $`a_4`$, light $`S^{(4)}`$.
  - **Note** — **Why**: The two kinds of sparkle (small pieces, thin gloss) are output as one layer to reduce the layer count. **How it works**: Combining the two screen values as $`1 - (1 - a_1)(1 - a_3)`$ gives the same result as laying them separately. A piece's "mean $`\min_c U`$" averages the darkest channel, so it is larger the closer to white light. **References**: [R3 ISO 32000-1 2008](../README.en.md#r3)

Rim light · reflected light are not made ($`w = 0`$) and stay in light if pixels with a channel maximum over 12/255 are fewer than $`\max(24, \mathrm{round}(0.003 \times \text{number of character pixels}))`$.

**Note** — **Why**: No empty layer is made for pictures with almost no rim or reflected light. **How it works**: If fewer pixels than 24 or 0.3% of the character exceed 12/255, that share stays in the light layer. **References**: a rule set by this program

## 4.12 Minimum-alpha storage

When the pixel value 𝑣 (0–1 per channel) of a multiply · screen layer is stored as "color 𝐾 + alpha 𝑎", the smallest alpha is used.

```math
a=\frac{\max(1,\ \mathrm{round}(255\max_c v_c))}{255},\qquad K_c=\mathrm{clamp}\!\left(\frac{v_c}a\right),\qquad
K^{(8)}_c=\mathrm{round}(255K_c),\quad a^{(8)}=\mathrm{round}(255\,a\,A)
```

Pixels with $`255 \max_c v_c < 0.5`$ are left empty. The largest channel becomes the alpha and that channel's 𝐾 is 1, so no smaller alpha can produce the same value.
Screen composites as $`1 - (1 - x)(1 - aK)`$ and multiply as $`x(1 - a + aK)`$, so multiply layers (gradient · shading) store the 𝐾 found with $`v = D`$ as $`K \gets 1 - K`$ (in 8 bits, $`255 - K^{(8)}`$).
The smaller the alpha, the more transparent the layer looks, so it looks like a layer an artist painted lightly and is easy to touch up.
Layers with fewer than 24 pixels of alpha over 8/255 are treated as empty and not made.

**Note** — **Why**: Many color–alpha pairs give the same effect; storing the pair with the smallest alpha makes the layer as transparent as possible, so it looks like a lightly painted layer and is easy to edit. **How it works**: Screening color 𝐾 at alpha 𝑎 has effect $`aK`$, so $`aK_c = v_c`$ must hold, and since $`K_c \le 1`$, $`a \ge \max_c v_c`$. Hence the largest channel value is the smallest alpha, and that channel's 𝐾 is 1. A multiply layer composites as $`x(1 - a + aK')`$, so storing $`K' = 1 - K`$ gives $`a(1 - K') = aK = D`$, the same formula. Multiplying the 8-bit alpha by the original alpha 𝐴 leaves no effect on transparent areas. **References**: [R1 Porter · Duff 1984](../README.en.md#r1) · [R2 Smith 1995](../README.en.md#r2) · [R3 ISO 32000-1 2008](../README.en.md#r3)

The other layers are stored as follows (all 8-bit, cropped to the smallest rectangle enclosing pixels with non-zero alpha).

| Layer | Color | Alpha |
|---|---|---|
| Base color | part base color | $`\mathrm{round}(255A)`$ |
| 1st · 2nd shadow | $`\mathrm{round}(255 \mathrm{sh}^1)`$ · $`\mathrm{round}(255 \mathrm{sh}^2)`$ | $`\mathrm{round}(255A)`$ on level 1 · 2 pixels for the 1st, level 2 pixels for the 2nd |
| Highlight | $`\mathrm{round}(255 \cdot \text{tone mean})`$ | $`\mathrm{round}(255A)`$ on highlight pixels |
| Line art | $`K^0`$ (line art + color trace), per-pixel 𝐾 (original line colors), 0 (black) | $`\mathrm{round}(255 \cdot a \cdot A)`$ |
| Color trace (clipped to line art) | per-pixel 𝐾 | 255 |
| Background | 𝑈 ($`\mathrm{base}`$ at background-effect · glow places) | 255 |
| Outer glow | 𝑈 | 255 |
| Silhouette (hidden) | gray 160 | $`\mathrm{round}(255A)`$ |

**Note** — **Why**: The other layers are stored as ordinary PSD layers (normal blending), so their 8-bit color and alpha must be set. **How it works**: Colors are 0–1 values times 255, rounded, and alpha uses the original alpha 𝐴 the same way. Shadow layers get alpha only at pixels of the matching tone step (first: 1 and 2, second: 2), so the multiply applies only where needed. Each layer is cropped to the smallest rectangle with nonzero alpha to keep the file small. **References**: [R4 Adobe PSD](../README.en.md#r4) · a rule set by this program

## 4.13 Reproduction check

The picture is recomposited from the 8-bit values exactly as they will be stored.

```math
v=\big(F\cdot sh^1\cdot sh^2\ \text{or highlight}\big)\times\prod_{\text{grad, shade}}(1-a+aK)
\ \to\ 1-(1-v)\prod_{\text{refl, rim, spark, fx}}(1-aK)
\ \to\ v(1-a_\ell)+a_\ell K_\ell
```

Background pixels are $`v = \text{background} \to 1 - (1 - v)(1 - aK)`$ (background effect) $`\to v(1 - a_g) + a_g K_g`$ (outer glow). Here 𝑎 and 𝐾 are all the stored 8-bit values divided by 255.

**Note** — **Why**: Recombining the saved layers in Photoshop's order and with its blend formulas lets the program check that the result equals the original. **How it works**: The color made from base, shadows and highlight is multiplied by the multiply layers (gradient, shading) $`(1 - a + aK)`$, the screen layers (reflected light, rim light, sparkle, light) are applied as $`1 - (1 - v)\prod(1 - aK)`$, and the line art covers it by normal blending $`v(1 - a_\ell) + a_\ell K_\ell`$. All values are the stored 8-bit values divided by 255, so this matches what opening the file gives. **References**: [R1 Porter · Duff 1984](../README.en.md#r1) · [R3 ISO 32000-1 2008](../README.en.md#r3) · [R4 Adobe PSD](../README.en.md#r4)

```math
\mathrm{MSE}=\frac1{3n}\sum_{p:\,A_p>0.98}\ \sum_c\big(255\,(v_c(p)-O_c(p))\big)^2,\qquad
\mathrm{PSNR}=10\log_{10}\frac{255^2}{\mathrm{MSE}}
```

𝑛 is the number of opaque pixels (alpha $`> 0.98`$). If $`\mathrm{MSE} \le 10^{-9}`$, <mark>PSNR</mark> is set to 99 and shown as "∞" on screen.

**Note** — **Why**: This gives one number for how exact the reconstruction is. **How it works**: MSE is the mean squared difference in 8-bit units over opaque pixels and channels, and <mark>PSNR</mark> $`= 10\log_{10}(255^2/\mathrm{MSE})`$ expresses the ratio of the squared peak signal (255) to the error in dB. It rises as the error shrinks; zero error would be infinite, so 99 is stored and "∞" shown. Semi-transparent pixels are excluded because their visible color depends on what is beneath. **References**: [R55 Huynh-Thu · Ghanbari 2008](../README.en.md#r55) · [R14 Gonzalez · Woods 2018](../README.en.md#r14)

---

[← README](../README.en.md#4-algorithms-and-formulas) · Next: [4.14 Rough generation](4-4-rough-psd-tools.en.md)
