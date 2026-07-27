import { MDXProvider } from '@mdx-js/react';
import { CodeBlock } from './CodeBlock';
import { Callout } from './Callout';
import React from 'react';

interface MDXContentProps {
  children: React.ReactNode;
}

const mdxComponents = {
  CodeBlock,
  Callout,
  code: ({ className, children }: any) => (
    <code className={`${className} bg-muted px-1.5 py-0.5 rounded text-sm`}>
      {children}
    </code>
  ),
  pre: ({ children }: any) => (
    <pre className="bg-muted border border-border rounded-lg p-4 overflow-x-auto">
      {children}
    </pre>
  ),
};

export function MDXContent({ children }: MDXContentProps) {
  return (
    <MDXProvider components={mdxComponents}>
      <div className="prose prose-reset">{children}</div>
    </MDXProvider>
  );
}
