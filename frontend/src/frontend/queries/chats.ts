'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { Chat, Page } from '../types';
import { useState } from 'react';
import { ChatParams } from '../store';

/**
 * Custom hook to post chat data to the backend.
 *
 * This hook uses the `useMutation` hook from React Query to handle the mutation.
 * It sends a POST request to the backend API to create a new chat.
 *
 * @returns {MutationResult<Chat, unknown, FormData, unknown>} The mutation result object.
 *
 * @example
 * const { mutate, isLoading, error } = usePostChat();
 *
 * const handleSubmit = (formData: FormData) => {
 *   mutate(formData);
 * };
 */
export const usePostChat = () => {
  return useMutation({
    mutationFn: async (formData: FormData) => {
      const response = await axios.post<Chat>(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/chats`,
        formData,
        {
          withCredentials: true,
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      return response.data;
    },
  });
};

/**
 * Fetches a paginated list of chats from the backend API.
 *
 * @param size - The number of chats to retrieve per page.
 * @param page - The page number to retrieve.
 * @returns A promise that resolves to a Page object containing Chat objects.
 */
export const getChats = async (size: number, page: number) => {
  const response = await axios.get<Page<Chat>>(
    `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/chats`,
    {
      withCredentials: true,
      params: {
        size,
        page,
      },
    }
  );
  return response.data;
};

/**
 * Custom hook to fetch chat data by ID using React Query.
 *
 * @param {string} id - The ID of the chat to fetch.
 * @returns {UseQueryResult<Chat, Error>} The result of the query, including the chat data or an error.
 *
 * @example
 * const { data, error, isLoading } = useGetChat('chat-id');
 *
 * @remarks
 * This hook uses Axios to make a GET request to the backend API.
 * The backend URL is retrieved from the environment variable `NEXT_PUBLIC_BACKEND_URL`.
 * The request includes credentials (cookies) for authentication.
 */
export const useGetChat = (id: string) => {
  return useQuery({
    queryKey: ['chats', id],
    queryFn: async () => {
      const response = await axios.get<Chat>(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/chats/${id}`,
        {
          withCredentials: true,
        }
      );
      return response.data;
    },
    enabled: !!id, // Only fetch if id is provided
  });
};

/**
 * Custom hook to delete a chat by its ID.
 *
 * This hook uses the `useMutation` hook from React Query to perform a DELETE request
 * to the backend API to delete a chat. The backend URL is retrieved from the environment
 * variable `NEXT_PUBLIC_BACKEND_URL`.
 *
 * @param {string} id - The ID of the chat to be deleted.
 * @returns {MutationResult} - The result of the mutation, including status and data.
 */
export const useDeleteChat = (id: string) => {
  return useMutation({
    mutationFn: async () => {
      const response = await axios.delete(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/chats/${id}`,
        {
          withCredentials: true,
        }
      );
      return response.data;
    },
  });
};

/**
 * Custom hook to update a chat by its ID.
 *
 * This hook uses the `useMutation` hook from React Query to handle the mutation.
 * It sends a PUT request to the backend API to update the chat with the provided ID.
 *
 * @param {string} id - The ID of the chat to be updated.
 * @returns {MutationResult} - The result of the mutation, including status and data.
 *
 * @example
 * const { mutate, isLoading, error } = useUpdateChat(chatId);
 *
 * const handleUpdate = (formData) => {
 *   mutate(formData);
 * };
 */
export const useUpdateChat = (id: string) => {
  return useMutation({
    mutationFn: async (formData: FormData) => {
      const response = await axios.put(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/chats/${id}`,
        formData,
        {
          withCredentials: true,
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      return response.data;
    },
  });
};

/**
 * Custom hook to handle file upload for a specific chat.
 *
 * @param id - The unique identifier of the chat.
 * @returns A mutation object that can be used to trigger the file upload.
 *
 * The mutation function accepts a FormData object containing the file to be uploaded.
 * It sends a POST request to the backend API to upload the file to the specified chat.
 *
 * The backend URL is retrieved from the environment variable `NEXT_PUBLIC_BACKEND_URL`.
 * The request includes credentials (cookies) for authentication.
 *
 * @example
 * ```typescript
 * const { mutate: uploadFile } = usePostFile(chatId);
 *
 * const handleFileUpload = (file: File) => {
 *   const formData = new FormData();
 *   formData.append('file', file);
 *   uploadFile(formData);
 * };
 * ```
 */
export const usePostFile = (id: string) => {
  return useMutation({
    mutationFn: async (formData: FormData) => {
      const response = await axios.post<Chat>(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/chats/${id}/upload`,
        formData,
        {
          withCredentials: true,
        }
      );
      return response.data;
    },
  });
};

/**
 * Custom hook to delete a file associated with a chat.
 *
 * @param {string} chatId - The ID of the chat from which the file will be deleted.
 * @returns {UseMutationResult} - The result of the mutation, including status and data.
 *
 * @example
 * const { mutate: deleteFile } = useDeleteFile(chatId);
 * deleteFile(fileId);
 */
export const useDeleteFile = (chatId: string) => {
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await axios.delete<Chat>(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/chats/${chatId}/delete/${id}`,
        {
          withCredentials: true,
        }
      );
      return response.data;
    },
  });
};

/**
 * Custom hook to handle streaming chat messages for a specific chat session.
 *
 * @param chatId - The unique identifier of the chat session.
 * @returns A tuple containing:
 * - `response`: The accumulated response text from the chat stream.
 * - `isStreaming`: A boolean indicating whether the chat stream is currently active.
 * - `sendMessageStream`: A mutation object to send a message and handle the streaming response.
 *
 * The `sendMessageStream` mutation sends a message to the backend and processes the server-sent events (SSE)
 * to update the `response` state with the streamed data. It also manages the streaming state and refreshes
 * the chat data upon successful completion.
 *
 * The server is expected to send data in SSE format, where each message is prefixed with `data: ` and ends
 * with a double newline (`\n\n`). The hook handles parsing and appending the streamed data to the response.
 *
 * Example usage:
 * ```typescript
 * const [response, isStreaming, sendMessageStream] = useChatStream(chatId);
 *
 * const handleSendMessage = () => {
 *   sendMessageStream.mutate('Hello, world!');
 * };
 * ```
 */
export const useChatStream = (chatId: string) => {
  const queryClient = useQueryClient();

  const [response, setResponse] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);

  const sendMessageStream = useMutation({
    mutationFn: async ({
      text,
      query_params,
    }: {
      text: string;
      query_params?: ChatParams;
    }) => {
      setResponse('');
      setIsStreaming(true);
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/chats/${chatId}/chat/stream`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: text, params: query_params }),
            credentials: 'include',
          }
        );
        if (!response.ok) throw new Error('Network response was not ok');
        if (!response.body) throw new Error('Response body is null');

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value);

          // Process SSE format (data: {...}\n\n)
          const lines = buffer.split('\n');
          buffer = lines.pop() || ''; // Keep incomplete line in buffer

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const jsonStr = line.substring(6).trim();
                if (jsonStr === '') continue;

                const data = JSON.parse(jsonStr);
                if (data.status === 'done') {
                  return; // Stream completed
                } else if (data.value) {
                  setResponse(prev => {
                    console.log(prev);
                    return prev + data.value;
                  });
                }
              } catch (error) {
                console.error('Error parsing SSE data:', error);
              }
            }
          }
        }
      } catch (error) {
        console.error('Error:', error);
      } finally {
        setIsStreaming(false);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat', chatId] }); // Refresh chat data
    },
  });

  return [response, isStreaming, sendMessageStream] as const;
};

/**
 * Fetches a list of chats filtered by the given title.
 *
 * This function sends a GET request to the backend API to retrieve chats
 * that match the specified title. It includes credentials in the request
 * and expects a JSON response.
 *
 * @param title - The title to filter chats by.
 * @returns A promise that resolves to an array of chats if the request is successful,
 *          or an empty array if the response status is not 200.
 * @throws An error if the request fails.
 */
export const getChatsByTitle = async (title: string) => {
  try {
    const res = await axios.get<Chat[]>(
      `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/chats/search`,
      {
        withCredentials: true,
        params: {
          title,
        },
        headers: {
          Accept: 'application/json',
        },
      }
    );
    if (res.status === 200) {
      return res.data;
    }
    return [];
  } catch (error) {
    console.error('Error fetching chats by title:', error);
    throw new Error('Failed to fetch chats');
  }
};
