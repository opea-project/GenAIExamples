import { AddCircle, Delete } from "@mui/icons-material";
import {
  IconButton,
  InputAdornment,
  List,
  ListItem,
  ListItemText,
  styled,
  TextField,
  useTheme,
} from "@mui/material";
import { useState } from "react";
import styles from "./WebInput.module.scss";
import { Language } from "@mui/icons-material";

import { useAppDispatch, useAppSelector } from "@redux/store";
import {
  conversationSelector,
  setSourceLinks,
} from "@redux/Conversation/ConversationSlice";

export const CustomTextInput = styled(TextField)(({ theme }) => ({
  ...theme.customStyles.webInput,
}));

export const AddIcon = styled(AddCircle)(({ theme }) => ({
  path: {
    fill: theme.customStyles.icon?.main,
  },
}));

const WebInput = () => {
  const [inputValue, setInputValue] = useState("");

  const theme = useTheme();

  const { sourceLinks } = useAppSelector(conversationSelector);
  const dispatch = useAppDispatch();

  const handleAdd = (newSource: string) => {
    if (!newSource) return;
    const prevSource = sourceLinks ?? [];
    dispatch(setSourceLinks([...prevSource, newSource]));
    setInputValue("");
  };

  const handleDelete = (index: number) => {
    const newSource = sourceLinks.filter((s: any, i: number) => i !== index);
    dispatch(setSourceLinks([...newSource]));
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && inputValue) {
      handleAdd(inputValue);
    }
  };

  const handleIconClick = () => {
    if (inputValue) {
      handleAdd(inputValue);
    }
  };

  const sourcesDisplay = () => {
    if (!sourceLinks || sourceLinks.length === 0) return;

    return (
      <List className={styles.dataList}>
        {sourceLinks.map((sourceItem: string, index: number) => (
          <ListItem
            sx={{ ...theme.customStyles.gradientBlock }}
            key={index}
            secondaryAction={
              <IconButton edge="end" onClick={() => handleDelete(index)}>
                <Delete />
              </IconButton>
            }
          >
            <ListItemText
              primary={
                sourceItem.length > 30
                  ? `${sourceItem.substring(0, 27)}...`
                  : sourceItem
              }
            />
            <Language />
          </ListItem>
        ))}
      </List>
    );
  };

  return (
    <div className={styles.inputWrapper}>
      <CustomTextInput
        id="web-input"
        value={inputValue}
        className={styles.searchInput}
        variant="outlined"
        placeholder="Enter a Web URL"
        onKeyDown={handleKeyPress}
        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
          setInputValue(e.target.value)
        }
        InputProps={{
          endAdornment: (
            <InputAdornment position="end" onClick={handleIconClick}>
              <AddIcon cursor={"pointer"} />
            </InputAdornment>
          ),
        }}
        fullWidth
      />

      {sourcesDisplay()}
    </div>
  );
};

export default WebInput;
