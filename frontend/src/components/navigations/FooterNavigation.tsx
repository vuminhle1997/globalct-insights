'use client';

import { Avatar, AvatarFallback, AvatarImage } from '../ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';
import { SidebarSeparator } from '../ui/sidebar';
import { Settings2Icon, LogOutIcon } from 'lucide-react';
import { useAppDispatch, useAppSelector } from '@/frontend/store/hooks/hooks';
import {
  selectUser,
  selectProfilePicture,
  setAppTheme,
  selectAppTheme,
} from '@/frontend/store/reducer/app_reducer';
import Link from 'next/link';
import { MoonIcon, SunIcon } from '@heroicons/react/24/solid';
import { Switch } from '../ui/switch';

/**
 * FooterNavigation component renders a footer section with user information,
 * theme toggle, and a logout option. It utilizes Redux for state management
 * and provides a responsive UI with dropdown menus and switches.
 *
 * @component
 * @returns {JSX.Element} The rendered FooterNavigation component.
 *
 * @remarks
 * - This component uses `useAppSelector` to access the Redux store for theme,
 *   user, and profile picture data.
 * - The `handleThemeChange` function dispatches a Redux action to update the
 *   application theme.
 * - The component includes a dropdown menu with options to toggle the theme
 *   and log out.
 *
 * @dependencies
 * - `useAppSelector` and `useAppDispatch` for Redux state management.
 * - `Avatar`, `DropdownMenu`, `Button`, and other UI components for layout and styling.
 * - Environment variable `NEXT_PUBLIC_BACKEND_URL` for logout URL.
 *
 * @example
 * ```tsx
 * import FooterNavigation from './FooterNavigation';
 *
 * function App() {
 *   return (
 *     <div className="app-container">
 *       <FooterNavigation />
 *     </div>
 *   );
 * }
 * ```
 */
export default function FooterNavigation() {
  const theme = useAppSelector(selectAppTheme);
  const dispatch = useAppDispatch();

  const user = useAppSelector(selectUser);
  const profilePicture = useAppSelector(selectProfilePicture);

  /**
   * Handles the theme change for the application.
   *
   * @param value - The new theme to be applied. Can be either 'dark' or 'light'.
   */
  const handleThemeChange = (value: 'dark' | 'light') => {
    localStorage.setItem('theme', value);
    dispatch(setAppTheme(value));
    window.location.reload();
  };

  return (
    <div className="mt-auto">
      <SidebarSeparator className="mx-0" />
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center gap-2">
          {user ? (
            <Avatar>
              <AvatarImage src={profilePicture ? profilePicture : undefined} />
              <AvatarFallback>{`${user?.givenName[0]}${user?.surname[0]}`}</AvatarFallback>
            </Avatar>
          ) : (
            <div className="h-10 w-10 animate-pulse rounded-full bg-gray-200 dark:bg-gray-700"></div>
          )}
          {user ? (
            <div className="flex flex-col">
              <span className="text-sm font-medium">
                {user?.displayName || ''}
              </span>
              <span className="text-xs text-muted-foreground">
                {user?.mail || user?.email || 'john.doe@example.com'}
              </span>
              <span className="text-xs text-muted-foreground">
                {`${user?.officeLocation} - ${user?.jobTitle}` ||
                  'john.doe@example.com'}
              </span>
            </div>
          ) : (
            <div className="flex flex-col">
              <div className="h-4 w-24 my-1 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
              <div className="h-4 w-32 my-1 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
              <div className="h-4 w-20 my-1 animate-pulse rounded bg-gray-200 dark:bg-gray-700" />
            </div>
          )}
        </div>
        {user ? (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Settings2Icon className="h-4 w-4" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem>
                <div className="flex flex-row w-full justify-between">
                  <SunIcon className="mr-2 h-4 w-4" />
                  <Switch
                    checked={theme === 'dark'}
                    onCheckedChange={checked => {
                      handleThemeChange(checked ? 'dark' : 'light');
                    }}
                    id="theme-switch"
                    aria-label="Theme switch"
                    aria-describedby="theme-switch-description"
                    aria-labelledby="theme-switch-label"
                    name="theme-switch"
                  />
                  <MoonIcon className="ml-2 h-4 w-4" />
                </div>
              </DropdownMenuItem>
              <DropdownMenuItem className="text-destructive">
                <Link href={`${process.env.NEXT_PUBLIC_BACKEND_URL}/logout`}>
                  <div className="flex flex-row">
                    <LogOutIcon className="mr-2 h-4 w-4" />
                    <span>Ausloggen</span>
                  </div>
                </Link>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        ) : (
          <div className="h-4 w-4 animate-pulse rounded bg-gray-200 dark:bg-gray-700"></div>
        )}
      </div>
    </div>
  );
}
