from collections import defaultdict


# ════════════════════════════════════════════════════════════════════════
# 1. 字符类(CharClass)—— NFA 边上的 label,决定“消费一个怎样的字符”
# ════════════════════════════════════════════════════════════════════════
class CharClass:
    def __init__(self, test, label):
        self.test = test          # 函数 ch -> bool
        self.label = label        # 仅用于调试打印
    def __repr__(self):
        return self.label


def cc_single(ch):
    return CharClass(lambda c: c == ch, repr(ch))

def cc_any():                                  # '.' :flex 里默认不含换行
    return CharClass(lambda c: c != '\n', '.')

def cc_set(ranges, chars, negate=False, label='[…]'):
    chars = set(chars)
    def test(c):
        hit = c in chars or any(lo <= c <= hi for lo, hi in ranges)
        return (not hit) if negate else hit
    return CharClass(test, label)

_PREDEF = {
    'd': cc_set([('0', '9')], '', label='\\d'),
    'w': cc_set([('0', '9'), ('a', 'z'), ('A', 'Z')], '_', label='\\w'),
    's': cc_set([], ' \t\n\r\f\v', label='\\s'),
    'n': cc_single('\n'), 't': cc_single('\t'),
}


# ════════════════════════════════════════════════════════════════════════
# 2. 正则 AST + 递归下降 parser(讽刺点:做 lexer 之前,先得手写一个 regex parser)
# ════════════════════════════════════════════════════════════════════════
class Lit:    __slots__ = ('cc',);    __init__ = lambda s, cc: setattr(s, 'cc', cc)
class Star:   __slots__ = ('x',);     __init__ = lambda s, x: setattr(s, 'x', x)
class Plus:   __slots__ = ('x',);     __init__ = lambda s, x: setattr(s, 'x', x)
class Opt:    __slots__ = ('x',);     __init__ = lambda s, x: setattr(s, 'x', x)
class Concat: __slots__ = ('xs',);    __init__ = lambda s, xs: setattr(s, 'xs', xs)
class Alt:    __slots__ = ('xs',);    __init__ = lambda s, xs: setattr(s, 'xs', xs)


class RegexParser:
    def __init__(self, src):
        self.s = src
        self.i = 0

    def peek(self):
        return self.s[self.i] if self.i < len(self.s) else ''

    def eat(self):
        c = self.s[self.i]; self.i += 1; return c

    def parse(self):
        node = self.alt()
        if self.i != len(self.s):
            raise ValueError(f"regex 解析未到末尾: {self.s!r} @ {self.i}")
        return node

    def alt(self):
        parts = [self.concat()]
        while self.peek() == '|':
            self.eat(); parts.append(self.concat())
        return parts[0] if len(parts) == 1 else Alt(parts)

    def concat(self):
        parts = []
        while self.peek() and self.peek() not in '|)':
            parts.append(self.repeat())
        return parts[0] if len(parts) == 1 else Concat(parts)

    def repeat(self):
        node = self.atom()
        while self.peek() and self.peek() in '*+?':
            op = self.eat()
            node = {'*': Star, '+': Plus, '?': Opt}[op](node)
        return node

    def atom(self):
        c = self.peek()
        if c == '(':
            self.eat(); node = self.alt()
            if self.eat() != ')':
                raise ValueError("缺少 )")
            return node
        if c == '[':
            return self.charclass()
        if c == '\\':
            self.eat(); e = self.eat()
            return Lit(_PREDEF.get(e, cc_single(e)))   # \d \w \s \n \t,否则字面字符
        if c == '.':
            self.eat(); return Lit(cc_any())
        self.eat(); return Lit(cc_single(c))

    def charclass(self):
        self.eat()                                     # '['
        negate = False
        if self.peek() == '^':
            self.eat(); negate = True
        ranges, chars = [], []
        while self.peek() and self.peek() != ']':
            c = self.eat()
            if c == '\\':
                c = self.eat()
                chars.append({'n': '\n', 't': '\t'}.get(c, c)); continue
            if self.peek() == '-' and self.i + 1 < len(self.s) and self.s[self.i + 1] != ']':
                self.eat(); hi = self.eat()
                ranges.append((c, hi))
            else:
                chars.append(c)
        if self.eat() != ']':
            raise ValueError("缺少 ]")
        return Lit(cc_set(ranges, chars, negate,
                          label=('[^' if negate else '[') + '…]'))


# ════════════════════════════════════════════════════════════════════════
# 3. Thompson construction:正则 AST -> NFA(ε-NFA)
# ════════════════════════════════════════════════════════════════════════
class NFA:
    def __init__(self):
        self.n = 0
        self.trans = defaultdict(list)   # state -> [(CharClass|None, state)]; None = ε
        self.accept_rule = {}            # accept_state -> (rule_index, rule_name)
        self.start = None

    def new(self):
        s = self.n; self.n += 1; return s

    def eps(self, a, b):
        self.trans[a].append((None, b))

    def edge(self, a, cc, b):
        self.trans[a].append((cc, b))

    def build(self, node):
        """返回 (start, accept) 片段,边写进 self.trans。"""
        if isinstance(node, Lit):
            s, a = self.new(), self.new(); self.edge(s, node.cc, a); return s, a
        if isinstance(node, Concat):
            s, a = self.build(node.xs[0])
            for nxt in node.xs[1:]:
                s2, a2 = self.build(nxt); self.eps(a, s2); a = a2
            return s, a
        if isinstance(node, Alt):
            s, a = self.new(), self.new()
            for opt in node.xs:
                os_, oa = self.build(opt); self.eps(s, os_); self.eps(oa, a)
            return s, a
        if isinstance(node, Star):
            s, a = self.new(), self.new(); ns, na = self.build(node.x)
            self.eps(s, ns); self.eps(na, a); self.eps(na, ns); self.eps(s, a)
            return s, a
        if isinstance(node, Plus):
            s, a = self.new(), self.new(); ns, na = self.build(node.x)
            self.eps(s, ns); self.eps(na, a); self.eps(na, ns)
            return s, a
        if isinstance(node, Opt):
            s, a = self.new(), self.new(); ns, na = self.build(node.x)
            self.eps(s, ns); self.eps(na, a); self.eps(s, a)
            return s, a
        raise TypeError(node)


def compile_spec(spec):
    """spec: [(name, regex_string), ...](顺序 = 优先级)-> 一个合并后的 NFA。"""
    nfa = NFA()
    master = nfa.new()
    for idx, (name, regex) in enumerate(spec):
        ast = RegexParser(regex).parse()
        s, a = nfa.build(ast)
        nfa.eps(master, s)
        nfa.accept_rule[a] = (idx, name)     # 接受态记住“这是第几条规则”
    nfa.start = master
    return nfa


# ════════════════════════════════════════════════════════════════════════
# 4. subset construction(lazy)+ maximal-munch driver = 生成出来的 scanner
# ════════════════════════════════════════════════════════════════════════
def _eps_closure(nfa, states):
    stack, seen = list(states), set(states)
    while stack:
        s = stack.pop()
        for label, t in nfa.trans.get(s, ()):
            if label is None and t not in seen:
                seen.add(t); stack.append(t)
    return frozenset(seen)


def _move(nfa, states, ch):
    out = set()
    for s in states:
        for label, t in nfa.trans.get(s, ()):
            if label is not None and label.test(ch):
                out.add(t)
    return out


def _accept(nfa, states):
    """该 DFA 状态(=NFA 状态集)对应哪条规则;平局取 rule_index 最小(先列出的)。"""
    best = None
    for s in states:
        r = nfa.accept_rule.get(s)
        if r is not None and (best is None or r[0] < best[0]):
            best = r
    return best


def scan(nfa, source):
    """这就是 generator“生成”的扫描器:DFA 转移 + 最长匹配回退。
    返回 (tokens, errors)。tokens: (name, lexeme, pos)。errors: (pos, char)。"""
    start = _eps_closure(nfa, {nfa.start})
    tokens, errors = [], []
    i, N = 0, len(source)
    while i < N:
        cur, j, last = start, i, None        # last = (end_pos, (rule_idx, name))
        while True:
            r = _accept(nfa, cur)
            if r is not None:
                last = (j, r)                # 记下“到此为止能接受”——为最长匹配服务
            if j >= N:
                break
            nxt = _eps_closure(nfa, _move(nfa, cur, source[j]))
            if not nxt:                      # 走不动了
                break
            cur, j = nxt, j + 1
        if last is None:                     # ← generator 唯一的内建错误信号:no match
            errors.append((i, source[i]))
            i += 1                            # 跳一个字符“恢复”(它能做的全部)
        else:
            end, (_, name) = last
            tokens.append((name, source[i:end], i))
            i = end if end > i else i + 1
    return tokens, errors


# ════════════════════════════════════════════════════════════════════════
# 5. 试水:喂一份 CIE 伪代码 token 的 spec,看它怎么反应
# ════════════════════════════════════════════════════════════════════════
# 注意:**故意不放** ':=' / '!=' / '->' 这些“误用规则” —— 只定义合法 token,
# 模拟一个正常人写 generator 的做法(你只描述语言里合法的东西)。
SPEC = [
    ('WS',      r'[ \t]+'),
    ('NEWLINE', r'\n'),
    ('ASSIGN',  r'<-'),                 # 多字符:测 maximal munch
    ('LE',      r'<='),
    ('NE',      r'<>'),
    ('GE',      r'>='),
    ('LT',      r'<'),                  # 单字符前缀
    ('GT',      r'>'),
    ('EQ',      r'='),
    ('COLON',   r':'),
    ('PLUS',    r'\+'),
    ('MINUS',   r'-'),
    ('INT',     r'[0-9]+'),
    ('STRING',  r'"[^"]*"'),
    ('ID',      r'[A-Za-z][A-Za-z0-9_]*'),   # 关键字也先识别成 ID,再查表(Dragon Book 推荐)
]
KEYWORDS = {'IF', 'THEN', 'ENDIF', 'OUTPUT', 'DECLARE', 'INTEGER'}


def retag(tokens):
    """action 阶段:把恰好是关键字的 ID 重新打标 —— 一个 dict 查表就够,根本不需要 DFA。"""
    out = []
    for name, lex, pos in tokens:
        if name == 'ID' and lex.upper() in KEYWORDS:
            out.append((lex.upper(), lex, pos))
        else:
            out.append((name, lex, pos))
    return out


def show(title, source, nfa):
    toks, errs = scan(nfa, source)
    toks = [t for t in retag(toks) if t[0] not in ('WS', 'NEWLINE')]
    print(f"\n输入: {source!r}")
    print("  tokens:", "  ".join(f"{n}({l!r})" for n, l, _ in toks))
    if errs:
        for pos, ch in errs:
            print(f"  ERROR @ col{pos+1}: no match — unexpected character {ch!r}"
                  f"  (← generator 能说的全部:'有个字符我吃不下',没有意图)")
    else:
        print("  errors: (无 —— DFA 没有任何抱怨)")


if __name__ == '__main__':
    nfa = compile_spec(SPEC)
    print("=" * 72)
    print(f"  lexer generator 试水 —— NFA 状态数: {nfa.n} (由 {len(SPEC)} 条规则编译而来)")
    print("=" * 72)

    print("\n【场景 A】maximal munch 正常工作 —— 这是 generator 真实的优点:")
    print("  '<=' 不会被拆成 '<' '='、'<-' 不会被拆;DFA 自动取最长匹配,无需手工排序。")
    show("A", "IF x <= 10 THEN", nfa)
    show("A", "x <- 10", nfa)

    print("\n" + "-" * 72)
    print("【场景 B】':=' 误用 —— generator 在这里效果不好:")
    show("B", "x := 10", nfa)
    print("  ↑ ':=' 被静默拆成 COLON(':') + EQ('=') 两个合法 token,DFA 全程没报警。")
    print("    因为它的错误模型是 'no match',而 ':=' 恰好能被拆成两个有 match 的 token。")

    print("\n  对比:手写 / regex 版的 lexer 对同一输入的输出 ——")
    try:
        import regex_lexer
        _, e2 = regex_lexer.tokenizer("x := 10\n", [])
        for e in e2:
            for line in str(e).splitlines():
                print("   ", line)
    except Exception as ex:
        print("    (无法导入 regex_lexer:", ex, ")")

    print("\n" + "-" * 72)
    print("【场景 C】真正的 no-match —— generator 唯一会报的错:")
    show("C", "x <- 1 @ 2", nfa)
    print("  ↑ '@' 没有任何规则匹配 -> no match。这是 generator 内建错误信号的全部表达力:")
    print("    一个没有意图、只有位置的负信号。它没法说 '你是不是想用别的'。")
