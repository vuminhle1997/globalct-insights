import { Favourite } from './favourites';
import { File } from './files';
import { Message } from './message';

export type LLMMessage = {
  id?: string;
  response: string;
  sources: any[];
  source_nodes: any[];
  is_dummy_stream: boolean;
  metadata: any;
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
  model_provider: 'GOOGLE_GENAI' | 'OPENAI' | 'AZURE_OPENAI' | 'HUGGINGFACE' | 'CUSTOM' | 'IONOS' | 'OLLAMA';
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
