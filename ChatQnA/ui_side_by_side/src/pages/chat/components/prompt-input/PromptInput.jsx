import "./prompt-input.scss";

import CloseIcon from "@mui/icons-material/Close";
import SendIcon from "@mui/icons-material/Send";
import UploadIcon from "@mui/icons-material/UploadFile";
import { CircularProgress, IconButton, TextField, Tooltip } from "@mui/material";
import { bool, func } from "prop-types";
import { useEffect, useState } from "react";

const PromptInput = ({
  isDisabled,
  isClearChatHistoryBtnDisabled,
  isUploading,
  onConfirmPrompt,
  onClearChatBtnClick,
  onUploadBtnClick,
}) => {
  const [promptTextFieldValue, setPromptTextFieldValue] = useState("");
  const [isSendBtnDisabled, setIsSendBtnDisabled] = useState(true);

  useEffect(() => {
    setIsSendBtnDisabled(promptTextFieldValue.length <= 0);
  }, [promptTextFieldValue]);

  const onPromptTextFieldChange = (event) => {
    setPromptTextFieldValue(event.target.value);
  };

  const onKeyDownHandler = (event) => {
    if (promptTextFieldValue.length > 0 && event.code === "Enter") {
      setPromptTextFieldValue("");
      onConfirmPrompt(promptTextFieldValue);
    }
  };

  const onSendPromptBtnPress = () => {
    setPromptTextFieldValue("");
    onConfirmPrompt(promptTextFieldValue);
  };

  return (
    <div className="prompt-input-wrapper">
      <TextField
        value={promptTextFieldValue}
        disabled={isDisabled}
        type="text"
        placeholder={isDisabled ? "Preparing answer..." : "What's on your mind?"}
        size="small"
        id="prompt-input-text-field"
        name="prompt-input-text-field"
        inputProps={{
          style: { fontFamily: "IntelOneText" },
        }}
        onChange={onPromptTextFieldChange}
        onKeyDown={onKeyDownHandler}
      />
      <Tooltip title="Send your question" placement="bottom">
        <span>
          <IconButton
            className="send-btn"
            disabled={isSendBtnDisabled}
            onClick={onSendPromptBtnPress}
          >
            <SendIcon />
          </IconButton>
        </span>
      </Tooltip>
      <Tooltip title="Clear chat history" placement="bottom">
        <span>
          <IconButton
            size="medium"
            disabled={isClearChatHistoryBtnDisabled}
            onClick={onClearChatBtnClick}
          >
            <CloseIcon />
          </IconButton>
        </span>
      </Tooltip>
      <Tooltip title={isUploading ? "Uploading..." : "Upload your file"} placement="bottom">
        {isUploading ? (
          <CircularProgress size={24} className="upload-loader" />
        ) : (
          <IconButton size="medium" onClick={onUploadBtnClick}>
            <UploadIcon />
          </IconButton>
        )}
      </Tooltip>
    </div>
  );
};

PromptInput.propTypes = {
  isDisabled: bool,
  isClearChatHistoryBtnDisabled: bool,
  isUploading: bool,
  onConfirmPrompt: func,
  onClearChatBtnClick: func,
  onUploadBtnClick: func,
};

export default PromptInput;
