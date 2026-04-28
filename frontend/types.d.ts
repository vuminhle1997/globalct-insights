export {};

declare namespace NodeJS {
  interface ProcessEnv {
    NEXT_PUBLIC_BACKEND_URL: string;
    NEXT_PUBLIC_APP_VERSION?: string;
  }
}
