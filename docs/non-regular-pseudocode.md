# 证明 9618 Pseudocode 非正则

> 配套 [pumping-lemma-duel.md](pumping-lemma-duel.md)（其中已证 `PAREN = {(ⁿ)ⁿ}` 非正则）。`Ctrl+Shift+V` 预览。

**记号**　`L` = 全体语法合法伪代码程序（token 字母表 `Σ`）。策略：反证 + 交 + 同态，归约到 `PAREN`。

**1. 反设**　`L` 正则。

**2. 正则切片**　`R = (IF X THEN)* · (X ← 1) · (ENDIF)*`　（头尾数目不要求相等，故正则）

**3. 切出 B_IF**　断言 `L ∩ R = B_IF = { (IF X THEN)ⁿ · (X ← 1) · (ENDIF)ⁿ : n ≥ 0 }`
- **(⊆)** `w∈L∩R`：由 `R` 得 `w=(IF X THEN)ⁱ(X←1)(ENDIF)ʲ`；由 `w∈L` 合法（一个 ENDIF 关一个 IF，§6.1）得 `i=j` ⟹ `w∈B_IF`
- **(⊇)** `w∈B_IF`：`w∈L`（n 层嵌套 IF，最内层 `X←1` 合法 §2.6）且 `w∈R`（形状对）

**4. 同态抹成 PAREN**　`h(IF)=(`，`h(ENDIF)=)`，`h(X)=h(THEN)=h(x)=h(←)=h(1)=ε`
⟹ 每个 `IF X THEN`→`(`、body→`ε`、每个 `ENDIF`→`)`　⟹　`h(B_IF) = {(ⁿ)ⁿ} = PAREN`

**5. 同态保正则**（引理）　取认 `B_IF` 的 NFA，把每条边 `q —a→ q'` 替换为一条拼出 `h(a)` 的路径（`h(a)=ε` 用 `ε`-边）；仍是 NFA ⟹ `h(B_IF)` 正则。

**6. 收网**
```
L 正则 ⟹ L∩R 正则(正则∩正则) ⟹ B_IF 正则(步3) ⟹ h(B_IF)=PAREN 正则(步4·5)
但 PAREN 非正则 ⟹ 矛盾 ⟹  L 非正则。 ∎
```

---
**闭包**：正则∩正则=正则；正则对同态封闭。　**精确性**：确立的是**语法层**非正则（`IF…ENDIF` 可任意深嵌套），不蕴含"非上下文无关"。条件 `X` 需 BOOLEAN，滴水不漏可写 `IF X = 1 THEN`。
