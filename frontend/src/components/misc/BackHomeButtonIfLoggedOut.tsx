'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { selectAuthorized, useAppSelector } from '@/frontend';

/**
 * Renders a primary button that links back to the start page ("/")
 * only when the user is NOT authorized / logged in.
 */
export default function BackHomeButtonIfLoggedOut({
  label = 'Zur Startseite',
  className = '',
}: {
  label?: string;
  className?: string;
}) {
  const authorized = useAppSelector(selectAuthorized);
  if (authorized) return null;
  return (
    <div className={`mt-4 mb-8 ${className}`.trim()}>
      <Button asChild>
        <Link href="/">{label}</Link>
      </Button>
    </div>
  );
}
