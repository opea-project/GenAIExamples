export interface ErrorResponse {
  response?: {
    data?: {
      error?: {
        message?: string;
      };
    };
  };
  message: string;
}
