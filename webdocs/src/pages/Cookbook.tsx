import { Link } from "react-router-dom";
import CodeBlock from "../components/CodeBlock";
import Callout from "../components/Callout";
import cookbookSnippets from "../snippets/cookbook.json";

export default function Cookbook() {
  return (
    <div className="content">
      <h1>Cookbook: Common Access Patterns</h1>
      <p>
        Short answers to the questions that come up most often in daily use:
        the exact expression for one lookup, verified against the current
        release so the examples below cannot go stale silently. Movement-level
        recipes keep their pages: the <a href="/runner">CollisionRunner
        guide</a> covers tile identity underfoot and surface drift.
      </p>
      <Callout kind="info" title="OBJECT IDS ARE DICT KEYS">
        Object layers store objects as a dictionary keyed by the editor's
        object id. There is no stable id field on the parsed entry itself; the
        key is the id.
      </Callout>
      {cookbookSnippets.map((snippet) => (
        <section key={snippet.id}>
          <h2 id={snippet.id}>{snippet.title}</h2>
          <p>{snippet.introduction}</p>
          <CodeBlock title={snippet.id} code={snippet.code} />
        </section>
      ))}
      <Callout kind="tip" title="MORE PATTERNS">
        Missing a pattern? The <a href="/json">JSON Formats</a> page maps each
        editor file to its parsed output, and the{" "}
        <Link to="/api">API Reference</Link> lists every public entry point.
      </Callout>
    </div>
  );
}
