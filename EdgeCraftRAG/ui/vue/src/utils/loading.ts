// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { nextTick } from "vue";
import "@/theme/loading.less";

/**
 * Global Loading
 * @method start create loading
 * @method done remove loading
 */
export const NextLoading = {
  start: () => {
    const bodys: Element = document.body;
    const div = <HTMLElement>document.createElement("div");
    div.setAttribute("class", "loading-next");
    const htmls = `
			<div class="loading-next-box">
				<div class="loading-next-box-warp">
					<div class="loading-next-box-item"></div>
					<div class="loading-next-box-item"></div>
					<div class="loading-next-box-item"></div>
					<div class="loading-next-box-item"></div>
					<div class="loading-next-box-item"></div>
					<div class="loading-next-box-item"></div>
					<div class="loading-next-box-item"></div>
					<div class="loading-next-box-item"></div>
					<div class="loading-next-box-item"></div>
				</div>
			</div>
		`;
    div.innerHTML = htmls;
    bodys.insertBefore(div, bodys.childNodes[0]);
    window.nextLoading = true;
  },

  done: (time: number = 0) => {
    nextTick(() => {
      setTimeout(() => {
        window.nextLoading = false;
        const el = <HTMLElement>document.querySelector(".loading-next");
        el?.parentNode?.removeChild(el);
      }, time);
    });
  },
};
