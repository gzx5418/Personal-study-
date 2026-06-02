App.register("evaluation", {
  title: "学习评估",

  render() {
    return `
      <div class="evaluation">
        <div class="section-head">
          <div>
            <h2 class="section-title">学习评估报告</h2>
            <p class="section-subtitle">基于练习数据和学习行为的综合分析</p>
          </div>
          <button class="btn btn-ghost" data-action="refresh-eval">刷新报告</button>
        </div>

        <div class="eval-overview" id="evalOverview">
          <div class="eval-stat-card">
            <div class="eval-stat-value" id="evalTotalTopics">0</div>
            <div class="eval-stat-label">已学知识点</div>
          </div>
          <div class="eval-stat-card">
            <div class="eval-stat-value" id="evalAvgLevel">0%</div>
            <div class="eval-stat-label">平均掌握度</div>
          </div>
          <div class="eval-stat-card">
            <div class="eval-stat-value" id="evalWeakCount">0</div>
            <div class="eval-stat-label">薄弱知识点</div>
          </div>
          <div class="eval-stat-card">
            <div class="eval-stat-value" id="evalStrongCount">0</div>
            <div class="eval-stat-label">已掌握知识点</div>
          </div>
        </div>

        <div class="eval-grid">
          <div class="eval-block">
            <h4 class="eval-block-title">掌握度分布</h4>
            <div id="evalDistribution" class="eval-distribution"></div>
          </div>

          <div class="eval-block">
            <h4 class="eval-block-title">薄弱知识点</h4>
            <div id="evalWeakTopics" class="eval-weak-list"></div>
          </div>
        </div>

        <div class="eval-block" style="margin-top:var(--space-6)">
          <h4 class="eval-block-title">掌握度变化趋势</h4>
          <canvas id="evalMasteryChart" width="700" height="280" style="width:100%;max-width:700px;display:block"></canvas>
          <p id="evalChartEmpty" style="color:var(--color-ink-light);font-size:var(--text-sm);display:none">完成练习后将显示掌握度变化趋势</p>
        </div>

        <div class="eval-block" style="margin-top:var(--space-6)">
          <h4 class="eval-block-title">错因分析</h4>
          <div id="evalErrorAnalysis" class="eval-error-grid"></div>
        </div>

        <div class="eval-block" style="margin-top:var(--space-6)">
          <h4 class="eval-block-title">知识点掌握详情</h4>
          <div id="evalTopicDetails" class="eval-topic-grid"></div>
        </div>

        <div class="eval-block" style="margin-top:var(--space-6)">
          <h4 class="eval-block-title">练习记录</h4>
          <div id="evalQuizSection">
            <p style="color:var(--color-ink-light);font-size:var(--text-sm);margin-bottom:var(--space-3)">前往资源中心生成练习题，在线作答后自动提交评估。</p>
            <button class="btn btn-primary" id="evalGoQuiz">前往资源中心生成练习</button>
            <div id="evalRecentQuizzes" style="margin-top:var(--space-4)"></div>
          </div>
        </div>
      </div>
    `;
  },

  async bind(container) {
    const refreshBtn = $("[data-action='refresh-eval']", container);
    if (refreshBtn) {
      on(refreshBtn, "click", async () => {
        showToast("正在刷新报告...");
        await this._loadReport(container);
        showToast("报告已刷新");
      });
    }

    const goQuizBtn = $("#evalGoQuiz", container);
    if (goQuizBtn) {
      on(goQuizBtn, "click", () => {
        window.location.hash = "#resources";
        setTimeout(() => {
          const typeSelect = document.querySelector("#resTypeSelect");
          if (typeSelect) typeSelect.value = "quiz";
        }, 200);
      });
    }

    await this._loadReport(container);
    this._loadRecentQuizzes(container);
  },

  async _loadReport(container) {
    try {
      const data = await Api.getMastery(AppState.currentUserId);
      const summary = data.summary || {};
      const weakTopics = data.weak_topics || [];
      const mastery = data.mastery || {};

      const totalTopics = summary.total_topics || 0;
      const avgLevel = summary.avg_level || 0;
      const weakCount = summary.weak_count || 0;
      const strongCount = summary.strong_count || 0;
      const distribution = summary.distribution || {};

      $("#evalTotalTopics", container).textContent = totalTopics;
      $("#evalAvgLevel", container).textContent = Math.round(avgLevel * 100) + "%";
      $("#evalWeakCount", container).textContent = weakCount;
      $("#evalStrongCount", container).textContent = strongCount;

      const distEl = $("#evalDistribution", container);
      if (distEl) {
        const levelLabels = { novice: "新手", beginner: "入门", intermediate: "中级", advanced: "高级", expert: "专家" };
        const levelColors = { novice: "var(--color-rose)", beginner: "var(--color-amber)", intermediate: "var(--color-sage)", advanced: "var(--color-amber-bright)", expert: "var(--color-ink)" };
        const maxCount = Math.max(1, ...Object.values(distribution));

        distEl.innerHTML = Object.entries(distribution).map(([k, v]) => `
          <div class="eval-dist-item">
            <span class="eval-dist-label">${levelLabels[k] || escapeHtml(k)}</span>
            <div class="eval-dist-bar">
              <div class="eval-dist-fill" style="width:${(v / maxCount) * 100}%;background:${levelColors[k] || 'var(--color-amber)'}"></div>
            </div>
            <span class="eval-dist-count">${v}</span>
          </div>
        `).join("");
      }

      const weakEl = $("#evalWeakTopics", container);
      if (weakEl) {
        if (weakTopics.length === 0) {
          weakEl.innerHTML = '<p style="color:var(--color-ink-light);padding:var(--space-4)">暂无薄弱知识点，继续保持！</p>';
        } else {
          weakEl.innerHTML = weakTopics.map(w => `
            <div class="eval-weak-item">
              <span class="eval-weak-name">${escapeHtml(w.topic_id)}</span>
              <span class="eval-weak-level" style="color:${w.level < 0.3 ? 'var(--color-rose)' : 'var(--color-amber)'}">${w.label} ${Math.round(w.level * 100)}%</span>
              <div class="eval-weak-bar">
                <div class="eval-weak-fill" style="width:${w.level * 100}%"></div>
              </div>
            </div>
          `).join("");
        }
      }

      // --- Mastery change chart ---
      this._drawMasteryChart(container, mastery);

      // --- Error analysis ---
      this._renderErrorAnalysis(container, weakTopics, mastery);

      const topicEl = $("#evalTopicDetails", container);
      if (topicEl) {
        const topics = Object.entries(mastery).sort((a, b) => b[1].level - a[1].level);
        if (topics.length === 0) {
          topicEl.innerHTML = '<p style="color:var(--color-ink-light);padding:var(--space-4)">暂无练习数据</p>';
        } else {
          topicEl.innerHTML = topics.map(([id, t]) => {
            const pct = Math.round(t.level * 100);
            const color = pct >= 70 ? 'var(--color-sage)' : pct >= 40 ? 'var(--color-amber)' : 'var(--color-rose)';
            return `
              <div class="eval-topic-item">
                <span class="eval-topic-name">${escapeHtml(id)}</span>
                <span class="eval-topic-pct" style="color:${color}">${pct}%</span>
                <span class="eval-topic-attempts">${t.attempts}次</span>
              </div>
            `;
          }).join("");
        }
      }
    } catch (e) {
      console.error("Failed to load evaluation report:", e);
    }
  },

  _drawMasteryChart(container, mastery) {
    const canvas = document.getElementById("evalMasteryChart");
    const emptyMsg = document.getElementById("evalChartEmpty");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    const topics = Object.entries(mastery);
    if (topics.length === 0) {
      canvas.style.display = "none";
      if (emptyMsg) emptyMsg.style.display = "block";
      return;
    }
    canvas.style.display = "block";
    if (emptyMsg) emptyMsg.style.display = "none";

    // Pick top 8 topics with history
    const chartTopics = topics
      .filter(([_, d]) => d.history && d.history.length > 1)
      .slice(0, 8);

    if (chartTopics.length === 0) {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = "#9ca3af";
      ctx.font = "13px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("完成更多练习后将显示掌握度变化趋势", canvas.width / 2, canvas.height / 2);
      return;
    }

    const W = canvas.width, H = canvas.height;
    const padL = 50, padR = 20, padT = 20, padB = 60;
    const plotW = W - padL - padR;
    const plotH = H - padT - padB;

    ctx.clearRect(0, 0, W, H);

    // Y-axis gridlines
    for (let i = 0; i <= 4; i++) {
      const y = padT + (plotH * (4 - i)) / 4;
      ctx.beginPath();
      ctx.moveTo(padL, y);
      ctx.lineTo(W - padR, y);
      ctx.strokeStyle = "rgba(0,0,0,0.06)";
      ctx.stroke();
      ctx.fillStyle = "#9ca3af";
      ctx.font = "11px sans-serif";
      ctx.textAlign = "right";
      ctx.fillText((i * 25) + "%", padL - 6, y + 4);
    }

    const colors = [
      "rgba(245,158,11,1)", "rgba(59,130,246,1)", "rgba(16,185,129,1)", "rgba(239,68,68,1)",
      "rgba(139,92,246,1)", "rgba(236,72,153,1)", "rgba(14,165,233,1)", "rgba(249,115,22,1)",
    ];

    chartTopics.forEach(([topicId, data], idx) => {
      const history = data.history || [];
      if (history.length < 2) return;
      const maxLen = Math.max(...chartTopics.map(([_, d]) => (d.history || []).length));
      const color = colors[idx % colors.length];

      ctx.beginPath();
      history.forEach((val, i) => {
        const x = padL + (plotW * i) / (maxLen - 1 || 1);
        const y = padT + plotH * (1 - val);
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      });
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.stroke();

      // Data points
      history.forEach((val, i) => {
        const x = padL + (plotW * i) / (maxLen - 1 || 1);
        const y = padT + plotH * (1 - val);
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, 2 * Math.PI);
        ctx.fillStyle = color;
        ctx.fill();
      });
    });

    // Legend
    ctx.font = "11px sans-serif";
    ctx.textAlign = "left";
    chartTopics.forEach(([topicId, _], idx) => {
      const x = padL + (idx % 4) * 160;
      const y = H - 10 - Math.floor(idx / 4) * 16;
      ctx.fillStyle = colors[idx % colors.length];
      ctx.fillRect(x, y - 4, 8, 8);
      ctx.fillStyle = "#6b7280";
      ctx.fillText(topicId.replace("py_", ""), x + 12, y + 4);
    });
  },

  _renderErrorAnalysis(container, weakTopics, mastery) {
    const el = document.getElementById("evalErrorAnalysis");
    if (!el) return;

    if (weakTopics.length === 0) {
      el.innerHTML = '<p style="color:var(--color-ink-light);padding:var(--space-4)">暂无错题数据</p>';
      return;
    }

    const errorTypes = [
      { type: "概念混淆", icon: "🔄", desc: "相似概念区分不清" },
      { type: "语法错误", icon: "✏️", desc: "语法格式或拼写错误" },
      { type: "逻辑错误", icon: "🧩", desc: "解题思路或流程错误" },
      { type: "代码调试", icon: "🔍", desc: "无法定位或修复错误" },
    ];

    // Categorize weak topics into error types heuristically
    const topicNames = weakTopics.map(w => w.topic_id || "");
    const categories = {
      "概念混淆": [],
      "语法错误": [],
      "逻辑错误": [],
      "代码调试": [],
    };

    topicNames.forEach(name => {
      if (name.includes("datatype") || name.includes("operator") || name.includes("comprehension")) {
        categories["概念混淆"].push(name);
      } else if (name.includes("syntax") || name.includes("string") || name.includes("comment")) {
        categories["语法错误"].push(name);
      } else if (name.includes("for") || name.includes("while") || name.includes("recursive") || name.includes("func")) {
        categories["逻辑错误"].push(name);
      } else {
        categories["代码调试"].push(name);
      }
    });

    el.innerHTML = errorTypes.map(et => {
      const items = categories[et.type];
      const count = items.length;
      return `
        <div class="eval-error-card">
          <div class="eval-error-header">
            <span class="eval-error-icon">${et.icon}</span>
            <span class="eval-error-type">${et.type}</span>
            <span class="eval-error-count">${count}次</span>
          </div>
          <div class="eval-error-desc">${et.desc}</div>
          ${count > 0 ? `<div class="eval-error-topics">${items.map(i => `<span class="tag">${i}</span>`).join("")}</div>` : ''}
          <div class="eval-error-suggestion">
            ${et.type === "概念混淆" ? "建议：多使用思维导图资源理清概念关系" : ""}
            ${et.type === "语法错误" ? "建议：多做代码实操练习巩固语法记忆" : ""}
            ${et.type === "逻辑错误" ? "建议：使用动画资源可视化理解执行流程" : ""}
            ${et.type === "代码调试" ? "建议：练习阅读报错信息和单步调试" : ""}
          </div>
        </div>
      `;
    }).join("");
  },

  async _loadRecentQuizzes(container) {
    const el = $("#evalRecentQuizzes", container);
    if (!el) return;

    try {
      const data = await Api.listResources(AppState.currentUserId, "quiz", AppState.currentCourseId);
      const quizzes = (data.resources || []).slice(0, 5);

      if (quizzes.length === 0) {
        el.innerHTML = '<p style="color:var(--color-ink-faint);font-size:var(--text-sm)">暂无练习记录，前往资源中心生成练习题。</p>';
        return;
      }

      el.innerHTML = `
        <h5 style="font-size:var(--text-sm);color:var(--color-ink-light);margin-bottom:var(--space-3)">最近生成的练习题</h5>
        ${quizzes.map(q => `
          <div style="display:flex;align-items:center;gap:var(--space-3);padding:var(--space-2) var(--space-3);background:var(--color-paper);border-radius:var(--radius-md);margin-bottom:var(--space-2);font-size:var(--text-sm)">
            <span style="flex:1">${escapeHtml(q.topic || '未命名练习')}</span>
            <span style="color:var(--color-ink-faint);font-size:var(--text-xs)">${new Date((q.created_at || 0) * 1000).toLocaleDateString()}</span>
            <button class="btn btn-ghost btn-sm eval-go-quiz-btn">查看</button>
          </div>
        `).join("")}
      `;

      el.querySelectorAll(".eval-go-quiz-btn").forEach(btn => {
        btn.addEventListener("click", () => {
          window.location.hash = "#resources";
          setTimeout(() => {
            const typeSelect = document.querySelector("#resTypeSelect");
            if (typeSelect) typeSelect.value = "quiz";
          }, 200);
        });
      });
    } catch (e) {
      el.innerHTML = '<p style="color:var(--color-ink-faint);font-size:var(--text-sm)">加载练习记录失败</p>';
    }
  },
});
