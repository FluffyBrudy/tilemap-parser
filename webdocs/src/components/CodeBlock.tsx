import { useState } from "react";
import SyntaxHighlighter from "react-syntax-highlighter/dist/esm/prism-light";
import oneDark from "react-syntax-highlighter/dist/esm/styles/prism/one-dark";
import python from "react-syntax-highlighter/dist/esm/languages/prism/python";
import json from "react-syntax-highlighter/dist/esm/languages/prism/json";
import bash from "react-syntax-highlighter/dist/esm/languages/prism/bash";

SyntaxHighlighter.registerLanguage("python", python);
SyntaxHighlighter.registerLanguage("json", json);
SyntaxHighlighter.registerLanguage("bash", bash);

type Props = {
  code: string;
  title?: string;
  language?: string;
};

export default function CodeBlock({
  code,
  title = "main.py",
  language = "python",
}: Props) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1400);
    } catch {
      /* clipboard unavailable */
    }
  };

  return (
    <figure className="my-6 overflow-hidden border-2 border-line-2 bg-[#0a0810] shadow-hard">
      <figcaption className="flex items-center gap-3 border-b-2 border-line-2 bg-panel-2 px-3 py-2">
        <span
          className="h-3 w-3 border border-line-2 bg-red"
          aria-hidden="true"
        />
        <span
          className="h-3 w-3 border border-line-2 bg-amber"
          aria-hidden="true"
        />
        <span
          className="h-3 w-3 border border-line-2 bg-teal"
          aria-hidden="true"
        />

        <span className="flex-1 truncate font-mono text-[12px] text-mute">
          {title}
        </span>

        <span className="font-pixel text-[8px] text-mute">
          {language.toUpperCase()}
        </span>

        <button
          onClick={copy}
          className="btn-pixel min-w-[72px] px-2 py-0.5 text-[11px]"
        >
          {copied ? "✓ COPIED" : "COPY"}
        </button>
      </figcaption>

      <SyntaxHighlighter
        language={language}
        style={{
          ...oneDark,
          comment: { color: "#9da5b4", fontStyle: "italic" },
        }}
        customStyle={{
          margin: 0,
          padding: "1rem",
          background: "#0a0810",
          fontSize: "14px",
          lineHeight: 1.7,
          fontFamily: '"Space Mono", monospace',
          borderRadius: 0,
        }}
        codeTagProps={{
          style: {
            fontFamily: '"Space Mono", monospace',
          },
        }}
      >
        {code}
      </SyntaxHighlighter>
    </figure>
  );
}
