# Illustracy — 4. Algorithms and formulas (1/4): Notation · color spaces · basic operations · line art

[← README](../README.en.md#4-algorithms-and-formulas) · Section 4 **1** · [2](4-2-background.en.md) · [3](4-3-regions-layers.en.md) · [4](4-4-rough-psd-tools.en.md) · [한국어](4-1-basics.md)

---

## 4.0 Notation

- <mark>Names highlighted in yellow</mark> are the statistical formulas · algorithms used in this document (<mark>Zhang–Suen thinning</mark>, <mark>Wilson score interval</mark>, <mark>Chi-square test of independence</mark> and others). The definitions of the statistics used for verification are collected in 11.1.
- Pixel values are sRGB values in 0–1 (8-bit value divided by 255). The original is 𝑂, the alpha 𝐴, the restored color under lines 𝑈, and the channel $`c \in \lbrace R, G, B\rbrace`$.
- Brightness is $`\mathrm{lum}(r, g, b) = 0.299r + 0.587g + 0.114b`$.
  The brightness used for finding lines is the brightness of the color laid on white, $`L = \mathrm{lum}(A\cdot O_R + 1 - A, A\cdot O_G + 1 - A, A\cdot O_B + 1 - A)`$.
- **Processing resolution**: for the long-side limit 𝑀 (default 2048, 0 means original size), $`k = \min(1, M / \max(w_0, h_0))`$, $`W = \max(1, \mathrm{round}(k\cdot w_0))`$, $`H = \max(1, \mathrm{round}(k\cdot h_0))`$,
  using the browser's high-quality downscaling. $`N = W\cdot H`$. If the limit is 0 and the original exceeds 16 million pixels, a warning is shown.
- **Transparent picture**: if more than $`0.001N`$ pixels have $`A < 0.98`$, the picture is treated as transparent. Pixels with $`A \le 0.02`$ are empty.
- $`s = \max(W, H) / 1000`$ is the scale factor for picture size (multiplied into length reference values).
- $`\mathrm{clamp}(x) = \min(1, \max(0, x))`$, and $`\mathrm{smoothstep}(a, b, x)`$ is $`t^2(3 - 2t)`$ for $`t = \mathrm{clamp}((x - a)/(b - a))`$ (a descending curve when $`a > b`$).
- In block formulas, an interval $`[a, b]`$ written under $`\mathrm{clip}`$ means the value is clipped to that interval: $`\min(b, \max(a, x))`$.
- Color difference $`\Delta E`$ is <mark>CIE76</mark> (<mark>Euclidean distance</mark> in Lab). Hue angle difference is $`\Delta h = \min(d, 360^\circ - d)`$ for $`d = \lvert h_1 - h_2\rvert \bmod 360^\circ`$.
- The percentage sliders in the settings (line sensitivity 𝜂, base color merge strength 𝑚, shadow threshold $`\eta_s`$) become 0–1 as $`\text{value}/100`$.
- $`\mathrm{round}`$ is the nearest integer (0.5 rounds up); $`\lfloor x \rfloor`$ · $`\lceil x \rceil`$ are floor · ceiling.

## 4.1 Color space

sRGB is linearized, then converted to Lab via XYZ (D65).

```math
C_{lin}=\begin{cases}C/12.92 & C\le 0.04045\\ \left(\frac{C+0.055}{1.055}\right)^{2.4} & \text{otherwise}\end{cases}
\qquad
L^*=116f(Y)-16,\; a^*=500\,(f(X/X_n)-f(Y)),\; b^*=200\,(f(Y)-f(Z/Z_n))
```

```math
f(t)=\begin{cases}t^{1/3} & t>0.008856\\ 7.787\,t+16/116 & \text{otherwise}\end{cases}
```

From linear RGB to XYZ the sRGB (D65) matrix is used, with reference white $`X_n = 0.95047,\ Y_n = 1,\ Z_n = 1.08883`$.

```math
\begin{pmatrix}X\\Y\\Z\end{pmatrix}=
\begin{pmatrix}0.4124564&0.3575761&0.1804375\\0.2126729&0.7151522&0.0721750\\0.0193339&0.1191920&0.9503041\end{pmatrix}
\begin{pmatrix}R_{lin}\\G_{lin}\\B_{lin}\end{pmatrix}
```

Linearization is precomputed as a 256-entry table of 8-bit values (𝐶 into bin $`\mathrm{round}(255C)`$). Chroma $`C^* = \sqrt{a^{*2} + b^{*2}}`$, hue angle $`h = \mathrm{atan2}(b^*, a^*)`$ (in degrees).

**Lab → sRGB** (when recovering, from a <mark>k-means</mark> center, the color of a tone that has no samples):

```math
f_y=\frac{L^*+16}{116},\ f_x=f_y+\frac{a^*}{500},\ f_z=f_y-\frac{b^*}{200},\qquad
f^{-1}(t)=\begin{cases}t^3 & t^3>0.008856\\ (t-16/116)/7.787 & \text{otherwise}\end{cases}
```

```math
\begin{pmatrix}R_{lin}\\G_{lin}\\B_{lin}\end{pmatrix}=
\begin{pmatrix}3.2404542&-1.5371385&-0.4985314\\-0.9692660&1.8760108&0.0415560\\0.0556434&-0.2040259&1.0572252\end{pmatrix}
\begin{pmatrix}X_n f^{-1}(f_x)\\ f^{-1}(f_y)\\ Z_n f^{-1}(f_z)\end{pmatrix},\qquad
C=\begin{cases}12.92\,C_{lin} & C_{lin}\le 0.0031308\\ 1.055\,C_{lin}^{1/2.4}-0.055 & \text{otherwise}\end{cases}
```

($`C_{lin}`$ is clipped to 0–1 before applying the gamma.) The color comparison of the manual correction tools (4.17) uses Lab from the same formulas.

## 4.2 Basic operations

- **Dilation / erosion** (square of radius 𝑟): $`\mathrm{dilate}_r(f)(x, y) = \max f(x + i, y + j)`$ (the maximum over $`\lvert i \rvert, \lvert j \rvert \le r`$; erosion takes the minimum; outside the picture is dropped from the window).
  The 1-D sliding max / min split into rows and columns is computed with a **monotonic deque**, $`O(1)`$ per pixel. **Closing** is dilation then erosion; **opening** is erosion then dilation.
- **<mark>Gaussian blur</mark>**: approximated by repeating a box blur of radius 𝑟 (width $`2r + 1`$, repeating edge values outside the picture) three times horizontally and vertically.
  One box pass has variance $`((2r + 1)^2 - 1)/12 = r(r + 1)/3`$, so three passes give $`r(r + 1) = \sigma^2`$, which solves to
  $`r = \max(1, \mathrm{round}((\sqrt{4\sigma^2 + 1} - 1)/2))`$. If $`\sigma < 0.3`$, there is no blur.
- **Inpainting**: unknown pixels are visited in order of distance from known pixels (outer rings first) and filled with the average of the 8-neighbors already settled one ring further in.

  $`\displaystyle U(p)=\frac1{|\mathcal N_p|}\sum_{q\in\mathcal N_p}U(q),\qquad \mathcal N_p=\lbrace q\in 8\text{-nbr}(p):\ \text{ring}(q)<\text{ring}(p)\rbrace`$

- **Label filling**: unlabeled pixels are visited in order of distance and filled by a majority vote of the settled 8-neighbor labels (4-neighbors get 2 votes, diagonals 1).
- **Connected component**: a lump of equal values connected by 4-neighbors. The **perimeter** is the sum, over the pixels of the component, of the number of 4-neighbor sides that belong to another component (or lie outside the picture).
- **Distance transform** (<mark>chamfer</mark>): two sweeps (top → bottom, bottom → top) with weight 1 for a horizontal · vertical step and $`\sqrt 2`$ for a diagonal step approximate the distance to the nearest marked pixel.

  $`\displaystyle d(p)=\min\big(d(p),\ d(q)+w_{pq}\big),\qquad w_{pq}\in\lbrace1,\sqrt2\rbrace`$

  Where it says "within so many steps", it means the number of steps of a 4-neighbor <mark>breadth-first search</mark> (<mark>Manhattan distance</mark>).
- **<mark>k-means</mark>** (squared Lab distance): $`M = \min(n, M_\max)`$ samples are drawn (with replacement if $`n > M_\max`$); with **<mark>k-means++</mark>** the first center is uniform and each next center is drawn with probability proportional to the squared distance $`D(x)^2`$ to the nearest center so far.
  Assignment → mean update runs up to 18 times, stopping from the 4th iteration on when fewer than $`0.001M`$ samples change assignment. An empty cluster is moved to the farthest sample.
  $`M_\max`$ is 50000 for region splitting, 40000 for the region graph of the color model, and 6000 for tones per material.
- **Random numbers**: fixed-seed <mark>mulberry32</mark> so results are the same every time (main computation 12345, region graph of the color model · face stage 777, rough 20261011). With 32-bit integer arithmetic,
  $`s \gets s + \mathtt{0x6D2B79F5}`$, $`t = (s \oplus s \gg 15) \cdot(s \mathbin{\vert} 1)`$, $`t \gets t \oplus(t + (t \oplus t \gg 7) \cdot(t \mathbin{\vert} 61))`$, random number $`= (t \oplus t \gg 14)/2^{32}`$ (≫ is the unsigned right shift).
- **Value noise** (pencil grain of the rough): a random number 𝑔 in $`[-1, 1]`$ at each grid point with spacing $`\mathrm{cell}`$, blended within a grid cell with $`s_x = \mathrm{smoothstep}(0, 1, t_x)`$, $`s_y = \mathrm{smoothstep}(0, 1, t_y)`$.

  $`\displaystyle n(x,y)=\big(g_{00}+(g_{10}-g_{00})s_x\big)(1-s_y)+\big(g_{01}+(g_{11}-g_{01})s_x\big)s_y`$

- **<mark>Bilinear interpolation</mark>**: with $`x_0 = \lfloor x\rfloor,\ t_x = x - x_0`$ (same vertically), $`f = f_{00}(1 - t_x)(1 - t_y) + f_{10}t_x(1 - t_y) + f_{01}(1 - t_x)t_y + f_{11}t_x t_y`$.
- **Resizing** (for face finding, horizontal · vertical separately): if the ratio $`r = n / m`$ (original cells / new cells) is at least 1, the **area average** of the original interval $`[ir, (i + 1)r)`$ covered by new cell 𝑖;
  if below 1, **<mark>linear interpolation</mark>** at $`x = (i + 0.5)r - 0.5`$.
- **Percentile**: for ascending $`s_0 \dots s_{n-1}`$ with $`x = (n - 1)q / 100,\ k = \lfloor x\rfloor`$, the value is $`s_k + (s_{k + 1} - s_k)(x - k)`$ (the median is $`q = 50`$). The **standard deviation** is the population standard deviation divided by 𝑛.
- **z-normalization**: $`z = (a - \text{mean})/\text{standard deviation}`$ (all 0 if the standard deviation is at most $`10^{-6}`$).

## 4.3 Line art detection

The brightness 𝐿 is closed with the line width limit 𝑤 (default $`w_0 = \max(3, \mathrm{round}(4s))`$, or the automatic setting below, or the set value).

```math
\mathcal C=\mathrm{erode}_w(\mathrm{dilate}_w(L)),\qquad d=\mathcal C-L,\qquad
\mathrm{strength}=\min\!\left(\frac d{\mathcal C},\frac d{0.3}\right)\quad(\mathcal C>0.02,\ d>0)
```

The hysteresis thresholds come from the line sensitivity $`\eta \in[0, 1]`$ (default 0.5):

```math
t_{high}=0.58-0.34\,\eta,\qquad t_{low}=0.45\,t_{high}
```

Starting from pixels with $`\mathrm{strength} \ge t_{high}`$, it grows into 8-neighbors with $`\mathrm{strength} \ge t_{low}`$, and pieces smaller than $`\max(4, \mathrm{round}(6s))`$ pixels are discarded.
$`\mathrm{strength}`$ is the smaller of "how dark compared with the surrounding bright paint ($`\mathcal C`$)" ($`d/\mathcal C`$) and "how dark in absolute terms" ($`d/0.3`$), so it filters both shallow bumps on dark paint and faint noise on bright paint.

**Filling crossings**: starting from lines, up to $`w + 1`$ steps, it grows into pixels not brighter than the starting line's brightness $`L_{ref}`$ by 0.05 or more and with $`L \le 0.5`$.
Grown lumps that reach the end of the $`w + 1`$ steps (dark surfaces continuing beyond the line width) are discarded, and the rest are added to the lines.

**Crisp lines**:

```math
d>0.02,\qquad \mathrm{strength}\ge 0.45,\qquad \frac{G_{1.5}(L)-L}d\ge 0.25
```

$`G_\sigma`$ is a <mark>Gaussian blur</mark>. The third condition means "a thin line that loses 25% or more of its depth when slightly blurred".

The lines and their 1px 8-neighbors are $`\mathrm{inMask}`$, and the remaining pixels with $`A > 0.02`$ are $`\mathrm{known}`$.

### Automatic setting (when the maximum line width is 0)

**Pen width**: $`\mathrm{strength}`$ as above is computed with a generous window $`R_b = \max(8, \mathrm{round}(12s))`$, and in the <mark>distance transform</mark> 𝐷 (<mark>chamfer</mark>) of structures with $`\mathrm{strength} \ge 0.5`$,
the width $`2D - 1`$ ($`\ge 1.8`$) is counted at each 4-neighbor local maximum ($`D(p) \ge`$ the 𝐷 of its four neighbors, a center line). In the histogram ℎ (0–63) of widths rounded into 1px bins,
the width among $`w = 2, \dots, 59`$ with the largest sum of $`h_k`$ over $`\lvert k - w \rvert \le \max(1, \mathrm{round}(0.2w))`$ is the peak 𝑚,
and the $`\lfloor 0.9(n - 1)\rfloor`$-th value (one decimal) of the widths at most 3 times 𝑚, in ascending order, is the pen width $`w_{90}`$. It is not measured if there are fewer than 150 center points.

```math
w=\begin{cases}\min\big(16,\ \lceil w_{90}/2\rceil+1\big) & \lceil w_{90}/2\rceil+1\ \ge\ w_0+2\\ w_0 & \text{otherwise}\end{cases}
```

## 4.4 Line alpha and line color

Pixels covered by lines must satisfy the normal compositing formula.

```math
O_c=a\,K_c+(1-a)\,U_c
```

- **Single black** ($`K = 0`$): $`a = \mathrm{clamp}(1 - \mathrm{lum}(O)/\mathrm{lum}(U))`$ (0 if $`\mathrm{lum}(U) \le 0.01`$)
- **Original line colors in one layer**: $`a = \mathrm{clamp}(\max_c(1 - O_c/U_c))`$ (only channels with $`U_c > 0.004`$), $`K_c = \mathrm{clamp}((O_c - (1 - a)U_c)/a)`$
- **Line art + color trace** (default):
  1. The base line color $`K^0`$ = per-channel median of the original colors of line pixels with alpha 0.85 or more (the first bin where the cumulative count reaches half, in the 256-bin 8-bit histogram)
  2. The least-squares alpha given a line color 𝐾 (the 𝑎 minimizing $`\sum_c (O_c - (aK_c + (1 - a)U_c))^2`$; 0 if the denominator is at most $`10^{-5}`$)

     $`\displaystyle a(K)=\mathrm{clamp}\!\left(\frac{\sum_c (U_c-O_c)(U_c-K_c)}{\sum_c (U_c-K_c)^2}\right)`$

  3. At pixels with $`a(K^0) \ge 0.5`$, the actual line color $`K_c = \mathrm{clamp}((O_c - (1 - a)U_c)/a)`$ is computed and inpainted over the whole line area ($`\mathrm{inMask}`$) to get a smooth line color $`\tilde K`$.
  4. If $`\Delta E(\tilde K, K^0) \le 6`$ and the residual of compositing with $`K^0`$ is at most 8/255 per channel, it is line art (base line color); otherwise it is color trace.
  5. The color trace alpha is taken at or above the **minimum alpha** at which the original is reproduced exactly by a line color within 0–1.

     $`\displaystyle a_{min}=\max_c\left\lbrace\,1-\frac{O_c}{U_c}\ (U_c>0.004),\ \ \frac{O_c-U_c}{1-U_c}\ (O_c>U_c,\ U_c<0.996)\right\rbrace,\qquad a=\max(a(\tilde K),a_{min})`$

     The color trace color of that pixel is $`K_c = \mathrm{clamp}((O_c - (1 - a)U_c)/a)`$. $`1 - O_c/U_c`$ is the minimum alpha that keeps the line color from going below 0, and $`(O_c - U_c)/(1 - U_c)`$ the minimum alpha that keeps it from going above 1.
  6. If the alpha sum of color trace pixels is less than 0.3% of the total line alpha sum, no color trace layer is made, and those pixels also go into the single line art layer with $`a(K^0)`$ and $`K^0`$.

Pixels with alpha at most 0.02 are treated as not lines, and their restored color is reset to the original.

---

[← README](../README.en.md#4-algorithms-and-formulas) · Next: [4.5 Background](4-2-background.en.md)
