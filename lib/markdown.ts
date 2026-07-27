export function markdownToHtml(markdown: string): string {
  let html = markdown;

  // Headings
  html = html.replace(/^### (.*?)$/gm, '<h3 className="text-2xl font-semibold mt-8 mb-4">$1</h3>');
  html = html.replace(/^## (.*?)$/gm, '<h2 className="text-3xl font-semibold mt-10 mb-6">$1</h2>');
  html = html.replace(/^# (.*?)$/gm, '<h1 className="text-4xl font-bold mt-0 mb-8">$1</h1>');

  // Code blocks
  html = html.replace(/```(\w+)\n([\s\S]*?)```/g, (match, lang, code) => {
    return `<CodeBlock code={\`${code.trim()}\`} language="${lang}" />`;
  });

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code className="bg-muted px-1.5 py-0.5 rounded text-sm">$1</code>');

  // Bold
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');

  // Italic
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  html = html.replace(/_(.+?)_/g, '<em>$1</em>');

  // Links
  html = html.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2">$1</a>');

  // Paragraphs
  html = html.split('\n\n').map((para) => {
    if (para.match(/^<h[1-6]|^<ul|^<ol|^<table|^<CodeBlock|^<Callout/)) {
      return para;
    }
    return `<p className="leading-relaxed mb-4">${ para}</p>`;
  }).join('\n');

  // Unordered lists
  html = html.replace(/^\* (.*?)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>)/s, '<ul className="list-disc list-inside mb-4">$1</ul>');

  // Line breaks
  html = html.replace(/\n/g, '<br />');

  return html;
}
