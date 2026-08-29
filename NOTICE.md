# Project Use, Design, and Attribution Notice

Last updated: 29 August 2026

## 1. Purpose and present use

Pseudocode Studio and its completion engine are a student-developed educational
project intended for personal learning and student use. The project is not
currently offered for sale, licensed for a fee, or operated as a commercial
service.

This description of non-commercial use is a statement of present purpose only.
It is not a claim that educational or non-commercial use automatically waives,
limits, or overrides any copyright, trade mark, patent, registered design,
unregistered design, contractual, or other intellectual-property right.

## 2. Current implementation and design references

To the maintainer's knowledge, and based on a review of the current IDE UI
source as of the date above, the project-specific HTML, CSS, and JavaScript in
`ide/static/` were written for this project unless a file or notice expressly
states otherwise. This statement is limited to the current IDE UI; it is not an
unqualified representation about every file, historical revision, research
source, or dependency in the repository.

The IDE uses common code-editor interaction patterns, including an editor tab
strip, inline or “ghost text” completion, a `Tab`-to-accept action, a suggestion
list, diagnostics, and dark and light workbench themes. During design work, the
project referred to publicly documented behaviour and general interaction
patterns found in modern editors, including Monaco Editor, Visual Studio Code,
and Cursor. Those references are acknowledged as design inspiration; they are
not a claim that the complete Visual Studio Code or Cursor products, their
branding, or their proprietary additions are open source.

The same review found no Cursor or Visual Studio Code logo, branded icon,
screenshot, product name as project branding, or copied Cursor-specific source
or stylesheet in the current IDE UI. Product names in this notice are used only
to identify the products discussed. This factual review is not a legal
conclusion of non-infringement.

## 3. Third-party software

The browser IDE loads Monaco Editor 0.55.1 from jsDelivr. Monaco Editor is
licensed by Microsoft Corporation under the MIT License. The applicable
copyright and complete permission notice are reproduced in
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

The project is not affiliated with, sponsored by, or endorsed by Microsoft
Corporation, Anysphere, Inc. (maker of Cursor), jsDelivr, Cambridge University
Press & Assessment, Cambridge Assessment International Education, Cambridge
International Education, the University of Cambridge Local Examinations
Syndicate (UCLES), or the maintainers of any third-party component. Their names
and trade marks remain the property of their respective owners. References to
`CAIE`, Cambridge IGCSE, and syllabus codes such as 0478 and 9618 are used only
to describe compatibility or research context; no affiliation or endorsement
is implied.

## 4. Interface appearance and protected designs

This project does not claim ownership of general editor interaction concepts or
of any third party's protected interface appearance. Nothing in this notice
grants or implies a licence to any third-party patent, registered design,
unregistered design, trade mark, or proprietary product feature. The project's
interface should be maintained as an independently expressed design and should
not incorporate third-party branding or a pixel-for-pixel reproduction of a
distinctive third-party interface.

The cited UK Intellectual Property Office guidance explains that the visual
appearance of a graphical user interface may be capable of registered-design
protection and that such protection concerns appearance rather than function.
It does not decide whether this project infringes any particular right.

## 5. Research materials and other third-party content

This notice addresses the project's IDE design references and software
dependency attribution. It is not a blanket licence for examination papers,
mark schemes, specifications, textbooks, guides, datasets, or other external
materials that may be referenced or used during research. Rights in those
materials remain with their respective owners, and possession or educational
use does not by itself grant a right to redistribute them. Anyone publishing or
redistributing the repository is responsible for checking the applicable terms
and permissions for such materials.

In particular, Cambridge examination papers, mark schemes, specifications,
guides, and related materials remain subject to the rights and terms of
Cambridge University Press & Assessment and Cambridge International Education.
The IDE is an independent compatibility and learning tool; it is not an
official Cambridge product or endorsed resource. This notice does not authorise
publication of Cambridge materials, and no present or future project licence
covers those third-party papers, mark schemes, guides, textbooks, or source
PDFs.

**Public-repository statement (29 August 2026).** Before this repository was
prepared for publication, all third-party source documents and all material
derived from them were physically removed. This includes every research
corpus, extracted or normalised pseudocode taken from examination papers,
mark schemes, or official guides, the experimental completion engine trained
on that corpus, its evaluation artefacts, and all acquisition tooling. The
published repository contains only original project code, original example
programs, and original documentation. The completion feature is therefore
disabled in this build (see Section 6).

## 6. Experimental completion engine (not distributed)

An experimental next-token completion engine was developed as a private
research exercise. Because its training corpus consisted of third-party
copyrighted examination material that cannot lawfully be redistributed, the
engine, its corpus, and its evaluation data are not distributed with this
repository and are not available on request. The public IDE build runs in
compiler-only mode and returns an explicit `completion_disabled` response
from its completion endpoint. Nothing in this repository grants any right to
reconstruct, request, or redistribute that corpus.

## 7. Scope of this notice

This file records purpose, attribution, and non-affiliation. It is not a licence
for the project's original source code, is not legal advice, and does not alter
the terms of any third-party licence. If the project is later released under an
open-source licence, that licence should be supplied separately in a `LICENSE`
file.

Questions or credible rights concerns should be raised with the repository
maintainer at <pseudocode-translator@protonmail.com> (or via a GitHub issue)
so the relevant material can be reviewed, attributed, replaced, or removed as
appropriate.

## 8. Reference sources

- Monaco Editor 0.55.1 license:
  <https://github.com/microsoft/monaco-editor/blob/v0.55.1/LICENSE.txt>
- Monaco Editor 0.55.1 upstream notices:
  <https://github.com/microsoft/monaco-editor/blob/v0.55.1/ThirdPartyNotices.txt>
- Visual Studio Code / Code - OSS license: <https://github.com/microsoft/vscode/blob/main/LICENSE.txt>
- Visual Studio Code licensing distinction: <https://code.visualstudio.com/docs/supporting/faq>
- Cursor open-source component notices: <https://cursor.com/licenses>
- Cursor Terms of Service: <https://cursor.com/en-US/terms-of-service>
- UK Intellectual Property Office guidance on graphical user interfaces and
  registered designs: <https://www.gov.uk/government/publications/designs-practice-notice-dpn-0126-practice-in-respect-of-graphic-symbolsicons-graphicalweb-user-interfaces-and-animated-designs/designs-practice-notice-dpn-0126-practice-in-respect-of-graphic-symbolsicons-graphicalweb-user-interfaces-and-animated-designs>
- Cambridge International Education website terms, including copyright and
  trade-mark provisions: <https://www.cambridgeinternational.org/privacy-and-legal/terms-and-conditions/>
- Cambridge guidance on permission for reproduction of examination materials:
  <https://www.cambridgeinternational.org/support-and-training-for-schools/endorsed-resources/>
- Cambridge guidance on publication of past papers on websites:
  <https://help.cambridgeinternational.org/hc/en-gb/articles/203544371-Can-I-reproduce-Cambridge-past-examination-papers-on-the-school-s-website-my-website>
