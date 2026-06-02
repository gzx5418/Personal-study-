App.register("resources", {
  title: "资源中心",

  render() {
    const types = ["all", "lecture", "quiz", "code_lab", "mindmap", "ppt_outline", "extended_reading", "animation", "document"];
    const typeLabels = {
      all: "全部",
      lecture: "讲义",
      quiz: "题库",
      code_lab: "代码实训",
      mindmap: "思维导图",
      ppt_outline: "PPT提纲",
      extended_reading: "拓展阅读",
      animation: "动画脚本",
      document: "文档",
    };

    return `
      <div class="resources">
        <div class="section-head">
          <div>
            <h2 class="section-title">资源中心</h2>
            <p class="section-subtitle">根据学习画像个性化推荐</p>
          </div>
          <div class="filter-bar">
            ${types.map(t => `
              <button class="filter-btn ${t === "all" ? "is-active" : ""}" data-filter="${t}">${typeLabels[t]}</button>
            `).join("")}
          </div>
        </div>

        <div class="res-gen-bar">
          <input type="text" class="tutor-input" id="resTopicInput" placeholder="输入知识点，自动生成个性化资源...">
          <select id="resTypeSelect" class="tutor-input" style="width:auto;margin-left:8px">
            <option value="lecture">讲义</option>
            <option value="quiz">练习题</option>
            <option value="code_lab">代码案例</option>
            <option value="mindmap">思维导图</option>
            <option value="ppt_outline">PPT提纲</option>
            <option value="extended_reading">拓展阅读</option>
            <option value="animation">动画脚本</option>
          </select>
          <button class="btn btn-primary" id="resGenBtn" style="margin-left:8px">生成</button>
          <input type="file" id="resFileInput" accept=".py,.js,.ts,.jsx,.tsx,.java,.cpp,.c,.h,.hpp,.html,.css,.json,.sql,.sh,.bat,.ps1,.txt,.md,.csv,.yaml,.yml,.pdf,.docx,.log,.r,.rb,.go,.rs,.swift,.kt,.php,.pl,.lua" style="display:none">
          <button class="btn btn-ghost" id="resUploadBtn" style="margin-left:var(--space-2)">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:middle;margin-right:4px"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
            上传资源
          </button>
        </div>

        <div class="res-grid" id="resGrid">
          <p style="color:var(--color-ink-light);padding:var(--space-8);text-align:center">输入知识点并点击「生成」，AI 将为您生成个性化学习资源</p>
        </div>
      </div>
    `;
  },

  bind(container) {
    this._cleanupListeners();
    $$(".filter-btn", container).forEach((btn) => {
      this._addListener(btn, "click", () => {
        $$(".filter-btn", container).forEach(b => b.classList.remove("is-active"));
        btn.classList.add("is-active");
        const filter = btn.dataset.filter;
        this._loadSavedResources(container, filter);
      });
    });

    // Delegated click for resource open buttons
    const grid = $("#resGrid", container);
    if (grid) {
      this._addListener(grid, "click", (e) => {
        const previewBtn = e.target.closest("[data-preview-id]");
        if (previewBtn) {
          const resource = (this._lastResources || []).find(r => r.id === previewBtn.dataset.previewId);
          if (resource) this._showPreviewModal(resource);
          return;
        }
        const star = e.target.closest(".res-star");
        if (star) {
          const ratingContainer = star.closest(".res-card-rating");
          if (ratingContainer) {
            const resourceId = ratingContainer.dataset.ratingId;
            const value = parseInt(star.dataset.star);
            if (resourceId && value) this._rateResource(resourceId, value);
          }
          return;
        }
        const btn = e.target.closest("[data-open-id]");
        if (btn) {
          grid.dispatchEvent(new CustomEvent("open-resource", { detail: btn.dataset.openId }));
        }
      });
      // 统一在这里绑定 open-resource 自定义事件，避免 _loadSavedResources 重复绑定
      this._addListener(grid, "open-resource", (e) => {
        this._handleOpenResource(e.detail, grid, container, this._currentFilter || "all");
      });
    }

    const genBtn = $("#resGenBtn", container);
    const topicInput = $("#resTopicInput", container);
    const typeSelect = $("#resTypeSelect", container);

    if (genBtn) {
      this._addListener(genBtn, "click", () => {
        const topic = topicInput.value.trim();
        if (!topic) { showToast("请输入知识点"); return; }
        this._generateResource(topic, typeSelect.value, grid, container);
      });
    }

    // 资源上传
    const fileInput = $("#resFileInput", container);
    const uploadBtn = $("#resUploadBtn", container);
    if (uploadBtn && fileInput) {
      this._addListener(uploadBtn, "click", () => fileInput.click());
      this._addListener(fileInput, "change", (e) => {
        const file = e.target.files[0];
        if (!file) return;
        if (file.size > AppState.maxUploadSizeMb * 1024 * 1024) {
          showToast(`文件大小不能超过 ${AppState.maxUploadSizeMb}MB`);
          return;
        }
        this._uploadResource(file, container);
        fileInput.value = "";
      });
    }

    this._loadSavedResources(container, "all");
  },

  _cleanupListeners() {
    if (this._eventCleanups && this._eventCleanups.length) {
      this._eventCleanups.forEach((fn) => {
        try { fn(); } catch (e) {}
      });
    }
    this._eventCleanups = [];
    // 重绑时也重置 grid 列表状态标记，避免老状态泄露
    this._gridListenerReady = false;
  },

  _addListener(element, event, handler, options) {
    if (!element) return;
    if (!this._eventCleanups) this._eventCleanups = [];
    element.addEventListener(event, handler, options);
    this._eventCleanups.push(() => {
      try { element.removeEventListener(event, handler, options); } catch (e) {}
    });
  },

  async _uploadResource(file, container) {
    showToast("正在上传: " + file.name);
    try {
      const ext = file.name.split(".").pop().toLowerCase();
      const textExts = ["txt", "md", "csv", "yaml", "yml", "json", "log", "py", "js", "ts", "jsx", "tsx", "java", "cpp", "c", "h", "hpp", "html", "css", "sql", "sh", "bat", "ps1", "r", "rb", "go", "rs", "swift", "kt", "php", "pl", "lua"];
      const binaryExts = ["pdf", "docx"];

      if (!textExts.includes(ext) && !binaryExts.includes(ext)) {
        showToast("不支持的文件类型: ." + ext);
        return;
      }

      const formData = new FormData();
      formData.append("file", file);
      formData.append("user_id", AppState.currentUserId);
      formData.append("topic", file.name.replace(/\.[^.]+$/, ""));
      formData.append("course_id", AppState.currentCourseId);

      const res = await fetch(`${AppState.apiBase}/api/resources/upload-file`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (data.success) {
        showToast("上传成功: " + file.name + " (" + (data.text_length || 0) + " 字)");
        this._loadSavedResources(container, "all");
      } else {
        showToast("上传失败");
      }
    } catch (e) {
      console.error("Upload failed:", e);
      showToast("上传失败，请稍后重试");
    }
  },

  async _loadSavedResources(container, filter) {
    const grid = $("#resGrid", container);
    if (!grid) return;
    this._currentFilter = filter;
    grid.innerHTML = this._renderSkeletonCards(6);
    try {
      const data = await Api.listResources(AppState.currentUserId, filter, AppState.currentCourseId);
      const resources = data.resources || [];

      if (resources.length === 0) {
        grid.innerHTML = '<p style="color:var(--color-ink-light);padding:var(--space-8);text-align:center">输入知识点并点击「生成」，AI 将为您生成个性化学习资源</p>';
        return;
      }

      const typeLabels = {
        lecture: "讲义",
        quiz: "练习题",
        code_lab: "代码实训",
        mindmap: "思维导图",
        ppt_outline: "PPT提纲",
        extended_reading: "拓展阅读",
        animation: "动画脚本",
        document: "文档",
      };
      grid.innerHTML = resources.map(r => {
        let preview = "";
        if (r.type === "quiz") {
          let questionCount = 0;
          try {
            let jsonStr = (r.content || "").trim().replace(/^```(?:json)?\s*\n?/m, '').replace(/\n?```\s*$/m, '');
            const parsed = JSON.parse(jsonStr);
            if (Array.isArray(parsed)) questionCount = parsed.length;
            else if (parsed.questions) questionCount = parsed.questions.length;
          } catch (e2) {}
          preview = questionCount > 0
            ? `<p style="color:var(--color-ink-mid);font-size:var(--text-xs)">📝 ${questionCount} 道练习题</p>`
            : `<p style="color:var(--color-ink-light);font-size:var(--text-xs)">练习题</p>`;
        } else if (r.type === "code_lab" || r.type === "document") {
          const fn = r.file_name || "";
          const fext = fn.includes(".") ? fn.split(".").pop().toLowerCase() : "";
          if (fext === "pdf") {
            preview = `<div style="display:flex;align-items:center;gap:var(--space-2);color:var(--color-ink-mid);font-size:var(--text-xs)"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>PDF文档 · 点击预览</div>`;
          } else if (fext === "docx") {
            let content = r.content || "";
            let text = content.replace(/[#*`>\[\]!]/g, "").replace(/\n+/g, " ").trim();
            preview = `<p style="font-size:var(--text-xs);color:var(--color-ink-light);line-height:1.5;max-height:60px;overflow:hidden">${this.escapeHtml(text.substring(0, 200))}${text.length > 200 ? '...' : ''}</p>`;
          } else {
            let content = r.content || "";
            let codeBlock = "";
            const codeMatch = content.match(/```(\w*)\n([\s\S]*?)```/);
            if (codeMatch) {
              const code = codeMatch[2].trim();
              const truncated = code.split("\n").slice(0, 6).join("\n");
              const hasMore = code.split("\n").length > 6;
              codeBlock = `<div style="background:oklch(0.15 0.02 260);border-radius:var(--radius-md);padding:var(--space-3);overflow:hidden;max-height:140px"><pre style="margin:0;background:none;color:oklch(0.88 0.01 80);font-size:var(--text-xs);line-height:1.5;white-space:pre"><code>${this.escapeHtml(truncated)}${hasMore ? "\n..." : ""}</code></pre></div>`;
            } else {
              const lines = content.split("\n").filter(l => !l.startsWith("#")).slice(0, 4).join("\n");
              codeBlock = `<pre style="background:var(--color-paper-deep);border-radius:var(--radius-md);padding:var(--space-2);font-size:var(--text-xs);color:var(--color-ink-mid);overflow:hidden;max-height:100px;white-space:pre-wrap"><code>${this.escapeHtml(lines)}...</code></pre>`;
            }
            preview = codeBlock;
          }
        } else {
          let content = r.content || "";
          let text = content.replace(/[#*`>\[\]!]/g, "").replace(/\n+/g, " ").trim();
          preview = `<p style="font-size:var(--text-xs);color:var(--color-ink-light);line-height:1.5;max-height:60px;overflow:hidden">${this.escapeHtml(text.substring(0, 200))}${text.length > 200 ? '...' : ''}</p>`;
        }

        return `
          <div class="res-card res-card-animated" data-type="${this.escapeHtml(r.type)}" data-id="${this.escapeHtml(r.id)}">
            <div class="res-card-head">
              <h4 class="res-title">${this.escapeHtml(r.topic || '未命名')}</h4>
              <div style="display:flex;align-items:center;gap:var(--space-1)">
                <span class="tag tag-filled">${(() => { const _fn = r.file_name || ""; const _fe = _fn.includes(".") ? _fn.split(".").pop().toLowerCase() : ""; return _fe === "pdf" ? "PDF" : _fe === "docx" ? "Word" : typeLabels[r.type] || r.type; })()}</span>
                <button class="btn-icon res-preview-btn" data-preview-id="${this.escapeHtml(r.id)}" title="预览">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                </button>
                <button class="btn-icon res-delete-btn" data-delete-id="${this.escapeHtml(r.id)}" data-delete-topic="${this.escapeHtml(r.topic || '')}" title="删除" style="background:none;border:none;cursor:pointer;padding:4px;color:var(--color-ink-faint);display:flex;align-items:center;transition:color 0.15s">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
                </button>
              </div>
            </div>
            <div class="res-preview">${preview}</div>
            ${r.safety_status?.checked ? `<p style="font-size:var(--text-xs);color:${r.safety_status.is_safe ? 'var(--color-sage)' : 'var(--color-rose)'};margin-top:var(--space-2)">${r.safety_status.is_safe ? '已通过安全与依据校验' : '存在安全/依据提示'}</p>` : ""}
            <div class="res-card-rating" data-rating-id="${this.escapeHtml(r.id)}">
              ${[1,2,3,4,5].map(v => `<span class="res-star${(r.user_rating || 0) >= v ? ' is-active' : ''}" data-star="${v}">★</span>`).join("")}
              <span class="res-rating-info">${r.avg_rating ? r.avg_rating.toFixed(1) + ' 分' : ''}</span>
            </div>
            <button class="btn btn-ghost btn-sm" style="margin-top:auto;width:100%" data-open-id="${this.escapeHtml(r.id)}">${(() => { const _fn = r.file_name || ""; const _fe = _fn.includes(".") ? _fn.split(".").pop().toLowerCase() : ""; return r.type === 'quiz' ? '开始作答' : _fe === 'pdf' ? '预览PDF' : _fe === 'docx' ? '预览DOCX' : '展开查看'; })()}</button>
          </div>
        `;
      }).join("");

      // Add delete button handlers
      grid.querySelectorAll(".res-delete-btn").forEach(btn => {
        on(btn, "click", (e) => {
          e.stopPropagation();
          const id = btn.dataset.deleteId;
          const topic = btn.dataset.deleteTopic;
          this._deleteResource(id, topic, container, filter);
        });
        on(btn, "mouseenter", () => { btn.style.color = "var(--color-rose)"; });
        on(btn, "mouseleave", () => { btn.style.color = "var(--color-ink-faint)"; });
      });

      // Add open button handlers
      grid.querySelectorAll("[data-open-id]").forEach(btn => {
        on(btn, "click", () => {
          grid.dispatchEvent(new CustomEvent("open-resource", { detail: btn.dataset.openId }));
        });
      });

      grid.querySelectorAll(".res-preview-btn").forEach(btn => {
        on(btn, "mouseenter", () => { btn.style.color = "var(--color-amber)"; });
        on(btn, "mouseleave", () => { btn.style.color = "var(--color-ink-faint)"; });
      });

      grid.querySelectorAll(".res-card-rating").forEach(container => {
        const stars = container.querySelectorAll(".res-star");
        on(container, "mouseenter", () => {
          stars.forEach(s => { s.style.transition = "color 0.1s, transform 0.1s"; });
        });
      });

      grid.querySelectorAll(".res-card-animated").forEach((card, i) => {
        card.style.animationDelay = `${i * 60}ms`;
      });

      this._lastResources = resources;
    } catch (e) {
      console.error("Failed to load resources:", e);
    }
  },

  _handleOpenResource(id, grid, container, filter) {
    const typeLabels = {
      lecture: "讲义", quiz: "练习题", code_lab: "代码实训",
      mindmap: "思维导图", ppt_outline: "PPT提纲", animation: "动画脚本",
      extended_reading: "拓展阅读", document: "文档",
    };
    const resources = this._lastResources || [];
    const r = resources.find(x => x.id === id);
    if (!r) return;
    Api.recordResourceEvent(r.id, "open", { type: r.type, topic: r.topic }, { sourcePage: "resources" });
    const fileName = r.file_name || "";
    const ext = fileName.includes(".") ? fileName.split(".").pop().toLowerCase() : "";
    const isPdf = ext === "pdf";
    const isDocx = ext === "docx";
    const sourceBlock = this._renderSourceBlock(r);

    if (r.type === "quiz") {
      grid.innerHTML = `
        <div class="res-card" style="grid-column:1/-1">
          <div class="res-card-head">
            <h4 class="res-title">${this.escapeHtml(r.topic)} - ${typeLabels[r.type] || r.type}</h4>
            <span class="tag tag-filled">${typeLabels[r.type] || r.type}</span>
          </div>
          <div class="res-content" style="margin-top:var(--space-4);line-height:var(--leading-normal)">
            ${this._renderMarkdown(r.content)}
          </div>
          ${sourceBlock}
          <div id="quizInteractive" style="margin-top:var(--space-4)">
            <div class="typing-dots"><span></span><span></span><span></span></div>
            <span style="color:var(--color-ink-light);font-size:var(--text-sm)"> 正在解析题目...</span>
          </div>
          <button class="btn btn-ghost btn-sm" style="margin-top:var(--space-4)" id="backToList">返回列表</button>
        </div>
      `;
      this._parseAndRenderQuiz(r.content, r.topic, container, grid);
      $("#backToList", grid)?.addEventListener("click", () => this._loadSavedResources(container, filter));
    } else if (isPdf) {
      grid.innerHTML = `
        <div class="res-card" style="grid-column:1/-1">
          <div class="res-card-head">
            <h4 class="res-title">${this.escapeHtml(r.topic)} - PDF文档</h4>
            <span class="tag tag-filled">PDF</span>
          </div>
          <div style="margin-top:var(--space-4);border-radius:var(--radius-md);overflow:hidden;border:1px solid oklch(0.90 0.01 80);background:oklch(0.95 0.01 80)">
            <iframe src="${AppState.apiBase}/api/resources/file/${encodeURIComponent(AppState.currentUserId)}/${encodeURIComponent(r.id)}" style="width:100%;height:75vh;border:none;display:block" title="PDF预览"></iframe>
          </div>
          ${sourceBlock}
          <button class="btn btn-ghost btn-sm" style="margin-top:var(--space-4)" id="backToList">返回列表</button>
        </div>
      `;
      $("#backToList", grid)?.addEventListener("click", () => this._loadSavedResources(container, filter));
    } else if (isDocx) {
      grid.innerHTML = `
        <div class="res-card" style="grid-column:1/-1">
          <div class="res-card-head">
            <h4 class="res-title">${this.escapeHtml(r.topic)} - Word文档</h4>
            <span class="tag tag-filled">DOCX</span>
          </div>
          <div id="docxPreview" style="margin-top:var(--space-4);padding:var(--space-4);border-radius:var(--radius-md);border:1px solid oklch(0.90 0.01 80);background:white;min-height:400px;overflow:auto"></div>
          ${sourceBlock}
          <button class="btn btn-ghost btn-sm" style="margin-top:var(--space-4)" id="backToList">返回列表</button>
        </div>
      `;
      this._renderDocxPreview(r.id, container);
      $("#backToList", grid)?.addEventListener("click", () => this._loadSavedResources(container, filter));
    } else {
      grid.innerHTML = `
        <div class="res-card" style="grid-column:1/-1">
          <div class="res-card-head">
            <h4 class="res-title">${this.escapeHtml(r.topic)} - ${typeLabels[r.type] || r.type}</h4>
            <span class="tag tag-filled">${typeLabels[r.type] || r.type}</span>
          </div>
          <div class="res-content" style="margin-top:var(--space-4);line-height:var(--leading-normal)">
            ${this._renderMarkdown(r.content)}
          </div>
          ${sourceBlock}
          ${r.type === "ppt_outline" ? `<a class="btn btn-primary btn-sm" style="margin-top:var(--space-4);margin-right:var(--space-2)" href="${AppState.apiBase}/api/resources/pptx/${encodeURIComponent(AppState.currentUserId)}/${encodeURIComponent(r.id)}" download>下载PPTX</a>` : ""}
          <button class="btn btn-ghost btn-sm" style="margin-top:var(--space-4)" id="backToList">返回列表</button>
        </div>
      `;
      $("#backToList", grid)?.addEventListener("click", () => this._loadSavedResources(container, filter));
    }
  },

  async _generateResource(topic, type, grid, container) {
    const typeLabels = {
      lecture: "讲义",
      quiz: "练习题",
      code_lab: "代码案例",
      mindmap: "思维导图",
      ppt_outline: "PPT提纲",
      extended_reading: "拓展阅读",
      animation: "动画脚本",
    };
    const safeTopic = escapeHtml(topic);
    showToast(`正在生成${typeLabels[type] || type}...`);

    grid.innerHTML = `
      <div class="res-card" style="grid-column:1/-1">
        <div class="msg-typing" style="padding:var(--space-8);text-align:center">
          <div class="typing-dots"><span></span><span></span><span></span></div>
          <p id="resGenStatus" style="margin-top:var(--space-4);color:var(--color-ink-light)">AI 正在生成中...</p>
          <div class="agent-chain" id="agentChain"></div>
        </div>
      </div>
    `;

    let content = "";
    let safetyWarning = "";
    let currentStage = "";
    let generatedResult = null;
    const agentChain = [];  // Track agent execution chain

    const _renderChain = () => {
      const chainEl = grid.querySelector("#agentChain");
      if (!chainEl) return;
      const stepLabels = {
        "resource_orchestrator": "编排调度",
        "lecture_agent": "讲义生成",
        "quiz_agent": "题库生成",
        "mindmap_agent": "思维导图",
        "code_lab_agent": "代码案例",
        "reading_agent": "拓展阅读",
        "animation_agent": "动画生成",
        "ppt_agent": "PPT生成",
        "generator_agent": "资源生成",
        "safety_agent": "安全审查",
      };
      chainEl.innerHTML = agentChain.map((step, i) => {
        const label = stepLabels[step.name] || step.name;
        const cls = step.status === "active" ? "active" : (step.status === "done" ? "done" : "");
        const icon = step.status === "done" ? "✓" : (step.status === "active" ? "●" : String(i + 1));
        const arrow = i < agentChain.length - 1 ? '<span class="agent-chain-arrow">→</span>' : '';
        return `<span class="agent-chain-step ${cls}"><span class="step-icon">${icon}</span>${label}</span>${arrow}`;
      }).join("");
    };

    try {
      await Api.generateResourceStream(topic, type, {
        onChunk(chunk) { content += chunk; },
        onThinking(text) {
          if (text && (text.includes("问题") || text.includes("安全") || text.includes("审查"))) {
            safetyWarning = text;
          }
        },
        onStage(event) {
          currentStage = event.description || event.stage || "";
          const statusEl = grid.querySelector("#resGenStatus");
          if (statusEl && currentStage) statusEl.textContent = currentStage;
        },
        onProgress(event) {
          const statusEl = grid.querySelector("#resGenStatus");
          if (statusEl) statusEl.textContent = `${event.message || "生成中"} (${event.current}/${event.total})`;
        },
        onAgentStart(event) {
          const existing = agentChain.find(s => s.name === event.agent_name);
          if (existing) {
            existing.status = "active";
          } else {
            agentChain.push({ name: event.agent_name, status: "active" });
          }
          _renderChain();
        },
        onAgentEnd(event) {
          const existing = agentChain.find(s => s.name === event.agent_name);
          if (existing) {
            existing.status = "done";
          }
          _renderChain();
        },
        onDone(event) {
          if (event && event.resource_id !== undefined) generatedResult = event;
          if (event?.type === "done" || event?.resource_id !== undefined) showToast("生成完成");
        },
      });

      const typeLabels = { lecture: "讲义", quiz: "练习题", code_lab: "代码案例", mindmap: "思维导图", ppt_outline: "PPT提纲", extended_reading: "拓展阅读", animation: "动画脚本", document: "文档" };
      const warningHtml = safetyWarning ? `<div style="background:var(--color-amber-surface);border:1px solid var(--color-amber-muted);border-radius:var(--radius-md);padding:var(--space-3);margin-top:var(--space-3);font-size:var(--text-sm);color:var(--color-amber)">⚠️ 安全审查提示：${safetyWarning}</div>` : '';
      const sourceHtml = this._renderSourceBlock({
        sources_used: generatedResult?.sources_used || [],
        safety_status: {
          checked: !!generatedResult?.safety,
          is_safe: generatedResult?.safety?.is_safe !== false,
          issues: generatedResult?.safety?.issues || [],
          review_skipped: generatedResult?.safety?.review_skipped || false,
        },
      });

      if (type === "quiz") {
        grid.innerHTML = `
          <div class="res-card" style="grid-column:1/-1">
            <div class="res-card-head">
              <h4 class="res-title">${safeTopic} - ${typeLabels[type]}</h4>
              <span class="tag tag-filled">${typeLabels[type]}</span>
            </div>
            <div class="res-content" style="margin-top:var(--space-4);line-height:var(--leading-normal)">
              ${this._renderMarkdown(content)}
            </div>
            ${warningHtml}
            ${sourceHtml}
            <div id="quizInteractive" style="margin-top:var(--space-4)">
              <div class="typing-dots"><span></span><span></span><span></span></div>
              <span style="color:var(--color-ink-light);font-size:var(--text-sm)"> 正在解析题目...</span>
            </div>
            <button class="btn btn-ghost btn-sm" style="margin-top:var(--space-4)" id="backToList">返回列表</button>
          </div>
        `;
        this._parseAndRenderQuiz(content, topic, container, grid);
      } else {
        grid.innerHTML = `
          <div class="res-card" style="grid-column:1/-1">
            <div class="res-card-head">
              <h4 class="res-title">${safeTopic} - ${typeLabels[type]}</h4>
              <span class="tag tag-filled">${typeLabels[type]}</span>
            </div>
            <div class="res-content" style="margin-top:var(--space-4);line-height:var(--leading-normal)">
              ${this._renderMarkdown(content)}
            </div>
            ${warningHtml}
            ${sourceHtml}
            ${type === "ppt_outline" && generatedResult?.resource_id ? `<a class="btn btn-primary btn-sm" style="margin-top:var(--space-4);margin-right:var(--space-2)" href="${AppState.apiBase}/api/resources/pptx/${encodeURIComponent(AppState.currentUserId)}/${encodeURIComponent(generatedResult.resource_id)}" download>下载PPTX</a>` : ""}
            <button class="btn btn-ghost btn-sm" style="margin-top:var(--space-4)" id="backToList">返回列表</button>
          </div>
        `;
      }

      if (container) {
        $("#backToList", grid)?.addEventListener("click", () => this._loadSavedResources(container, "all"));
      }
      if (generatedResult?.resource_id) {
        Api.recordResourceEvent(generatedResult.resource_id, "open", { generated_now: true }, { sourcePage: "resources-generate" });
      }
    } catch (e) {
      grid.innerHTML = `<p style="color:var(--color-rose);padding:var(--space-8)">生成失败：${escapeHtml(e.message)}</p>`;
    }
  },

  _renderMarkdown(text) {
    return renderMarkdown(text);
  },

  async _parseAndRenderQuiz(content, topic, container, grid) {
    const quizEl = grid.querySelector("#quizInteractive");
    const contentEl = grid.querySelector(".res-content");
    if (!quizEl) return;

    let questions = [];

    // 先尝试直接解析 JSON（LLM 经常直接输出 JSON 格式）
    try {
      let jsonStr = content.trim();
      // 去掉 markdown 代码块标记
      jsonStr = jsonStr.replace(/^```(?:json)?\s*\n?/m, '').replace(/\n?```\s*$/m, '');
      const parsed = JSON.parse(jsonStr);
      if (Array.isArray(parsed)) {
        questions = parsed;
      } else if (parsed.questions && Array.isArray(parsed.questions)) {
        questions = parsed.questions;
      }
    } catch (e) {
      // JSON 解析失败，尝试从内容中提取 JSON 块
      try {
        const jsonMatch = content.match(/\{[\s\S]*"questions"[\s\S]*\}/);
        if (jsonMatch) {
          const parsed = JSON.parse(jsonMatch[0]);
          if (parsed.questions) questions = parsed.questions;
        }
      } catch (e2) {}
    }

    // 如果直接解析失败，调用后端 API
    if (questions.length === 0) {
      try {
        const res = await fetch(`${AppState.apiBase}/api/evaluation/parse-quiz`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content }),
        });
        const data = await res.json();
        questions = data.questions || [];
      } catch (e) {}
    }

    if (questions.length === 0) {
      quizEl.innerHTML = '<p style="color:var(--color-ink-light)">无法解析为交互式练习，请参考上方文本内容。</p>';
      return;
    }

    // 隐藏原始 JSON/文本内容，只显示交互式表单
    if (contentEl) contentEl.style.display = "none";

    const letters = ["A", "B", "C", "D", "E", "F"];

    const renderQuestion = (q, i) => {
      const qType = q.type || "choice";
      if (qType === "fill") {
        return `
          <div class="quiz-question" data-index="${i}" data-type="fill" style="margin-bottom:var(--space-5);padding:var(--space-4);background:var(--color-paper);border-radius:var(--radius-md);border:1px solid oklch(0.90 0.01 80)">
            <p style="font-weight:500;margin-bottom:var(--space-3)">${i + 1}. ${escapeHtml(q.question)}</p>
            <div style="display:flex;gap:var(--space-2);align-items:center">
              <input type="text" class="quiz-fill-input" data-index="${i}" placeholder="输入答案..." style="flex:1;padding:var(--space-2) var(--space-3);border:1px solid oklch(0.85 0.01 80);border-radius:var(--radius-md);font-size:var(--text-sm)">
            </div>
            <div class="quiz-feedback" style="display:none;margin-top:var(--space-2);font-size:var(--text-sm)"></div>
            ${q.explanation ? `<div class="quiz-explanation" style="display:none;margin-top:var(--space-2);padding:var(--space-3);background:var(--color-paper-warm);border-radius:var(--radius-md);font-size:var(--text-sm);color:var(--color-ink-mid)">${escapeHtml(q.explanation)}</div>` : ''}
          </div>
        `;
      }
      if (qType === "code") {
        return `
          <div class="quiz-question" data-index="${i}" data-type="code" style="margin-bottom:var(--space-5);padding:var(--space-4);background:var(--color-paper);border-radius:var(--radius-md);border:1px solid oklch(0.90 0.01 80)">
            <p style="font-weight:500;margin-bottom:var(--space-3)">${i + 1}. ${escapeHtml(q.question)}</p>
            <textarea class="quiz-code-input" data-index="${i}" rows="6" placeholder="在此编写代码..." style="width:100%;padding:var(--space-3);border:1px solid oklch(0.85 0.01 80);border-radius:var(--radius-md);font-family:monospace;font-size:var(--text-sm);resize:vertical"></textarea>
            <div class="quiz-feedback" style="display:none;margin-top:var(--space-2);font-size:var(--text-sm)"></div>
            ${q.explanation ? `<div class="quiz-explanation" style="display:none;margin-top:var(--space-2);padding:var(--space-3);background:var(--color-paper-warm);border-radius:var(--radius-md);font-size:var(--text-sm);color:var(--color-ink-mid)">${escapeHtml(q.explanation)}</div>` : ''}
          </div>
        `;
      }
      // 默认 choice 类型
      return `
        <div class="quiz-question" data-index="${i}" data-type="choice" style="margin-bottom:var(--space-5);padding:var(--space-4);background:var(--color-paper);border-radius:var(--radius-md);border:1px solid oklch(0.90 0.01 80)">
          <p style="font-weight:500;margin-bottom:var(--space-3)">${i + 1}. ${escapeHtml(q.question)}</p>
          <div class="quiz-options">
            ${(q.options || []).map((opt, j) => `
              <label class="quiz-option" style="display:flex;align-items:center;gap:var(--space-2);padding:var(--space-2) var(--space-3);margin-bottom:var(--space-1);border-radius:var(--radius-md);cursor:pointer;font-size:var(--text-sm);transition:background 0.15s">
                <input type="radio" name="quiz_${i}" value="${letters[j]}" style="accent-color:var(--color-amber)">
                <span><strong>${letters[j]}.</strong> ${escapeHtml(opt)}</span>
              </label>
            `).join("")}
          </div>
          <div class="quiz-feedback" style="display:none;margin-top:var(--space-2);font-size:var(--text-sm)"></div>
          ${q.explanation ? `<div class="quiz-explanation" style="display:none;margin-top:var(--space-2);padding:var(--space-3);background:var(--color-paper-warm);border-radius:var(--radius-md);font-size:var(--text-sm);color:var(--color-ink-mid)">${escapeHtml(q.explanation)}</div>` : ''}
        </div>
      `;
    };

    quizEl.innerHTML = `
      <h4 style="font-size:var(--text-base);font-weight:600;margin-bottom:var(--space-4)">在线作答（${questions.length} 题）</h4>
      ${questions.map((q, i) => renderQuestion(q, i)).join("")}
      <button class="btn btn-primary" id="submitQuiz" style="margin-top:var(--space-2)">提交答案</button>
      <div id="quizResult" style="margin-top:var(--space-4)"></div>
    `;

    const submitBtn = quizEl.querySelector("#submitQuiz");
    submitBtn.addEventListener("click", async () => {
      const quizResults = [];
      let correctCount = 0;

      questions.forEach((q, i) => {
        const qType = q.type || "choice";
        const feedback = quizEl.querySelectorAll(".quiz-feedback")[i];
        const explanation = quizEl.querySelectorAll(".quiz-explanation")[i];
        let isCorrect = false;
        let userAnswer = "";

        if (qType === "choice") {
          const selected = quizEl.querySelector(`input[name="quiz_${i}"]:checked`);
          userAnswer = selected ? selected.value : null;
          isCorrect = userAnswer === q.answer;
        } else if (qType === "fill") {
          const input = quizEl.querySelector(`.quiz-fill-input[data-index="${i}"]`);
          userAnswer = input ? input.value.trim() : "";
          isCorrect = userAnswer.toLowerCase() === (q.answer || "").toLowerCase();
        } else if (qType === "code") {
          const textarea = quizEl.querySelector(`.quiz-code-input[data-index="${i}"]`);
          userAnswer = textarea ? textarea.value.trim() : "";
          isCorrect = userAnswer.length >= 20;
        }

        if (isCorrect) correctCount++;

        if (feedback) {
          feedback.style.display = "block";
          if (qType === "choice") {
            if (isCorrect) {
              feedback.innerHTML = `<span style="color:var(--color-sage)">✓ 正确</span>`;
              feedback.closest(".quiz-question").style.borderColor = "var(--color-sage)";
            } else {
              feedback.innerHTML = `<span style="color:var(--color-rose)">✗ 错误</span>（正确答案：${escapeHtml(q.answer)}）`;
              feedback.closest(".quiz-question").style.borderColor = "var(--color-rose)";
            }
          } else if (qType === "fill") {
            if (isCorrect) {
              feedback.innerHTML = `<span style="color:var(--color-sage)">✓ 正确</span>`;
              feedback.closest(".quiz-question").style.borderColor = "var(--color-sage)";
            } else {
              feedback.innerHTML = `<span style="color:var(--color-rose)">✗ 错误</span>（正确答案：${escapeHtml(q.answer)}）`;
              feedback.closest(".quiz-question").style.borderColor = "var(--color-rose)";
            }
          } else {
            feedback.innerHTML = `<span style="color:var(--color-sage)">✓ 已提交</span>`;
          }
        }
        if (explanation) explanation.style.display = "block";

        quizResults.push({
          topic_id: q.topic || topic,
          correct: isCorrect,
          difficulty: q.difficulty === "hard" ? 0.8 : q.difficulty === "medium" ? 0.5 : 0.3,
          question: q.question,
          question_type: q.type || "choice",
          student_answer: userAnswer,
          correct_answer: q.answer,
          required_keywords: q.required_keywords || [],
          expected_points: q.expected_points || [],
          test_cases: q.test_cases || [],
        });
      });

      submitBtn.disabled = true;
      submitBtn.textContent = "已提交";

      const resultEl = quizEl.querySelector("#quizResult");
      resultEl.innerHTML = `
        <div style="padding:var(--space-4);background:var(--color-paper-warm);border-radius:var(--radius-md)">
          <p style="font-weight:600">得分：${correctCount}/${questions.length}（${Math.round(correctCount / questions.length * 100)}%）</p>
          <p style="font-size:var(--text-sm);color:var(--color-ink-light);margin-top:var(--space-2)">已自动提交评估，掌握度已更新。</p>
        </div>
      `;

      try {
        await Api.submitQuiz(quizResults, { sessionId: `quiz_${Date.now()}` });
      } catch (e) {
        console.error("Failed to submit quiz:", e);
      }
    });
  },

  async _renderDocxPreview(resourceId, container) {
    const previewEl = document.getElementById("docxPreview");
    if (!previewEl) return;

    try {
      // Wait for docx-preview to load (max 5 seconds)
      let attempts = 0;
      while (typeof window.docx === 'undefined' && attempts < 50) {
        await new Promise(resolve => setTimeout(resolve, 100));
        attempts++;
      }

      if (typeof window.docx === 'undefined') {
        previewEl.innerHTML = '<p style="color:var(--color-rose);padding:var(--space-4)">docx-preview 库未加载，请检查网络连接后刷新页面重试。</p>';
        return;
      }

      previewEl.innerHTML = '<div style="text-align:center;padding:var(--space-8)"><div class="typing-dots"><span></span><span></span><span></span></div><p style="color:var(--color-ink-light);margin-top:var(--space-2)">正在加载文档预览...</p></div>';

      const response = await fetch(`${AppState.apiBase}/api/resources/file/${encodeURIComponent(AppState.currentUserId)}/${encodeURIComponent(resourceId)}`);
      if (!response.ok) throw new Error("HTTP " + response.status);
      const arrayBuffer = await response.arrayBuffer();

      previewEl.innerHTML = "";
      await window.docx.renderAsync(arrayBuffer, previewEl, null, {
        className: "docx",
        inWrapper: true,
        ignoreWidth: false,
        ignoreHeight: false,
        ignoreFonts: false,
        breakPages: true,
        ignoreLastRenderedPageBreak: true,
        experimental: false,
        trimXmlDeclaration: true,
        useBase64: false,
        useMathMLPolyfill: false,
        showChanges: false,
      });
    } catch (e) {
      console.error("DOCX preview failed:", e);
      previewEl.innerHTML = `<p style="color:var(--color-rose);padding:var(--space-4)">文档预览加载失败: ${e.message}</p>`;
    }
  },

  async _deleteResource(resourceId, topic, container, filter) {
    if (!confirm(`确定要删除「${escapeHtml(topic || '未命名')}」吗？此操作不可撤销。`)) return;

    try {
      const data = await Api.deleteResource(resourceId);
      if (data.success) {
        showToast("已删除: " + (topic || "资源"));
        this._loadSavedResources(container, filter);
      } else {
        showToast("删除失败");
      }
    } catch (e) {
      console.error("Delete failed:", e);
      showToast("删除失败");
    }
  },

  escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str || "";
    return div.innerHTML;
  },

  _renderSourceBlock(resource) {
    const sources = resource.sources_used || [];
    const safety = resource.safety_status || {};
    const issues = safety.issues || [];
    const confidence = resource.confidence;
    const confidenceBreakdown = resource.confidence_breakdown || {};
    const agentsInvolved = resource.agents_involved || [];

    if (sources.length === 0 && !safety.checked && confidence === undefined) return "";

    // Confidence bar
    let confidenceHtml = "";
    if (confidence !== undefined) {
      const pct = Math.round(confidence);
      const color = pct >= 70 ? 'var(--color-sage)' : pct >= 30 ? 'var(--color-amber)' : 'var(--color-rose)';
      const label = pct >= 70 ? '高置信度' : pct >= 30 ? '中等置信度' : '低置信度';
      confidenceHtml = `
        <div style="margin-bottom:var(--space-3)">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px">
            <span style="font-size:var(--text-xs);font-weight:600;color:${color}">内容置信度: ${label}</span>
            <span style="font-size:var(--text-xs);font-weight:700;color:${color}">${pct}/100</span>
          </div>
          <div style="height:6px;background:var(--color-paper-deep);border-radius:3px;overflow:hidden">
            <div style="height:100%;width:${pct}%;background:${color};border-radius:3px;transition:width 0.5s ease"></div>
          </div>
          ${pct < 30 ? `<p style="margin:4px 0 0;font-size:var(--text-xs);color:var(--color-rose);font-weight:500">⚠️ 置信度较低，部分内容可能不够准确，请结合教材判断</p>` : ''}
        </div>
      `;
    }

    // Agent chain info
    let agentsHtml = "";
    if (agentsInvolved.length > 0) {
      agentsHtml = `
        <div style="margin-bottom:var(--space-3);padding:var(--space-2);background:var(--color-paper);border-radius:var(--radius-sm)">
          <span style="font-size:var(--text-xs);font-weight:600;color:var(--color-ink-light)">参与智能体: </span>
          ${agentsInvolved.map(a => `<span style="display:inline-block;font-size:var(--text-xs);background:var(--color-amber-surface);color:var(--color-amber);padding:1px 6px;border-radius:var(--radius-full);margin:1px">${a.role || a.name}</span>`).join("")}
        </div>
      `;
    }

    // Safety status
    const safetyColor = safety.is_safe === false || safety.review_skipped ? 'var(--color-rose)' : 'var(--color-sage)';
    const safetyLabel = safety.review_skipped ? '安全审查未完成，请人工复核' : (safety.checked ? (safety.is_safe === false ? '存在校验提示' : '已通过内容与依据校验') : '暂无校验信息');
    const safetyIcon = safety.is_safe === false ? '⚠️' : (safety.checked ? '✅' : '⏳');

    return `
      <div style="margin-top:var(--space-4);padding:var(--space-4);background:var(--color-paper-warm);border-radius:var(--radius-md);border:1px solid oklch(0.90 0.01 80)">
        <h5 style="margin:0 0 var(--space-3) 0;font-size:var(--text-sm);display:flex;align-items:center;gap:6px">内容可信度面板</h5>
        ${confidenceHtml}
        ${agentsHtml}
        <div style="display:flex;align-items:center;gap:4px;margin-bottom:var(--space-2)">
          <span>${safetyIcon}</span>
          <p style="font-size:var(--text-xs);color:${safetyColor};margin:0">${safetyLabel}</p>
        </div>
        ${issues.length > 0 ? `
          <div style="margin:var(--space-2) 0;padding:var(--space-2) var(--space-3);background:oklch(0.97 0.02 25);border-left:3px solid var(--color-rose);border-radius:0 var(--radius-sm) var(--radius-sm) 0">
            <p style="font-size:var(--text-xs);font-weight:600;color:var(--color-rose);margin:0 0 4px">未经验证的声明</p>
            <ul style="margin:0 0 0 var(--space-4);font-size:var(--text-xs);color:var(--color-ink-mid);padding:0 0 0 16px">${issues.map(issue => `<li style="margin:2px 0">${this.escapeHtml(issue.description || issue)}</li>`).join("")}</ul>
          </div>
        ` : ""}
        ${sources.length > 0 ? `
          <div style="margin-top:var(--space-3)">
            <p style="font-size:var(--text-xs);font-weight:600;color:var(--color-ink-light);margin:0 0 var(--space-2)">参考来源 (${sources.length})</p>
            <div style="display:grid;gap:var(--space-2)">${sources.map((src, i) => `
              <div style="padding:var(--space-2) var(--space-3);background:rgba(255,255,255,0.7);border-radius:var(--radius-sm);font-size:var(--text-xs);display:flex;gap:var(--space-2);align-items:flex-start">
                <span style="font-weight:700;color:var(--color-amber);min-width:18px">${i + 1}.</span>
                <div>
                  <strong>${this.escapeHtml(src.title || src.source_id || "来源")}</strong>
                  ${src.chapter ? `<span style="color:var(--color-ink-light);margin-left:4px">${this.escapeHtml(src.chapter)}</span>` : ""}
                  ${src.snippet ? `<div style="color:var(--color-ink-light);margin-top:2px">${this.escapeHtml(src.snippet.substring(0, 120))}${src.snippet.length > 120 ? '...' : ''}</div>` : ""}
                </div>
              </div>
            `).join("")}</div>
          </div>
        ` : ""}
      </div>
    `;
  },

  _renderSkeletonCards(count) {
    return Array.from({ length: count }, () => `
      <div class="res-card res-skeleton">
        <div class="res-card-head">
          <div class="skeleton-line" style="width:55%"></div>
          <div class="skeleton-badge"></div>
        </div>
        <div class="skeleton-line" style="width:100%"></div>
        <div class="skeleton-line" style="width:85%"></div>
        <div class="skeleton-line" style="width:60%"></div>
        <div class="skeleton-btn"></div>
      </div>
    `).join("");
  },

  _showPreviewModal(resource) {
    const existing = $(".res-preview-modal");
    if (existing) existing.remove();

    const typeLabels = {
      lecture: "讲义", quiz: "练习题", code_lab: "代码实训",
      mindmap: "思维导图", ppt_outline: "PPT提纲", animation: "动画脚本",
      extended_reading: "拓展阅读", document: "文档",
    };

    const contentHtml = this._renderMarkdown(resource.content || "");

    const modal = document.createElement("div");
    modal.className = "res-preview-modal";
    modal.innerHTML = `
      <div class="res-preview-overlay"></div>
      <div class="res-preview-panel">
        <div class="res-preview-header">
          <h3 class="res-preview-title">${this.escapeHtml(resource.topic || '未命名')} - ${typeLabels[resource.type] || resource.type}</h3>
          <div class="res-preview-actions">
            <button class="res-preview-fs-btn" title="全屏">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></svg>
            </button>
            <button class="res-preview-close-btn" title="关闭">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
        </div>
        <div class="res-preview-body res-content">${contentHtml}</div>
        ${resource.type === "ppt_outline" ? `<div style="padding:0 var(--space-6) var(--space-3)"><a class="btn btn-primary btn-sm" href="${AppState.apiBase}/api/resources/pptx/${encodeURIComponent(AppState.currentUserId)}/${encodeURIComponent(resource.id)}" download>下载PPTX</a></div>` : ""}
        <div class="res-preview-footer">
          <div class="res-feedback">
            <p class="res-feedback-label">这个资源对你有帮助吗？</p>
            <div class="res-feedback-types">
              <button class="res-feedback-btn" data-type="useful">👍 有用</button>
              <button class="res-feedback-btn" data-type="useless">👎 无用</button>
              <button class="res-feedback-btn" data-type="error">⚠️ 有误</button>
            </div>
            <div class="res-feedback-input-area" style="display:none">
              <textarea class="res-feedback-text" placeholder="补充反馈意见（可选）..." rows="2"></textarea>
              <button class="btn btn-primary btn-sm res-feedback-submit" data-resource-id="${this.escapeHtml(resource.id)}">提交</button>
            </div>
          </div>
        </div>
      </div>
    `;

    document.body.appendChild(modal);
    document.body.style.overflow = "hidden";

    setTimeout(() => {
      modal.querySelectorAll('.mermaid:not([data-processed])').forEach(el => {
        if (typeof mermaid !== 'undefined') {
          try {
            const id = 'mermaid-preview-' + Math.random().toString(36).substr(2, 9);
            mermaid.render(id, el.textContent.trim()).then(({ svg }) => {
              el.innerHTML = svg;
              el.setAttribute('data-processed', 'true');
            });
          } catch (e) {}
        }
      });
    }, 100);

    let removeKeyHandler;
    const closeModal = () => {
      if (removeKeyHandler) removeKeyHandler();
      modal.remove();
      document.body.style.overflow = "";
    };

    const overlay = modal.querySelector(".res-preview-overlay");
    const closeBtn = modal.querySelector(".res-preview-close-btn");
    const fsBtn = modal.querySelector(".res-preview-fs-btn");
    const panel = modal.querySelector(".res-preview-panel");

    on(overlay, "click", closeModal);
    on(closeBtn, "click", closeModal);
    removeKeyHandler = on(document, "keydown", (e) => { if (e.key === "Escape") closeModal(); });

    on(fsBtn, "click", () => {
      panel.classList.toggle("is-fullscreen");
    });

    modal.querySelectorAll(".res-feedback-btn").forEach(btn => {
      on(btn, "click", () => {
        modal.querySelectorAll(".res-feedback-btn").forEach(b => b.classList.remove("is-active"));
        btn.classList.add("is-active");
        const inputArea = modal.querySelector(".res-feedback-input-area");
        if (inputArea) inputArea.style.display = "flex";
      });
    });

    const submitBtn = modal.querySelector(".res-feedback-submit");
    if (submitBtn) {
      on(submitBtn, "click", () => {
        const activeBtn = modal.querySelector(".res-feedback-btn.is-active");
        const feedbackType = activeBtn ? activeBtn.dataset.type : "";
        const text = modal.querySelector(".res-feedback-text")?.value.trim() || "";
        if (!feedbackType) { showToast("请选择反馈类型"); return; }
        this._submitFeedback(resource.id, text, feedbackType);
      });
    }

    Api.recordResourceEvent(resource.id, "preview", { type: resource.type, topic: resource.topic }, { sourcePage: "resources-preview" });
  },

  async _rateResource(resourceId, rating) {
    try {
      await Api.rateResource(AppState.currentUserId, resourceId, rating);
      Api.recordResourceEvent(resourceId, "rate", { rating }, { sourcePage: "resources" });
      showToast("已评分: " + rating + " 星");
      const ratingEl = $(`.res-card-rating[data-rating-id="${resourceId}"]`);
      if (ratingEl) {
        ratingEl.querySelectorAll(".res-star").forEach(star => {
          const v = parseInt(star.dataset.star);
          star.classList.toggle("is-active", v <= rating);
        });
        const infoEl = ratingEl.querySelector(".res-rating-info");
        if (infoEl) infoEl.textContent = rating + " 分";
      }
    } catch (e) {
      console.error("Rate failed:", e);
      showToast("评分失败");
    }
  },

  async _submitFeedback(resourceId, feedback, feedbackType) {
    try {
      await Api.recordResourceEvent(resourceId, "feedback", {
        feedback_type: feedbackType,
        feedback_text: feedback,
      }, { sourcePage: "resources-feedback" });
      showToast("感谢你的反馈！");
      const modal = $(".res-preview-modal");
      if (modal) {
        const footer = modal.querySelector(".res-preview-footer");
        if (footer) footer.innerHTML = '<p style="color:var(--color-sage);text-align:center;padding:var(--space-3)">✓ 感谢你的反馈！</p>';
      }
    } catch (e) {
      console.error("Feedback failed:", e);
      showToast("反馈提交失败");
    }
  },
});
