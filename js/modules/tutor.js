App.register("tutor", {
  title: "智能辅导",
  _timers: [],
  _capability: "chat",
  _pendingImage: "",
  _pendingFile: null,
  _currentSessionId: "",

  render() {
    return `
      <div class="tutor">
        <div class="tutor-layout">
          <div class="tutor-sidebar" id="tutorSidebar">
            <div class="tutor-sidebar-header">
              <button class="btn btn-primary btn-sm" id="newChatBtn" style="width:100%">+ 新对话</button>
            </div>
            <div class="tutor-session-list" id="sessionList">
              <p style="color:var(--color-ink-faint);font-size:var(--text-xs);text-align:center;padding:var(--space-4)">加载中...</p>
            </div>
          </div>
          <div class="tutor-main">
            <div class="tutor-mode-bar">
              <button class="tutor-sidebar-toggle" id="sidebarToggle" aria-label="历史对话">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
              </button>
              <button class="tutor-mode-btn is-active" data-cap="chat">普通对话</button>
              <button class="tutor-mode-btn" data-cap="deep_solve">深度求解</button>
            </div>

            <div class="tutor-messages" id="tutorMessages">
              <div class="msg msg-bot">
                <div class="msg-avatar msg-avatar-bot">智</div>
                <div class="msg-bubble">
                  <p>您好！我是智学助手。请问有什么我可以帮助您的？</p>
                  <p style="font-size:var(--text-xs);color:var(--color-ink-faint);margin-top:var(--space-2)">支持文字和图片输入 | 普通对话：问答、解释概念 | 深度求解：复杂问题分步求解</p>
                </div>
              </div>
            </div>

            <div class="tutor-suggestions" id="tutorSuggestions">
              <button class="tutor-chip" data-prompt="帮我构建学习画像">帮我构建学习画像</button>
              <button class="tutor-chip" data-prompt="解释反向传播算法">解释反向传播算法</button>
              <button class="tutor-chip" data-prompt="推荐学习资源">推荐学习资源</button>
              <button class="tutor-chip" data-prompt="用Python实现二分查找">用Python实现二分查找</button>
            </div>

            <div id="imagePreview" style="display:none;padding:var(--space-2) var(--space-4);background:var(--color-paper-warm);border-top:1px solid oklch(0.90 0.01 80)">
              <div style="display:flex;align-items:center;gap:var(--space-2)">
                <img id="previewImg" style="max-height:60px;max-width:100px;border-radius:var(--radius-md);object-fit:cover">
                <span style="font-size:var(--text-xs);color:var(--color-ink-light)">图片已选择</span>
                <button class="btn btn-ghost btn-sm" id="clearImage" style="margin-left:auto">✕</button>
              </div>
            </div>

            <div id="filePreview" style="display:none;padding:var(--space-2) var(--space-4);background:var(--color-paper-warm);border-top:1px solid oklch(0.90 0.01 80)">
              <div style="display:flex;align-items:center;gap:var(--space-2)">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--color-amber)" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                <span id="fileName" style="font-size:var(--text-xs);color:var(--color-ink);font-weight:500"></span>
                <span id="fileSize" style="font-size:var(--text-xs);color:var(--color-ink-faint)"></span>
                <button class="btn btn-ghost btn-sm" id="clearFile" style="margin-left:auto">✕</button>
              </div>
            </div>

            <div class="tutor-input-bar">
              <input type="file" id="imageInput" accept="image/*" style="display:none">
              <input type="file" id="fileInput" accept=".py,.js,.ts,.jsx,.tsx,.java,.cpp,.c,.h,.hpp,.html,.css,.json,.xml,.sql,.sh,.bat,.ps1,.txt,.md,.csv,.log,.yaml,.yml,.toml,.ini,.cfg,.conf,.r,.rb,.go,.rs,.swift,.kt,.php,.pl,.lua,.vim" style="display:none">
              <button class="tutor-send" id="imageUploadBtn" aria-label="上传图片" style="background:var(--color-paper-warm);color:var(--color-ink-mid)">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                  <circle cx="8.5" cy="8.5" r="1.5"></circle>
                  <polyline points="21 15 16 10 5 21"></polyline>
                </svg>
              </button>
              <button class="tutor-send" id="fileUploadBtn" aria-label="上传文件" style="background:var(--color-paper-warm);color:var(--color-ink-mid)">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                  <line x1="12" y1="18" x2="12" y2="12"></line>
                  <line x1="9" y1="15" x2="15" y2="15"></line>
                </svg>
              </button>
              <input type="text" class="tutor-input" id="tutorInput" placeholder="输入您的问题，可上传图片或文件..." autocomplete="off">
              <button class="tutor-send" id="tutorSend" aria-label="发送">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <path d="M3 10L17 3L10 17L9 11L3 10Z" fill="currentColor"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
  },

  bind(container) {
    const input = $("#tutorInput", container);
    const sendBtn = $("#tutorSend", container);
    const messages = $("#tutorMessages", container);
    const suggestions = $("#tutorSuggestions", container);
    const imageInput = $("#imageInput", container);
    const imageUploadBtn = $("#imageUploadBtn", container);
    const imagePreview = $("#imagePreview", container);
    const previewImg = $("#previewImg", container);
    const clearImageBtn = $("#clearImage", container);
    const newChatBtn = $("#newChatBtn", container);
    const sidebarToggle = $("#sidebarToggle", container);
    const sidebar = $("#tutorSidebar", container);

    this._currentSessionId = "chat_" + Date.now();

    // 侧栏切换
    on(sidebarToggle, "click", () => {
      sidebar.classList.toggle("is-open");
    });

    // 新对话
    on(newChatBtn, "click", () => {
      this._currentSessionId = "chat_" + Date.now();
      messages.innerHTML = `
        <div class="msg msg-bot">
          <div class="msg-avatar msg-avatar-bot">智</div>
          <div class="msg-bubble">
            <p>您好！我是智学助手。请问有什么我可以帮助您的？</p>
            <p style="font-size:var(--text-xs);color:var(--color-ink-faint);margin-top:var(--space-2)">支持文字和图片输入</p>
          </div>
        </div>
      `;
      if (suggestions) suggestions.style.display = "flex";
      this._loadSessionList();
    });

    // 模式切换
    $$(".tutor-mode-btn", container).forEach((btn) => {
      on(btn, "click", () => {
        $$(".tutor-mode-btn", container).forEach(b => b.classList.remove("is-active"));
        btn.classList.add("is-active");
        this._capability = btn.dataset.cap;
        input.placeholder = this._capability === "deep_solve"
          ? "输入复杂问题，AI将分步求解..."
          : "输入您的问题，可上传图片...";
      });
    });

    // 图片上传
    on(imageUploadBtn, "click", () => imageInput.click());
    on(imageInput, "change", (e) => {
      const file = e.target.files[0];
      if (!file) return;
      if (file.size > AppState.maxUploadSizeMb * 1024 * 1024) {
        showToast(`图片大小不能超过 ${AppState.maxUploadSizeMb}MB`);
        return;
      }
      const reader = new FileReader();
      reader.onload = (ev) => {
        this._pendingImage = ev.target.result.split(",")[1];
        previewImg.src = ev.target.result;
        imagePreview.style.display = "block";
      };
      reader.readAsDataURL(file);
      imageInput.value = "";
    });
    on(clearImageBtn, "click", () => {
      this._pendingImage = "";
      imagePreview.style.display = "none";
      previewImg.src = "";
    });

    // 文件上传
    const fileInput = $("#fileInput", container);
    const fileUploadBtn = $("#fileUploadBtn", container);
    const filePreview = $("#filePreview", container);
    const fileNameEl = $("#fileName", container);
    const fileSizeEl = $("#fileSize", container);
    const clearFileBtn = $("#clearFile", container);

    on(fileUploadBtn, "click", () => fileInput.click());
    on(fileInput, "change", (e) => {
      const file = e.target.files[0];
      if (!file) return;
      if (file.size > AppState.maxUploadSizeMb * 1024 * 1024) {
        showToast(`文件大小不能超过 ${AppState.maxUploadSizeMb}MB`);
        return;
      }
      const reader = new FileReader();
      reader.onload = (ev) => {
        this._pendingFile = { name: file.name, content: ev.target.result, size: file.size };
        fileNameEl.textContent = file.name;
        fileSizeEl.textContent = this._formatFileSize(file.size);
        filePreview.style.display = "block";
      };
      reader.readAsText(file);
      fileInput.value = "";
    });
    on(clearFileBtn, "click", () => {
      this._pendingFile = null;
      filePreview.style.display = "none";
    });

    const sendMessage = () => {
      try {
        const text = input.value.trim();
        if (!text && !this._pendingImage && !this._pendingFile) return;
        input.value = "";
        if (suggestions) suggestions.style.display = "none";

        const isProfileBuild = (text || "").includes("构建画像") || (text || "").includes("学习画像");
        const capability = isProfileBuild ? "profile_build" : this._capability;

        const imageHtml = this._pendingImage
          ? `<div style="margin-bottom:var(--space-2)"><img src="data:image/png;base64,${this._pendingImage}" style="max-width:200px;max-height:150px;border-radius:var(--radius-md);object-fit:cover"></div>`
          : "";

        const fileHtml = this._pendingFile
          ? `<div style="margin-bottom:var(--space-2);display:flex;align-items:center;gap:var(--space-2);padding:var(--space-2) var(--space-3);background:oklch(0.95 0.01 80);border-radius:var(--radius-md)"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-amber)" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg><span style="font-size:var(--text-xs);font-weight:500">${this.escapeHtml(this._pendingFile.name)}</span><span style="font-size:var(--text-xs);color:var(--color-ink-faint)">${this._formatFileSize(this._pendingFile.size)}</span></div>`
          : "";

        messages.insertAdjacentHTML("beforeend", `
          <div class="msg msg-user">
            <div class="msg-bubble">
              ${imageHtml}
              ${fileHtml}
              ${text ? `<p>${this.escapeHtml(text)}</p>` : ""}
            </div>
          </div>
        `);
        messages.scrollTop = messages.scrollHeight;

        const typingId = "typing-" + Date.now();
        messages.insertAdjacentHTML("beforeend", `
          <div class="msg msg-bot msg-typing" id="${typingId}">
            <div class="msg-avatar msg-avatar-bot">智</div>
            <div class="msg-bubble">
              <div class="typing-dots"><span></span><span></span><span></span></div>
            </div>
          </div>
        `);
        messages.scrollTop = messages.scrollHeight;

        const currentImage = this._pendingImage;
        const currentFile = this._pendingFile;
        this._pendingImage = "";
        this._pendingFile = null;
        imagePreview.style.display = "none";
        previewImg.src = "";
        if (filePreview) filePreview.style.display = "none";

        let fullResponse = "";

        Api.chatStream(text || (currentFile ? "请分析这个文件" : "请分析这张图片"), {
          sessionId: this._currentSessionId,
          userId: AppState.currentUserId,
          capability,
          imageBase64: currentImage,
          fileContent: currentFile ? currentFile.content : "",
          fileName: currentFile ? currentFile.name : "",
          courseId: AppState.currentCourseId,
          onChunk: (chunk) => {
            fullResponse += chunk;
            const el = document.getElementById(typingId);
            if (el) {
              el.classList.remove("msg-typing");
              el.querySelector(".msg-bubble").innerHTML = renderMarkdown(fullResponse);
            }
            messages.scrollTop = messages.scrollHeight;
          },
          onDone: () => {
            const el = document.getElementById(typingId);
            if (el) {
              el.classList.remove("msg-typing");
              el.querySelector(".msg-bubble").innerHTML = fullResponse ? renderMarkdown(fullResponse) : "<p>已完成</p>";
            }
            this._loadSessionList();
          },
          onError: (err) => {
            const el = document.getElementById(typingId);
            if (el) {
              el.classList.remove("msg-typing");
              el.querySelector(".msg-bubble").innerHTML = `<p style="color:var(--color-rose)">抱歉，出现了错误，请稍后重试。</p>`;
            }
          },
        });
      } catch (e) {
        console.error("sendMessage error:", e);
        showToast("发送失败，请稍后重试");
      }
    };

    on(input, "keypress", (e) => { if (e.key === "Enter") sendMessage(); });
    on(sendBtn, "click", sendMessage);

    $$(".tutor-chip", container).forEach((chip) => {
      on(chip, "click", () => {
        input.value = chip.dataset.prompt;
        sendMessage();
      });
    });

    this._loadSessionList();
  },

  async _loadSessionList() {
    const listEl = document.getElementById("sessionList");
    if (!listEl) return;

    try {
      const data = await Api.getSessions(AppState.currentUserId);
      const sessions = (data.sessions || []).filter(s => s.message_count > 0).sort((a, b) => {
        const aId = parseInt(a.session_id.split("_").pop()) || 0;
        const bId = parseInt(b.session_id.split("_").pop()) || 0;
        return bId - aId;
      });

      if (sessions.length === 0) {
        listEl.innerHTML = '<p style="color:var(--color-ink-faint);font-size:var(--text-xs);text-align:center;padding:var(--space-4)">暂无历史对话</p>';
        return;
      }

      listEl.innerHTML = sessions.map(s => {
        const isActive = s.session_id === this._currentSessionId;
        const title = s.first_message || "新对话";
        const preview = s.last_message || "";
        return `
          <div class="tutor-session-item ${isActive ? 'is-active' : ''}" data-session="${s.session_id}">
            <div class="tutor-session-content">
              <div class="tutor-session-title">${this.escapeHtml(title.substring(0, 25))}${title.length > 25 ? '...' : ''}</div>
              <div class="tutor-session-preview">${this.escapeHtml(preview.substring(0, 35))}${preview.length > 35 ? '...' : ''}</div>
            </div>
            <button class="tutor-session-delete" data-delete="${s.session_id}" title="删除对话">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
            </button>
          </div>
        `;
      }).join("");

      listEl.querySelectorAll(".tutor-session-item").forEach(item => {
        on(item, "click", (e) => {
          if (e.target.closest(".tutor-session-delete")) return;
          const sessionId = item.dataset.session;
          this._loadSession(sessionId);
        });
      });

      listEl.querySelectorAll(".tutor-session-delete").forEach(btn => {
        on(btn, "click", async (e) => {
          e.stopPropagation();
          const sessionId = btn.dataset.delete;
          await this._deleteSession(sessionId);
        });
      });
    } catch (e) {
      console.error("Failed to load sessions:", e);
    }
  },

  async _loadSession(sessionId) {
    try {
      const messages = document.getElementById("tutorMessages");
      const suggestions = document.getElementById("tutorSuggestions");
      if (!messages) return;

      this._currentSessionId = sessionId;
      if (suggestions) suggestions.style.display = "none";

      const data = await Api.getSessionHistory(sessionId, AppState.currentUserId);
      const history = data.history || [];

      if (history.length === 0) {
        messages.innerHTML = `
          <div class="msg msg-bot">
            <div class="msg-avatar msg-avatar-bot">智</div>
            <div class="msg-bubble"><p>空对话</p></div>
          </div>
        `;
        return;
      }

      messages.innerHTML = history.map(m => {
        if (m.role === "user") {
          const imgMatch = m.content.match(/\[用户上传了一张图片: ([^\]]+)\]/);
          let text = m.content.replace(/\[用户上传了一张图片:[^\]]*\]/, "").trim();
          const imgPath = imgMatch ? imgMatch[1].replace(/[^a-zA-Z0-9_\-/.]/g, '') : '';
          const imgHtml = imgPath ? `<div style="margin-bottom:var(--space-2)"><img src="${AppState.apiBase}${imgPath}" style="max-width:200px;max-height:150px;border-radius:var(--radius-md);object-fit:cover" onerror="this.style.display='none'"></div>` : "";
          return `
            <div class="msg msg-user">
              <div class="msg-bubble">
                ${imgHtml}
                ${text ? `<p>${this.escapeHtml(text)}</p>` : ""}
              </div>
            </div>
          `;
        }
        return `
          <div class="msg msg-bot">
            <div class="msg-avatar msg-avatar-bot">智</div>
            <div class="msg-bubble">${renderMarkdown(m.content || "")}</div>
          </div>
        `;
      }).join("");

      messages.scrollTop = messages.scrollHeight;
      this._loadSessionList();
    } catch (e) {
      console.error("Failed to load session:", e);
      showToast("加载对话失败");
    }
  },

  async _deleteSession(sessionId) {
    try {
      await Api.deleteSession(sessionId, AppState.currentUserId);

      if (sessionId === this._currentSessionId) {
        this._currentSessionId = "chat_" + Date.now();
        const messages = document.getElementById("tutorMessages");
        const suggestions = document.getElementById("tutorSuggestions");
        if (messages) {
          messages.innerHTML = `
            <div class="msg msg-bot">
              <div class="msg-avatar msg-avatar-bot">智</div>
              <div class="msg-bubble">
                <p>对话已删除。您好！我是智学助手。请问有什么我可以帮助您的？</p>
              </div>
            </div>
          `;
        }
        if (suggestions) suggestions.style.display = "flex";
      }

      this._loadSessionList();
      showToast("对话已删除");
    } catch (e) {
      console.error("Failed to delete session:", e);
      showToast("删除失败");
    }
  },

  exit() {
    this._timers.forEach(clearTimeout);
    this._timers = [];
    this._pendingImage = "";
  },

  escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  },

  _formatFileSize(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  },
});
