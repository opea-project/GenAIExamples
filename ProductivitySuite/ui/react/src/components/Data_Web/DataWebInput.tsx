import ProgressIcon from "@components/ProgressIcon/ProgressIcon";
import {
  CustomTextInput,
  AddIcon,
} from "@components/Summary_WebInput/WebInput";
import styles from "@components/Summary_WebInput/WebInput.module.scss";
import { Box, InputAdornment } from "@mui/material";
import {
  conversationSelector,
  submitDataSourceURL,
} from "@redux/Conversation/ConversationSlice";
import { useAppDispatch, useAppSelector } from "@redux/store";
import { useEffect, useState } from "react";

const DataWebInput = () => {
  const { dataSourceUrlStatus } = useAppSelector(conversationSelector);
  const [inputValue, setInputValue] = useState("");
  const [uploading, setUploading] = useState(false);
  const dispatch = useAppDispatch();

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && inputValue) {
      handleAdd(inputValue);
    }
  };

  const handleAdd = (newSource: string) => {
    dispatch(submitDataSourceURL({ link_list: [newSource] }));
    setInputValue("");
  };

  const handleIconClick = () => {
    if (inputValue) {
      handleAdd(inputValue);
    }
  };

  useEffect(() => {
    setUploading(dataSourceUrlStatus === "pending");
  }, [dataSourceUrlStatus]);

  return (
    <Box className={styles.inputWrapper}>
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
          endAdornment: !uploading ? (
            <InputAdornment position="end" onClick={handleIconClick}>
              <AddIcon cursor={"pointer"} />
            </InputAdornment>
          ) : (
            <InputAdornment position="end">
              <ProgressIcon />
            </InputAdornment>
          ),
        }}
        fullWidth
      />
    </Box>
  );
};

export default DataWebInput;
