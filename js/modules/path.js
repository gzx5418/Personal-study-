App.register("path", {
  title: "学习路径",
  _currentView: "timeline",

  render() {
    return `
      <div class="path">
        <div class="section-head">
          <div>
            <h2 class="section-title">学习路径</h2>
            <p class="section-subtitle">基于知识依赖图和掌握度智能生成</p>
          </div>
          <div style="display:flex;gap:var(--space-2)">
            <div class="path-view-toggle" style="display:flex;border:1px solid oklch(0.85 0.01 80);border-radius:var(--radius-md);overflow:hidden">
              <button class="btn btn-sm path-view-btn is-active" data-view="timeline" style="border-radius:0;border:none">时间线</button>
              <button class="btn btn-sm path-view-btn" data-view="graph" style="border-radius:0;border:none">图谱</button>
            </div>
            <button class="btn btn-ghost" data-action="regenerate">重新生成</button>
          </div>
        </div>

        <div class="path-overview" id="pathOverview">
          <div class="path-overview-item">
            <span class="path-overview-label">学习目标</span>
            <span class="path-overview-value">加载中...</span>
          </div>
        </div>

        <div id="pathTimelineView">
          <div class="path-timeline" id="pathTimeline">
            <div class="path-stage">
              <div class="path-stage-dot">...</div>
              <div class="path-stage-card">
                <p>正在加载学习路径...</p>
              </div>
            </div>
          </div>
        </div>

        <div id="pathGraphView" style="display:none">
          <div class="path-graph-container" id="pathGraph" style="background:var(--color-paper-warm);border-radius:var(--radius-xl);border:1px solid oklch(0.88 0.01 80);padding:var(--space-6);min-height:400px;overflow:auto;text-align:center">
            <div class="typing-dots"><span></span><span></span><span></span></div>
            <p style="color:var(--color-ink-light);margin-top:var(--space-3)">正在加载知识图谱...</p>
          </div>
        </div>
      </div>
    `;
  },

  async bind(container) {
    $$(".path-view-btn", container).forEach(btn => {
      on(btn, "click", () => {
        $$(".path-view-btn", container).forEach(b => b.classList.remove("is-active"));
        btn.classList.add("is-active");
        const view = btn.dataset.view;
        this._currentView = view;
        const timelineView = $("#pathTimelineView", container);
        const graphView = $("#pathGraphView", container);
        if (view === "timeline") {
          timelineView.style.display = "block";
          graphView.style.display = "none";
        } else {
          timelineView.style.display = "none";
          graphView.style.display = "block";
          this._loadGraphView(container);
        }
      });
    });

    const btn = $("[data-action='regenerate']", container);
    if (btn) {
      on(btn, "click", async () => {
        showToast("正在根据最新掌握度调整学习路径...");
        await this._loadPath(container, true);
        showToast("学习路径已调整");
      });
    }

    await this._loadPath(container);
  },

  async _loadPath(container, isAdjust = false) {
    try {
      let pathData;
      if (isAdjust) {
        pathData = await Api.adjustPath("用户手动重新生成", AppState.currentUserId, AppState.currentCourseId);
      } else {
        pathData = await Api.planPath();
      }

      const stages = pathData.stages || [];
      const graphPath = pathData.graph_path || [];
      const recommended = pathData.recommended_next || [];
      const masterySummary = pathData.mastery_summary || {};
      const tips = pathData.tips || "";
      const focusAreas = pathData.focus_areas || [];

      const overviewEl = container.querySelector("#pathOverview");
      const timelineEl = container.querySelector("#pathTimeline");

      if (overviewEl) {
        overviewEl.innerHTML = `
          <div class="path-overview-item">
            <span class="path-overview-label">学习目标</span>
            <span class="path-overview-value">${escapeHtml(pathData.goal || "掌握 Python 程序设计核心知识")}</span>
          </div>
          <div class="path-overview-item">
            <span class="path-overview-label">预计时长</span>
            <span class="path-overview-value">${escapeHtml(pathData.duration || "待规划")}</span>
          </div>
          <div class="path-overview-item">
            <span class="path-overview-label">当前掌握度</span>
            <span class="path-overview-value">${Math.round((masterySummary.avg_level || 0) * 100)}%</span>
          </div>
          <div class="path-overview-item">
            <span class="path-overview-label">薄弱知识点</span>
            <span class="path-overview-value">${masterySummary.weak_count || 0} 个</span>
          </div>
        `;
      }

      if (timelineEl) {
        if (stages.length > 0) {
          const statusLabel = { completed: "已完成", current: "进行中", pending: "待学习", blocked: "需先修" };
          const statusClass = { completed: "completed", current: "current", pending: "pending", blocked: "pending" };

          timelineEl.innerHTML = stages.map((stage, i) => `
            <div class="path-stage path-stage-${statusClass[stage.status] || 'pending'}" data-index="${i}">
              <div class="path-stage-line"></div>
              <div class="path-stage-dot">
                ${stage.status === "completed" ? "&#10003;" : stage.status === "current" ? "" : (i + 1)}
                ${stage.status === "current" ? '<div class="path-stage-pulse"></div>' : ""}
              </div>
              <div class="path-stage-card">
                <div class="path-stage-head">
                  <h4 class="path-stage-name">${escapeHtml(stage.name)}</h4>
                  <span class="path-stage-badge path-stage-badge-${statusClass[stage.status] || 'pending'}">
                    ${statusLabel[stage.status] || escapeHtml(stage.status)} ${Math.round((stage.mastery_level || 0) * 100)}%
                  </span>
                </div>
                <p class="path-stage-desc">${escapeHtml(stage.desc || "")}</p>
                ${stage.topics && stage.topics.length > 0 ? `<p class="path-stage-desc" style="font-size:var(--text-xs);color:var(--color-ink-faint)">知识点: ${escapeHtml(stage.topics.join(", "))}</p>` : ""}
                ${stage.resources && stage.resources.length > 0 ? `<p class="path-stage-desc" style="font-size:var(--text-xs);color:var(--color-amber)">推荐: ${escapeHtml(stage.resources.join(", "))}</p>` : ""}
              </div>
            </div>
          `).join("");

          if (tips) {
            timelineEl.innerHTML += `
              <div class="path-stage" style="margin-top:var(--space-4)">
                <div class="path-stage-dot" style="background:var(--color-amber-surface);color:var(--color-amber)">!</div>
                <div class="path-stage-card" style="border-left:3px solid var(--color-amber)">
                  <h4 class="path-stage-name">个性化建议</h4>
                  <p class="path-stage-desc">${escapeHtml(tips)}</p>
                  ${focusAreas.length > 0 ? `<p class="path-stage-desc" style="font-size:var(--text-xs);margin-top:var(--space-2)">重点关注: ${escapeHtml(focusAreas.join(", "))}</p>` : ""}
                </div>
              </div>
            `;
          }
        } else if (graphPath.length > 0) {
          const statusLabel = { mastered: "已掌握", in_progress: "进行中", ready: "待学习", blocked: "需先修" };
          const statusClass = { mastered: "completed", in_progress: "current", ready: "pending", blocked: "pending" };

          timelineEl.innerHTML = graphPath.slice(0, 15).map((node, i) => `
            <div class="path-stage path-stage-${statusClass[node.status]}" data-index="${i}">
              <div class="path-stage-line"></div>
              <div class="path-stage-dot">
                ${node.status === "mastered" ? "&#10003;" : node.status === "in_progress" ? "" : (i + 1)}
                ${node.status === "in_progress" ? '<div class="path-stage-pulse"></div>' : ""}
              </div>
              <div class="path-stage-card">
                <div class="path-stage-head">
                  <h4 class="path-stage-name">${escapeHtml(node.name)}</h4>
                  <span class="path-stage-badge path-stage-badge-${statusClass[node.status]}">
                    ${statusLabel[node.status]} ${Math.round(node.mastery_level * 100)}%
                  </span>
                </div>
                <p class="path-stage-desc">${escapeHtml(node.chapter)} | 难度: ${"★".repeat(node.difficulty)}${"☆".repeat(5 - node.difficulty)}</p>
                ${node.prerequisites.length > 0 ? `<p class="path-stage-desc" style="font-size:var(--text-xs);color:var(--color-ink-faint)">前置: ${escapeHtml(node.prerequisites.join(", "))}</p>` : ""}
              </div>
            </div>
          `).join("");
        } else {
          timelineEl.innerHTML = `
            <div class="path-stage path-stage-current">
              <div class="path-stage-dot"><div class="path-stage-pulse"></div></div>
              <div class="path-stage-card">
                <h4 class="path-stage-name">开始学习之旅</h4>
                <p class="path-stage-desc">开始对话后，系统将自动构建您的学习画像并生成个性化路径</p>
              </div>
            </div>
          `;
        }
      }

      timelineEl.querySelectorAll(".path-stage-card").forEach(card => {
        card.style.cursor = "pointer";
        card.addEventListener("click", () => {
          const nameEl = card.querySelector(".path-stage-name");
          if (nameEl) {
            const topic = nameEl.textContent.trim();
            if (topic && topic !== "开始学习之旅" && topic !== "个性化建议") {
              window.location.hash = "#resources";
              setTimeout(() => {
                const topicInput = document.querySelector("#resTopicInput");
                if (topicInput) topicInput.value = topic;
              }, 200);
            }
          }
        });
      });
    } catch (e) {
      console.error("Failed to load path:", e);
      showToast("加载路径失败，请检查后端服务");
    }
  },

  async _loadGraphView(container) {
    const graphEl = $("#pathGraph", container);
    if (!graphEl) return;

    try {
      const data = await Api.getGraph(AppState.currentCourseId);
      const nodes = data.nodes || [];
      const masteryData = await Api.getMastery(AppState.currentUserId);
      const mastery = masteryData.mastery || {};

      if (nodes.length === 0) {
        graphEl.innerHTML = '<p style="color:var(--color-ink-light)">暂无知识图谱数据</p>';
        return;
      }

      if (typeof mermaid === 'undefined') {
        graphEl.innerHTML = '<p style="color:var(--color-ink-light)">Mermaid.js 未加载，无法渲染图谱</p>';
        return;
      }

      const nodeLines = nodes.map(n => {
        const m = mastery[n.id] || {};
        const level = m.level || 0;
        const pct = Math.round(level * 100);
        const icon = level >= 0.8 ? "✅" : level >= 0.5 ? "🔶" : level > 0 ? "🔴" : "⬜";
        const safeId = n.id.replace(/[^a-zA-Z0-9_]/g, '_');
        const safeName = n.name.replace(/["\]<>]/g, '');
        return `    ${safeId}["${icon} ${safeName}<br/>${pct}%"]`;
      });

      const edgeLines = [];
      nodes.forEach(n => {
        const prereqs = n.prerequisites || [];
        const safeId = n.id.replace(/[^a-zA-Z0-9_]/g, '_');
        prereqs.forEach(p => {
          const safeFrom = p.replace(/[^a-zA-Z0-9_]/g, '_');
          edgeLines.push(`    ${safeFrom} --> ${safeId}`);
        });
      });

      const graphDef = `graph TD\n${nodeLines.join('\n')}\n${edgeLines.join('\n')}`;

      const id = 'kg-' + Math.random().toString(36).substr(2, 9);
      try {
        const { svg } = await mermaid.render(id, graphDef);
        graphEl.innerHTML = `
          <div style="margin-bottom:var(--space-4)">
            <div style="display:flex;gap:var(--space-4);justify-content:center;font-size:var(--text-xs);color:var(--color-ink-light)">
              <span>✅ 已掌握 (≥80%)</span>
              <span>🔶 进行中 (50-80%)</span>
              <span>🔴 薄弱 (<50%)</span>
              <span>⬜ 未学习</span>
            </div>
          </div>
          <div style="overflow-x:auto">${svg}</div>
          <p style="font-size:var(--text-xs);color:var(--color-ink-faint);margin-top:var(--space-3)">点击节点可跳转到资源中心生成对应内容</p>
        `;

        graphEl.querySelectorAll('.node').forEach(nodeEl => {
          nodeEl.style.cursor = 'pointer';
          nodeEl.addEventListener('click', () => {
            const label = nodeEl.querySelector('.nodeLabel');
            if (label) {
              const text = label.textContent.replace(/[✅🔶🔴⬜]/g, '').replace(/\d+%/, '').trim();
              if (text) {
                window.location.hash = '#resources';
                setTimeout(() => {
                  const topicInput = document.querySelector('#resTopicInput');
                  if (topicInput) topicInput.value = text;
                }, 200);
              }
            }
          });
        });
      } catch (mermaidErr) {
        graphEl.innerHTML = `<p style="color:var(--color-rose)">图谱渲染失败，请刷新重试</p>`;
      }
    } catch (e) {
      console.error("Failed to load graph:", e);
      graphEl.innerHTML = '<p style="color:var(--color-rose)">加载知识图谱失败</p>';
    }
  },
});
