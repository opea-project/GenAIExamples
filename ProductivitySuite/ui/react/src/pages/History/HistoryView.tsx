import {
  Box,
  Checkbox,
  FormControlLabel,
  List,
  ListItem,
  Typography,
  Link,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { useState } from "react";
import styles from "./HistoryView.module.scss";

import { Link as RouterLink } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "@redux/store";
import {
  conversationSelector,
  deleteConversation,
  deleteConversations,
} from "@redux/Conversation/ConversationSlice";
import { Conversation } from "@redux/Conversation/Conversation";
import { userSelector } from "@redux/User/userSlice";
import SearchInput from "@components/SearchInput/SearchInput";
import {
  DeleteButton,
  SolidButton,
  TextButton,
} from "@root/shared/ActionButtons";

interface HistoryViewProps {
  shared: boolean;
}

const HistoryView: React.FC<HistoryViewProps> = ({ shared }) => {
  const dispatch = useAppDispatch();
  const { name } = useAppSelector(userSelector);

  const theme = useTheme();

  const { conversations, sharedConversations } =
    useAppSelector(conversationSelector);

  const [historyList, setHistoryList] = useState<Conversation[]>(
    shared ? sharedConversations : conversations,
  );
  const [selectActive, setSelectActive] = useState(false);
  const [selectAll, setSelectAll] = useState(false);
  const [checkedItems, setCheckedItems] = useState<Record<string, boolean>>({});

  const convertTime = (timestamp: number) => {
    const now = Math.floor(Date.now() / 1000);
    const diffInSeconds = now - timestamp;

    const diffInMinutes = Math.floor(diffInSeconds / 60);
    const diffInHours = Math.floor(diffInSeconds / 3600);
    const diffInDays = Math.floor(diffInSeconds / 86400);

    if (diffInDays > 0) {
      return `${diffInDays} day${diffInDays > 1 ? "s" : ""} ago`;
    } else if (diffInHours > 0) {
      return `${diffInHours} hour${diffInHours > 1 ? "s" : ""} ago`;
    } else {
      return `${diffInMinutes} minute${diffInMinutes > 1 ? "s" : ""} ago`;
    }
  };

  const handleCheckboxChange = (conversationId: string) => {
    setCheckedItems((prev) => ({
      ...prev,
      [conversationId]: !prev[conversationId],
    }));
  };

  const displayHistory = () => {
    return historyList.map((conversation: Conversation) => {
      const isChecked = !!checkedItems[conversation.id];

      const itemText = (
        <>
          <Typography className={styles.title} variant="h2">
            {conversation.first_query}
          </Typography>
          {/* TODO: timestamp for all conversations? */}
          {/* <Typography variant="caption">Last message {convertTime(conversation.updated_at)}</Typography> */}
        </>
      );

      const controlCheckBox = (
        <Checkbox
          id={`check_${conversation.id}`}
          onChange={() => handleCheckboxChange(conversation.id)}
          checked={isChecked}
        />
      );

      return (
        <Box
          className={styles.historyItem}
          component={ListItem}
          key={conversation.id}
        >
          {selectActive ? (
            <FormControlLabel
              sx={{ ...theme.customStyles.gradientBlock }}
              className={styles.historyLink}
              control={controlCheckBox}
              label={itemText}
            />
          ) : (
            <Link
              component={RouterLink}
              to={`/chat/${conversation.id}`}
              sx={{ ...theme.customStyles.gradientBlock }}
              className={styles.historyLink}
            >
              {/* body1 Typography is automatically applied in label above, added here to match for spacing */}
              <Box>{itemText}</Box>
            </Link>
          )}
        </Box>
      );
    });
  };

  const cancelSelect = () => {
    setSelectActive(false);
    setSelectAll(false);
    setCheckedItems({});
  };

  const deleteSelected = () => {
    setSelectActive(false);

    let ids = [];
    for (const [key, value] of Object.entries(checkedItems)) {
      if (value === true) {
        ids.push(key);
      }
    }

    if (ids.length > 0) {
      //update current state
      setHistoryList((prev) =>
        prev.filter((conversation) => !checkedItems[conversation.id]),
      );
      dispatch(
        deleteConversations({ user: name, conversationIds: ids, useCase: "" }),
      );
    }
  };

  const handleSelectAll = () => {
    const newSelectAll = !selectAll;
    setSelectAll(newSelectAll);

    // Add all items' checked state
    const updatedCheckedItems: Record<string, boolean> = {};
    historyList.forEach((conversation) => {
      updatedCheckedItems[conversation.id] = newSelectAll;
    });

    setCheckedItems(updatedCheckedItems);
  };

  const handleSearch = (value: string) => {
    const filteredList = shared ? sharedConversations : conversations;
    const searchResults = filteredList.filter((conversation: Conversation) =>
      conversation.first_query?.toLowerCase().includes(value.toLowerCase()),
    );
    setHistoryList(
      value ? searchResults : shared ? sharedConversations : conversations,
    );
  };

  return (
    <div className={styles.historyView}>
      <SearchInput handleSearch={handleSearch} />

      <div className={styles.historyListWrapper}>
        <Typography>
          You have {historyList.length} previous chat
          {historyList.length > 1 && "s"}
        </Typography>

        {historyList.length > 0 && (
          <div className={styles.actions}>
            {selectActive ? (
              <TextButton onClick={() => handleSelectAll()}>
                Select All
              </TextButton>
            ) : (
              <TextButton onClick={() => setSelectActive(true)}>
                Select
              </TextButton>
            )}

            {selectActive && (
              <>
                <SolidButton onClick={() => cancelSelect()}>Cancel</SolidButton>
                <DeleteButton onClick={() => deleteSelected()}>
                  Delete Selected
                </DeleteButton>
              </>
            )}
          </div>
        )}
      </div>

      <List>{displayHistory()}</List>
    </div>
  );
};

export default HistoryView;
