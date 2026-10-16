# Illustracy — 4. Algorithms and formulas (2/4): Background

[← README](../README.en.md#4-algorithms-and-formulas) · Section 4 [1](4-1-basics.en.md) · **2** · [3](4-3-regions-layers.en.md) · [4](4-4-rough-psd-tools.en.md) · [한국어](4-2-background.md)

---

## 4.5 Background

### Cutout model (0.51 – 0.54, default)

When the "Cutout model" setting is on and the picture has no transparent pixels, this decides the character instead of the background steps below. The picture $`I`$ (processing resolution $`W \times H`$) is shrunk to a long side of 1024 px and placed in the middle of a 1024×1024 frame (the rest 0), and the sigmoid output of the network $`f_\theta`$ is brought back to the original size the same way. Shrinking and enlarging use pixel-center-aligned <mark>bilinear</mark> interpolation (edge pixels repeated).

```math
x = \mathrm{pad}_{1024}\!\left(\mathrm{resize}\!\left(\tfrac{I}{255},\ \tfrac{1024}{\max(W,H)}\right)\right),\qquad m = \mathrm{resize}^{-1}\!\left(\sigma(f_\theta(x))\right),\qquad p \text{ is character} \iff m(p) \ge 0.5
```

$`f_\theta`$ is the <mark>ISNet</mark> model published by SkyTNT's anime-segmentation (skytnt/anime-seg, Apache-2.0, 114 convolutions · 44,004,873 weights) [R90 Qin et al. 2022](../README.en.md#r90) · [R91 SkyTNT anime-segmentation](../README.en.md#r91). To fit it in the app file, the convolution weights were reduced to symmetric 8 bits per output channel $`c`$ [R92 Krishnamoorthi 2018](../README.en.md#r92).

```math
s_c = \frac{\max_k \lvert W_{c,k}\rvert}{127},\qquad q_{c,k} = \mathrm{round}\!\left(\frac{W_{c,k}}{s_c}\right) \in [-127, 127],\qquad \hat W_{c,k} = s_c\, q_{c,k}
```

On first use the app rebuilds $`\hat W`$ from $`q`$ and $`s`$ and runs it with the WASM runtime (one thread) of ONNX Runtime Web (1.29.0, MIT, [R93 ONNX Runtime Web](../README.en.md#r93)) in a separate worker. Outer glow · background effects · correction painting are applied on top of this result as before.

**Notes** — **Why**: background detection that fills inward from the border cannot stop at boundaries without a line, so an arm rendered with a rim light becomes one piece with the background. Rules that sort such pieces by color · area · boundary cues did not exceed AUC 0.69 on 207 development pictures (0.51 preparation in README 7.5). The cutout model looks at the shape of the body and picks out the whole character at once. **Principle**: ISNet is a segmentation network that shrinks and enlarges the image over several resolutions to fit the foreground · background boundary finely. The 8-bit reduction is symmetric quantization that maps each channel's largest absolute value to 127, so the weight error is at most 0.4% of the channel maximum; on the 185 ground-truth pictures the 32-bit and 8-bit models differ on 0.035% of pixels. **References**: [R90 Qin et al. 2022](../README.en.md#r90) · [R91 SkyTNT anime-segmentation](../README.en.md#r91) · [R92 Krishnamoorthi 2018](../README.en.md#r92) · [R93 ONNX Runtime Web](../README.en.md#r93).

**Adding the previous method (0.52)**: with the cutout model, the background steps below (flat · scene · color model · face-based · gaps · neural-network assist) still run and give a decision $`c(p)`$ (character 1 · background 0), which is added to the model probability.

```math
p \text{ is character} \iff m(p) + \alpha\,\bigl(c(p) - \tfrac12\bigr) \ge \tfrac12,\qquad \alpha = 0.4
```

Where the two agree, that is the answer; where they disagree, $`m(p) \ge 0.3`$ (previous method says character) or $`m(p) \ge 0.7`$ (previous method says background) decides. This result is the background layer as it is; outer glow and the small-pieces-on-background rule are not applied. α was chosen on 498 synthetic pictures (0.2 · 0.4 · 0.6 on set A, 299 pictures, confirmed on set B, 199) and the 14 artist-made cutouts (README 7.5 · 12, 0.52).

**Notes** — **Why**: the model alone (0.51) misses some of the background the previous method found on real pictures (background found 94.7% on the 14 artist-made cutouts), while the previous method alone hands a lineless arm to the background. Letting the model's confidence decide only where the two disagree lets each cover the other's mistakes. **Principle**: a linear combination of two classifiers' scores; α is the weight that gives one vote of the previous method the value of 0.2 of model probability.

**Pictures the model missed use the previous method (0.53)**: when the area the model calls character is under 1% of the picture while the previous method calls 5% or more character, the model is taken to have missed the character entirely, and that picture uses the previous method's decision as it is ($`N`$ is the number of pixels in the picture).

```math
\frac1N\,\bigl|\{p : m(p) \ge \tfrac12\}\bigr| < 0.01 \ \text{and}\ \frac1N\,\bigl|\{p : c(p) = 1\}\bigr| \ge 0.05 \quad\Rightarrow\quad p \text{ is character} \iff c(p) = 1
```

It is not a weight that changes gradually but a rule switched per picture, so pictures that do not meet the condition equal 0.52.

**Notes** — **Why**: the model can miss a character that is not human-shaped (animal · monster fan art) entirely, and then even in the addition one vote of the previous method (0.2) cannot overcome a model probability near 0, so the character disappears. Only on such pictures is the previous method followed as it is. **Principle**: the areas of the two decisions are compared, and the picture is handed to the other side only when one is almost empty. The rule was made after seeing results (the Bulbasaur fan art among the 14 artist-made cutouts), and 1% · 5% are the first values set. Raising the previous method's weight on a log scale with how far the model falls short was also measured, but worsened more synthetic pictures than it improved and was not adopted (README 7.5 · 12, 0.53).

**Averaging with a fine-tuned copy (0.54)**: the model probability is the weighted average (0.6 · 0.4) of the original cutout model's probability $`p_0`$ and the probability $`p_1`$ of a copy of the same network trained for 12 more epochs on 290 synthetic composites (pixel ground truth) and 292 pixiv development pictures (the mean of the original model's black-filled · mirror-filled probabilities as soft targets); the addition threshold rises to 0.55 and the 0.53 rule is unchanged.

```math
m(p) = 0.6\,p_0(p) + 0.4\,p_1(p),\qquad p \text{ is character} \iff m(p) + 0.4\,\bigl(c(p) - \tfrac12\bigr) \ge 0.55
```

In the app the fine-tuned copy's 8-bit values are stored as the difference from the original 8-bit values (modulo 256, same scales), and the two models are run one after the other.

**Notes** — **Why**: the two remaining causes of loss in 0.53 (a boundary colored like the background · a body cut off at the edge) are places where the model is confidently wrong with a low probability, which thresholds · filling · cohesion could not fix (README 7.5). So the model itself was trained further. **Principle**: the fine-tuned copy alone keeps more character (character kept 97.6 → 99.4% on the 14 artist-made cutouts) but takes aura · flame effects and background attached to the character as character, raising the mean BER (background found 92.5 → 89.3%); the original model is confident that such places are background, so averaging the two softens each one's confident errors. These mixing weights and threshold were chosen after seeing the fine-tuned copy's results, from 34 rule candidates and 1,089 weight · threshold combinations written down first and scored on the 14 artist-made cutouts · synthetic set B (post-hoc selection), so the value on the 14 pairs is not out of sample (README 12, 0.54).

### Find at reduced size (setting, off by default)

With "Find only background · faces at reduced size" and $`\max(W, H) > S`$ (the target size), the background stages below and face finding alone run on a picture with each channel area-averaged down by $`k = S / \max(W, H)`$
(the line width is the user's chosen value times 𝑘, or measured again on the reduced picture if automatic). The background · returned-part maps are enlarged back to the original size <mark>bilinearly</mark> and turned on where $`\ge 0.5`$,
but on the original-size lines (+ 1px edge) only where the enlarged value is 1. Faces have their position · size multiplied by $`1/k`$.
"Reduce everything" is the same as lowering the processing resolution to $`\min(\text{processing resolution}, S)`$.

**Note** — **Why**: The background and face stages take time in proportion to the pixel count, so for a large picture the decisions are made on a reduced copy and the results carried back to full size. On full-size lines a pixel is switched on only where the enlarged value is 1, so boundaries blended by the reduction do not drag the character's lines into the background. **How it works**: Area-average reduction weights each original pixel by the area it covers in the new cell, which keeps aliasing low. Enlarging a 0/1 map bilinearly gives values between 0 and 1 at boundaries, and the $`\ge 0.5`$ threshold picks the nearer side. Face positions and sizes are lengths, so they are scaled back by $`1/k`$. **References**: [R14 Gonzalez · Woods 2018](../README.en.md#r14)

### Frame

Let $`\kappa(d)`$ be the share of $`\mathrm{known}`$ pixels on the ring around the border (the ring at depth 𝑑 = the perimeter of the rectangle 𝑑px in from the edge).
If $`\kappa(0) < 0.05`$ and the long and short sides are larger than 16px, the first 𝑑 in $`d = 1 \dots \max(3, \mathrm{round}(0.01 \cdot \max(W, H)))`$ with $`\kappa(d) \ge 0.5`$ is the frame thickness 𝑓.
If $`f > 0`$, only during the background stages (everything below, and face finding), each pixel within 𝑓px of the edge has its 𝑈, original, $`\mathrm{known}`$, line, crisp line, and $`\mathrm{inMask}`$ replaced by the values of the nearest
inner pixel ($`(\mathrm{clamp}(x, f, W - 1 - f), \mathrm{clamp}(y, f, H - 1 - f))`$), restored at the end. Not done for transparent pictures.
3 of the 666 pictures had $`\kappa(0) < 0.05`$, and a frame was found in 2 of them ($`f = 2\,\mathrm{px}`$).

**Note** — **Why**: A frame line (black or white border) around the picture blocks the background fill that starts from the border. Measuring the frame thickness and covering it with the nearest inner pixels lets background finding start right at the border. **How it works**: The share $`\kappa(d)`$ of painted pixels on the ring at depth 𝑑 is near 0 inside the frame and rises once past it, so the first depth where it passes one half is the thickness. Clamping coordinates to $`[f, W - 1 - f]`$ sends each frame pixel to the nearest inner pixel (edge replication). The search depth is capped at 1% of the long side so picture content is not taken for a frame. **References**: [R14 Gonzalez · Woods 2018](../README.en.md#r14) · a rule set by this program

### Rotated canvas (0.37)

1. If at least three of the four corner pixels are the same fill, it is treated as a fill: at least three transparent ($`A \le 0.02`$), or at least three opaque ($`A \ge 0.98`$) with mutual $`\max_c`$ difference $`\le 4/255`$.
   $`F_0`$ is taken by following pixels equal to the fill from the corners with 4-neighbors.
   - **Note** — **Why**: A picture saved after rotation gets transparent or single-color triangles in its four corners. Taken as content, they make background finding start in the wrong place. **How it works**: The corners count as fill when at least three of the four agree (one corner may be touched by the character). For opaque corners, a largest channel difference within $`4/255`$ (4 steps in 8 bits) counts as the same color, which tolerates JPEG noise. A 4-neighbor flood fill from the corners collects the connected fill as $`F_0`$. **References**: [R14 Gonzalez · Woods 2018](../README.en.md#r14) · [R15 Soille 2003](../README.en.md#r15)
2. For each row 𝑦, the first · last 𝑥 not in $`F_0`$ ($`x_l(y),\ x_r(y)`$), and for each column 𝑥, the first · last 𝑦 ($`y_t(x),\ y_b(x)`$) are collected.
   For a rotated rectangle, $`x_l`$ is two straight lines bending at its minimum, and $`x_r`$ two straight lines bending at its maximum (likewise $`y_t,\ y_b`$).
   For each bend candidate (the minimum · maximum and 15 evenly spaced positions), both sides are fitted with least-squares lines, points deviating more than $`\tau = 1.5 + 0.002 \cdot \max(W, H)`$px from the line are removed, and it is refitted twice.
   The candidate with the most fitting points (within 𝜏) is chosen, and if fewer than 85% of points fit, it is not a rotated canvas (white paint touching the picture edge connects to the fill and becomes deviating points).
   - **Note** — **Why**: The rotated rectangle's boundary must be fitted with one straight line per side to draw the content area exactly. Outliers such as a character or white paint touching the boundary would sway the fit, so they must be filtered out. **How it works**: In a rotated rectangle, the left end $`x_l(y)`$ of each row is a V (two lines) bending at its minimum. For each candidate bend, both sides are fitted by <mark>least squares</mark> lines $`x = my + c`$ (minimum sum of squared residuals, the closed-form normal-equation solution); points farther than 𝜏 are dropped and the fit repeated, which reduces the pull of outliers. Choosing the candidate with the most inliers selects the model by its support, as RANSAC does. 𝜏 is 1.5px plus 0.2% of the long side, tolerating staircase and anti-aliasing on large pictures. **References**: [R43 Björck 1996](../README.en.md#r43) · [R44 Fischler · Bolles 1981](../README.en.md#r44)
3. Content = pixels with $`\max(l_1(y), l_2(y)) - 0.5 \le x \le \min(r_1(y), r_2(y)) + 0.5`$ and $`\max(t_1(x), t_2(x)) - 0.5 \le y \le \min(b_1(x), b_2(x)) + 0.5`$; the fill region 𝐹 = the rest.
   It is used only if 𝐹 is 1–70% of the picture and at least 97% of 𝐹 is actually the fill color.
   - **Note** — **Why**: Only the inside of the four lines is picture content; the rest is fill created by the rotation. If the fill is too small or too large, or not actually the fill color, the rotated canvas was misread and is not used. **How it works**: The inside of a convex quadrilateral is the intersection of four half-planes, so on row 𝑦 the content runs from the larger of the two left lines to the smaller of the two right lines (likewise for column 𝑥). The $`\pm 0.5`$ is a half-pixel margin measured from pixel centers. **References**: a rule set by this program
4. Tilt 𝜃: the direction angles 𝛼 of the eight lines (for row ends, from the slope $`m = dx/dy,\ \alpha = \mathrm{atan2}(1, m)`$; for column ends, $`\alpha = \mathrm{atan2}(m, 1)`$) are averaged as quadrupled angles, $`\theta = 1/4 \cdot \mathrm{atan2}(\sum \sin 4\alpha, \sum \cos 4\alpha)`$ (−45°–45°, clockwise positive).
   The rectangle's sides alone cannot distinguish 𝜃 from $`\theta \mp 90^\circ`$. If $`\lvert \theta \rvert < 1^\circ`$ (untilted margins · letterboxes), it is not used.
   - **Note** — **Why**: The slopes of the eight lines must be combined into one rotation angle, which face finding later uses as its tilt hypothesis. **How it works**: Rectangle sides repeat every 90° (horizontal and vertical sides), so multiplying angles by 4 maps all four directions to one point. Summing unit vectors $`(\cos 4\alpha, \sin 4\alpha)`$, taking atan2 and dividing by 4 is the mean direction of circular statistics. A plain average of angles would turn −44° and 44° into 0°. The result has a 90° period, so 𝜃 and $`\theta \mp 90^\circ`$ cannot be told apart, and face finding tries all three hypotheses. **References**: [R83 Fisher 1993](../README.en.md#r83)
5. Only during the background stages (everything below, and the stages after face finding), each pixel of the band $`B = F \oplus 7\times 7`$ (𝐹 widened by 3px: mixed colors · outliers at the boundary created by rotation) has
   its 𝑈, original, alpha, $`\mathrm{known}`$, line, crisp line, and $`\mathrm{inMask}`$ replaced by the values of the nearest pixel outside 𝐵 by 4-neighbor <mark>breadth-first search</mark>, restored at the end.
   Then 𝐹 is set as background (removed from returned parts). Even with transparent corners, the background is searched for, and "send to background" also works. The background layer's alpha is the original alpha (255 as is for opaque pictures).
   - **Note** — **Why**: Where the fill meets the picture, rotation interpolation leaves blended colors and outliers that would be taken as lines or character. Covering this band with outside picture values during the background stages only lets background finding start naturally from the border. **How it works**: $`F \oplus 7\times 7`$ is dilation (Minkowski sum) with a 7×7 square structuring element, widening 𝐹 by 3px on every side. Spreading inward from outside the band by 4-neighbor breadth-first search gives each band pixel the value of the outside pixel nearest in steps (Manhattan distance). **References**: [R15 Soille 2003](../README.en.md#r15) · [R14 Gonzalez · Woods 2018](../README.en.md#r14)
6. Faces are searched for in the picture before filling.

### The picture's down direction (0.37)

When there is a tilt hypothesis (rotated canvas or the "Tilted picture" setting), the down directions 𝑓 of the naming faces (mirror-agreed) are averaged with weights $`w = \max(0, s - 10)^2`$,
and if $`\bar g = \sum w f / \sum w`$ has $`\lvert \bar g\rvert \ge 0.8`$ (the faces agree) and is tilted more than 40° from vertical, $`g = \bar g / \lvert \bar g\rvert`$ is used as the down direction.

**Note** — **Why**: In a rotated picture the "bottom border" need not be the bottom of the file. The down directions indicated by the faces are combined to find the true down. **How it works**: Each face's unit down vector 𝑓 is averaged with a weight from its score. $`w = \max(0, s - 10)^2`$ gives weak faces near the threshold of 10 almost nothing and high scores much more. The length $`\lvert \bar g\rvert`$ of a mean of unit vectors measures how well the directions agree (the mean resultant length of circular statistics), so 0.8 or more means the faces agree. $`\bar g / \lvert \bar g\rvert`$ normalizes it to a pure direction. **References**: [R83 Fisher 1993](../README.en.md#r83)
- For the outward direction 𝑛 of a border pixel (top $`(0, -1)`$ · right $`(1, 0)`$ · bottom $`(0, 1)`$ · left $`(-1, 0)`$, both at corners), the side with $`n \cdot g \ge 0.5`$ is the "bottom" border.
  The bottom-border rule of the flat background (1) and the seeds of the scene background (stage 1 starts without the "bottom" border) use this border.
  - **Note** — **Why**: Which border is "bottom" in a rotated picture must be known before the bottom-border rule and seed choice can be used. **How it works**: The dot product $`n \cdot g`$ of two unit vectors is the cosine of the angle between them, so 0.5 or more means within 60°: the border faces roughly downward. **References**: [R35 Strang 2016](../README.en.md#r35)
- The "upper corners" excluded when restoring cropped parts are the corners with corner direction $`(s_x, s_y) \in \lbrace\pm 1\rbrace^2`$ satisfying $`(s_x g_x + s_y g_y) / \sqrt 2 < -0.4`$.
  - **Note** — **Why**: Restoring cut-off parts must skip the two top corners where sky or ceiling meets the border; in a rotated picture the down direction decides which corners are on top. **How it works**: $`(s_x, s_y)/\sqrt 2`$ is the unit vector toward a corner; a dot product with 𝑔 below −0.4 means an angle above about 114°, so the corner points away from down (upward). **References**: [R35 Strang 2016](../README.en.md#r35)
- 40° is larger than the maximum tilt of faces found without a tilt hypothesis (pair filter $`\lvert \Delta y\rvert \le 0.8\Delta x`$, 38.7°), so it is never used for upright pictures without a tilt hypothesis.
  - **Note** — **Why**: On upright pictures without a tilt hypothesis this rule must stay off so existing results do not change. **How it works**: The pair filter $`\lvert \Delta y\rvert \le 0.8\Delta x`$ means the eye line slopes at most $`\arctan 0.8 \approx 38.7^\circ`$, so 40° cannot arise in that case. **References**: a rule set by this program

### Flat · gradient background

1. The $`\mathrm{known}`$ pixel colors on the border are counted in per-channel 16-level bins $`q(U) = 256\lfloor 15.99U_R\rfloor + 16\lfloor 15.99U_G\rfloor + \lfloor 15.99U_B\rfloor`$ (4096 bins), and the average of the fullest bin is the reference color 𝑟.
   It gives up if there are fewer than 16 $`\mathrm{known}`$ border pixels, or if fewer than 45% of them have $`\max_c\lvert U_c - r_c\rvert < 0.1`$.
2. Starting from border pixels with $`\max_c\lvert U - r\rvert < 0.12`$, it spreads into $`\mathrm{known}`$ pixels with neighbor-to-neighbor change $`< 0.035 \cdot k`$ and difference from the starting reference color $`< 0.3`$ (each pixel carries its own reference color while spreading).
   $`k = \min(1, 1200 / \max(W, H))`$ is the size ratio (1 for a long side of 1200px or less). If $`k < 1`$ and the area condition of 4 fails, 1–4 are redone with $`k = 1`$.
   It spreads first from the top · right · left borders and then from the bottom border; among 4-connected components newly reached only from the bottom border, those with 5% or more pixels having $`\max_c\lvert U - r\rvert > 0.04`$ are removed from the background.
   White clothes · skirts reaching the bottom edge of the picture have shading · folds even if as white as the background, while a white floor · margin on the bottom border is almost one color.
   - **Note** — **Why**: This stage takes the nearly single-colored area connected to the border as background. **How it works**: It is a flood fill that starts from the most common border color and spreads between similar neighboring colors. **References**: [R14 Gonzalez · Woods 2018](../README.en.md#r14)
3. Walking along the border (the path going once around top → right → bottom → left) twice in both directions, $`\mathrm{known}`$ pixels within 64 cells of the last background pixel on the path and with $`\max_c`$ difference $`< 0.05`$ from its color
   are added as new seeds (their own color as reference) and it spreads again with tolerance 0.12 (until there are no new seeds, at most 3 times). The walk is broken when it meets a line (a pixel that is not $`\mathrm{known}`$).
   - **Note** — **Why**: This continues a background whose color changes slowly along the border, as in a gradient. **How it works**: Walking the border, pixels close to the last background color are added as new seeds and the fill is repeated. **References**: [R14 Gonzalez · Woods 2018](../README.en.md#r14)
   - **Floor band** (0.40): the known pixels on the left, right and bottom borders that are not yet background are counted in the same 4096 bins as in 1; if the fullest bin holds 10% or more of the known border pixels, its average is a second reference color r₂.
     If border pixels within a channel-max difference of 0.12 from r₂ make up at least 3% of the height on the left and on the right, and at least 30% of the width on the bottom, the area spread from them under the same conditions as 2 (neighbor change < 0.035k, difference from r₂ < 0.3) is the band F.
     For each column x the topmost pixel t(x) of F is taken, and a line y = a·x + b is fitted on 64 evenly chosen columns with a = the median of the slopes between every two columns and b = the median of t(x) − a·x (<mark>Theil–Sen</mark>; columns hidden by the character, where t(x) sags lower, do not move the medians).
     F is added to the background if it covers at least 3% and at most 60% of the picture, at least 60% of the columns are within τ = max(3, 0.01H)px of the line, and at most 2% of F's pixels are more than τ above the line. It is not done for rotated pictures (whose downward direction is set).
     The floor of a line-drawn room, differing in color from the wall, is caught here, while clothes · hair crossing the bottom of the picture have a curved top edge and too few columns on the line. On the 666 pixiv pictures, all 7 pictures that reached this check were stopped by the straight-top-edge condition.
     **Fallback line** (0.43): if these conditions fail while F is 3–60% of the picture (the character hides much of the floor and the Theil-Sen line wavers), among the lines through two of the 64 columns,
     the one with at most one column more than τ above it and the most columns within τ is chosen. If 25% or more of the width lies within τ of it, at least half of the leftmost and of the rightmost 10% of columns each lie within τ
     (the wall-floor line crosses the picture), and no more than 2% of F is more than τ above it, F is added to the background. On the 777 real pictures no picture changed through this line.
     - **Note** — **Why**: This picks out a floor of a different color from the wall by its straight top edge. **How it works**: The <mark>Theil–Sen estimator</mark> takes the median of pairwise slopes, a line fit not swayed by columns hidden by the character (outliers). **References**: [R45 Theil 1950](../README.en.md#r45) · [R46 Sen 1968](../README.en.md#r46)
4. It is used only if the area is 3–97% of the whole.
5. **Closing narrow gaps** (0.34): if the background found by 1–4 is bright and almost one color (median $`L^*`$ of at most about 20,000 background $`\mathrm{known}`$ pixels $`\ge 70`$,
   share within $`\Delta E < 10`$ of that median color $`\ge 0.6`$, the same formula as "almost one color" in face-based widening), 1–4 are redone with the same thresholds,
   but it does not spread into $`\mathrm{dilate}_g(B)`$, the wall $`B = \lnot\mathrm{known} \lor(\text{change to the right · lower neighbor} \ge 0.035k)`$ dilated by $`g = \max(2, \mathrm{round}(2 \cdot \max(W, H)/1200))`$.
   After spreading, $`\mathrm{known}`$ pixels up to $`g + 1`$ steps from the background are restored with the original spreading conditions (neighbor change $`< 0.035k`$ and difference from the reference color $`< 0.3`$).
   The fill cannot cross outlines broken by $`2g`$ or less (faint lines, anti-aliasing gaps), and the background around the walls is filled again by the restoration.
   If the redone result fails the area condition of 4, the first result is used.
   For scene · patterned backgrounds, single-step color differences become walls here and there and the fill breaks up, and for dark one-color backgrounds (night scenes), background objects beyond the closed gaps return to the character, so it is not done (7.5).
   - **Note** — **Why**: This keeps the background fill from leaking into the character through gaps in broken outlines. **How it works**: The walls are dilated by 𝑔 to close gaps up to $`2g`$ wide, and after filling, $`g + 1`$ steps of regrowth recover the background around the walls (the same idea as morphological closing). **References**: [R15 Soille 2003](../README.en.md#r15)

### Scene background

Line density is the value blurred with $`\sigma = 0.02 \cdot \max(W, H)`$. If line pixels are fewer than $`0.002N`$, the scene background is not searched for.

**Note** — **Why**: This uses the difference that a scene background has few lines (empty sky, walls) while the character is dense with lines. Pictures with almost no line pixels cannot be split this way and are skipped. **How it works**: Gaussian-blurring the 0/1 line map gives each pixel the share of lines within about 𝜎 of it (a kernel density estimate). Setting 𝜎 to 2% of the long side looks at the same relative neighborhood at any picture size. Below $`0.002N`$ line pixels (0.2% of the picture) there is no density contrast. **References**: [R14 Gonzalez · Woods 2018](../README.en.md#r14)

**Degree of enclosure by lines** $`\varepsilon(p)`$: the line map is reduced to $`S = 240`$ cells on the long side ($`w = \max(2, \mathrm{round}(240W / \max(W, H)))`$, ℎ likewise;
pixel $`(x, y)`$ falls in cell $`(\min(w - 1, \lfloor xw/W\rfloor), \min(h - 1, \lfloor yh/H\rfloor))`$, and a cell is a wall if it contains even one line pixel).
From each cell, it goes straight in 16 directions $`\theta_k = 2\pi k/16`$ for $`t = 1 \dots 60`$ cells (25% of the long side) ($`(\mathrm{round}(x + t \cos \theta_k), \mathrm{round}(y + t \sin \theta_k))`$); if the first thing it meets is a wall, the direction is blocked,
and if it leaves the picture or meets no wall within 60 cells, the direction is open. 𝜀 is the share of blocked directions, and a pixel's value is that of its cell.
**Enclosed places** are $`\varepsilon \ge 0.9`$ (15 or more of 16 directions). The number of cells does not depend on the picture size, so it takes 0.1–0.3 seconds for any picture (longer with sparser lines).

**Note** — **Why**: Wide empty paint inside the character (face, clothes) has low line density and looks like background, but it is surrounded by lines. The degree of enclosure removes such places from the background candidates. **How it works**: From each cell, straight rays are cast in 16 directions (22.5° apart) and the share of directions that hit a wall within 60 cells is measured. Ray points are the grid points $`(x + t\cos\theta_k,\ y + t\sin\theta_k)`$ rounded. 15/16 or more means an almost closed place. When the line map is reduced to 240 cells on the long side, a cell is a wall if it holds any line pixel (max reduction), so thin lines do not vanish, and the work is bounded by $`240^2 \times 16 \times 60`$ at any picture size. **References**: [R14 Gonzalez · Woods 2018](../README.en.md#r14) · a rule set by this program

```math
D_a=G_\sigma(\mathbb 1_{line}),\quad D_c=G_\sigma(\mathbb 1_{crisp}),\quad D_s=G_\sigma(\mathbb 1_{line\wedge\neg crisp}),\qquad
\tau_a=\tfrac14\,\mathrm{median}_{line}D_a,\quad \tau_c=\tfrac14\,\mathrm{median}_{crisp}D_c
```

**Note** — **Why**: What counts as "low line density" differs from picture to picture (thick dense lines, thin sparse lines). Setting the threshold from the picture's own density on its lines adapts it to each picture. **How it works**: $`\mathbb 1_{line}`$ is the indicator that is 1 on line pixels and $`G_\sigma`$ a Gaussian blur, so 𝐷 is the share of lines nearby. The median density on lines is "the typical density where there are lines", and a quarter of it marks sparse places. The median is a representative value not swayed by a few very dense spots. Crisp lines and soft lines ($`line \wedge \neg crisp`$) are separated so blended, smudgy backgrounds can be handled in stage 2. **References**: [R14 Gonzalez · Woods 2018](../README.en.md#r14) · [R50 Hyndman · Fan 1996](../README.en.md#r50)

The median is $`i/1000`$ for the first bin 𝑖 where the cumulative count reaches half in the 1001-bin histogram of $`\mathrm{round}(1000D)`$ ($`\tau_c = 0`$ if there are no crisp lines).

**Note** — **Why**: This finds the median of hundreds of thousands of values quickly and identically every time, without sorting. **How it works**: Counting 0–1 values in 0.001-wide bins and finding the first bin where the running count reaches half gives the middle of the sorted values to within 0.001 (a quantile from a histogram). **References**: [R50 Hyndman · Fan 1996](../README.en.md#r50)

- **Stage 1 candidates**: $`\mathrm{known} \land D_a < \tau_a \land \varepsilon < 0.9`$. The candidates are eroded by $`r = \max(2, \mathrm{round}(3s))`$, filled from the top · left · right borders, and restored within the original candidates by the eroded amount (+1). It does not leak through narrow gaps.
  - **Note** — **Why**: Even a sparse-line area leaks into the character if it connects through a narrow gap. **How it works**: Eroding the candidates by 𝑟 cuts necks up to $`2r`$ wide. After filling from the border, regrowing by the same amount (+1) only inside the original candidates (conditional dilation, morphological reconstruction) restores the shape of wide areas but not what lies beyond a cut neck. $`r = \max(2, \mathrm{round}(3s))`$ is a length threshold, so it is multiplied by the size ratio 𝑠. **References**: [R15 Soille 2003](../README.en.md#r15) · [R14 Gonzalez · Woods 2018](../README.en.md#r14)
- **Blocking the flat background edge** (0.37): the flat · gradient background $`B_1`$ (above), plus pixels connected to it with 4-neighbors within 3 steps and with $`\max_c\lvert \Delta U_c\rvert < 0.06`$ from the $`B_1`$ pixel they started from,
  form the "background-like pixels" $`\tilde B`$ (the flat background stops 2px before crisp edges, so this includes the space in between).
  In the stage 1 · 2 fills (both filling from the eroded candidates and restoring), a step $`p \to q`$ is blocked when $`q \notin \tilde B`$ and either $`p \in \tilde B`$ or the pixel one step back $`p' = 2p - q`$ is in $`\tilde B`$,
  and the $`\max_c\lvert \Delta U_c\rvert`$ between that pixel and 𝑞 is 0.1 or more (up to a 1–2px blended edge). Not done when there is no $`B_1`$; margin widening · the color model are unchanged.
  - **Note** — **Why**: Where a flat background meets the character without a line (black stockings or clothes on a light background), the scene fill crosses the boundary into the character. Steps leaving the flat background with a large color change are blocked. **How it works**: For a step $`p \to q`$, if the start 𝑝 or the pixel one step back $`p' = 2p - q`$ (the vector from 𝑞 to 𝑝 extended once more from 𝑝) is background-like, the target 𝑞 is not, and the color changes by 0.1 or more in some channel, the step crosses from background into another object. Looking one step back also blocks edges blended over 1–2px by anti-aliasing. **References**: a rule set by this program
- **Blocking before dark places** (0.42): in the same stage 1 · 2 fills (also when searching again without 𝜀), a step $`p \to q`$ is also blocked when, in the Lab of 𝑈 (the same values as crisp edges), $`L^*_q \le 35`$ and either $`\Delta E(p, q) \ge 20`$
  or, for the pixel one step back $`p' = 2p - q`$ (when it is inside the picture without wrapping to another row), $`\Delta E(p', q) \ge 20`$. Done even without $`B_1`$; with $`B_1`$ it is used together with the blocking above.
  Only whether the arriving pixel is dark is checked. Also blocking when the starting pixel is dark made $`\mathrm{BER}`$ worse by 0.226 on one ground-truth picture (0.42 in 12).
  - **Note** — **Why**: Dark hair or clothes meeting the background without a line let the scene fill run into them. Steps into a dark place with a large color change are blocked. **How it works**: $`\Delta E`$ is the Lab distance (CIE76) and 20 is a clearly different color. Only the target is tested for darkness ($`L^*_q \le 35`$), so steps from background into a dark character are blocked while steps from dark to light are not; blocking those too made results worse on the ground-truth pictures. **References**: [R7 CIE 2004](../README.en.md#r7) · this program's experiments (12)
- **Widened blocking before dark places** (0.43): after the scene background is found, stages 1 · 2 are filled once more with the blocking above also checking the pixel two steps back $`p'' = 3p - 2q`$ (when inside the picture without wrapping to another row) with $`\Delta E(p'', q) \ge 20`$.
  From the two results before the area criterion and returning swallowed characters, $`S`$ and $`S_3`$, the pixels of $`S \land \lnot S_3`$ that are not flat background are remembered and, after all background stages, put back on the character side unless they are gaps (below).
  The other stages still run on $`S`$, so only these pixels change (changing the scene background itself shifted the color statistics of later stages and disturbed other places, 0.43 in 12). Searching the scene background once more costs time: 2.7% on 8 real pictures.
  - **Note** — **Why**: The blocking is widened by one more step so dark parts do not leak where blended edges are wider than 2px. **How it works**: $`p'' = 3p - 2q = p + 2(p - q)`$ is the point two steps back along the direction from 𝑞 to 𝑝. The other stages still run on the original result 𝑆 and only the difference $`S \land \lnot S_3`$ is returned to the character at the very end, so the change is confined to those pixels and later stages' color statistics stay put. **References**: a rule set by this program · this program's experiments (12)
- **Returning islands in the scene background** (0.38): if $`B_1`$ exists, the finished scene background 𝑆 (after returning swallowed characters and passing the area criterion) is split into 4-neighbor connected components (islands) of $`S \land \lnot \tilde B`$,
  and the islands containing no top · left · right border pixel form $`\mathcal I`$ (if the picture's down direction is set, the border pixels that are not the bottom border for that direction, 4.5).
  Splitting the character lump $`C = \lnot(B_1 \lor S) \lor \bigcup \mathcal I`$ into 4-neighbor connected components with largest area $`\lvert C_\max \rvert`$, an island $`I \in \mathcal I`$ is removed from 𝑆 when the component $`C(I)`$ containing it
  has $`\lvert C(I)\rvert/ \lvert C_\max \rvert \ge 0.25`$ or contains the center $`(\mathrm{round}(c_x), \mathrm{round}(c_y))`$ of a found face (4.5) (it is also removed from the scene background before returning swallowed characters).
  Then 𝑆 is merged into $`B_1`$. In real pictures, the components of floating text · emblems had $`\lvert C(I)\rvert/ \lvert C_\max \rvert \le 0.04`$.
  - **Note** — **Why**: This undoes cases where the scene fill takes small areas inside the character's body (pieces of clothing in the background color) as islands. Islands that do not touch the border and attach to a large character blob are likely part of the character. **How it works**: 4-neighbor connected-component labeling separates islands and character blobs. If the blob containing an island is at least 0.25 of the largest blob by area ($`\lvert C(I)\rvert / \lvert C_\max\rvert`$), the island belongs to a main character; floating text and patterns are at most 0.04, so the two separate. A blob containing a face center also counts as character. **References**: [R14 Gonzalez · Woods 2018](../README.en.md#r14) · a rule set by this program
- **Stage 2 candidates**: $`\text{stage 1 candidates} \cup (D_c < \tau_c \land D_s \ge 0.085 \land(\mathrm{known} \lor \text{faint line}))`$. Filled the same way from the stage 1 background and the top · side borders.
  - **Note** — **Why**: Soft brush strokes and smudged backgrounds have few crisp lines but many soft ones, so stage 1 sees high line density and leaves them out. Places with few crisp lines and many soft ones are added to the candidates. **How it works**: It uses the difference that character outlines are crisp while background detail is mostly soft. $`D_s \ge 0.085`$ means at least 8.5% of the neighborhood is soft line. **References**: a rule set by this program
- **Margin**: starting from the background, up to $`\mathrm{round}(0.05 \cdot \max(W, H))`$ steps, it widens into $`\mathrm{known}`$ pixels with neighbor change $`\max_c\lvert \Delta U_c\rvert < 0.03 \cdot k`$ (𝑘 as for the flat background above), $`\max_c`$ difference from the starting color $`< 0.1`$, and $`\varepsilon < 0.9`$.
  If $`k < 1`$ and the area after widening is below $`0.05N`$, it is reverted to before widening and widened again with $`k = 1`$.
  - **Note** — **Why**: The line-density blur spreads by 𝜎, so background close to the character (the margin) drops out of the candidates. It is recovered by growing along continuous color. **How it works**: A breadth-first fill under three conditions: neighbor change $`< 0.03k`$ (slow gradients pass), difference from the start color $`< 0.1`$ (no drifting color over long distances), and $`\varepsilon < 0.9`$ (no entering enclosed places). Steps are capped at 5% of the long side. 𝑘 is the size ratio that compensates for smaller per-step color changes on large pictures. **References**: [R14 Gonzalez · Woods 2018](../README.en.md#r14)
- It is used only if, after returning swallowed characters (below), the area is 2–90%. If the scene background with 𝜀 fails this criterion, it is searched once more without the 𝜀 condition (removing $`\varepsilon < 0.9`$ from the stage 1 candidates and the margin).
  The color model · face-based widening keep using 𝜀. Pictures that exceeded 90% because a character with an invisible outline was swallowed whole (a black-haired character on a gradient sky) are used after returning, too.
  - **Note** — **Why**: A scene background that is too small is noise, and one that is too large has swallowed the character. If the 𝜀 condition is too strict and fails, the search is repeated without it. **How it works**: Area shares (2%, 90%) act as a sanity check on the result. **References**: a rule set by this program

### Cropped character parts

For the connected pieces of the stage 1 background, runs are made by walking the border path once. Pieces under 0.3% are treated as gaps.
The widest piece, pieces over 15%, and pieces touching near the two upper corners (within $`\max(3, \mathrm{round}(0.05W))`$ from the corner along the top border and $`\max(3, \mathrm{round}(0.05H))`$ along the side borders) are excluded.
If, in every run of a piece, there is a crisp line on the way to the first other piece met on each side across gap runs, and the average colors (Lab of 𝑈) of the two pieces differ by $`\Delta E \ge 25`$, the piece is returned to the character.

**Note** — **Why**: Character parts cut off by the picture border (cropped arms, hair) fall into the stage-1 background that starts from the border. Pieces separated along the border by crisp lines and very different in color are cut-off character, not background. **How it works**: Each piece is compared with its neighbors run by run along the border path. A mean-color $`\Delta E \ge 25`$ is a clearly different color. Pieces near the two top corners are skipped to protect backgrounds such as sky or ceiling that touch those corners; the range is 5% of the width or height (at least 3px). **References**: [R7 CIE 2004](../README.en.md#r7) · a rule set by this program

### Widening with a color model (GrabCut style)

1. **Regions**: the Lab of the original is split by <mark>k-means</mark> (24 colors, 40,000 samples) on $`\mathrm{known}`$ pixels; 4-connected components of the same color with 40px or more become regions 𝑟, and the rest are attached by label filling.
   If there are fewer than $`0.2N`$ $`\mathrm{known}`$ pixels, this stage and face-based widening are not done.
   - **Note** — **Why**: A graph cut over hundreds of thousands of pixels would be slow, so connected pixels of similar color are grouped into regions (superpixels) and the cut runs on regions. **How it works**: <mark>k-means</mark> repeatedly assigns each point to the nearest center and moves each center to the mean of its points, reducing the sum of squared errors $`\sum \lVert x - \mu\rVert^2`$ (Lloyd's algorithm). Working in Lab makes distances close to perceived color differences, and learning centers from 40,000 samples bounds the time. Components under 40px are noise and are filled with neighboring labels. **References**: [R22 Lloyd 1982](../README.en.md#r22) · [R7 CIE 2004](../README.en.md#r7)
2. **Region features**: area $`A_r`$, mean Lab ($`\mathrm{known}`$ pixels), crisp-line density ratio $`\rho_r = \mathrm{mean}_r(D_c)/\tau_c`$ (here $`\tau_c \ge 10^{-4}`$), existing background share $`\beta_r`$, number $`F_r`$ of top · left · right border pixels that are in 𝑟,
   and the share of crisp lines on the perimeter $`\kappa_r = (\text{number of boundary pixel pairs on crisp lines})/(\text{number of boundary pixel pairs touching other regions})`$.
   - **Note** — **Why**: Cues for telling character from background (area, color, crisp-line density, existing background share, border contact, enclosure by crisp lines) are gathered per region. **How it works**: $`\rho_r`$ divides the region's mean crisp-line density by the picture's reference $`\tau_c`$, removing per-picture differences in line weight and density (1 means equal to the reference). $`\kappa_r`$ is the share of the region's boundary lying on crisp lines, large for character parts enclosed by outlines. $`\tau_c \ge 10^{-4}`$ prevents division by zero. **References**: [R25 Rother et al. 2004](../README.en.md#r25) · a rule set by this program
3. **Contact**: for each horizontally · vertically adjacent pixel pair in different regions, 1 is added to the line contact length 𝑙 if either is $`\mathrm{inMask}`$, otherwise to the lineless contact length 𝑜,
   and if either is a crisp line, 1 is also added to the crisp line length 𝑘.
4. **Color distribution**: Lab is counted in $`13 \times 32 \times 32`$ bins ($`\lfloor L/8\rfloor,\ \lfloor(a + 128)/8\rfloor,\ \lfloor(b + 128)/8\rfloor`$, out-of-range values go to the end bins), smoothed by summing the neighboring $`3 \times 3 \times 3`$ bins, and normalized.

   $`\displaystyle p(i)=\frac{\tilde h(i)}{\sum_j \tilde h(j)},\qquad \tilde h(l,a,b)=\sum_{|\delta_l|,|\delta_a|,|\delta_b|\le1}h(l+\delta_l,\,a+\delta_a,\,b+\delta_b)`$
   - **Note** — **Why**: Measuring whether a region has character colors or background colors as a probability needs color distributions for both sides. With fine bins and few samples many bins are empty and give probability 0, so neighboring bins are pooled for smoothing. **How it works**: It is a 3-D color histogram of Lab in steps of 8 (13 × 32 × 32 = 13,312 bins). Summing 3×3×3 neighbors is a kernel density estimate that blurs the histogram with a box kernel, and dividing by the total gives a probability distribution 𝑝 summing to 1. A histogram in place of GrabCut's Gaussian mixture needs no iterative fitting, so it is fast and always gives the same result. **References**: [R84 Swain · Ballard 1991](../README.en.md#r84) · [R25 Rother et al. 2004](../README.en.md#r25)

5. **Initial values**: background $`B^0 = \lbrace\beta_r > 0.5\rbrace \cup \lbrace F_r > 0 \land \rho_r < 1\rbrace`$, character core $`F^0 = \lbrace\rho_r > 3 \land F_r = 0\rbrace \setminus B^0`$.
   $`F^0`$ is used only for the overlap check below; the character distribution of the first cut is learned from all regions outside $`B^0`$.
   - **Note** — **Why**: A graph cut needs two initial color distributions to start. Sure background (more than half existing background, or touching the border with few lines) and sure character (dense crisp lines, not touching the border) provide the starting point. **How it works**: $`\lbrace\text{condition}\rbrace`$ is the set of regions meeting the condition, ∪ is union and ∖ is set difference. $`\rho_r > 3`$ means crisp lines more than three times denser than the reference. **References**: [R25 Rother et al. 2004](../README.en.md#r25) · a rule set by this program
6. **Safeguards**:
   - Not done if the overlap of the two distributions is $`\sum \min(p_{F^0}, p_{B^0}) \ge 0.3`$.
     - **Note** — **Why**: If the character and background color distributions overlap heavily, color cannot separate them and the color model risks sending the wrong places to the background. **How it works**: $`\sum \min(p, q)`$ is the intersection of two normalized histograms (histogram intersection): 0 for no overlap, 1 for identical distributions. 0.3 or more means over 30% overlap. **References**: [R84 Swain · Ballard 1991](../README.en.md#r84)
   - Not done if the existing background covers 90% or more of the top · left · right borders.
7. **Energy**: for labels $`x_r`$ that are 1 for character and 0 for background,

   $`\displaystyle E(x)=\sum_r \theta_r\,[x_r=0]\;+\;\sum_{(r,q)} w_{rq}\,[x_r\ne x_q]`$

   $`\displaystyle \theta_r=\sum_{p\in r,\,known}\mathrm{clip}_{[-3,3]}\ln\frac{p_F(c_p)+10^{-6}}{p_B(c_p)+10^{-6}} +A_r\,\mathrm{clip}_{[0,2]}\ln\frac{\max(\rho_r,\,10^{-3})}2 -A_r\,\beta_r-20F_r +A_r\,\mathrm{clip}_{[0,2]}\frac{\kappa_r-0.3}{0.15}`$

   The first term is color, the second is how far the crisp-line density exceeds $`2\tau_c`$ (half the median density on crisp lines) (maximum 2 at $`\rho_r = 2e^2 \approx 14.8`$),
   the third · fourth terms are the existing background and the border, and the fifth is how much the region is surrounded by crisp lines (0 at $`\kappa_r`$ 30%, 2 at 60%).

   $`\displaystyle w_{rq}=8\,o\,\exp\!\left(-\frac{\Delta E_{rq}^2}{2\cdot 12^2}\right)+0.3\,l`$

   $`\theta_r > 0`$ is the cost on the character side. Regions with $`\beta_r > 0.5`$ are fixed as background ($`\theta = -\infty`$); regions with mean $`L^* < 30`$ and $`C^* < 12`$ (near-black achromatic) and
   regions with region mean $`\bar \varepsilon_r \ge 0.9`$ (enclosed by lines) are fixed as character ($`\theta = +\infty`$).
   - **Note** — **Why**: For each region, evidence for character (color, line density, enclosure) and for background (existing background, border) is combined into one cost, a cost is added for putting similar-colored regions that touch without a line on different sides, and the split with the lowest total cost is found. **How it works**: 𝐸 is an energy of the same form as GrabCut's (data term + smoothness term). $`[x_r = 0]`$ is the Iverson bracket, 1 when true, so sending a region with $`\theta_r > 0`$ to the background costs $`\theta_r`$. The color term sums per pixel the log-likelihood ratio $`\ln(p_F/p_B)`$ of the two distributions (the evidence between two hypotheses in Bayesian discrimination); $`10^{-6}`$ prevents log 0, and clipping to ±3 keeps a few rare-color pixels from deciding. The line-density term $`\ln(\rho/2)`$ is 0 at 𝜌 = 2 and clips at 2 at $`2e^2`$; the 𝜅 term ramps from 0 at 30% to 2 at 60%. $`w_{rq}`$ multiplies the line-free contact length 𝑜 by a Gaussian weight $`\exp(-\Delta E^2/2\sigma^2)`$ (𝜎 = 12) that is larger for similar colors, and gives the line contact length 𝑙 a small weight 0.3 so cuts follow lines. $`\theta = \pm\infty`$ fixes that region's label. **References**: [R25 Rother et al. 2004](../README.en.md#r25) · [R24 Boykov · Jolly 2001](../README.en.md#r24) · [R7 CIE 2004](../README.en.md#r7)
8. **Minimum cut**: in the graph with capacity $`\theta_r^{+} = \max(\theta_r, 0)`$ from the source (character) to each region, $`\theta_r^{-} = \max(-\theta_r, 0)`$ from each region to the sink (background), and $`w_{rq}`$ in both directions between region pairs, the **<mark>Dinic</mark>** <mark>maximum flow</mark> is found
   (repeat: assign levels by <mark>breadth-first search</mark>, then push flow along augmenting paths whose level increases by one, depth-first, until blocked; residual capacity $`10^{-9}`$ or less counts as 0),
   and the regions reachable from the source in the residual graph become character. The <mark>maximum flow</mark> equals the <mark>minimum cut</mark>, so this is the split that minimizes $`E(x)`$.
   - **Note** — **Why**: The 0/1 labeling that minimizes the energy above is found exactly, without trying all $`2^{\text{regions}}`$ combinations. **How it works**: For a two-label energy with non-negative smoothness weights (submodular), the cut value of the source–sink graph equals the energy, so the minimum cut is the minimum energy. By the max-flow min-cut theorem (Ford–Fulkerson), after computing the maximum flow the side reachable from the source in the residual graph is one side of a minimum cut. Dinic's algorithm alternates building a breadth-first level graph and saturating it with depth-first blocking flows, finishing within $`O(V^2E)`$. Treating residual capacity at or below $`10^{-9}`$ as 0 prevents endless loops from rounding error. **References**: [R26 Ford · Fulkerson 1956](../README.en.md#r26) · [R27 Dinic 1970](../README.en.md#r27) · [R24 Boykov · Jolly 2001](../README.en.md#r24)
9. **Connection condition**: a new background region must be reachable from the reference background ($`B^0`$) crossing only boundaries whose non-crisp contact $`o + l - k`$ is at least $`\max(3, 0.3(o + l))`$. If not reachable, it is returned to the character.
   - **Note** — **Why**: A newly assigned background region that meets the existing background only across crisp lines is likely a character region beyond an outline. **How it works**: $`o + l - k`$ is the contact length not on crisp lines. Only regions reachable from the reference background by graph search across boundaries where that length is at least 30% of the contact (and at least 3px) stay background. **References**: a rule set by this program
10. The two color distributions are relearned from the split and 7–9 are repeated 4 times. The $`\mathrm{known}`$ pixels and faint line pixels of regions that became background are added to the background (crisp lines are not added).

The random numbers use a fixed seed (777) for this stage alone, so pictures where this stage does not act are not changed by a single bit. The region graph is built once when first needed and shared with the face stage below.

### Attached character parts

1. **Crisp edges**: pixels of the Lab of 𝑈 (the picture with the color under lines restored) with $`\max(\Delta E(p-1, p + 1), \Delta E(p-W, p + W)) \ge 20`$. Blurred, smudged edges have small differences across 2px and are not included.
   - **Note** — **Why**: This catches character boundaries where only the color changes, without a line (lineless coloring). **How it works**: The Lab distance between the two neighbors 2px apart is the magnitude of a central-difference color gradient. If the larger of the horizontal and vertical values is 20 or more, the edge is sharp; since it spans only 2px, soft blurred edges (gradients) change too little per step to count. **References**: [R7 CIE 2004](../README.en.md#r7) · [R14 Gonzalez · Woods 2018](../README.en.md#r14)
2. **Pieces**: 4-connected components 𝑘 of stage 1–5 background pixels that are neither crisp edges nor lines. Edge · line pixels are filled with the label of the nearest piece or character, and the contact length is measured by neighbor pairs with different labels.
3. **Color log-likelihood ratio**: Lab is counted in $`10 \times 16 \times 16 = 2560`$ bins ($`\lfloor L/10\rfloor,\ \lfloor(a + 128)/16\rfloor,\ \lfloor(b + 128)/16\rfloor`$, out-of-range values go to the end bins), and the character distribution $`h_C`$ ($`\mathrm{known}`$ not in background, $`n_C`$ pixels) is compared with
   the background distribution $`h_B`$ ($`\mathrm{known}`$, $`n_B`$ pixels) minus the piece's own $`h_k`$ (Laplace smoothing adding 1 to each bin, $`n_B - \lvert k\rvert`$ at least 1).

   $`\displaystyle \bar\ell_k=\frac1{|k|}\sum_{p\in k,\,known}\mathrm{clip}_{[-4,4]}\ln\frac{(h_C(c_p)+1)/(n_C+2560)}{(h_B(c_p)-h_k(c_p)+1)/(n_B-|k|+2560)}`$
   - **Note** — **Why**: This measures whether a piece taken into the background is closer to the character colors or the background colors, and returns it if it is character-colored. **How it works**: For each pixel of the piece, the log of the ratio of the probabilities of its color under the character and background distributions (the log-likelihood ratio) is summed and divided by the area. Positive means the character side is more likely. Laplace smoothing, adding 1 per bin, $`(h + 1)/(n + K)`$ (𝐾 = 2560), keeps unseen colors from getting probability 0. Removing the piece itself from the background distribution follows the leave-one-out idea and stops the piece from inflating the background distribution with its own colors and judging itself background. **References**: [R51 Manning et al. 2008](../README.en.md#r51) · [R74 Stone 1974](../README.en.md#r74)

4. **Conditions**: area at least 0.1% of the whole, not touching the top · left · right borders, contact length with the character at least 0.8 times the total contact length, $`\bar \ell_k \ge 0.8`$.
   **Border pieces** (0.41): a piece touching the top · left · right borders is chosen if, in the face frame $`(u, v)`$ (3 of face finding) of a face scoring 11 or more, at least half of its area (counted on a 2px grid) lies in the head ellipse $`(u/2.2)^2 + ((v + 0.3)/2)^2 \le 1`$ or
   the body column ($`-1.2 \le v \le 8`$, $`\lvert u\rvert \le 1.2 + 0.35 \cdot \max(v - 1.5, 0)`$), it is not the largest piece,
   its area is between 0.1% and 6% of the whole, its contact length with the character is at least 0.75 times the total, and $`\bar \ell_k \ge 0.75`$.
   Hair tips · sleeves · arms cut off by the frame come back under this condition, while border background far from faces and the largest background piece stay.
   - **Note** — **Why**: The likelihood ratio alone could return small background pieces too, so area and contact conditions are added. Pieces touching the border are likely background and are returned only near a face. **How it works**: The head ellipse $`(u/2.2)^2 + ((v + 0.3)/2)^2 \le 1`$ is, in face-frame coordinates (units of the eye distance 𝑑), an ellipse with horizontal radius 2.2 and vertical radius 2 centered 0.3 above the eyes. The body column is a trapezoid widening with slope 0.35 below $`v = 1.5`$ (the spread of shoulders and skirt). A contact ratio with the character of 0.8 or more means the piece is almost surrounded by character. **References**: a rule set by this program
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
   - **Note** — **Why**: Black hair or clothes on a dark background are close to the background color, so the likelihood ratio above does not return them. They are separated by whether their colors are rare in the border background. **How it works**: Each term of $`\nu_k`$, $`\ln\frac{n_T + K}{K} - \ln(h_T + 1) = \ln\frac{1/K}{(h_T + 1)/(n_T + K)}`$, is the log ratio of the uniform distribution $`1/K`$ to the Laplace-smoothed border distribution, positive when the color is rarer than average in the border background. Fine bins of 4 (102,400 bins) separate similar dark colors. Contact $`\ge 0.25\sqrt{|k|}`$ scales the requirement to the area, since a perimeter grows with the square root of area; repeatedly accepting pieces touching accepted ones is region growing. **References**: [R51 Manning et al. 2008](../README.en.md#r51) · a rule set by this program

### Face finding

It finds faces with hand-set rules and averaged patterns, without a trained model. The picture is scaled by $`k_f = 800 / \max(W, H)`$ ($`w = \max(2, \mathrm{round}(k_f W))`$, ℎ likewise)
(area averaging when shrinking, white backing $`A\cdot O + 1 - A`$ for transparent areas), and measured in Lab. Found positions · sizes are multiplied by $`1/k_f`$ to return to the processing resolution.

**Note** — **Why**: Running face finding at a fixed size (800px long side) keeps thresholds and radius lists valid at any picture size and the time constant. **How it works**: Area-average reduction and compositing over white $`A\cdot O + 1 - A`$ (4.0) are used, and positions and lengths found are scaled back by $`1/k_f`$. **References**: [R14 Gonzalez · Woods 2018](../README.en.md#r14) · [R1 Porter · Duff 1984](../README.en.md#r1)

1. **Eye candidates**: $`\ell = L^*/100`$ is blurred by 3 box blurs (radius $`\rho \in \lbrace1, 2, 3, 4, 5, 7, 9, 12, 15, 20\rbrace`$, $`\sigma^2 = \rho^2 + \rho`$: the box-blur variance formula of 4.2 solved backwards), and the <mark>Hessian</mark> is computed with second differences,

   $`\displaystyle L_{xx}=\ell_{x-1,y}-2\ell_{x,y}+\ell_{x+1,y},\quad L_{yy}=\ell_{x,y-1}-2\ell_{x,y}+\ell_{x,y+1},\quad L_{xy}=\tfrac14\left(\ell_{x+1,y+1}-\ell_{x-1,y+1}-\ell_{x+1,y-1}+\ell_{x-1,y-1}\right)`$

   $`\displaystyle D_\sigma=\sigma^4\left(L_{xx}L_{yy}-L_{xy}^2\right)\quad(L_{xx}+L_{yy}>0)`$

   A positive <mark>Hessian determinant</mark> means a round blob, and only $`L_{xx} + L_{yy} > 0`$ (center darker than its surroundings) is considered. $`\sigma^4`$ is the scale normalization that makes values comparable across sizes.
   Points that are the largest within the two neighboring scales and 5×5 and have $`D > 0.004`$ become candidates of radius $`r = 1.414\sigma`$, up to 3000 in descending order.
   - **Note** — **Why**: Eyes in anime pictures are round blobs darker than their surroundings. The standard way to find round dark blobs at many sizes is the <mark>determinant of the Hessian</mark> blob detector. **How it works**: The second derivatives of the blurred lightness are approximated by differences ($`L_{xx}`$ a central second difference, $`L_{xy}`$ a mixed difference of four diagonal points). The Hessian determinant $`L_{xx}L_{yy} - L_{xy}^2`$ is the product of the two eigenvalues (curvatures in two directions), positive for a round blob curving the same way in both and near 0 for a line curving in one. A positive trace $`L_{xx} + L_{yy}`$ (positive Laplacian) means the center is darker than the surroundings. $`\sigma^4`$ is Lindeberg's scale normalization ($`\sigma^2`$ per second derivative), making values comparable across sizes and peaking for blobs of radius about $`\sqrt 2\sigma`$. Three box blurs approximate a Gaussian; one box of radius 𝜌 has variance $`\rho(\rho + 1)/3`$, so three give $`\sigma^2 = \rho^2 + \rho`$. Only points larger than their neighbors in both scale and position are kept (non-maximum suppression). **References**: [R33 Lindeberg 1998](../README.en.md#r33) · [R17 Wells 1986](../README.en.md#r17) · [R14 Gonzalez · Woods 2018](../README.en.md#r14)
2. **Pairs**: two candidates (left 𝑎, right 𝑏) with distance $`d \ge 16,\ 4 \le d / \bar r \le 24`$ ($`\bar r`$ the mean of the two radii), $`\lvert \Delta y\rvert \le 0.8\Delta x`$, radius ratio $`\le 1.7`$.
   **Tilt hypotheses** (0.37): for a rotated canvas (tilt 𝜃), it searches separately for each hypothesis $`\varphi \in \lbrace\theta, \theta \mp 90^\circ \rbrace`$. The pair filter uses $`\lvert \tan \delta \rvert \le 0.8`$ for the difference 𝛿 (folded into −90°–90°) between the eye-to-eye direction and 𝜑,
   the tilt evidence ("not much tilted" in 5) is $`t = \lvert \tan(\angle e - \varphi)\rvert`$, and the position refinement of 6 and the selection of 7 are also done per hypothesis. A face lying on its side does not tell which way is down, so
   pairs whose eye line is steep are also measured in the frame rotated by 180° (both 𝑒 and 𝑓 sign-flipped). The hypothesis with the larger top score of naming faces (mirror-agreed: $`-\varphi`$ for the flipped picture) is used; on a tie, 𝜃.
   With the "Tilted picture" setting on, pictures that are not rotated canvases are also searched the same way with $`\varphi \in \lbrace0, -30, 30, -60, 60, -90, 90\rbrace^\circ`$ (0° is not favored).
   If neither, there is one $`\varphi = 0`$, the same as 0.36.
   - **Note** — **Why**: Two eyes are similar in size, a moderate distance apart and mostly side by side. These geometric conditions keep only the plausible faces among millions of pairs from thousands of candidates. **How it works**: $`4 \le d/\bar r \le 24`$ requires an eye distance of 4–24 eye radii, $`\lvert \Delta y\rvert \le 0.8\Delta x`$ an eye line within $`\arctan 0.8 \approx 38.7^\circ`$, and a radius ratio $`\le 1.7`$ similar eye sizes. In rotated pictures the reference direction is turned by 𝜑 and the same condition becomes $`\lvert\tan\delta\rvert \le 0.8`$; the angle difference is folded to −90°…90° because the eye line is an undirected axis. **References**: a rule set by this program · [R83 Fisher 1993](../README.en.md#r83)
3. **Face frame**: with the midpoint of the two eyes as the origin, the eye direction as 𝑢, and the downward direction perpendicular to it as 𝑣, grid samples (<mark>bilinear interpolation</mark>, edge values outside the picture) are taken in units of 𝑑.

   $`\displaystyle \mathbf c=\tfrac12(\mathbf a+\mathbf b),\quad d=|\mathbf b-\mathbf a|,\quad \mathbf e=\frac{\mathbf b-\mathbf a}d,\quad \mathbf f=\pm(-e_y,\,e_x)\ (f_y\ge0),\qquad \mathbf x(u,v)=\mathbf c+d\,(u\,\mathbf e+v\,\mathbf f)`$

   Conversely, the frame coordinates of pixel 𝑥 are $`u = (x - c)\cdot e / d,\ v = (x - c)\cdot f / d`$. The tilt is $`t = \lvert b_y - a_y\rvert/ \max(\lvert b_x - a_x\rvert, 10^{-6})`$.
   A grid is $`n_u \times n_v`$ points evenly dividing the range, including both ends.
   - **Note** — **Why**: Coordinates based on eye position and distance measure the same places (cheeks, nose bridge, lashes) at the same coordinates whatever the face size or tilt. **How it works**: It is a similarity transform $`\mathbf x(u, v) = \mathbf c + d(u\mathbf e + v\mathbf f)`$ (translation, rotation, scale) built from the center 𝑐, eye distance 𝑑, the unit eye direction 𝑒 and the perpendicular 𝑓. $`(-e_y, e_x)`$ is 𝑒 rotated by 90°, with the sign chosen to point down ($`f_y \ge 0`$). Since 𝑒 and 𝑓 are an orthonormal basis, the inverse is the dot product $`u = (x - c)\cdot e / d`$. Values at non-integer positions come from <mark>bilinear interpolation</mark>. **References**: [R35 Strang 2016](../README.en.md#r35) · [R14 Gonzalez · Woods 2018](../README.en.md#r14)

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

   **Note** — **Why**: Features common to anime faces (light, even skin; dark eyes; strong lashes; a highlight in the eye) are measured in fixed cells of the face frame. **How it works**: Cell ranges are in units of the eye distance 𝑑, so they do not depend on face size. Skin lightness is the median of 74 samples, so a few samples landing on hair or shadow do not move it. The iris color averages only the darker half of the eye cell, excluding the white and the highlight. The highlight ℎ is the difference between the brightest point and the median of 8 points around it, a local contrast that picks out small spots much brighter than their surroundings. **References**: a rule set by this program
4. **Average patterns**: the eye pattern (12×12, $`0.2 \le \lvert u\rvert \le 0.8,\ \lvert v\rvert \le 0.3`$, right eye mirrored) and the face pattern (16×16, $`\lvert u\rvert \le 1.1,\ -0.9 \le v \le 1.3`$) are
   the brightness measured on 31 faces of the 24 test pictures aligned by eye positions marked by a person, each set to mean 0 · standard deviation 1, then averaged (400 numbers inside the program).
   Candidates also set the same grid to mean 0 · standard deviation 1 and measure the correlation $`c = \mathrm{mean}(z \cdot T)`$. For eyes, the smaller of the two eyes.
   - **Note** — **Why**: Rules alone struggle to tell face-like patterns (clothing prints) from real faces, so the similarity to the average lightness pattern of real faces is measured. **How it works**: Standardizing lightness to mean 0 and standard deviation 1 (𝑧 scores) removes differences in brightness and contrast, and the mean product of two 𝑧-score grids $`\mathrm{mean}(z\cdot T)`$ is the Pearson correlation (normalized cross-correlation), between −1 and 1. The templates average the 𝑧 scores of 31 hand-marked faces. **References**: [R34 Lewis 1995](../README.en.md#r34) · [R60 Pearson 1900](../README.en.md#r60)
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

   **Note** — **Why**: Each cue is weak alone, so cues are mapped to 0–1, weighted and summed into a score that decides whether a pair is a face. **How it works**: Each cue is a linear ramp $`(\text{value} - \text{low})/\text{width}`$ clipped to 0–1: 0 below the low end and 1 from low + width (e.g. skin lightness $`(S - 60)/25`$ is 0 at $`L^*`$ 60 and 1 at 85). The weights sum to at most 15, and the whole-face template correlation gets the largest weight, 3. The tilt 𝑡 is the vertical eye difference over the horizontal one (a tangent). **References**: a rule set by this program

6. **Position refinement**: for the top 40 pairs by score, each eye in turn is moved within $`\pm 0.12d`$ (5×5 grid, spacing $`0.06d`$, 𝑑 the distance before refinement) to where the face pattern correlation is largest,
   repeated twice in the order left eye → right eye (moving only when the correlation becomes larger than now), and measured again.
   - **Note** — **Why**: Blob detection can place an eye a few pixels off because of the discrete scales, so each eye is moved to where the face template fits best. **How it works**: It is coordinate descent: one eye at a time moves to the position with the highest correlation on a 5×5 grid. Moves happen only when the correlation rises, so the fit never gets worse. **References**: [R34 Lewis 1995](../README.en.md#r34)
7. **Selection**: scores of 11 or more are chosen in descending order, but a pair is dropped if its center is less than $`\max(d, d')`$ from an already chosen face, or one of its eyes is within $`0.5 \max(d, d')`$ of that face's eyes.
   - **Note** — **Why**: The same face appears as several overlapping pairs, so only one is kept. **How it works**: This is non-maximum suppression: pick by descending score and discard nearby ones. The distance threshold is the larger eye distance $`\max(d, d')`$, matching face size. **References**: a rule set by this program
8. **A face-like place?**: a real face has the head almost entirely inside the picture, and the face itself is not on already found background. Only faces with 80% or more of the head ellipse (below) inside the picture,
   and with 30% or less already found background in it, or 5% or less background in the face ellipse (eyes · cheeks, $`u^2 + ((v - 0.2)/0.8)^2 \le 1`$), are kept.
   Picture pixels within $`2.4d`$ of the center are looked at every 4px horizontally · vertically (coordinates that are multiples of 4), and with one sample counted as $`16\,\mathrm{px}^2`$, "80% or more inside the picture" is
   a sample count inside the head ellipse of $`n \ge 0.8 \cdot \pi \cdot 2.2 \cdot 2 \cdot d^2 / 16`$.
   The top-scoring face is dropped only when more than half of its face ellipse is background.
   This reduces fake faces that grab a knee · cushion at large size and block wide background as "head · body zones", while keeping the faces of characters with small heads whose head ellipse is surrounded by background.
   All 30 real faces in the test pictures had 0% background in the face ellipse and at most 28% in the head ellipse.
   - **Note** — **Why**: A real face has its head inside the picture and does not float on background. This reduces fake faces (knees, cushions) blocking wide background as character area. **How it works**: An ellipse has area $`\pi ab`$ (radii $`2.2d`$ and $`2d`$), and each sample on the 4px grid stands for $`16\,\mathrm{px}^2`$, so "at least 80% inside the picture" is a sample count $`n \ge 0.8 \cdot \pi \cdot 2.2 \cdot 2 \cdot d^2 / 16`$. The face ellipse $`u^2 + ((v - 0.2)/0.8)^2 \le 1`$ has radii 1 and 0.8 and covers eyes and cheeks. **References**: a rule set by this program

The thresholds were set on the side of missing few faces. Fake faces (knees, hands, bowls, clothing patterns) only protect that place for the character in the stages below and do not add background,
but the character of a missed face is not protected.

9. **Faces for names · character folders**: for each pair measured up to 6, the adjustments below are added to the score and 7 · 8 are done once more (threshold 10.75). Background decisions (the stages below) use the faces of 7; part names and character splitting use these faces.

   | Adjustment | Value |
   |---|---|
   | Mouth visible | $`\mathrm{clamp}((m - 15)/20) - 1`$, 𝑚 = the median $`L^*`$ of the cheek · below-nose-bridge cell ($`\lvert u\rvert \le 0.9,\ 0.4 \le v \le 0.8`$) minus the minimum of the below-nose cell ($`\lvert u\rvert \le 0.25,\ 0.8 \le v \le 1.3`$) |
   | Eye contrast too strong | $`-\mathrm{clamp}((S - \text{eye cell mean }L^* - 40)/15)`$ |
   | Lower eyelid too bright | $`-\mathrm{clamp}((\text{lower band mean }L^* - \text{upper band mean }L^* - 35)/20)`$, upper band $`\lvert u\rvert \le 0.7,\ -0.3 \le v \le -0.12`$, lower band $`\lvert u\rvert \le 0.7,\ 0.12 \le v \le 0.3`$ |
   | Skin is white paper | $`-\mathrm{clamp}((S - 97)/3)`$ |

   **Note** — **Why**: Fake faces do more harm in names and character folders, so the score is adjusted with cues found in data marked real or fake. **How it works**: $`\mathrm{clamp}((x - a)/b)`$ is a ramp from 0 at 𝑎 to 1 at $`a + b`$. The mouth cue runs from −1 to 0 (−1 if no mouth shows); the others are penalties from 0 to −1. **References**: this program's experiments (11)

   When a person marked face candidates in 300 unseen pixiv pictures as real · fake (11), real faces had visible mouths (median 𝑚 of candidates scoring 9 or more: 57 vs 38 for fakes),
   and fakes (clothing patterns, text, props, snacks) often had too large eye contrast and lower-eyelid brightness or a white backing in the skin area.
   Among pairs scoring 10 or more, the mean adjustment is −0.13 for real faces (median 0) and −0.41 for fakes (a quarter at −0.85 or less).
   Two kinds of faces are used because changing the faces for background decisions with this adjustment too made the background flip between better and worse (7.5).

   **Head-structure cues** (0.48): on the default path (setting "Tilted picture" off), pairs whose score including the adjustments above is 9 or more get the bonus 𝐻 below (at most 7.5), and 7 · 8 are done with threshold 16.5.
   So a pair cannot be picked as a naming face without the bonus. A picked face reports its score before the bonus, and the faces for background decisions (7) are unchanged.
   On the face-frame grid ($`u`$ −2 to 2, $`v`$ −2 to 2.6, step $`0.1d`$, bilinear sampling), the per-channel medians of $`L^*`$ · $`a^*`$ · $`b^*`$ over the nose-bridge ($`\lvert u\rvert \le 0.12,\ 0.05 \le v \le 0.45`$) and cheek ($`0.3 \le \lvert u\rvert \le 0.7,\ 0.35 \le v \le 0.7`$) grid points are the reference skin color ($`L^*_s, a^*_s, b^*_s`$).
   Grid points inside the picture with $`L^* \ge L^*_s - 25`$ (not a line) and $`\Delta E \le 12`$ to the reference are skin; a blob is grown by 4-neighbours from the skin points of the nose bridge · cheeks.
   At each cheek height ($`v`$ = 0.3, 0.4, …, 0.8) we step outward from the centre by $`0.1`$ and take the last $`\lvert u\rvert`$ before the blob first breaks; the median of these is taken on the left and on the right, and the smaller one is the cheek extent 𝑒.

   ```math
   H = 3\,\mathrm{clamp}\!\left(\frac{a^*_s + 4}{8}\right) + 3\,\mathrm{clamp}\!\left(\frac{e}{0.3}\right) + 1.5\,\mathrm{clamp}\!\left(\frac{b^*_s}{5}\right)
   ```

   **Note** — **Why**: a real face is one blob of skin color from below the eyes to the cheeks, and skin has a red · yellow cast. Fake pairs from clothing folds · patterns · props often lose the skin blob right at cheek height, or their "skin" area is grey · bluish. **How it works**: everything is measured in face-frame coordinates (𝑢, 𝑣 in units of 𝑑), so the same places are looked at whatever the face size · tilt. $`a^*_s`$ · $`b^*_s`$ are the red · yellow cast of the reference skin, 𝑒 is how many eye distances wide the cheek skin continues, and the three are ramped to 0–1 and added with weights 3 · 3 · 1.5. The weights · threshold were chosen on 205 of 293 development pixiv pictures. **References**: this program's experiments (0.48 in 12)

   On 88 development pictures never used for choosing, faces found went 40 → 44 and fake faces 57 → 47 (neither significant; same direction as on the pictures used for choosing).
   On 120 posed synthetic pictures, whose skin is even and wide, pictures with a face found went 46 → 63 while fake faces also went 11 → 38 (hands · legs · one eye with a cheek take the full bonus, 0.48 in 12).
10. **Mirror agreement** (0.34): the picture is flipped left-right and 1–9 are done once more; among the faces of 9, only those that also have a face at the same place in 9 of the flipped picture
   (the flipped center mapped back by $`x \mapsto W - 1 - x`$, with the two centers less than $`\max(d, d')`$ apart) are used for names · character folders (position · score from the original picture).
   A real face is still a face when flipped, but fakes arising by chance from clothing folds · patterns · text often cross the threshold on only one side because of the asymmetry of the average patterns · lash band · eye refinement order.
   Marking the naming faces that appeared on only one side in pixiv pictures, 101 of 108 were fake (11). The faces of 7 (for background decisions) are kept as they are
   (using it for background decisions too increased the pictures losing character parts that fake faces had protected, 7.5). Face finding runs twice, so it takes that much longer (median processing time on 666 pictures 9.4 s → 10.8 s).
    - **Note** — **Why**: A real face is still a face when mirrored, but chance fakes pass the threshold on one side only. **How it works**: It is a mirror-consistency check: coordinates from the flipped picture are mapped back with $`x \mapsto W - 1 - x`$ and a face must be found at the same place. That 101 of 108 one-sided faces were fake is the evidence that the check removes almost only fakes. **References**: this program's experiments (11)

Face finding is done once regardless of the background. For pictures where the background was not searched or not found, transparent areas (alpha 0.02 or less) are treated as background and 8 is applied, for part names and character splitting.

### Returning swallowed characters

In pictures whose outline has the same color as the hair · background and cannot be seen, and whose hair · clothes are painted without lines, the scene background found by line density crosses the character boundary as it is.

1. **Swallowed faces**: among faces scoring 13 or more (all found faces regardless of the conditions of 8), those with more than 25% background in the face ellipse ($`u^2 + ((v - 0.2)/0.8)^2 \le 1`$) or the crown cell ($`\lvert u\rvert \le 0.8,\ -1.6 \le v \le -0.45`$)
   (measured with all pixels within $`1.7d`$ horizontally · vertically of the center).
   Real faces in the test pictures were at most 2% for both, and fake faces whose face · crown sat on background (background decorations) all scored 12.6 or less.
   - **Note** — **Why**: If the face ellipse or crown cell is covered by background, the scene background has swallowed the character. **How it works**: In face-frame coordinates the crown cell $`\lvert u\rvert \le 0.8,\ -1.6 \le v \le -0.45`$ is the hair above the eyes. A background share above 25% in either marks a swallowed face (real faces are at 2% or less). **References**: a rule set by this program
2. **Pieces**: the current background is split into pieces 𝑘 the same way as for attached character parts (crisp edge $`\Delta E \ge 20`$, lines).
3. **Rare color**: from the color distribution $`h_B`$ (Lab $`10 \times 16 \times 16 = 2560`$ bins) counted over the $`n_B`$ pixels of pieces touching the top · left · right borders, for each piece 𝑘 not touching the border,

   $`\displaystyle \nu_k=\sum_{p\in k}\mathrm{clip}_{[-4,4]}\ln\frac{1/2560}{(h_B(c_p)+1)/(n_B+2560)}`$

   The numerator is the uniform distribution and the denominator the border-side background distribution (Laplace smoothing), so it grows positive the rarer the color is in the border-side background compared with the uniform distribution.
   - **Note** — **Why**: A swallowed character piece has colors rare in the border background. For each piece, how rare its colors are there is measured. **How it works**: $`\ln\frac{1/2560}{(h_B + 1)/(n_B + 2560)}`$ is the log ratio of the uniform distribution to the Laplace-smoothed border distribution, positive for colors rarer than average in the border background. It is a sum, not a mean, so evidence accumulates with size. Pieces are split by the same $`\Delta E \ge 20`$ edges as for absorbed parts. **References**: [R51 Manning et al. 2008](../README.en.md#r51)
4. **Returning**: pieces with at least half of their area inside the head ellipse or body column (the same shape as the zone probability of face-based widening) of one of the swallowed faces,
   not touching the top · left · right borders, and with $`\nu_k > 0`$, plus the edge · line band on the piece side and the edge band on the character side (up to 3px), are returned to the character.
   Background gaps seen between hair and neck have the background color and remain.
   - **Note** — **Why**: Pieces inside the head ellipse or body column, not touching the border and of colors rare in the border background, are swallowed character. **How it works**: They are returned only when all three conditions hold (a conjunction), along with a 3px boundary band so no background rim remains. **References**: a rule set by this program
5. If swallowed faces still remain after returning (black hair of almost the same color as the background: no crisp edge), the crisp edge is lowered to $`\Delta E \ge 8`$ and 1–4 are done once more.
   If some still remain, it is lowered to $`\Delta E \ge 5`$ and the color bins of 3 are made finer, $`25 \times 64 \times 64 = 102400`$ bins with spacing 4 for all of $`L^*`$ · $`a^*`$ · $`b^*`$ (numerator · smoothing also with this bin count), and done once more (0.34).
   Black hair with $`\Delta E`$ 6–9 from the background is in the same bin as the background with 2560 bins and is not rare, but falls in a different bin with the fine bins.
   - **Note** — **Why**: Black hair almost the same color as the background has no $`\Delta E`$ 20 edge, so it is not split into its own piece. **How it works**: The threshold is lowered to 8 and then 5, going from coarse to fine. Shrinking the bin width from 10 · 16 to 4 puts $`\Delta E`$ 6–9 differences into different bins, so they count as rare. **References**: a rule set by this program
6. **Body-zone pieces** (before 1–5): if there is a face scoring 13 or more that was not swallowed, among the same pieces ($`\Delta E \ge 20`$), pieces with at least half of their area in the lower part of that face's body column
   ($`1 \le v \le 8`$, $`\lvert u\rvert \le 1.2 + 0.35 \cdot \max(v - 1.5, 0)`$), not touching the top · left · right borders, and with area at least 0.3% of the whole are considered.
   White clothes on a white background have the same color as the background, so the rarity condition of 3 is not used; only pieces whose color log-likelihood ratio between the character (pixels not currently background) distribution and the remaining background pieces' distribution
   (the same formula as $`\bar \ell_k`$ of attached character parts) is $`\bar \ell_k \ge -2`$ are returned.
   Background holes seen between skirt and sleeve ($`\bar \ell \approx -3.9`$) and text boxes next to the character (−2.1) remain, while white clothes · skirt pieces were −1.6 or more.
   - **Note** — **Why**: White clothes on a white background share the background color, so the rarity condition cannot be used. Instead the character and background distributions are compared and only pieces clearly on the background side are rejected. **How it works**: $`\bar\ell_k \ge -2`$ means a mean log-likelihood ratio of at least −2, i.e. the background side is not more than $`e^2 \approx 7.4`$ times as likely. Background holes are at −3.9 and white clothes at −1.6 or above, so they separate. **References**: [R51 Manning et al. 2008](../README.en.md#r51) · a rule set by this program
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
   - **Note** — **Why**: This stage is skipped when the background is nearly one color. **How it works**: The per-channel median of the samples is the representative color, and the share of samples within $`\Delta E < 10`$ of it is the flatness. **References**: [R7 CIE 2004](../README.en.md#r7)
1. It uses the same region graph as the color model (24-color regions, contact lengths $`o, l`$, color distributions). The two stages share the graph built once.
2. **Zone probability** (probability of being character) $`\pi(p)`$: for each face, at $`(u, v)`$ of the original resolution,

   $`\displaystyle \pi_f=\begin{cases}0.9 & -1.2\le v\le 8,\ |u|\le 1.2+0.35\max(v-1.5,\,0)\quad(\text{body})\\ 0.85 & (u/2.2)^2+((v+0.3)/2)^2\le 1\quad(\text{head})\\ 0.45 & \text{otherwise}\end{cases},\qquad \pi(p)=\max_f \pi_f(p)`$

   The region mean is $`\bar \pi_r`$. The log odds of the zone term are $`\ln(0.9/0.1) = 2.197,\ \ln(0.85/0.15) = 1.735,\ \ln(0.45/0.55) = -0.201`$.
   - **Note** — **Why**: When a face is present, the prior knowledge that the body and head areas below it are probably character is put in as a probability. **How it works**: Each place gets a prior probability (body 0.9, head 0.85, elsewhere 0.45), taking the largest over faces. It enters the energy as the log odds $`\ln(\pi/(1 - \pi))`$: by Bayes' rule, log posterior odds = log-likelihood ratio + log prior odds, so it adds directly to the color term (a log-likelihood ratio). The region graph (contact lengths 𝑜, 𝑙) is shared with the color model. **References**: [R25 Rother et al. 2004](../README.en.md#r25) · a rule set by this program
3. **First split**: character is the regions with $`\bar \pi_r \ge 0.8 \land \beta_r < 0.5`$ (head · body zones), background the regions with $`\beta_r > 0.5`$ (existing background). After that, it learns from the previous cut (character / everything else).
4. The **energy** and <mark>minimum cut</mark> (the same <mark>Dinic</mark> as the color model) are repeated 4 times, relearning the color distributions.

   $`\displaystyle \theta_r=\sum_{p\in r,\,known}\mathrm{clip}_{[-3,3]}\ln\frac{p_F(c_p)+10^{-6}}{p_B(c_p)+10^{-6}}+\sum_{p\in r}\ln\frac{\pi(p)}{1-\pi(p)}-2A_r\beta_r,\qquad w_{rq}=o\,\exp\!\left(-\frac{\Delta E_{rq}^2}{288}\right)+0.0375\,l`$
   - **Note** — **Why**: Starting from sure head and body areas and the existing background, color distributions are learned and the split is repeated by minimum cut together with the position prior. **How it works**: $`\theta_r`$ is the color log-likelihood ratio + the position log odds − $`2A_r\beta_r`$ (pulling existing background toward background). $`w_{rq}`$ uses the same Gaussian as the color model ($`2\cdot 12^2 = 288`$), and the four rounds alternate splitting and relearning distributions, as GrabCut's iterative estimation does. **References**: [R25 Rother et al. 2004](../README.en.md#r25) · [R24 Boykov · Jolly 2001](../README.en.md#r24) · [R27 Dinic 1970](../README.en.md#r27)

5. **Only sure places**: among regions that ended on the background side, those whose mean color term (per $`\mathrm{known}`$ pixel) is below −1, whose mean color term measured with the initial color distributions is also below −0.5 (0.42, below),
   and with $`\bar \pi_r \le 0.5`$ are candidates (excluding regions where returned character parts exceed half the area, and regions with $`\bar \varepsilon_r \ge 0.9`$).
   Starting from the existing background ($`\beta_r > 0.5`$), the pixels of regions connected into the candidates crossing only boundaries with $`o \ge 0.5(o + l)`$ are added to the background
   (excluding crisp line pixels and character parts returned earlier).
   The color term with the initial color distributions uses the distributions $`p^0_F, p^0_B`$ counted from the first split in 3 (the same color bins):
   $`\theta^0_r=\sum_{p\in r,\,known}\mathrm{clip}_{[-3,3]}\ln\frac{p^0_F(c_p)+10^{-4}}{p^0_B(c_p)+10^{-4}}`$, and the condition is $`\theta^0_r / k_r < -0.5`$ ($`k_r`$ is the number of $`\mathrm{known}`$ pixels in the region).
   The repetition in 4 keeps using $`10^{-6}`$. The distributions relearned over the repetitions pushed rarely seen colors to one side, so dark legs · clothes near the head · body zones that were on the character side at first often became candidates.
   - **Note** — **Why**: Distributions relearned over the rounds drift by pushing rare colors to one side, so only regions that are background-side under the initial distributions as well are taken (a conjunction of two judgments). **How it works**: $`\theta^0_r / k_r`$ is the mean per-pixel log-likelihood ratio under the initial distributions; below −0.5 the background side is more than $`e^{0.5} \approx 1.65`$ times as likely. Smoothing with $`10^{-4}`$, larger than $`10^{-6}`$, makes ratios for rare colors less extreme. $`o \ge 0.5(o + l)`$ means at least half the boundary touches without a line. **References**: [R25 Rother et al. 2004](../README.en.md#r25) · a rule set by this program

### Background seen between character parts (gaps)

Done after face-based widening. Only when the painted ($`\mathrm{known}`$) pixels of the background found so far are $`0.02N`$ or more,
and line pixels ($`\mathrm{lineMask}`$) are fewer than $`0.3 n_o`$ of the $`n_o`$ opaque ($`A > 0.02`$) non-background pixels (pictures where grain · halftone · dense hatching is picked up as lines are excluded because the bleeding of 4.6 below is large).

**Note** — **Why**: Pictures with little background paint or very many lines (particles, halftone, hatching) easily get gaps wrong, so they are skipped. **How it works**: Two thresholds: background paint area (2% of the picture) and line share (30% of opaque pixels). **References**: a rule set by this program

1. **Background representative color**: from the $`n_b`$ painted background pixels, one in every $`t = \max(1, \lfloor n_b / 20000\rfloor)`$ is taken in pixel order, the per-channel medians $`(m_L, m_a, m_b)`$ of the Lab of the color under lines (𝑈) are found,
   and the flatness $`\mathrm{flat}`$ (the share within $`\Delta E`$ 10 of the median) is measured with the same formula as 0 of face-based widening. If $`\mathrm{flat} < 0.6`$, it is not done (scene backgrounds have varied colors where they show through gaps too, so this rule cannot separate them).
2. **Candidates**: painted non-background pixels with almost the same color as the background representative color (excluding returned character parts) are split into 4-connected pieces 𝑟.

   $`\displaystyle (L_p-m_L)^2+(a_p-m_a)^2+(b_p-m_b)^2\le 5^2`$
   - **Note** — **Why**: Background seen between characters has the background color, so painted pixels very close to the representative background color are collected as candidates. **How it works**: The representative color is the per-channel Lab median of samples thinned to 20,000. Comparing the squared Lab distance with $`5^2`$ is $`\Delta E \le 5`$ (a small difference that looks like the same color) without the square root. **References**: [R7 CIE 2004](../README.en.md#r7)

3. **Piece conditions**: with the 8-neighbors outside the piece that are not candidates as the perimeter $`R_r`$, and the painted non-background pixels among them as $`R^c_r`$,

   $`\displaystyle 30\le A_r\le 0.02N,\qquad |R^c_r|\le 0.1\,|R_r|,\qquad \forall p\in r,\ \forall f:\ (u/2.2)^2+((v+0.3)/2)^2>1`$

   The perimeter must be almost only lines and background (white clothes · white hair touching other paint usually touch shadows · shading), and the piece must be outside the head ellipses of faces (faces used for background decisions) (whites of the eyes · teeth).
   - **Note** — **Why**: This separates character parts in the background color (white clothes, eye whites, teeth) from real gaps. **How it works**: Area from 30px to 2% of the picture, a share of the rim touching other paint $`|R^c_r| / |R_r| \le 0.1`$ (a rim of almost only lines and background), and outside the head ellipse of every face (∀𝑓). **References**: a rule set by this program
4. **Picture condition**: all pieces meeting the conditions are added to the background only when their total area is 5% or less of the number $`n_c`$ of painted character-side pixels.

   $`\displaystyle \sum_{r\ \text{meeting the conditions}} A_r\le 0.05\,n_c`$

   Pictures where the character itself has the background color, like white clothes on a white background or black-and-white line art filled with white, have a large sum and are filtered out. The two thresholds (0.05 · 0.02) and flatness 0.6 were set by looking one by one at the 161 pictures changed by a version that gathered pieces loosely (no sum limit, pieces 5%)
   (11). The pixels sent are remembered separately as a gap map and used for region · tone filling (4.6).
   - **Note** — **Why**: Per-piece conditions alone cannot reject pictures where the character itself is in the background color (white clothes on white), so a whole-picture condition is added. **How it works**: Only used when the matching pieces total at most 5% of the character's painted area $`n_c`$; a large total signals that the character itself is background-colored. **References**: this program's experiments (11)

### Rectangular background objects drawn with lines (0.43)

Done after the gaps. For every 4-connected component 𝑟 of painted pixels left on the character side (not background, lines or returned character parts), its area $`A_r`$ and bounding box $`w_r \times h_r`$ are measured.

1. **Rectangle**: it does not touch the border, $`w_r, h_r \ge \max(4, \mathrm{round}(0.015\max(W, H)))`$, $`0.97\,w_r h_r \le A_r \le 0.1N`$, all four corner pixels of the box belong to 𝑟,
   and the box center lies outside the head ellipse $`(u/2.2)^2 + ((v + 0.3)/2)^2 \le 1`$ and the body column ($`-1.2 \le v \le 8`$, $`\lvert u\rvert \le 1.2 + 0.35 \max(v - 1.5, 0)`$) of every face used for background decisions.
   - **Note** — **Why**: Window panes, shelves and books in a line-drawn room are almost full rectangles enclosed by lines. **How it works**: An area-to-bounding-box ratio (rectangularity) $`A_r / (w_r h_r) \ge 0.97`$ means nearly rectangular, and requiring all four corner pixels rules out rounded shapes. The size threshold is 1.5% of the long side (at least 4px). Being outside the head ellipse and body column keeps square patterns on the character untouched. **References**: [R14 Gonzalez · Woods 2018](../README.en.md#r14) · a rule set by this program
2. **Surroundings**: if at least half of the painted pixels in the ring around the box widened by $`d = 2\,\mathrm{lw} + 6`$px (lw is the line width), not counting other rectangle candidates, are background, it is accepted (several panes split by window frames leave each other out of their rings).
   Once something is accepted, the check is repeated until nothing more is accepted.
   - **Note** — **Why**: The surroundings confirm whether a rectangle is an object within the background. **How it works**: If at least half the painted pixels on a ring widened by twice the line width + 6px (the neighbors beyond the line) are background, it is an object in the background. Re-checking with accepted ones removed from the rings lets panes divided by window frames be accepted one after another. **References**: a rule set by this program
3. **Hidden panes**: accepted rectangles of one color (90% or more of their pixels within $`\Delta E \le 4`$ of the mean color) are grouped into a window when their mean colors differ by $`\Delta E < 4`$ and their boxes are within 𝑑 of each other.
   Inside the group's bounding box widened by the panes' mean width · height plus 𝑑, painted pixels within $`\Delta E \le 4`$ of the group's mean color (outside face zones and returned character parts) are also sent to the background (panes hidden by the character, no longer rectangles).
   - **Note** — **Why**: Panes that are no longer rectangles because the character hides part of them are sent to the background too when they belong to the same window. **How it works**: $`\Delta E \le 4`$ is a small difference that counts as the same paint (a just-noticeable difference in CIELAB is about 2.3). Same-colored rectangles are grouped, and same-colored pixels inside the group's box are sent to the background, catching hidden panes. **References**: [R7 CIE 2004](../README.en.md#r7) · [R8 Mahy et al. 1994](../README.en.md#r8)

Window panes · shelves · books of line-drawn rooms (synthetic pictures) are caught here. Being enclosed by lines, the scene background · color model · face-based widening do not take them, and with an almost one-color background face-based widening is not done either.
Only 1 of the 777 real pictures changed (0.43 in 12).

### Neural-network-assisted removal (0.49 · 0.50)

Done at the very end of background detection (after the rectangular background objects, when the setting "Neural-network assist" is on). For each color region 𝑟 still on the character side with an area of at least $`0.002N`$, two scores are computed.

1. **Statistical formula**: the region features $`x_{r,1}, \ldots, x_{r,45}`$ (log ratios of the average templates for color · position · face-relative coordinates, line · background shares of the surroundings, area, lightness spread and more: 40, plus 5 texture features) and an additive logit $`\ell_r`$ built from the first 40 are standardized and summed.

```math
s_r = b_0 + \sum_{j=1}^{46} b_j\,\frac{F_{r,j} - \mu_j}{\sigma_j},\qquad F_r = (\ell_r, x_{r,1}, \ldots, x_{r,45})
```

   - **Note** — **Why**: the color · position · surroundings · texture of a single region are weak cues to whether it belongs to the background; none separates on its own, so several are weighted and summed. **How it works**: each feature is standardized by its mean $`\mu_j`$ and standard deviation $`\sigma_j`$, the weights $`b_j`$ are fitted by <mark>logistic regression</mark> (regularization $`\lambda = 30`$), and $`s_r`$ is the "log-odds of being background". The threshold 0.358 is the value at which 80% of the removed area is background on the development region ground truth. **References**: [R69 Cox 1958](../README.en.md#r69)
2. **Texture features**: a structure tensor is built from the Sobel gradients $`I_x, I_y`$ of the lightness $`I = L^*/100`$ and pooled with a $`\sigma = 2`$ Gaussian $`G_\sigma`$.

```math
J_{ab} = G_\sigma \ast (I_a I_b),\qquad c = \frac{\sqrt{(J_{xx} - J_{yy})^2 + 4J_{xy}^2}}{J_{xx} + J_{yy}} = \frac{\lambda_1 - \lambda_2}{\lambda_1 + \lambda_2},\qquad \mathrm{coh}_r = \frac{\sum_{p \in r} c(p)\,(J_{xx} + J_{yy})(p)}{\sum_{p \in r} (J_{xx} + J_{yy})(p)}
```

   The other four are the mean gradient strength $`\sqrt{I_x^2 + I_y^2}`$, the mean local lightness standard deviation ($`\sigma = 2`$), the share of pixels with gradient above 0.3, and the standard deviation of the region's lightness.
   - **Note** — **Why**: hair flows in fine strands in one direction, while sky · walls · blurred backgrounds have no strands or scattered directions. **How it works**: the two eigenvalues $`\lambda_1 \ge \lambda_2`$ of the structure tensor show how much the surrounding gradients gather in one direction; $`c`$ is 1 for strands in one direction and 0 for no direction. Averaging with the tensor energy $`J_{xx} + J_{yy}`$ as weight barely counts the noise directions of flat places. The texture features alone give hair vs background AUC 0.78, so they are not used on their own but inside the formula. **References**: [R89 Bigün · Granlund 1987](../README.en.md#r89)
3. **Neural network**: seven planes of the picture downscaled by area averaging to a long side of 256 (R · G · B · background found so far · dark-part protection · lines · face zones), scaled to $`[-0.5, 0.5]`$, give a character logit $`z`$ at half resolution.
   The face-zone plane is the maximum over faces of $`\max\bigl(0,\ 1 - \sqrt{(u/1.3)^2 + ((v + 0.2)/1.5)^2}\,/\,2.5\bigr)`$ in face-frame coordinates $`(u, v)`$.
   The structure is three levels of two 3×3 convolutions (ReLU) each (8 · 16 · 32 channels, 2×2 averaging between levels), dilated 2 · 4 · 8 convolutions at the deepest level (48 channels), two levels that upsample 2× and join the same-size level, and a final 1×1 convolution (109,073 weights, about 240 million multiply-adds for a 4:3 picture).
   Binary cross-entropy against the ground-truth character share on synthetic pictures and the cells covered by region labels on development pictures was minimized with <mark>Adam</mark> (real-picture cells weighted 8, 15 epochs).

```math
\bar z_r = \frac{1}{\lvert r\rvert}\sum_{p \in r} z(p),\qquad p_r = \sigma\!\left(1.148\,\frac{s_r - 0.059}{1.492} - 0.466\,\frac{\bar z_r + 0.095}{1.662} + 0.055\right),\qquad r \text{ to background} \quad\text{if}\quad p_r > 0.8
```

   Line pixels are not changed (the later line clean-up rule decides them), and background is never returned to the character.
   - **Note** — **Why**: rules that remove more of the remaining background easily remove the character by mistake, and losing the character is much worse than leaving background. Neither the formula alone nor one formula mixing in the network score reached 80% background in the removed area. **How it works**: the formula looks at one region's color · position · texture, the network at the shape of the whole downscaled picture. The less their mistakes overlap, the smaller the chance that both are wrong together, so 0.49 removed only when both said background ($`s_r \ge 0.358 \land \bar z_r < -1.25`$), raising precision (80.4%, removing 17.6%). 0.50 combines the two scores in one two-input logistic formula, so a very sure judge can remove even when the other is a little less sure. On nested out-of-fold scores, where the formula, the combiner and the threshold never see the outer fold, the background share of the removed area rose from 76% (the 0.49 rule) to 90% while the amount removed stayed similar (28% → 27%). Like <mark>U-Net</mark>, the network shrinks and grows while joining same-size levels so it keeps positions, and the dilated convolutions at the deepest level see wide surroundings. The combiner coefficients are a <mark>logistic regression</mark> fitted on the out-of-fold scores of both judges, and the threshold 0.8 minimizes the area-weighted loss counting character loss 3×. The network weights are the same as in 0.49. **References**: [R86 Ronneberger et al. 2015](../README.en.md#r86) · [R87 Kingma · Ba 2015](../README.en.md#r87) · [R88 Yu · Koltun 2016](../README.en.md#r88) · a rule set by this program

The training and inference code was written from scratch for this program (training with numpy matrix operations, inference in plain JS). The weights are stored as float32 inside the app file, and inference uses only additions · multiplications · maxima · averages. Evidence and test results are in 0.49 · 0.50 in 12.

### Outer glow

A saturated, bright band around the character (neon glow, fluorescent outline) is taken out separately.

It is looked at only in pictures whose background is 2–95% of the whole.

1. **Band candidates**: painted ($`\mathrm{known}`$, non-line) pixels touching the background with 4-neighbors are at depth 1, and pixels reached toward the character within $`D = \max(12, \mathrm{round}(0.025\cdot \max(W, H)))`$ steps without crossing lines (4-neighbor <mark>breadth-first search</mark>; the depth is the number of steps).
   - **Note** — **Why**: A glow is a band around the character, so only a fixed depth from the background boundary into the character is examined. **How it works**: Step counts of a 4-neighbor <mark>breadth-first search</mark> give the depth (Manhattan distance). 𝐷 is 2.5% of the long side (at least 12px), so it scales with the picture. **References**: [R14 Gonzalez · Woods 2018](../README.en.md#r14)
2. **Decision**: a pixel is fluorescent if $`L^* > 60`$ and $`C^* > 45`$ (in 𝑈, with the color under lines restored). With $`f_r`$ fluorescent among $`n_r`$ band candidates and $`f_i`$ fluorescent among $`n_i`$ pixels inside the character (<mark>chamfer distance</mark> to background $`> 2D`$),
   it needs $`f_r \ge 0.18 n_r,\ f_r / n_r \ge 4 f_i / n_i,\ f_r \ge 0.002N`$.
   - **Note** — **Why**: To remove a glow, it must be established that the fluorescent band lies only around the character (that the character is not wearing fluorescent clothes). **How it works**: $`C^* = \sqrt{a^{*2} + b^{*2}}`$ is Lab chroma, so together with $`L^* > 60`$ it marks bright, vivid colors as fluorescent. The band must be at least 18% fluorescent and at least 4 times the share inside the character, so the fluorescence is only around it. The <mark>chamfer distance</mark> is an approximate Euclidean distance computed in two passes (3-4 weights). **References**: [R7 CIE 2004](../README.en.md#r7) · [R21 Borgefors 1986](../README.en.md#r21)
3. **Glow colors**: fluorescent pixels of the band candidates are counted in 16×16 $`(a^*, b^*)`$ bins ($`\lfloor(a^* + 128)/16\rfloor,\ \lfloor(b^* + 128)/16\rfloor`$); bins with $`0.005 f_r`$ or more.
   - **Note** — **Why**: This picks the glow's hues so growth continues only through pixels of the same hue. **How it works**: In a 2-D histogram of the chroma plane $`(a^*, b^*)`$ (steps of 16, 16×16 bins), bins holding at least 0.5% of the fluorescent pixels are glow colors. Ignoring lightness puts the glow's bright core and fading edge in the same bins. **References**: [R84 Swain · Ballard 1991](../README.en.md#r84)
4. **Glow**: widened with 4-neighbors from the fluorescent pixels of the band candidates.
   - Character side: among pixels with depth to background + <mark>chamfer distance</mark> to the nearest line $`\le D`$ (a band squeezed between background and outline), glow colors ($`L^* > 45,\ C^* > 25`$, glow bin) or white cores ($`L^* > 80`$)
   - Background side: glow colors with <mark>chamfer distance</mark> to the character $`\le D`$
5. **Surrounding**: used only if 35% or more of the background pixels touching the character (<mark>chamfer distance</mark> to the character $`\le 1.5`$) are within 3px of the glow (square dilation of radius 3).
   - **Note** — **Why**: Growing from fluorescent pixels captures the whole glow, but on the character side only up to the band between background and outline, and on the background side only near the character. Finally it checks that the glow really surrounds the character. **How it works**: "Depth to background + distance to a line $`\le D`$" says the pixel lies in a band at most 𝐷 wide between background and outline. A radius-3 square dilation marks pixels within 3px of the glow, and at least 35% of the background touching the character must be in it for the glow to count as surrounding. **References**: [R21 Borgefors 1986](../README.en.md#r21) · [R15 Soille 2003](../README.en.md#r15)
6. Glow pixels are moved to the background side and put in the "Outer glow" layer (normal, opaque) with their original colors. The background layer color below them is inpainted from the rest of the background.
   Places the user returned to the character and character parts returned from the background are excluded.

### Background effects

Non-background ($`A > 0.02`$) 4-connected pieces with area below $`0.015N`$ are background-effect candidates (excluding pieces containing returned character parts · places the user returned to the character).
The background color below them $`U^{bg}`$ is inpainted from the rest of the background (skipping other character pixels); the background layer gets $`\mathrm{base}_c = \min(U_c, U^{bg}_c)`$ ($`U^{bg}_c`$ at outer glow places),
and the background-effect layer gets (excluding outer glow places), when $`U_c > \mathrm{base}_c + 1.2/255`$ and $`\mathrm{base}_c < 0.9999`$, the screen value $`S_c = \mathrm{clamp}(1 - (1 - U_c)/(1 - \mathrm{base}_c))`$ (saved with the minimum alpha of 4.12).

**Note** — **Why**: Separating small light or sparkle effects over the background into their own screen layer keeps the effects when the background is edited. **How it works**: Screen compositing is $`1 - (1 - a)(1 - b)`$, so solving for the 𝑆 that gives 𝑈 when screened over base yields $`S = 1 - (1 - U)/(1 - \mathrm{base})`$. Setting $`\mathrm{base} = \min(U, U^{bg})`$ keeps 𝑆 non-negative. Division is unstable as base nears 1, so only base below 0.9999 is used, and only pixels brighter by more than 1.2/255 to skip 8-bit noise. $`U^{bg}`$ is inpainted from the surrounding background. **References**: [R3 ISO 32000-1 2008](../README.en.md#r3) · [R20 Telea 2004](../README.en.md#r20)

### Removing lines in the background

For each line-connected piece:

- Removed if 50% or more of the piece is inside the background.
- When 85% or more of its non-line 4-neighbors (outside $`\mathrm{inMask}`$) are background: removed if it is more than $`\max(10, \mathrm{round}(20s))`$ steps away from the character (non-background $`\mathrm{known}`$), if it is a small piece under 0.5% of all line pixels,
  or if the $`\Delta E`$ between the line's original mean color and the mean color of the neighboring background (𝑈 of touching background pixels) is $`< 15`$.
  - **Note** — **Why**: Lines that depict the background belong in the background picture, not the character line layer. **How it works**: Lines far from the character (beyond $`\max(10, \mathrm{round}(20s))`$ steps, a length scaled by the size ratio 𝑠), small pieces, or lines close in color to the adjacent background ($`\Delta E < 15`$) are taken as background lines. **References**: [R7 CIE 2004](../README.en.md#r7) · a rule set by this program
- Faint (non-crisp) line pixels absorbed into the background are removed per pixel.

Removed line pixels are restored to their original colors and left in the background picture.

---

[← README](../README.en.md#4-algorithms-and-formulas) · Next: [4.6 Regions and materials](4-3-regions-layers.en.md)
