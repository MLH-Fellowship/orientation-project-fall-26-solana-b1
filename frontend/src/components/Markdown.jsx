import "katex/dist/katex.min.css";
import ReactMarkdown from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import { CodeBlock } from "./arc/code-block/code-block";

// Fenced blocks arrive as <pre><code class="language-x">; inline code has no <pre> and stays plain.
function Pre({ children }) {
  const { className = "", children: code = "" } = children?.props ?? {};
  const language = /language-(\S+)/.exec(className)?.[1] ?? "text";
  return <CodeBlock code={String(code).replace(/\n$/, "")} language={language} maxLines={20} />;
}

function Link(props) {
  return <a {...props} target="_blank" rel="noreferrer" />;
}

const components = { pre: Pre, a: Link };
const remarkPlugins = [remarkGfm, remarkMath];
// LLMs write maths as $…$ / $$…$$ LaTeX; malformed input renders as red source instead of throwing.
const rehypePlugins = [[rehypeKatex, { throwOnError: false }]];

export default function Markdown({ children }) {
  return (
    <ReactMarkdown remarkPlugins={remarkPlugins} rehypePlugins={rehypePlugins} components={components}>
      {children}
    </ReactMarkdown>
  );
}
