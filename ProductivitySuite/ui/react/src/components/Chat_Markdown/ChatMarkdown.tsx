import React, { lazy, Suspense, useEffect } from "react";
import markdownStyles from "./markdown.module.scss";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkFrontmatter from "remark-frontmatter";
import remarkBreaks from "remark-breaks";

const CodeRender = lazy(() => import("./CodeRender/CodeRender"));

type MarkdownProps = {
  content: string;
};

const ChatMarkdown = ({ content }: MarkdownProps) => {
  useEffect(() => {
    // preload in background
    import("./CodeRender/CodeRender");
  }, []);

  return (
    <ReactMarkdown
      children={content.replace(/\\\\n/g, "\n").replace(/\\n/g, "\n")} // line-breaks were escaped and double escaped...
      className={`${markdownStyles.md} ${markdownStyles.markdownWrapper}`}
      remarkPlugins={[remarkBreaks, remarkGfm, remarkFrontmatter]}
      components={{
        p: ({ children, ...props }) => {
          // check for nested block elements attempting to inject into a p tag
          const hasBlockElement = React.Children.toArray(children).some(
            (child) =>
              React.isValidElement(child) &&
              typeof child.type === "string" &&
              ["div", "h1", "h2", "h3", "ul", "ol", "table"].includes(
                child.type,
              ),
          );

          // If block-level elements are found, avoid wrapping in <p>
          return hasBlockElement ? (
            <>{children}</>
          ) : (
            <p {...props} style={{ whiteSpace: "pre-wrap" }}>
              {children}
            </p>
          );
        },
        a: ({ children, ...props }) => {
          return (
            //@ts-ignore
            <a
              href={props.href}
              target="_blank"
              rel="noopener noreferrer"
              {...props}
            >
              {children}
            </a>
          );
        },
        table: ({ children, ...props }) => {
          return (
            <div
              className={markdownStyles.tableDiv}
              style={{
                overflowX: "auto",
                padding: "10px",
              }}
            >
              <table {...props}>{children}</table>
            </div>
          );
        },
        code({ inline, className, children }) {
          const lang = /language-(\w+)/.exec(className || "");
          return (
            <Suspense fallback={<code>Loading Code Block...</code>}>
              {/*@ts-ignore*/}
              <CodeRender
                cleanCode={children}
                inline={inline}
                language={(lang && lang[1]) || ""}
              />
            </Suspense>
          );
        },
      }}
    />
  );
};

export default ChatMarkdown;
