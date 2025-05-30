// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { marked } from "marked";
import hljs from "highlight.js";
import { formatCapitalize } from "./common";
import ClipboardJS from "clipboard";
import { message } from "ant-design-vue";

interface CodeRenderParams {
  text: string;
  lang?: string;
}

class ClipboardManager {
  private clipboard: ClipboardJS | null = null;
  private observer: MutationObserver | null = null;

  constructor() {
    this.autoInit();
  }

  private autoInit() {
    if (typeof document === "undefined") return;
    const init = () => {
      this.init(".copy-btn");
      this.setupMutationObserver();
    };

    if (document.readyState === "complete") {
      init();
    } else {
      document.addEventListener("DOMContentLoaded", init);
    }
  }

  private init(selector: string) {
    this.destroy();

    this.clipboard = new ClipboardJS(selector, { container: document.body });

    this.clipboard.on("success", (e) => this.handleSuccess(e));
    this.clipboard.on("error", (e) => this.handleError(e));
  }

  private setupMutationObserver() {
    this.observer = new MutationObserver((mutations) => {
      const hasNewButtons = mutations.some((mutation) =>
        Array.from(mutation.addedNodes).some(
          (node) => node instanceof HTMLElement && (node.matches(".copy-btn") || node.querySelector(".copy-btn")),
        ),
      );
      if (hasNewButtons) this.init(".copy-btn");
    });

    this.observer.observe(document.body, {
      childList: true,
      subtree: true,
    });
  }

  destroy() {
    this.clipboard?.destroy();
    this.observer?.disconnect();
    this.clipboard = null;
    this.observer = null;
  }

  private handleSuccess(e: ClipboardJS.Event) {
    e.clearSelection();
    message.success("Copy Successful !");
    const button = e.trigger as HTMLElement;
    const copyIcon = button.querySelector(".copy-icon") as HTMLElement;
    const successIcon = button.querySelector(".success-icon") as HTMLElement;

    copyIcon.style.display = "none";
    successIcon.style.display = "block";

    let timeout = null;
    if (timeout) clearTimeout(timeout);

    timeout = setTimeout(() => {
      copyIcon.style.display = "block";
      successIcon.style.display = "none";
    }, 2000);
  }

  private handleError(e: ClipboardJS.Event) {
    message.error("Copy Failure !");
  }
}

export const clipboardManager = new ClipboardManager();

const createCustomRenderer = () => {
  const renderer = new marked.Renderer();

  renderer.link = ({ href, title, text }) => {
    return `<a href="${href}" target="_blank" rel="noopener noreferrer" ${title ? `title="${title}"` : ""}>${text}</a>`;
  };

  renderer.code = ({ text, lang }: CodeRenderParams) => {
    const language = hljs.getLanguage(lang || "") ? lang : "plaintext";
    const codeTitle = formatCapitalize(language || "Code");
    const codeHtml = hljs.highlight(text, {
      language: language || "plaintext",
    }).value;
    const uniqueId = `code-${Date.now()}-${Math.random().toString(16).slice(2)}`;

    return `
      <div  class="intel-highlighter">
        <div class="header-wrap">
          <span class="code-title">${codeTitle}</span>
          <span class="copy-btn" data-clipboard-target="#${uniqueId}">
            <i class="icon-intel iconfont icon-copy copy-icon" ></i>
            <i class="icon-intel iconfont icon-copy-success success-icon" ></i>
          </span>
        </div>
        <pre class="content-wrap" id="${uniqueId}"><div>${codeHtml}</div></pre>
      </div>
    `;
  };

  return renderer;
};

const CustomRenderer = createCustomRenderer();
export default CustomRenderer;
