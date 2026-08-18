/// <reference types="vite/client" />

/** Environment variables this app reads, typed so the API client stays strict. */
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
