# cases test 3

E (space after <):

```math
\mathrm{shadeRelated}(c_1,c_2)=
\begin{cases}
\text{참} & \Delta E<\varepsilon_s\\
|L_1-L_2|<3\varepsilon_s & C_1<12,\ C_2<12\\
|h_1-h_2|<\varepsilon_h,\ \ 0.3< C_1/C_2<3.3 & C_1\ge 12,\ C_2\ge 12\\
\text{아래 규칙} & \text{한쪽만 무채색}
\end{cases}
\qquad \varepsilon_h=14+40m,\ \ \varepsilon_s=5+12m
```

F (\lt):

```math
\mathrm{shadeRelated}(c_1,c_2)=
\begin{cases}
\text{참} & \Delta E<\varepsilon_s\\
|L_1-L_2|<3\varepsilon_s & C_1<12,\ C_2<12\\
|h_1-h_2|<\varepsilon_h,\ \ 0.3\lt C_1/C_2<3.3 & C_1\ge 12,\ C_2\ge 12\\
\text{아래 규칙} & \text{한쪽만 무채색}
\end{cases}
\qquad \varepsilon_h=14+40m,\ \ \varepsilon_s=5+12m
```

G (minimal x<y):

```math
f=
\begin{cases}
a & x<y\\
b & x\ge 1
\end{cases}
```
