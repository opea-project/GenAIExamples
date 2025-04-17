import { Mic } from "@mui/icons-material";
import { Button, styled, Tooltip } from "@mui/material";
import { useState } from "react";
import styles from "@components/PrimaryInput/PrimaryInput.module.scss";
import {
  NotificationSeverity,
  notify,
} from "@components/Notification/Notification";
import { useAppSelector } from "@redux/store";
import { conversationSelector } from "@redux/Conversation/ConversationSlice";
import ProgressIcon from "@components/ProgressIcon/ProgressIcon";

interface AudioInputProps {
  setSearchText: (value: string) => void;
}

const AudioButton = styled(Button)(({ theme }) => ({
  ...theme.customStyles.audioEditButton,
}));

const AudioInput: React.FC<AudioInputProps> = ({ setSearchText }) => {
  const isSpeechRecognitionSupported =
    ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) &&
    window.isSecureContext;

  const { type } = useAppSelector(conversationSelector);
  const [isListening, setIsListening] = useState(false);

  const handleMicClick = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = "en-US"; // Set language for recognition
    recognition.interimResults = false; // Only process final results

    if (!isListening) {
      setIsListening(true);
      recognition.start();

      recognition.onresult = (event: SpeechRecognitionEvent) => {
        const transcript = event.results[0][0].transcript;
        setSearchText(transcript); // Update search text with recognized speech
        setIsListening(false);
      };

      recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
        notify(
          `Speech recognition error:${event.error}`,
          NotificationSeverity.ERROR,
        );
        console.error("Speech recognition error:", event);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };
    } else {
      recognition.stop();
      setIsListening(false);
    }
  };

  const renderMic = () => {
    if (type === "summary" || type === "faq" || !isSpeechRecognitionSupported)
      return <></>;

    if (isListening) {
      return <ProgressIcon />;
    } else {
      return (
        <Tooltip title="Voice mode" arrow placement="top">
          <AudioButton className={styles.circleButton}>
            <Mic className={styles.micIcon} onClick={handleMicClick} />
          </AudioButton>
        </Tooltip>
      );
    }
  };

  return renderMic();
};

export default AudioInput;
