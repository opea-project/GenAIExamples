import {
  Box,
  Button,
  IconButton,
  List,
  ListItem,
  styled,
  Tooltip,
} from "@mui/material";
import { deletePrompt, promptSelector } from "@redux/Prompt/PromptSlice";
import { useAppDispatch, useAppSelector } from "@redux/store";
import { useEffect, useRef, useState } from "react";
import { Delete, ExpandMore } from "@mui/icons-material";
import styles from "./PromptSelector.module.scss";

const ExpandButton = styled(Button)(({ theme }) => ({
  ...theme.customStyles.promptExpandButton,
}));

const PromptButton = styled(Button)(({ theme }) => ({
  ...theme.customStyles.promptButton,
}));

const PromptListWrapper = styled(Box)(({ theme }) => ({
  ...theme.customStyles.promptListWrapper,
}));

interface PromptSelectorProps {
  setSearchText: (value: string) => void;
}

const PromptSelector: React.FC<PromptSelectorProps> = ({ setSearchText }) => {
  const dispatch = useAppDispatch();
  const { prompts } = useAppSelector(promptSelector);
  const [showPrompts, setShowPrompts] = useState<boolean>(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!showPrompts) return;

    const handleClickOutside = (event: MouseEvent) => {
      if (
        wrapperRef.current &&
        !wrapperRef.current.contains(event.target as Node)
      ) {
        setShowPrompts(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showPrompts]);

  const handleDelete = (id: string, text: string) => {
    dispatch(deletePrompt({ promptId: id, promptText: text }));
  };

  const handleSelect = (promptText: string) => {
    setSearchText(promptText);
    setShowPrompts(false);
  };

  return (
    prompts &&
    prompts.length > 0 && (
      <Box ref={wrapperRef} className={styles.promptsWrapper}>
        <Tooltip title={!showPrompts ? "Show suggestions" : ""} arrow>
          <ExpandButton
            className={`${styles.expand} ${showPrompts ? styles.open : ""}`}
            onClick={() => setShowPrompts(!showPrompts)}
          >
            <ExpandMore fontSize="small" />
          </ExpandButton>
        </Tooltip>

        <PromptListWrapper
          className={`${styles.promptsListWrapper} ${showPrompts ? styles.open : ""}`}
        >
          <List className={styles.promptsList}>
            {prompts?.map((prompt, promptIndex) => {
              return (
                <ListItem key={promptIndex}>
                  <PromptButton
                    className={styles.promptText}
                    onClick={() => handleSelect(prompt.prompt_text)}
                  >
                    <span>{prompt.prompt_text}</span>
                  </PromptButton>

                  <Tooltip title="Remove suggestion" arrow>
                    <IconButton
                      className={styles.delete}
                      onClick={() =>
                        handleDelete(prompt.id, prompt.prompt_text)
                      }
                    >
                      <Delete />
                    </IconButton>
                  </Tooltip>
                </ListItem>
              );
            })}
          </List>
        </PromptListWrapper>
      </Box>
    )
  );
};

export default PromptSelector;
