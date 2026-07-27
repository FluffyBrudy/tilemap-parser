import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';
import { TocEntry } from '@/components/TableOfContents';

const CONTENT_DIR = path.join(process.cwd(), 'content');

export interface DocumentMatter {
  title: string;
  description?: string;
  category?: string;
  order?: number;
  keywords?: string[];
  updated?: string;
}

export interface Document {
  slug: string;
  matter: DocumentMatter;
  content: string;
  toc: TocEntry[];
}

function extractHeadings(content: string): TocEntry[] {
  const headingRegex = /^(#{2,6})\s+(.+)$/gm;
  const headings: TocEntry[] = [];
  let match;

  while ((match = headingRegex.exec(content)) !== null) {
    const level = match[1].length;
    const title = match[2].trim();
    const id = title
      .toLowerCase()
      .replace(/[^\w\s-]/g, '')
      .replace(/\s+/g, '-');

    headings.push({ id, title, level });
  }

  return headings;
}

export async function getDocument(slug: string): Promise<Document | null> {
  try {
    // Handle nested slugs like "getting-started/installation"
    const filePath = path.join(CONTENT_DIR, `${slug}.mdx`);
    
    if (!fs.existsSync(filePath)) {
      return null;
    }

    const fileContents = fs.readFileSync(filePath, 'utf8');
    const { data, content } = matter(fileContents);
    const toc = extractHeadings(content);

    return {
      slug,
      matter: data as DocumentMatter,
      content,
      toc,
    };
  } catch (error) {
    console.error(`Error loading document: ${slug}`, error);
    return null;
  }
}

export async function getAllDocuments(): Promise<Document[]> {
  const documents: Document[] = [];

  function walkDir(dir: string, baseSlug = '') {
    const files = fs.readdirSync(dir);

    for (const file of files) {
      const filePath = path.join(dir, file);
      const stat = fs.statSync(filePath);

      if (stat.isDirectory()) {
        walkDir(filePath, path.join(baseSlug, file));
      } else if (file.endsWith('.mdx')) {
        const slug = path.join(baseSlug, file.replace(/\.mdx$/, '')).replace(/\\/g, '/');
        const fileContents = fs.readFileSync(filePath, 'utf8');
        const { data, content } = matter(fileContents);
        const toc = extractHeadings(content);

        documents.push({
          slug,
          matter: data as DocumentMatter,
          content,
          toc,
        });
      }
    }
  }

  walkDir(CONTENT_DIR);
  return documents;
}

export async function getDocumentSlugs(): Promise<string[]> {
  const documents = await getAllDocuments();
  return documents.map((doc) => doc.slug);
}
