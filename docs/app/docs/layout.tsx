import { source } from '@/lib/source';
import { DocsLayout } from 'fumadocs-ui/layout';
import type { ReactNode } from 'react';

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <DocsLayout
      nav={{ title: 'jsonschema-ts' }}
      tree={source.pageTree}
    >
      {children}
    </DocsLayout>
  );
}
