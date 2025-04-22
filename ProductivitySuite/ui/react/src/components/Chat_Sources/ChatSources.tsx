import { Box } from "@mui/material";
import { conversationSelector } from "@redux/Conversation/ConversationSlice";
import { useAppSelector } from "@redux/store";
import styles from "./ChatSources.module.scss";
import FileDispaly from "@components/File_Display/FileDisplay";

const ChatSources: React.FC = () => {
  const { sourceLinks, sourceFiles, sourceType } =
    useAppSelector(conversationSelector);
  const isWeb = sourceType === "web";
  const sourceElements = isWeb ? sourceLinks : sourceFiles;

  if (sourceLinks.length === 0 && sourceFiles.length === 0) return;

  const renderElements = () => {
    return sourceElements.map((element: any, elementIndex) => {
      return (
        <span key={elementIndex}>
          <FileDispaly index={elementIndex} file={element.file} isWeb={isWeb} />
        </span>
      );
    });
  };

  return <Box className={styles.sourceWrapper}>{renderElements()}</Box>;
};

export default ChatSources;
