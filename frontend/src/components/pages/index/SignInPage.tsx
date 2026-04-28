'use client';

import React from 'react';
import Logo from '@/static/globalLogo.png';
import Image from 'next/image';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useForm } from 'react-hook-form';
import { Button } from '@/components/ui/button';
import { useLoginUser, useRegisterUser } from '@/frontend/queries';
import { WaveBackground } from '@/components/ui/wave-animation';

enum SignInPageSections {
  LOGIN = 'login',
  SIGNUP = 'signup',
  WELCOME = 'welcome',
}

/**
 * A functional React component that renders a welcome section for a sign-in page.
 * This section includes a title, a description, and a button for signing in with a Microsoft account.
 *
 * @component
 * @returns {JSX.Element} The rendered welcome section.
 *
 * @remarks
 * - The sign-in button redirects the user to the backend sign-in URL, which is constructed
 *   using the `NEXT_PUBLIC_BACKEND_URL` environment variable.
 * - The button includes a Microsoft logo represented by an SVG icon.
 *
 * @example
 * <WelcomeSection />
 *
 * @dependencies
 * - Relies on Tailwind CSS classes for styling.
 * - Requires the `NEXT_PUBLIC_BACKEND_URL` environment variable to be set.
 */
const WelcomeSection = () => {
  return (
    <div className="welcome-section">
      <div className="text-center">
        <h2 className="text-xl md:text-2xl font-bold tracking-tight text-foreground">
          Anmelden
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Bitte melden Sie sich mit Ihrem Microsoft-Konto an, um fortzufahren
        </p>
      </div>
      <div className="mt-8">
        <a
          href={`${process.env.NEXT_PUBLIC_BACKEND_URL}/signin/`}
          className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-primary dark:bg-accent border px-4 py-3 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 23 23"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path fill="#F25022" d="M1 1h10v10H1z" />
            <path fill="#00A4EF" d="M1 12h10v10H1z" />
            <path fill="#7FBA00" d="M12 1h10v10H12z" />
            <path fill="#FFB900" d="M12 12h10v10H12z" />
          </svg>
          Mit Microsoft anmelden
        </a>
      </div>
      {/* Show version of app */}
      <div className="flex items-center justify-center text-center mt-4">
        <span className="text-xs text-muted-foreground">
          Version: v{process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0'}
        </span>
      </div>
    </div>
  );
};

/**
 * The `SignUpSection` component renders a registration form for users to sign up.
 * It includes fields for first name, last name, email, password, and password confirmation.
 * The form validates user input and displays error messages for invalid fields.
 *
 * @param {Object} props - The component props.
 * @param {React.Dispatch<React.SetStateAction<SignInPageSections>>} props.setShowSections - A function to update the current section of the sign-in page.
 *
 * @returns {JSX.Element} A JSX element representing the sign-up section.
 *
 * @remarks
 * - The form uses `react-hook-form` for form handling and validation.
 * - The `useRegisterUser` hook is used to handle user registration via an asynchronous mutation.
 * - Validation rules include minimum length requirements and email format validation.
 * - On successful registration, the page reloads.
 * - Users can reset the form or navigate to the login section.
 *
 * @example
 * ```tsx
 * <SignUpSection setShowSections={setShowSections} />
 * ```
 */
const SignUpSection = ({
  setShowSections,
}: {
  setShowSections: React.Dispatch<React.SetStateAction<SignInPageSections>>;
}) => {
  const {
    register,
    handleSubmit: handleFormSubmit,
    formState: { errors },
    reset,
  } = useForm<{
    name: string;
    last_name: string;
    email: string;
    password: string;
    confirm_password: string;
  }>();

  const { mutateAsync: registerUser, isPending, isError } = useRegisterUser();

  const handleSubmit = async (data: {
    name: string;
    last_name: string;
    email: string;
    password: string;
    confirm_password: string;
  }) => {
    const res = await registerUser(data);
    if (res.status === 200) {
      window.location.reload();
    }
  };

  return (
    <div className="welcome-section">
      <div className="text-center">
        <h2 className="text-xl md:text-2xl font-bold tracking-tight text-foreground">
          Registrieren
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Bitte registrieren Sie sich mit Ihrer E-Mail-Adresse, um fortzufahren.
        </p>
        <p className="mt text-sm text-muted-foreground">
          Andernfalls können Sie sich{' '}
          <span
            onClick={() => setShowSections(SignInPageSections.LOGIN)}
            className="text-primary underline cursor-pointer"
          >
            hier anmelden
          </span>
          .
        </p>
      </div>
      <form onSubmit={handleFormSubmit(handleSubmit)} className="mt-8">
        <div className="flex gap-2">
          <div className="w-[50%]">
            <Label
              htmlFor="name"
              className="text-sm font-medium text-foreground"
            >
              Vorname
            </Label>
            <Input
              type="text"
              id="name"
              {...register('name', {
                required: true,
                minLength: {
                  value: 2,
                  message: 'Vorname muss mindestens 2 Zeichen lang sein',
                },
                validate: value => {
                  if (value.length < 2) {
                    return 'Vorname muss mindestens 2 Zeichen lang sein';
                  }
                  return true;
                },
              })}
              placeholder="John"
            />
            {errors.name && (
              <p className="text-sm text-red-500 mt-2">{errors.name.message}</p>
            )}
          </div>
          <div className="w-[50%]">
            <Label
              htmlFor="last_name"
              className="text-sm font-medium text-foreground"
            >
              Nachname
            </Label>
            <Input
              type="text"
              id="last_name"
              placeholder="Doe"
              {...register('last_name', {
                required: true,
                minLength: {
                  value: 2,
                  message: 'Nachname muss mindestens 2 Zeichen lang sein',
                },
                validate: value => {
                  if (value.length < 2) {
                    return 'Nachname muss mindestens 2 Zeichen lang sein';
                  }
                  return true;
                },
              })}
            />
            {errors.last_name && (
              <p className="text-sm text-red-500 mt-2">
                {errors.last_name.message}
              </p>
            )}
          </div>
        </div>
        <div className="w-full">
          <Label
            htmlFor="email"
            className="text-sm font-medium text-foreground"
          >
            E-Mail
          </Label>
          <Input
            type="email"
            id="email"
            {...register('email', {
              required: true,
              pattern: {
                value: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
                message: 'Bitte geben Sie eine gültige E-Mail-Adresse ein',
              },
              validate: value => {
                if (value.length < 5) {
                  return 'E-Mail-Adresse muss mindestens 5 Zeichen lang sein';
                }
                return true;
              },
            })}
            placeholder="john@doe.com"
          />
          {errors.email && (
            <p className="text-sm text-red-500 mt-2">{errors.email.message}</p>
          )}
        </div>
        <div className="w-full">
          <Label
            htmlFor="password"
            className="text-sm font-medium text-foreground"
          >
            Passwort
          </Label>
          <Input
            type="password"
            id="password"
            {...register('password', {
              required: true,
              minLength: {
                value: 8,
                message: 'Passwort muss mindestens 8 Zeichen lang sein',
              },
              validate: value => {
                if (value.length < 8) {
                  return 'Passwort muss mindestens 8 Zeichen lang sein';
                }
                return true;
              },
            })}
          />
          {errors.password && (
            <p className="text-sm text-red-500 mt-2">
              {errors.password.message}
            </p>
          )}
        </div>
        <div className="w-full">
          <Label
            htmlFor="password"
            className="text-sm font-medium text-foreground"
          >
            Passwort bestätigen
          </Label>
          <Input
            type="password"
            id="confirm"
            {...register('confirm_password', {
              required: true,
              minLength: {
                value: 8,
                message: 'Passwort muss mindestens 8 Zeichen lang sein',
              },
              validate: value => {
                if (value.length < 8) {
                  return 'Passwort muss mindestens 8 Zeichen lang sein';
                }
                return true;
              },
            })}
          />
          {errors.confirm_password && (
            <p className="text-sm text-red-500 mt-2">
              {errors.confirm_password.message}
            </p>
          )}
        </div>
        {!isPending && isError && (
          <p className="text-sm text-red-500 mt-2">
            Registrierungsfehler. Bitte überprüfen Sie Ihre
            Anmeldeinformationen.
          </p>
        )}
        <div className="flex flex-col">
          <Button type="submit" className="mt-4 w-full dark:text-black">
            Registrieren
          </Button>
          <Button
            type="reset"
            className="mt-4 w-full dark:text-black"
            onClick={() => reset()}
          >
            Zurücksetzen
          </Button>
        </div>
      </form>
    </div>
  );
};

/**
 * The `LogInSection` component renders a login form for users to sign in.
 * It includes fields for email and password, along with validation and error handling.
 *
 * @param {Object} props - The component props.
 * @param {React.Dispatch<React.SetStateAction<SignInPageSections>>} props.setShowSections -
 * A function to update the current section of the sign-in page.
 *
 * @returns {JSX.Element} A JSX element representing the login section.
 *
 * @remarks
 * - The form uses `react-hook-form` for handling form state and validation.
 * - The `useLoginUser` hook is used to handle the login API call.
 * - Displays error messages for invalid email or password inputs.
 * - Shows a loading state when the login request is pending.
 * - Redirects the user by reloading the page upon successful login.
 *
 * @example
 * ```tsx
 * <LogInSection setShowSections={setShowSections} />
 * ```
 */
const LogInSection = ({
  setShowSections,
}: {
  setShowSections: React.Dispatch<React.SetStateAction<SignInPageSections>>;
}) => {
  const {
    register,
    handleSubmit: handleFormSubmit,
    formState: { errors },
  } = useForm<{
    email: string;
    password: string;
  }>();

  const { mutateAsync: login, isPending, isError } = useLoginUser();

  const handleSubmit = async (data: { email: string; password: string }) => {
    const res = await login(data);
    if (res.status === 200) {
      window.location.reload();
    }
  };

  return (
    <div className="welcome-section">
      <div className="text-center">
        <h2 className="text-xl md:text-2xl font-bold tracking-tight text-foreground">
          Anmelden
        </h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Bitte melden Sie sich mit Ihrem Email an, um fortzufahren.
        </p>
        <p className="mt text-sm text-muted-foreground">
          Andernfalls können Sie sich{' '}
          <span
            onClick={() => setShowSections(SignInPageSections.SIGNUP)}
            className="text-primary underline cursor-pointer"
          >
            hier registrieren
          </span>
          .
        </p>
      </div>
      <form onSubmit={handleFormSubmit(handleSubmit)} className="mt-8">
        <div className="w-full">
          <Label
            htmlFor="email"
            className="text-sm font-medium text-foreground"
          >
            E-Mail
          </Label>
          <Input
            disabled={isPending}
            type="email"
            id="email"
            {...register('email', {
              required: true,
              pattern: {
                value: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
                message: 'Bitte geben Sie eine gültige E-Mail-Adresse ein',
              },
              validate: value => {
                if (value.length < 5) {
                  return 'E-Mail-Adresse muss mindestens 5 Zeichen lang sein';
                }
                return true;
              },
            })}
            placeholder="john@doe.com"
          />
          {errors.email && (
            <p className="text-sm text-red-500 mt-2">{errors.email.message}</p>
          )}
        </div>
        <div className="w-full">
          <Label
            htmlFor="password"
            className="text-sm font-medium text-foreground"
          >
            Passwort
          </Label>
          <Input
            disabled={isPending}
            type="password"
            id="password"
            {...register('password', {
              required: true,
              minLength: {
                value: 8,
                message: 'Passwort muss mindestens 8 Zeichen lang sein',
              },
              validate: value => {
                if (value.length < 8) {
                  return 'Passwort muss mindestens 8 Zeichen lang sein';
                }
                return true;
              },
            })}
          />
          {errors.password && (
            <p className="text-sm text-red-500 mt-2">
              {errors.password.message}
            </p>
          )}
        </div>
        {!isPending && isError && (
          <p className="text-sm text-red-500 mt-2">
            Anmeldefehler. Bitte überprüfen Sie Ihre Anmeldeinformationen.
          </p>
        )}
        <Button
          disabled={isPending}
          type="submit"
          className="mt-4 w-full dark:text-black"
        >
          Anmelden
        </Button>
      </form>
    </div>
  );
};

/**
 * The `SignInPage` component represents the main sign-in page of the application.
 * It provides a user interface for signing in or signing up, with a welcome section
 * and tabs for different authentication methods (e.g., Azure and Email).
 *
 * @component
 * @returns {JSX.Element} The rendered sign-in page component.
 *
 * @remarks
 * - The component uses a state variable `showSections` to determine which section
 *   (welcome, sign-up, or log-in) to display.
 * - The `Tabs` component allows users to switch between authentication methods.
 * - The left section contains branding and a welcome message, while the right section
 *   contains the authentication form.
 * - The footer includes links to privacy policy, terms of use, and contact information.
 *
 * @example
 * ```tsx
 * import SignInPage from './SignInPage';
 *
 * function App() {
 *   return <SignInPage />;
 * }
 * ```
 *
 * @see {@link SignInPageSections} for the available sections.
 * @see {@link SignUpSection} and {@link LogInSection} for the respective components.
 */
export default function SignInPage() {
  const [showSections, setShowSections] = React.useState<SignInPageSections>(
    SignInPageSections.WELCOME
  );

  const section = () => {
    switch (showSections) {
      case SignInPageSections.SIGNUP:
        return <SignUpSection setShowSections={setShowSections} />;
      case SignInPageSections.LOGIN:
        return <LogInSection setShowSections={setShowSections} />;
      case SignInPageSections.WELCOME:
        return <WelcomeSection />;
      default:
        return null;
    }
  };

  return (
    <div className="relative flex min-h-screen flex-col">
      <main className="flex flex-grow flex-col md:flex-row items-center justify-center md:items-stretch">
        {/* Left Section */}
        <div className="relative flex w-full md:w-1/2 flex-col items-center justify-center md:bg-primary/10 p-4 md:p-0 overflow-hidden">
          {/* Content above waves */}
          <div className="relative z-10 text-center">
            <Image
              src={Logo}
              alt="Login illustration"
              className="mx-auto w-2/3 md:w-1/2 drop-shadow-lg animate-fade-in-up delay-200"
            />
            <div className="mt-8">
              <h1 className="mb-3 text-2xl md:text-4xl font-bold text-foreground animate-fade-in-up delay-300">
                Global CT Insights
              </h1>
              <p className="mb-6 text-lg md:text-xl text-muted-foreground animate-fade-in-up delay-400">
                Intelligenz durch datengestützte Gespräche
              </p>
            </div>
          </div>
          {/* Animated waves background */}
          <WaveBackground />
        </div>

        {/* Right Section */}
        <div className="flex w-full md:w-1/2 items-center justify-center bg-card px-4 md:px-8 py-8 md:py-0">
          <div className="w-full max-w-md space-y-8">{section()}</div>
        </div>
      </main>

      {/* Footer Section */}
      <footer className="w-full border-t border-border bg-background py-4 text-center md:text-left">
        <div className="mx-auto max-w-7xl px-4">
          <div className="flex flex-col items-center justify-between space-y-4 sm:flex-row sm:space-y-0">
            <div className="text-sm text-muted-foreground flex items-center justify-center text-center">
              © 2014 - {new Date().getFullYear()} global CT Services &
              Consulting GmbH. <br /> Alle Rechte vorbehalten. <br />
            </div>
            <div className="flex flex-wrap justify-center lg:gap-4 gap-2 w-full lg:w-auto">
              <a
                href="/privacy"
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                Datenschutzerklärung
              </a>
              <a
                href="/terms"
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                Nutzungsbedingungen
              </a>
              <a
                href="/contact"
                className="text-sm text-muted-foreground hover:text-foreground"
              >
                Kontakt
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
