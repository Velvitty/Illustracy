# Illustracy — 4. Algorithms and formulas (2/4): Background

[← README](../README.en.md#4-algorithms-and-formulas) · Section 4 [1](4-1-basics.en.md) · **2** · [3](4-3-regions-layers.en.md) · [4](4-4-rough-psd-tools.en.md) · [한국어](4-2-background.md)

---

## 4.5 Background

### Find at reduced size (setting, off by default)

With "Find only background · faces at reduced size" and $`\max(W, H) > S`$ (the target size), the background stages below and face finding alone run on a picture with each channel area-averaged down by $`k = S / \max(W, H)`$
(the line width is the user's chosen value times 𝑘, or measured again on the reduced picture if automatic). The background · returned-part maps are enlarged back to the original size <mark>bilinearly</mark> and turned on where $`\ge 0.5`$,
but on the original-size lines (+ 1px edge) only where the enlarged value is 1. Faces have their position · size multiplied by $`1/k`$.
"Reduce everything" is the same as lowering the processing resolution to $`\min(\text{processing resolution}, S)`$.

### Frame

Let $`\kappa(d)`$ be the share of $`\mathrm{known}`$ pixels on the ring around the border (the ring at depth 𝑑 = the perimeter of the rectangle 𝑑px in from the edge).
If $`\kappa(0) < 0.05`$ and the long and short sides are larger than 16px, the first 𝑑 in $`d = 1 \dots \max(3, \mathrm{round}(0.01 \cdot \max(W, H)))`$ with $`\kappa(d) \ge 0.5`$ is the frame thickness 𝑓.
If $`f > 0`$, only during the background stages (everything below, and face finding), each pixel within 𝑓px of the edge has its 𝑈, original, $`\mathrm{known}`$, line, crisp line, and $`\mathrm{inMask}`$ replaced by the values of the nearest
inner pixel ($`(\mathrm{clamp}(x, f, W - 1 - f), \mathrm{clamp}(y, f, H - 1 - f))`$), restored at the end. Not done for transparent pictures.
3 of the 666 pictures had $`\kappa(0) < 0.05`$, and a frame was found in 2 of them ($`f = 2\,\mathrm{px}`$).

### Rotated canvas (0.37)

1. If at least three of the four corner pixels are the same fill, it is treated as a fill: at least three transparent ($`A \le 0.02`$), or at least three opaque ($`A \ge 0.98`$) with mutual $`\max_c`$ difference $`\le 4/255`$.
   $`F_0`$ is taken by following pixels equal to the fill from the corners with 4-neighbors.
2. For each row 𝑦, the first · last 𝑥 not in $`F_0`$ ($`x_l(y),\ x_r(y)`$), and for each column 𝑥, the first · last 𝑦 ($`y_t(x),\ y_b(x)`$) are collected.
   For a rotated rectangle, $`x_l`$ is two straight lines bending at its minimum, and $`x_r`$ two straight lines bending at its maximum (likewise $`y_t,\ y_b`$).
   For each bend candidate (the minimum · maximum and 15 evenly spaced positions), both sides are fitted with least-squares lines, points deviating more than $`\tau = 1.5 + 0.002 \cdot \max(W, H)`$px from the line are removed, and it is refitted twice.
   The candidate with the most fitting points (within 𝜏) is chosen, and if fewer than 85% of points fit, it is not a rotated canvas (white paint touching the picture edge connects to the fill and becomes deviating points).
3. Content = pixels with $`\max(l_1(y), l_2(y)) - 0.5 \le x \le \min(r_1(y), r_2(y)) + 0.5`$ and $`\max(t_1(x), t_2(x)) - 0.5 \le y \le \min(b_1(x), b_2(x)) + 0.5`$; the fill region 𝐹 = the rest.
   It is used only if 𝐹 is 1–70% of the picture and at least 97% of 𝐹 is actually the fill color.
4. Tilt 𝜃: the direction angles 𝛼 of the eight lines (for row ends, from the slope $`m = dx/dy,\ \alpha = \mathrm{atan2}(1, m)`$; for column ends, $`\alpha = \mathrm{atan2}(m, 1)`$) are averaged as quadrupled angles, $`\theta = 1/4 \cdot \mathrm{atan2}(\sum \sin 4\alpha, \sum \cos 4\alpha)`$ (−45°–45°, clockwise positive).
   The rectangle's sides alone cannot distinguish 𝜃 from $`\theta \mp 90^\circ`$. If $`\lvert \theta \rvert < 1^\circ`$ (untilted margins · letterboxes), it is not used.
5. Only during the background stages (everything below, and the stages after face finding), each pixel of the band $`B = F \oplus 7\times 7`$ (𝐹 widened by 3px: mixed colors · outliers at the boundary created by rotation) has
   its 𝑈, original, alpha, $`\mathrm{known}`$, line, crisp line, and $`\mathrm{inMask}`$ replaced by the values of the nearest pixel outside 𝐵 by 4-neighbor <mark>breadth-first search</mark>, restored at the end.
   Then 𝐹 is set as background (removed from returned parts). Even with transparent corners, the background is searched for, and "send to background" also works. The background layer's alpha is the original alpha (255 as is for opaque pictures).
6. Faces are searched for in the picture before filling.

### The picture's down direction (0.37)

When there is a tilt hypothesis (rotated canvas or the "Tilted picture" setting), the down directions 𝑓 of the naming faces (mirror-agreed) are averaged with weights $`w = \max(0, s - 10)^2`$,
and if $`\bar g = \sum w f / \sum w`$ has $`\lvert \bar g\rvert \ge 0.8`$ (the faces agree) and is tilted more than 40° from vertical, $`g = \bar g / \lvert \bar g\rvert`$ is used as the down direction.
- For the outward direction 𝑛 of a border pixel (top $`(0, -1)`$ · right $`(1, 0)`$ · bottom $`(0, 1)`$ · left $`(-1, 0)`$, both at corners), the side with $`n \cdot g \ge 0.5`$ is the "bottom" border.
  The bottom-border rule of the flat background (1) and the seeds of the scene background (stage 1 starts without the "bottom" border) use this border.
- The "upper corners" excluded when restoring cropped parts are the corners with corner direction $`(s_x, s_y) \in \lbrace\pm 1\rbrace^2`$ satisfying $`(s_x g_x + s_y g_y) / \sqrt 2 < -0.4`$.
- 40° is larger than the maximum tilt of faces found without a tilt hypothesis (pair filter $`\lvert \Delta y\rvert \le 0.8\Delta x`$, 38.7°), so it is never used for upright pictures without a tilt hypothesis.

### Flat · gradient background

1. The $`\mathrm{known}`$ pixel colors on the border are counted in per-channel 16-level bins $`q(U) = 256\lfloor 15.99U_R\rfloor + 16\lfloor 15.99U_G\rfloor + \lfloor 15.99U_B\rfloor`$ (4096 bins), and the average of the fullest bin is the reference color 𝑟.
   It gives up if there are fewer than 16 $`\mathrm{known}`$ border pixels, or if fewer than 45% of them have $`\max_c\lvert U_c - r_c\rvert < 0.1`$.
2. Starting from border pixels with $`\max_c\lvert U - r\rvert < 0.12`$, it spreads into $`\mathrm{known}`$ pixels with neighbor-to-neighbor change $`< 0.035 \cdot k`$ and difference from the starting reference color $`< 0.3`$ (each pixel carries its own reference color while spreading).
   $`k = \min(1, 1200 / \max(W, H))`$ is the size ratio (1 for a long side of 1200px or less). If $`k < 1`$ and the area condition of 4 fails, 1–4 are redone with $`k = 1`$.
   It spreads first from the top · right · left borders and then from the bottom border; among 4-connected components newly reached only from the bottom border, those with 5% or more pixels having $`\max_c\lvert U - r\rvert > 0.04`$ are removed from the background.
   White clothes · skirts reaching the bottom edge of the picture have shading · folds even if as white as the background, while a white floor · margin on the bottom border is almost one color.
3. Walking along the border (the path going once around top → right → bottom → left) twice in both directions, $`\mathrm{known}`$ pixels within 64 cells of the last background pixel on the path and with $`\max_c`$ difference $`< 0.05`$ from its color
   are added as new seeds (their own color as reference) and it spreads again with tolerance 0.12 (until there are no new seeds, at most 3 times). The walk is broken when it meets a line (a pixel that is not $`\mathrm{known}`$).
   - **Floor band** (0.40): the known pixels on the left, right and bottom borders that are not yet background are counted in the same 4096 bins as in 1; if the fullest bin holds 10% or more of the known border pixels, its average is a second reference color r₂.
     If border pixels within a channel-max difference of 0.12 from r₂ make up at least 3% of the height on the left and on the right, and at least 30% of the width on the bottom, the area spread from them under the same conditions as 2 (neighbor change < 0.035k, difference from r₂ < 0.3) is the band F.
     For each column x the topmost pixel t(x) of F is taken, and a line y = a·x + b is fitted on 64 evenly chosen columns with a = the median of the slopes between every two columns and b = the median of t(x) − a·x (<mark>Theil–Sen</mark>; columns hidden by the character, where t(x) sags lower, do not move the medians).
     F is added to the background if it covers at least 3% and at most 60% of the picture, at least 60% of the columns are within τ = max(3, 0.01H)px of the line, and at most 2% of F's pixels are more than τ above the line. It is not done for rotated pictures (whose downward direction is set).
     The floor of a line-drawn room, differing in color from the wall, is caught here, while clothes · hair crossing the bottom of the picture have a curved top edge and too few columns on the line. On the 666 pixiv pictures, all 7 pictures that reached this check were stopped by the straight-top-edge condition.
     **Fallback line** (0.43): if these conditions fail while F is 3–60% of the picture (the character hides much of the floor and the Theil-Sen line wavers), among the lines through two of the 64 columns,
     the one with at most one column more than τ above it and the most columns within τ is chosen. If 25% or more of the width lies within τ of it, at least half of the leftmost and of the rightmost 10% of columns each lie within τ
     (the wall-floor line crosses the picture), and no more than 2% of F is more than τ above it, F is added to the background. On the 777 real pictures no picture changed through this line.
4. It is used only if the area is 3–97% of the whole.
5. **Closing narrow gaps** (0.34): if the background found by 1–4 is bright and almost one color (median $`L^*`$ of at most about 20,000 background $`\mathrm{known}`$ pixels $`\ge 70`$,
   share within $`\Delta E < 10`$ of that median color $`\ge 0.6`$, the same formula as "almost one color" in face-based widening), 1–4 are redone with the same thresholds,
   but it does not spread into $`\mathrm{dilate}_g(B)`$, the wall $`B = \lnot\mathrm{known} \lor(\text{change to the right · lower neighbor} \ge 0.035k)`$ dilated by $`g = \max(2, \mathrm{round}(2 \cdot \max(W, H)/1200))`$.
   After spreading, $`\mathrm{known}`$ pixels up to $`g + 1`$ steps from the background are restored with the original spreading conditions (neighbor change $`< 0.035k`$ and difference from the reference color $`< 0.3`$).
   The fill cannot cross outlines broken by $`2g`$ or less (faint lines, anti-aliasing gaps), and the background around the walls is filled again by the restoration.
   If the redone result fails the area condition of 4, the first result is used.
   For scene · patterned backgrounds, single-step color differences become walls here and there and the fill breaks up, and for dark one-color backgrounds (night scenes), background objects beyond the closed gaps return to the character, so it is not done (7.5).

### Scene background

Line density is the value blurred with $`\sigma = 0.02 \cdot \max(W, H)`$. If line pixels are fewer than $`0.002N`$, the scene background is not searched for.

**Degree of enclosure by lines** $`\varepsilon(p)`$: the line map is reduced to $`S = 240`$ cells on the long side ($`w = \max(2, \mathrm{round}(240W / \max(W, H)))`$, ℎ likewise;
pixel $`(x, y)`$ falls in cell $`(\min(w - 1, \lfloor xw/W\rfloor), \min(h - 1, \lfloor yh/H\rfloor))`$, and a cell is a wall if it contains even one line pixel).
From each cell, it goes straight in 16 directions $`\theta_k = 2\pi k/16`$ for $`t = 1 \dots 60`$ cells (25% of the long side) ($`(\mathrm{round}(x + t \cos \theta_k), \mathrm{round}(y + t \sin \theta_k))`$); if the first thing it meets is a wall, the direction is blocked,
and if it leaves the picture or meets no wall within 60 cells, the direction is open. 𝜀 is the share of blocked directions, and a pixel's value is that of its cell.
**Enclosed places** are $`\varepsilon \ge 0.9`$ (15 or more of 16 directions). The number of cells does not depend on the picture size, so it takes 0.1–0.3 seconds for any picture (longer with sparser lines).

```math
D_a=G_\sigma(\mathbb 1_{line}),\quad D_c=G_\sigma(\mathbb 1_{crisp}),\quad D_s=G_\sigma(\mathbb 1_{line\wedge\neg crisp}),\qquad
\tau_a=\tfrac14\,\mathrm{median}_{line}D_a,\quad \tau_c=\tfrac14\,\mathrm{median}_{crisp}D_c
```

The median is $`i/1000`$ for the first bin 𝑖 where the cumulative count reaches half in the 1001-bin histogram of $`\mathrm{round}(1000D)`$ ($`\tau_c = 0`$ if there are no crisp lines).

- **Stage 1 candidates**: $`\mathrm{known} \land D_a < \tau_a \land \varepsilon < 0.9`$. The candidates are eroded by $`r = \max(2, \mathrm{round}(3s))`$, filled from the top · left · right borders, and restored within the original candidates by the eroded amount (+1). It does not leak through narrow gaps.
- **Blocking the flat background edge** (0.37): the flat · gradient background $`B_1`$ (above), plus pixels connected to it with 4-neighbors within 3 steps and with $`\max_c\lvert \Delta U_c\rvert < 0.06`$ from the $`B_1`$ pixel they started from,
  form the "background-like pixels" $`\tilde B`$ (the flat background stops 2px before crisp edges, so this includes the space in between).
  In the stage 1 · 2 fills (both filling from the eroded candidates and restoring), a step $`p \to q`$ is blocked when $`q \notin \tilde B`$ and either $`p \in \tilde B`$ or the pixel one step back $`p' = 2p - q`$ is in $`\tilde B`$,
  and the $`\max_c\lvert \Delta U_c\rvert`$ between that pixel and 𝑞 is 0.1 or more (up to a 1–2px blended edge). Not done when there is no $`B_1`$; margin widening · the color model are unchanged.
- **Blocking before dark places** (0.42): in the same stage 1 · 2 fills (also when searching again without 𝜀), a step $`p \to q`$ is also blocked when, in the Lab of 𝑈 (the same values as crisp edges), $`L^*_q \le 35`$ and either $`\Delta E(p, q) \ge 20`$
  or, for the pixel one step back $`p' = 2p - q`$ (when it is inside the picture without wrapping to another row), $`\Delta E(p', q) \ge 20`$. Done even without $`B_1`$; with $`B_1`$ it is used together with the blocking above.
  Only whether the arriving pixel is dark is checked. Also blocking when the starting pixel is dark made $`\mathrm{BER}`$ worse by 0.226 on one ground-truth picture (0.42 in 12).
- **Widened blocking before dark places** (0.43): after the scene background is found, stages 1 · 2 are filled once more with the blocking above also checking the pixel two steps back $`p'' = 3p - 2q`$ (when inside the picture without wrapping to another row) with $`\Delta E(p'', q) \ge 20`$.
  From the two results before the area criterion and returning swallowed characters, $`S`$ and $`S_3`$, the pixels of $`S \land \lnot S_3`$ that are not flat background are remembered and, after all background stages, put back on the character side unless they are gaps (below).
  The other stages still run on $`S`$, so only these pixels change (changing the scene background itself shifted the color statistics of later stages and disturbed other places, 0.43 in 12). Searching the scene background once more costs time: 2.7% on 8 real pictures.
- **Returning islands in the scene background** (0.38): if $`B_1`$ exists, the finished scene background 𝑆 (after returning swallowed characters and passing the area criterion) is split into 4-neighbor connected components (islands) of $`S \land \lnot \tilde B`$,
  and the islands containing no top · left · right border pixel form $`\mathcal I`$ (if the picture's down direction is set, the border pixels that are not the bottom border for that direction, 4.5).
  Splitting the character lump $`C = \lnot(B_1 \lor S) \lor \bigcup \mathcal I`$ into 4-neighbor connected components with largest area $`\lvert C_\max \rvert`$, an island $`I \in \mathcal I`$ is removed from 𝑆 when the component $`C(I)`$ containing it
  has $`\lvert C(I)\rvert/ \lvert C_\max \rvert \ge 0.25`$ or contains the center $`(\mathrm{round}(c_x), \mathrm{round}(c_y))`$ of a found face (4.5) (it is also removed from the scene background before returning swallowed characters).
  Then 𝑆 is merged into $`B_1`$. In real pictures, the components of floating text · emblems had $`\lvert C(I)\rvert/ \lvert C_\max \rvert \le 0.04`$.
- **Stage 2 candidates**: $`\text{stage 1 candidates} \cup (D_c < \tau_c \land D_s \ge 0.085 \land(\mathrm{known} \lor \text{faint line}))`$. Filled the same way from the stage 1 background and the top · side borders.
- **Margin**: starting from the background, up to $`\mathrm{round}(0.05 \cdot \max(W, H))`$ steps, it widens into $`\mathrm{known}`$ pixels with neighbor change $`\max_c\lvert \Delta U_c\rvert < 0.03 \cdot k`$ (𝑘 as for the flat background above), $`\max_c`$ difference from the starting color $`< 0.1`$, and $`\varepsilon < 0.9`$.
  If $`k < 1`$ and the area after widening is below $`0.05N`$, it is reverted to before widening and widened again with $`k = 1`$.
- It is used only if, after returning swallowed characters (below), the area is 2–90%. If the scene background with 𝜀 fails this criterion, it is searched once more without the 𝜀 condition (removing $`\varepsilon < 0.9`$ from the stage 1 candidates and the margin).
  The color model · face-based widening keep using 𝜀. Pictures that exceeded 90% because a character with an invisible outline was swallowed whole (a black-haired character on a gradient sky) are used after returning, too.

### Cropped character parts

For the connected pieces of the stage 1 background, runs are made by walking the border path once. Pieces under 0.3% are treated as gaps.
The widest piece, pieces over 15%, and pieces touching near the two upper corners (within $`\max(3, \mathrm{round}(0.05W))`$ from the corner along the top border and $`\max(3, \mathrm{round}(0.05H))`$ along the side borders) are excluded.
If, in every run of a piece, there is a crisp line on the way to the first other piece met on each side across gap runs, and the average colors (Lab of 𝑈) of the two pieces differ by $`\Delta E \ge 25`$, the piece is returned to the character.

### Widening with a color model (GrabCut style)

1. **Regions**: the Lab of the original is split by <mark>k-means</mark> (24 colors, 40,000 samples) on $`\mathrm{known}`$ pixels; 4-connected components of the same color with 40px or more become regions 𝑟, and the rest are attached by label filling.
   If there are fewer than $`0.2N`$ $`\mathrm{known}`$ pixels, this stage and face-based widening are not done.
2. **Region features**: area $`A_r`$, mean Lab ($`\mathrm{known}`$ pixels), crisp-line density ratio $`\rho_r = \mathrm{mean}_r(D_c)/\tau_c`$ (here $`\tau_c \ge 10^{-4}`$), existing background share $`\beta_r`$, number $`F_r`$ of top · left · right border pixels that are in 𝑟,
   and the share of crisp lines on the perimeter $`\kappa_r = (\text{number of boundary pixel pairs on crisp lines})/(\text{number of boundary pixel pairs touching other regions})`$.
3. **Contact**: for each horizontally · vertically adjacent pixel pair in different regions, 1 is added to the line contact length 𝑙 if either is $`\mathrm{inMask}`$, otherwise to the lineless contact length 𝑜,
   and if either is a crisp line, 1 is also added to the crisp line length 𝑘.
4. **Color distribution**: Lab is counted in $`13 \times 32 \times 32`$ bins ($`\lfloor L/8\rfloor,\ \lfloor(a + 128)/8\rfloor,\ \lfloor(b + 128)/8\rfloor`$, out-of-range values go to the end bins), smoothed by summing the neighboring $`3 \times 3 \times 3`$ bins, and normalized.

   $`\displaystyle p(i)=\frac{\tilde h(i)}{\sum_j \tilde h(j)},\qquad \tilde h(l,a,b)=\sum_{|\delta_l|,|\delta_a|,|\delta_b|\le1}h(l+\delta_l,\,a+\delta_a,\,b+\delta_b)`$

5. **Initial values**: background $`B^0 = \lbrace\beta_r > 0.5\rbrace \cup \lbrace F_r > 0 \land \rho_r < 1\rbrace`$, character core $`F^0 = \lbrace\rho_r > 3 \land F_r = 0\rbrace \setminus B^0`$.
   $`F^0`$ is used only for the overlap check below; the character distribution of the first cut is learned from all regions outside $`B^0`$.
6. **Safeguards**:
   - Not done if the overlap of the two distributions is $`\sum \min(p_{F^0}, p_{B^0}) \ge 0.3`$.
   - Not done if the existing background covers 90% or more of the top · left · right borders.
7. **Energy**: for labels $`x_r`$ that are 1 for character and 0 for background,

   $`\displaystyle E(x)=\sum_r \theta_r\,[x_r=0]\;+\;\sum_{(r,q)} w_{rq}\,[x_r\ne x_q]`$

   $`\displaystyle \theta_r=\sum_{p\in r,\,known}\mathrm{clip}_{[-3,3]}\ln\frac{p_F(c_p)+10^{-6}}{p_B(c_p)+10^{-6}} +A_r\,\mathrm{clip}_{[0,2]}\ln\frac{\max(\rho_r,\,10^{-3})}2 -A_r\,\beta_r-20F_r +A_r\,\mathrm{clip}_{[0,2]}\frac{\kappa_r-0.3}{0.15}`$

   The first term is color, the second is how far the crisp-line density exceeds $`2\tau_c`$ (half the median density on crisp lines) (maximum 2 at $`\rho_r = 2e^2 \approx 14.8`$),
   the third · fourth terms are the existing background and the border, and the fifth is how much the region is surrounded by crisp lines (0 at $`\kappa_r`$ 30%, 2 at 60%).

   $`\displaystyle w_{rq}=8\,o\,\exp\!\left(-\frac{\Delta E_{rq}^2}{2\cdot 12^2}\right)+0.3\,l`$

   $`\theta_r > 0`$ is the cost on the character side. Regions with $`\beta_r > 0.5`$ are fixed as background ($`\theta = -\infty`$); regions with mean $`L^* < 30`$ and $`C^* < 12`$ (near-black achromatic) and
   regions with region mean $`\bar \varepsilon_r \ge 0.9`$ (enclosed by lines) are fixed as character ($`\theta = +\infty`$).
8. **Minimum cut**: in the graph with capacity $`\theta_r^{+} = \max(\theta_r, 0)`$ from the source (character) to each region, $`\theta_r^{-} = \max(-\theta_r, 0)`$ from each region to the sink (background), and $`w_{rq}`$ in both directions between region pairs, the **<mark>Dinic</mark>** <mark>maximum flow</mark> is found
   (repeat: assign levels by <mark>breadth-first search</mark>, then push flow along augmenting paths whose level increases by one, depth-first, until blocked; residual capacity $`10^{-9}`$ or less counts as 0),
   and the regions reachable from the source in the residual graph become character. The <mark>maximum flow</mark> equals the <mark>minimum cut</mark>, so this is the split that minimizes $`E(x)`$.
9. **Connection condition**: a new background region must be reachable from the reference background ($`B^0`$) crossing only boundaries whose non-crisp contact $`o + l - k`$ is at least $`\max(3, 0.3(o + l))`$. If not reachable, it is returned to the character.
10. The two color distributions are relearned from the split and 7–9 are repeated 4 times. The $`\mathrm{known}`$ pixels and faint line pixels of regions that became background are added to the background (crisp lines are not added).

The random numbers use a fixed seed (777) for this stage alone, so pictures where this stage does not act are not changed by a single bit. The region graph is built once when first needed and shared with the face stage below.

### Attached character parts

1. **Crisp edges**: pixels of the Lab of 𝑈 (the picture with the color under lines restored) with $`\max(\Delta E(p-1, p + 1), \Delta E(p-W, p + W)) \ge 20`$. Blurred, smudged edges have small differences across 2px and are not included.
2. **Pieces**: 4-connected components 𝑘 of stage 1–5 background pixels that are neither crisp edges nor lines. Edge · line pixels are filled with the label of the nearest piece or character, and the contact length is measured by neighbor pairs with different labels.
3. **Color log-likelihood ratio**: Lab is counted in $`10 \times 16 \times 16 = 2560`$ bins ($`\lfloor L/10\rfloor,\ \lfloor(a + 128)/16\rfloor,\ \lfloor(b + 128)/16\rfloor`$, out-of-range values go to the end bins), and the character distribution $`h_C`$ ($`\mathrm{known}`$ not in background, $`n_C`$ pixels) is compared with
   the background distribution $`h_B`$ ($`\mathrm{known}`$, $`n_B`$ pixels) minus the piece's own $`h_k`$ (Laplace smoothing adding 1 to each bin, $`n_B - \lvert k\rvert`$ at least 1).

   $`\displaystyle \bar\ell_k=\frac1{|k|}\sum_{p\in k,\,known}\mathrm{clip}_{[-4,4]}\ln\frac{(h_C(c_p)+1)/(n_C+2560)}{(h_B(c_p)-h_k(c_p)+1)/(n_B-|k|+2560)}`$

4. **Conditions**: area at least 0.1% of the whole, not touching the top · left · right borders, contact length with the character at least 0.8 times the total contact length, $`\bar \ell_k \ge 0.8`$.
   **Border pieces** (0.41): a piece touching the top · left · right borders is chosen if, in the face frame $`(u, v)`$ (3 of face finding) of a face scoring 11 or more, at least half of its area (counted on a 2px grid) lies in the head ellipse $`(u/2.2)^2 + ((v + 0.3)/2)^2 \le 1`$ or
   the body column ($`-1.2 \le v \le 8`$, $`\lvert u\rvert \le 1.2 + 0.35 \cdot \max(v - 1.5, 0)`$), it is not the largest piece,
   its area is between 0.1% and 6% of the whole, its contact length with the character is at least 0.75 times the total, and $`\bar \ell_k \ge 0.75`$.
   Hair tips · sleeves · arms cut off by the frame come back under this condition, while border background far from faces and the largest background piece stay.
5. The chosen pieces, the edge · line band on the piece side, and the edge band on the character side (up to 3px) are removed from the background.
   The color model is computed with the background before returning; returned pixels are also removed from the background added by the color model, and from the background-effect candidates below.
6. In pictures where a swallowed character was returned in the scene background stage (below), splitting into pieces and color comparison use the background before returning.
   If the returned character colors enter the character-side distribution, the likelihood ratio of other pieces (hair of the same color family) changes and the decision wavers.
7. **Dark character parts** (0.43): the same background, minus the pieces returned under 4, is cut this time at faint edges ($`\Delta E \ge 5`$ between pixels 2px apart) and lines into pieces 𝑘 (label filling · contact lengths as in 2).
   The pixels of pieces touching the top · left · right border are counted in $`25 \times 64 \times 64 = 102400`$ Lab bins ($`\lfloor L/4\rfloor,\ \lfloor(a + 128)/4\rfloor,\ \lfloor(b + 128)/4\rfloor`$, out-of-range values go to the end bins) as $`h_T`$ (total $`n_T`$), and for every piece not touching the border

   $`\displaystyle \nu_k=\frac1{|k|}\sum_{p\in k}\mathrm{clip}_{[-4,4]}\Big(\ln\frac{n_T+102400}{102400}-\ln\big(h_T(c_p)+1\big)\Big),\qquad \bar L_k=\frac1{|k|}\sum_{p\in k}L^*_p`$

   is measured. Pieces with $`2\times10^{-5}N \le |k| \le 0.15N`$, $`\bar L_k \le 35`$ and $`\nu_k > 0`$ (colors rarer than average in the border background) are candidates; a candidate whose contact with the character plus contact with already accepted candidates
   is at least 0.1 of its total contact length or at least $`0.25\sqrt{|k|}`$ is accepted, repeated until nothing more is accepted (connected pieces like legs → skirt → body). The band (3px) between accepted pieces and the character is returned too.
   The dark background itself has the colors of the border background and does not come back; parts painted on it with slightly different colors, such as black hair · skirts · legs, do.

### Face finding

It finds faces with hand-set rules and averaged patterns, without a trained model. The picture is scaled by $`k_f = 800 / \max(W, H)`$ ($`w = \max(2, \mathrm{round}(k_f W))`$, ℎ likewise)
(area averaging when shrinking, white backing $`A\cdot O + 1 - A`$ for transparent areas), and measured in Lab. Found positions · sizes are multiplied by $`1/k_f`$ to return to the processing resolution.

1. **Eye candidates**: $`\ell = L^*/100`$ is blurred by 3 box blurs (radius $`\rho \in \lbrace1, 2, 3, 4, 5, 7, 9, 12, 15, 20\rbrace`$, $`\sigma^2 = \rho^2 + \rho`$: the box-blur variance formula of 4.2 solved backwards), and the <mark>Hessian</mark> is computed with second differences,

   $`\displaystyle L_{xx}=\ell_{x-1,y}-2\ell_{x,y}+\ell_{x+1,y},\quad L_{yy}=\ell_{x,y-1}-2\ell_{x,y}+\ell_{x,y+1},\quad L_{xy}=\tfrac14\left(\ell_{x+1,y+1}-\ell_{x-1,y+1}-\ell_{x+1,y-1}+\ell_{x-1,y-1}\right)`$

   $`\displaystyle D_\sigma=\sigma^4\left(L_{xx}L_{yy}-L_{xy}^2\right)\quad(L_{xx}+L_{yy}>0)`$

   A positive <mark>Hessian determinant</mark> means a round blob, and only $`L_{xx} + L_{yy} > 0`$ (center darker than its surroundings) is considered. $`\sigma^4`$ is the scale normalization that makes values comparable across sizes.
   Points that are the largest within the two neighboring scales and 5×5 and have $`D > 0.004`$ become candidates of radius $`r = 1.414\sigma`$, up to 3000 in descending order.
2. **Pairs**: two candidates (left 𝑎, right 𝑏) with distance $`d \ge 16,\ 4 \le d / \bar r \le 24`$ ($`\bar r`$ the mean of the two radii), $`\lvert \Delta y\rvert \le 0.8\Delta x`$, radius ratio $`\le 1.7`$.
   **Tilt hypotheses** (0.37): for a rotated canvas (tilt 𝜃), it searches separately for each hypothesis $`\varphi \in \lbrace\theta, \theta \mp 90^\circ \rbrace`$. The pair filter uses $`\lvert \tan \delta \rvert \le 0.8`$ for the difference 𝛿 (folded into −90°–90°) between the eye-to-eye direction and 𝜑,
   the tilt evidence ("not much tilted" in 5) is $`t = \lvert \tan(\angle e - \varphi)\rvert`$, and the position refinement of 6 and the selection of 7 are also done per hypothesis. A face lying on its side does not tell which way is down, so
   pairs whose eye line is steep are also measured in the frame rotated by 180° (both 𝑒 and 𝑓 sign-flipped). The hypothesis with the larger top score of naming faces (mirror-agreed: $`-\varphi`$ for the flipped picture) is used; on a tie, 𝜃.
   With the "Tilted picture" setting on, pictures that are not rotated canvases are also searched the same way with $`\varphi \in \lbrace0, -30, 30, -60, 60, -90, 90\rbrace^\circ`$ (0° is not favored).
   If neither, there is one $`\varphi = 0`$, the same as 0.36.
3. **Face frame**: with the midpoint of the two eyes as the origin, the eye direction as 𝑢, and the downward direction perpendicular to it as 𝑣, grid samples (<mark>bilinear interpolation</mark>, edge values outside the picture) are taken in units of 𝑑.

   $`\displaystyle \mathbf c=\tfrac12(\mathbf a+\mathbf b),\quad d=|\mathbf b-\mathbf a|,\quad \mathbf e=\frac{\mathbf b-\mathbf a}d,\quad \mathbf f=\pm(-e_y,\,e_x)\ (f_y\ge0),\qquad \mathbf x(u,v)=\mathbf c+d\,(u\,\mathbf e+v\,\mathbf f)`$

   Conversely, the frame coordinates of pixel 𝑥 are $`u = (x - c)\cdot e / d,\ v = (x - c)\cdot f / d`$. The tilt is $`t = \lvert b_y - a_y\rvert/ \max(\lvert b_x - a_x\rvert, 10^{-6})`$.
   A grid is $`n_u \times n_v`$ points evenly dividing the range, including both ends.

   | Cell | Range | Grid |
   |---|---|---|
   | Eye cell (each eye) | $`0.28 \le \lvert u\rvert \le 0.72,\ \lvert v\rvert \le 0.18`$ | 8 × 6 |
   | Lash band (each eye) | $`0.25 \le \lvert u\rvert \le 0.75,\ -0.32 \le v \le -0.14`$ | 8 × 3 |
   | Nose bridge | $`\lvert u\rvert \le 0.12,\ 0.05 \le v \le 0.45`$ | 4 × 6 |
   | Cheek (each cheek) | $`0.3 \le \lvert u\rvert \le 0.7,\ 0.35 \le v \le 0.7`$ | 5 × 5 |
   | Eye sparkle (each eye) | $`\lvert u \mp 0.5\rvert \le 0.2,\ \lvert v\rvert \le 0.2`$ | 17 × 17 |
   | Cheek below mouth · below nose (adjustment of 9) | $`\lvert u\rvert \le 0.9,\ 0.4 \le v \le 0.8`$ · $`\lvert u\rvert \le 0.25,\ 0.8 \le v \le 1.3`$ | 9 × 5 · 7 × 7 |
   | Upper · lower eyelid band (adjustment of 9) | $`\lvert u\rvert \le 0.7,\ -0.3 \le v \le -0.12`$ · $`0.12 \le v \le 0.3`$ | 15 × 4 |

   The skin brightness 𝑆 is the median $`L^*`$ of the 74 nose-bridge · two-cheek samples. The **iris color** of an eye cell is the mean Lab of samples with $`L^*`$ at or below the median, the **lash band value** is the mean of the minimum of every 3 rows,
   and the **eye cell minimum** is the mean of the two eye cells' minimums. The **sparkle** ℎ is, on the 17 × 17 grid (spacing $`0.025d`$), the difference between the brightest point and the median of 8 points around it: the 4 points 3 grid steps away $`(\pm 3, 0),\ (0, \pm 3)`$ and the 4 points 2 diagonal steps away $`(\pm 2, \pm 2)`$
   (edge values outside the grid).
4. **Average patterns**: the eye pattern (12×12, $`0.2 \le \lvert u\rvert \le 0.8,\ \lvert v\rvert \le 0.3`$, right eye mirrored) and the face pattern (16×16, $`\lvert u\rvert \le 1.1,\ -0.9 \le v \le 1.3`$) are
   the brightness measured on 31 faces of the 24 test pictures aligned by eye positions marked by a person, each set to mean 0 · standard deviation 1, then averaged (400 numbers inside the program).
   Candidates also set the same grid to mean 0 · standard deviation 1 and measure the correlation $`c = \mathrm{mean}(z \cdot T)`$. For eyes, the smaller of the two eyes.
5. **Score**: the weighted sum of each cue's value clipped to $`[0, 1]`$ (maximum 15).

   | Cue | Value (clipped to 0–1) | Weight |
   |---|---|---|
   | Eyes darker than skin | $`(S - \text{eye cell mean }L^* - 8)/16`$ | 1 |
   | Skin is bright | $`(S - 60) / 25`$ | 1 |
   | Nose bridge is even | $`(16 - \text{nose bridge }L^*\text{ standard deviation})/12`$ | 1 |
   | Nose bridge · both cheeks have the same color | $`(32 - \text{maximum }\Delta E\text{ of the three mean colors})/22`$ | 1 |
   | Both irises have the same color | $`(28 - \Delta E\text{ of the mean colors of the darker halves of the two eye cells})/20`$ | 1 |
   | Lashes are dark | $`(S - \text{mean of row minimums of the lash band} - 20)/30`$ | 1 |
   | Pupils are dark | $`(25 - \text{eye cell minimum})/18`$ | 1 |
   | Cheeks are even | $`(22 - \text{cheek }L^*\text{ standard deviation})/14`$ | 1 |
   | Not much tilted | $`(0.7 - t) / 0.5`$, $`t = \lvert b_y - a_y \rvert/ \lvert b_x - a_x \rvert`$ (vertical difference of the two eyes divided by horizontal difference) | 1 |
   | Face pattern | $`(c_{face} - 0.2) / 0.3`$ | 3 |
   | Eye pattern | $`(c_{eye} - 0.1) / 0.4`$ | 1 |
   | Sparkle in the eyes | $`(h - 2) / 8`$, ℎ = the brightest point in the eye cell ($`0.4d \times 0.4d`$, 17×17 grid) minus the median of the 8 surrounding points about $`0.07d`$ away (the smaller of the two eyes) | 2 |

6. **Position refinement**: for the top 40 pairs by score, each eye in turn is moved within $`\pm 0.12d`$ (5×5 grid, spacing $`0.06d`$, 𝑑 the distance before refinement) to where the face pattern correlation is largest,
   repeated twice in the order left eye → right eye (moving only when the correlation becomes larger than now), and measured again.
7. **Selection**: scores of 11 or more are chosen in descending order, but a pair is dropped if its center is less than $`\max(d, d')`$ from an already chosen face, or one of its eyes is within $`0.5 \max(d, d')`$ of that face's eyes.
8. **A face-like place?**: a real face has the head almost entirely inside the picture, and the face itself is not on already found background. Only faces with 80% or more of the head ellipse (below) inside the picture,
   and with 30% or less already found background in it, or 5% or less background in the face ellipse (eyes · cheeks, $`u^2 + ((v - 0.2)/0.8)^2 \le 1`$), are kept.
   Picture pixels within $`2.4d`$ of the center are looked at every 4px horizontally · vertically (coordinates that are multiples of 4), and with one sample counted as $`16\,\mathrm{px}^2`$, "80% or more inside the picture" is
   a sample count inside the head ellipse of $`n \ge 0.8 \cdot \pi \cdot 2.2 \cdot 2 \cdot d^2 / 16`$.
   The top-scoring face is dropped only when more than half of its face ellipse is background.
   This reduces fake faces that grab a knee · cushion at large size and block wide background as "head · body zones", while keeping the faces of characters with small heads whose head ellipse is surrounded by background.
   All 30 real faces in the test pictures had 0% background in the face ellipse and at most 28% in the head ellipse.

The thresholds were set on the side of missing few faces. Fake faces (knees, hands, bowls, clothing patterns) only protect that place for the character in the stages below and do not add background,
but the character of a missed face is not protected.

9. **Faces for names · character folders**: for each pair measured up to 6, the adjustments below are added to the score and 7 · 8 are done once more (threshold 10.75). Background decisions (the stages below) use the faces of 7; part names and character splitting use these faces.

   | Adjustment | Value |
   |---|---|
   | Mouth visible | $`\mathrm{clamp}((m - 15)/20) - 1`$, 𝑚 = the median $`L^*`$ of the cheek · below-nose-bridge cell ($`\lvert u\rvert \le 0.9,\ 0.4 \le v \le 0.8`$) minus the minimum of the below-nose cell ($`\lvert u\rvert \le 0.25,\ 0.8 \le v \le 1.3`$) |
   | Eye contrast too strong | $`-\mathrm{clamp}((S - \text{eye cell mean }L^* - 40)/15)`$ |
   | Lower eyelid too bright | $`-\mathrm{clamp}((\text{lower band mean }L^* - \text{upper band mean }L^* - 35)/20)`$, upper band $`\lvert u\rvert \le 0.7,\ -0.3 \le v \le -0.12`$, lower band $`\lvert u\rvert \le 0.7,\ 0.12 \le v \le 0.3`$ |
   | Skin is white paper | $`-\mathrm{clamp}((S - 97)/3)`$ |

   When a person marked face candidates in 300 unseen pixiv pictures as real · fake (11), real faces had visible mouths (median 𝑚 of candidates scoring 9 or more: 57 vs 38 for fakes),
   and fakes (clothing patterns, text, props, snacks) often had too large eye contrast and lower-eyelid brightness or a white backing in the skin area.
   Among pairs scoring 10 or more, the mean adjustment is −0.13 for real faces (median 0) and −0.41 for fakes (a quarter at −0.85 or less).
   Two kinds of faces are used because changing the faces for background decisions with this adjustment too made the background flip between better and worse (7.5).
10. **Mirror agreement** (0.34): the picture is flipped left-right and 1–9 are done once more; among the faces of 9, only those that also have a face at the same place in 9 of the flipped picture
   (the flipped center mapped back by $`x \mapsto W - 1 - x`$, with the two centers less than $`\max(d, d')`$ apart) are used for names · character folders (position · score from the original picture).
   A real face is still a face when flipped, but fakes arising by chance from clothing folds · patterns · text often cross the threshold on only one side because of the asymmetry of the average patterns · lash band · eye refinement order.
   Marking the naming faces that appeared on only one side in pixiv pictures, 101 of 108 were fake (11). The faces of 7 (for background decisions) are kept as they are
   (using it for background decisions too increased the pictures losing character parts that fake faces had protected, 7.5). Face finding runs twice, so it takes that much longer (median processing time on 666 pictures 9.4 s → 10.8 s).

Face finding is done once regardless of the background. For pictures where the background was not searched or not found, transparent areas (alpha 0.02 or less) are treated as background and 8 is applied, for part names and character splitting.

### Returning swallowed characters

In pictures whose outline has the same color as the hair · background and cannot be seen, and whose hair · clothes are painted without lines, the scene background found by line density crosses the character boundary as it is.

1. **Swallowed faces**: among faces scoring 13 or more (all found faces regardless of the conditions of 8), those with more than 25% background in the face ellipse ($`u^2 + ((v - 0.2)/0.8)^2 \le 1`$) or the crown cell ($`\lvert u\rvert \le 0.8,\ -1.6 \le v \le -0.45`$)
   (measured with all pixels within $`1.7d`$ horizontally · vertically of the center).
   Real faces in the test pictures were at most 2% for both, and fake faces whose face · crown sat on background (background decorations) all scored 12.6 or less.
2. **Pieces**: the current background is split into pieces 𝑘 the same way as for attached character parts (crisp edge $`\Delta E \ge 20`$, lines).
3. **Rare color**: from the color distribution $`h_B`$ (Lab $`10 \times 16 \times 16 = 2560`$ bins) counted over the $`n_B`$ pixels of pieces touching the top · left · right borders, for each piece 𝑘 not touching the border,

   $`\displaystyle \nu_k=\sum_{p\in k}\mathrm{clip}_{[-4,4]}\ln\frac{1/2560}{(h_B(c_p)+1)/(n_B+2560)}`$

   The numerator is the uniform distribution and the denominator the border-side background distribution (Laplace smoothing), so it grows positive the rarer the color is in the border-side background compared with the uniform distribution.
4. **Returning**: pieces with at least half of their area inside the head ellipse or body column (the same shape as the zone probability of face-based widening) of one of the swallowed faces,
   not touching the top · left · right borders, and with $`\nu_k > 0`$, plus the edge · line band on the piece side and the edge band on the character side (up to 3px), are returned to the character.
   Background gaps seen between hair and neck have the background color and remain.
5. If swallowed faces still remain after returning (black hair of almost the same color as the background: no crisp edge), the crisp edge is lowered to $`\Delta E \ge 8`$ and 1–4 are done once more.
   If some still remain, it is lowered to $`\Delta E \ge 5`$ and the color bins of 3 are made finer, $`25 \times 64 \times 64 = 102400`$ bins with spacing 4 for all of $`L^*`$ · $`a^*`$ · $`b^*`$ (numerator · smoothing also with this bin count), and done once more (0.34).
   Black hair with $`\Delta E`$ 6–9 from the background is in the same bin as the background with 2560 bins and is not rare, but falls in a different bin with the fine bins.
6. **Body-zone pieces** (before 1–5): if there is a face scoring 13 or more that was not swallowed, among the same pieces ($`\Delta E \ge 20`$), pieces with at least half of their area in the lower part of that face's body column
   ($`1 \le v \le 8`$, $`\lvert u\rvert \le 1.2 + 0.35 \cdot \max(v - 1.5, 0)`$), not touching the top · left · right borders, and with area at least 0.3% of the whole are considered.
   White clothes on a white background have the same color as the background, so the rarity condition of 3 is not used; only pieces whose color log-likelihood ratio between the character (pixels not currently background) distribution and the remaining background pieces' distribution
   (the same formula as $`\bar \ell_k`$ of attached character parts) is $`\bar \ell_k \ge -2`$ are returned.
   Background holes seen between skirt and sleeve ($`\bar \ell \approx -3.9`$) and text boxes next to the character (−2.1) remain, while white clothes · skirt pieces were −1.6 or more.
7. It is done just before the area check of the scene background stage, and after the color model · returning attached parts. Returned parts are treated like attached character parts
   (the color model · face-based widening do not take them back, and they are removed from the background-effect candidates).

### Face-based widening

0. **Skip when the background is almost one color**: from the $`n_b`$ background pixels found so far (flatness 0 if fewer than 100), one in every $`t = \max(1, \lfloor n_b / 20000\rfloor)`$ is taken in pixel order and
   the per-channel medians $`(m_L, m_a, m_b)`$ of the original Lab $`(L_i, a_i, b_i)`$ are found (the $`\lfloor n/2\rfloor`$-th of 𝑛 sorted values, from 0).

   $`\displaystyle \mathrm{flat}=\frac1n\left|\left\lbrace\,i:(L_i-m_L)^2+(a_i-m_a)^2+(b_i-m_b)^2<10^2\,\right\rbrace\right|`$

   If $`\mathrm{flat} \ge 0.6`$ (white background · one-color background), this stage is not done. Measured on the background before the face stage over 666 pictures, 171 of 211 white · one-color backgrounds (81%) are 0.6 or more,
   while only 13 of 173 scene backgrounds drawn with lines or paint (8%) are 0.6 or more (11).
   With a floor band (flat · gradient background 3 above, 0.40), the samples are split into inside and outside the band, each counted against its own medians, and the two are added. A two-color wall/floor background then counts as one color,
   so face-based widening does not switch on and take the character. The flatness used in closing narrow gaps (flat · gradient background 5) is the same.
1. It uses the same region graph as the color model (24-color regions, contact lengths $`o, l`$, color distributions). The two stages share the graph built once.
2. **Zone probability** (probability of being character) $`\pi(p)`$: for each face, at $`(u, v)`$ of the original resolution,

   $`\displaystyle \pi_f=\begin{cases}0.9 & -1.2\le v\le 8,\ |u|\le 1.2+0.35\max(v-1.5,\,0)\quad(\text{body})\\ 0.85 & (u/2.2)^2+((v+0.3)/2)^2\le 1\quad(\text{head})\\ 0.45 & \text{otherwise}\end{cases},\qquad \pi(p)=\max_f \pi_f(p)`$

   The region mean is $`\bar \pi_r`$. The log odds of the zone term are $`\ln(0.9/0.1) = 2.197,\ \ln(0.85/0.15) = 1.735,\ \ln(0.45/0.55) = -0.201`$.
3. **First split**: character is the regions with $`\bar \pi_r \ge 0.8 \land \beta_r < 0.5`$ (head · body zones), background the regions with $`\beta_r > 0.5`$ (existing background). After that, it learns from the previous cut (character / everything else).
4. The **energy** and <mark>minimum cut</mark> (the same <mark>Dinic</mark> as the color model) are repeated 4 times, relearning the color distributions.

   $`\displaystyle \theta_r=\sum_{p\in r,\,known}\mathrm{clip}_{[-3,3]}\ln\frac{p_F(c_p)+10^{-6}}{p_B(c_p)+10^{-6}}+\sum_{p\in r}\ln\frac{\pi(p)}{1-\pi(p)}-2A_r\beta_r,\qquad w_{rq}=o\,\exp\!\left(-\frac{\Delta E_{rq}^2}{288}\right)+0.0375\,l`$

5. **Only sure places**: among regions that ended on the background side, those whose mean color term (per $`\mathrm{known}`$ pixel) is below −1, whose mean color term measured with the initial color distributions is also below −0.5 (0.42, below),
   and with $`\bar \pi_r \le 0.5`$ are candidates (excluding regions where returned character parts exceed half the area, and regions with $`\bar \varepsilon_r \ge 0.9`$).
   Starting from the existing background ($`\beta_r > 0.5`$), the pixels of regions connected into the candidates crossing only boundaries with $`o \ge 0.5(o + l)`$ are added to the background
   (excluding crisp line pixels and character parts returned earlier).
   The color term with the initial color distributions uses the distributions $`p^0_F, p^0_B`$ counted from the first split in 3 (the same color bins):
   $`\theta^0_r=\sum_{p\in r,\,known}\mathrm{clip}_{[-3,3]}\ln\frac{p^0_F(c_p)+10^{-4}}{p^0_B(c_p)+10^{-4}}`$, and the condition is $`\theta^0_r / k_r < -0.5`$ ($`k_r`$ is the number of $`\mathrm{known}`$ pixels in the region).
   The repetition in 4 keeps using $`10^{-6}`$. The distributions relearned over the repetitions pushed rarely seen colors to one side, so dark legs · clothes near the head · body zones that were on the character side at first often became candidates.

### Background seen between character parts (gaps)

Done after face-based widening. Only when the painted ($`\mathrm{known}`$) pixels of the background found so far are $`0.02N`$ or more,
and line pixels ($`\mathrm{lineMask}`$) are fewer than $`0.3 n_o`$ of the $`n_o`$ opaque ($`A > 0.02`$) non-background pixels (pictures where grain · halftone · dense hatching is picked up as lines are excluded because the bleeding of 4.6 below is large).

1. **Background representative color**: from the $`n_b`$ painted background pixels, one in every $`t = \max(1, \lfloor n_b / 20000\rfloor)`$ is taken in pixel order, the per-channel medians $`(m_L, m_a, m_b)`$ of the Lab of the color under lines (𝑈) are found,
   and the flatness $`\mathrm{flat}`$ (the share within $`\Delta E`$ 10 of the median) is measured with the same formula as 0 of face-based widening. If $`\mathrm{flat} < 0.6`$, it is not done (scene backgrounds have varied colors where they show through gaps too, so this rule cannot separate them).
2. **Candidates**: painted non-background pixels with almost the same color as the background representative color (excluding returned character parts) are split into 4-connected pieces 𝑟.

   $`\displaystyle (L_p-m_L)^2+(a_p-m_a)^2+(b_p-m_b)^2\le 5^2`$

3. **Piece conditions**: with the 8-neighbors outside the piece that are not candidates as the perimeter $`R_r`$, and the painted non-background pixels among them as $`R^c_r`$,

   $`\displaystyle 30\le A_r\le 0.02N,\qquad |R^c_r|\le 0.1\,|R_r|,\qquad \forall p\in r,\ \forall f:\ (u/2.2)^2+((v+0.3)/2)^2>1`$

   The perimeter must be almost only lines and background (white clothes · white hair touching other paint usually touch shadows · shading), and the piece must be outside the head ellipses of faces (faces used for background decisions) (whites of the eyes · teeth).
4. **Picture condition**: all pieces meeting the conditions are added to the background only when their total area is 5% or less of the number $`n_c`$ of painted character-side pixels.

   $`\displaystyle \sum_{r\ \text{meeting the conditions}} A_r\le 0.05\,n_c`$

   Pictures where the character itself has the background color, like white clothes on a white background or black-and-white line art filled with white, have a large sum and are filtered out. The two thresholds (0.05 · 0.02) and flatness 0.6 were set by looking one by one at the 161 pictures changed by a version that gathered pieces loosely (no sum limit, pieces 5%)
   (11). The pixels sent are remembered separately as a gap map and used for region · tone filling (4.6).

### Rectangular background objects drawn with lines (0.43)

Done after the gaps. For every 4-connected component 𝑟 of painted pixels left on the character side (not background, lines or returned character parts), its area $`A_r`$ and bounding box $`w_r \times h_r`$ are measured.

1. **Rectangle**: it does not touch the border, $`w_r, h_r \ge \max(4, \mathrm{round}(0.015\max(W, H)))`$, $`0.97\,w_r h_r \le A_r \le 0.1N`$, all four corner pixels of the box belong to 𝑟,
   and the box center lies outside the head ellipse $`(u/2.2)^2 + ((v + 0.3)/2)^2 \le 1`$ and the body column ($`-1.2 \le v \le 8`$, $`\lvert u\rvert \le 1.2 + 0.35 \max(v - 1.5, 0)`$) of every face used for background decisions.
2. **Surroundings**: if at least half of the painted pixels in the ring around the box widened by $`d = 2\,\mathrm{lw} + 6`$px (lw is the line width), not counting other rectangle candidates, are background, it is accepted (several panes split by window frames leave each other out of their rings).
   Once something is accepted, the check is repeated until nothing more is accepted.
3. **Hidden panes**: accepted rectangles of one color (90% or more of their pixels within $`\Delta E \le 4`$ of the mean color) are grouped into a window when their mean colors differ by $`\Delta E < 4`$ and their boxes are within 𝑑 of each other.
   Inside the group's bounding box widened by the panes' mean width · height plus 𝑑, painted pixels within $`\Delta E \le 4`$ of the group's mean color (outside face zones and returned character parts) are also sent to the background (panes hidden by the character, no longer rectangles).

Window panes · shelves · books of line-drawn rooms (synthetic pictures) are caught here. Being enclosed by lines, the scene background · color model · face-based widening do not take them, and with an almost one-color background face-based widening is not done either.
Only 1 of the 777 real pictures changed (0.43 in 12).

### Outer glow

A saturated, bright band around the character (neon glow, fluorescent outline) is taken out separately.

It is looked at only in pictures whose background is 2–95% of the whole.

1. **Band candidates**: painted ($`\mathrm{known}`$, non-line) pixels touching the background with 4-neighbors are at depth 1, and pixels reached toward the character within $`D = \max(12, \mathrm{round}(0.025\cdot \max(W, H)))`$ steps without crossing lines (4-neighbor <mark>breadth-first search</mark>; the depth is the number of steps).
2. **Decision**: a pixel is fluorescent if $`L^* > 60`$ and $`C^* > 45`$ (in 𝑈, with the color under lines restored). With $`f_r`$ fluorescent among $`n_r`$ band candidates and $`f_i`$ fluorescent among $`n_i`$ pixels inside the character (<mark>chamfer distance</mark> to background $`> 2D`$),
   it needs $`f_r \ge 0.18 n_r,\ f_r / n_r \ge 4 f_i / n_i,\ f_r \ge 0.002N`$.
3. **Glow colors**: fluorescent pixels of the band candidates are counted in 16×16 $`(a^*, b^*)`$ bins ($`\lfloor(a^* + 128)/16\rfloor,\ \lfloor(b^* + 128)/16\rfloor`$); bins with $`0.005 f_r`$ or more.
4. **Glow**: widened with 4-neighbors from the fluorescent pixels of the band candidates.
   - Character side: among pixels with depth to background + <mark>chamfer distance</mark> to the nearest line $`\le D`$ (a band squeezed between background and outline), glow colors ($`L^* > 45,\ C^* > 25`$, glow bin) or white cores ($`L^* > 80`$)
   - Background side: glow colors with <mark>chamfer distance</mark> to the character $`\le D`$
5. **Surrounding**: used only if 35% or more of the background pixels touching the character (<mark>chamfer distance</mark> to the character $`\le 1.5`$) are within 3px of the glow (square dilation of radius 3).
6. Glow pixels are moved to the background side and put in the "Outer glow" layer (normal, opaque) with their original colors. The background layer color below them is inpainted from the rest of the background.
   Places the user returned to the character and character parts returned from the background are excluded.

### Background effects

Non-background ($`A > 0.02`$) 4-connected pieces with area below $`0.015N`$ are background-effect candidates (excluding pieces containing returned character parts · places the user returned to the character).
The background color below them $`U^{bg}`$ is inpainted from the rest of the background (skipping other character pixels); the background layer gets $`\mathrm{base}_c = \min(U_c, U^{bg}_c)`$ ($`U^{bg}_c`$ at outer glow places),
and the background-effect layer gets (excluding outer glow places), when $`U_c > \mathrm{base}_c + 1.2/255`$ and $`\mathrm{base}_c < 0.9999`$, the screen value $`S_c = \mathrm{clamp}(1 - (1 - U_c)/(1 - \mathrm{base}_c))`$ (saved with the minimum alpha of 4.12).

### Removing lines in the background

For each line-connected piece:

- Removed if 50% or more of the piece is inside the background.
- When 85% or more of its non-line 4-neighbors (outside $`\mathrm{inMask}`$) are background: removed if it is more than $`\max(10, \mathrm{round}(20s))`$ steps away from the character (non-background $`\mathrm{known}`$), if it is a small piece under 0.5% of all line pixels,
  or if the $`\Delta E`$ between the line's original mean color and the mean color of the neighboring background (𝑈 of touching background pixels) is $`< 15`$.
- Faint (non-crisp) line pixels absorbed into the background are removed per pixel.

Removed line pixels are restored to their original colors and left in the background picture.

---

[← README](../README.en.md#4-algorithms-and-formulas) · Next: [4.6 Regions and materials](4-3-regions-layers.en.md)
