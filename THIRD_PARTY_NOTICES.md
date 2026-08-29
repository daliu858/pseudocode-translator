# Third-Party Notices and Dependency Boundaries

This file records third-party packages loaded by the IDE or referenced by
repository tooling. Runtime and research-tool dependencies are separated below.
It does not change the licence of this project's original source code and does
not, by itself, establish compliance with every third-party licence.

## IDE runtime dependency

### Monaco Editor 0.55.1

- Project: <https://github.com/microsoft/monaco-editor/tree/v0.55.1>
- Loaded by: `ide/static/app.js`, from jsDelivr at runtime
- License: MIT
- Version-specific license:
  <https://github.com/microsoft/monaco-editor/blob/v0.55.1/LICENSE.txt>
- Version-specific upstream notices:
  <https://github.com/microsoft/monaco-editor/blob/v0.55.1/ThirdPartyNotices.txt>

The IDE currently loads Monaco from a CDN rather than storing a Monaco
distribution in this repository. If Monaco is bundled or vendored later, its
version-specific `LICENSE.txt` and `ThirdPartyNotices.txt` must be copied with
the distribution rather than replaced by this summary.

The MIT License (MIT)

Copyright (c) 2016 - present Microsoft Corporation

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Research and acquisition tooling (removed)

Earlier private research tooling used PyMuPDF (AGPL-3.0 / commercial
dual-licensed) and Requests (Apache-2.0). That tooling, together with the
research corpus it processed, was removed before this repository was made
public and is not distributed here. The published repository has **no
third-party Python dependencies**: the compiler, the IDE server, and the
test suites use only the Python standard library. Monaco Editor (above) is
the sole third-party runtime component, loaded from a CDN by the browser.
