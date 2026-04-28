'use client';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { LLMModel } from '../types/models';

export const useGetModels = () => {
  return useQuery({
    queryKey: ['models'],
    queryFn: async () => {
      const response = await axios.get<{ models: LLMModel[] }>(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/models`,
        {
          withCredentials: true,
        }
      );
      return response.data.models;
    },
  });
};