const AppState = {
  apiBase:
    window.localStorage.getItem("ZHIXUE_API_BASE") ||
    `${window.location.protocol}//${window.location.hostname}:8001`,
  currentUserId: window.localStorage.getItem("ZHIXUE_USER_ID") || "demo_student",
  currentCourseId: window.localStorage.getItem("ZHIXUE_COURSE_ID") || "python_programming",
  appName: "智学助手",
  maxUploadSizeMb: 10,

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

const Api = {
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
    onChunk,
    onDone,
    onError,
    onSources,
  } = {}) {
    try {
      const res = await fetch(`${getApiBase()}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
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
        }),
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
            if (event.type === "content" && onChunk) onChunk(event.text);
            if (event.type === "sources" && onSources) onSources(event.sources);
            if (event.type === "result" && onDone) onDone(event);
            if (event.type === "error" && onError) onError(event.message);
            if (event.type === "done" && onDone) onDone(event);
          } catch (e) {}
        }
      }
    } catch (err) {
      if (onError) onError(err.message);
    }
  },

  async chatSync(message, {
    sessionId = "default",
    userId = AppState.currentUserId,
    capability = "chat",
    courseId = AppState.currentCourseId,
  } = {}) {
    const res = await fetch(`${getApiBase()}/api/chat/sync`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId, user_id: userId, capability, course_id: courseId }),
    });
    return res.json();
  },

  async getCourses() {
    const res = await fetch(`${getApiBase()}/api/courses`);
    return res.json();
  },

  async getProfile(userId = AppState.currentUserId) {
    const res = await fetch(`${getApiBase()}/api/profile/${userId}`);
    return res.json();
  },

  async updateProfile(userId, updates) {
    const res = await fetch(`${getApiBase()}/api/profile/${userId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updates),
    });
    return res.json();
  },

  async generateResourceStream(topic, resourceType = "lecture", {
    userId = AppState.currentUserId,
    courseId = AppState.currentCourseId,
    onChunk,
    onDone,
    onThinking,
  } = {}) {
    const res = await fetch(`${getApiBase()}/api/resources/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic, resource_type: resourceType, user_id: userId, course_id: courseId }),
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
          if (event.type === "content" && onChunk) onChunk(event.text);
          if (event.type === "thinking" && onThinking) onThinking(event.text);
          if (event.type === "result" && onDone) onDone(event);
          if (event.type === "done" && onDone) onDone(event);
        } catch (e) {}
      }
    }
  },

  async planResources(message, {
    userId = AppState.currentUserId,
    sessionId = "default",
    courseId = AppState.currentCourseId,
  } = {}) {
    const res = await fetch(`${getApiBase()}/api/resources/plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, user_id: userId, session_id: sessionId, course_id: courseId }),
    });
    return res.json();
  },

  async listResources(userId = AppState.currentUserId, type = "all", courseId = AppState.currentCourseId) {
    const params = new URLSearchParams({ type });
    if (courseId) params.set("course_id", courseId);
    const res = await fetch(`${getApiBase()}/api/resources/list/${userId}?${params.toString()}`);
    return res.json();
  },

  async getResourceDetail(resourceId, userId = AppState.currentUserId) {
    const res = await fetch(`${getApiBase()}/api/resources/detail/${userId}/${resourceId}`);
    return res.json();
  },

  async deleteResource(resourceId, userId = AppState.currentUserId) {
    const res = await fetch(`${getApiBase()}/api/resources/${userId}/${resourceId}`, { method: "DELETE" });
    return res.json();
  },

  async recordResourceEvent(resourceId, eventType, payload = {}, {
    userId = AppState.currentUserId,
    courseId = AppState.currentCourseId,
    sourcePage = "",
  } = {}) {
    const res = await fetch(`${getApiBase()}/api/evaluation/resource-event`, {
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
    });
    return res.json();
  },

  async planPath(userId = AppState.currentUserId, courseId = AppState.currentCourseId) {
    const res = await fetch(`${getApiBase()}/api/path/plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, course_id: courseId }),
    });
    return res.json();
  },

  async adjustPath(reason = "用户手动重新生成", userId = AppState.currentUserId, courseId = AppState.currentCourseId) {
    const res = await fetch(`${getApiBase()}/api/path/adjust`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, course_id: courseId, reason }),
    });
    return res.json();
  },

  async getGraph(courseId = AppState.currentCourseId) {
    const res = await fetch(`${getApiBase()}/api/path/graph/${courseId}`);
    return res.json();
  },

  async submitQuiz(quizResults, {
    userId = AppState.currentUserId,
    courseId = AppState.currentCourseId,
    sessionId = "default",
  } = {}) {
    const res = await fetch(`${getApiBase()}/api/evaluation/submit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, quiz_results: quizResults, course_id: courseId, session_id: sessionId }),
    });
    return res.json();
  },

  async getMastery(userId = AppState.currentUserId) {
    const res = await fetch(`${getApiBase()}/api/evaluation/mastery/${userId}`);
    return res.json();
  },

  async diagnose(message, userId = AppState.currentUserId) {
    const res = await fetch(`${getApiBase()}/api/evaluation/diagnose`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, message }),
    });
    return res.json();
  },

  async getSessions(userId = AppState.currentUserId) {
    const res = await fetch(`${getApiBase()}/api/chat/sessions/${userId}`);
    return res.json();
  },

  async getSessionHistory(sessionId, userId = AppState.currentUserId) {
    const res = await fetch(`${getApiBase()}/api/chat/history/${sessionId}?user_id=${encodeURIComponent(userId)}`);
    return res.json();
  },

  async deleteSession(sessionId, userId = AppState.currentUserId) {
    const res = await fetch(`${getApiBase()}/api/chat/session/${sessionId}?user_id=${encodeURIComponent(userId)}`, {
      method: "DELETE",
    });
    return res.json();
  },

  async getStats() {
    const res = await fetch(`${getApiBase()}/api/stats`);
    return res.json();
  },
};

window.AppState = AppState;
window.Api = Api;
