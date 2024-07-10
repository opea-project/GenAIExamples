import styles from './codeRender.module.scss'
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { tomorrow } from "react-syntax-highlighter/dist/esm/styles/prism";
import { IconCopy } from '@tabler/icons-react';
import { Button, CopyButton } from '@mantine/core';

type CodeRenderProps = {
    cleanCode: React.ReactNode,
    language: string,
    inline: boolean
}
const CodeRender = ({ cleanCode, language, inline }:CodeRenderProps) => {
    cleanCode = String(cleanCode).replace(/\n$/, '').replace(/^\s*[\r\n]/gm, '') //right trim and remove empty lines from the input
    console.log(styles)
    try {
        return inline ? (<code className='inline-code'><i>{cleanCode}</i></code>) : (
            <div className={styles.code}>
                <div className={styles.codeHead}>
                    <div className='code-title'>
                        {language || "language not detected"}
                    </div>
                    <div className={styles.codeActionGroup} >
                        <CopyButton value={cleanCode.toString()}>
                            {({ copied, copy }) => (
                                <Button color={copied ? 'teal' : 'blue'} styles={{root:{border:"none"}}} leftSection={<IconCopy size={12} />} onClick={copy}>
                                    {copied ? 'Copied' : 'Copy'}
                                </Button>
                            )}
                        </CopyButton>
                    </div>
                </div>
                <SyntaxHighlighter
                    className={styles.codeHighlighterDiv}
                    children={cleanCode.toString()}
                    wrapLongLines={true}
                    style={tomorrow}
                    language={language}
                    PreTag="div"
                />
            </div>)
    } catch (err) {
        return (
            <pre>
                {cleanCode}
            </pre>
        )
    }

}


export default CodeRender;