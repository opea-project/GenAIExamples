import styles from "./codeRender.module.scss";
import { Light as SyntaxHighlighter } from "react-syntax-highlighter";
import {
  atomOneDark,
  atomOneLight,
} from "react-syntax-highlighter/dist/esm/styles/hljs";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import { IconButton, styled, Tooltip, useTheme } from "@mui/material";
import {
  NotificationSeverity,
  notify,
} from "@components/Notification/Notification";

const TitleBox = styled("div")(({ theme }) => ({
  background: theme.customStyles.code?.primary,
  color: theme.customStyles.code?.title,
}));

const StyledCode = styled(SyntaxHighlighter)(({ theme }) => ({
  background: theme.customStyles.code?.secondary + " !important",
}));

type CodeRenderProps = {
  cleanCode: React.ReactNode;
  language: string;
  inline: boolean;
};
const CodeRender = ({ cleanCode, language, inline }: CodeRenderProps) => {
  const theme = useTheme();

  const isClipboardAvailable = navigator.clipboard && window.isSecureContext;

  cleanCode = String(cleanCode)
    .replace(/\n$/, "")
    .replace(/^\s*[\r\n]/gm, ""); //right trim and remove empty lines from the input

  const copyText = (text: string) => {
    navigator.clipboard.writeText(text);
    notify("Copied to clipboard", NotificationSeverity.SUCCESS);
  };

  try {
    return inline ? (
      <code className={styles.inlineCode} style={{ fontStyle: "italic" }}>
        {cleanCode}
      </code>
    ) : (
      <div className={styles.code}>
        <TitleBox className={styles.codeHead}>
          <div className={styles.codeTitle}>
            {language || "language not detected"}
          </div>
          <div className={styles.codeActionGroup}>
            {isClipboardAvailable && (
              <Tooltip title="Copy" arrow placement="top">
                <IconButton onClick={() => copyText(cleanCode.toString())}>
                  <ContentCopyIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
          </div>
        </TitleBox>
        <StyledCode
          className={styles.codeHighlighterDiv}
          style={theme.palette.mode === "dark" ? atomOneLight : atomOneDark}
          children={cleanCode.toString()}
          wrapLongLines={true}
          language={language}
          PreTag="div"
        />
      </div>
    );
  } catch (err) {
    return <pre>{cleanCode}</pre>;
  }
};

export default CodeRender;
