// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

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

interface User {
	id?: string;
	email: string;
	password?: string;
	token?: string;
	[key: string]: any;
}

type AuthResponse = Result<User>;

interface AuthAdapter {
	login(props: { email: string; password: string }): Promise<AuthResponse>;
	signup(props: { email: string; password: string; password_confirm: string }): Promise<AuthResponse>;
	validate_session(props: { token: string }): Promise<AuthResponse>;
	logout(props: { token: string; email: string }): Promise<Result<void>>;
	forgotPassword(props: { email: string; password: string }): Promise<Result<void>>;
}

interface ChatAdapter {
	modelList(props: {}): Promise<Result<void>>;
	txt2img(props: {}): Promise<Result<void>>;
}

interface ChatMessage {
	role: string;
	content: string;
}

interface ChatMessageType {
	model: string;
	knowledge: string;
	temperature: string;
	max_new_tokens: string;
	topk: string;
}
