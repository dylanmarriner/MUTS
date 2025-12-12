'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { HardwareProvider } from '@/contexts/HardwareContext';
import { ReactNode } from 'react';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5000,
      retry: 1,
    },
  },
});

interface ProvidersProps {
  children: ReactNode;
}

export default function Providers({ children }: ProvidersProps) {
  return (
    <QueryClientProvider client={queryClient}>
      <HardwareProvider>
        {children}
      </HardwareProvider>
    </QueryClientProvider>
  );
}