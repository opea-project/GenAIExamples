// See: https://kit.svelte.dev/docs/types#app
// import { Result} from "neverthrow";

declare namespace App {
	interface Locals {
		user?: User;
	}
	// interface PageData { }
	// interface PageError {}
	// interface Platform {}
}

interface ChatMessage {
	role: string;
	content: string;
}
