"use strict";

(() => {
  const LANGUAGE_ID = "caie-pseudocode";
  const MONACO_VERSION = "0.55.1";
  const MONACO_BASE = `https://cdn.jsdelivr.net/npm/monaco-editor@${MONACO_VERSION}`;
  const STORAGE_SOURCE = "pseudocode-studio.source.v1";
  const STORAGE_FILE = "pseudocode-studio.file.v1";
  const STORAGE_THEME = "pseudocode-studio.theme.v1";
  const STORAGE_STDIN = "pseudocode-studio.stdin.v1";
  const STORAGE_LOCALE = "pseudocode-studio.locale.v1";
  const STORAGE_SIDEBAR = "pseudocode-studio.sidebar.v1";
  const STORAGE_COMPLETION = "pseudocode-studio.completion.v1";
  const THEME_DARK = "studio-dark";
  const THEME_IVORY = "ivory-gold";
  const I18N = {
    zh: {
      tagline: "本地考试工作台",
      open: "打开", save: "保存", compile: "编译", run: "运行",
      openTitle: "打开本地 .pseudo 文件",
      saveTitle: "下载当前程序（Ctrl+S）",
      compileTitle: "编译为 Python（Ctrl+Enter）",
      runTitle: "编译并运行（Ctrl+Shift+Enter）",
      themeNext: "纸页", themeNextDark: "灯下",
      deskFolder: "工作夹", program: "程序", dataFiles: "数据文件", examples: "示例",
      dataFolder: "数据文件夹",
      dataFolderTitle: "OPENFILE / READFILE / WRITEFILE 使用的本机文件夹",
      openFolder: "打开文件夹", useDesktop: "放到桌面", importFile: "导入", newFile: "新建",
      collapseSidebar: "收起侧栏", expandSidebar: "展开侧栏",
      completionToggleTitle: "打开或关闭代码补全",
      completionOff: "补全：已关闭",
      completionFileOp: "补全已停：文件操作语料不足",
      openFolderTitle: "在资源管理器中打开 OPENFILE 使用的文件夹",
      useDesktopTitle: "把数据文件夹改到桌面\\PseudocodeFiles",
      importTitle: "把电脑上的 txt 复制进数据文件夹",
      newFileTitle: "在数据文件夹里新建空文件",
      filesBlurb: "OPENFILE / READFILE / WRITEFILE 读写的是下面这个文件夹，不是左边的 .pseudo 程序。先导入或新建 txt，再用文件名去写伪代码。",
      filesTab: "文件操作", problems: "问题", console: "控制台", tokens: "词法",
      ready: "就绪", accept: "接受", suggest: "补全",
      stdin: "标准输入", stdout: "程序输出", clear: "清空",
      stdinPlaceholder: "每行一个 INPUT 值",
      notRunYet: "尚未运行",
      consoleIdle: "运行程序后，输出会出现在这里。",
      starting: "正在启动本地服务…",
      serviceReady: "编译器与补全已就绪",
      completionWaiting: "补全：等待中",
      loadingEditor: "正在加载编辑器…",
      spaces: "缩进 4",
      offlineBanner: "Monaco 无法加载。已切换离线编辑器；补全、编译和运行仍可用。",
      noDataFiles: "还没有数据文件。点「导入」或「新建」。",
      emptyPreview: "（空文件）",
      noFolder: "（未选择文件夹）",
      newFilePrompt: "新数据文件名",
      filesGuideTitle: "文件操作怎么用",
      filesGuideLead: "这是本机文件夹，不是网站网盘。伪代码里的文件名必须和下面列表里的名字一致，例如 FileA.txt。",
      filesGuideSteps: [
        "点顶栏「数据文件夹」打开面板，用「导入」或「新建」把 txt / dat 放进来；也可以点「打开文件夹」直接在磁盘上改。",
        "程序里写 OPENFILE \"文件名\" FOR READ / WRITE / APPEND。随机文件再用 FOR RANDOM。",
        "READFILE 一次读一行；WRITEFILE 一次写一行；EOF(\"文件名\") 判断是否读完；最后 CLOSEFILE。",
        "点运行。新文件会出现在面板列表里，点文件名可预览内容。",
      ],
      filesGuideSyntax: `DECLARE Line : STRING
OPENFILE "FileA.txt" FOR READ
OPENFILE "FileB.txt" FOR WRITE
WHILE NOT EOF("FileA.txt")
    READFILE "FileA.txt", Line
    WRITEFILE "FileB.txt", Line
ENDWHILE
CLOSEFILE "FileA.txt"
CLOSEFILE "FileB.txt"`,
      filesGuideRandom: "A Level 随机文件：OPENFILE \"Rec.Dat\" FOR RANDOM，然后 SEEK、GETRECORD、PUTRECORD。地址从 1 开始。",
      loadCopyExample: "载入拷贝示例",
      exampleNames: {
        "Running total": "累加",
        "Count vowels": "数元音",
        "Maximum function": "最大值函数",
        "Copy text file": "拷贝文本文件",
      },
      checking: "检查中…", compiling: "正在编译…",
      compileFailed: "编译失败",
      startingProgram: "正在启动程序…",
      running: "运行中",
      compileAndRun: "正在编译并运行…",
      runFailed: "运行失败",
      runUnavailable: "无法运行",
      stillDiagnostics: "编译和编辑器诊断仍然可用。",
      noPython: "# 尚未生成 Python。",
      noProblems: "没有编译问题。",
      noTokens: "没有词法单元。",
      hint: "提示",
      timedOut: "超时", failed: "失败", finished: "完成",
      offlineEditor: "离线编辑器",
      serviceError: "服务出错",
      compiled: "已编译",
      problemSummary: "个问题",
      completionPaused: "补全已暂停：正在改旧代码",
      completionIdle: "Completion: no safe action",
      tabNewLine: "Tab: new line",
      completionUnavailable: "补全不可用",
      runnerLimit: "超过 3 秒运行上限，已停止。",
      truncated: "输出超过 64 KiB，已截断。",
      noOutput: "程序结束，没有输出。",
      didNotRun: "程序没有运行。请到「问题」查看编译诊断。",
      filesGuideSeed: "数据文件夹里已经有一份 FileA.txt，可以直接点「载入拷贝示例」再运行。",
      detected: "检测到",
      noParams: "不需要参数输入",
      inputOrder: "请按顺序每行输入一个值",
      argument: "参数",
      themeTo: "切换到",
      resizePanelTitle: "拖动调整输出面板高度",
    },
    en: {
      tagline: "local exam desk",
      open: "Open", save: "Save", compile: "Compile", run: "Run",
      openTitle: "Open a local .pseudo file",
      saveTitle: "Download this program (Ctrl+S)",
      compileTitle: "Compile to Python (Ctrl+Enter)",
      runTitle: "Compile and run (Ctrl+Shift+Enter)",
      themeNext: "Paper", themeNextDark: "Lamp",
      deskFolder: "Folder", program: "Program", dataFiles: "Data files", examples: "Examples",
      dataFolder: "Data folder",
      dataFolderTitle: "Local folder used by OPENFILE / READFILE / WRITEFILE",
      openFolder: "Open folder", useDesktop: "Desktop", importFile: "Import", newFile: "New",
      collapseSidebar: "Collapse sidebar", expandSidebar: "Expand sidebar",
      completionToggleTitle: "Turn code completion on or off",
      completionOff: "Completion: off",
      completionFileOp: "Completion off: file operations (sparse training data)",
      openFolderTitle: "Open the folder used by OPENFILE in Explorer",
      useDesktopTitle: "Use Desktop\\PseudocodeFiles for data files",
      importTitle: "Copy a local text file into the data folder",
      newFileTitle: "Create an empty file in the data folder",
      filesBlurb: "OPENFILE / READFILE / WRITEFILE use the folder below, not the .pseudo program. Import or create a txt first, then use that file name in code.",
      filesTab: "File I/O", problems: "Problems", console: "Console", tokens: "Tokens",
      ready: "Ready", accept: "accept", suggest: "suggest",
      stdin: "Standard input", stdout: "Program output", clear: "Clear",
      stdinPlaceholder: "One INPUT value per line",
      notRunYet: "Not run yet",
      consoleIdle: "Run the program to see its output here.",
      starting: "Starting local service…",
      serviceReady: "Compiler + completion ready",
      completionWaiting: "Completion: waiting",
      loadingEditor: "Loading editor…",
      spaces: "Spaces: 4",
      offlineBanner: "Monaco could not be loaded. The offline editor is active; completion, compilation, and execution remain available.",
      noDataFiles: "No data files yet. Import or New.",
      emptyPreview: "(empty)",
      noFolder: "(no folder)",
      newFilePrompt: "New data file name",
      filesGuideTitle: "How file operations work",
      filesGuideLead: "This is a folder on this computer, not a cloud drive. The name in OPENFILE must match a file in the list, for example FileA.txt.",
      filesGuideSteps: [
        "Open Data folder in the top bar, then Import or New a .txt / .dat. You can also click Open folder and edit on disk.",
        "In the program write OPENFILE \"filename\" FOR READ / WRITE / APPEND. Use FOR RANDOM for A Level random files.",
        "READFILE reads one line; WRITEFILE writes one line; EOF(\"filename\") tests the end; CLOSEFILE when finished.",
        "Click Run. New files appear in the panel; click a name to preview it.",
      ],
      filesGuideSyntax: `DECLARE Line : STRING
OPENFILE "FileA.txt" FOR READ
OPENFILE "FileB.txt" FOR WRITE
WHILE NOT EOF("FileA.txt")
    READFILE "FileA.txt", Line
    WRITEFILE "FileB.txt", Line
ENDWHILE
CLOSEFILE "FileA.txt"
CLOSEFILE "FileB.txt"`,
      filesGuideRandom: "A Level random files: OPENFILE \"Rec.Dat\" FOR RANDOM, then SEEK, GETRECORD, PUTRECORD. Addresses are 1-based.",
      loadCopyExample: "Load copy example",
      exampleNames: {},
      checking: "Checking…", compiling: "Compiling…",
      compileFailed: "Compile failed",
      startingProgram: "Starting program…",
      running: "Running",
      compileAndRun: "Compiling and running…",
      runFailed: "Run failed",
      runUnavailable: "Run unavailable",
      stillDiagnostics: "Compilation and editor diagnostics are still available.",
      noPython: "# No Python generated.",
      noProblems: "No compiler problems detected.",
      noTokens: "No tokens emitted.",
      hint: "Hint",
      timedOut: "Timed out", failed: "Failed", finished: "Finished",
      offlineEditor: "Offline editor",
      serviceError: "Service error",
      compiled: "Compiled",
      problemSummary: "problems",
      completionPaused: "Completion paused: editing old code",
      completionIdle: "Completion: no safe action",
      tabNewLine: "Tab: new line",
      completionUnavailable: "Completion unavailable",
      runnerLimit: "Stopped after the 3-second execution limit.",
      truncated: "Output was truncated at the 64 KiB limit.",
      noOutput: "Program finished without output.",
      didNotRun: "The program did not run. Check Problems for compiler diagnostics.",
      filesGuideSeed: "FileA.txt is already in the data folder, so you can load the copy example and run it.",
      detected: "Detected",
      noParams: "no parameter input required",
      inputOrder: "input values one per line, in order",
      argument: "argument",
      themeTo: "Switch to",
      resizePanelTitle: "Drag to resize the output panel",
    },
  };
  const DEFAULT_SOURCE = `DECLARE total : INTEGER
DECLARE value : INTEGER
total <- 0

INPUT value
WHILE value <> -1
    total <- total + value
    INPUT value
ENDWHILE

OUTPUT total`;

  const state = {
    meta: null,
    monaco: null,
    editor: null,
    mode: "starting",
    fileName: localStorage.getItem(STORAGE_FILE) || "main.pseudo",
    dirty: false,
    suppressChange: false,
    completionTimer: null,
    diagnosticsTimer: null,
    completionCache: new Map(),
    completionSequence: 0,
    compileSequence: 0,
    runSequence: 0,
    theme: localStorage.getItem(STORAGE_THEME) === THEME_IVORY ? THEME_IVORY : THEME_DARK,
    latestSuggestions: [],
    suggestionContext: null,
    newlineDecorationIds: [],
    locale: localStorage.getItem(STORAGE_LOCALE) === "en" ? "en" : "zh",
    lastCompile: null,
    lastRun: null,
    workspace: null,
    completionEnabled: localStorage.getItem(STORAGE_COMPLETION) !== "off",
    outputHeight: null,
  };

  const dom = {};

  window.addEventListener("DOMContentLoaded", bootstrap);

  async function bootstrap() {
    cacheDom();
    applyTheme(state.theme, false);
    applyLocale(false);
    bindChrome();
    dom["stdin-input"].value = localStorage.getItem(STORAGE_STDIN) || "";
    setFileName(state.fileName);
    if (dom["compile-state"]) dom["compile-state"].textContent = t("ready");

    let initialSource = localStorage.getItem(STORAGE_SOURCE) || DEFAULT_SOURCE;
    try {
      state.meta = await getJSON("/api/meta");
      renderMetadata(state.meta);
      markServiceReady(true);
    } catch (error) {
      markServiceReady(false, error.message);
    }

    try {
      const monaco = await loadMonaco(7000);
      initMonaco(monaco, initialSource);
    } catch (error) {
      console.warn("Monaco unavailable; using textarea fallback.", error);
      initFallback(initialSource);
    }

    updateCursorStatus();
    applyCompletionEnabled(state.completionEnabled, false);
    scheduleCompletions(20);
    scheduleDiagnostics(80);
  }

  function cacheDom() {
    [
      "service-dot", "file-name", "explorer-file-name", "tab-file-name",
      "open-button", "save-button", "compile-button", "run-button", "file-input",
      "theme-button", "theme-label", "offline-banner", "example-list", "editor",
      "fallback-editor", "problem-count", "compile-state", "problems-panel",
      "python-panel", "tokens-panel", "console-panel", "stdin-input",
      "console-output", "console-run-button", "clear-stdin-button", "run-meta",
      "entrypoint-hint", "connection-status", "editor-mode", "cursor-position",
      "completion-status", "workspace-path", "workspace-open-button",
      "workspace-desktop-button", "data-import-button", "data-new-button",
      "data-file-list", "data-preview", "data-file-input", "workspace-status",
      "files-panel", "files-blurb", "locale-zh", "locale-en",
      "workspace-open-trigger", "workspace-popover", "sidebar-toggle",
      "completion-toggle", "output-resizer",
    ].forEach((id) => {
      dom[id] = document.getElementById(id);
    });
  }

  const LIVE_I18N_IDS = new Set([
    "compile-state", "connection-status", "console-output", "run-meta",
    "editor-mode", "completion-status",
  ]);

  function t(key) {
    const pack = I18N[state.locale] || I18N.zh;
    if (pack[key] !== undefined) return pack[key];
    if (I18N.en[key] !== undefined) return I18N.en[key];
    return key;
  }

  function setLocale(locale) {
    state.locale = locale === "en" ? "en" : "zh";
    localStorage.setItem(STORAGE_LOCALE, state.locale);
    applyLocale(false);
  }

  function applyLocale(persist = true) {
    if (persist) localStorage.setItem(STORAGE_LOCALE, state.locale);
    document.documentElement.lang = state.locale === "en" ? "en" : "zh";
    document.title = state.locale === "zh"
      ? "伪代码工作台 · Pseudocode Studio"
      : "Pseudocode Studio";
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      if (LIVE_I18N_IDS.has(el.id)) return;
      const value = t(el.dataset.i18n);
      if (typeof value === "string") el.textContent = value;
    });
    document.querySelectorAll("[data-i18n-title]").forEach((el) => {
      el.title = t(el.dataset.i18nTitle);
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      el.placeholder = t(el.dataset.i18nPlaceholder);
    });
    if (dom["locale-zh"]) dom["locale-zh"].classList.toggle("active", state.locale === "zh");
    if (dom["locale-en"]) dom["locale-en"].classList.toggle("active", state.locale === "en");
    updateThemeLabels();
    if (dom["files-blurb"]) dom["files-blurb"].textContent = t("filesBlurb");
    renderFilesGuide();
    if (state.meta) renderExamples(state.meta);
    if (state.workspace) renderWorkspace(state.workspace);
    if (state.lastRun) renderRunResult(state.lastRun);
    else if (state.lastCompile) renderProblems(state.lastCompile);
    else if (dom["compile-state"]) dom["compile-state"].textContent = t("ready");
    if (dom["service-dot"] && !dom["service-dot"].classList.contains("error") && state.meta) {
      dom["connection-status"].textContent = t("serviceReady");
    }
    if (state.mode === "fallback" && dom["editor-mode"]) {
      dom["editor-mode"].textContent = t("offlineEditor");
    }
    if (!state.lastRun && dom["console-output"] && !document.body.classList.contains("is-running")) {
      dom["console-output"].textContent = t("consoleIdle");
      if (dom["run-meta"]) dom["run-meta"].textContent = t("notRunYet");
    }
  }

  function renderFilesGuide() {
    const panel = dom["files-panel"];
    if (!panel) return;
    panel.replaceChildren();
    const heading = document.createElement("h2");
    heading.textContent = t("filesGuideTitle");
    const lead = document.createElement("p");
    lead.className = "lead";
    lead.textContent = t("filesGuideLead");
    const steps = document.createElement("ol");
    (t("filesGuideSteps") || []).forEach((step) => {
      const item = document.createElement("li");
      item.textContent = step;
      steps.append(item);
    });
    const sample = document.createElement("pre");
    sample.textContent = t("filesGuideSyntax");
    const random = document.createElement("p");
    random.className = "lead";
    random.textContent = t("filesGuideRandom");
    const seed = document.createElement("p");
    seed.className = "lead";
    seed.textContent = t("filesGuideSeed");
    const actions = document.createElement("div");
    actions.className = "guide-actions";
    const load = document.createElement("button");
    load.type = "button";
    load.className = "chip-button";
    load.textContent = t("loadCopyExample");
    load.addEventListener("click", loadCopyExample);
    actions.append(load);
    panel.append(heading, lead, steps, sample, random, seed, actions);
  }

  function loadCopyExample() {
    const example = ((state.meta && state.meta.examples) || []).find(
      (item) => item.name === "Copy text file",
    );
    if (!example) return;
    setEditorValue(example.code);
    setFileName("copy-text-file.pseudo");
    setDirty(true);
    compileNow(true);
  }

  function exampleLabel(example) {
    if (state.locale !== "zh") return example.name;
    return example.nameZh || (t("exampleNames")[example.name] || example.name);
  }

  function renderExamples(meta) {
    if (!dom["example-list"]) return;
    dom["example-list"].replaceChildren();
    (meta.examples || []).forEach((example) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "example-row";
      button.textContent = exampleLabel(example);
      button.addEventListener("click", () => {
        setEditorValue(example.code);
        setFileName(`${slugify(example.name)}.pseudo`);
        setDirty(true);
        compileNow(true);
      });
      dom["example-list"].append(button);
    });
  }

  function bindChrome() {
    const shell = document.querySelector(".app-shell");
    const sidebarToggle = dom["sidebar-toggle"];
    if (sidebarToggle && shell) {
      const applySidebar = (collapsed) => {
        shell.classList.toggle("sidebar-collapsed", collapsed);
        sidebarToggle.setAttribute("aria-expanded", String(!collapsed));
        sidebarToggle.title = t(collapsed ? "expandSidebar" : "collapseSidebar");
        sidebarToggle.setAttribute(
          "aria-label",
          t(collapsed ? "expandSidebar" : "collapseSidebar"),
        );
        if (state.editor && state.mode === "monaco") state.editor.layout();
      };
      applySidebar(localStorage.getItem(STORAGE_SIDEBAR) === "collapsed");
      sidebarToggle.addEventListener("click", () => {
        const collapsed = !shell.classList.contains("sidebar-collapsed");
        localStorage.setItem(STORAGE_SIDEBAR, collapsed ? "collapsed" : "open");
        applySidebar(collapsed);
      });
    }
    const completionToggle = dom["completion-toggle"];
    if (completionToggle) {
      completionToggle.addEventListener("click", () => {
        applyCompletionEnabled(!state.completionEnabled);
      });
    }
    applyCompletionEnabled(state.completionEnabled, false);
    const trigger = dom["workspace-open-trigger"];
    const popover = dom["workspace-popover"];
    if (trigger && popover) {
      const setOpen = (open) => {
        popover.hidden = !open;
        trigger.setAttribute("aria-expanded", String(open));
        trigger.closest(".popover-anchor").classList.toggle("open", open);
      };
      trigger.addEventListener("click", (event) => {
        event.stopPropagation();
        setOpen(popover.hidden);
      });
      popover.addEventListener("click", (event) => event.stopPropagation());
      document.addEventListener("click", (event) => {
        if (!popover.hidden && !popover.contains(event.target) && event.target !== trigger) {
          setOpen(false);
        }
      });
      document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && !popover.hidden) {
          setOpen(false);
          trigger.focus();
        }
      });
    }
    dom["compile-button"].addEventListener("click", () => compileNow(false));
    dom["run-button"].addEventListener("click", runNow);
    dom["console-run-button"].addEventListener("click", runNow);
    dom["theme-button"].addEventListener("click", toggleTheme);
    dom["open-button"].addEventListener("click", () => dom["file-input"].click());
    dom["save-button"].addEventListener("click", saveFile);
    dom["file-input"].addEventListener("change", openSelectedFile);
    dom["stdin-input"].addEventListener("input", () => {
      localStorage.setItem(STORAGE_STDIN, dom["stdin-input"].value);
    });
    dom["clear-stdin-button"].addEventListener("click", () => {
      dom["stdin-input"].value = "";
      localStorage.removeItem(STORAGE_STDIN);
      dom["stdin-input"].focus();
    });

    if (dom["locale-zh"]) {
      dom["locale-zh"].addEventListener("click", () => setLocale("zh"));
    }
    if (dom["locale-en"]) {
      dom["locale-en"].addEventListener("click", () => setLocale("en"));
    }

    document.querySelectorAll(".output-tab").forEach((button) => {
      button.addEventListener("click", () => switchOutputPanel(button.dataset.panel));
    });

    dom["data-import-button"].addEventListener("click", () => dom["data-file-input"].click());
    dom["data-file-input"].addEventListener("change", importDataFile);
    dom["data-new-button"].addEventListener("click", createDataFile);
    dom["workspace-open-button"].addEventListener("click", () => {
      postJSON("/api/workspace/reveal", {}).catch((error) => {
        window.alert(error.message);
      });
    });
    dom["workspace-desktop-button"].addEventListener("click", async () => {
      try {
        renderWorkspace(await postJSON("/api/workspace/desktop", {}));
      } catch (error) {
        window.alert(error.message);
      }
    });
    window.addEventListener("keydown", (event) => {
      const modifier = event.ctrlKey || event.metaKey;
      if (modifier && event.shiftKey && event.key === "Enter") {
        event.preventDefault();
        runNow();
      } else if (modifier && event.key === "Enter") {
        event.preventDefault();
        compileNow(false);
      } else if (modifier && event.key.toLowerCase() === "s") {
        event.preventDefault();
        saveFile();
      }
    });

    const outputResizer = dom["output-resizer"];
    if (outputResizer) {
      outputResizer.addEventListener("pointerdown", (event) => {
        if (event.button !== 0) return;
        event.preventDefault();
        const column = document.querySelector(".editor-column");
        if (!column) return;
        const startY = event.clientY;
        const measured = parseFloat(
          getComputedStyle(column).getPropertyValue("--output-height"),
        );
        const startOutput = Number.isFinite(state.outputHeight)
          ? state.outputHeight
          : (Number.isFinite(measured) ? measured : 220);
        outputResizer.classList.add("dragging");
        document.body.classList.add("output-resizing");
        outputResizer.setPointerCapture(event.pointerId);
        const onMove = (moveEvent) => {
          const next = startOutput + (startY - moveEvent.clientY);
          applyOutputHeight(next);
        };
        const onUp = () => {
          outputResizer.classList.remove("dragging");
          document.body.classList.remove("output-resizing");
          outputResizer.removeEventListener("pointermove", onMove);
          outputResizer.removeEventListener("pointerup", onUp);
          outputResizer.removeEventListener("pointercancel", onUp);
        };
        outputResizer.addEventListener("pointermove", onMove);
        outputResizer.addEventListener("pointerup", onUp);
        outputResizer.addEventListener("pointercancel", onUp);
      });
    }
  }

  function applyOutputHeight(height) {
    const column = document.querySelector(".editor-column");
    if (!column) return;
    const columnHeight = column.getBoundingClientRect().height;
    const min = 96;
    const max = Math.max(min, columnHeight - 36 - 120);
    const clamped = Math.round(Math.min(max, Math.max(min, height)));
    state.outputHeight = clamped;
    column.style.setProperty("--output-height", `${clamped}px`);
    if (state.mode === "monaco" && state.editor) state.editor.layout();
  }

  function applyCompletionEnabled(enabled, persist = true) {
    state.completionEnabled = !!enabled;
    if (persist) {
      localStorage.setItem(STORAGE_COMPLETION, enabled ? "on" : "off");
    }
    const button = dom["completion-toggle"];
    if (button) {
      button.classList.toggle("off", !enabled);
      button.setAttribute("aria-checked", String(!!enabled));
    }
    if (state.mode === "monaco" && state.editor) {
      state.editor.updateOptions({
        quickSuggestions: enabled
          ? { other: true, comments: false, strings: false }
          : false,
        suggestOnTriggerCharacters: enabled,
        tabCompletion: enabled ? "on" : "off",
        inlineSuggest: { enabled: !!enabled },
      });
    }
    if (!enabled) {
      state.latestSuggestions = [];
      state.suggestionContext = null;
      updateNewlineDecoration(null);
      setCompletionStatus(t("completionOff"));
    } else {
      scheduleCompletions(20);
    }
  }

  function renderMetadata(meta) {
    state.meta = meta;
    dom["connection-status"].textContent = t("serviceReady");
    renderWorkspace(meta.workspace);
    renderExamples(meta);
  }

  function markServiceReady(ready, message = "") {
    dom["service-dot"].classList.toggle("ready", ready);
    dom["service-dot"].classList.toggle("error", !ready);
    if (!ready) {
      dom["connection-status"].textContent = `${t("serviceError")}: ${message}`;
    }
  }

  function updateThemeLabels() {
    if (!dom["theme-label"] || !dom["theme-button"]) return;
    const nextTheme = state.theme === THEME_DARK ? t("themeNext") : t("themeNextDark");
    dom["theme-label"].textContent = nextTheme;
    const title = `${t("themeTo")} ${nextTheme}`;
    dom["theme-button"].title = title;
    dom["theme-button"].setAttribute("aria-label", title);
  }

  function toggleTheme() {
    applyTheme(state.theme === THEME_DARK ? THEME_IVORY : THEME_DARK);
  }

  function applyTheme(theme, persist = true) {
    const selected = theme === THEME_IVORY ? THEME_IVORY : THEME_DARK;
    state.theme = selected;
    document.documentElement.dataset.theme = selected;
    const colorScheme = document.querySelector('meta[name="color-scheme"]');
    if (colorScheme) colorScheme.content = selected === THEME_IVORY ? "light" : "dark";
    updateThemeLabels();
    if (persist) localStorage.setItem(STORAGE_THEME, selected);
    if (state.monaco) state.monaco.editor.setTheme(monacoThemeName(selected));
  }

  function monacoThemeName(theme) {
    return theme === THEME_IVORY
      ? "pseudocode-ivory-gold"
      : "pseudocode-studio-dark";
  }

  function loadMonaco(timeoutMs) {
    return new Promise((resolve, reject) => {
      let settled = false;
      const finish = (fn, value) => {
        if (settled) return;
        settled = true;
        clearTimeout(timeout);
        fn(value);
      };
      const timeout = setTimeout(
        () => finish(reject, new Error("Monaco load timed out")),
        timeoutMs,
      );

      const workerSource = `self.MonacoEnvironment={baseUrl:'${MONACO_BASE}/min/'};importScripts('${MONACO_BASE}/min/vs/base/worker/workerMain.js');`;
      window.MonacoEnvironment = {
        getWorkerUrl() {
          return `data:text/javascript;charset=utf-8,${encodeURIComponent(workerSource)}`;
        },
      };

      const script = document.createElement("script");
      script.src = `${MONACO_BASE}/min/vs/loader.js`;
      script.async = true;
      script.onerror = () => finish(reject, new Error("Monaco CDN request failed"));
      script.onload = () => {
        try {
          window.require.config({ paths: { vs: `${MONACO_BASE}/min/vs` } });
          window.require(
            ["vs/editor/editor.main"],
            () => finish(resolve, window.monaco),
            (error) => finish(reject, error),
          );
        } catch (error) {
          finish(reject, error);
        }
      };
      document.head.append(script);
    });
  }

  function initMonaco(monaco, initialSource) {
    state.monaco = monaco;
    state.mode = "monaco";
    registerPseudocodeLanguage(monaco);
    registerCompletionProviders(monaco);

    state.editor = monaco.editor.create(dom.editor, {
      value: initialSource,
      language: LANGUAGE_ID,
      theme: monacoThemeName(state.theme),
      automaticLayout: true,
      fontFamily: "Inconsolata, Cascadia Code, SFMono-Regular, Consolas, Liberation Mono, monospace",
      fontSize: 14,
      lineHeight: 22,
      // Keep ASCII operators visually honest. Cascadia Code otherwise draws
      // `!=` as a single `≠` ligature even though the source still contains
      // two ASCII characters and the compiler correctly diagnoses `!=`.
      fontLigatures: false,
      minimap: { enabled: false },
      lineNumbersMinChars: 2,
      lineDecorationsWidth: 6,
      padding: { top: 12, bottom: 16 },
      tabSize: 4,
      insertSpaces: true,
      detectIndentation: false,
      smoothScrolling: true,
      cursorSmoothCaretAnimation: "on",
      renderWhitespace: "selection",
      renderLineHighlight: "all",
      bracketPairColorization: { enabled: true },
      guides: { bracketPairs: false, indentation: false },
      quickSuggestions: { other: true, comments: false, strings: false },
      suggestOnTriggerCharacters: true,
      tabCompletion: "on",
      wordBasedSuggestions: "off",
      suggest: { selectionMode: "always", preview: true, showStatusBar: true },
      inlineSuggest: {
        enabled: true,
        showToolbar: "onHover",
        syntaxHighlightingEnabled: true,
      },
      scrollBeyondLastLine: false,
      fixedOverflowWidgets: true,
    });

    state.editor.onDidChangeModelContent(onEditorChanged);
    state.editor.onDidChangeCursorPosition(() => {
      updateCursorStatus();
      clearIfEditingExistingText();
      scheduleCompletions(90);
    });
    state.editor.onKeyDown((event) => {
      if (event.keyCode !== monaco.KeyCode.Tab) return;
      const first = state.latestSuggestions[0];
      if (!first || first.actionKind !== "insert_newline") return;
      const source = getEditorValue();
      const offset = getCursorOffset();
      if (
        !state.suggestionContext ||
        state.suggestionContext.source !== source ||
        state.suggestionContext.offset !== offset
      ) return;
      event.preventDefault();
      event.stopPropagation();
      applySuggestion(first);
    });
    state.editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => compileNow(false));
    state.editor.addCommand(
      monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.Enter,
      runNow,
    );
    state.editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, saveFile);
    // Keep the paper margin rule glued to the right edge of the (narrowed)
    // line-number gutter instead of a hard-coded pixel offset.
    state.editor.onDidLayoutChange(updateMarginLine);
    updateMarginLine();
    if (state.outputHeight !== null) applyOutputHeight(state.outputHeight);
    dom["editor-mode"].textContent = `Monaco ${MONACO_VERSION}`;
    dom["fallback-editor"].hidden = true;
    dom.editor.hidden = false;
    state.editor.focus();
  }

  function registerPseudocodeLanguage(monaco) {
    const keywords = (state.meta && state.meta.keywords) || [];
    monaco.languages.register({ id: LANGUAGE_ID });
    monaco.languages.setMonarchTokensProvider(LANGUAGE_ID, {
      ignoreCase: true,
      keywords,
      tokenizer: {
        root: [
          [/\/\/.*$/, "comment"],
          [/"[^"\n]*"/, "string"],
          [/"[^"\n]*$/, "string.invalid"],
          [/'[^'\n]'/, "string.char"],
          [/\d+\.\d+/, "number.float"],
          [/\d+/, "number"],
          [/[A-Za-z_][A-Za-z0-9_]*/, { cases: { "@keywords": "keyword", "@default": "identifier" } }],
          [/<-|<=|>=|<>|[=<>+\-*\/&^]/, "operator"],
          [/[()\[\]]/, "@brackets"],
          [/[,:.]/, "delimiter"],
        ],
      },
    });
    monaco.languages.setLanguageConfiguration(LANGUAGE_ID, {
      comments: { lineComment: "//" },
      brackets: [["(", ")"], ["[", "]"]],
      autoClosingPairs: [
        { open: "(", close: ")" },
        { open: "[", close: "]" },
        { open: '"', close: '"' },
        { open: "'", close: "'" },
      ],
      surroundingPairs: [
        { open: "(", close: ")" },
        { open: "[", close: "]" },
        { open: '"', close: '"' },
        { open: "'", close: "'" },
      ],
      indentationRules: {
        increaseIndentPattern: /^\s*(IF\b.*\bTHEN|FOR\b.*|WHILE\b.*|REPEAT\b.*|CASE\b.*|PROCEDURE\b.*|FUNCTION\b.*|TYPE\b.*|CLASS\b.*)$/i,
        decreaseIndentPattern: /^\s*(ELSE|OTHERWISE|ENDIF|NEXT|ENDWHILE|UNTIL|ENDCASE|ENDPROCEDURE|ENDFUNCTION|ENDTYPE|ENDCLASS)\b/i,
      },
    });
    monaco.editor.defineTheme("pseudocode-studio-dark", {
      base: "vs-dark",
      inherit: true,
      rules: [
        { token: "keyword", foreground: "6FBFA8", fontStyle: "bold" },
        { token: "identifier", foreground: "C7C1AE" },
        { token: "operator", foreground: "C7C1AE" },
        { token: "number", foreground: "B9C98E" },
        { token: "number.float", foreground: "B9C98E" },
        { token: "string", foreground: "C99A4B" },
        { token: "string.char", foreground: "C99A4B" },
        { token: "string.invalid", foreground: "D06A55" },
        { token: "comment", foreground: "70806F", fontStyle: "italic" },
        { token: "delimiter", foreground: "8B8977" },
      ],
      colors: {
        "editor.background": "#141C17",
        "editor.foreground": "#C7C1AE",
        "editorLineNumber.foreground": "#5A6659",
        "editorLineNumber.activeForeground": "#C99A4B",
        "editor.lineHighlightBackground": "#1A231F",
        "editorCursor.foreground": "#C99A4B",
        "editor.selectionBackground": "#2C4A3E",
        "editor.inactiveSelectionBackground": "#24312A",
        "editorIndentGuide.background1": "#2B362E",
        "editorIndentGuide.activeBackground1": "#3F4F44",
        "editorSuggestWidget.background": "#202A22",
        "editorSuggestWidget.border": "#3F4F44",
        "editorSuggestWidget.selectedBackground": "#24443A",
        "editorGhostText.foreground": "#5A6659",
        "editorGhostText.background": "#00000000",
        "editorGhostText.border": "#00000000",
      },
    });
    monaco.editor.defineTheme("pseudocode-ivory-gold", {
      base: "vs",
      inherit: true,
      rules: [
        { token: "keyword", foreground: "1F6B58", fontStyle: "bold" },
        { token: "identifier", foreground: "3E372A" },
        { token: "operator", foreground: "A87B2D" },
        { token: "number", foreground: "6B7A23" },
        { token: "number.float", foreground: "6B7A23" },
        { token: "string", foreground: "9A6A1F" },
        { token: "string.char", foreground: "9A6A1F" },
        { token: "string.invalid", foreground: "A23B2C" },
        { token: "comment", foreground: "9A8F74", fontStyle: "italic" },
        { token: "delimiter", foreground: "7C7260" },
      ],
      colors: {
        "editor.background": "#F8F3E6",
        "editor.foreground": "#3E372A",
        "editorLineNumber.foreground": "#A89C82",
        "editorLineNumber.activeForeground": "#A87B2D",
        "editor.lineHighlightBackground": "#EFE6D2",
        "editorCursor.foreground": "#A87B2D",
        "editor.selectionBackground": "#DCE7DF",
        "editor.inactiveSelectionBackground": "#EAE1CC",
        "editorIndentGuide.background1": "#D6C9AB",
        "editorIndentGuide.activeBackground1": "#B3A37E",
        "editorSuggestWidget.background": "#FDFAF0",
        "editorSuggestWidget.border": "#B3A37E",
        "editorSuggestWidget.selectedBackground": "#D9E9E0",
        "editorSuggestWidget.foreground": "#3E372A",
        "editorGhostText.foreground": "#B4A98E",
        "editorGhostText.background": "#00000000",
        "editorGhostText.border": "#00000000",
      },
    });
  }

  function registerCompletionProviders(monaco) {
    monaco.languages.registerCompletionItemProvider(LANGUAGE_ID, {
      triggerCharacters: [" ", "(", "[", ",", ":", "."],
      async provideCompletionItems(model, position, _context, cancellationToken) {
        if (!state.completionEnabled) return { suggestions: [] };
        const source = model.getValue();
        const offset = model.getOffsetAt(position);
        if (!isAtDocumentFrontier(source, offset)) return { suggestions: [] };
        try {
          const result = await requestCompletions(source, offset);
          if (cancellationToken.isCancellationRequested) return { suggestions: [] };
          renderCompletions(result, source, offset);
          return {
            suggestions: result.items.map((item, index) => ({
              label: item.label,
              kind: monacoCompletionKind(monaco, item.kind),
              insertText: item.insertText,
              filterText: item.filterText,
              range: itemRange(model, monaco, item),
              sortText: String(index).padStart(4, "0"),
              preselect: index === 0,
              detail: completionDetail(item),
              documentation: item.actionKind === "insert_newline"
                ? "Layout action: insert one logical newline and deterministic indentation."
                : "Hybrid trigram prediction over parser-legal token categories.",
            })),
          };
        } catch (error) {
          console.warn("Completion request failed", error);
          return { suggestions: [] };
        }
      },
    });

    if (typeof monaco.languages.registerInlineCompletionsProvider === "function") {
      monaco.languages.registerInlineCompletionsProvider(LANGUAGE_ID, {
        async provideInlineCompletions(model, position, _context, cancellationToken) {
          if (!state.completionEnabled) return { items: [] };
          const source = model.getValue();
          const offset = model.getOffsetAt(position);
          if (!isAtDocumentFrontier(source, offset)) return { items: [] };
          try {
            const result = await requestCompletions(source, offset);
            if (cancellationToken.isCancellationRequested || !result.items.length) {
              return { items: [] };
            }
            renderCompletions(result, source, offset);
            const first = result.items[0];
            // NEWLINE has its own compact inline action hint. Returning it to
            // Monaco too would render the same prediction twice.
            if (first.actionKind === "insert_newline") return { items: [] };
            return {
              items: [{
                insertText: first.insertText,
                range: itemRange(model, monaco, first),
              }],
            };
          } catch (error) {
            return { items: [] };
          }
        },
        disposeInlineCompletions() {},
        freeInlineCompletions() {},
      });
    }
  }

  function updateMarginLine() {
    if (state.mode !== "monaco" || !state.editor) return;
    const host = document.querySelector(".editor-host");
    if (!host) return;
    const left = state.editor.getLayoutInfo().contentLeft;
    host.style.setProperty("--margin-left", `${Math.max(0, left)}px`);
    host.classList.add("margin-ready");
  }

  function initFallback(initialSource) {
    state.mode = "fallback";
    state.editor = dom["fallback-editor"];
    const host = document.querySelector(".editor-host");
    if (host) host.classList.add("no-margin-line");
    dom.editor.hidden = true;
    state.editor.hidden = false;
    state.editor.value = initialSource;
    dom["offline-banner"].hidden = false;
    dom["editor-mode"].textContent = t("offlineEditor");
    state.editor.addEventListener("input", onEditorChanged);
    ["click", "keyup", "select"].forEach((eventName) => {
      state.editor.addEventListener(eventName, () => {
        updateCursorStatus();
        scheduleCompletions(90);
      });
    });
    state.editor.addEventListener("keydown", (event) => {
      if (event.key === "Tab") {
        event.preventDefault();
        handleFallbackTab();
      }
    });
    state.editor.focus();
  }

  async function handleFallbackTab() {
    const source = getEditorValue();
    const offset = getCursorOffset();
    if (!state.completionEnabled) {
      insertFallbackText(offset, offset, "    ");
      return;
    }
    let result = null;
    if (
      state.suggestionContext &&
      state.suggestionContext.source === source &&
      state.suggestionContext.offset === offset &&
      state.latestSuggestions.length
    ) {
      applySuggestion(state.latestSuggestions[0]);
      return;
    }
    try {
      result = await requestCompletions(source, offset);
    } catch (_error) {
      result = null;
    }
    if (getEditorValue() !== source || getCursorOffset() !== offset) return;
    if (result && result.items.length) {
      renderCompletions(result, source, offset);
      applySuggestion(result.items[0]);
    } else {
      insertFallbackText(offset, offset, "    ");
    }
  }

  function onEditorChanged() {
    if (state.suppressChange) return;
    updateNewlineDecoration(null);
    localStorage.setItem(STORAGE_SOURCE, getEditorValue());
    setDirty(true);
    updateCursorStatus();
    clearIfEditingExistingText();
    scheduleCompletions(110);
    scheduleDiagnostics(550);
  }

  function scheduleCompletions(delay = 110) {
    clearTimeout(state.completionTimer);
    state.completionTimer = setTimeout(refreshCompletions, delay);
  }

  async function refreshCompletions() {
    if (!state.editor) return;
    if (!state.completionEnabled) {
      state.latestSuggestions = [];
      state.suggestionContext = null;
      updateNewlineDecoration(null);
      setCompletionStatus(t("completionOff"));
      return;
    }
    const source = getEditorValue();
    const offset = getCursorOffset();
    if (!isAtDocumentFrontier(source, offset)) {
      renderCompletions(
        { items: [], elapsedMs: 0, fallback: "editing_existing_text" },
        source,
        offset,
      );
      return;
    }
    const sequence = ++state.completionSequence;
    try {
      const result = await requestCompletions(source, offset);
      if (sequence !== state.completionSequence) return;
      if (source !== getEditorValue() || offset !== getCursorOffset()) return;
      renderCompletions(result, source, offset);
    } catch (error) {
      if (sequence !== state.completionSequence) return;
      renderCompletionError(error);
    }
  }

  function scheduleDiagnostics(delay = 550) {
    clearTimeout(state.diagnosticsTimer);
    state.diagnosticsTimer = setTimeout(() => compileNow(true), delay);
  }

  async function compileNow(silent) {
    if (!state.editor) return;
    const source = getEditorValue();
    const sequence = ++state.compileSequence;
    dom["compile-button"].disabled = true;
    dom["compile-state"].textContent = silent ? t("checking") : t("compiling");
    try {
      const result = await postJSON("/api/compile", { source });
      if (sequence !== state.compileSequence || source !== getEditorValue()) return;
      renderProblems(result);
      if (!silent) switchOutputPanel(result.ok ? "python" : "problems");
    } catch (error) {
      if (sequence !== state.compileSequence) return;
      dom["compile-state"].textContent = `${t("compileFailed")}: ${error.message}`;
    } finally {
      if (sequence === state.compileSequence) dom["compile-button"].disabled = false;
    }
  }

  async function runNow() {
    if (!state.editor) return;
    const source = getEditorValue();
    const sequence = ++state.runSequence;
    setRunBusy(true);
    switchOutputPanel("console");
    dom["console-output"].classList.remove("error");
    dom["console-output"].textContent = t("startingProgram");
    dom["run-meta"].textContent = t("running");
    dom["compile-state"].textContent = t("compileAndRun");
    try {
      const result = await postJSON("/api/run", {
        source,
        stdin: dom["stdin-input"].value,
      });
      if (sequence !== state.runSequence) return;
      if (source !== getEditorValue()) return;
      renderRunResult(result || {});
    } catch (error) {
      if (sequence !== state.runSequence) return;
      dom["console-output"].classList.add("error");
      dom["console-output"].textContent = [
        `${t("runUnavailable")}: ${error.message}`,
        "",
        t("stillDiagnostics"),
      ].join("\n");
      dom["run-meta"].textContent = t("runFailed");
      dom["compile-state"].textContent = t("runFailed");
    } finally {
      if (sequence === state.runSequence) setRunBusy(false);
    }
  }

  function setRunBusy(running) {
    document.body.classList.toggle("is-running", running);
    dom["run-button"].disabled = running;
    dom["console-run-button"].disabled = running;
  }

  function renderRunResult(result) {
    state.lastRun = result;
    renderEntrypoint(result.entrypoint);

    const runDiagnostics = Array.isArray(result.diagnostics)
      ? result.diagnostics
      : [];
    renderProblems({
      ok: !runDiagnostics.some((item) => item && item.severity === "error"),
      diagnostics: runDiagnostics,
      python: typeof result.python === "string" ? result.python : "",
      tokens: Array.isArray(result.tokens) ? result.tokens : [],
      elapsedMs: Number(result.elapsedMs || 0),
    });

    const stdout = typeof result.stdout === "string"
      ? result.stdout
      : (typeof result.output === "string" ? result.output : "");
    const stderr = typeof result.stderr === "string" ? result.stderr : "";
    const chunks = [];
    if (stdout) chunks.push(stdout.replace(/\s+$/, ""));
    if (stderr) chunks.push(`[stderr]\n${stderr.replace(/\s+$/, "")}`);
    if (result.error && !stderr) chunks.push(`[runtime error]\n${String(result.error)}`);
    if (result.timedOut) {
      chunks.push(`[runner]\n${t("runnerLimit")}`);
    }
    if (result.truncated) {
      chunks.push(`[runner]\n${t("truncated")}`);
    }
    if (Object.prototype.hasOwnProperty.call(result, "returnValue")) {
      chunks.push(`[return] ${String(result.returnValue)}`);
    }
    if (!chunks.length) {
      chunks.push(result.ok === false ? t("didNotRun") : t("noOutput"));
    }

    dom["console-output"].textContent = chunks.join("\n\n");
    dom["console-output"].classList.toggle(
      "error",
      result.ok === false && !stdout,
    );

    const exitCode = result.exitCode ?? result.returnCode ?? result.returncode;
    const meta = [];
    if (result.timedOut) meta.push(t("timedOut"));
    else if (exitCode !== undefined && exitCode !== null) meta.push(`Exit ${exitCode}`);
    else meta.push(result.ok === false ? t("failed") : t("finished"));
    if (Number.isFinite(Number(result.elapsedMs))) {
      meta.push(`${Number(result.elapsedMs).toFixed(1)} ms`);
    }
    dom["run-meta"].textContent = meta.join(" · ");
    dom["compile-state"].textContent = `Run ${meta.join(" · ")}`;
    if (result.workspace) renderWorkspace(result.workspace);
  }

  function renderWorkspace(workspace) {
    if (!workspace || typeof workspace !== "object") return;
    state.workspace = workspace;
    const path = String(workspace.path || "");
    const shortPath = path.replace(/^.*[\\/](?=[^\\/]+[\\/][^\\/]+$)/, "…/");
    if (dom["workspace-path"]) {
      dom["workspace-path"].textContent = shortPath || path || t("noFolder");
      dom["workspace-path"].title = path;
    }
    if (dom["workspace-status"]) {
      const leaf = path.split(/[\\/]/).filter(Boolean).pop() || "workspace";
      dom["workspace-status"].textContent = leaf;
      dom["workspace-status"].title = path;
    }
    const files = Array.isArray(workspace.files) ? workspace.files : [];
    if (!dom["data-file-list"]) return;
    dom["data-file-list"].replaceChildren();
    if (!files.length) {
      const empty = document.createElement("div");
      empty.className = "empty-state data-empty";
      empty.textContent = t("noDataFiles");
      dom["data-file-list"].append(empty);
      return;
    }
    files.forEach((file) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "data-row";
      button.dataset.name = file.name;
      const name = document.createElement("span");
      name.textContent = file.name;
      const size = document.createElement("span");
      size.className = "data-row-size";
      size.textContent = `${file.size} B`;
      button.append(name, size);
      button.addEventListener("click", () => previewDataFile(file.name));
      dom["data-file-list"].append(button);
    });
  }

  async function previewDataFile(name) {
    try {
      const result = await getJSON(`/api/workspace/file?name=${encodeURIComponent(name)}`);
      dom["data-preview"].hidden = false;
      dom["data-preview"].textContent = result.content || t("emptyPreview");
      document.querySelectorAll(".data-row").forEach((row) => {
        row.classList.toggle("active", row.dataset.name === name);
      });
    } catch (error) {
      window.alert(error.message);
    }
  }

  async function importDataFile() {
    const file = dom["data-file-input"].files && dom["data-file-input"].files[0];
    if (!file) return;
    try {
      const content = await file.text();
      renderWorkspace(await postJSON("/api/workspace/file", {
        name: sanitiseFileName(file.name),
        content,
      }));
    } catch (error) {
      window.alert(error.message);
    } finally {
      dom["data-file-input"].value = "";
    }
  }

  async function createDataFile() {
    const name = window.prompt(t("newFilePrompt"), "notes.txt");
    if (!name) return;
    try {
      renderWorkspace(await postJSON("/api/workspace/file", {
        name: sanitiseFileName(name),
        content: "",
      }));
    } catch (error) {
      window.alert(error.message);
    }
  }

  function renderEntrypoint(entrypoint) {
    if (!entrypoint || typeof entrypoint !== "object") {
      dom["entrypoint-hint"].hidden = true;
      dom["entrypoint-hint"].textContent = "";
      return;
    }
    const kind = String(entrypoint.kind || "entrypoint").toUpperCase();
    const name = String(entrypoint.name || "").trim();
    const parameters = Array.isArray(entrypoint.parameters)
      ? entrypoint.parameters
      : [];
    const parameterText = parameters.map((parameter, index) => {
      if (!parameter || typeof parameter !== "object") return `${t("argument")} ${index + 1}`;
      const parameterName = String(parameter.name || `${t("argument")} ${index + 1}`);
      const type = parameter.type ? `: ${parameter.type}` : "";
      const passBy = parameter.passBy ? ` ${parameter.passBy}` : "";
      return `${parameterName}${type}${passBy}`;
    }).join(", ");
    const returnType = entrypoint.returnType ? ` → ${entrypoint.returnType}` : "";
    const detected = `${t("detected")} ${kind}${name ? ` ${name}` : ""}${returnType}`;
    dom["entrypoint-hint"].textContent = parameters.length
      ? `${detected} — ${t("inputOrder")}: ${parameterText}`
      : `${detected} — ${t("noParams")}`;
    dom["entrypoint-hint"].hidden = false;
  }

  const FILE_OP_KEYWORDS = [
    "OPENFILE", "READFILE", "WRITEFILE", "CLOSEFILE",
    "SEEK", "GETRECORD", "PUTRECORD", "EOF",
  ];

  function isFileOperationContext(source, cursorOffset) {
    const prefix = source.slice(0, cursorOffset);
    const rawLine = prefix.split("\n").pop() || "";
    let line = rawLine;
    let inDouble = false;
    let inSingle = false;
    for (let index = 0; index < rawLine.length; index += 1) {
      const char = rawLine[index];
      if (char === "\"" && !inSingle) inDouble = !inDouble;
      else if ((char === "'" || char === "\u2018" || char === "\u2019") && !inDouble) {
        inSingle = !inSingle;
      } else if (
        char === "/" && rawLine[index + 1] === "/" && !inDouble && !inSingle
      ) {
        line = rawLine.slice(0, index);
        break;
      }
    }
    const upper = line.toUpperCase();
    for (const name of FILE_OP_KEYWORDS) {
      const re = new RegExp(`(?:^|[^A-Z0-9_])${name}(?![A-Z0-9_])`);
      if (re.test(upper)) return true;
    }
    const match = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)/);
    if (!match || match[1].length < 3) return false;
    const word = match[1].toUpperCase();
    return FILE_OP_KEYWORDS.some((name) => name.startsWith(word));
  }

  function requestCompletions(source, cursorOffset) {
    if (isFileOperationContext(source, cursorOffset)) {
      return Promise.resolve({ items: [], fallback: "file_operation", elapsedMs: 0 });
    }
    const key = `${cursorOffset}\u0000${source}`;
    if (state.completionCache.has(key)) return state.completionCache.get(key);
    const promise = postJSON("/api/completions", { source, cursorOffset, limit: 8 })
      .catch((error) => {
        state.completionCache.delete(key);
        throw error;
      });
    state.completionCache.set(key, promise);
    if (state.completionCache.size > 40) {
      const oldest = state.completionCache.keys().next().value;
      state.completionCache.delete(oldest);
    }
    return promise;
  }

  function renderCompletions(result, source, offset) {
    state.latestSuggestions = result.items || [];
    state.suggestionContext = { source, offset };
    const first = state.latestSuggestions[0];
    updateNewlineDecoration(first);
    if (!first) {
      setCompletionStatus(
        result.fallback === "editing_existing_text"
          ? t("completionPaused")
          : result.fallback === "file_operation"
            ? t("completionFileOp")
            : t("completionIdle"),
      );
      return;
    }

    const isNewline = first.actionKind === "insert_newline";
    setCompletionStatus(isNewline
      ? `\u21b5  ${t("tabNewLine")}`
      : `Tab: ${first.label}`,
    isNewline);
  }

  function renderCompletionError(error) {
    updateNewlineDecoration(null);
    setCompletionStatus(`${t("completionUnavailable")}: ${error.message}`);
  }

  function applySuggestion(item) {
    if (!item) return;
    const currentSource = getEditorValue();
    const currentOffset = getCursorOffset();
    if (
      !state.suggestionContext ||
      state.suggestionContext.source !== currentSource ||
      state.suggestionContext.offset !== currentOffset
    ) {
      scheduleCompletions(0);
      return;
    }
    if (state.mode === "monaco") {
      const model = state.editor.getModel();
      const start = model.getPositionAt(item.replaceStart);
      const end = model.getPositionAt(item.replaceEnd);
      const range = new state.monaco.Range(
        start.lineNumber,
        start.column,
        end.lineNumber,
        end.column,
      );
      state.editor.executeEdits("pseudocode-completion", [{
        range,
        text: item.insertText,
        forceMoveMarkers: true,
      }]);
      const newOffset = item.replaceStart + item.insertText.length;
      state.editor.setPosition(model.getPositionAt(newOffset));
      state.editor.focus();
    } else {
      insertFallbackText(item.replaceStart, item.replaceEnd, item.insertText);
    }
    scheduleCompletions(30);
  }

  function insertFallbackText(start, end, text) {
    const source = state.editor.value;
    state.editor.setRangeText(text, start, end, "end");
    if (source === state.editor.value) return;
    state.editor.dispatchEvent(new Event("input", { bubbles: true }));
    state.editor.focus();
  }

  function renderProblems(result) {
    state.lastCompile = result;
    const diagnostics = result.diagnostics || [];
    const elapsed = Number(result.elapsedMs || 0);
    const python = result.python || "";
    dom["problem-count"].textContent = String(diagnostics.length);
    if (result.ok && !diagnostics.length && !python.trim()) {
      dom["compile-state"].textContent = t("ready");
    } else {
      dom["compile-state"].textContent = result.ok
        ? `${t("compiled")} · ${elapsed.toFixed(1)} ms`
        : `${diagnostics.length} ${t("problemSummary")} · ${elapsed.toFixed(1)} ms`;
    }
    dom["python-panel"].textContent = python || t("noPython");
    dom["problems-panel"].replaceChildren();

    if (!diagnostics.length) {
      const empty = document.createElement("div");
      empty.className = "empty-state success";
      empty.textContent = t("noProblems");
      dom["problems-panel"].append(empty);
    } else {
      diagnostics.forEach((diagnostic) => {
        const row = document.createElement("div");
        row.className = "problem-row";
        row.addEventListener("click", () => goToLocation(diagnostic.line, diagnostic.column));
        const icon = document.createElement("span");
        icon.className = `problem-icon ${diagnostic.severity}`;
        icon.textContent = diagnostic.severity === "warning" ? "△" : "×";
        const content = document.createElement("span");
        content.className = "problem-message";
        content.textContent = diagnostic.message;
        if (diagnostic.suggestion) {
          const hint = document.createElement("span");
          hint.className = "problem-hint";
          hint.textContent = `${t("hint")}: ${diagnostic.suggestion}`;
          content.append(hint);
        }
        const location = document.createElement("span");
        location.className = "problem-location";
        location.textContent = `Ln ${diagnostic.line}:${diagnostic.column}`;
        row.append(icon, content, location);
        dom["problems-panel"].append(row);
      });
    }

    renderTokens(result.tokens || []);
    setMonacoMarkers(diagnostics);
  }

  function renderTokens(tokens) {
    dom["tokens-panel"].replaceChildren();
    if (!tokens.length) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = t("noTokens");
      dom["tokens-panel"].append(empty);
      return;
    }
    tokens.forEach((token) => {
      const row = document.createElement("div");
      row.className = "token-row";
      const location = document.createElement("span");
      location.className = "token-location";
      location.textContent = `${token.line}:${token.column}`;
      const type = document.createElement("span");
      type.className = "token-type";
      type.textContent = token.type;
      const value = document.createElement("span");
      value.className = "token-value";
      value.textContent = JSON.stringify(token.value);
      row.append(location, type, value);
      dom["tokens-panel"].append(row);
    });
  }

  function setMonacoMarkers(diagnostics) {
    if (state.mode !== "monaco" || !state.editor) return;
    const model = state.editor.getModel();
    const lineCount = model.getLineCount();
    const markers = diagnostics.map((diagnostic) => {
      const line = Math.min(Math.max(1, diagnostic.line), lineCount);
      const maxColumn = model.getLineMaxColumn(line);
      const startColumn = Math.min(Math.max(1, diagnostic.column), maxColumn);
      return {
        severity: diagnostic.severity === "warning"
          ? state.monaco.MarkerSeverity.Warning
          : state.monaco.MarkerSeverity.Error,
        startLineNumber: line,
        startColumn,
        endLineNumber: line,
        endColumn: Math.min(Math.max(startColumn + 1, diagnostic.endColumn || startColumn + 1), maxColumn),
        message: diagnostic.suggestion
          ? `${diagnostic.message}\n${t("hint")}: ${diagnostic.suggestion}`
          : diagnostic.message,
        source: "pseudocode compiler",
      };
    });
    state.monaco.editor.setModelMarkers(model, "pseudocode-compiler", markers);
  }

  function switchOutputPanel(name) {
    document.querySelectorAll(".output-tab").forEach((button) => {
      button.classList.toggle("active", button.dataset.panel === name);
    });
    document.querySelectorAll(".output-view").forEach((panel) => {
      panel.classList.toggle("active", panel.id === `${name}-panel`);
    });
  }

  function goToLocation(line, column) {
    if (state.mode === "monaco") {
      state.editor.setPosition({ lineNumber: line, column });
      state.editor.revealPositionInCenter({ lineNumber: line, column });
      state.editor.focus();
      return;
    }
    const source = state.editor.value;
    const lines = source.split("\n");
    let offset = 0;
    for (let index = 0; index < Math.max(0, line - 1); index += 1) {
      offset += (lines[index] || "").length + 1;
    }
    offset += Math.max(0, column - 1);
    state.editor.setSelectionRange(offset, offset);
    state.editor.focus();
  }

  function getEditorValue() {
    if (!state.editor) return "";
    return state.mode === "monaco" ? state.editor.getValue() : state.editor.value;
  }

  function setEditorValue(source) {
    state.suppressChange = true;
    if (state.mode === "monaco") {
      state.editor.setValue(source);
      state.editor.setPosition({ lineNumber: 1, column: 1 });
    } else if (state.editor) {
      state.editor.value = source;
      state.editor.setSelectionRange(0, 0);
    }
    state.suppressChange = false;
    localStorage.setItem(STORAGE_SOURCE, source);
    updateCursorStatus();
    scheduleCompletions(20);
    scheduleDiagnostics(50);
  }

  function getCursorOffset() {
    if (!state.editor) return 0;
    if (state.mode === "monaco") {
      return state.editor.getModel().getOffsetAt(state.editor.getPosition());
    }
    return state.editor.selectionStart;
  }

  function updateCursorStatus() {
    if (!state.editor) return;
    if (state.mode === "monaco") {
      const position = state.editor.getPosition();
      dom["cursor-position"].textContent = `Ln ${position.lineNumber}, Col ${position.column}`;
      return;
    }
    const offset = state.editor.selectionStart;
    const before = state.editor.value.slice(0, offset);
    const lines = before.split("\n");
    dom["cursor-position"].textContent = `Ln ${lines.length}, Col ${lines[lines.length - 1].length + 1}`;
  }

  async function openSelectedFile() {
    const file = dom["file-input"].files && dom["file-input"].files[0];
    if (!file) return;
    try {
      const source = await file.text();
      setEditorValue(source);
      setFileName(file.name || "main.pseudo");
      setDirty(false);
      compileNow(true);
    } finally {
      dom["file-input"].value = "";
    }
  }

  function saveFile() {
    if (!state.editor) return;
    const blob = new Blob([getEditorValue()], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = state.fileName;
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    setDirty(false);
  }

  function setFileName(name) {
    state.fileName = sanitiseFileName(name);
    ["file-name", "explorer-file-name", "tab-file-name"].forEach((id) => {
      dom[id].textContent = state.fileName;
    });
    localStorage.setItem(STORAGE_FILE, state.fileName);
  }

  function setDirty(dirty) {
    state.dirty = dirty;
    document.body.classList.toggle("dirty", dirty);
  }

  function itemRange(model, monaco, item) {
    const start = model.getPositionAt(item.replaceStart);
    const end = model.getPositionAt(item.replaceEnd);
    return new monaco.Range(start.lineNumber, start.column, end.lineNumber, end.column);
  }

  function monacoCompletionKind(monaco, kind) {
    const kinds = monaco.languages.CompletionItemKind;
    return {
      keyword: kinds.Keyword,
      operator: kinds.Operator,
      identifier: kinds.Variable,
      literal: kinds.Value,
      punctuation: kinds.Text,
      layout: kinds.Snippet,
    }[kind] || kinds.Text;
  }

  function completionDetail(item) {
    if (item.actionKind === "insert_newline") {
      return item.decisionSource === "complete_statement_newline"
        ? "NEWLINE | statement boundary + layout support"
        : `NEWLINE | layout ${formatProbability(item.probability)}`;
    }
    return `${item.tokenType} | P(${formatTokenType(item.tokenType)}) ${formatProbability(item.probability)} | ${legalityText(item.legal)} | ${surfaceSourceText(item.surfaceSource)}`;
  }

  function formatTokenType(tokenType) {
    return String(tokenType || "LAYOUT").replace("KEYWORD_", "");
  }

  function surfaceSourceText(source) {
    return {
      placeholder: "editor placeholder",
      document_identifier: "document identifier",
      type_context: "type context",
      type_prefix: "type prefix",
      keyword_prefix: "keyword prefix",
      lexical_prefix: "lexical prefix",
      canonical_literal: "literal template",
      fixed_token: "fixed spelling",
      layout_action: "layout action",
    }[source] || "surface adapter";
  }

  function pill(text) {
    const element = document.createElement("span");
    element.className = "pill";
    element.textContent = text;
    return element;
  }

  function legalityPill(legal) {
    const element = pill(legalityText(legal));
    if (legal === true) element.classList.add("legal");
    if (legal === false) element.classList.add("illegal");
    return element;
  }

  function legalityText(legal) {
    if (legal === true) return "parser-legal";
    if (legal === false) return "soft fallback";
    return "ngram fallback";
  }

  function formatProbability(probability) {
    return `${(Number(probability || 0) * 100).toFixed(1)}%`;
  }

  function visibleWhitespace(text) {
    return text.replace(/^ /, "\u00b7 ").replace(/ $/, " \u00b7");
  }

  function isAtDocumentFrontier(source, offset) {
    // A final newline and blank lines are normal EOF whitespace, not old code.
    return !source.slice(offset).trim();
  }

  function clearIfEditingExistingText() {
    if (!state.editor) return;
    const source = getEditorValue();
    const offset = getCursorOffset();
    if (!isAtDocumentFrontier(source, offset)) {
      renderCompletions(
        { items: [], elapsedMs: 0, fallback: "editing_existing_text" },
        source,
        offset,
      );
    }
  }

  function updateNewlineDecoration(item) {
    if (state.mode !== "monaco" || !state.editor) return;
    const decorations = [];
    if (item && item.actionKind === "insert_newline") {
      const position = state.editor.getPosition();
      decorations.push({
        range: new state.monaco.Range(
          position.lineNumber,
          position.column,
          position.lineNumber,
          position.column,
        ),
        options: {
          after: {
            // Keep the complete affordance in Monaco's native injected text.
            // Pseudo-elements on a view-line span are not rendered reliably.
            content: "  \u21b5  new line  [Tab]",
            inlineClassName: "newline-ghost-decoration",
            inlineClassNameAffectsLetterSpacing: false,
          },
        },
      });
    }
    state.newlineDecorationIds = state.editor.deltaDecorations(
      state.newlineDecorationIds,
      decorations,
    );
  }

  function setCompletionStatus(text, active = false) {
    if (!dom["completion-status"]) return;
    dom["completion-status"].textContent = text;
    dom["completion-status"].classList.toggle("active", active);
  }

  function sanitiseFileName(name) {
    const cleaned = String(name || "main.pseudo").replace(/[\\/:*?"<>|]/g, "-").trim();
    return cleaned || "main.pseudo";
  }

  function slugify(value) {
    return String(value).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "example";
  }

  async function getJSON(url) {
    const response = await fetch(url, { headers: { Accept: "application/json" } });
    return parseResponse(response);
  }

  async function postJSON(url, payload) {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(payload),
    });
    return parseResponse(response);
  }

  async function parseResponse(response) {
    let payload = null;
    try {
      payload = await response.json();
    } catch (_error) {
      throw new Error(`Server returned ${response.status}`);
    }
    if (!response.ok) throw new Error(payload.error || `Server returned ${response.status}`);
    return payload;
  }
})();
