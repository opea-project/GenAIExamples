type SpeechRecognitionErrorEvent = Event & {
  error:
    | "no-speech"
    | "audio-capture"
    | "not-allowed"
    | "network"
    | "aborted"
    | "service-not-allowed"
    | "bad-grammar"
    | "language-not-supported";
  message?: string; // Some browsers may provide an additional error message
};

type SpeechRecognitionEvent = Event & {
  results: {
    [index: number]: {
      [index: number]: {
        transcript: string;
        confidence: number;
      };
      isFinal: boolean;
    };
  };
};
