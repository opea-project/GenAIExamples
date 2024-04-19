export function scrollToBottom(scrollToDiv: HTMLElement) {
	if (scrollToDiv) {
		setTimeout(
			() =>
				scrollToDiv.scroll({
					behavior: "auto",
					top: scrollToDiv.scrollHeight,
				}),
			300,
		);
	}
}
