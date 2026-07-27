import { getDocument, getDocumentSlugs } from '@/lib/mdx';
import { TableOfContents } from '@/components/TableOfContents';
import { notFound } from 'next/navigation';
import type { Metadata } from 'next';

interface PageProps {
  params: Promise<{
    slug: string[];
  }>;
}

export async function generateStaticParams() {
  const slugs = await getDocumentSlugs();
  return slugs.map((slug) => ({
    slug: slug.split('/'),
  }));
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const doc = await getDocument(slug.join('/'));

  if (!doc) {
    return {};
  }

  return {
    title: doc.matter.title,
    description: doc.matter.description,
    keywords: doc.matter.keywords,
    openGraph: {
      title: doc.matter.title,
      description: doc.matter.description,
      type: 'article',
    },
  };
}

export default async function Page({ params }: PageProps) {
  const { slug } = await params;
  const doc = await getDocument(slug.join('/'));

  if (!doc) {
    notFound();
  }

  return (
    <div className="flex gap-8">
      <div className="flex-1 min-w-0">
        <article className="prose prose-reset max-w-none">
          <h1>{doc.matter.title}</h1>
          {doc.matter.description && (
            <p className="text-lg text-muted-foreground">{doc.matter.description}</p>
          )}
          <div className="mt-8 whitespace-pre-wrap text-sm bg-muted p-4 rounded border border-border overflow-x-auto">
            <code>{doc.content}</code>
          </div>
          <p className="mt-8 text-muted-foreground text-sm italic">
            Note: Full markdown rendering coming soon. This is the raw content.
          </p>
        </article>
      </div>
      <TableOfContents entries={doc.toc} />
    </div>
  );
}
