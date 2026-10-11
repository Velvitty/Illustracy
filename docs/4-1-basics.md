# Illustracy — 4. 알고리즘과 수식 (1/4): 표기 · 색공간 · 기본 연산 · 선화

[← README](../README.md#4-알고리즘과-수식) · 4절 **1** · [2](4-2-background.md) · [3](4-3-regions-layers.md) · [4](4-4-rough-psd-tools.md) · [English](4-1-basics.en.md)

---

## 4.0 표기

- <mark>노랗게 칠한 이름</mark>은 이 글에서 쓴 통계식 · 알고리즘입니다(<mark>Zhang–Suen 세선화</mark>, <mark>윌슨 점수 구간</mark>, <mark>카이제곱 독립성 검정</mark> 등). 검증에 쓴 통계식의 정의는 11.1에 모았습니다.
- 픽셀 값은 0~1로 둔 sRGB 값입니다(8비트 값을 255로 나눔). 원본을 𝑂, 알파를 𝐴, 선 아래 복원색을 𝑈, 채널을 $`c \in \lbrace R, G, B\rbrace`$로 씁니다.
- 밝기는 $`\mathrm{lum}(r, g, b) = 0.299r + 0.587g + 0.114b`$입니다.
  선을 찾을 때의 밝기는 흰 바탕에 얹은 색의 밝기 $`L = \mathrm{lum}(A\cdot O_R + 1 - A, A\cdot O_G + 1 - A, A\cdot O_B + 1 - A)`$입니다.
- **처리 해상도**: 긴 변 한계 𝑀(기본 2048, 0은 원본 크기)에 대해 $`k = \min(1, M / \max(w_0, h_0))`$, $`W = \max(1, \mathrm{round}(k\cdot w_0))`$, $`H = \max(1, \mathrm{round}(k\cdot h_0))`$로
  브라우저의 고품질 축소를 씁니다. $`N = W\cdot H`$입니다. 한계가 0이고 원본이 1600만 픽셀을 넘으면 경고를 띄웁니다.
- **투명 그림**: $`A < 0.98`$인 픽셀이 $`0.001N`$보다 많으면 투명 그림으로 봅니다. $`A \le 0.02`$인 픽셀은 빈 곳입니다.
- $`s = \max(W, H) / 1000`$은 그림 크기에 따른 배율입니다(길이 기준값에 곱함).
- $`\mathrm{clamp}(x) = \min(1, \max(0, x))`$, $`\mathrm{smoothstep}(a, b, x)`$는 $`t = \mathrm{clamp}((x - a)/(b - a))`$에 대한 $`t^2(3 - 2t)`$입니다($`a > b`$이면 거꾸로 내려가는 곡선).
- 블록 수식의 $`\mathrm{clip}`$ 아래에 붙은 구간 $`[a, b]`$는 값을 그 구간으로 자른다는 뜻입니다: $`\min(b, \max(a, x))`$.
- 색 차이 $`\Delta E`$는 <mark>CIE76</mark>(Lab 공간의 <mark>유클리드 거리</mark>)입니다. 색상각 차이는 $`d = \lvert h_1 - h_2\rvert \bmod 360^\circ`$에 대해 $`\Delta h = \min(d, 360^\circ - d)`$입니다.
- 설정의 백분율 슬라이더(선 감도 𝜂, 밑색 병합 강도 𝑚, 그림자 판정 기준 $`\eta_s`$)는 $`\text{값}/100`$으로 0~1이 됩니다.
- $`\mathrm{round}`$는 가장 가까운 정수(0.5는 올림), $`\lfloor x \rfloor`$ · $`\lceil x \rceil`$는 내림 · 올림입니다.

## 4.1 색공간

sRGB를 선형화한 뒤 XYZ(D65)를 거쳐 Lab으로 바꿉니다.

```math
C_{lin}=\begin{cases}C/12.92 & C\le 0.04045\\ \left(\frac{C+0.055}{1.055}\right)^{2.4} & \text{otherwise}\end{cases}
\qquad
L^*=116f(Y)-16,\; a^*=500\,(f(X/X_n)-f(Y)),\; b^*=200\,(f(Y)-f(Z/Z_n))
```

```math
f(t)=\begin{cases}t^{1/3} & t>0.008856\\ 7.787\,t+16/116 & \text{otherwise}\end{cases}
```

선형 RGB에서 XYZ로는 sRGB(D65) 행렬을 쓰고, 기준 백색은 $`X_n = 0.95047,\ Y_n = 1,\ Z_n = 1.08883`$입니다.

```math
\begin{pmatrix}X\\Y\\Z\end{pmatrix}=
\begin{pmatrix}0.4124564&0.3575761&0.1804375\\0.2126729&0.7151522&0.0721750\\0.0193339&0.1191920&0.9503041\end{pmatrix}
\begin{pmatrix}R_{lin}\\G_{lin}\\B_{lin}\end{pmatrix}
```

선형화는 8비트 값 256칸 표로 미리 계산해 둡니다(𝐶를 $`\mathrm{round}(255C)`$칸으로). 채도 $`C^* = \sqrt{a^{*2} + b^{*2}}`$, 색상각 $`h = \mathrm{atan2}(b^*, a^*)`$(도 단위).

**Lab → sRGB**(표본이 하나도 없는 톤의 색을 <mark>k-평균</mark> 중심에서 되살릴 때):

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

($`C_{lin}`$은 0~1로 자른 뒤 감마를 씌웁니다.) 수동 보정 도구의 색 비교(4.17)도 같은 식의 Lab을 씁니다.

## 4.2 기본 연산

- **팽창 / 침식**(정사각형 반지름 𝑟): $`\mathrm{dilate}_r(f)(x, y) = \max f(x + i, y + j)`$($`\lvert i \rvert, \lvert j \rvert \le r`$에서의 최댓값. 침식은 최솟값, 그림 밖은 창에서 뺌).
  행과 열로 나눈 1차원 슬라이딩 최대 / 최소를 **단조 덱**으로 계산해 픽셀당 $`O(1)`$입니다. **닫기**는 팽창 뒤 침식, **열기**는 침식 뒤 팽창입니다.
- **<mark>가우시안 흐림</mark>**: 반지름 𝑟인 상자 흐림(폭 $`2r + 1`$, 그림 밖은 가장자리 값을 되풀이)을 가로 · 세로로 3번 반복해 근사합니다.
  상자 한 번의 분산이 $`((2r + 1)^2 - 1)/12 = r(r + 1)/3`$이므로 세 번이면 $`r(r + 1) = \sigma^2`$이 되고, 이를 풀면
  $`r = \max(1, \mathrm{round}((\sqrt{4\sigma^2 + 1} - 1)/2))`$입니다. $`\sigma < 0.3`$이면 흐리지 않습니다.
- **인페인팅**: 모르는 픽셀을 아는 픽셀과의 거리 순서(바깥 겹부터)로 방문해, 한 겹 안쪽까지 확정된 8-이웃의 평균으로 채웁니다.

  $`\displaystyle U(p)=\frac1{|\mathcal N_p|}\sum_{q\in\mathcal N_p}U(q),\qquad \mathcal N_p=\lbrace q\in 8\text{-이웃}(p):\ \text{겹}(q)<\text{겹}(p)\rbrace`$

- **라벨 채우기**: 라벨 없는 픽셀을 거리 순서로 방문해, 확정된 8-이웃 라벨의 다수결(4-이웃은 2표, 대각선은 1표)로 채웁니다.
- **연결 성분**: 같은 값끼리 4-이웃으로 이어진 덩어리입니다. **둘레**는 성분의 픽셀마다 4-이웃 중 다른 성분(또는 그림 밖)인 변의 수를 더한 값입니다.
- **<mark>거리 변환</mark>**(<mark>체임퍼</mark>): 가로 · 세로 한 칸 1, 대각선 한 칸 $`\sqrt 2`$인 두 번 훑기(위 → 아래, 아래 → 위)로 가장 가까운 표시 픽셀까지의 거리를 근사합니다.

  $`\displaystyle d(p)=\min\big(d(p),\ d(q)+w_{pq}\big),\qquad w_{pq}\in\lbrace1,\sqrt2\rbrace`$

  "몇 걸음 안"이라고 쓴 곳은 4-이웃 <mark>너비 우선 탐색</mark>의 걸음 수(<mark>맨해튼 거리</mark>)입니다.
- **<mark>k-평균</mark>**(Lab 제곱 거리): 표본 $`M = \min(n, M_\max)`$개를 뽑고($`n > M_\max`$이면 복원 추출), **<mark>k-means++</mark>** 방식으로 첫 중심은 고르게, 다음 중심은 지금까지의 가장 가까운 중심까지 거리의 제곱 $`D(x)^2`$에 비례하는 확률로 뽑습니다.
  배정 → 평균 갱신을 최대 18번 하고, 4번째 반복부터 배정이 바뀐 표본이 $`0.001M`$ 미만이면 멈춥니다. 빈 군집은 가장 먼 표본으로 옮깁니다.
  $`M_\max`$는 영역 나누기 50000, 색 모델의 영역 그래프 40000, 재질별 톤 6000입니다.
- **난수**: 결과가 매번 같도록 고정 씨앗의 <mark>mulberry32</mark>를 씁니다(본 계산 12345, 색 모델 · 얼굴 단계의 영역 그래프 777, 러프 20261011). 32비트 정수 연산으로
  $`s \gets s + \mathtt{0x6D2B79F5}`$, $`t = (s \oplus s \gg 15) \cdot(s \mathbin{\vert} 1)`$, $`t \gets t \oplus(t + (t \oplus t \gg 7) \cdot(t \mathbin{\vert} 61))`$, 난수 $`= (t \oplus t \gg 14)/2^{32}`$입니다(≫는 부호 없는 오른쪽 시프트).
- **값 잡음**(러프의 연필 결): 간격 $`\mathrm{cell}`$인 격자점마다 $`[-1, 1]`$의 난수 𝑔를 두고, 격자 칸 안에서 $`s_x = \mathrm{smoothstep}(0, 1, t_x)`$, $`s_y = \mathrm{smoothstep}(0, 1, t_y)`$로 섞습니다.

  $`\displaystyle n(x,y)=\big(g_{00}+(g_{10}-g_{00})s_x\big)(1-s_y)+\big(g_{01}+(g_{11}-g_{01})s_x\big)s_y`$

- **<mark>쌍선형 보간</mark>**: $`x_0 = \lfloor x\rfloor,\ t_x = x - x_0`$(세로도 같게)일 때 $`f = f_{00}(1 - t_x)(1 - t_y) + f_{10}t_x(1 - t_y) + f_{01}(1 - t_x)t_y + f_{11}t_x t_y`$.
- **크기 바꾸기**(얼굴 찾기용, 가로 · 세로 따로): 비율 $`r = n / m`$(원래 칸 수 / 새 칸 수)이 1 이상이면 새 칸 𝑖가 덮는 원래 구간 $`[ir, (i + 1)r)`$의 **면적 평균**,
  1 미만이면 $`x = (i + 0.5)r - 0.5`$에서의 <mark>**선형 보간**</mark>입니다.
- **백분위**: 오름차순 $`s_0 \dots s_{n-1}`$에서 $`x = (n - 1)q / 100,\ k = \lfloor x\rfloor`$일 때 $`s_k + (s_{k + 1} - s_k)(x - k)`$(중앙값은 $`q = 50`$). **표준편차**는 𝑛으로 나눈 모표준편차입니다.
- **z 정규화**: $`z = (a - \text{평균})/\text{표준편차}`$(표준편차가 $`10^{-6}`$ 이하이면 모두 0).

## 4.3 선화 검출

선 굵기 한계 𝑤(기본 $`w_0 = \max(3, \mathrm{round}(4s))`$, 아래 자동 설정 또는 설정값)로 밝기 𝐿을 클로징합니다.

```math
\mathcal C=\mathrm{erode}_w(\mathrm{dilate}_w(L)),\qquad d=\mathcal C-L,\qquad
\mathrm{strength}=\min\!\left(\frac d{\mathcal C},\frac d{0.3}\right)\quad(\mathcal C>0.02,\ d>0)
```

히스테리시스 임계값은 선 감도 $`\eta \in[0, 1]`$(기본 0.5)에서

```math
t_{high}=0.58-0.34\,\eta,\qquad t_{low}=0.45\,t_{high}
```

$`\mathrm{strength} \ge t_{high}`$인 픽셀에서 출발해 $`\mathrm{strength} \ge t_{low}`$인 8-이웃으로 넓히고, $`\max(4, \mathrm{round}(6s))`$픽셀보다 작은 조각은 버립니다.
$`\mathrm{strength}`$는 "주변의 밝은 칠($`\mathcal C`$)에 비해 얼마나 어두운가"($`d/\mathcal C`$)와 "절대적으로 얼마나 어두운가"($`d/0.3`$) 중 작은 값이라, 어두운 칠 위의 얕은 요철과 밝은 칠 위의 옅은 잡음을 모두 거릅니다.

**교차점 채우기**: 선에서 출발해 $`w + 1`$단계까지, 출발 선의 밝기 $`L_{ref}`$보다 0.05 이상 밝지 않고 $`L \le 0.5`$인 픽셀로 넓힙니다.
넓힌 덩어리 중 $`w + 1`$단계 끝까지 닿은 것(선 굵기를 넘어 이어지는 어두운 면)은 버리고 나머지를 선에 더합니다.

**선명한 선**:

```math
d>0.02,\qquad \mathrm{strength}\ge 0.45,\qquad \frac{G_{1.5}(L)-L}d\ge 0.25
```

$`G_\sigma`$는 <mark>가우시안 흐림</mark>입니다. 세 번째 조건은 "살짝 흐리면 깊이의 25% 이상이 사라지는 가는 선"을 뜻합니다.

선과 그 8-이웃 1px을 $`\mathrm{inMask}`$, 나머지 픽셀 중 $`A > 0.02`$인 것을 $`\mathrm{known}`$으로 둡니다.

### 자동 설정(최대 선 굵기가 0일 때)

**펜 굵기**: 넉넉한 창 $`R_b = \max(8, \mathrm{round}(12s))`$로 위와 같은 $`\mathrm{strength}`$를 구하고, $`\mathrm{strength} \ge 0.5`$인 구조의 <mark>거리 변환</mark> 𝐷(<mark>체임퍼</mark>)에서
4-이웃 극대점($`D(p) \ge`$ 네 이웃의 𝐷, 중심선)마다 굵기 $`2D - 1`$($`\ge 1.8`$)을 셉니다. 굵기를 $`\mathrm{round}`$한 1px 칸 히스토그램 ℎ(0~63)에서
$`w = 2, \dots, 59`$ 중 $`\lvert k - w \rvert \le \max(1, \mathrm{round}(0.2w))`$인 $`h_k`$의 합이 가장 큰 굵기가 봉우리 𝑚이고,
𝑚의 3배 이하인 굵기들을 오름차순으로 놓은 $`\lfloor 0.9(n - 1)\rfloor`$번째 값(소수 첫째 자리)이 펜 굵기 $`w_{90}`$입니다. 중심선이 150개 미만이면 재지 않습니다.

```math
w=\begin{cases}\min\big(16,\ \lceil w_{90}/2\rceil+1\big) & \lceil w_{90}/2\rceil+1\ \ge\ w_0+2\\ w_0 & \text{그 밖}\end{cases}
```

## 4.4 선 알파와 선 색

선이 덮은 픽셀은 표준 합성식을 만족해야 합니다.

```math
O_c=a\,K_c+(1-a)\,U_c
```

- **검정 단색**($`K = 0`$): $`a = \mathrm{clamp}(1 - \mathrm{lum}(O)/\mathrm{lum}(U))`$($`\mathrm{lum}(U) \le 0.01`$이면 0)
- **원본 선 색 한 장**: $`a = \mathrm{clamp}(\max_c(1 - O_c/U_c))`$($`U_c > 0.004`$인 채널만), $`K_c = \mathrm{clamp}((O_c - (1 - a)U_c)/a)`$
- **선화 + 색 트레이스**(기본):
  1. 기본 선 색 $`K^0`$ = 알파 0.85 이상인 선 픽셀의 원본 색 채널별 중앙값(8비트 256칸 히스토그램에서 누적이 절반 이상이 되는 첫 칸)
  2. 선 색 𝐾가 주어졌을 때의 <mark>최소제곱</mark> 알파($`\sum_c (O_c - (aK_c + (1 - a)U_c))^2`$을 가장 작게 하는 𝑎, 분모가 $`10^{-5}`$ 이하이면 0)

     $`\displaystyle a(K)=\mathrm{clamp}\!\left(\frac{\sum_c (U_c-O_c)(U_c-K_c)}{\sum_c (U_c-K_c)^2}\right)`$

  3. $`a(K^0) \ge 0.5`$인 픽셀에서 실제 선 색 $`K_c = \mathrm{clamp}((O_c - (1 - a)U_c)/a)`$를 구하고, 선 영역($`\mathrm{inMask}`$) 전체로 인페인팅해 부드러운 선 색 $`\tilde K`$를 얻습니다.
  4. $`\Delta E(\tilde K, K^0) \le 6`$이고 $`K^0`$로 합성한 잔차가 채널별 8/255 이하이면 선화(기본 선 색), 아니면 색 트레이스입니다.
  5. 색 트레이스 알파는 원본이 0~1 범위 안의 선 색으로 정확히 재현되는 **최소 알파** 이상으로 잡습니다.

     $`\displaystyle a_{min}=\max_c\left\lbrace\,1-\frac{O_c}{U_c}\ (U_c>0.004),\ \ \frac{O_c-U_c}{1-U_c}\ (O_c>U_c,\ U_c<0.996)\right\rbrace,\qquad a=\max(a(\tilde K),a_{min})`$

     그 픽셀의 색 트레이스 색은 $`K_c = \mathrm{clamp}((O_c - (1 - a)U_c)/a)`$입니다. $`1 - O_c/U_c`$는 선 색이 0 아래로 내려가지 않을 최소 알파, $`(O_c - U_c)/(1 - U_c)`$는 1 위로 올라가지 않을 최소 알파입니다.
  6. 색 트레이스 픽셀의 알파 합이 전체 선 알파 합의 0.3% 미만이면 색 트레이스 층을 만들지 않고, 그 픽셀들도 $`a(K^0)`$와 $`K^0`$로 선화 한 장에 둡니다.

알파가 0.02 이하인 픽셀은 선이 아닌 것으로 보고 복원색을 원본으로 되돌립니다.

---

[← README](../README.md#4-알고리즘과-수식) · 다음: [4.5 배경](4-2-background.md)
