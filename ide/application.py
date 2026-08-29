"""Application boundary between the browser IDE and the compiler engines.

This module deliberately owns the orchestration that neither the compiler nor
the completion model should know about: selecting the production corpus,
turning token-category predictions into source lexemes, and serialising
compiler diagnostics for a UI.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re
import time

from compiler import _detect_single_callable, compile_pseudocode
from errors import ErrorSeverity
from lexer import tokenizer
from tokens import KEYWORDS, Token, TokenType

# The completion engine is an EXPERIMENTAL research component and is not
# distributed with the public repository (its training corpus contains
# third-party copyrighted examination material that cannot be redistributed).
# When the package or its corpus is absent, the IDE runs in compiler-only
# mode: editing, diagnostics, compile and run all work; only ghost-text
# completion is disabled.
try:
    from completion_engine.corpus import dedupe_identical_streams, load_dir
    from completion_engine.layout_corpus import layout_example_streams
    from completion_engine.layout_model import END, NEWLINE, SAME_LINE, LayoutModel
    from completion_engine.ngram import NGramModel
    from completion_engine.service import (
        INSERT_NEWLINE,
        INSERT_TOKEN,
        NONE,
        CompletionService,
        RankedTokenCategory,
    )
    from completion_engine.vocab import SURFACE
    COMPLETION_ENGINE_AVAILABLE = True
except ImportError:
    COMPLETION_ENGINE_AVAILABLE = False
    # Action-kind constants mirrored from completion_engine.service so the
    # disabled-completion payload keeps the same wire format.
    INSERT_NEWLINE = "insert_newline"
    INSERT_TOKEN = "insert_token"
    NONE = "none"
from .runner import execute_python
from .workspace import (
    default_workspace,
    desktop_workspace,
    ensure_workspace,
    workspace_payload,
)


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RELEASE_GOLD = REPO_ROOT / "corpus_v2" / "release" / "gold"

# `official_guides` is the external-validation family in corpus v2.  A
# deployed model can use every approved model-source sample, including the
# former held-out papers, but must not silently train on its external test set.
MODEL_FAMILIES = frozenset({
    "igcse_0478_p2",
    "alevel_9618_p2",
    "alevel_9618_p3",
    # Empty in v2, but automatically becomes trainable once the reviewed
    # user-written family is present in a later release.
    "user_written",
})

MAX_SOURCE_CHARS = 250_000
_WORD_AT_CURSOR = re.compile(r"[A-Za-z_][A-Za-z0-9_]*$")

_OPEN_CLASS_LEXEMES = {
    "INTEGER_LITERAL": ("1",),
    "REAL_LITERAL": ("1.0",),
    "STRING_LITERAL": ('"text"',),
    "CHAR_LITERAL": ("'A'",),
    "BOOLEAN_LITERAL": ("TRUE", "FALSE"),
}

_BUILTIN_TYPES = ("INTEGER", "REAL", "STRING", "CHAR", "BOOLEAN", "DATE")
_TYPE_PRECEDERS = frozenset({
    TokenType.COLON,
    TokenType.KEYWORD_RETURNS,
    TokenType.KEYWORD_OF,
    TokenType.CARET,
})
_NEW_NAME_CONTEXTS = {
    TokenType.KEYWORD_DECLARE: "value",
    TokenType.KEYWORD_CONSTANT: "ConstantValue",
    TokenType.KEYWORD_FOR: "index",
    TokenType.KEYWORD_PROCEDURE: "ProcessData",
    TokenType.KEYWORD_FUNCTION: "Calculate",
    TokenType.KEYWORD_TYPE: "NewType",
    TokenType.KEYWORD_CLASS: "NewClass",
}
_NON_REUSABLE_BINDING_CONTEXTS = frozenset({
    TokenType.KEYWORD_DECLARE,
    TokenType.KEYWORD_CONSTANT,
    TokenType.KEYWORD_PROCEDURE,
    TokenType.KEYWORD_FUNCTION,
    TokenType.KEYWORD_TYPE,
    TokenType.KEYWORD_CLASS,
})

_HEADER_ONLY_ERRORS = frozenset({
    "Missing 'ENDIF'.",
    "Expected 'NEXT' but reached end of input.",
    "Expected 'ENDWHILE' but reached end of input.",
    "Expected 'UNTIL' but reached end of input.",
    "Expected 'ENDCASE' but reached end of input.",
    "Expected 'ENDPROCEDURE' but reached end of input.",
    "Expected 'ENDFUNCTION' but reached end of input.",
    "Expected 'ENDTYPE' but reached end of input.",
    "Expected 'ENDCLASS' but reached end of input.",
})
_COMPLETE_STANDALONE_TYPES = frozenset({
    TokenType.KEYWORD_ELSE,
    TokenType.KEYWORD_ENDIF,
    TokenType.KEYWORD_ENDWHILE,
    TokenType.KEYWORD_ENDCASE,
    TokenType.KEYWORD_ENDPROCEDURE,
    TokenType.KEYWORD_ENDFUNCTION,
    TokenType.KEYWORD_ENDTYPE,
    TokenType.KEYWORD_ENDCLASS,
})
_CONTINUATION_TAIL_TYPES = frozenset({
    TokenType.ASSIGN,
    TokenType.EQUALS,
    TokenType.NOT_EQUALS,
    TokenType.LESS_THAN,
    TokenType.LESS_EQUAL,
    TokenType.GREATER_THAN,
    TokenType.GREATER_EQUAL,
    TokenType.PLUS,
    TokenType.MINUS,
    TokenType.MULTIPLY,
    TokenType.DIVIDE,
    TokenType.AMPERSAND,
    TokenType.CARET,
    TokenType.KEYWORD_AND,
    TokenType.KEYWORD_OR,
    TokenType.KEYWORD_NOT,
    TokenType.KEYWORD_MOD,
    TokenType.KEYWORD_DIV,
    TokenType.KEYWORD_TO,
    TokenType.KEYWORD_STEP,
    TokenType.KEYWORD_RETURNS,
    TokenType.KEYWORD_OF,
    TokenType.KEYWORD_BYVAL,
    TokenType.KEYWORD_BYREF,
    TokenType.KEYWORD_INHERITS,
    TokenType.LPAREN,
    TokenType.LBRACKET,
    TokenType.COMMA,
    TokenType.DOT,
})

_OPERATORS = frozenset({
    "ASSIGN", "EQUALS", "NOT_EQUALS", "LESS_THAN", "LESS_EQUAL",
    "GREATER_THAN", "GREATER_EQUAL", "PLUS", "MINUS", "MULTIPLY",
    "DIVIDE", "AMPERSAND", "CARET", "KEYWORD_AND", "KEYWORD_OR",
    "KEYWORD_NOT", "KEYWORD_MOD", "KEYWORD_DIV",
})
_PUNCTUATION = frozenset({
    "LPAREN", "RPAREN", "LBRACKET", "RBRACKET", "COMMA", "COLON", "DOT",
})
_LINE_START_CATEGORIES = frozenset({
    "IDENTIFIER",
    "KEYWORD_DECLARE", "KEYWORD_CONSTANT", "KEYWORD_IF", "KEYWORD_FOR",
    "KEYWORD_WHILE", "KEYWORD_REPEAT", "KEYWORD_CASE", "KEYWORD_INPUT",
    "KEYWORD_OUTPUT", "KEYWORD_PRINT", "KEYWORD_CALL", "KEYWORD_RETURN",
    "KEYWORD_PROCEDURE", "KEYWORD_FUNCTION", "KEYWORD_TYPE",
    "KEYWORD_DEFINE", "KEYWORD_CLASS", "KEYWORD_ELSE", "KEYWORD_OTHERWISE",
    "KEYWORD_ENDIF", "KEYWORD_NEXT", "KEYWORD_ENDWHILE", "KEYWORD_UNTIL",
    "KEYWORD_ENDCASE", "KEYWORD_ENDPROCEDURE", "KEYWORD_ENDFUNCTION",
    "KEYWORD_ENDTYPE", "KEYWORD_ENDCLASS",
})

EXAMPLES = (
    {
        "name": "Running total",
        "nameZh": "累加",
        "nameZh": "累加",
        "code": """DECLARE total : INTEGER
DECLARE value : INTEGER
total <- 0

INPUT value
WHILE value <> -1
    total <- total + value
    INPUT value
ENDWHILE

OUTPUT total""",
    },
    {
        "name": "Count vowels",
        "nameZh": "数元音",
        "nameZh": "数元音",
        "code": """DECLARE text : STRING
DECLARE count : INTEGER
DECLARE index : INTEGER
text <- "PSEUDOCODE"
count <- 0

FOR index <- 1 TO LENGTH(text)
    IF MID(text, index, 1) = "A" OR MID(text, index, 1) = "E" THEN
        count <- count + 1
    ENDIF
NEXT index

OUTPUT count""",
    },
    {
        "name": "Maximum function",
        "nameZh": "最大值函数",
        "nameZh": "最大值函数",
        "code": """FUNCTION Maximum(a : INTEGER, b : INTEGER) RETURNS INTEGER
    IF a > b THEN
        RETURN a
    ELSE
        RETURN b
    ENDIF
ENDFUNCTION

OUTPUT Maximum(12, 7)""",
    },
    {
        "name": "Copy text file",
        "nameZh": "拷贝文本文件",
        "nameZh": "拷贝文本文件",
        "code": """DECLARE LineOfText : STRING
OPENFILE "FileA.txt" FOR READ
OPENFILE "FileB.txt" FOR WRITE
WHILE NOT EOF("FileA.txt")
    READFILE "FileA.txt", LineOfText
    IF LineOfText = "" THEN
        WRITEFILE "FileB.txt", " ----------------------------"
    ELSE
        WRITEFILE "FileB.txt", LineOfText
    ENDIF
ENDWHILE
CLOSEFILE "FileA.txt"
CLOSEFILE "FileB.txt"
OUTPUT "Copied FileA.txt to FileB.txt" """,
    },
)


@dataclass(frozen=True)
class ModelStats:
    release_files: int
    model_source_files: int
    lex_compatible_files: int
    unique_streams: int
    duplicate_streams_removed: int
    external_overlap_streams: int
    training_tokens: int
    layout_boundaries: int
    layout_same_line: int
    layout_newline: int
    layout_end: int
    corpus_path: str
    n: int
    alpha: float


class IDEApplication:
    """Long-lived compiler/completion service used by the HTTP layer."""

    def __init__(
        self,
        model: NGramModel | None = None,
        layout_model: LayoutModel | None = None,
        stats: ModelStats | None = None,
        workspace: Path | None = None,
    ) -> None:
        self.model = model
        self.layout_model = layout_model
        self.completion_available = (
            COMPLETION_ENGINE_AVAILABLE
            and model is not None
            and layout_model is not None
        )
        self.completion_service = (
            CompletionService(model, layout_model)
            if self.completion_available
            else None
        )
        self.stats = stats
        self.workspace = ensure_workspace(workspace or default_workspace())

    @classmethod
    def from_release(
        cls,
        gold_directory: str | Path = DEFAULT_RELEASE_GOLD,
        workspace: str | Path | None = None,
    ):
        gold = Path(gold_directory).resolve()
        if not COMPLETION_ENGINE_AVAILABLE or not gold.is_dir():
            # Compiler-only build: the experimental completion engine and its
            # training corpus are not distributed. Everything except
            # ghost-text completion stays fully functional.
            return cls(workspace=workspace)

        release_files = load_dir(str(gold))
        model_files = [
            file for file in release_files
            if _source_family(file.name) in MODEL_FAMILIES
        ]
        clean_files = [file for file in model_files if file.lexes_clean]
        unique_files, duplicates = dedupe_identical_streams(clean_files)
        if not unique_files:
            raise RuntimeError("the release contains no lex-compatible model samples")

        external_streams = {
            tuple(file.stream)
            for file in release_files
            if _source_family(file.name) == "official_guides" and file.lexes_clean
        }
        external_overlap_streams = sum(
            tuple(file.stream) in external_streams for file in unique_files
        )

        model = NGramModel(n=3, alpha=1.0)
        model.train(file.stream for file in unique_files)
        layout_streams = layout_example_streams(unique_files)
        layout_model = LayoutModel(n=3, alpha=1.0)
        layout_model.train(layout_streams)
        layout_labels = [
            example.label for stream in layout_streams for example in stream
        ]
        stats = ModelStats(
            release_files=len(release_files),
            model_source_files=len(model_files),
            lex_compatible_files=len(clean_files),
            unique_streams=len(unique_files),
            duplicate_streams_removed=len(duplicates),
            external_overlap_streams=external_overlap_streams,
            training_tokens=sum(len(file.tokens) for file in unique_files),
            layout_boundaries=len(layout_labels),
            layout_same_line=layout_labels.count(SAME_LINE),
            layout_newline=layout_labels.count(NEWLINE),
            layout_end=layout_labels.count(END),
            corpus_path=str(gold),
            n=model.n,
            alpha=model.alpha,
        )
        return cls(model, layout_model, stats, workspace=workspace)

    def health(self) -> dict:
        return {
            "status": "ok",
            "engine": (
                "hybrid3+layout3" if self.completion_available
                else "compiler-only"
            ),
            "completionAvailable": self.completion_available,
            "model": asdict(self.stats) if self.stats is not None else None,
        }

    def metadata(self) -> dict:
        return {
            **self.health(),
            "language": "CAIE 9618 pseudocode",
            "keywords": sorted(KEYWORDS),
            "examples": list(EXAMPLES),
            "workspace": workspace_payload(self.workspace),
            "shortcuts": {
                "compile": "Ctrl+Enter",
                "suggest": "Ctrl+Space",
                "accept": "Tab",
            },
        }

    def complete(
        self,
        source: str,
        cursor_offset: int | None = None,
        limit: int = 8,
    ) -> dict:
        source = _validate_source(source)
        if cursor_offset is None:
            cursor_offset = len(source)
        if isinstance(cursor_offset, bool) or not isinstance(cursor_offset, int):
            raise ValueError("cursorOffset must be an integer")
        if not 0 <= cursor_offset <= len(source):
            raise ValueError("cursorOffset is outside the source")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 30:
            raise ValueError("limit must be an integer between 1 and 30")

        started = time.perf_counter()
        if not self.completion_available:
            return self._completion_payload(
                [], started,
                fallback="completion_disabled",
                reason="experimental completion engine not distributed "
                       "in this build",
            )
        if _has_existing_source_suffix(source, cursor_offset):
            return self._completion_payload(
                [], started, fallback="editing_existing_text")
        prefix = source[:cursor_offset]
        if _cursor_is_in_comment(prefix):
            return self._completion_payload([], started, fallback="inside_comment")
        if _in_file_operation_context(prefix):
            return self._completion_payload(
                [], started, fallback="file_operation")

        tokens, lexical_errors = _tokenize_prefix(prefix)
        if tokens and tokens[-1].type == TokenType.UNKNOWN:
            return self._completion_payload([], started, fallback="incomplete_lexeme")

        fragment_match = _WORD_AT_CURSOR.search(prefix)
        fragment = fragment_match.group(0) if fragment_match else ""
        recent_identifiers = _recent_value_identifiers(tokens)
        context_prefix = prefix[:-len(fragment)] if fragment else prefix
        context_tokens, _ = _tokenize_prefix(context_prefix)
        type_identifiers = []
        if context_tokens and context_tokens[-1].type in _TYPE_PRECEDERS:
            type_identifiers = _recent_type_identifiers(context_tokens)
        reusable_identifiers = (
            [] if _is_new_binding_context(context_tokens)
            else recent_identifiers
        )
        partial_lexemes = _matching_partial_lexemes(
            fragment,
            reusable_identifiers,
            type_identifiers,
        )

        # A fragment such as DEC is a current-token completion, not the next
        # token after an identifier.  Remove it from the context before asking
        # the category model, then rank matching source lexemes by that result.
        if partial_lexemes:
            ranked = self._rank_categories(context_tokens, context_prefix)
            by_name = {item.name: item for item in ranked}
            rank_index = {item.name: index for index, item in enumerate(ranked)}
            partial_lexemes.sort(
                key=lambda pair: (rank_index.get(pair[1], 10_000), pair[0].upper())
            )
            items = []
            for lexeme, token_name in partial_lexemes[:limit]:
                category = by_name.get(token_name)
                # In a valid context the parser is the authority for a
                # current-token replacement.  Without this guard,
                # `DECLARE co` offered illegal CONSTANT and replaced a valid
                # identifier prefix when Tab was pressed.
                if category is None or category.legal is False:
                    continue
                items.append(_suggestion(
                    label=lexeme,
                    insert_text=lexeme,
                    token_name=token_name,
                    probability=category.probability,
                    legal=category.legal,
                    replace_start=cursor_offset - len(fragment),
                    replace_end=cursor_offset,
                    partial=True,
                    surface_source=_partial_surface_source(
                        lexeme,
                        token_name,
                        reusable_identifiers,
                        type_identifiers,
                    ),
                ))
            if items:
                return self._completion_payload(
                    items,
                    started,
                    fallback="lexical_prefix",
                    lexical_errors=lexical_errors,
                )

        allow_layout = (
            bool(tokens)
            and not _at_line_start(prefix)
            and not _line_is_explicitly_incomplete(prefix)
        )
        decision = self.completion_service.decide(
            tokens,
            allow_layout=allow_layout,
            force_newline=allow_layout and _line_is_complete_statement(prefix),
        )
        if decision.kind == INSERT_NEWLINE:
            newline_text = "\n" + _indent_after_newline(prefix)
            item = {
                "label": "\u21b5 New line",
                "insertText": newline_text,
                "filterText": "new line",
                "tokenType": None,
                "kind": "layout",
                "probability": round(decision.confidence, 8),
                "legal": None,
                "replaceStart": cursor_offset,
                "replaceEnd": cursor_offset,
                "partial": False,
                "actionKind": INSERT_NEWLINE,
                "decisionSource": decision.reason,
                "surfaceSource": "layout_action",
            }
            return self._completion_payload(
                [item],
                started,
                fallback=None,
                lexical_errors=lexical_errors,
                action_kind=INSERT_NEWLINE,
                layout_scores=decision.layout_scores,
                reason=decision.reason,
            )
        if decision.kind == NONE:
            return self._completion_payload(
                [],
                started,
                fallback="end_of_sample",
                lexical_errors=lexical_errors,
                action_kind=NONE,
                layout_scores=decision.layout_scores,
                reason=decision.reason,
            )

        ranked = self._order_categories_for_line_start(
            list(decision.categories), prefix)
        items = []
        for category in ranked:
            for lexeme in _source_lexemes(category.name, recent_identifiers, tokens):
                items.append(_suggestion(
                    label=lexeme,
                    insert_text=_format_next_lexeme(prefix, category.name, lexeme),
                    token_name=category.name,
                    probability=category.probability,
                    legal=category.legal,
                    replace_start=cursor_offset,
                    replace_end=cursor_offset,
                    partial=False,
                    surface_source=_token_surface_source(
                        category.name,
                        lexeme,
                        recent_identifiers,
                        tokens,
                    ),
                ))
                if len(items) >= limit:
                    break
            if len(items) >= limit:
                break

        return self._completion_payload(
            items,
            started,
            fallback="ngram_only" if lexical_errors else None,
            lexical_errors=lexical_errors,
            action_kind=INSERT_TOKEN if items else NONE,
            layout_scores=decision.layout_scores,
            reason=decision.reason,
        )

    def compile(self, source: str) -> dict:
        result, _ast = self._compile_with_ast(source)
        return result

    def _compile_with_ast(self, source: str) -> tuple[dict, object | None]:
        source = _validate_source(source)
        started = time.perf_counter()
        try:
            tokens, ast, python_code, errors = compile_pseudocode(source)
        except Exception as exc:  # User input must not take down the IDE server.
            return {
                "ok": False,
                "python": "",
                "diagnostics": [{
                    "severity": "error",
                    "line": 1,
                    "column": 1,
                    "endColumn": 2,
                    "message": f"Compiler failed safely: {type(exc).__name__}: {exc}",
                    "suggestion": "Reduce the input to a minimal example and inspect it.",
                    "sourceLine": None,
                }],
                "tokens": [],
                "elapsedMs": round((time.perf_counter() - started) * 1000, 2),
                "internalFailure": True,
            }, None

        diagnostics = [_serialise_error(error) for error in errors]
        has_error = any(error.severity == ErrorSeverity.ERROR for error in errors)
        return {
            "ok": ast is not None and not has_error,
            "python": python_code,
            "diagnostics": diagnostics,
            "tokens": [
                {
                    "type": token.type.name,
                    "value": token.value,
                    "line": token.line,
                    "column": token.column,
                }
                for token in tokens
                if token.type not in (TokenType.EOF, TokenType.COMMENT)
            ],
            "elapsedMs": round((time.perf_counter() - started) * 1000, 2),
            "internalFailure": False,
        }, ast

    def run(self, source: str, stdin: str = "") -> dict:
        """Compile pseudocode, then execute its Python in a bounded child.

        Compilation always happens first.  Any compiler error is returned to
        the caller without starting a Python process, preserving the compiler
        as the single source of diagnostic truth.
        """
        started = time.perf_counter()
        compilation, ast = self._compile_with_ast(source)
        entrypoint = (
            _serialise_entrypoint(_detect_single_callable(ast))
            if compilation["ok"] else None
        )
        base_result = {
            "python": compilation["python"],
            "diagnostics": compilation["diagnostics"],
            "tokens": compilation["tokens"],
            "entrypoint": entrypoint,
        }
        if not compilation["ok"]:
            return {
                "ok": False,
                "stdout": "",
                "stderr": "",
                "exitCode": None,
                "timedOut": False,
                "truncated": False,
                "elapsedMs": round((time.perf_counter() - started) * 1000, 2),
                "internalFailure": compilation["internalFailure"],
                **base_result,
            }

        try:
            execution = execute_python(
                compilation["python"],
                stdin,
                entrypoint=entrypoint,
                workspace=self.workspace,
            )
        except ValueError:
            # Invalid API data (most commonly an oversized stdin value) is a
            # client error and is converted to HTTP 400 by the server layer.
            raise
        except Exception as exc:
            # A missing/interrupted child runtime must not take down the
            # long-lived IDE server.
            return {
                "ok": False,
                "stdout": "",
                "stderr": (
                    f"Runner failed safely: {type(exc).__name__}: {exc}"
                ),
                "exitCode": None,
                "timedOut": False,
                "truncated": False,
                "elapsedMs": round((time.perf_counter() - started) * 1000, 2),
                "internalFailure": True,
                **base_result,
            }

        execution["elapsedMs"] = round(
            (time.perf_counter() - started) * 1000, 2)
        return {
            "ok": (
                not execution["timedOut"]
                and execution["exitCode"] == 0
            ),
            **execution,
            "internalFailure": False,
            "workspace": workspace_payload(self.workspace),
            **base_result,
        }

    def set_workspace(self, path: str | Path, create: bool = True) -> dict:
        if not isinstance(path, (str, Path)) or not str(path).strip():
            raise ValueError("workspace path is required")
        folder = Path(path).expanduser()
        if create:
            self.workspace = ensure_workspace(folder)
        else:
            folder = folder.resolve()
            if not folder.is_dir():
                raise ValueError("workspace folder does not exist")
            self.workspace = folder
        return workspace_payload(self.workspace)

    def _rank_categories(
        self,
        tokens: list[Token],
        prefix: str,
    ) -> list[RankedTokenCategory]:
        decision = self.completion_service.decide(tokens, allow_layout=False)
        return self._order_categories_for_line_start(
            list(decision.categories), prefix)

    @staticmethod
    def _order_categories_for_line_start(
        categories: list[RankedTokenCategory],
        prefix: str,
    ) -> list[RankedTokenCategory]:
        if _at_line_start(prefix):
            line_starters = [
                item for item in categories
                if item.name in _LINE_START_CATEGORIES
            ]
            if line_starters:
                return line_starters + [
                    item for item in categories
                    if item.name not in _LINE_START_CATEGORIES
                ]
        return categories

    def _completion_payload(
        self,
        items: list[dict],
        started: float,
        fallback: str | None,
        lexical_errors: list | None = None,
        action_kind: str | None = None,
        layout_scores: dict | None = None,
        reason: str | None = None,
    ) -> dict:
        if action_kind is None:
            action_kind = INSERT_TOKEN if items else NONE
        first = items[0] if items else None
        return {
            "items": items,
            "action": {
                "kind": action_kind,
                "text": first["insertText"] if first else "",
                "tokenType": first["tokenType"] if first else None,
                "confidence": first["probability"] if first else 0.0,
                "reason": reason or fallback,
            },
            "engine": (
                "hybrid3+layout3" if self.completion_available
                else "compiler-only"
            ),
            "fallback": fallback,
            "layoutScores": layout_scores or {},
            "lexicalErrorCount": len(lexical_errors or []),
            "elapsedMs": round((time.perf_counter() - started) * 1000, 2),
        }


def _source_family(name: str) -> str:
    return name.split("--", 1)[0]


def _validate_source(source) -> str:
    if not isinstance(source, str):
        raise ValueError("source must be a string")
    if len(source) > MAX_SOURCE_CHARS:
        raise ValueError(f"source exceeds the {MAX_SOURCE_CHARS:,}-character limit")
    return source


def _tokenize_prefix(prefix: str) -> tuple[list[Token], list]:
    errors = []
    tokens, _ = tokenizer(prefix, errors)
    real = [
        token for token in tokens
        if token.type not in (TokenType.EOF, TokenType.COMMENT)
    ]
    return real, errors


def _recent_value_identifiers(tokens: list[Token]) -> list[str]:
    """Identifiers usable as values, excluding type-position identifiers.

    The compiler intentionally tokenises names such as INTEGER and custom
    types as IDENTIFIER.  A UI cannot therefore equate every IDENTIFIER token
    with a variable to reuse in an expression.
    """
    seen = set()
    result = []
    for index in range(len(tokens) - 1, -1, -1):
        token = tokens[index]
        if token.type != TokenType.IDENTIFIER:
            continue
        value = str(token.value)
        previous = tokens[index - 1].type if index else None
        if value.upper() in _BUILTIN_TYPES:
            continue
        if previous in _TYPE_PRECEDERS or previous == TokenType.KEYWORD_TYPE:
            continue
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result


def _recent_type_identifiers(tokens: list[Token]) -> list[str]:
    seen = set()
    result = []
    for index in range(len(tokens) - 1, -1, -1):
        token = tokens[index]
        if token.type != TokenType.IDENTIFIER:
            continue
        previous = tokens[index - 1].type if index else None
        value = str(token.value)
        if previous not in _TYPE_PRECEDERS and previous != TokenType.KEYWORD_TYPE:
            continue
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            result.append(value)
    for value in _BUILTIN_TYPES:
        if value.casefold() not in seen:
            result.append(value)
    return result


def _matching_partial_lexemes(
    fragment: str,
    recent_identifiers: list[str],
    type_identifiers: list[str] | tuple[str, ...] = (),
) -> list[tuple[str, str]]:
    if not fragment:
        return []
    upper = fragment.upper()
    matches = [
        (word, token_type.name)
        for word, token_type in KEYWORDS.items()
        if word.startswith(upper) and word != upper
    ]
    matches.extend(
        (identifier, "IDENTIFIER")
        for identifier in recent_identifiers
        if identifier.casefold().startswith(fragment.casefold())
        and identifier.casefold() != fragment.casefold()
    )
    matches.extend(
        (identifier, "IDENTIFIER")
        for identifier in type_identifiers
        if identifier.casefold().startswith(fragment.casefold())
        and identifier.casefold() != fragment.casefold()
    )
    # Preserve ranking inputs while preventing the same lexeme from being
    # emitted twice when it appears in both history and the builtin fallback.
    seen = set()
    unique = []
    for lexeme, token_name in matches:
        key = (lexeme.casefold(), token_name)
        if key not in seen:
            seen.add(key)
            unique.append((lexeme, token_name))
    return unique


def _source_lexemes(
    token_name: str,
    recent_identifiers: list[str],
    tokens: list[Token] | tuple[Token, ...] = (),
) -> tuple[str, ...]:
    if token_name == "IDENTIFIER":
        previous_type = tokens[-1].type if tokens else None
        if previous_type in _TYPE_PRECEDERS:
            types = _recent_type_identifiers(list(tokens))
            return (types[0],) if types else ("INTEGER",)
        if previous_type in _NEW_NAME_CONTEXTS:
            return (_NEW_NAME_CONTEXTS[previous_type],)
        if _expects_parameter_name(tokens):
            return ("value",)
        return (recent_identifiers[0],) if recent_identifiers else ("value",)
    if token_name in _OPEN_CLASS_LEXEMES:
        return _OPEN_CLASS_LEXEMES[token_name]
    token_type = TokenType[token_name]
    return (str(SURFACE[token_type]),)


def _format_next_lexeme(prefix: str, token_name: str, lexeme: str) -> str:
    if token_name == "COMMA":
        return ", "
    if token_name == "COLON":
        return ": "
    if token_name in {"DOT", "RPAREN", "RBRACKET"}:
        return lexeme
    if token_name in {"LPAREN", "LBRACKET"}:
        return lexeme

    needs_leading_space = bool(prefix) and not prefix[-1].isspace() and prefix[-1] not in "([."
    leading = " " if needs_leading_space else ""
    trailing = " " if token_name in _OPERATORS else ""
    return f"{leading}{lexeme}{trailing}"


def _expects_parameter_name(tokens: list[Token] | tuple[Token, ...]) -> bool:
    """True at the first/next parameter slot of a callable definition."""
    if not tokens or tokens[-1].type not in {TokenType.LPAREN, TokenType.COMMA}:
        return False
    depth = 0
    opener = None
    for index in range(len(tokens) - 1, -1, -1):
        token_type = tokens[index].type
        if token_type == TokenType.RPAREN:
            depth += 1
        elif token_type == TokenType.LPAREN:
            if depth == 0:
                opener = index
                break
            depth -= 1
    if opener is None or opener < 2:
        return False
    return (
        tokens[opener - 1].type == TokenType.IDENTIFIER
        and tokens[opener - 2].type
        in {TokenType.KEYWORD_FUNCTION, TokenType.KEYWORD_PROCEDURE}
    )


def _is_new_binding_context(tokens: list[Token] | tuple[Token, ...]) -> bool:
    if not tokens:
        return False
    return (
        tokens[-1].type in _NON_REUSABLE_BINDING_CONTEXTS
        or _expects_parameter_name(tokens)
    )


def _line_is_complete_statement(prefix: str) -> bool:
    """Conservative deterministic sentence-boundary check.

    Simple statements are parsed in isolation. Container headers are accepted
    only when the compiler's sole ERROR is the expected missing block closer.
    CompletionService uses this signal to promote NEWLINE over semantic-token
    continuations, but only when the independent layout model clears its
    minimum support floor.  That avoids treating every extensible expression
    prefix as a finished line.
    """
    line = prefix.rsplit("\n", 1)[-1].strip()
    if not line:
        return False
    line_tokens, _ = _tokenize_prefix(line)
    if not line_tokens:
        return False

    first = line_tokens[0].type
    if first in _COMPLETE_STANDALONE_TYPES and len(line_tokens) == 1:
        return True
    if (
        first == TokenType.KEYWORD_NEXT
        and len(line_tokens) == 2
        and line_tokens[1].type == TokenType.IDENTIFIER
    ):
        return True
    if first == TokenType.KEYWORD_OTHERWISE:
        return line_tokens[-1].type == TokenType.COLON
    if first == TokenType.KEYWORD_UNTIL:
        _tokens, ast, _python, _errors = compile_pseudocode(
            "REPEAT\n    OUTPUT 0\n" + line)
        return ast is not None

    _tokens, ast, _python, errors = compile_pseudocode(line)
    if ast is not None:
        return True
    hard_errors = [
        error.message for error in errors
        if error.severity == ErrorSeverity.ERROR
    ]
    return len(hard_errors) == 1 and hard_errors[0] in _HEADER_ONLY_ERRORS


def _line_is_explicitly_incomplete(prefix: str) -> bool:
    """Reject layout actions at boundaries that structurally require a token.

    Layout trigrams see only the final two categories, so an incomplete
    ``FOR i <- 1`` can resemble the end of an assignment and an unfinished
    function parameter can resemble a complete declaration.  These are not
    ambiguous sentence ends: the current construct itself proves that more
    same-line syntax is required.
    """
    line = prefix.rsplit("\n", 1)[-1]
    line_tokens, _ = _tokenize_prefix(line)
    if not line_tokens:
        return False
    types = [token.type for token in line_tokens]
    first = types[0]

    paren_depth = 0
    bracket_depth = 0
    for token_type in types:
        if token_type == TokenType.LPAREN:
            paren_depth += 1
        elif token_type == TokenType.RPAREN:
            paren_depth -= 1
        elif token_type == TokenType.LBRACKET:
            bracket_depth += 1
        elif token_type == TokenType.RBRACKET:
            bracket_depth -= 1
    if paren_depth > 0 or bracket_depth > 0:
        return True
    if types[-1] in _CONTINUATION_TAIL_TYPES:
        return True

    if first == TokenType.KEYWORD_IF:
        return TokenType.KEYWORD_THEN not in types
    if first == TokenType.KEYWORD_FOR:
        to_index = next(
            (index for index, value in enumerate(types)
             if value == TokenType.KEYWORD_TO),
            None,
        )
        return to_index is None or to_index == len(types) - 1
    if first == TokenType.KEYWORD_CASE:
        return (
            TokenType.KEYWORD_OF not in types
            or types[-1] == TokenType.KEYWORD_OF
        )
    if first == TokenType.KEYWORD_DECLARE:
        colon_index = next(
            (index for index, value in enumerate(types)
             if value == TokenType.COLON),
            None,
        )
        return colon_index is None or colon_index == len(types) - 1
    if first == TokenType.KEYWORD_CONSTANT:
        equals_index = next(
            (index for index, value in enumerate(types)
             if value == TokenType.EQUALS),
            None,
        )
        return equals_index is None or equals_index == len(types) - 1
    if first in {TokenType.KEYWORD_PROCEDURE, TokenType.KEYWORD_FUNCTION}:
        if TokenType.LPAREN not in types or TokenType.RPAREN not in types:
            return True
        if first == TokenType.KEYWORD_FUNCTION:
            returns_index = next(
                (index for index, value in enumerate(types)
                 if value == TokenType.KEYWORD_RETURNS),
                None,
            )
            return returns_index is None or returns_index == len(types) - 1
    if first == TokenType.KEYWORD_DEFINE:
        colon_index = next(
            (index for index, value in enumerate(types)
             if value == TokenType.COLON),
            None,
        )
        return colon_index is None or colon_index == len(types) - 1
    if first == TokenType.KEYWORD_OTHERWISE:
        return types[-1] != TokenType.COLON
    return False


def _indent_after_newline(prefix: str) -> str:
    line = prefix.rsplit("\n", 1)[-1]
    leading = re.match(r"[ \t]*", line).group(0)
    line_tokens, _ = _tokenize_prefix(line)
    if not line_tokens:
        return leading
    types = [token.type for token in line_tokens]
    first = types[0]
    opens_block = (
        (first == TokenType.KEYWORD_IF and types[-1] == TokenType.KEYWORD_THEN)
        or first in {
            TokenType.KEYWORD_FOR,
            TokenType.KEYWORD_WHILE,
            TokenType.KEYWORD_REPEAT,
            TokenType.KEYWORD_CASE,
            TokenType.KEYWORD_PROCEDURE,
            TokenType.KEYWORD_FUNCTION,
            TokenType.KEYWORD_CLASS,
            TokenType.KEYWORD_ELSE,
        }
        or (
            first == TokenType.KEYWORD_TYPE
            and TokenType.EQUALS not in types
        )
        or (
            first == TokenType.KEYWORD_OTHERWISE
            and types[-1] == TokenType.COLON
        )
    )
    return leading + ("    " if opens_block else "")


def _suggestion(
    *,
    label: str,
    insert_text: str,
    token_name: str,
    probability: float,
    legal: bool | None,
    replace_start: int,
    replace_end: int,
    partial: bool,
    surface_source: str = "fixed_token",
) -> dict:
    return {
        "label": label,
        "insertText": insert_text,
        "filterText": label,
        "tokenType": token_name,
        "kind": _completion_kind(token_name),
        "probability": round(probability, 8),
        "legal": legal,
        "replaceStart": replace_start,
        "replaceEnd": replace_end,
        "partial": partial,
        "actionKind": INSERT_TOKEN,
        "decisionSource": "token_category",
        "surfaceSource": surface_source,
    }


def _partial_surface_source(
    lexeme: str,
    token_name: str,
    recent_identifiers: list[str],
    type_identifiers: list[str],
) -> str:
    if token_name.startswith("KEYWORD_"):
        return "keyword_prefix"
    folded = lexeme.casefold()
    if any(value.casefold() == folded for value in type_identifiers):
        return "type_prefix"
    if any(value.casefold() == folded for value in recent_identifiers):
        return "document_identifier"
    return "lexical_prefix"


def _token_surface_source(
    token_name: str,
    lexeme: str,
    recent_identifiers: list[str],
    tokens: list[Token],
) -> str:
    if token_name != "IDENTIFIER":
        return "canonical_literal" if token_name.endswith("_LITERAL") else "fixed_token"
    previous_type = tokens[-1].type if tokens else None
    if previous_type in _TYPE_PRECEDERS:
        return "type_context"
    if previous_type in _NEW_NAME_CONTEXTS or _expects_parameter_name(tokens):
        return "placeholder"
    if any(value.casefold() == lexeme.casefold() for value in recent_identifiers):
        return "document_identifier"
    return "placeholder"


def _completion_kind(token_name: str) -> str:
    if token_name == "IDENTIFIER":
        return "identifier"
    if token_name.endswith("_LITERAL"):
        return "literal"
    if token_name in _PUNCTUATION:
        return "punctuation"
    if token_name in _OPERATORS:
        return "operator"
    if token_name.startswith("KEYWORD_"):
        return "keyword"
    return "text"


def _serialise_entrypoint(callable_info) -> dict | None:
    if not callable_info:
        return None
    return {
        "name": callable_info["name"],
        "kind": (
            "function" if callable_info["is_function"] else "procedure"
        ),
        "parameters": [
            {
                "name": parameter["name"],
                "type": parameter.get("type", "STRING"),
                "passBy": parameter.get("pass_by", "BYVAL"),
            }
            for parameter in callable_info["params"]
        ],
        "returnType": callable_info["return_type"],
    }


def _serialise_error(error) -> dict:
    line = max(1, int(error.line or 1))
    column = max(1, int(error.column or 1))
    return {
        "severity": error.severity.value.lower(),
        "line": line,
        "column": column,
        "endColumn": column + 1,
        "message": error.message,
        "suggestion": error.suggestion,
        "sourceLine": error.source_line,
    }


def _at_line_start(prefix: str) -> bool:
    return not prefix.rsplit("\n", 1)[-1].strip()


_FILE_OPERATION_KEYWORDS = (
    "OPENFILE",
    "READFILE",
    "WRITEFILE",
    "CLOSEFILE",
    "SEEK",
    "GETRECORD",
    "PUTRECORD",
    "EOF",
)
_FILE_OPERATION_WORD = re.compile(
    r"(?<![A-Za-z0-9_])("
    + "|".join(_FILE_OPERATION_KEYWORDS)
    + r")(?![A-Za-z0-9_])",
    re.IGNORECASE,
)
_LEADING_WORD = re.compile(r"\s*([A-Za-z_][A-Za-z0-9_]*)")


def _code_before_comment(line: str) -> str:
    in_double = False
    in_single = False
    index = 0
    while index < len(line):
        char = line[index]
        if char == '"' and not in_single:
            in_double = not in_double
        elif char in {"'", "\u2018", "\u2019"} and not in_double:
            in_single = not in_single
        elif (
            char == "/"
            and index + 1 < len(line)
            and line[index + 1] == "/"
            and not in_double
            and not in_single
        ):
            return line[:index]
        index += 1
    return line


def _in_file_operation_context(prefix: str) -> bool:
    """File I/O is sparse in the training corpus, so the n-gram guesses OOD."""
    line = _code_before_comment(prefix.rsplit("\n", 1)[-1])
    if _FILE_OPERATION_WORD.search(line):
        return True
    match = _LEADING_WORD.match(line)
    if not match:
        return False
    word = match.group(1).upper()
    if len(word) < 3:
        return False
    return any(keyword.startswith(word) for keyword in _FILE_OPERATION_KEYWORDS)


def _cursor_is_in_comment(prefix: str) -> bool:
    line = prefix.rsplit("\n", 1)[-1]
    in_double = False
    in_single = False
    index = 0
    while index < len(line):
        char = line[index]
        if char == '"' and not in_single:
            in_double = not in_double
        elif char in {"'", "\u2018", "\u2019"} and not in_double:
            in_single = not in_single
        elif char == "/" and index + 1 < len(line) and line[index + 1] == "/":
            return not in_double and not in_single
        index += 1
    return False


def _has_existing_source_suffix(source: str, cursor_offset: int) -> bool:
    """Only autocomplete before trailing whitespace, never before real code.

    A conventional final newline (or blank lines at EOF) is still the live
    document frontier.  Only a non-whitespace suffix proves that the cursor is
    revising existing source.
    """
    return bool(source[cursor_offset:].strip())
