// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

export function clickOutside(node: HTMLElement): { destroy(): void } {
	const handleClick = (event: MouseEvent) => {
		if (node && !node.contains(event.target as Node) && !event.defaultPrevented) {
			node.dispatchEvent(new CustomEvent("click_outside", { detail: node }));
		}
	};

	document.addEventListener("click", handleClick, true);

	return {
		destroy() {
			document.removeEventListener("click", handleClick, true);
		},
	};
}
