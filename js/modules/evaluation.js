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
    await this._loadReport(container);

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

    this._loadRecentQuizzes(container);
  },

  async _loadReport(container) {
    try {
      const res = await fetch(`${API_BASE}/api/evaluation/mastery/default`);
      const data = await res.json();
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
            <span class="eval-dist-label">${levelLabels[k] || k}</span>
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
              <span class="eval-weak-name">${w.topic_id}</span>
              <span class="eval-weak-level" style="color:${w.level < 0.3 ? 'var(--color-rose)' : 'var(--color-amber)'}">${w.label} ${Math.round(w.level * 100)}%</span>
              <div class="eval-weak-bar">
                <div class="eval-weak-fill" style="width:${w.level * 100}%"></div>
              </div>
            </div>
          `).join("");
        }
      }

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
                <span class="eval-topic-name">${id}</span>
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

  async _loadRecentQuizzes(container) {
    const el = $("#evalRecentQuizzes", container);
    if (!el) return;

    try {
      const res = await fetch(`${API_BASE}/api/resources/list/default?type=quiz`);
      const data = await res.json();
      const quizzes = (data.resources || []).slice(0, 5);

      if (quizzes.length === 0) {
        el.innerHTML = '<p style="color:var(--color-ink-faint);font-size:var(--text-sm)">暂无练习记录，前往资源中心生成练习题。</p>';
        return;
      }

      el.innerHTML = `
        <h5 style="font-size:var(--text-sm);color:var(--color-ink-light);margin-bottom:var(--space-3)">最近生成的练习题</h5>
        ${quizzes.map(q => `
          <div style="display:flex;align-items:center;gap:var(--space-3);padding:var(--space-2) var(--space-3);background:var(--color-paper);border-radius:var(--radius-md);margin-bottom:var(--space-2);font-size:var(--text-sm)">
            <span style="flex:1">${q.topic || '未命名练习'}</span>
            <span style="color:var(--color-ink-faint);font-size:var(--text-xs)">${new Date((q.created_at || 0) * 1000).toLocaleDateString()}</span>
            <button class="btn btn-ghost btn-sm" onclick="window.location.hash='#resources'">查看</button>
          </div>
        `).join("")}
      `;
    } catch (e) {
      el.innerHTML = '<p style="color:var(--color-ink-faint);font-size:var(--text-sm)">加载练习记录失败</p>';
    }
  },
});
