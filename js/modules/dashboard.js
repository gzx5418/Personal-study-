App.register("dashboard", {
  title: "首页",

  render() {
    const hour = new Date().getHours();
    let greeting = "晚上好";
    if (hour < 6) greeting = "夜深了";
    else if (hour < 12) greeting = "早上好";
    else if (hour < 18) greeting = "下午好";

    return `
      <div class="dashboard">
        <div class="dash-hero">
          <h1 class="dash-greeting">${greeting}</h1>
          <p class="dash-greeting-sub">根据您的学习画像，为您推荐今天的学习内容</p>
        </div>

        <div class="dash-grid">
          <div class="dash-featured card">
            <div class="dash-featured-badge">今日推荐</div>
            <h3 class="dash-featured-title" id="dashFeaturedTitle">加载中...</h3>
            <p class="dash-featured-desc" id="dashFeaturedDesc"></p>
            <div class="dash-featured-meta">
              <span class="tag tag-filled" id="dashFeaturedType">资源</span>
            </div>
            <button class="btn btn-primary dash-featured-btn" data-action="open-resource">开始学习</button>
          </div>

          <div class="dash-list">
            <h4 class="dash-list-heading">更多推荐</h4>
            <div id="dashRecommendList">加载中...</div>
          </div>
        </div>

        <div class="dash-progress-section">
          <h3 class="section-title" style="font-size:var(--text-xl)">学习进度</h3>
          <div class="dash-courses" id="dashCourses">
            <div class="dash-course">
              <div class="dash-course-head">
                <span class="dash-course-name">加载中...</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  },

  _prefTopic: "",

  bind(container) {
    this._prefTopic = "";
    this._loadProfile(container);
    this._loadRecommendations(container);

    const openBtn = $("[data-action='open-resource']", container);
    if (openBtn) {
      on(openBtn, "click", (e) => {
        e.stopPropagation();
        window.location.hash = "#resources";
        if (this._prefTopic) {
          setTimeout(() => {
            const topicInput = document.querySelector("#resTopicInput");
            if (topicInput) topicInput.value = this._prefTopic;
          }, 200);
        }
      });
    }
  },

  async _loadProfile(container) {
    try {
      const profile = await Api.getProfile();
      const stats = profile.stats || {};
      const coursesEl = container.querySelector("#dashCourses");
      if (coursesEl) {
        coursesEl.innerHTML = `
          <div class="dash-course">
            <div class="dash-course-head">
              <span class="dash-course-name">学习消息数</span>
              <span class="dash-course-pct">${stats.total_messages || 0}</span>
            </div>
            <div class="bar-track"><div class="bar-fill" style="width:0%" data-target="${Math.min(100, (stats.total_messages || 0) * 2)}"></div></div>
          </div>
          <div class="dash-course">
            <div class="dash-course-head">
              <span class="dash-course-name">练习次数</span>
              <span class="dash-course-pct">${stats.total_practice || 0}</span>
            </div>
            <div class="bar-track"><div class="bar-fill" style="width:0%" data-target="${Math.min(100, (stats.total_practice || 0) * 5)}"></div></div>
          </div>
        `;
        $$(".bar-fill", coursesEl).forEach((bar) => {
          requestAnimationFrame(() => { bar.style.width = bar.dataset.target + "%"; });
        });
      }
    } catch (e) {
      console.error("Failed to load profile:", e);
    }
  },

  async _loadRecommendations(container) {
    try {
      const mastery = await Api.getMastery();
      const weakTopics = mastery.weak_topics || [];
      const featuredTitle = container.querySelector("#dashFeaturedTitle");
      const featuredDesc = container.querySelector("#dashFeaturedDesc");
      const listEl = container.querySelector("#dashRecommendList");

      if (weakTopics.length > 0) {
        if (featuredTitle) featuredTitle.textContent = `重点复习：${weakTopics[0].topic_id}`;
        if (featuredDesc) featuredDesc.textContent = `掌握度 ${Math.round(weakTopics[0].level * 100)}%，建议加强练习`;
        this._prefTopic = weakTopics[0].topic_id;
      } else {
        if (featuredTitle) featuredTitle.textContent = "您学习表现优秀！";
        if (featuredDesc) featuredDesc.textContent = "继续保持，可以尝试更高难度的内容";
      }

      if (listEl) {
        const items = weakTopics.slice(1, 4);
        if (items.length === 0) {
          listEl.innerHTML = '<p style="color:var(--color-ink-light);padding:var(--space-4)">暂无薄弱知识点</p>';
        } else {
          listEl.innerHTML = items.map(t => `
            <button class="dash-list-item" data-topic="${t.topic_id}" data-action="go-resource">
              <span class="dash-list-icon">!</span>
              <div class="dash-list-info">
                <span class="dash-list-title">${t.topic_id}</span>
                <span class="dash-list-type">掌握度 ${Math.round(t.level * 100)}%</span>
              </div>
              <span class="dash-list-arrow">&rarr;</span>
            </button>
          `).join("");

          listEl.querySelectorAll("[data-action='go-resource']").forEach(btn => {
            on(btn, "click", () => {
              const topic = btn.dataset.topic;
              window.location.hash = "#resources";
              setTimeout(() => {
                const topicInput = document.querySelector("#resTopicInput");
                if (topicInput) topicInput.value = topic;
              }, 200);
            });
          });
        }
      }
    } catch (e) {
      console.error("Failed to load recommendations:", e);
    }
  },
});
