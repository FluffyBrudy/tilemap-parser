import { useRef } from "react";
import { motion } from "framer-motion";
import { CodeBlock } from "../components/CodeBlock";
import type { ClassEntry, ApiEntry } from "../config/api-config";

interface ClassReferenceProps {
  cls: ClassEntry;
}

export function ClassReference({ cls }: ClassReferenceProps) {
  const ref = useRef<HTMLElement>(null);

  return (
    <motion.section
      ref={ref}
      id={`cls-${cls.name}`}
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-12 scroll-mt-8"
    >
      <div className="flex items-center gap-2">
        <h3 className="font-mono text-lg font-medium text-zinc-100">{cls.name}</h3>
        <a href={`#cls-${cls.name}`} className="text-zinc-600 hover:text-zinc-400 text-sm opacity-0 group-hover:opacity-100">#</a>
      </div>
      <p className="text-zinc-400 text-sm mb-4">{cls.description}</p>

      {cls.properties && cls.properties.length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-medium text-zinc-300 mb-2">Properties</h4>
          <div className="space-y-2">
            {cls.properties.map((prop) => (
              <div key={prop.name} className="flex gap-4 text-sm">
                <code className="font-mono text-blue-400 w-48 shrink-0">{prop.name}</code>
                <div>
                  <span className="text-zinc-500 font-mono text-xs">{prop.type}</span>
                  <p className="text-zinc-400">{prop.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {cls.methods && cls.methods.length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-medium text-zinc-300 mb-2">Methods</h4>
          <div className="space-y-4">
            {cls.methods.map((method) => (
              <div key={method.name} className="border-l-2 border-zinc-800 pl-4">
                <code className="font-mono text-sm text-zinc-200">{method.signature}</code>
                <p className="text-zinc-400 text-sm mt-1">{method.description}</p>
                {method.parameters && method.parameters.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {method.parameters.map((param) => (
                      <div key={param.name} className="flex gap-2 text-xs">
                        <code className="font-mono text-amber-400">{param.name}</code>
                        <span className="text-zinc-500">:</span>
                        <code className="font-mono text-zinc-500">{param.type}</code>
                        {param.optional && <span className="text-zinc-600">(optional)</span>}
                        <span className="text-zinc-400">{param.description}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {cls.examples && cls.examples.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-zinc-300 mb-2">Examples</h4>
          {cls.examples.map((ex, i) => (
            <div key={i} className="mb-3">
              {ex.description && <p className="text-zinc-500 text-xs mb-2">{ex.description}</p>}
              <CodeBlock code={ex.code} />
            </div>
          ))}
        </div>
      )}
    </motion.section>
  );
}

interface FunctionReferenceProps {
  fn: ApiEntry;
}

export function FunctionReference({ fn }: FunctionReferenceProps) {
  return (
    <motion.div
      id={`fn-${fn.name}`}
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-8 scroll-mt-8"
    >
      <code className="font-mono text-sm text-zinc-200">{fn.signature}</code>
      <p className="text-zinc-400 text-sm mt-2">{fn.description}</p>

      {fn.parameters && fn.parameters.length > 0 && (
        <div className="mt-3 space-y-1">
          {fn.parameters.map((param) => (
            <div key={param.name} className="flex gap-2 text-sm">
              <code className="font-mono text-amber-400">{param.name}</code>
              <code className="font-mono text-zinc-500">{param.type}</code>
              {param.optional && <span className="text-zinc-600 text-xs">(optional)</span>}
              <span className="text-zinc-400">— {param.description}</span>
            </div>
          ))}
        </div>
      )}

      {fn.returns && (
        <div className="mt-3 text-sm">
          <span className="text-zinc-500">Returns: </span>
          <code className="font-mono text-zinc-400">{fn.returns}</code>
        </div>
      )}

      {fn.examples && fn.examples.length > 0 && (
        <div className="mt-4">
          {fn.examples.map((ex, i) => (
            <div key={i} className="mb-2">
              {ex.description && <p className="text-zinc-500 text-xs mb-1">{ex.description}</p>}
              <CodeBlock code={ex.code} />
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
}