// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

// export interface Model {
//     model_type: string;
//     token_limit: number;
//     temperature: number;
//     display_name: string;
//     version: number;
//     vendor: string;
//     platform: string;
//     min_temperature: number;
//     max_temperature: number;
//     min_token_limit: number;
//     max_token_limit: number;
//     data_insights_input_token: number;
//     data_insights_output_token: number;
// }

export interface InferenceSettings {
  model: string;
  temperature: number;
  token_limit: number;
  input_token?: number;
  output_token?: number;
  tags?: null;
  maxTokenLimit?: number;
  minTokenLimit?: number;
  maxTemperatureLimit?: number;
  minTemperatureLimit?: number;
}

export interface Feedback {
  comment: string;
  rating: number;
  is_thumbs_up: boolean;
}

export interface SuccessResponse {
  message: string;
}

export interface PromptsResponse {
  prompt_text: string;
  tags: [];
  tag_category: string;
  author: string;
}

export interface StreamChatProps {
  user_id: string;
  conversation_id: string;
  use_case: string;
  query: string;
  tags: string[];
  settings: InferenceSettings;
}
