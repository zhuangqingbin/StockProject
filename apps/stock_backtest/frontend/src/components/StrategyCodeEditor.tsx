import { Suspense, lazy } from "react";

type StrategyCodeEditorProps = {
  code: string;
};

const MonacoEditor = lazy(() => import("@monaco-editor/react"));

const CodeEditorFallback = ({ code }: StrategyCodeEditorProps) => (
  <textarea aria-label="strategy-code-editor" className="code-editor__fallback" readOnly value={code} />
);

export const StrategyCodeEditor = ({ code }: StrategyCodeEditorProps) => {
  if (import.meta.env.MODE === "test") {
    return <CodeEditorFallback code={code} />;
  }

  return (
    <div className="code-editor">
      <Suspense fallback={<CodeEditorFallback code={code} />}>
        <MonacoEditor
          defaultLanguage="python"
          defaultValue={code}
          height="420px"
          theme="vs-dark"
          options={{
            minimap: { enabled: false },
            fontFamily: "IBM Plex Mono",
            fontSize: 13,
            lineNumbers: "on",
            readOnly: true,
            scrollBeyondLastLine: false,
          }}
        />
      </Suspense>
    </div>
  );
};
