App.register("resources", {
  title: "资源中心",

  render() {
    const types = ["all", "lecture", "quiz", "code", "mindmap", "document"];
    const typeLabels = { all: "全部", lecture: "讲义", quiz: "题库", code: "代码", mindmap: "思维导图", document: "文档" };

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
            <option value="code">代码案例</option>
            <option value="mindmap">思维导图</option>
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
    $$(".filter-btn", container).forEach((btn) => {
      on(btn, "click", () => {
        $$(".filter-btn", container).forEach(b => b.classList.remove("is-active"));
        btn.classList.add("is-active");
        const filter = btn.dataset.filter;
        this._loadSavedResources(container, filter);
      });
    });

    const genBtn = $("#resGenBtn", container);
    const topicInput = $("#resTopicInput", container);
    const typeSelect = $("#resTypeSelect", container);
    const grid = $("#resGrid", container);

    if (genBtn) {
      on(genBtn, "click", () => {
        const topic = topicInput.value.trim();
        if (!topic) { showToast("请输入知识点"); return; }
        this._generateResource(topic, typeSelect.value, grid, container);
      });
    }

    // 资源上传
    const fileInput = $("#resFileInput", container);
    const uploadBtn = $("#resUploadBtn", container);
    if (uploadBtn && fileInput) {
      on(uploadBtn, "click", () => fileInput.click());
      on(fileInput, "change", (e) => {
        const file = e.target.files[0];
        if (!file) return;
        if (file.size > 5 * 1024 * 1024) {
          showToast("文件大小不能超过 5MB");
          return;
        }
        this._uploadResource(file, container);
        fileInput.value = "";
      });
    }

    this._loadSavedResources(container, "all");
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
      formData.append("user_id", "default");
      formData.append("topic", file.name.replace(/\.[^.]+$/, ""));

      const res = await fetch(`${API_BASE}/api/resources/upload-file`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (data.success) {
        showToast("上传成功: " + file.name + " (" + (data.text_length || 0) + " 字)");
        this._loadSavedResources(container, "all");
      } else {
        showToast("上传失败: " + (data.error || "未知错误"));
      }
    } catch (e) {
      console.error("Upload failed:", e);
      showToast("上传失败: " + e.message);
    }
  },

  async _loadSavedResources(container, filter) {
    const grid = $("#resGrid", container);
    if (!grid) return;
    try {
      const res = await fetch(`${API_BASE}/api/resources/list/default?type=${filter}`);
      const data = await res.json();
      const resources = data.resources || [];

      if (resources.length === 0) {
        grid.innerHTML = '<p style="color:var(--color-ink-light);padding:var(--space-8);text-align:center">输入知识点并点击「生成」，AI 将为您生成个性化学习资源</p>';
        return;
      }

      const typeLabels = { lecture: "讲义", quiz: "练习题", code: "代码案例", mindmap: "思维导图", document: "文档" };
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
        } else if (r.type === "code" || r.type === "document") {
          let content = r.content || "";
          let titleLine = "";
          const titleMatch = content.match(/^#\s+(.+)$/m);
          if (titleMatch) titleLine = titleMatch[1];
          let codeBlock = "";
          const codeMatch = content.match(/```(\w*)\n([\s\S]*?)```/);
          if (codeMatch) {
            const lang = codeMatch[1] || "code";
            const code = codeMatch[2].trim();
            const truncated = code.split("\n").slice(0, 6).join("\n");
            const hasMore = code.split("\n").length > 6;
            codeBlock = `<div style="background:oklch(0.15 0.02 260);border-radius:var(--radius-md);padding:var(--space-3);overflow:hidden;max-height:140px"><pre style="margin:0;background:none;color:oklch(0.88 0.01 80);font-size:var(--text-xs);line-height:1.5;white-space:pre"><code>${this.escapeHtml(truncated)}${hasMore ? "\n..." : ""}</code></pre></div>`;
          } else {
            const lines = content.split("\n").filter(l => !l.startsWith("#")).slice(0, 4).join("\n");
            codeBlock = `<pre style="background:var(--color-paper-deep);border-radius:var(--radius-md);padding:var(--space-2);font-size:var(--text-xs);color:var(--color-ink-mid);overflow:hidden;max-height:100px;white-space:pre-wrap"><code>${this.escapeHtml(lines)}...</code></pre>`;
          }
          preview = codeBlock;
        } else {
          let content = r.content || "";
          let text = content.replace(/[#*`>\[\]!]/g, "").replace(/\n+/g, " ").trim();
          preview = `<p style="font-size:var(--text-xs);color:var(--color-ink-light);line-height:1.5;max-height:60px;overflow:hidden">${this.escapeHtml(text.substring(0, 200))}${text.length > 200 ? '...' : ''}</p>`;
        }

        return `
          <div class="res-card" data-type="${r.type}" data-id="${r.id}">
            <div class="res-card-head">
              <h4 class="res-title">${r.topic || '未命名'}</h4>
              <span class="tag tag-filled">${typeLabels[r.type] || r.type}</span>
            </div>
            <div class="res-preview">${preview}</div>
            <button class="btn btn-ghost btn-sm" style="margin-top:auto;width:100%" onclick="document.querySelector('#resGrid').dispatchEvent(new CustomEvent('open-resource', {detail:'${r.id}'}))">${r.type === 'quiz' ? '开始作答' : '展开查看'}</button>
          </div>
        `;
      }).join("");

      grid.addEventListener("open-resource", (e) => {
        const id = e.detail;
        const r = resources.find(x => x.id === id);
        if (r) {
          if (r.type === "quiz") {
            grid.innerHTML = `
              <div class="res-card" style="grid-column:1/-1">
                <div class="res-card-head">
                  <h4 class="res-title">${r.topic} - ${typeLabels[r.type] || r.type}</h4>
                  <span class="tag tag-filled">${typeLabels[r.type] || r.type}</span>
                </div>
                <div class="res-content" style="margin-top:var(--space-4);line-height:var(--leading-normal)">
                  ${this._renderMarkdown(r.content)}
                </div>
                <div id="quizInteractive" style="margin-top:var(--space-4)">
                  <div class="typing-dots"><span></span><span></span><span></span></div>
                  <span style="color:var(--color-ink-light);font-size:var(--text-sm)"> 正在解析题目...</span>
                </div>
                <button class="btn btn-ghost btn-sm" style="margin-top:var(--space-4)" id="backToList">返回列表</button>
              </div>
            `;
            this._parseAndRenderQuiz(r.content, r.topic, container, grid);
            $("#backToList", grid)?.addEventListener("click", () => this._loadSavedResources(container, filter));
          } else {
            grid.innerHTML = `
              <div class="res-card" style="grid-column:1/-1">
                <div class="res-card-head">
                  <h4 class="res-title">${r.topic} - ${typeLabels[r.type] || r.type}</h4>
                  <span class="tag tag-filled">${typeLabels[r.type] || r.type}</span>
                </div>
                <div class="res-content" style="margin-top:var(--space-4);line-height:var(--leading-normal)">
                  ${this._renderMarkdown(r.content)}
                </div>
                <button class="btn btn-ghost btn-sm" style="margin-top:var(--space-4)" id="backToList">返回列表</button>
              </div>
            `;
            $("#backToList", grid)?.addEventListener("click", () => this._loadSavedResources(container, filter));
          }
        }
      });
    } catch (e) {
      console.error("Failed to load resources:", e);
    }
  },

  async _generateResource(topic, type, grid, container) {
    showToast(`正在生成${type === "lecture" ? "讲义" : type === "quiz" ? "练习题" : type === "code" ? "代码案例" : "思维导图"}...`);

    grid.innerHTML = `
      <div class="res-card" style="grid-column:1/-1">
        <div class="msg-typing" style="padding:var(--space-8);text-align:center">
          <div class="typing-dots"><span></span><span></span><span></span></div>
          <p style="margin-top:var(--space-4);color:var(--color-ink-light)">AI 正在生成中...</p>
        </div>
      </div>
    `;

    let content = "";
    let safetyWarning = "";
    try {
      await Api.generateResourceStream(topic, type, {
        onChunk(chunk) { content += chunk; },
        onThinking(text) {
          if (text && (text.includes("问题") || text.includes("安全") || text.includes("审查"))) {
            safetyWarning = text;
          }
        },
        onDone() { showToast("生成完成"); },
      });

      const typeLabels = { lecture: "讲义", quiz: "练习题", code: "代码案例", mindmap: "思维导图", document: "文档" };
      const warningHtml = safetyWarning ? `<div style="background:var(--color-amber-surface);border:1px solid var(--color-amber-muted);border-radius:var(--radius-md);padding:var(--space-3);margin-top:var(--space-3);font-size:var(--text-sm);color:var(--color-amber)">⚠️ 安全审查提示：${safetyWarning}</div>` : '';

      if (type === "quiz") {
        grid.innerHTML = `
          <div class="res-card" style="grid-column:1/-1">
            <div class="res-card-head">
              <h4 class="res-title">${topic} - ${typeLabels[type]}</h4>
              <span class="tag tag-filled">${typeLabels[type]}</span>
            </div>
            <div class="res-content" style="margin-top:var(--space-4);line-height:var(--leading-normal)">
              ${this._renderMarkdown(content)}
            </div>
            ${warningHtml}
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
              <h4 class="res-title">${topic} - ${typeLabels[type]}</h4>
              <span class="tag tag-filled">${typeLabels[type]}</span>
            </div>
            <div class="res-content" style="margin-top:var(--space-4);line-height:var(--leading-normal)">
              ${this._renderMarkdown(content)}
            </div>
            ${warningHtml}
            <button class="btn btn-ghost btn-sm" style="margin-top:var(--space-4)" id="backToList">返回列表</button>
          </div>
        `;
      }

      if (container) {
        $("#backToList", grid)?.addEventListener("click", () => this._loadSavedResources(container, "all"));
      }
    } catch (e) {
      grid.innerHTML = `<p style="color:var(--color-rose);padding:var(--space-8)">生成失败：${e.message}</p>`;
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
        const res = await fetch(`${API_BASE}/api/evaluation/parse-quiz`, {
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
            <p style="font-weight:500;margin-bottom:var(--space-3)">${i + 1}. ${q.question}</p>
            <div style="display:flex;gap:var(--space-2);align-items:center">
              <input type="text" class="quiz-fill-input" data-index="${i}" placeholder="输入答案..." style="flex:1;padding:var(--space-2) var(--space-3);border:1px solid oklch(0.85 0.01 80);border-radius:var(--radius-md);font-size:var(--text-sm)">
            </div>
            <div class="quiz-feedback" style="display:none;margin-top:var(--space-2);font-size:var(--text-sm)"></div>
            ${q.explanation ? `<div class="quiz-explanation" style="display:none;margin-top:var(--space-2);padding:var(--space-3);background:var(--color-paper-warm);border-radius:var(--radius-md);font-size:var(--text-sm);color:var(--color-ink-mid)">${q.explanation}</div>` : ''}
          </div>
        `;
      }
      if (qType === "code") {
        return `
          <div class="quiz-question" data-index="${i}" data-type="code" style="margin-bottom:var(--space-5);padding:var(--space-4);background:var(--color-paper);border-radius:var(--radius-md);border:1px solid oklch(0.90 0.01 80)">
            <p style="font-weight:500;margin-bottom:var(--space-3)">${i + 1}. ${q.question}</p>
            <textarea class="quiz-code-input" data-index="${i}" rows="6" placeholder="在此编写代码..." style="width:100%;padding:var(--space-3);border:1px solid oklch(0.85 0.01 80);border-radius:var(--radius-md);font-family:monospace;font-size:var(--text-sm);resize:vertical"></textarea>
            <div class="quiz-feedback" style="display:none;margin-top:var(--space-2);font-size:var(--text-sm)"></div>
            ${q.explanation ? `<div class="quiz-explanation" style="display:none;margin-top:var(--space-2);padding:var(--space-3);background:var(--color-paper-warm);border-radius:var(--radius-md);font-size:var(--text-sm);color:var(--color-ink-mid)">${q.explanation}</div>` : ''}
          </div>
        `;
      }
      // 默认 choice 类型
      return `
        <div class="quiz-question" data-index="${i}" data-type="choice" style="margin-bottom:var(--space-5);padding:var(--space-4);background:var(--color-paper);border-radius:var(--radius-md);border:1px solid oklch(0.90 0.01 80)">
          <p style="font-weight:500;margin-bottom:var(--space-3)">${i + 1}. ${q.question}</p>
          <div class="quiz-options">
            ${(q.options || []).map((opt, j) => `
              <label class="quiz-option" style="display:flex;align-items:center;gap:var(--space-2);padding:var(--space-2) var(--space-3);margin-bottom:var(--space-1);border-radius:var(--radius-md);cursor:pointer;font-size:var(--text-sm);transition:background 0.15s">
                <input type="radio" name="quiz_${i}" value="${letters[j]}" style="accent-color:var(--color-amber)">
                <span><strong>${letters[j]}.</strong> ${opt}</span>
              </label>
            `).join("")}
          </div>
          <div class="quiz-feedback" style="display:none;margin-top:var(--space-2);font-size:var(--text-sm)"></div>
          ${q.explanation ? `<div class="quiz-explanation" style="display:none;margin-top:var(--space-2);padding:var(--space-3);background:var(--color-paper-warm);border-radius:var(--radius-md);font-size:var(--text-sm);color:var(--color-ink-mid)">${q.explanation}</div>` : ''}
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
          isCorrect = userAnswer.length > 10; // 简单判断是否写了代码
        }

        if (isCorrect) correctCount++;

        if (feedback) {
          feedback.style.display = "block";
          if (qType === "choice") {
            if (isCorrect) {
              feedback.innerHTML = `<span style="color:var(--color-sage)">✓ 正确</span>`;
              feedback.closest(".quiz-question").style.borderColor = "var(--color-sage)";
            } else {
              feedback.innerHTML = `<span style="color:var(--color-rose)">✗ 错误</span>（正确答案：${q.answer}）`;
              feedback.closest(".quiz-question").style.borderColor = "var(--color-rose)";
            }
          } else if (qType === "fill") {
            if (isCorrect) {
              feedback.innerHTML = `<span style="color:var(--color-sage)">✓ 正确</span>`;
              feedback.closest(".quiz-question").style.borderColor = "var(--color-sage)";
            } else {
              feedback.innerHTML = `<span style="color:var(--color-rose)">✗ 错误</span>（正确答案：${q.answer}）`;
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
          student_answer: userAnswer,
          correct_answer: q.answer,
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
        await fetch(`${API_BASE}/api/evaluation/submit`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: "default", quiz_results: quizResults }),
        });
      } catch (e) {
        console.error("Failed to submit quiz:", e);
      }
    });
  },

  escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str || "";
    return div.innerHTML;
  },
});
