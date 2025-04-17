import { IconButton, styled, Tooltip } from "@mui/material";
import React from "react";
import styles from "./ChatUser.module.scss";
import AddCircle from "@mui/icons-material/AddCircle";
import { useAppDispatch } from "@redux/store";
import { addPrompt } from "@redux/Prompt/PromptSlice";
import ChatMarkdown from "@components/Chat_Markdown/ChatMarkdown";

interface ChatUserProps {
  content: string;
}

const UserInput = styled("div")(({ theme }) => ({
  background: theme.customStyles.user?.main,
}));

const AddIcon = styled(AddCircle)(({ theme }) => ({
  path: {
    fill: theme.customStyles.icon?.main,
  },
}));

const ChatUser: React.FC<ChatUserProps> = ({ content }) => {
  const dispatch = useAppDispatch();

  const sharePrompt = () => {
    dispatch(addPrompt({ promptText: content }));
  };

  return (
    <div className={styles.userWrapper}>
      <UserInput className={styles.userPrompt}>
        <ChatMarkdown content={content} />
      </UserInput>
      <Tooltip title="Save prompt" arrow>
        <IconButton className={styles.addIcon} onClick={sharePrompt}>
          <AddIcon />
        </IconButton>
      </Tooltip>
    </div>
  );
};

export default ChatUser;
