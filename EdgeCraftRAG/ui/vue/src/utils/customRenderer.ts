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

const isInternalAnchorLink = (href?: string | null) => {
  return !!href && href.startsWith("#") && href.length > 1;
};

const getAnchorTargetId = (href: string) => {
  return href.slice(1);
};

const getAnchorScope = (anchorLink: HTMLAnchorElement) => {
  return anchorLink.closest("[id='message-container']");
};

const queryAnchorTargetInScope = (scope: Element | Document, targetId: string) => {
  const decodedTargetId = decodeURIComponent(targetId);

  if (scope instanceof Document) {
    return scope.getElementById(targetId) || scope.getElementById(decodedTargetId);
  }

  if (typeof CSS !== "undefined" && typeof CSS.escape === "function") {
    return scope.querySelector(`#${CSS.escape(targetId)}`) || scope.querySelector(`#${CSS.escape(decodedTargetId)}`);
  }

  return null;
};

const getAnchorScrollTarget = (targetElement: HTMLElement) => {
  if (
    targetElement.tagName.toLowerCase() === "a" &&
    !targetElement.textContent?.trim() &&
    targetElement.childElementCount === 0
  ) {
    return (targetElement.nextElementSibling as HTMLElement | null) || targetElement;
  }

  return targetElement;
};

const resolveAnchorTarget = (anchorLink: HTMLAnchorElement, targetId: string) => {
  const decodedTargetId = decodeURIComponent(targetId);
  const anchorScope = getAnchorScope(anchorLink);

  if (anchorScope) {
    const scopedTarget = queryAnchorTargetInScope(anchorScope, targetId);
    if (scopedTarget instanceof HTMLElement) {
      return scopedTarget;
    }
  }

  return document.getElementById(targetId) || document.getElementById(decodedTargetId);
};

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
      const anchorLink = target.closest("a[data-anchor-target]") as HTMLAnchorElement | null;

      if (copyBtn) {
        e.preventDefault();
        this.handleCopyClick(copyBtn as HTMLElement);
        return;
      }

      if (anchorLink) {
        e.preventDefault();
        this.handleAnchorClick(anchorLink);
      }
    });
  }

  private handleAnchorClick(anchorLink: HTMLAnchorElement) {
    const targetId = anchorLink.getAttribute("data-anchor-target");
    if (!targetId) return;

    const targetElement = resolveAnchorTarget(anchorLink, targetId);
    if (!targetElement) return;

    const scrollTarget = getAnchorScrollTarget(targetElement);

    scrollTarget.scrollIntoView({
      behavior: "smooth",
      block: "start",
      inline: "nearest",
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
    if (isInternalAnchorLink(href)) {
      const targetId = getAnchorTargetId(href);

      return `<a href="${href}" data-anchor-target="${targetId}" ${title ? `title="${title}"` : ""}>${text}</a>`;
    }

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
