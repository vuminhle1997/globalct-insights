import { Favourite } from './favourites';
import { File } from './files';
import { Message } from './message';

export type LLMMessage = {
  id?: string;
  response: string;
  sources: Record<string, unknown>[]; // TODO: check if this is correct
  source_nodes: Record<string, unknown>[]; // TODO: check if this is correct
  metadata: Record<string, unknown>; // TODO: check if this is correct
};

export type LLMAgentResponse = {
  response: LLMMessage;
};

export type Chat = {
  id: string;
  title: string;
  description: string;
  context: string;
  temperature: number;
  model: string;
  model_provider: 'GOOGLE_GENAI' | 'OPENAI' | 'CUSTOM' | 'IONOS' | 'OLLAMA';
  created_at: string;
  updated_at: string;
  last_interacted_at: string;
  files: File[];
  user_id: string;
  messages: Message[];
  message?: LLMAgentResponse;
  favourite?: Favourite;
  avatar_blob?: string;
  avatar_path: string;
};
