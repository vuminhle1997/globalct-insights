export interface LLMModel {
  name: string;
  description: string;
  llm_provider: string;
  llm_model: string;
  type: 'llm' | 'embedding';
}