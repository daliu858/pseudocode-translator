/* CAIE 9618 block indent helpers shared by Monaco and the textarea fallback. */
(function (root, factory) {
  const api = factory();
  root.PseudocodeIndent = api;
  if (typeof module === "object" && module.exports) {
    module.exports = api;
  }
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  // Trailing `//` comments are allowed. OTHERWISE is not a block opener here:
  // treating it like ELSE would leave ENDCASE one level too deep.
  const INCREASE_SOURCE =
    "^\\s*(?:IF\\b.*\\bTHEN|THEN|ELSE|FOR\\b.*|WHILE\\b.*|REPEAT\\b.*|CASE\\b.*|PROCEDURE\\b.*|FUNCTION\\b.*|TYPE\\b(?!\\s+\\w+\\s*=).*|CLASS\\b.*)(?:\\s*\\/\\/.*)?\\s*$";
  const DECREASE_SOURCE =
    "^\\s*(?:ELSE|ENDIF|NEXT|ENDWHILE|UNTIL|ENDCASE|ENDPROCEDURE|ENDFUNCTION|ENDTYPE|ENDCLASS)\\b";
  const INDENT_NEXT_SOURCE =
    "^\\s*OTHERWISE\\b\\s*:?\\s*(?:\\/\\/.*)?\\s*$";

  const UNIT = "    ";

  function increaseIndentPattern() {
    return new RegExp(INCREASE_SOURCE, "i");
  }

  function decreaseIndentPattern() {
    return new RegExp(DECREASE_SOURCE, "i");
  }

  function indentNextLinePattern() {
    return new RegExp(INDENT_NEXT_SOURCE, "i");
  }

  function stripEol(line) {
    return String(line || "").replace(/\r$/, "");
  }

  function leadingWhitespace(line) {
    const match = stripEol(line).match(/^[ \t]*/);
    return match ? match[0] : "";
  }

  function opensBlock(line) {
    return increaseIndentPattern().test(stripEol(line));
  }

  function isDedentLine(line) {
    return decreaseIndentPattern().test(stripEol(line));
  }

  function indentAfterLine(line) {
    const leading = leadingWhitespace(line);
    if (opensBlock(line) || indentNextLinePattern().test(stripEol(line))) {
      return leading + UNIT;
    }
    return leading;
  }

  function reindent(source) {
    const text = String(source || "");
    const eol = text.includes("\r\n") ? "\r\n" : "\n";
    const lines = text.split(/\r?\n/);
    let level = 0;
    const out = [];
    for (const line of lines) {
      if (!stripEol(line).trim()) {
        out.push("");
        continue;
      }
      if (isDedentLine(line)) {
        level = Math.max(0, level - 1);
      }
      out.push(UNIT.repeat(level) + stripEol(line).trimStart());
      if (opensBlock(line)) {
        level += 1;
      }
    }
    return out.join(eol);
  }

  return {
    UNIT,
    INCREASE_SOURCE,
    DECREASE_SOURCE,
    INDENT_NEXT_SOURCE,
    increaseIndentPattern,
    decreaseIndentPattern,
    indentNextLinePattern,
    leadingWhitespace,
    opensBlock,
    isDedentLine,
    indentAfterLine,
    reindent,
  };
});

if (typeof require !== "undefined" && typeof module !== "undefined" && require.main === module) {
  const assert = require("assert");
  const indent = module.exports;

  function assertOpen(line) {
    assert.ok(indent.opensBlock(line), `expected opener: ${JSON.stringify(line)}`);
  }
  function assertNotOpen(line) {
    assert.ok(!indent.opensBlock(line), `expected not opener: ${JSON.stringify(line)}`);
  }

  assertOpen("IF x > 0 THEN");
  assertOpen("IF x > 0 THEN // comment");
  assertOpen("THEN");
  assertOpen("ELSE");
  assertOpen("WHILE value <> -1");
  assertOpen("FOR i <- 1 TO 10");
  assertOpen("REPEAT");
  assertOpen("CASE OF colour");
  assertOpen("PROCEDURE Foo()");
  assertOpen("FUNCTION Bar() RETURNS INTEGER");
  assertOpen("TYPE Student");
  assertOpen("CLASS Foo");
  assertNotOpen("OTHERWISE");
  assertNotOpen("OTHERWISE :");

  assertNotOpen("IF x > 0");
  assertNotOpen("IF x > 0 THEN OUTPUT 1");
  assertNotOpen("DECLARE total : INTEGER");
  assertNotOpen("TYPE Score = INTEGER");
  assertNotOpen("OPENFILE \"data.txt\" FOR READ");
  assertNotOpen("OUTPUT total");
  assert.ok(!indent.opensBlock("OTHERWISE : OUTPUT \"x\""));
  assert.ok(indent.indentNextLinePattern().test("OTHERWISE :"));
  assert.ok(indent.indentNextLinePattern().test("    OTHERWISE"));
  assert.ok(!indent.indentNextLinePattern().test("OTHERWISE : OUTPUT \"x\""));
  assertNotOpen("ENDIF");

  assert.ok(indent.isDedentLine("ENDIF"));
  assert.ok(indent.isDedentLine("    ENDWHILE"));
  assert.ok(indent.isDedentLine("NEXT i"));
  assert.ok(indent.isDedentLine("ELSE"));
  assert.ok(!indent.isDedentLine("WHILE x"));

  assert.strictEqual(indent.indentAfterLine("WHILE x"), "    ");
  assert.strictEqual(indent.indentAfterLine("    IF x THEN"), "        ");
  assert.strictEqual(indent.indentAfterLine("    OUTPUT x"), "    ");

  const messy = [
    "DECLARE total : INTEGER",
    "WHILE value <> -1",
    "total <- total + value",
    "IF total > 10 THEN",
    "OUTPUT total",
    "ELSE",
    "OUTPUT 0",
    "ENDIF",
    "ENDWHILE",
  ].join("\n");

  assert.strictEqual(
    indent.reindent(messy),
    [
      "DECLARE total : INTEGER",
      "WHILE value <> -1",
      "    total <- total + value",
      "    IF total > 10 THEN",
      "        OUTPUT total",
      "    ELSE",
      "        OUTPUT 0",
      "    ENDIF",
      "ENDWHILE",
    ].join("\n"),
  );

  const already = [
    "WHILE value <> -1",
    "    total <- total + value",
    "    INPUT value",
    "ENDWHILE",
  ].join("\n");
  assert.strictEqual(indent.reindent(already), already);

  const thenSplit = indent.reindent("IF x > 0\nTHEN\nOUTPUT x\nENDIF");
  assert.strictEqual(thenSplit, "IF x > 0\nTHEN\n    OUTPUT x\nENDIF");

  const caseBlock = indent.reindent([
    "CASE OF colour",
    "\"Red\" : OUTPUT 1",
    "OTHERWISE :",
    "OUTPUT 2",
    "ENDCASE",
  ].join("\n"));
  assert.strictEqual(
    caseBlock,
    [
      "CASE OF colour",
      "    \"Red\" : OUTPUT 1",
      "    OTHERWISE :",
      "    OUTPUT 2",
      "ENDCASE",
    ].join("\n"),
  );

  assert.strictEqual(indent.indentAfterLine("    OTHERWISE :"), "        ");

  console.log("indent.js ok");
}
