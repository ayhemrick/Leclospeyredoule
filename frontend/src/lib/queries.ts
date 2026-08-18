/** TanStack Query hooks: one place per endpoint, one cache key factory. */

import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseMutationResult,
  type UseQueryResult,
} from '@tanstack/react-query';

import { api, ApiError } from '@/lib/api';
import type {
  AccessCode,
  AccessPolicy,
  AccessStats,
  AccessStatus,
  Admin,
  AdminAttraction,
  AdminGuideSection,
  Attraction,
  AttractionCategory,
  AuditEntry,
  GuestSessionRow,
  GuideSection,
  LoginResponse,
  Page,
} from '@/lib/types';

export const keys = {
  attractions: (category?: AttractionCategory) => ['attractions', category ?? 'all'] as const,
  publicGuide: () => ['guide', 'public'] as const,
  guestGuide: () => ['guide', 'guest'] as const,
  accessStatus: () => ['access', 'status'] as const,
  me: () => ['admin', 'me'] as const,
  accessCode: () => ['admin', 'access', 'code'] as const,
  accessPolicy: () => ['admin', 'access', 'policy'] as const,
  accessStats: () => ['admin', 'access', 'stats'] as const,
  sessions: (includeEnded: boolean) => ['admin', 'access', 'sessions', includeEnded] as const,
  adminSections: () => ['admin', 'content', 'sections'] as const,
  adminAttractions: () => ['admin', 'content', 'attractions'] as const,
  admins: () => ['admin', 'users'] as const,
  audit: (action: string) => ['admin', 'audit', action] as const,
};

// ---------------------------------------------------------------------------
// Public site
// ---------------------------------------------------------------------------
export function useAttractions(category?: AttractionCategory): UseQueryResult<Attraction[]> {
  return useQuery({
    queryKey: keys.attractions(category),
    queryFn: ({ signal }) =>
      api.get<Attraction[]>('/api/v1/public/attractions', { category }, signal),
    staleTime: 5 * 60 * 1000,
  });
}

export function usePublicGuide(): UseQueryResult<GuideSection[]> {
  return useQuery({
    queryKey: keys.publicGuide(),
    queryFn: ({ signal }) => api.get<GuideSection[]>('/api/v1/public/guide', undefined, signal),
    staleTime: 5 * 60 * 1000,
  });
}

export function useAccessStatus(): UseQueryResult<AccessStatus> {
  return useQuery({
    queryKey: keys.accessStatus(),
    queryFn: ({ signal }) => api.get<AccessStatus>('/api/v1/access/status', undefined, signal),
    // The window is measured in hours; a minute of staleness is harmless and
    // keeps the countdown from hammering the API.
    staleTime: 60 * 1000,
    retry: false,
  });
}

export function useGuestGuide(enabled: boolean): UseQueryResult<GuideSection[]> {
  return useQuery({
    queryKey: keys.guestGuide(),
    queryFn: ({ signal }) =>
      api.get<GuideSection[]>('/api/v1/public/guide/guest', undefined, signal),
    enabled,
    retry: (failureCount, error) =>
      !(error instanceof ApiError && error.isAccessDenied) && failureCount < 2,
  });
}

export function useRedeemCode(): UseMutationResult<AccessStatus, Error, string> {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (code: string) => api.post<AccessStatus>('/api/v1/access/redeem', { code }),
    onSuccess: (status) => {
      client.setQueryData(keys.accessStatus(), status);
      void client.invalidateQueries({ queryKey: keys.guestGuide() });
    },
  });
}

export function useLeaveAccess(): UseMutationResult<{ detail: string }, Error, void> {
  const client = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<{ detail: string }>('/api/v1/access/leave'),
    onSuccess: () => {
      client.setQueryData(keys.accessStatus(), {
        granted: false,
        expires_at: null,
        seconds_remaining: null,
      } satisfies AccessStatus);
      client.removeQueries({ queryKey: keys.guestGuide() });
    },
  });
}

// ---------------------------------------------------------------------------
// Admin: session
// ---------------------------------------------------------------------------
export function useCurrentAdmin(): UseQueryResult<Admin | null> {
  return useQuery({
    queryKey: keys.me(),
    queryFn: async ({ signal }) => {
      try {
        return await api.get<Admin>('/api/v1/auth/me', undefined, signal);
      } catch (error) {
        if (error instanceof ApiError && error.isUnauthenticated) return null;
        throw error;
      }
    },
    retry: false,
    staleTime: 30 * 1000,
  });
}

export function useLogin(): UseMutationResult<
  LoginResponse,
  Error,
  { email: string; password: string }
> {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (credentials) => api.post<LoginResponse>('/api/v1/auth/login', credentials),
    onSuccess: (response) => {
      client.setQueryData(keys.me(), response.admin);
    },
  });
}

export function useLogout(): UseMutationResult<{ detail: string }, Error, void> {
  const client = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<{ detail: string }>('/api/v1/auth/logout'),
    onSuccess: () => {
      client.setQueryData(keys.me(), null);
      client.clear();
    },
  });
}

// ---------------------------------------------------------------------------
// Admin: access control
// ---------------------------------------------------------------------------
export function useAccessCode(): UseQueryResult<AccessCode> {
  return useQuery({
    queryKey: keys.accessCode(),
    queryFn: ({ signal }) => api.get<AccessCode>('/api/v1/admin/access/code', undefined, signal),
  });
}

export function useAccessPolicy(): UseQueryResult<AccessPolicy> {
  return useQuery({
    queryKey: keys.accessPolicy(),
    queryFn: ({ signal }) =>
      api.get<AccessPolicy>('/api/v1/admin/access/policy', undefined, signal),
  });
}

export function useAccessStats(): UseQueryResult<AccessStats> {
  return useQuery({
    queryKey: keys.accessStats(),
    queryFn: ({ signal }) => api.get<AccessStats>('/api/v1/admin/access/stats', undefined, signal),
    refetchInterval: 30 * 1000,
  });
}

export function useUpdatePolicy(): UseMutationResult<AccessPolicy, Error, Partial<AccessPolicy>> {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (patch) => api.patch<AccessPolicy>('/api/v1/admin/access/policy', patch),
    onSuccess: (policy) => {
      client.setQueryData(keys.accessPolicy(), policy);
      void client.invalidateQueries({ queryKey: keys.accessCode() });
      void client.invalidateQueries({ queryKey: keys.accessStats() });
    },
  });
}

export function useRotateCode(): UseMutationResult<AccessCode, Error, void> {
  const client = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<AccessCode>('/api/v1/admin/access/code/rotate'),
    onSuccess: (code) => {
      client.setQueryData(keys.accessCode(), code);
      void client.invalidateQueries({ queryKey: keys.accessStats() });
      void client.invalidateQueries({ queryKey: ['admin', 'audit'] });
    },
  });
}

export function useGuestSessions(includeEnded: boolean): UseQueryResult<Page<GuestSessionRow>> {
  return useQuery({
    queryKey: keys.sessions(includeEnded),
    queryFn: ({ signal }) =>
      api.get<Page<GuestSessionRow>>(
        '/api/v1/admin/access/sessions',
        { include_ended: includeEnded, limit: 100 },
        signal,
      ),
  });
}

export function useRevokeSession(): UseMutationResult<{ detail: string }, Error, string> {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (id) => api.delete<{ detail: string }>(`/api/v1/admin/access/sessions/${id}`),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ['admin', 'access'] });
    },
  });
}

export function useRevokeAllSessions(): UseMutationResult<{ detail: string }, Error, void> {
  const client = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<{ detail: string }>('/api/v1/admin/access/sessions/revoke-all'),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ['admin', 'access'] });
    },
  });
}

// ---------------------------------------------------------------------------
// Admin: content
// ---------------------------------------------------------------------------
export function useAdminSections(): UseQueryResult<AdminGuideSection[]> {
  return useQuery({
    queryKey: keys.adminSections(),
    queryFn: ({ signal }) =>
      api.get<AdminGuideSection[]>('/api/v1/admin/content/guide-sections', undefined, signal),
  });
}

export function useSaveSection(): UseMutationResult<
  AdminGuideSection,
  Error,
  { id?: string; values: Record<string, unknown> }
> {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, values }) =>
      id
        ? api.patch<AdminGuideSection>(`/api/v1/admin/content/guide-sections/${id}`, values)
        : api.post<AdminGuideSection>('/api/v1/admin/content/guide-sections', values),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: keys.adminSections() });
      void client.invalidateQueries({ queryKey: ['guide'] });
    },
  });
}

export function useDeleteSection(): UseMutationResult<{ detail: string }, Error, string> {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (id) =>
      api.delete<{ detail: string }>(`/api/v1/admin/content/guide-sections/${id}`),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: keys.adminSections() });
      void client.invalidateQueries({ queryKey: ['guide'] });
    },
  });
}

export function useAdminAttractions(): UseQueryResult<AdminAttraction[]> {
  return useQuery({
    queryKey: keys.adminAttractions(),
    queryFn: ({ signal }) =>
      api.get<AdminAttraction[]>('/api/v1/admin/content/attractions', undefined, signal),
  });
}

export function useSaveAttraction(): UseMutationResult<
  AdminAttraction,
  Error,
  { id?: string; values: Record<string, unknown> }
> {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, values }) =>
      id
        ? api.patch<AdminAttraction>(`/api/v1/admin/content/attractions/${id}`, values)
        : api.post<AdminAttraction>('/api/v1/admin/content/attractions', values),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: keys.adminAttractions() });
      void client.invalidateQueries({ queryKey: ['attractions'] });
    },
  });
}

export function useDeleteAttraction(): UseMutationResult<{ detail: string }, Error, string> {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (id) => api.delete<{ detail: string }>(`/api/v1/admin/content/attractions/${id}`),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: keys.adminAttractions() });
      void client.invalidateQueries({ queryKey: ['attractions'] });
    },
  });
}

// ---------------------------------------------------------------------------
// Admin: accounts and audit
// ---------------------------------------------------------------------------
export function useAdmins(enabled: boolean): UseQueryResult<Admin[]> {
  return useQuery({
    queryKey: keys.admins(),
    queryFn: ({ signal }) => api.get<Admin[]>('/api/v1/admin/users', undefined, signal),
    enabled,
    retry: false,
  });
}

export function useSaveAdmin(): UseMutationResult<
  Admin,
  Error,
  { id?: string; values: Record<string, unknown> }
> {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, values }) =>
      id
        ? api.patch<Admin>(`/api/v1/admin/users/${id}`, values)
        : api.post<Admin>('/api/v1/admin/users', values),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: keys.admins() });
    },
  });
}

export function useDeleteAdmin(): UseMutationResult<{ detail: string }, Error, string> {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (id) => api.delete<{ detail: string }>(`/api/v1/admin/users/${id}`),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: keys.admins() });
    },
  });
}

export function useAuditLog(action: string): UseQueryResult<Page<AuditEntry>> {
  return useQuery({
    queryKey: keys.audit(action),
    queryFn: ({ signal }) =>
      api.get<Page<AuditEntry>>(
        '/api/v1/admin/audit',
        { action: action || undefined, limit: 100 },
        signal,
      ),
  });
}
