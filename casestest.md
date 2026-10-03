# cases test

A (current):

```math
f=
\begin{cases}
a & x<1\\
b & x\ge 1
\end{cases}
```

B (leading row break):

```math
f=
\begin{cases}
a & x<1
\\ b & x\ge 1
\end{cases}
```

C (one line per row, break mid-line):

```math
f=
\begin{cases}
a & x<1 \\ b & x\ge 1
\end{cases}
```

D (trailing break plus space comment-free):

```math
f=
\begin{cases}
a & x<1\\[0pt]
b & x\ge 1
\end{cases}
```
