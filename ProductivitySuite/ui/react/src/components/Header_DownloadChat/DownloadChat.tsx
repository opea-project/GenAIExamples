import { FileDownloadOutlined } from "@mui/icons-material";
import { IconButton, Tooltip } from "@mui/material";
import { conversationSelector } from "@redux/Conversation/ConversationSlice";
import { useAppSelector } from "@redux/store";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

const DownloadChat = () => {
  const { selectedConversationHistory, type, model, token, temperature } =
    useAppSelector(conversationSelector);
  const [url, setUrl] = useState<string | undefined>(undefined);
  const [fileName, setFileName] = useState<string>("");

  const safeBtoa = (str: string) => {
    const encoder = new TextEncoder();
    const uint8Array = encoder.encode(str);
    let binaryString = "";
    for (let i = 0; i < uint8Array.length; i++) {
      binaryString += String.fromCharCode(uint8Array[i]);
    }
    return btoa(binaryString);
  };

  useEffect(() => {
    if (selectedConversationHistory.length === 0) return;

    //TODO: if we end up with a systemPrompt for code change this
    const userPromptIndex = type === "code" ? 0 : 1;

    const conversationObject = {
      model,
      token,
      temperature,
      messages: [...selectedConversationHistory],
      type,
    };

    const newUrl = `data:application/json;charset=utf-8;base64,${safeBtoa(JSON.stringify(conversationObject))}`;

    if (
      selectedConversationHistory &&
      selectedConversationHistory.length > 0 &&
      selectedConversationHistory[userPromptIndex]
    ) {
      const firstPrompt = selectedConversationHistory[userPromptIndex].content; // Assuming content is a string
      if (firstPrompt) {
        const newFileName = firstPrompt.split(" ").slice(0, 4).join("_");
        setUrl(newUrl);
        setFileName(newFileName.toLowerCase());
      }
    }
  }, [selectedConversationHistory]);

  //TODO: only support download for chat for now
  return (
    url &&
    type === "chat" && (
      <Link
        download={`${fileName}.json`}
        to={url}
        target="_blank"
        rel="noopener noreferrer"
      >
        <Tooltip title="Download" arrow>
          <IconButton>
            <FileDownloadOutlined />
          </IconButton>
        </Tooltip>
      </Link>
    )
  );
};

export default DownloadChat;
