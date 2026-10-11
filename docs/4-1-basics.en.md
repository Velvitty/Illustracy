# Illustracy — 4. Algorithms and formulas (1/4): Notation · color spaces · basic operations · line art

[← README](../README.en.md#4-algorithms-and-formulas) · Section 4 **1** · [2](4-2-background.en.md) · [3](4-3-regions-layers.en.md) · [4](4-4-rough-psd-tools.en.md) · [한국어](4-1-basics.md)

---

## 4.0 Notation

- <mark>Names highlighted in yellow</mark> are the statistical formulas · algorithms used in this document (<mark>Zhang–Suen thinning</mark>, <mark>Wilson score interval</mark>, <mark>Chi-square test of independence</mark> and others). The definitions of the statistics used for verification are collected in 11.1.
- Pixel values are sRGB values in 0–1 (8-bit value divided by 255). The original is 𝑂, the alpha 𝐴, the restored color under lines 𝑈, and the channel $`c \in \lbrace R, G, B\rbrace`$.
  - **Note** — **Why**: The same formula is repeated for each channel, so one subscript 𝑐 stands for all three. **How it works**: The basis is the 0–1 value of the 8-bit sRGB file value divided by 255, so every formula maps directly onto the values stored in the picture file. **References**: [R6 IEC 1999](../README.en.md#r6)
- Brightness is $`\mathrm{lum}(r, g, b) = 0.299r + 0.587g + 0.114b`$.
  The brightness used for finding lines is the brightness of the color laid on white, $`L = \mathrm{lum}(A\cdot O_R + 1 - A, A\cdot O_G + 1 - A, A\cdot O_B + 1 - A)`$.
  - **Note** — **Why**: Finding lines or comparing which color is darker needs the three channels reduced to one lightness. Transparent pixels are replaced by the color they show over white paper, so transparent areas are not taken as black lines. **How it works**: The eye is most sensitive to green and least to blue, so the channels are summed with the television luma weights 0.299 · 0.587 · 0.114 (they sum to 1, so white is 1). Compositing over white is the standard over formula $`A\cdot O + (1 - A)\cdot 1`$ per channel. **References**: [R9 ITU-R BT.601](../README.en.md#r9) · [R1 Porter · Duff 1984](../README.en.md#r1)
- **Processing resolution**: for the long-side limit 𝑀 (default 2048, 0 means original size), $`k = \min(1, M / \max(w_0, h_0))`$, $`W = \max(1, \mathrm{round}(k\cdot w_0))`$, $`H = \max(1, \mathrm{round}(k\cdot h_0))`$,
  using the browser's high-quality downscaling. $`N = W\cdot H`$. If the limit is 0 and the original exceeds 16 million pixels, a warning is shown.
  - **Note** — **Why**: The work grows with the pixel count, so large pictures are reduced to a fixed long side to bound time and memory. Small pictures are not enlarged (𝑘 ≤ 1). **How it works**: Width and height are multiplied by the same 𝑘 to keep the aspect ratio, rounded, and kept at least 1px. 𝑁 is later the denominator of area shares (e.g. 0.1% of the picture). **References**: [R14 Gonzalez · Woods 2018](../README.en.md#r14) · a rule set by this program
- **Transparent picture**: if more than $`0.001N`$ pixels have $`A < 0.98`$, the picture is treated as transparent. Pixels with $`A \le 0.02`$ are empty.
  - **Note** — **Why**: In a PNG with a transparent background the transparent area itself is the background, so background finding works differently. A share threshold keeps a few anti-aliased edge pixels from making a picture count as transparent. **How it works**: A picture counts as transparent only when semi-transparent pixels exceed 0.1% of it. Alpha 0.02 or less is 5 or less in 8 bits, an invisible, practically empty pixel. **References**: a rule set by this program
- $`s = \max(W, H) / 1000`$ is the scale factor for picture size (multiplied into length reference values).
  - **Note** — **Why**: Length thresholds such as line width or blur radius were set on pictures with a 1000px long side, so on other sizes they must be scaled by the same ratio to measure the same shapes. **How it works**: Lengths scale in proportion to picture size, so base values are multiplied by 𝑠, and area thresholds by $`s^2`$. **References**: a rule set by this program
- $`\mathrm{clamp}(x) = \min(1, \max(0, x))`$, and $`\mathrm{smoothstep}(a, b, x)`$ is $`t^2(3 - 2t)`$ for $`t = \mathrm{clamp}((x - a)/(b - a))`$ (a descending curve when $`a > b`$).
  - **Note** — **Why**: Computed alphas and ratios outside 0–1 cannot be stored and have no meaning, so they are clipped. A hard threshold makes results jump near it, so a weight that passes smoothly from 0 to 1 is also needed. **How it works**: smoothstep is the cubic Hermite polynomial $`t^2(3 - 2t) = 3t^2 - 2t^3`$ with zero slope at both ends: 0 at 𝑡 = 0, 1 at 𝑡 = 1, slope 1.5 in the middle, so joining two thresholds with it changes the weight without jumps. **References**: [R47 Ebert et al. 2003](../README.en.md#r47)
- In block formulas, an interval $`[a, b]`$ written under $`\mathrm{clip}`$ means the value is clipped to that interval: $`\min(b, \max(a, x))`$.
  - **Note** — **Why**: Values such as log-likelihood ratios can become huge in sparsely sampled bins, so they are bounded above and below to keep one or two pixels from deciding the outcome. **How it works**: It is the same clipping as clamp, widened to an arbitrary interval $`[a, b]`$. **References**: a rule set by this program
- Color difference $`\Delta E`$ is <mark>CIE76</mark> (<mark>Euclidean distance</mark> in Lab). Hue angle difference is $`\Delta h = \min(d, 360^\circ - d)`$ for $`d = \lvert h_1 - h_2\rvert \bmod 360^\circ`$.
  - **Note** — **Why**: How different two colors look to a person must be compared as one number. Hue is an angle, so 350° and 10° must differ by 20°, not 340°. **How it works**: CIELAB is built so that equal distances are roughly equal perceived differences, so the Euclidean distance $`\sqrt{\Delta L^{*2} + \Delta a^{*2} + \Delta b^{*2}}`$ (CIE76) is used as the color difference. The angle difference is the shorter way around the circle. **References**: [R7 CIE 2004](../README.en.md#r7) · [R8 Mahy et al. 1994](../README.en.md#r8)
- The percentage sliders in the settings (line sensitivity 𝜂, base color merge strength 𝑚, shadow threshold $`\eta_s`$) become 0–1 as $`\text{value}/100`$.
  - **Note** — **Why**: The on-screen sliders are integers 0–100, but the threshold formulas are simpler with ratios 0–1. **How it works**: Dividing by 100 gives a unitless ratio, and each threshold moves as a linear function of it (e.g. $`t_{high}`$ in 4.3, the shadow threshold in 4.7). **References**: a rule set by this program
- $`\mathrm{round}`$ is the nearest integer (0.5 rounds up); $`\lfloor x \rfloor`$ · $`\lceil x \rceil`$ are floor · ceiling.
  - **Note** — **Why**: Pixel coordinates, bin indices and 8-bit values must be integers, so one fixed rule for turning reals into integers keeps results identical every time. **How it works**: Rounding sends 0.5 up (JavaScript `Math.round`); floor and ceiling are the usual functions. **References**: a rule set by this program

## 4.1 Color space

sRGB is linearized, then converted to Lab via XYZ (D65).

```math
C_{lin}=\begin{cases}C/12.92 & C\le 0.04045\\ \left(\frac{C+0.055}{1.055}\right)^{2.4} & \text{otherwise}\end{cases}
\qquad
L^*=116f(Y)-16,\; a^*=500\,(f(X/X_n)-f(Y)),\; b^*=200\,(f(Y)-f(Z/Z_n))
```

**Note** — **Why**: sRGB values carry the display gamma, so they are not proportional to the amount of light. To measure color differences as people perceive them, the values are first returned to light amounts (linear values) and then taken through XYZ to Lab. **How it works**: The sRGB transfer function is inverted: a straight line (divide by 12.92) up to 0.04045, a 2.4-power curve above. Lab's $`L^*`$ follows the cube root of $`Y`$ to imitate perceived lightness, and $`a^*`$ · $`b^*`$ are the red–green and yellow–blue opponent axes. **References**: [R6 IEC 1999](../README.en.md#r6) · [R7 CIE 2004](../README.en.md#r7)

```math
f(t)=\begin{cases}t^{1/3} & t>0.008856\\ 7.787\,t+16/116 & \text{otherwise}\end{cases}
```

**Note** — **Why**: The cube root has infinite slope near 0, so used as is it would blow up small noise in very dark colors. **How it works**: For $`t \le (6/29)^3 pprox 0.008856`$ it is replaced by the line $`7.787t + 16/116`$, which meets the cube root in value and slope (the CIE definition). **References**: [R7 CIE 2004](../README.en.md#r7)

From linear RGB to XYZ the sRGB (D65) matrix is used, with reference white $`X_n = 0.95047,\ Y_n = 1,\ Z_n = 1.08883`$.

**Note** — **Why**: Lab measures "how light and what color compared with white", so it needs a reference white. **How it works**: These are the XYZ values of the sRGB white, the D65 illuminant, normalized to $`Y_n = 1`$. **References**: [R7 CIE 2004](../README.en.md#r7) · [R6 IEC 1999](../README.en.md#r6)

```math
\begin{pmatrix}X\\Y\\Z\end{pmatrix}=
\begin{pmatrix}0.4124564&0.3575761&0.1804375\\0.2126729&0.7151522&0.0721750\\0.0193339&0.1191920&0.9503041\end{pmatrix}
\begin{pmatrix}R_{lin}\\G_{lin}\\B_{lin}\end{pmatrix}
```

**Note** — **Why**: The three linear RGB primaries have fixed positions in XYZ, so one 3×3 matrix converts between them. **How it works**: The columns are the XYZ of the sRGB red · green · blue primaries (white point D65), and the middle row (𝑌) holds the luminance weights 0.2126 · 0.7152 · 0.0722. **References**: [R6 IEC 1999](../README.en.md#r6)

Linearization is precomputed as a 256-entry table of 8-bit values (𝐶 into bin $`\mathrm{round}(255C)`$). Chroma $`C^* = \sqrt{a^{*2} + b^{*2}}`$, hue angle $`h = \mathrm{atan2}(b^*, a^*)`$ (in degrees).

**Note** — **Why**: Rules that separate achromatic materials or check whether a shadow's hue is close to the lit side need chroma and hue separately. Computing powers per pixel would be slow. **How it works**: These are polar coordinates in the $`(a^*, b^*)`$ plane: the distance from the origin is chroma $`C^*`$ and the angle is hue ℎ. An 8-bit input has only 256 values, so the linearization is precomputed in a table. **References**: [R7 CIE 2004](../README.en.md#r7) · [R10 Fairchild 2013](../README.en.md#r10)

**Lab → sRGB** (when recovering, from a <mark>k-means</mark> center, the color of a tone that has no samples):

```math
f_y=\frac{L^*+16}{116},\ f_x=f_y+\frac{a^*}{500},\ f_z=f_y-\frac{b^*}{200},\qquad
f^{-1}(t)=\begin{cases}t^3 & t^3>0.008856\\ (t-16/116)/7.787 & \text{otherwise}\end{cases}
```

**Note** — **Why**: A k-means center is a Lab value, so painting the color of a tone with no pixels into a layer requires converting back to sRGB. **How it works**: The forward formulas are inverted: $`f(Y)`$ comes from $`L^*`$, adding or subtracting $`a^*`$ · $`b^*`$ gives $`f(X/X_n)`$ · $`f(Z/Z_n)`$, and cubing (or inverting the linear part) undoes 𝑓. **References**: [R7 CIE 2004](../README.en.md#r7)

```math
\begin{pmatrix}R_{lin}\\G_{lin}\\B_{lin}\end{pmatrix}=
\begin{pmatrix}3.2404542&-1.5371385&-0.4985314\\-0.9692660&1.8760108&0.0415560\\0.0556434&-0.2040259&1.0572252\end{pmatrix}
\begin{pmatrix}X_n f^{-1}(f_x)\\ f^{-1}(f_y)\\ Z_n f^{-1}(f_z)\end{pmatrix},\qquad
C=\begin{cases}12.92\,C_{lin} & C_{lin}\le 0.0031308\\ 1.055\,C_{lin}^{1/2.4}-0.055 & \text{otherwise}\end{cases}
```

**Note** — **Why**: Going from XYZ to linear RGB and then to gamma-encoded sRGB gives screen and file values. **How it works**: This is the inverse of the forward matrix followed by the sRGB encoding gamma (a line with factor 12.92 up to 0.0031308, a 1/2.4 power above). Values are clipped to 0–1 before the gamma because some Lab points lie outside the sRGB gamut. **References**: [R6 IEC 1999](../README.en.md#r6) · [R35 Strang 2016](../README.en.md#r35)

($`C_{lin}`$ is clipped to 0–1 before applying the gamma.) The color comparison of the manual correction tools (4.17) uses Lab from the same formulas.

## 4.2 Basic operations

- **Dilation / erosion** (square of radius 𝑟): $`\mathrm{dilate}_r(f)(x, y) = \max f(x + i, y + j)`$ (the maximum over $`\lvert i \rvert, \lvert j \rvert \le r`$; erosion takes the minimum; outside the picture is dropped from the window).
  The 1-D sliding max / min split into rows and columns is computed with a **monotonic deque**, $`O(1)`$ per pixel. **Closing** is dilation then erosion; **opening** is erosion then dilation.
  - **Note** — **Why**: The closing that finds lines, the opening that removes small pieces, and widening · narrowing are all built from these two operations. They must stay fast for large radii to be usable on large pictures. **How it works**: The maximum over a square window equals the row-window maximum followed by the column-window maximum, so two 1-D passes suffice. A 1-D sliding maximum keeps candidate positions with decreasing values in a deque; sliding the window drops expired ones from the front and smaller ones from the back, so each element enters and leaves once, a constant cost per element. **References**: [R15 Soille 2003](../README.en.md#r15) · [R16 Lemire 2006](../README.en.md#r16)
- **<mark>Gaussian blur</mark>**: approximated by repeating a box blur of radius 𝑟 (width $`2r + 1`$, repeating edge values outside the picture) three times horizontally and vertically.
  One box pass has variance $`((2r + 1)^2 - 1)/12 = r(r + 1)/3`$, so three passes give $`r(r + 1) = \sigma^2`$, which solves to
  $`r = \max(1, \mathrm{round}((\sqrt{4\sigma^2 + 1} - 1)/2))`$. If $`\sigma < 0.3`$, there is no blur.
  - **Note** — **Why**: Wide blurs such as line density and gradient envelopes are frequent, so a Gaussian approximation whose cost does not depend on the radius is needed. **How it works**: A uniform distribution of width $`n = 2r + 1`$ has variance $`(n^2 - 1)/12`$, and cascaded independent blurs add variances. Three box blurs approach a Gaussian by the central limit theorem with variance $`r(r + 1)`$, so 𝑟 is the rounded positive root of $`r^2 + r - \sigma^2 = 0`$. A box blur costs a constant per pixel with running sums. **References**: [R17 Wells 1986](../README.en.md#r17) · [R14 Gonzalez · Woods 2018](../README.en.md#r14)
- **Inpainting**: unknown pixels are visited in order of distance from known pixels (outer rings first) and filled with the average of the 8-neighbors already settled one ring further in.

  $`\displaystyle U(p)=\frac1{|\mathcal N_p|}\sum_{q\in\mathcal N_p}U(q),\qquad \mathcal N_p=\lbrace q\in 8\text{-nbr}(p):\ \text{ring}(q)<\text{ring}(p)\rbrace`$
  - **Note** — **Why**: The color painted under a line must be known to solve for the line's alpha and the base color. **How it works**: Layers are filled inward one at a time starting from the known area, averaging only neighbors from the layer just outside, so colors continue smoothly from both sides of the line. It is a simplified variant of Telea's fast-marching inpainting (fill in distance order) with an unweighted mean. **References**: [R20 Telea 2004](../README.en.md#r20)

- **Label filling**: unlabeled pixels are visited in order of distance and filled by a majority vote of the settled 8-neighbor labels (4-neighbors get 2 votes, diagonals 1).
- **Connected component**: a lump of equal values connected by 4-neighbors. The **perimeter** is the sum, over the pixels of the component, of the number of 4-neighbor sides that belong to another component (or lie outside the picture).
- **Distance transform** (<mark>chamfer</mark>): two sweeps (top → bottom, bottom → top) with weight 1 for a horizontal · vertical step and $`\sqrt 2`$ for a diagonal step approximate the distance to the nearest marked pixel.

  $`\displaystyle d(p)=\min\big(d(p),\ d(q)+w_{pq}\big),\qquad w_{pq}\in\lbrace1,\sqrt2\rbrace`$

  Where it says "within so many steps", it means the number of steps of a 4-neighbor <mark>breadth-first search</mark> (<mark>Manhattan distance</mark>).
  - **Note** — **Why**: Distance to lines, width (twice the distance at the center line) and widening · narrowing need Euclidean distances, which are expensive to compute exactly. **How it works**: Two raster passes (forward and backward) compare each pixel with neighbors' distances plus one step (1 horizontally · vertically, √2 diagonally), a dynamic program. Looking only at 3×3 neighbors, it approximates the Euclidean distance within about 8%. **References**: [R21 Borgefors 1986](../README.en.md#r21)
- **<mark>k-means</mark>** (squared Lab distance): $`M = \min(n, M_\max)`$ samples are drawn (with replacement if $`n > M_\max`$); with **<mark>k-means++</mark>** the first center is uniform and each next center is drawn with probability proportional to the squared distance $`D(x)^2`$ to the nearest center so far.
  Assignment → mean update runs up to 18 times, stopping from the 4th iteration on when fewer than $`0.001M`$ samples change assignment. An empty cluster is moved to the farthest sample.
  $`M_\max`$ is 50000 for region splitting, 40000 for the region graph of the color model, and 6000 for tones per material.
  - **Note** — **Why**: Colors are grouped into a few representative colors to split regions · tones. Capping the sample count bounds the time regardless of picture size. **How it works**: Lloyd's algorithm assigns each sample to its nearest center and moves each center to the mean of its samples, repeatedly lowering the sum of squared distances. k-means++ picks samples farther from the chosen centers with probability proportional to $`D(x)^2`$, spreading the first centers so the expected error is within $`O(\log k)`$ of optimal. Distances are taken in perceptual Lab. **References**: [R22 Lloyd 1982](../README.en.md#r22) · [R23 Arthur · Vassilvitskii 2007](../README.en.md#r23) · [R7 CIE 2004](../README.en.md#r7)
- **Random numbers**: fixed-seed <mark>mulberry32</mark> so results are the same every time (main computation 12345, region graph of the color model · face stage 777, rough 20261011). With 32-bit integer arithmetic,
  $`s \gets s + \mathtt{0x6D2B79F5}`$, $`t = (s \oplus s \gg 15) \cdot(s \mathbin{\vert} 1)`$, $`t \gets t \oplus(t + (t \oplus t \gg 7) \cdot(t \mathbin{\vert} 61))`$, random number $`= (t \oplus t \gg 14)/2^{32}`$ (≫ is the unsigned right shift).
  - **Note** — **Why**: Validation by byte comparison requires the same result for the same picture and settings, so a pseudorandom generator with fixed seeds is needed. **How it works**: An odd constant is added to a 32-bit state (a Weyl sequence) and the bits are mixed by shifts · XOR · multiplication into a uniform 32-bit number. Each stage has its own seed so one stage's random draws never spill into another. **References**: [R48 Ettinger 2017](../README.en.md#r48)
- **Value noise** (pencil grain of the rough): a random number 𝑔 in $`[-1, 1]`$ at each grid point with spacing $`\mathrm{cell}`$, blended within a grid cell with $`s_x = \mathrm{smoothstep}(0, 1, t_x)`$, $`s_y = \mathrm{smoothstep}(0, 1, t_y)`$.

  $`\displaystyle n(x,y)=\big(g_{00}+(g_{10}-g_{00})s_x\big)(1-s_y)+\big(g_{01}+(g_{11}-g_{01})s_x\big)s_y`$
  - **Note** — **Why**: Pencil grain and the warp of the rough composition need random values that change smoothly; drawing a new value per pixel would sizzle. **How it works**: Random values sit only on grid points, and inside each cell a bilinear interpolation weighted by smoothstep keeps value and slope continuous across cell borders (value noise). **References**: [R47 Ebert et al. 2003](../README.en.md#r47)

- **<mark>Bilinear interpolation</mark>**: with $`x_0 = \lfloor x\rfloor,\ t_x = x - x_0`$ (same vertically), $`f = f_{00}(1 - t_x)(1 - t_y) + f_{10}t_x(1 - t_y) + f_{01}(1 - t_x)t_y + f_{11}t_x t_y`$.
  - **Note** — **Why**: Values must be read at non-integer coordinates of scaled or rotated grids (face-frame samples, enlarging a background found at reduced size). **How it works**: The four neighboring pixels are mixed with weights equal to the opposite cell areas; the weights sum to 1 and are linear in each direction. **References**: [R14 Gonzalez · Woods 2018](../README.en.md#r14)
- **Resizing** (for face finding, horizontal · vertical separately): if the ratio $`r = n / m`$ (original cells / new cells) is at least 1, the **area average** of the original interval $`[ir, (i + 1)r)`$ covered by new cell 𝑖;
  if below 1, **<mark>linear interpolation</mark>** at $`x = (i + 0.5)r - 0.5`$.
  - **Note** — **Why**: Face finding works on the picture scaled to an 800px long side. Picking samples when shrinking would make thin lines vanish or staircase. **How it works**: Shrinking averages the source interval covered by each new cell (a box filter), and enlarging interpolates linearly at the pixel-center-aligned coordinate $`(i + 0.5)r - 0.5`$. **References**: [R14 Gonzalez · Woods 2018](../README.en.md#r14)
- **Percentile**: for ascending $`s_0 \dots s_{n-1}`$ with $`x = (n - 1)q / 100,\ k = \lfloor x\rfloor`$, the value is $`s_k + (s_{k + 1} - s_k)(x - k)`$ (the median is $`q = 50`$). The **standard deviation** is the population standard deviation divided by 𝑛.
  - **Note** — **Why**: Thresholds measured per picture (such as the median line density) need representative values that outliers do not move. **How it works**: This is the sample quantile interpolating linearly between sorted values (Hyndman–Fan type 7). The standard deviation divides by 𝑛, measuring the spread of the picture itself. **References**: [R50 Hyndman · Fan 1996](../README.en.md#r50)
- **z-normalization**: $`z = (a - \text{mean})/\text{standard deviation}`$ (all 0 if the standard deviation is at most $`10^{-6}`$).
  - **Note** — **Why**: Comparing two patterns with different brightness and contrast, such as the correlation with the face pattern, should compare shape only. **How it works**: Subtracting the mean and dividing by the standard deviation makes the value invariant to added brightness and multiplied contrast; the mean product of two such vectors is the normalized cross-correlation. **References**: [R34 Lewis 1995](../README.en.md#r34)

## 4.3 Line art detection

The brightness 𝐿 is closed with the line width limit 𝑤 (default $`w_0 = \max(3, \mathrm{round}(4s))`$, or the automatic setting below, or the set value).

```math
\mathcal C=\mathrm{erode}_w(\mathrm{dilate}_w(L)),\qquad d=\mathcal C-L,\qquad
\mathrm{strength}=\min\!\left(\frac d{\mathcal C},\frac d{0.3}\right)\quad(\mathcal C>0.02,\ d>0)
```

**Note** — **Why**: A line is "darker than its surroundings and thinner than the pen". Only brightness valleys narrower than the window must be picked to separate lines from wide dark paint (black clothes). **How it works**: Dilation then erosion (closing) fills dark valleys narrower than the window 𝑤 with the surrounding light values and leaves wide areas alone. The difference 𝑑 from the original (black top-hat) is the line depth; the smaller of the depth relative to the surrounding brightness and the absolute depth over 0.3 is used, so a strong line must be deep in both senses. **References**: [R15 Soille 2003](../README.en.md#r15) · [R14 Gonzalez · Woods 2018](../README.en.md#r14)

The hysteresis thresholds come from the line sensitivity $`\eta \in[0, 1]`$ (default 0.5):

```math
t_{high}=0.58-0.34\,\eta,\qquad t_{low}=0.45\,t_{high}
```

Starting from pixels with $`\mathrm{strength} \ge t_{high}`$, it grows into 8-neighbors with $`\mathrm{strength} \ge t_{low}`$, and pieces smaller than $`\max(4, \mathrm{round}(6s))`$ pixels are discarded.
$`\mathrm{strength}`$ is the smaller of "how dark compared with the surrounding bright paint ($`\mathcal C`$)" ($`d/\mathcal C`$) and "how dark in absolute terms" ($`d/0.3`$), so it filters both shallow bumps on dark paint and faint noise on bright paint.

**Note** — **Why**: A single threshold breaks lines at faint stretches between dark ones, and lowering it picks up noise as well. **How it works**: Hysteresis (as in Canny edge detection) starts from sure pixels above the high threshold and grows only into neighbors above the low one. Both thresholds fall linearly as line sensitivity 𝜂 rises; 0.58 · 0.34 · 0.45 and the minimum piece size were tuned on test pictures. **References**: [R18 Canny 1986](../README.en.md#r18) · this program's experiments (7.1)

**Filling crossings**: starting from lines, up to $`w + 1`$ steps, it grows into pixels not brighter than the starting line's brightness $`L_{ref}`$ by 0.05 or more and with $`L \le 0.5`$.
Grown lumps that reach the end of the $`w + 1`$ steps (dark surfaces continuing beyond the line width) are discarded, and the rest are added to the lines.

**Note** — **Why**: Where several lines meet, the dark blob is wider than the window, the closing cannot fill it, and the line breaks. **How it works**: Growth from the line into dark pixels is limited to window size + 1 steps, and blobs that reach the limit (areas wider than the pen) are discarded, so only junctions are filled. 0.05 · 0.5 were set on test pictures. **References**: this program's experiments (7.1)

**Crisp lines**:

```math
d>0.02,\qquad \mathrm{strength}\ge 0.45,\qquad \frac{G_{1.5}(L)-L}d\ge 0.25
```

**Note** — **Why**: Backgrounds are often painted blurred like out-of-focus areas, so dark, crisp lines point to the character. **How it works**: A thin line loses much of its depth after a slight blur (σ = 1.5) as it mixes with the light surroundings, while an already blurred mark barely changes. So only lines that lose more than 25% of their depth count as crisp (the depth-of-field principle, section 5). **References**: [R13 Hecht 2017](../README.en.md#r13) · this program's experiments (7.2)

$`G_\sigma`$ is a <mark>Gaussian blur</mark>. The third condition means "a thin line that loses 25% or more of its depth when slightly blurred".

The lines and their 1px 8-neighbors are $`\mathrm{inMask}`$, and the remaining pixels with $`A > 0.02`$ are $`\mathrm{known}`$.

**Note** — **Why**: Line pixels and their edges have unknown original colors, so they must be left out of color statistics and fills. **How it works**: The line plus one 8-neighbor ring (the anti-aliasing band) is unknown; the rest, if not practically empty, is known. **References**: a rule set by this program

### Automatic setting (when the maximum line width is 0)

**Pen width**: $`\mathrm{strength}`$ as above is computed with a generous window $`R_b = \max(8, \mathrm{round}(12s))`$, and in the <mark>distance transform</mark> 𝐷 (<mark>chamfer</mark>) of structures with $`\mathrm{strength} \ge 0.5`$,
the width $`2D - 1`$ ($`\ge 1.8`$) is counted at each 4-neighbor local maximum ($`D(p) \ge`$ the 𝐷 of its four neighbors, a center line). In the histogram ℎ (0–63) of widths rounded into 1px bins,
the width among $`w = 2, \dots, 59`$ with the largest sum of $`h_k`$ over $`\lvert k - w \rvert \le \max(1, \mathrm{round}(0.2w))`$ is the peak 𝑚,
and the $`\lfloor 0.9(n - 1)\rfloor`$-th value (one decimal) of the widths at most 3 times 𝑚, in ascending order, is the pen width $`w_{90}`$. It is not measured if there are fewer than 150 center points.

**Note** — **Why**: A small picture drawn with a thick pen has lines the default window cannot hold, so almost no lines are found; the picture's pen width must be measured. **How it works**: In the distance transform of dark structures found with a wide window, local maxima are center lines and twice the value minus 1 is the width there. One pen concentrates on one width, so the peak of the histogram summed over a ±20% window is found, and the 90th percentile of widths up to three times the peak (excluding junctions · paint) is the pen width. **References**: [R21 Borgefors 1986](../README.en.md#r21) · [R14 Gonzalez · Woods 2018](../README.en.md#r14) · this program's experiments (7.1)

```math
w=\begin{cases}\min\big(16,\ \lceil w_{90}/2\rceil+1\big) & \lceil w_{90}/2\rceil+1\ \ge\ w_0+2\\ w_0 & \text{otherwise}\end{cases}
```

**Note** — **Why**: Other stages (background finding by line density) are tuned to the default window, so it is widened only when the measured pen clearly exceeds it, leaving other pictures unchanged. **How it works**: A square closing of radius 𝑤 fills valleys up to width $`2w + 1`$, so half the pen width + 1 holds the line. It is used only when at least 2 above the default, capped at 16. **References**: [R15 Soille 2003](../README.en.md#r15) · this program's experiments (7.1)

## 4.4 Line alpha and line color

Pixels covered by lines must satisfy the normal compositing formula.

```math
O_c=a\,K_c+(1-a)\,U_c
```

**Note** — **Why**: The line art is a normal (covering) layer, so the original must be "the line color laid over the color beneath by the alpha". Solving this gives the line's alpha and color. **How it works**: It is Porter–Duff over compositing per channel (ink covers a share 𝑎 of the pixel area). With the color beneath 𝑈 known, fixing either 𝐾 or 𝑎 solves for the other. **References**: [R1 Porter · Duff 1984](../README.en.md#r1) · [R2 Smith 1995](../README.en.md#r2)

- **Single black** ($`K = 0`$): $`a = \mathrm{clamp}(1 - \mathrm{lum}(O)/\mathrm{lum}(U))`$ (0 if $`\mathrm{lum}(U) \le 0.01`$)
  - **Note** — **Why**: With the line color set to black, only the alpha needs solving. **How it works**: With 𝐾 = 0, $`O = (1 - a)U`$, so $`a = 1 - O/U`$; the three channels are combined into one lightness to reduce noise. **References**: [R1 Porter · Duff 1984](../README.en.md#r1)
- **Original line colors in one layer**: $`a = \mathrm{clamp}(\max_c(1 - O_c/U_c))`$ (only channels with $`U_c > 0.004`$), $`K_c = \mathrm{clamp}((O_c - (1 - a)U_c)/a)`$
  - **Note** — **Why**: To keep the original line color per pixel, the smallest alpha for which a 0–1 line color exists keeps the layer light and the reproduction exact. **How it works**: 𝐾 ≥ 0 requires $`a \ge 1 - O_c/U_c`$ in each channel, so the maximum is the minimal alpha, and 𝐾 is the compositing formula solved for 𝐾. **References**: [R1 Porter · Duff 1984](../README.en.md#r1)
- **Line art + color trace** (default):
  1. The base line color $`K^0`$ = per-channel median of the original colors of line pixels with alpha 0.85 or more (the first bin where the cumulative count reaches half, in the 256-bin 8-bit histogram)
  2. The least-squares alpha given a line color 𝐾 (the 𝑎 minimizing $`\sum_c (O_c - (aK_c + (1 - a)U_c))^2`$; 0 if the denominator is at most $`10^{-5}`$)

     $`\displaystyle a(K)=\mathrm{clamp}\!\left(\frac{\sum_c (U_c-O_c)(U_c-K_c)}{\sum_c (U_c-K_c)^2}\right)`$
     - **Note** — **Why**: Given a line color 𝐾, each channel yields its own alpha, and noise makes the three differ slightly. One alpha that fits all three best is needed. **How it works**: The squared error $`\sum_c (O_c - U_c - a(K_c - U_c))^2`$ is quadratic in 𝑎; setting its derivative to zero gives this normal-equation solution (one-variable least squares). When the denominator is near 0 (line color equals the color beneath) it cannot be solved and is set to 0. **References**: [R43 Björck 1996](../README.en.md#r43) · [R1 Porter · Duff 1984](../README.en.md#r1)

  3. At pixels with $`a(K^0) \ge 0.5`$, the actual line color $`K_c = \mathrm{clamp}((O_c - (1 - a)U_c)/a)`$ is computed and inpainted over the whole line area ($`\mathrm{inMask}`$) to get a smooth line color $`\tilde K`$.
     - **Note** — **Why**: Finding lit lines · colored lines that differ from the base line color requires the actual line color per pixel. **How it works**: The compositing formula is solved for 𝐾 only where alpha is large enough (0.5 or more), since division by a small alpha amplifies noise; the other line pixels are filled by inpainting into a smooth line-color map $`	ilde K`$. **References**: [R1 Porter · Duff 1984](../README.en.md#r1) · [R20 Telea 2004](../README.en.md#r20)
  4. If $`\Delta E(\tilde K, K^0) \le 6`$ and the residual of compositing with $`K^0`$ is at most 8/255 per channel, it is line art (base line color); otherwise it is color trace.
     - **Note** — **Why**: Sending pixels whose line color is almost the base color to the color trace would make the layer messy, so only visibly different places are chosen. **How it works**: ΔE 6 is a difference noticeable side by side (two to three times the just-noticeable 2.3), and 8/255 is a few steps of 8-bit rounding. When both hold, the base line color reproduces the original, so the pixel stays in the line art. **References**: [R8 Mahy et al. 1994](../README.en.md#r8) · this program's experiments (7.1)
  5. The color trace alpha is taken at or above the **minimum alpha** at which the original is reproduced exactly by a line color within 0–1.

     $`\displaystyle a_{min}=\max_c\left\lbrace\,1-\frac{O_c}{U_c}\ (U_c>0.004),\ \ \frac{O_c-U_c}{1-U_c}\ (O_c>U_c,\ U_c<0.996)\right\rbrace,\qquad a=\max(a(\tilde K),a_{min})`$

     The color trace color of that pixel is $`K_c = \mathrm{clamp}((O_c - (1 - a)U_c)/a)`$. $`1 - O_c/U_c`$ is the minimum alpha that keeps the line color from going below 0, and $`(O_c - U_c)/(1 - U_c)`$ the minimum alpha that keeps it from going above 1.
     - **Note** — **Why**: Color-trace colors must lie in 0–1 to be stored, and compositing must reproduce the original exactly. **How it works**: $`K = (O - (1 - a)U)/a`$ is at least 0 only if $`a \ge 1 - O/U`$, and at most 1 only if $`a \ge (O - U)/(1 - U)`$ (when 𝑂 > 𝑈). With an alpha below the largest of these bounds no color can produce the original, so the larger of the least-squares alpha and this bound is used. **References**: [R1 Porter · Duff 1984](../README.en.md#r1)
  6. If the alpha sum of color trace pixels is less than 0.3% of the total line alpha sum, no color trace layer is made, and those pixels also go into the single line art layer with $`a(K^0)`$ and $`K^0`$.
     - **Note** — **Why**: With very few color-trace pixels there is no reason for a separate layer, and artists' files have no such layer either. **How it works**: If the color-trace alpha sum is under 0.3% of the total line alpha, those pixels also go into the single line-art layer with the base color $`K^0`$ and its least-squares alpha. 0.3% was set on test pictures. **References**: this program's experiments (7.1)

Pixels with alpha at most 0.02 are treated as not lines, and their restored color is reset to the original.

---

[← README](../README.en.md#4-algorithms-and-formulas) · Next: [4.5 Background](4-2-background.en.md)
