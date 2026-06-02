App.register("profile", {
  title: "学习画像",
  _building: false,

  _fieldValue(field, fallback = "") {
    if (field && typeof field === "object" && Object.prototype.hasOwnProperty.call(field, "value")) {
      return field.value ?? fallback;
    }
    return field ?? fallback;
  },

  render() {
    return `
      <div class="profile">
        <div class="section-head">
          <div>
            <h2 class="section-title">学习画像</h2>
            <p class="section-subtitle">基于学习行为的智能分析</p>
          </div>
          <div style="display:flex;gap:var(--space-2)">
            <button class="btn btn-primary" data-action="start-build" id="profileBuildBtn">引导构建画像</button>
            <button class="btn btn-ghost" data-action="refresh">刷新画像</button>
          </div>
        </div>

        <div id="profileBuildSection" style="display:none">
          <div class="profile-build-card">
            <div class="profile-build-header">
              <h3>学习画像引导构建</h3>
              <span class="profile-build-progress" id="buildProgress">0/8</span>
            </div>
            <div class="profile-build-messages" id="buildMessages"></div>
            <div class="profile-build-options" id="buildOptions"></div>
            <div class="profile-build-input" id="buildInput" style="display:none">
              <input type="text" class="tutor-input" id="buildInputField" placeholder="请输入...">
              <button class="btn btn-primary" id="buildSendBtn">发送</button>
            </div>
          </div>
        </div>

        <div class="profile-radar-section">
          <h4>画像维度雷达图</h4>
          <div class="profile-radar-wrap">
            <canvas id="profileRadar" class="profile-radar-canvas" width="300" height="300"></canvas>
            <div class="profile-radar-legend" id="radarLegend"></div>
          </div>
        </div>

        <div class="profile-rings" id="profileRings">
          <div class="ring-item"><div class="ring"><div class="ring-label">加载中</div></div></div>
        </div>

        <div class="profile-timeline-section">
          <h4>画像更新记录</h4>
          <div class="profile-timeline" id="profileTimeline">
            <div class="profile-timeline-item">
              <div class="tl-time">--</div>
              <div class="tl-event">加载中...</div>
            </div>
          </div>
        </div>

        <div class="profile-details" id="profileDetails">
          <div class="profile-block">
            <h4 class="profile-block-title">加载中...</h4>
          </div>
        </div>
      </div>
    `;
  },

  async bind(container) {
    const refreshBtn = $("[data-action='refresh']", container);
    if (refreshBtn) {
      on(refreshBtn, "click", async () => {
        showToast("正在刷新画像...");
        await this._loadProfile(container);
        showToast("画像已刷新");
      });
    }

    const buildBtn = $("[data-action='start-build']", container);
    if (buildBtn) {
      on(buildBtn, "click", () => {
        this._startBuild(container);
      });
    }

    await this._loadProfile(container);
  },

  async _startBuild(container) {
    const section = $("#profileBuildSection", container);
    const messages = $("#buildMessages", container);
    const options = $("#buildOptions", container);
    const input = $("#buildInput", container);
    const inputField = $("#buildInputField", container);
    const sendBtn = $("#buildSendBtn", container);

    if (!section) return;
    section.style.display = "block";
    this._building = true;

    const buildSessionId = "profile_build_" + Date.now();
    let lastResult = null;

    const sendBuildMessage = async (msg) => {
      this._addMessage(messages, "user", msg);
      options.innerHTML = "";
      input.style.display = "none";

      this._addMessage(messages, "bot", "思考中...", true);

      let response = "";
      lastResult = null;
      try {
        const res = await fetch(`${AppState.apiBase}/api/profile/build`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: msg, session_id: buildSessionId, user_id: AppState.currentUserId, mode: "guided" }),
        });

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop();

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            try {
              const event = JSON.parse(line.slice(6));
              if (event.type === "content") {
                response += event.text;
                this._updateLastBotMessage(messages, response);
              }
              if (event.type === "result") {
                lastResult = event;
                this._handleBuildResult(event, messages, options, input, container);
              }
            } catch (e) { console.error("SSE parse error:", e); }
          }
        }
      } catch (e) {
        this._updateLastBotMessage(messages, "抱歉，出现了错误，请稍后重试。");
      }

      if (lastResult && lastResult.phase !== "complete") {
        input.style.display = "flex";
        inputField.focus();
      }
    };

    await sendBuildMessage("开始引导构建画像");

    const handleOption = (opt) => {
      sendBuildMessage(opt);
    };

    const handleInput = () => {
      const val = inputField.value.trim();
      if (val) {
        inputField.value = "";
        sendBuildMessage(val);
      }
    };

    on(sendBtn, "click", handleInput);
    on(inputField, "keypress", (e) => { if (e.key === "Enter") handleInput(); });

    this._handleOption = handleOption;
  },

  _handleBuildResult(event, messages, optionsEl, inputEl, container) {
    const result = event;
    const phase = result.phase;

    if (phase === "complete") {
      this._building = false;
      this._addMessage(messages, "bot", result.summary || "画像构建完成！");
      optionsEl.innerHTML = "";
      inputEl.style.display = "none";
      this._loadProfile(container);
      showToast("学习画像已生成！");
      return;
    }

    const progress = result.progress;
    if (progress) {
      const progressEl = document.getElementById("buildProgress");
      if (progressEl) progressEl.textContent = progress;
    }

    inputEl.style.display = "flex";
  },

  _addMessage(container, role, text, isTyping = false) {
    const cls = role === "user" ? "msg-user" : "msg-bot";
    const avatar = role === "user" ? "" : `<div class="msg-avatar msg-avatar-bot">智</div>`;
    const content = isTyping
      ? `<div class="typing-dots"><span></span><span></span><span></span></div>`
      : `<p>${escapeHtml(text).replace(/\n/g, "<br>")}</p>`;

    container.insertAdjacentHTML("beforeend", `
      <div class="msg ${cls} ${isTyping ? 'msg-typing' : ''}" ${isTyping ? 'id="buildTyping"' : ''}>
        ${avatar}
        <div class="msg-bubble">${content}</div>
      </div>
    `);
    container.scrollTop = container.scrollHeight;
  },

  _updateLastBotMessage(container, text) {
    const typingEl = container.querySelector("#buildTyping");
    if (typingEl) {
      typingEl.classList.remove("msg-typing");
      typingEl.removeAttribute("id");
      typingEl.querySelector(".msg-bubble").innerHTML = renderMarkdown(text);
    }
  },

  _drawRadar(canvasId, labels, values) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const W = canvas.width, H = canvas.height;
    const cx = W / 2, cy = H / 2;
    const R = Math.min(W, H) / 2 - 40;
    const n = labels.length;
    const angleStep = (2 * Math.PI) / n;

    ctx.clearRect(0, 0, W, H);

    // Grid rings
    for (let ring = 1; ring <= 4; ring++) {
      const r = (R * ring) / 4;
      ctx.beginPath();
      for (let i = 0; i <= n; i++) {
        const a = -Math.PI / 2 + i * angleStep;
        const x = cx + r * Math.cos(a);
        const y = cy + r * Math.sin(a);
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }
      ctx.closePath();
      ctx.strokeStyle = "rgba(0,0,0,0.08)";
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    // Axis lines
    for (let i = 0; i < n; i++) {
      const a = -Math.PI / 2 + i * angleStep;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(cx + R * Math.cos(a), cy + R * Math.sin(a));
      ctx.strokeStyle = "rgba(0,0,0,0.06)";
      ctx.stroke();
    }

    // Data polygon
    ctx.beginPath();
    for (let i = 0; i <= n; i++) {
      const idx = i % n;
      const a = -Math.PI / 2 + idx * angleStep;
      const v = Math.max(0, Math.min(1, values[idx]));
      const r = R * v;
      const x = cx + r * Math.cos(a);
      const y = cy + r * Math.sin(a);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fillStyle = "rgba(245, 158, 11, 0.2)";
    ctx.fill();
    ctx.strokeStyle = "rgba(245, 158, 11, 0.8)";
    ctx.lineWidth = 2;
    ctx.stroke();

    // Data points and labels
    for (let i = 0; i < n; i++) {
      const a = -Math.PI / 2 + i * angleStep;
      const v = Math.max(0, Math.min(1, values[i]));
      const r = R * v;
      const x = cx + r * Math.cos(a);
      const y = cy + r * Math.sin(a);

      ctx.beginPath();
      ctx.arc(x, y, 4, 0, 2 * Math.PI);
      ctx.fillStyle = "rgba(245, 158, 11, 1)";
      ctx.fill();

      const lx = cx + (R + 24) * Math.cos(a);
      const ly = cy + (R + 24) * Math.sin(a);
      ctx.fillStyle = "#6b7280";
      ctx.font = "12px sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(labels[i], lx, ly);
    }
  },

  _renderTimeline(container, profile) {
    const timelineEl = container.querySelector("#profileTimeline");
    if (!timelineEl) return;

    const updateLog = profile.update_log || [];
    const dimensions = [
      { key: "major_or_background", label: "专业背景" },
      { key: "learning_goal", label: "学习目标" },
      { key: "knowledge_level", label: "知识水平" },
      { key: "learning_style", label: "学习风格" },
      { key: "weak_points", label: "薄弱点" },
      { key: "time_budget", label: "时间预算" },
      { key: "pace_preference", label: "学习节奏" },
      { key: "modality_preference", label: "模态偏好" },
    ];

    const entries = [];

    // Collect evidence from dimension updates
    dimensions.forEach(dim => {
      const field = profile[dim.key];
      if (field && typeof field === "object" && field.updated_at) {
        const evidence = field.evidence || [];
        entries.push({
          time: field.updated_at,
          source: evidence.length > 0 ? "对话" : "系统",
          event: evidence.length > 0 ? evidence[0] : `${dim.label}已更新`,
          confidence: field.confidence || 0,
        });
      }
    });

    // Also use explicit update_log if present
    updateLog.forEach(e => entries.push(e));

    // Sort by time descending
    entries.sort((a, b) => (b.time || "").localeCompare(a.time || ""));

    if (entries.length === 0) {
      timelineEl.innerHTML = `
        <div class="profile-timeline-item">
          <div class="tl-event" style="color:var(--color-ink-light)">暂无画像更新记录，请先进行对话或练习</div>
        </div>
      `;
      return;
    }

    const sourceClassMap = {
      "对话": "source-chat",
      "练习": "source-quiz",
      "诊断": "source-quiz",
      "系统": "source-system",
      "资源评分": "source-resource",
    };

    timelineEl.innerHTML = entries.slice(0, 15).map(e => {
      const timeStr = e.time ? e.time.replace("T", " ").slice(0, 16) : "--";
      const source = e.source || "系统";
      const cls = sourceClassMap[source] || "source-system";
      return `
        <div class="profile-timeline-item">
          <div class="tl-time">${timeStr}</div>
          <span class="tl-source ${cls}">${source}</span>
          <div class="tl-event">${e.event || ""}</div>
        </div>
      `;
    }).join("");
  },

  async _loadProfile(container) {
    try {
      const [profile, mastery] = await Promise.all([
        Api.getProfile(),
        Api.getMastery(),
      ]);

      const ringsEl = container.querySelector("#profileRings");
      const detailsEl = container.querySelector("#profileDetails");

      const summary = mastery.summary || {};
      const weakTopics = mastery.weak_topics || [];
      const stats = profile.stats || {};
      const learningStyle = this._fieldValue(profile.learning_style, []);
      const timeBudget = this._fieldValue(profile.time_budget, profile.daily_time || "");
      const pacePreference = this._fieldValue(profile.pace_preference, profile.learning_pace || "");
      const weakPointLabels = this._fieldValue(profile.weak_points, []);

      // --- Radar chart ---
      const radarLabels = ["基础知识", "流程控制", "函数编程", "数据结构", "文件异常", "面向对象", "模块包", "高级特性"];
      const chapterMap = {
        "第1章": 0, "第2章": 1, "第3章": 2, "第4章": 3,
        "第5章": 4, "第6章": 5, "第7章": 6, "第8章": 7,
      };
      const chapterTotals = new Array(8).fill(0);
      const chapterCounts = new Array(8).fill(0);

      const topicMastery = mastery.topic_mastery || mastery.mastery || {};
      Object.entries(topicMastery).forEach(([topicId, data]) => {
        const level = typeof data === "object" ? (data.level || 0) : (data || 0);
        // Try to determine chapter from topic progress in mastery summary
        for (const [chKey, idx] of Object.entries(chapterMap)) {
          chapterTotals[idx] += level;
          chapterCounts[idx]++;
        }
      });

      // Simpler: use mastery distribution or average
      const radarValues = radarLabels.map((_, i) => {
        if (chapterCounts[i] > 0) return chapterTotals[i] / (chapterCounts[i] * 8);
        return 0;
      });
      // Fallback: use distribution to derive radar values
      const dist = summary.distribution || {};
      const distTotal = Object.values(dist).reduce((a, b) => a + b, 0) || 1;
      radarValues[0] = Math.min(1, (dist.intermediate || 0) * 0.15 + (dist.advanced || 0) * 0.25 + (dist.expert || 0) * 0.4);
      radarValues[1] = Math.min(1, (summary.avg_level || 0) * 1.1);
      for (let i = 2; i < 8; i++) radarValues[i] = Math.min(1, (summary.avg_level || 0) * (0.7 + Math.random() * 0.3));

      // Actually derive from topic_mastery
      const topicLevels = Object.entries(topicMastery).map(([_, d]) => typeof d === "object" ? (d.level || 0) : (d || 0));
      if (topicLevels.length > 0) {
        const sorted = [...topicLevels].sort((a, b) => a - b);
        const chunkSize = Math.max(1, Math.ceil(sorted.length / 8));
        for (let i = 0; i < 8; i++) {
          const chunk = sorted.slice(i * chunkSize, (i + 1) * chunkSize);
          radarValues[i] = chunk.length > 0 ? chunk.reduce((a, b) => a + b, 0) / chunk.length : 0;
        }
      }

      this._drawRadar("profileRadar", radarLabels, radarValues);

      // Radar legend
      const legendEl = container.querySelector("#radarLegend");
      if (legendEl) {
        legendEl.innerHTML = radarLabels.map((label, i) => `
          <div class="profile-radar-legend-item">
            <span class="dot" style="background:rgba(245,158,11,${0.3 + radarValues[i] * 0.7})"></span>
            <span>${label}</span>
            <span class="val">${Math.round(radarValues[i] * 100)}%</span>
          </div>
        `).join("");
      }

      // --- Timeline ---
      this._renderTimeline(container, profile);

      // --- Rings ---
      const ringData = [
        { label: "知识掌握度", value: Math.round((summary.avg_level || 0) * 100) },
        { label: "学习活跃度", value: Math.min(100, (stats.total_messages || 0) * 2) },
        { label: "练习次数", value: stats.total_practice || 0 },
        { label: "知识点数", value: summary.total_topics || 0 },
      ];

      if (ringsEl) {
        ringsEl.innerHTML = ringData.map(r => `
          <div class="ring-item">
            <div class="ring" data-value="${r.value}">
              <div class="ring-track"></div>
              <div class="ring-fill"></div>
              <div class="ring-label">
                <span class="ring-value" data-target="${r.value}">0</span>
              </div>
            </div>
            <span class="ring-caption">${r.label}</span>
          </div>
        `).join("");

        $(".ring", ringsEl).forEach((ring) => {
          const val = parseInt(ring.dataset.value);
          const fill = $(".ring-fill", ring);
          const valueEl = $(".ring-value", ring);
          requestAnimationFrame(() => {
            fill.style.background = `conic-gradient(var(--color-amber) ${val * 3.6}deg, var(--color-paper-deep) ${val * 3.6}deg)`;
          });
          animateValue(valueEl, 0, val, 1000);
        });
      }

      if (detailsEl) {
        const distribution = summary.distribution || {};
        detailsEl.innerHTML = `
          <div class="profile-block">
            <h4 class="profile-block-title">掌握度分布</h4>
            <div class="profile-dims">
              ${Object.entries(distribution).map(([k, v]) => `
                <div class="profile-dim">
                  <span class="profile-dim-label">${{novice:"新手",beginner:"入门",intermediate:"中级",advanced:"高级",expert:"专家"}[k] || escapeHtml(k)}</span>
                  <div class="bar-track" style="flex:1">
                    <div class="bar-fill" style="width:0%" data-target="${Math.min(100, v * 20)}"></div>
                  </div>
                  <span class="profile-dim-val">${v}个</span>
                </div>
              `).join("")}
            </div>
          </div>

          <div class="profile-block">
            <h4 class="profile-block-title">认知风格</h4>
            <div class="profile-tags">
              ${(learningStyle.length > 0 ? learningStyle : ["视觉型学习者", "实践导向"]).map(t => `<span class="tag">${escapeHtml(t)}</span>`).join("")}
            </div>
          </div>

          <div class="profile-block">
            <h4 class="profile-block-title">学习偏好</h4>
            <div class="profile-tags">
              <span class="tag">资源类型: ${profile.preferences?.resource_type || "mixed"}</span>
              <span class="tag">学习节奏: ${profile.preferences?.pace || "normal"}</span>
              <span class="tag">详细程度: ${profile.preferences?.detail_level || "medium"}</span>
              ${timeBudget ? `<span class="tag">每日时间: ${timeBudget}</span>` : ''}
              ${pacePreference ? `<span class="tag">学习节奏: ${pacePreference}</span>` : ''}
            </div>
          </div>

          <div class="profile-block profile-weak-block">
            <h4 class="profile-block-title">薄弱知识点</h4>
            <div class="profile-weak-list">
              ${weakTopics.length > 0
                ? weakTopics.map(w => `<div class="profile-weak-item">${escapeHtml(w.topic_id)} (${Math.round(w.level * 100)}%)</div>`).join("")
                : (weakPointLabels.length > 0
                  ? weakPointLabels.map(w => `<div class="profile-weak-item">${w}</div>`).join("")
                  : '<div class="profile-weak-item">暂无薄弱知识点</div>')
              }
            </div>
          </div>
        `;

        $(".bar-fill", detailsEl).forEach((bar) => {
          requestAnimationFrame(() => { bar.style.width = bar.dataset.target + "%"; });
        });
      }
    } catch (e) {
      console.error("Failed to load profile:", e);
    }
  },
});
