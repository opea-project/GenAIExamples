export interface Benchmark {
  generator: string;
  postprocessor: string;
  retriever: string;
}
export interface IMessage {
  author: string;
  content: string;
  benchmark?: Benchmark | undefined;
}
export interface ConfigType {
  top_n: number;
  temperature: number;
  top_p: number;
  top_k: number;
  repetition_penalty: number;
  max_tokens: number;
  stream: boolean;
}
