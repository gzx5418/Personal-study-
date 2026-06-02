const AppState = {
  apiBase:
    window.localStorage.getItem("ZHIXUE_API_BASE") ||
    `${window.location.protocol}//${window.location.hostname}:8001`,
  currentUserId: window.localStorage.getItem("ZHIXUE_USER_ID") || "demo_student",
  currentCourseId: window.localStorage.getItem("ZHIXUE_COURSE_ID") || "python_programming",
  appName: "智学助手",
  maxUploadSizeMb: 10,
  modelCatalog: { text: [], reasoning: [], vision: [], embedding: [], defaults: {} },

  async init() {
    try {
      const res = await fetch(`${this.apiBase}/api/config`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      if (data.api_base_url) this.apiBase = data.api_base_url;
      if (!window.localStorage.getItem("ZHIXUE_USER_ID") && data.default_user_id) {
        this.currentUserId = data.default_user_id;
      }
      if (!window.localStorage.getItem("ZHIXUE_COURSE_ID") && data.default_course_id) {
        this.currentCourseId = data.default_course_id;
      }
      this.appName = data.app_name || this.appName;
      this.maxUploadSizeMb = data.max_upload_size_mb || this.maxUploadSizeMb;
      this.modelCatalog = data.model_catalog || this.modelCatalog;
    } catch (err) {
      console.warn("Failed to load app config:", err);
    }
    this.persist();
  },

  persist() {
    window.localStorage.setItem("ZHIXUE_API_BASE", this.apiBase);
    window.localStorage.setItem("ZHIXUE_USER_ID", this.currentUserId);
    window.localStorage.setItem("ZHIXUE_COURSE_ID", this.currentCourseId);
  },

  setCourseId(courseId) {
    this.currentCourseId = courseId;
    this.persist();
  },
};

function getApiBase() {
  return AppState.apiBase;
}

// Default timeouts (ms)
const DEFAULT_FETCH_TIMEOUT = 30000;
const DEFAULT_STREAM_TIMEOUT = 120000;

async function _fetchJson(url, options = {}, timeoutMs = DEFAULT_FETCH_TIMEOUT) {
  const controller = new AbortController();
  const externalSignal = options.signal;
  if (externalSignal) {
    if (externalSignal.aborted) controller.abort();
    else externalSignal.addEventListener("abort", () => controller.abort(), { once: true });
  }
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { ...options, signal: controller.signal });
    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new Error(`HTTP ${res.status}: ${text.slice(0, 200)}`);
    }
    return res.json();
  } catch (e) {
    if (e.name === "AbortError") {
      throw new Error("请求超时，请检查网络连接");
    }
    throw e;
  } finally {
    clearTimeout(timeoutId);
  }
}

const Api = {
  // Active in-flight request controllers, keyed by requestId
  _activeRequests: new Map(),

  cancelRequest(requestId) {
    const controller = this._activeRequests.get(requestId);
    if (controller) {
      controller.abort();
      this._activeRequests.delete(requestId);
    }
  },

  cancelAll() {
    this._activeRequests.forEach((controller) => {
      try { controller.abort(); } catch (e) {}
    });
    this._activeRequests.clear();
  },

  async _fetch(url, options = {}, timeoutMs = DEFAULT_FETCH_TIMEOUT) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const res = await fetch(url, { ...options, signal: controller.signal });
      return res;
    } catch (e) {
      if (e.name === "AbortError") {
        throw new Error("请求超时，请检查网络连接");
      }
      throw e;
    } finally {
      clearTimeout(timeoutId);
    }
  },

  async init() {
    await AppState.init();
  },

  async chatStream(message, {
    sessionId = "default",
    userId = AppState.currentUserId,
    capability = "chat",
    knowledgeBases = [],
    imageBase64 = "",
    fileContent = "",
    fileName = "",
    courseId = AppState.currentCourseId,
    llmModel = "",
    reasoningModel = "",
    visionModel = "",
    embeddingModel = "",
    onChunk,
    onDone,
    onError,
    onSources,
    requestId,
    timeout,
  } = {}) {
    const controller = new AbortController();
    const reqId = requestId || `chat_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    this._activeRequests.set(reqId, controller);

    const timeoutMs = timeout || DEFAULT_STREAM_TIMEOUT;
    let timedOut = false;
    const timeoutId = setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, timeoutMs);

    try {
      const res = await fetch(`${getApiBase()}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({
          message,
          session_id: sessionId,
          user_id: userId,
          capability,
          knowledge_bases: knowledgeBases,
          image_base64: imageBase64,
          file_content: fileContent,
          file_name: fileName,
          course_id: courseId,
          llm_model: llmModel,
          reasoning_model: reasoningModel,
          vision_model: visionModel,
          embedding_model: embeddingModel,
        }),
      });

      if (!res.ok) {
        if (onError) onError(`HTTP ${res.status}`);
        return;
      }

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
            if (event.type === "content" && onChunk) onChunk(event.text);
            if (event.type === "sources" && onSources) onSources(event.sources);
            if (event.type === "result" && onDone) onDone(event);
            if (event.type === "error" && onError) onError(event.message);
            if (event.type === "done" && onDone) onDone(event);
          } catch (e) { console.warn("SSE parse error:", e); }
        }
      }
    } catch (err) {
      if (err.name === "AbortError") {
        if (timedOut && onError) onError("请求超时");
        // 用户主动取消时不再触发 onError
        return;
      }
      if (onError) onError(err.message);
    } finally {
      clearTimeout(timeoutId);
      this._activeRequests.delete(reqId);
    }
  },

  async chatSync(message, {
    sessionId = "default",
    userId = AppState.currentUserId,
    capability = "chat",
    courseId = AppState.currentCourseId,
    llmModel = "",
    reasoningModel = "",
    visionModel = "",
    embeddingModel = "",
  } = {}) {
    return _fetchJson(`${getApiBase()}/api/chat/sync`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        session_id: sessionId,
        user_id: userId,
        capability,
        course_id: courseId,
        llm_model: llmModel,
        reasoning_model: reasoningModel,
        vision_model: visionModel,
        embedding_model: embeddingModel,
      }),
    });
  },

  async getCourses() {
    return _fetchJson(`${getApiBase()}/api/courses`);
  },

  async getProfile(userId = AppState.currentUserId) {
    return _fetchJson(`${getApiBase()}/api/profile/${userId}`);
  },

  async updateProfile(userId, updates) {
    return _fetchJson(`${getApiBase()}/api/profile/${userId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ updates }),
    });
  },

  async generateResourceStream(topic, resourceType = "lecture", {
    userId = AppState.currentUserId,
    courseId = AppState.currentCourseId,
    onChunk,
    onDone,
    onThinking,
    onStage,
    onProgress,
    onAgentStart,
    onAgentEnd,
    onError,
    requestId,
    timeout,
  } = {}) {
    const controller = new AbortController();
    const reqId = requestId || `gen_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    this._activeRequests.set(reqId, controller);

    const timeoutMs = timeout || DEFAULT_STREAM_TIMEOUT;
    let timedOut = false;
    const timeoutId = setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, timeoutMs);

    try {
      const res = await fetch(`${getApiBase()}/api/resources/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({ topic, resource_type: resourceType, user_id: userId, course_id: courseId }),
      });

      if (!res.ok) {
        console.error("Resource generation failed:", res.status);
        if (onError) onError(`HTTP ${res.status}`);
        return;
      }

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
            if (event.type === "content" && onChunk) onChunk(event.text);
            if (event.type === "thinking" && onThinking) onThinking(event.text);
            if ((event.type === "stage_start" || event.type === "stage_end") && onStage) onStage(event);
            if (event.type === "progress" && onProgress) onProgress(event);
            if (event.type === "agent_start" && onAgentStart) onAgentStart(event);
            if (event.type === "agent_end" && onAgentEnd) onAgentEnd(event);
            if (event.type === "result" && onDone) onDone(event);
            if (event.type === "done" && onDone) onDone(event);
          } catch (e) { console.warn("SSE parse error:", e); }
        }
      }
    } catch (err) {
      if (err.name === "AbortError") {
        if (timedOut && onError) onError("请求超时");
        // 用户主动取消不报错
        return;
      }
      if (onError) onError(err.message);
      else throw err;
    } finally {
      clearTimeout(timeoutId);
      this._activeRequests.delete(reqId);
    }
  },

  async planResources(message, {
    userId = AppState.currentUserId,
    sessionId = "default",
    courseId = AppState.currentCourseId,
  } = {}) {
    return _fetchJson(`${getApiBase()}/api/resources/plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, user_id: userId, session_id: sessionId, course_id: courseId }),
    });
  },

  async listResources(userId = AppState.currentUserId, type = "all", courseId = AppState.currentCourseId) {
    const params = new URLSearchParams({ type });
    if (courseId) params.set("course_id", courseId);
    return _fetchJson(`${getApiBase()}/api/resources/list/${userId}?${params.toString()}`);
  },

  async getResourceDetail(resourceId, userId = AppState.currentUserId) {
    return _fetchJson(`${getApiBase()}/api/resources/detail/${userId}/${resourceId}`);
  },

  async deleteResource(resourceId, userId = AppState.currentUserId) {
    return _fetchJson(`${getApiBase()}/api/resources/${userId}/${resourceId}`, { method: "DELETE" });
  },

  async rateResource(userId, resourceId, rating) {
    return _fetchJson(`${getApiBase()}/api/resources/rate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, resource_id: resourceId, rating }),
    });
  },

  async recordResourceEvent(resourceId, eventType, payload = {}, {
    userId = AppState.currentUserId,
    courseId = AppState.currentCourseId,
    sourcePage = "",
  } = {}) {
    return _fetchJson(`${getApiBase()}/api/evaluation/resource-event`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId,
        resource_id: resourceId,
        event_type: eventType,
        course_id: courseId,
        source_page: sourcePage,
        payload,
      }),
    }).catch(() => ({}));
  },

  async planPath(userId = AppState.currentUserId, courseId = AppState.currentCourseId) {
    return _fetchJson(`${getApiBase()}/api/path/plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, course_id: courseId }),
    });
  },

  async adjustPath(reason = "用户手动重新生成", userId = AppState.currentUserId, courseId = AppState.currentCourseId) {
    return _fetchJson(`${getApiBase()}/api/path/adjust`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, course_id: courseId, reason }),
    });
  },

  async getGraph(courseId = AppState.currentCourseId) {
    return _fetchJson(`${getApiBase()}/api/path/graph/${courseId}`);
  },

  async submitQuiz(quizResults, {
    userId = AppState.currentUserId,
    courseId = AppState.currentCourseId,
    sessionId = "default",
  } = {}) {
    return _fetchJson(`${getApiBase()}/api/evaluation/submit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, quiz_results: quizResults, course_id: courseId, session_id: sessionId }),
    });
  },

  async getMastery(userId = AppState.currentUserId) {
    return _fetchJson(`${getApiBase()}/api/evaluation/mastery/${userId}`);
  },

  async diagnose(message, userId = AppState.currentUserId) {
    return _fetchJson(`${getApiBase()}/api/evaluation/diagnose`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, message }),
    });
  },

  async getSessions(userId = AppState.currentUserId) {
    return _fetchJson(`${getApiBase()}/api/chat/sessions/${userId}`);
  },

  async getSessionHistory(sessionId, userId = AppState.currentUserId) {
    return _fetchJson(`${getApiBase()}/api/chat/history/${sessionId}?user_id=${encodeURIComponent(userId)}`);
  },

  async deleteSession(sessionId, userId = AppState.currentUserId) {
    return _fetchJson(`${getApiBase()}/api/chat/session/${sessionId}?user_id=${encodeURIComponent(userId)}`, {
      method: "DELETE",
    });
  },

  async getLearningPathTimeline(userId = AppState.currentUserId, courseId = AppState.currentCourseId) {
    return _fetchJson(`${getApiBase()}/api/learning-path/timeline/${encodeURIComponent(userId)}?course_id=${encodeURIComponent(courseId)}`);
  },

  async getLearningPathGraph(userId = AppState.currentUserId, courseId = AppState.currentCourseId) {
    return _fetchJson(`${getApiBase()}/api/learning-path/graph/${encodeURIComponent(userId)}?course_id=${encodeURIComponent(courseId)}`);
  },

  async getLearningPathRecommendations(userId = AppState.currentUserId, courseId = AppState.currentCourseId) {
    return _fetchJson(`${getApiBase()}/api/learning-path/recommendations/${encodeURIComponent(userId)}?course_id=${encodeURIComponent(courseId)}`);
  },

  async getSpacedRepetition(userId = AppState.currentUserId) {
    return _fetchJson(`${getApiBase()}/api/learning-path/spaced-repetition/${encodeURIComponent(userId)}`);
  },

  async getStats() {
    return _fetchJson(`${getApiBase()}/api/stats`);
  },
};

window.AppState = AppState;
window.Api = Api;
