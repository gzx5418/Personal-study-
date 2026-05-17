App.register("path", {
  title: "学习路径",
  _currentView: "timeline",
  _nodeDetails: {},

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

        <div class="path-progress-bar-wrap" id="pathProgressWrap" style="display:none">
          <div class="path-progress-info">
            <span class="path-progress-label">整体完成度</span>
            <span class="path-progress-pct" id="pathProgressPct">0%</span>
          </div>
          <div class="path-progress-track">
            <div class="path-progress-fill" id="pathProgressFill" style="width:0%"></div>
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

        <div class="path-side-panels">
          <div class="path-panel path-rec-panel" id="pathRecPanel">
            <h3 class="path-panel-title">推荐学习</h3>
            <div class="path-panel-body" id="pathRecBody">
              <div class="typing-dots"><span></span><span></span><span></span></div>
            </div>
          </div>
          <div class="path-panel path-sr-panel" id="pathSrPanel">
            <h3 class="path-panel-title">间隔复习</h3>
            <div class="path-panel-body" id="pathSrBody">
              <div class="typing-dots"><span></span><span></span><span></span></div>
            </div>
          </div>
        </div>

        <div class="path-modal-overlay" id="pathNodeModal" style="display:none">
          <div class="path-modal">
            <button class="path-modal-close" id="pathModalClose">&times;</button>
            <div class="path-modal-body" id="pathModalBody"></div>
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

    const modalClose = $("#pathModalClose", container);
    if (modalClose) {
      on(modalClose, "click", () => this._closeModal(container));
    }

    const modalOverlay = $("#pathNodeModal", container);
    if (modalOverlay) {
      on(modalOverlay, "click", (e) => {
        if (e.target === modalOverlay) this._closeModal(container);
      });
    }

    await this._loadPath(container);
    this._loadRecommendations(container);
    this._loadSpacedRepetition(container);
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
          const completedCount = stages.filter(s => s.status === "completed").length;
          const progressPct = Math.round((completedCount / stages.length) * 100);
          this._updateProgressBar(container, progressPct);

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
                ${stage.topics && stage.topics.length > 0 ? this._renderTopicList(stage.topics, stage) : ""}
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
          const completedCount = graphPath.filter(n => n.status === "mastered").length;
          const progressPct = Math.round((completedCount / graphPath.length) * 100);
          this._updateProgressBar(container, progressPct);

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
          this._updateProgressBar(container, 0);
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

  _updateProgressBar(container, pct) {
    const wrap = container.querySelector("#pathProgressWrap");
    const fill = container.querySelector("#pathProgressFill");
    const pctEl = container.querySelector("#pathProgressPct");
    if (wrap) wrap.style.display = "block";
    if (fill) fill.style.width = pct + "%";
    if (pctEl) pctEl.textContent = pct + "%";
  },

  _renderTopicList(topics, stage) {
    const items = topics.map(t => {
      const name = typeof t === "string" ? t : (t.name || t.topic || "");
      const status = typeof t === "object" ? (t.status || "") : "";
      const mastery = typeof t === "object" ? (t.mastery || 0) : 0;
      let statusIcon = "";
      let statusClass = "";
      if (status === "mastered" || mastery >= 0.8) {
        statusIcon = "&#10003;";
        statusClass = "topic-mastered";
      } else if (status === "in_progress" || mastery >= 0.4) {
        statusIcon = "&#9679;";
        statusClass = "topic-learning";
      } else if (mastery > 0) {
        statusIcon = "&#9675;";
        statusClass = "topic-weak";
      } else {
        statusIcon = "&#9675;";
        statusClass = "topic-pending";
      }
      return `<span class="path-topic-tag ${statusClass}">${statusIcon} ${escapeHtml(name)}</span>`;
    }).join("");
    return `<div class="path-topic-list">${items}</div>`;
  },

  async _loadGraphView(container) {
    const graphEl = $("#pathGraph", container);
    if (!graphEl) return;

    try {
      let graphData;
      try {
        graphData = await Api.getLearningPathGraph(AppState.currentUserId, AppState.currentCourseId);
      } catch (_) {
        graphData = await Api.getGraph(AppState.currentCourseId);
      }

      const nodes = graphData.nodes || [];
      let mastery = {};
      try {
        const masteryData = await Api.getMastery(AppState.currentUserId);
        mastery = masteryData.mastery || {};
      } catch (_) {}

      if (nodes.length === 0) {
        graphEl.innerHTML = '<p style="color:var(--color-ink-light)">暂无知识图谱数据</p>';
        return;
      }

      this._nodeDetails = {};
      nodes.forEach(n => {
        const m = mastery[n.id] || {};
        const level = m.level || n.mastery || 0;
        this._nodeDetails[n.id] = {
          id: n.id,
          name: n.name,
          mastery: level,
          chapter: n.chapter || "",
          difficulty: n.difficulty || 0,
          prerequisites: n.prerequisites || [],
          status: n.status || (level >= 0.8 ? "mastered" : level > 0 ? "in_progress" : "ready"),
        };
      });

      if (typeof mermaid === 'undefined') {
        graphEl.innerHTML = '<p style="color:var(--color-ink-light)">Mermaid.js 未加载，无法渲染图谱</p>';
        return;
      }

      const nodeLines = nodes.map(n => {
        const m = mastery[n.id] || {};
        const level = m.level || n.mastery || 0;
        const pct = Math.round(level * 100);
        const safeId = n.id.replace(/[^a-zA-Z0-9_]/g, '_');
        const safeName = n.name.replace(/["\]<>]/g, '');
        return `    ${safeId}["${safeName}<br/>${pct}%"]:::${this._getMasteryClass(level)}`;
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

      const classDefs = [
        "    classDef mastered fill:#d4edda,stroke:#28a745,color:#155724",
        "    classDef learning fill:#fff3cd,stroke:#ffc107,color:#856404",
        "    classDef weak fill:#f8d7da,stroke:#dc3545,color:#721c24",
        "    classDef pending fill:#e9ecef,stroke:#6c757d,color:#383d41",
      ];

      const graphDef = `graph TD\n${nodeLines.join('\n')}\n${edgeLines.join('\n')}\n${classDefs.join('\n')}`;

      const id = 'kg-' + Math.random().toString(36).substr(2, 9);
      try {
        const { svg } = await mermaid.render(id, graphDef);
        graphEl.innerHTML = `
          <div class="path-graph-legend">
            <span class="path-legend-item"><span class="path-legend-dot" style="background:#28a745"></span>已掌握 (&ge;80%)</span>
            <span class="path-legend-item"><span class="path-legend-dot" style="background:#ffc107"></span>学习中 (40%-80%)</span>
            <span class="path-legend-item"><span class="path-legend-dot" style="background:#dc3545"></span>薄弱 (&lt;40%)</span>
            <span class="path-legend-item"><span class="path-legend-dot" style="background:#6c757d"></span>未开始</span>
          </div>
          <div style="overflow-x:auto">${svg}</div>
          <p style="font-size:var(--text-xs);color:var(--color-ink-faint);margin-top:var(--space-3)">点击节点查看详情</p>
        `;

        graphEl.querySelectorAll('.node').forEach(nodeEl => {
          nodeEl.style.cursor = 'pointer';
          nodeEl.addEventListener('click', () => {
            const label = nodeEl.querySelector('.nodeLabel');
            if (label) {
              const text = label.textContent.replace(/\d+%/, '').trim();
              const detailKey = Object.keys(this._nodeDetails).find(k => {
                const d = this._nodeDetails[k];
                return d.name === text || k.replace(/[^a-zA-Z0-9_\u4e00-\u9fff]/g, '') === text.replace(/[^a-zA-Z0-9_\u4e00-\u9fff]/g, '');
              });
              if (detailKey) {
                this._showNodeModal(container, this._nodeDetails[detailKey]);
              } else {
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

  _getMasteryClass(level) {
    if (level >= 0.8) return "mastered";
    if (level >= 0.4) return "learning";
    if (level > 0) return "weak";
    return "pending";
  },

  _showNodeModal(container, node) {
    const modal = $("#pathNodeModal", container);
    const body = $("#pathModalBody", container);
    if (!modal || !body) return;

    const pct = Math.round(node.mastery * 100);
    const masteryColor = node.mastery >= 0.8 ? "var(--color-sage)" : node.mastery >= 0.4 ? "var(--color-amber)" : node.mastery > 0 ? "var(--color-rose)" : "var(--color-ink-faint)";
    const masteryLabel = node.mastery >= 0.8 ? "已掌握" : node.mastery >= 0.4 ? "学习中" : node.mastery > 0 ? "薄弱" : "未开始";
    const difficultyStars = "★".repeat(node.difficulty || 0) + "☆".repeat(5 - (node.difficulty || 0));
    const prereqHtml = node.prerequisites && node.prerequisites.length > 0
      ? node.prerequisites.map(p => `<span class="path-modal-tag">${escapeHtml(p)}</span>`).join("")
      : '<span style="color:var(--color-ink-faint);font-size:var(--text-xs)">无前置要求</span>';

    body.innerHTML = `
      <div class="path-modal-header">
        <h3 class="path-modal-title">${escapeHtml(node.name)}</h3>
        <span class="path-modal-badge" style="background:${masteryColor};color:white">${masteryLabel} ${pct}%</span>
      </div>
      <div class="path-modal-progress">
        <div class="path-modal-progress-track">
          <div class="path-modal-progress-fill" style="width:${pct}%;background:${masteryColor}"></div>
        </div>
      </div>
      <div class="path-modal-grid">
        <div class="path-modal-field">
          <span class="path-modal-field-label">所属章节</span>
          <span class="path-modal-field-value">${escapeHtml(node.chapter || "未知")}</span>
        </div>
        <div class="path-modal-field">
          <span class="path-modal-field-label">难度</span>
          <span class="path-modal-field-value">${difficultyStars}</span>
        </div>
        <div class="path-modal-field">
          <span class="path-modal-field-label">掌握度</span>
          <span class="path-modal-field-value" style="color:${masteryColor}">${pct}%</span>
        </div>
      </div>
      <div class="path-modal-section">
        <h4 class="path-modal-section-title">前置知识点</h4>
        <div class="path-modal-tags">${prereqHtml}</div>
      </div>
      <div class="path-modal-actions">
        <button class="btn btn-primary" data-modal-action="learn" data-topic="${escapeHtml(node.name)}">开始学习</button>
        <button class="btn btn-ghost" data-modal-action="practice" data-topic="${escapeHtml(node.name)}">练习测试</button>
      </div>
    `;

    body.querySelectorAll("[data-modal-action]").forEach(btn => {
      on(btn, "click", () => {
        const action = btn.dataset.modalAction;
        const topic = btn.dataset.topic;
        this._closeModal(container);
        if (action === "practice") {
          window.location.hash = "#resources";
          setTimeout(() => {
            const typeSelect = document.querySelector("#resTypeSelect");
            const topicInput = document.querySelector("#resTopicInput");
            if (typeSelect) typeSelect.value = "quiz";
            if (topicInput) topicInput.value = topic;
          }, 200);
        } else {
          window.location.hash = "#resources";
          setTimeout(() => {
            const topicInput = document.querySelector("#resTopicInput");
            if (topicInput) topicInput.value = topic;
          }, 200);
        }
      });
    });

    modal.style.display = "flex";
  },

  _closeModal(container) {
    const modal = $("#pathNodeModal", container);
    if (modal) modal.style.display = "none";
  },

  async _loadRecommendations(container) {
    const body = $("#pathRecBody", container);
    if (!body) return;

    try {
      const data = await Api.getLearningPathRecommendations(AppState.currentUserId, AppState.currentCourseId);
      const recs = data.recommendations || data.items || data || [];

      if (!Array.isArray(recs) || recs.length === 0) {
        body.innerHTML = '<p class="path-panel-empty">暂无推荐，继续学习以获取个性化建议</p>';
        return;
      }

      body.innerHTML = recs.map((rec, i) => {
        const topic = rec.topic || rec.name || rec.title || "";
        const reason = rec.reason || rec.description || "";
        const estTime = rec.estimated_time || rec.duration || rec.time || "";
        const priority = rec.priority || rec.importance || "";
        const priorityClass = priority === "high" ? "rec-high" : priority === "medium" ? "rec-medium" : "rec-low";
        const mastery = rec.mastery || rec.current_mastery || 0;
        const pct = Math.round(mastery * 100);

        return `
          <div class="path-rec-card ${priorityClass}" data-rec-index="${i}">
            <div class="path-rec-head">
              <h4 class="path-rec-topic">${escapeHtml(topic)}</h4>
              ${priority ? `<span class="path-rec-priority path-rec-priority-${priorityClass}">${priority === "high" ? "高优" : priority === "medium" ? "中优" : "低优"}</span>` : ""}
            </div>
            ${reason ? `<p class="path-rec-reason">${escapeHtml(reason)}</p>` : ""}
            <div class="path-rec-meta">
              ${estTime ? `<span class="path-rec-time">&#9201; ${escapeHtml(estTime)}</span>` : ""}
              ${pct > 0 ? `<span class="path-rec-mastery">掌握度 ${pct}%</span>` : ""}
            </div>
            <button class="btn btn-ghost btn-sm path-rec-btn" data-rec-topic="${escapeHtml(topic)}">开始学习</button>
          </div>
        `;
      }).join("");

      body.querySelectorAll("[data-rec-topic]").forEach(btn => {
        on(btn, "click", () => {
          const topic = btn.dataset.recTopic;
          if (topic) {
            window.location.hash = "#resources";
            setTimeout(() => {
              const topicInput = document.querySelector("#resTopicInput");
              if (topicInput) topicInput.value = topic;
            }, 200);
          }
        });
      });
    } catch (e) {
      console.error("Failed to load recommendations:", e);
      body.innerHTML = '<p class="path-panel-empty">加载推荐失败</p>';
    }
  },

  async _loadSpacedRepetition(container) {
    const body = $("#pathSrBody", container);
    if (!body) return;

    try {
      const data = await Api.getSpacedRepetition(AppState.currentUserId, AppState.currentCourseId);
      const items = data.items || data.reviews || data.schedule || data || [];

      if (!Array.isArray(items) || items.length === 0) {
        body.innerHTML = '<p class="path-panel-empty">暂无待复习内容</p>';
        return;
      }

      body.innerHTML = items.map((item, i) => {
        const topic = item.topic || item.name || item.title || "";
        const nextReview = item.next_review || item.next_review_time || item.due_date || "";
        const interval = item.interval || item.review_interval || "";
        const urgency = item.urgency || "";
        const mastery = item.mastery || item.current_mastery || 0;
        const pct = Math.round(mastery * 100);
        const isOverdue = urgency === "overdue" || urgency === "high";
        const formattedTime = nextReview ? this._formatReviewTime(nextReview) : "";

        return `
          <div class="path-sr-card ${isOverdue ? 'path-sr-overdue' : ''}" data-sr-index="${i}">
            <div class="path-sr-head">
              <h4 class="path-sr-topic">${escapeHtml(topic)}</h4>
              ${isOverdue ? '<span class="path-sr-badge-overdue">已逾期</span>' : ""}
            </div>
            <div class="path-sr-meta">
              ${formattedTime ? `<span class="path-sr-time">${formattedTime}</span>` : ""}
              ${interval ? `<span class="path-sr-interval">间隔 ${escapeHtml(String(interval))}</span>` : ""}
              ${pct > 0 ? `<span class="path-sr-mastery">掌握度 ${pct}%</span>` : ""}
            </div>
            <button class="btn btn-ghost btn-sm path-sr-btn" data-sr-topic="${escapeHtml(topic)}">复习</button>
          </div>
        `;
      }).join("");

      body.querySelectorAll("[data-sr-topic]").forEach(btn => {
        on(btn, "click", () => {
          const topic = btn.dataset.srTopic;
          if (topic) {
            window.location.hash = "#resources";
            setTimeout(() => {
              const topicInput = document.querySelector("#resTopicInput");
              if (topicInput) topicInput.value = topic;
            }, 200);
          }
        });
      });
    } catch (e) {
      console.error("Failed to load spaced repetition:", e);
      body.innerHTML = '<p class="path-panel-empty">加载复习计划失败</p>';
    }
  },

  _formatReviewTime(timeStr) {
    if (!timeStr) return "";
    try {
      const date = new Date(timeStr);
      if (isNaN(date.getTime())) return "&#9201; " + escapeHtml(timeStr);
      const now = new Date();
      const diffMs = date.getTime() - now.getTime();
      const diffMins = Math.round(diffMs / 60000);
      const diffHours = Math.round(diffMs / 3600000);
      const diffDays = Math.round(diffMs / 86400000);

      let label;
      if (diffMins < 0) {
        const absMins = Math.abs(diffMins);
        if (absMins < 60) label = absMins + " 分钟前";
        else if (absMins < 1440) label = Math.round(absMins / 60) + " 小时前";
        else label = Math.round(absMins / 1440) + " 天前";
      } else if (diffMins < 60) {
        label = diffMins + " 分钟后";
      } else if (diffHours < 24) {
        label = diffHours + " 小时后";
      } else {
        label = diffDays + " 天后";
      }
      return "&#9201; " + label;
    } catch (_) {
      return "&#9201; " + escapeHtml(timeStr);
    }
  },
});
