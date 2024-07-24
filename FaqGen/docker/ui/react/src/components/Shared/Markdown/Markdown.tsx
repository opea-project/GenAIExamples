import  markdownStyles from './markdown.module.scss'
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkFrontmatter from 'remark-frontmatter';
import CodeRender from '../CodeRender/CodeRender';

type MarkdownProps = {
    content: string
}
const Markdown = ({ content }: MarkdownProps) => {
        return (
            <ReactMarkdown
                children={content}
                className={markdownStyles.md}
                remarkPlugins={[remarkGfm, remarkFrontmatter]}
                components={{
                    p: ({  children, ...props }) => {
                        return (
                            <p {...props} style={{ whiteSpace: "pre-wrap" }}>
                                {children}
                            </p>
                        );
                    },
                    a: ({  children, ...props }) => {
                        return (
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
                    table: ({  children, ...props }) => {
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
                    // @ts-expect-error inline can be undefined
                    code({ inline, className, children, }) {
                        const lang = /language-(\w+)/.exec(className || '')
                            // if (lang && lang[1] === "mermaid") {
                            //     return <Mermaid content={String(children).replace(/\n$/, '')} key={"id"} />
                            // }
                        return <CodeRender cleanCode={children} inline={inline} language={(lang && lang[1]) || ""} />
                    }
                }}
            />)
}

export default Markdown;