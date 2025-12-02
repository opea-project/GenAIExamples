// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { marked } from "marked";
import hljs from "highlight.js";
import { formatCapitalize } from "./common";
import { useClipboard } from "./clipboard";

interface CodeRenderParams {
  text: string;
  lang?: string;
}

class ClipboardManager {
  private clipboard;

  constructor() {
    this.clipboard = useClipboard();
    this.init();
  }

  private init() {
    document.addEventListener("click", (e) => {
      const target = e.target as HTMLElement;
      const copyBtn = target.closest(".copy-btn");

      if (copyBtn) {
        e.preventDefault();
        this.handleCopyClick(copyBtn as HTMLElement);
      }
    });
  }

  private async handleCopyClick(button: HTMLElement) {
    const targetId = button.getAttribute("data-clipboard-target");
    if (!targetId) return;

    const targetElement = document.querySelector(targetId);
    if (!targetElement) return;

    const textToCopy = targetElement.textContent || "";
    const success = await this.clipboard.copy(textToCopy);

    if (success) {
      this.showSuccessIcon(button);
    }
  }

  private showSuccessIcon(button: HTMLElement) {
    const copyIcon = button.querySelector(".copy-icon") as HTMLElement;
    const successIcon = button.querySelector(".success-icon") as HTMLElement;

    if (copyIcon && successIcon) {
      copyIcon.style.display = "none";
      successIcon.style.display = "block";

      setTimeout(() => {
        copyIcon.style.display = "block";
        successIcon.style.display = "none";
      }, 2000);
    }
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
      <div class="intel-highlighter">
        <div class="header-wrap">
          <span class="code-title">${codeTitle}</span>
          <span class="copy-btn" data-clipboard-target="#${uniqueId}">
            <i class="icon-intel iconfont icon-copy copy-icon"></i>
            <i class="icon-intel iconfont icon-copy-success success-icon" style="display: none;"></i>
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
