'use client';

import { useMutation, useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { Page } from '../types/page';
import { Favourite } from '../types/favourites';

/**
 * Custom hook to fetch a paginated list of favourites.
 *
 * @param {number} size - The number of items per page.
 * @param {number} page - The current page number.
 * @returns {UseQueryResult<Page<Favourite>, Error>} The result of the query, including the data and status.
 *
 * @example
 * const { data, error, isLoading } = useGetFavourites(10, 1);
 *
 * @remarks
 * This hook uses the `useQuery` hook from `react-query` to fetch data from the backend.
 * The backend URL is retrieved from the environment variable `NEXT_PUBLIC_BACKEND_URL`.
 * The request includes credentials (cookies) for authentication.
 */
export const useGetFavourites = (size: number, page: number) => {
  return useQuery({
    queryKey: ['favourites', size, page],
    queryFn: async () => {
      const response = await axios.get<Page<Favourite>>(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/favourites`,
        {
          withCredentials: true,
          params: { size, page },
        }
      );
      return response.data;
    },
  });
};

/**
 * Custom hook to fetch a favourite item by its ID.
 *
 * This hook uses the `useQuery` hook from React Query to fetch a favourite item
 * from the backend API. The query key is constructed using the 'favourites' string
 * and the provided ID. The query function makes an HTTP GET request to the backend
 * API endpoint to retrieve the favourite item data.
 *
 * @param {string} id - The ID of the favourite item to fetch.
 * @returns {UseQueryResult<Favourite, Error>} The result of the query, including
 * the favourite item data or any error encountered during the fetch.
 */
export const useGetFavourite = (id: string) => {
  return useQuery({
    queryKey: ['favourites', id],
    queryFn: async () => {
      const response = await axios.get<Favourite>(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/favourites/${id}`
      );
      return response.data;
    },
  });
};

/**
 * Custom hook to post a favourite item.
 *
 * This hook uses the `useMutation` hook from React Query to handle the mutation.
 * It sends a POST request to the backend API to add a favourite item by its ID.
 *
 * @returns {MutationResult} The result of the mutation, including status and data.
 *
 * @example
 * const { mutate, isLoading, error } = usePostFavourite();
 *
 * const handleAddFavourite = (id: string) => {
 *   mutate(id);
 * };
 */
export const usePostFavourite = () => {
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await axios.post<Favourite>(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/favourites/${id}`,
        {},
        { withCredentials: true }
      );
      return response.data;
    },
  });
};

/**
 * Custom hook to delete a favourite item.
 *
 * This hook uses the `useMutation` hook from React Query to perform a DELETE request
 * to the backend API to remove a favourite item by its ID.
 *
 * @returns {MutationFunction} A mutation function that can be used to trigger the delete operation.
 *
 * @example
 * const deleteFavourite = useDeleteFavourite();
 * deleteFavourite.mutate(favouriteId);
 *
 * @remarks
 * The backend URL is retrieved from the environment variable `NEXT_PUBLIC_BACKEND_URL`.
 * The request includes credentials (cookies) for authentication.
 *
 * @throws {Error} Throws an error if the request fails.
 */
export const useDeleteFavourite = () => {
  return useMutation({
    mutationFn: async (id: string) => {
      const response = await axios.delete<Favourite>(
        `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/favourites/${id}`,
        {
          withCredentials: true,
        }
      );
      return response.data;
    },
  });
};
