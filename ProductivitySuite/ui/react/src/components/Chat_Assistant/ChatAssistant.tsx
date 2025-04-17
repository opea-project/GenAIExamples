import React, { useEffect, useRef, useState } from "react";

import styles from "./ChatAssistant.module.scss";
import {
  Button,
  Typography,
  IconButton,
  Box,
  styled,
  Tooltip,
} from "@mui/material";
import { AtomIcon } from "@icons/Atom";
import ThumbUpIcon from "@mui/icons-material/ThumbUp";
import ThumbUpOutlinedIcon from "@mui/icons-material/ThumbUpOutlined";
import ThumbDownIcon from "@mui/icons-material/ThumbDown";
import ThumbDownOutlinedIcon from "@mui/icons-material/ThumbDownOutlined";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import EditNoteIcon from "@mui/icons-material/EditNote";
import ChatSettingsModal from "@components/Chat_SettingsModal/ChatSettingsModal";

import {
  NotificationSeverity,
  notify,
} from "@components/Notification/Notification";
import { ChatMessageProps, Message } from "@redux/Conversation/Conversation";
import ChatMarkdown from "@components/Chat_Markdown/ChatMarkdown";
import { useAppDispatch, useAppSelector } from "@redux/store";
import {
  conversationSelector,
  saveConversationtoDatabase,
  setSelectedConversationHistory,
} from "@redux/Conversation/ConversationSlice";
import WaitingIcon from "@icons/Waiting";

const CancelStyle = styled(Button)(({ theme }) => ({
  ...theme.customStyles.actionButtons.delete,
}));

const SaveStyle = styled(Button)(({ theme }) => ({
  ...theme.customStyles.actionButtons.solid,
}));

const ChatAssistant: React.FC<ChatMessageProps> = ({
  message,
  pending = false,
}) => {
  const dispatch = useAppDispatch();
  const {
    onGoingResult,
    selectedConversationHistory,
    selectedConversationId,
    type,
  } = useAppSelector(conversationSelector);

  const [currentMessage, setCurrentMessage] = useState<Message>(message);
  const [editResponse, setEditResponse] = useState(false);
  const responseRef = useRef(currentMessage.content);
  const [disabledSave, setDisabledSave] = useState(false);
  const [inputHeight, setInputHeight] = useState<Number>(0);
  const heightCheck = useRef<HTMLDivElement>(null);
  const isClipboardAvailable = navigator.clipboard && window.isSecureContext;

  useEffect(() => {
    setCurrentMessage(message);
  }, [message]);

  const assistantMessage = currentMessage.content ?? "";

  // const [feedback, setFeedback] = useState<boolean | null>(
  //     currentMessage.feedback?.is_thumbs_up === true ? true : currentMessage.feedback?.is_thumbs_up === false ? false : null
  // );

  // const submitFeedback = (thumbsUp: boolean) => {
  //     setFeedback(thumbsUp);
  //     notify('Feedback Submitted', NotificationSeverity.SUCCESS);
  //     // MessageService.submitFeedback({ id: currentMessage.message_id, feedback: {is_thumbs_up: thumbsUp}, useCase: selectedUseCase.use_case });
  // };

  const copyText = (text: string) => {
    navigator.clipboard.writeText(text);
    notify("Copied to clipboard", NotificationSeverity.SUCCESS);
  };

  const modifyResponse = () => {
    if (heightCheck.current) {
      let updateHeight = heightCheck.current.offsetHeight;
      setInputHeight(updateHeight);
      setEditResponse(true);
    }
  };

  const updateResponse = (response: string) => {
    responseRef.current = response;
    setDisabledSave(response === "");
  };

  const saveResponse = () => {
    const convoClone: Message[] = selectedConversationHistory.map(
      (messageItem) => {
        if (messageItem.time === currentMessage.time) {
          return {
            ...messageItem,
            content: responseRef.current,
          };
        }
        return messageItem;
      },
    );

    dispatch(setSelectedConversationHistory(convoClone));
    dispatch(
      saveConversationtoDatabase({
        conversation: { id: selectedConversationId },
      }),
    );

    setInputHeight(0);
    setEditResponse(false);
    setDisabledSave(false);
  };

  const cancelResponse = () => {
    setEditResponse(false);
  };

  const displayCurrentMessage = () => {
    if (currentMessage.content) {
      if (editResponse) {
        return (
          <div>
            <textarea
              style={{ height: inputHeight + "px" }}
              className={styles.textedit}
              defaultValue={assistantMessage}
              onChange={(e) => updateResponse(e.target.value)}
            ></textarea>

            <SaveStyle
              disabled={disabledSave}
              sx={{ marginRight: "0.5rem" }}
              onClick={saveResponse}
            >
              Save
            </SaveStyle>
            <CancelStyle onClick={cancelResponse}>Cancel</CancelStyle>
          </div>
        );
      } else {
        return (
          <Box ref={heightCheck}>
            <ChatMarkdown content={assistantMessage} />
          </Box>
        );
      }
    } else {
      return (
        <span>
          Generating response
          <span className={styles.ellipsis}>
            <span>.</span>
            <span>.</span>
            <span>.</span>
          </span>
        </span>
      );
    }
  };

  const displayMessageActions = () => {
    if (onGoingResult) return;

    return (
      <Box display="flex" flexDirection="row">
        {/*TODO: feedback support */}
        {/* <IconButton onClick={() => submitFeedback(true)}>
                        {feedback === null || feedback === false ? (
                            <ThumbUpOutlinedIcon />
                        ) : (
                            <ThumbUpIcon />
                        )}
                    </IconButton>

                    <IconButton onClick={() => submitFeedback(false)}>
                        {feedback === null || feedback === true ? (
                            <ThumbDownOutlinedIcon />
                        ) : (
                            <ThumbDownIcon />
                        )}
                    </IconButton> */}

        <ChatSettingsModal />

        {isClipboardAvailable && (
          <Tooltip title="Copy" arrow>
            <IconButton onClick={() => copyText(assistantMessage)}>
              <ContentCopyIcon />
            </IconButton>
          </Tooltip>
        )}

        {type === "chat" && (
          <Tooltip title="Edit response" arrow>
            <IconButton onClick={modifyResponse}>
              <EditNoteIcon />
            </IconButton>
          </Tooltip>
        )}
      </Box>
    );
  };

  return (
    <div className={styles.chatReply}>
      <div className={styles.icon}>
        <AtomIcon />
      </div>

      <div className={styles.chatPrompt}>
        {displayCurrentMessage()}

        {!pending && displayMessageActions()}
      </div>
    </div>
  );
};

export default ChatAssistant;
