import {
  NotificationSeverity,
  notify,
} from "@components/Notification/Notification";
import { LinkedMenuItem, NavIcon } from "@components/SideBar/SideBar";
import { FileUploadOutlined } from "@mui/icons-material";
import { ListItemText } from "@mui/material";
import {
  conversationSelector,
  getAllConversations,
  saveConversationtoDatabase,
  uploadChat,
} from "@redux/Conversation/ConversationSlice";
import { useAppDispatch, useAppSelector } from "@redux/store";
import { userSelector } from "@redux/User/userSlice";
import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";

interface UploadChatProps {
  asideOpen: boolean;
  setAsideOpen: (open: boolean) => void;
}

const UploadChat: React.FC<UploadChatProps> = ({ asideOpen, setAsideOpen }) => {
  const dispatch = useAppDispatch();
  const { selectedConversationHistory } = useAppSelector(conversationSelector);

  const navigate = useNavigate();

  const fileInputRef = useRef<HTMLInputElement>(null);
  const newUpload = useRef<boolean>(false);

  useEffect(() => {
    if (newUpload.current && selectedConversationHistory) {
      saveConversation();
    }
  }, [selectedConversationHistory]);

  const handleUploadClick = (event: React.MouseEvent<HTMLLIElement>) => {
    event.preventDefault();
    event.currentTarget.blur(); // so we can apply the aria hidden attribute while menu closed
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const saveConversation = async () => {
    try {
      const resultAction = await dispatch(
        saveConversationtoDatabase({ conversation: { id: "" } }),
      );

      if (saveConversationtoDatabase.fulfilled.match(resultAction)) {
        const responseData = resultAction.payload;
        setAsideOpen(false);
        newUpload.current = false;
        notify(
          "Conversation successfully uploaded",
          NotificationSeverity.SUCCESS,
        );
        navigate(`/chat/${responseData}`);
      } else {
        newUpload.current = false;
        notify("Error saving conversation", NotificationSeverity.ERROR);
        console.error("Error saving conversation:", resultAction.error);
      }
    } catch (error) {
      newUpload.current = false;
      notify("Error saving conversation", NotificationSeverity.ERROR);
      console.error("An unexpected error occurred:", error);
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];

    if (file) {
      newUpload.current = true;
      const reader = new FileReader();

      reader.onload = () => {
        try {
          const fileContent = JSON.parse(reader.result as string);

          if (
            !fileContent.messages ||
            !fileContent.model ||
            !fileContent.token ||
            !fileContent.temperature ||
            fileContent.type
          ) {
            throw "Incorrect Format";
          }

          dispatch(
            uploadChat({
              messages: fileContent.messages,
              model: fileContent.model,
              token: fileContent.token,
              temperature: fileContent.temperature,
              type: fileContent.type,
            }),
          );
        } catch (error) {
          notify(
            `Error parsing JSON file: ${error}`,
            NotificationSeverity.ERROR,
          );
          console.error("Error parsing JSON file:", error);
        }
      };

      reader.readAsText(file);
    }
  };

  return (
    <>
      <LinkedMenuItem
        open={asideOpen}
        to=""
        sx={{ marginBottom: "2rem" }}
        onClick={handleUploadClick}
      >
        <NavIcon component={FileUploadOutlined} />
        <ListItemText>Upload Chat</ListItemText>
      </LinkedMenuItem>

      {/* Hidden file input */}
      <input
        type="file"
        accept=".json"
        ref={fileInputRef}
        style={{ display: "none" }}
        onChange={handleFileChange}
      />
    </>
  );
};

export default UploadChat;
