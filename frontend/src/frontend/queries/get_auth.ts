'use client';

import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { setIsAuthorized, setUser, useAppDispatch } from '../store';
import { AzureProfileResponse } from '../types';

/**
 * Custom hook to handle user authentication.
 *
 * This hook uses Redux to set the authentication state and fetches user claims
 * from the backend. It utilizes the `useQuery` hook from `react-query` to manage
 * the asynchronous request and caching.
 *
 * @returns {UseQueryResult<AzureClaims, Error>} The result of the query, including
 * the user claims if authenticated, or an error if not.
 *
 * @example
 * const { data, error, isLoading } = useAuth();
 *
 * if (isLoading) {
 *   // Show loading state
 * }
 *
 * if (error) {
 *   // Handle error
 * }
 *
 * if (data) {
 *   // User is authenticated, access user claims from `data`
 * }
 */
export const useAuth = () => {
  // use redux to set isAuthenticated to true or false
  const dispatch = useAppDispatch();

  return useQuery({
    queryKey: ['auth'],
    queryFn: async () => {
      try {
        const response = await axios.get<AzureProfileResponse>(
          `${process.env.NEXT_PUBLIC_BACKEND_URL}/me`,
          {
            withCredentials: true,
            headers: {
              'Content-Type': 'application/json',
            },
          }
        );

        dispatch(setUser(response.data.user));
        dispatch(setIsAuthorized(true));
        return response.data;
      } catch (error) {
        console.error('Error fetching authentication data:', error);
        dispatch(setIsAuthorized(false));
        throw new Error('Unauthorized');
      }
    },
  });
};
