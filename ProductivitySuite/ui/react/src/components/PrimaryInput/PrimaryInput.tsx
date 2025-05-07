import { useEffect, useRef, useState } from "react";
import { Box, Button, styled, TextareaAutosize } from "@mui/material";
import ArrowUpwardIcon from "@mui/icons-material/ArrowUpward";
import styles from "./PrimaryInput.module.scss";
import { Stop } from "@mui/icons-material";
import { useAppDispatch, useAppSelector } from "@redux/store";
import {
  abortStream,
  conversationSelector,
  saveConversationtoDatabase,
  setSourceFiles,
  setSourceLinks,
} from "@redux/Conversation/ConversationSlice";
import AudioInput from "@components/PrimaryInput_AudioInput/AudioInput";
import PromptSelector from "@components/PrimparyInput_PromptSelector/PromptSelector";
import {
  NotificationSeverity,
  notify,
} from "@components/Notification/Notification";

const InputWrapper = styled(Box)(({ theme }) => ({
  ...theme.customStyles.primaryInput.inputWrapper,
}));

const TextInput = styled(TextareaAutosize)(({ theme }) => ({
  ...theme.customStyles.primaryInput.textInput,
}));

const CircleButton = styled(Button)(({ theme }) => ({
  ...theme.customStyles.primaryInput.circleButton,
}));

interface PrimaryInputProps {
  onSend: (messageContent: string) => Promise<void>;
  type?: string;
  home?: boolean;
}

const PrimaryInput: React.FC<PrimaryInputProps> = ({
  onSend,
  home = false,
}) => {
  const {
    onGoingResult,
    type,
    selectedConversationId,
    sourceLinks,
    sourceFiles,
  } = useAppSelector(conversationSelector);
  const dispatch = useAppDispatch();

  const [promptText, setPromptText] = useState("");
  const clearText = useRef(true);

  const isSummary = type === "summary";
  const isFaq = type === "faq";

  useEffect(() => {
    if (clearText.current) setPromptText("");
    clearText.current = true;
  }, [type, sourceFiles, sourceLinks]);

  const handleSubmit = () => {
    if (
      (isSummary || isFaq) &&
      sourceLinks &&
      sourceLinks.length === 0 &&
      sourceFiles &&
      sourceFiles.length === 0 &&
      promptText === ""
    ) {
      notify("Please provide content process", NotificationSeverity.ERROR);
      return;
    } else if (!(isSummary || isFaq) && promptText === "") {
      notify("Please provide a message", NotificationSeverity.ERROR);
      return;
    }

    let textToSend = promptText;
    onSend(textToSend);
    setPromptText("");
  };

  const handleKeyDown = (event: KeyboardEvent) => {
    if (!event.shiftKey && event.key === "Enter") {
      handleSubmit();
    }
  };

  const updatePromptText = (value: string) => {
    setPromptText(value);
    if (sourceFiles.length > 0) {
      clearText.current = false;
      dispatch(setSourceFiles([]));
    }
    if (sourceLinks.length > 0) {
      clearText.current = false;
      dispatch(setSourceLinks([]));
    }
  };

  const cancelStream = () => {
    dispatch(abortStream());
    if (type === "chat") {
      dispatch(
        saveConversationtoDatabase({
          conversation: { id: selectedConversationId },
        }),
      );
    }
  };

  const isActive = () => {
    if ((isSummary || isFaq) && sourceFiles.length > 0) {
      return true;
    } else if (promptText !== "") return true;
    return false;
  };

  const submitButton = () => {
    if (!onGoingResult) {
      return (
        <CircleButton
          className={`${styles.circleButton} ${isActive() ? "active" : ""}`}
          onClick={handleSubmit}
        >
          <ArrowUpwardIcon />
        </CircleButton>
      );
    }
    return;
  };

  const placeHolderCopy = () => {
    if (home && (isSummary || isFaq)) return "Enter text here or sources below";
    else return "Enter your message";
  };

  const renderInput = () => {
    if (!home && onGoingResult && (isSummary || isFaq)) {
      return (
        <Box className={styles.primaryInput}>
          <CircleButton className={styles.circleButton} onClick={cancelStream}>
            <Stop />
          </CircleButton>
        </Box>
      );
    } else if ((!home && !isSummary && !isFaq) || home) {
      return (
        <Box className={styles.inputWrapper}>
          <InputWrapper
            className={`${styles.primaryInput} ${promptText ? "active" : ""}`}
          >
            <TextInput
              className={`${styles.textAreaAuto} ${(isSummary || isFaq) && home ? styles.summaryInput : ""}`}
              minRows={1}
              maxRows={8}
              placeholder={placeHolderCopy()}
              value={promptText}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                updatePromptText(e.target.value)
              }
              onKeyDown={handleKeyDown}
              sx={{
                resize: "none",
                backgroundColor: "transparent",
              }}
            />

            <Box className={styles.inputActions}>
              <AudioInput setSearchText={updatePromptText} />

              {onGoingResult && (
                <CircleButton
                  className={styles.circleButton}
                  onClick={cancelStream}
                >
                  <Stop />
                </CircleButton>
              )}

              {submitButton()}
            </Box>
          </InputWrapper>

          {home && !isSummary && !isFaq && (
            <PromptSelector setSearchText={updatePromptText} />
          )}
        </Box>
      );
    }
  };

  return renderInput();
};

export default PrimaryInput;
