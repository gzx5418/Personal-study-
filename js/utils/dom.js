const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

function on(el, evt, fn, opts) {
  el?.addEventListener(evt, fn, opts);
  return () => el?.removeEventListener(evt, fn, opts);
}

function escapeHtml(str) {
  if (str == null) return "";
  return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function createElement(tag, attrs = {}, children = []) {
  const el = document.createElement(tag);
  for (const [key, val] of Object.entries(attrs)) {
    if (key === "className") el.className = val;
    else if (key === "textContent") el.textContent = val;
    else if (key.startsWith("data")) el.dataset[key.slice(4).toLowerCase()] = val;
    else el.setAttribute(key, val);
  }
  children.forEach((child) => {
    if (typeof child === "string") el.appendChild(document.createTextNode(child));
    else if (child) el.appendChild(child);
  });
  return el;
}

function showToast(message, duration = 3000) {
  let container = $(".toast-container");
  if (!container) {
    container = createElement("div", { className: "toast-container" });
    document.body.appendChild(container);
  }
  const toast = createElement("div", { className: "toast", textContent: message });
  container.appendChild(toast);
  setTimeout(() => {
    toast.classList.add("toast-exit");
    setTimeout(() => toast.remove(), 150);
  }, duration);
}

function animateValue(el, start, end, duration = 800) {
  const startTime = performance.now();
  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = Math.round(start + (end - start) * eased);
    el.textContent = current;
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

function renderMarkdown(text) {
  if (!text) return "";
  if (typeof marked !== 'undefined') {
    let processed = text;
    // 提取 mermaid 代码块，避免被 marked 解析
    const mermaidBlocks = [];
    processed = processed.replace(/```mermaid\n([\s\S]*?)```/g, (_, code) => {
      const placeholder = `__MERMAID_${mermaidBlocks.length}__`;
      mermaidBlocks.push(code.trim());
      return placeholder;
    });
    let html = marked.parse(processed);

    // 还原 mermaid 占位符
    mermaidBlocks.forEach((code, i) => {
      html = html.replace(`__MERMAID_${i}__`, `<div class="mermaid">${escapeHtml(code)}</div>`);
    });

    // 增强代码块
    html = html.replace(/<pre><code(?:\s+class="language-(\w+)")?>([\s\S]*?)<\/code><\/pre>/g, (_, lang, code) => {
      const langLabel = lang ? `<span class="code-lang">${lang}</span>` : '';
      return `<div class="code-block"><div class="code-header">${langLabel}<button class="code-copy-btn" onclick="copyCode(this)">复制</button></div><pre><code${lang ? ` class="language-${lang}"` : ''}>${code}</code></pre></div>`;
    });

    // 使用 DOMPurify 净化 HTML（替换手动正则净化）
    if (typeof DOMPurify !== 'undefined') {
      html = DOMPurify.sanitize(html, {
        ADD_TAGS: ['div', 'span', 'pre', 'code', 'h2', 'h3', 'h4', 'strong', 'em', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'ul', 'ol', 'li', 'blockquote', 'br', 'hr', 'img', 'a'],
        ADD_ATTR: ['class', 'style', 'data-processed', 'target'],
        ALLOW_DATA_ATTR: false,
      });
    } else {
      // 降级：手动净化
      html = html.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, "");
      html = html.replace(/<iframe\b[^>]*>[\s\S]*?<\/iframe>/gi, "");
      html = html.replace(/<object\b[^>]*>[\s\S]*?<\/object>/gi, "");
      html = html.replace(/<embed\b[^>]*>/gi, "");
      html = html.replace(/\s+on\w+\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)/gi, "");
      html = html.replace(/(href|src)\s*=\s*["']\s*javascript:[^"']*["']/gi, '$1="#"');
    }

    setTimeout(() => {
      document.querySelectorAll('.mermaid:not([data-processed])').forEach(el => {
        if (typeof mermaid !== 'undefined') {
          try {
            const id = 'mermaid-' + Math.random().toString(36).substr(2, 9);
            mermaid.render(id, el.textContent.trim()).then(({ svg }) => {
              el.innerHTML = svg;
              el.setAttribute('data-processed', 'true');
            }).catch(() => {});
          } catch (e) {}
        }
      });
    }, 100);
    return html;
  }
  return escapeHtml(text)
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre class="res-code"><code>$2</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/^### (.+)$/gm, '<h4>$1</h4>')
    .replace(/^## (.+)$/gm, '<h3>$1</h3>')
    .replace(/^# (.+)$/gm, '<h2>$1</h2>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');
}

function copyCode(btn) {
  const codeBlock = btn.closest('.code-block').querySelector('code');
  const text = codeBlock.textContent;
  navigator.clipboard.writeText(text).then(() => {
    btn.textContent = '已复制';
    btn.classList.add('copied');
    setTimeout(() => {
      btn.textContent = '复制';
      btn.classList.remove('copied');
    }, 2000);
  }).catch(() => {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    btn.textContent = '已复制';
    btn.classList.add('copied');
    setTimeout(() => {
      btn.textContent = '复制';
      btn.classList.remove('copied');
    }, 2000);
  });
}
