import { useEffect, useRef, useState } from "react";
import { styled } from "@mui/material/styles";
import { Link, useNavigate } from "react-router-dom";
import config from "@root/config";

import styles from "./Header.module.scss";
import { Box, IconButton, Tooltip, Typography } from "@mui/material";
import { SideBar } from "@components/SideBar/SideBar";
import DropDown from "@components/DropDown/DropDown";
import ThemeToggle from "@components/Header_ThemeToggle/ThemeToggle";
import ViewSidebarOutlinedIcon from "@mui/icons-material/ViewSidebarOutlined";
import Create from "@mui/icons-material/Create";
import Home from "@mui/icons-material/Home";
import ShareOutlinedIcon from "@mui/icons-material/ShareOutlined";
import FileDownloadOutlinedIcon from "@mui/icons-material/FileDownloadOutlined";
import ChatBubbleIcon from "@icons/ChatBubble";

import { useAppDispatch, useAppSelector } from "@redux/store";
import { userSelector } from "@redux/User/userSlice";
import {
  Message,
  MessageRole,
  UseCase,
} from "@redux/Conversation/Conversation";
import {
  conversationSelector,
  setUseCase,
} from "@redux/Conversation/ConversationSlice";
import DownloadChat from "@components/Header_DownloadChat/DownloadChat";

interface HeaderProps {
  asideOpen: boolean;
  setAsideOpen: (open: boolean) => void;
  chatView?: boolean;
  historyView?: boolean;
  dataView?: boolean;
}

interface AvailableUseCase {
  name: string;
  value: string;
}

const HeaderWrapper = styled(Box)(({ theme }) => ({
  ...theme.customStyles.header,
}));

const Header: React.FC<HeaderProps> = ({
  asideOpen,
  setAsideOpen,
  chatView,
  historyView,
  dataView,
}) => {
  const { companyName } = config;

  const sideBarRef = useRef<HTMLDivElement>(null);
  const toggleRef = useRef<HTMLDivElement>(null);

  const navigate = useNavigate();

  const dispatch = useAppDispatch();
  const { role, name } = useAppSelector(userSelector);
  const { selectedConversationHistory, type } =
    useAppSelector(conversationSelector);

  const [currentTopic, setCurrentTopic] = useState<string>("");

  useEffect(() => {
    if (
      !selectedConversationHistory ||
      selectedConversationHistory.length === 0
    ) {
      setCurrentTopic("");
      return;
    }
    const firstUserPrompt = selectedConversationHistory.find(
      (message: Message) => message.role === MessageRole.User,
    );
    if (firstUserPrompt) setCurrentTopic(firstUserPrompt.content);
  }, [selectedConversationHistory]);

  const handleChange = (value: string) => {
    dispatch(setUseCase(value));
  };

  const newChat = () => {
    navigate("/");
    setAsideOpen(false);
  };

  const handleClickOutside = (event: MouseEvent) => {
    if (
      sideBarRef.current &&
      toggleRef.current &&
      !sideBarRef.current.contains(event.target as Node) &&
      !toggleRef.current.contains(event.target as Node)
    ) {
      setAsideOpen(false);
    }
  };

  useEffect(() => {
    if (asideOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      return () =>
        document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [asideOpen]);

  const userDetails = () => {
    return (
      <Box display="flex" flexDirection="column">
        <div>{name}</div>
      </Box>
    );
  };

  const getTitle = () => {
    if (historyView)
      return (
        <Box className={styles.viewContext}>
          <ChatBubbleIcon />
          &nbsp; Your Chat History
        </Box>
      );

    if (dataView)
      return (
        <Typography className={styles.viewContext}>
          Data Source Management
        </Typography>
      );

    if (chatView) {
      if (type !== "chat" && !currentTopic) {
        return (
          <Box
            className={`${styles.titleWrap} ${styles.viewContext} ${styles.capitalize}`}
          >
            <Typography noWrap>{type}</Typography>
          </Box>
        );
      } else {
        return (
          <Box className={`${styles.titleWrap} ${styles.viewContext}`}>
            <ChatBubbleIcon />
            <Typography noWrap title={currentTopic}>
              &nbsp; {currentTopic}
            </Typography>
          </Box>
        );
      }
    }
  };

  return (
    <HeaderWrapper component="header" className={styles.header}>
      <Box
        ref={toggleRef}
        className={`${styles.sideWrapper} ${asideOpen ? styles.sideWrapperOpen : ""}`}
      >
        <Tooltip
          title={asideOpen ? "Close Sidebar" : "Open Sidebar"}
          arrow
          slotProps={{
            popper: {
              modifiers: [{ name: "offset", options: { offset: [10, 0] } }],
            },
          }}
        >
          <IconButton onClick={() => setAsideOpen(!asideOpen)}>
            <ViewSidebarOutlinedIcon />
          </IconButton>
        </Tooltip>
        <Box className={styles.chatWrapper}>
          {/* <span className={styles.chatCopy}>New Chat</span> */}
          <Tooltip title="New Chat" arrow>
            <IconButton onClick={newChat}>
              <Home />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      <Box ref={sideBarRef}>
        <SideBar
          asideOpen={asideOpen}
          setAsideOpen={setAsideOpen}
          userDetails={userDetails}
        />
      </Box>

      <Box className={styles.rightSide}>
        <div>
          <span className={styles.companyName}>{companyName}</span>
        </div>

        {getTitle()}

        <Box className={styles.rightActions}>
          {chatView && (
            <>
              {/* <Link to={'/'} >
                                <IconButton><Create/></IconButton>
                            </Link> */}

              <DownloadChat />
            </>
          )}

          {/* {chatView && <IconButton onClick={() => { }}><ShareOutlinedIcon /></IconButton>} */}

          <Box className={styles.desktopUser}>
            <ThemeToggle />
          </Box>

          <Box className={styles.desktopUser}>{userDetails()}</Box>
        </Box>
      </Box>
    </HeaderWrapper>
  );
};

export default Header;
