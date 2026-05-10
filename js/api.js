const API_BASE = "http://localhost:8001";
let currentCourseId = "python_programming";

const Api = {
  // 流式聊天（SSE）
  async chatStream(message, { sessionId = "default", userId = "default", capability = "chat", knowledgeBases = [], imageBase64 = "", fileContent = "", fileName = "", onChunk, onDone, onError, onSources } = {}) {
    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
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

  // 同步聊天
  async chatSync(message, { sessionId = "default", userId = "default", capability = "chat" } = {}) {
    const res = await fetch(`${API_BASE}/api/chat/sync`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId, user_id: userId, capability }),
    });
    return res.json();
  },

  // 获取画像
  async getProfile(userId = "default") {
    const res = await fetch(`${API_BASE}/api/profile/${userId}`);
    return res.json();
  },

  // 更新画像
  async updateProfile(userId, updates) {
    const res = await fetch(`${API_BASE}/api/profile/${userId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updates),
    });
    return res.json();
  },

  // 生成资源（流式）
  async generateResourceStream(topic, resourceType = "lecture", { userId = "default", onChunk, onDone, onThinking } = {}) {
    const res = await fetch(`${API_BASE}/api/resources/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic, resource_type: resourceType, user_id: userId }),
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

  // 获取学习路径
  async planPath(userId = "default", courseId = null) {
    courseId = courseId || currentCourseId;
    const res = await fetch(`${API_BASE}/api/path/plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, course_id: courseId }),
    });
    return res.json();
  },

  // 获取知识图谱
  async getGraph(courseId = null) {
    courseId = courseId || currentCourseId;
    const res = await fetch(`${API_BASE}/api/path/graph/${courseId}`);
    return res.json();
  },

  // 提交练习结果
  async submitQuiz(quizResults, userId = "default") {
    const res = await fetch(`${API_BASE}/api/evaluation/submit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, quiz_results: quizResults }),
    });
    return res.json();
  },

  // 获取掌握度
  async getMastery(userId = "default") {
    const res = await fetch(`${API_BASE}/api/evaluation/mastery/${userId}`);
    return res.json();
  },

  // 诊断
  async diagnose(message, userId = "default") {
    const res = await fetch(`${API_BASE}/api/evaluation/diagnose`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, message }),
    });
    return res.json();
  },

  // 获取 Token 统计
  async getStats() {
    const res = await fetch(`${API_BASE}/api/stats`);
    return res.json();
  },

  // 获取课程列表
  async getCourses() {
    const res = await fetch(`${API_BASE}/api/courses`);
    return res.json();
  },
};
