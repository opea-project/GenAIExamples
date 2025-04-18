import { Link } from "react-router-dom";
import { useTheme } from "@mui/material/styles";
import { SvgIconProps } from "@mui/material/SvgIcon";
import styles from "./SideBar.module.scss";
import LogoutIcon from "@mui/icons-material/Logout";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import AdminPanelSettingsIcon from "@mui/icons-material/AdminPanelSettings";
import DatabaseIcon from "@icons/Database";
import RecentIcon from "@icons/Recent";
import PeopleOutlineOutlinedIcon from "@mui/icons-material/PeopleOutlineOutlined";
import FileUploadOutlinedIcon from "@mui/icons-material/FileUploadOutlined";
import { Box, ListItemText, MenuItem, MenuList } from "@mui/material";

import { JSX, MouseEventHandler } from "react";
import ThemeToggle from "@components/Header_ThemeToggle/ThemeToggle";

import { useAppSelector } from "@redux/store";
import { userSelector } from "@redux/User/userSlice";
import {
  conversationSelector,
  newConversation,
} from "@redux/Conversation/ConversationSlice";
import { Conversation } from "@redux/Conversation/Conversation";
import { useKeycloak } from "@react-keycloak/web";
import UploadChat from "@components/SideBar_UploadChat/UploadChat";
import { KeyboardBackspace } from "@mui/icons-material";
import { useDispatch } from "react-redux";

interface SideBarProps {
  asideOpen: boolean;
  setAsideOpen?: (open: boolean) => void;
  userDetails?: () => JSX.Element;
}

interface NavIconProps {
  component: React.ComponentType<SvgIconProps>;
}

export const NavIcon: React.FC<NavIconProps> = ({
  component: ListItemIcon,
}) => {
  const theme = useTheme();
  return <ListItemIcon sx={{ fill: theme.customStyles.icon?.main }} />;
};

const EmptySvg: React.FC = () => {
  return (
    <svg
      className={styles.emptySvg}
      viewBox="0 0 24 24"
      width={"24px"}
      height={"24px"}
    ></svg>
  );
};

interface LinkedMenuItemProps {
  to: string;
  children: React.ReactNode;
  onClick?: MouseEventHandler;
  sx?: any;
  open?: boolean;
}

export const LinkedMenuItem: React.FC<LinkedMenuItemProps> = ({
  to,
  children,
  onClick,
  sx,
  open,
}) => {
  return (
    <MenuItem sx={sx}>
      <Link
        to={to}
        onClick={onClick}
        tabIndex={open ? 0 : -1}
        aria-hidden={!open}
      >
        {children}
      </Link>
    </MenuItem>
  );
};

const SideBar: React.FC<SideBarProps> = ({
  asideOpen,
  setAsideOpen = () => {},
  userDetails,
}) => {
  const dispatch = useDispatch();
  const theme = useTheme();

  const { keycloak } = useKeycloak();
  const { role } = useAppSelector(userSelector);
  const { conversations } = useAppSelector(conversationSelector);

  const asideBackgroundColor = {
    backgroundColor: theme.customStyles.aside?.main,
  };

  const dividerColor = {
    borderBottom: `1px solid ${theme.customStyles.customDivider?.main}`,
  };

  const handleLinkedMenuItemClick = (
    event: React.MouseEvent<HTMLLIElement>,
  ) => {
    event.currentTarget.blur(); // so we can apply the aria hidden attribute while menu closed
    dispatch(newConversation(true));
    setAsideOpen(false);
  };

  const history = (type: Conversation[]) => {
    if (type && type.length > 0) {
      return type.map((conversation: Conversation, index: number) => {
        if (index > 2) return null;
        return (
          <LinkedMenuItem
            open={asideOpen}
            to={`/chat/${conversation.id}`}
            key={conversation.id}
            onClick={handleLinkedMenuItemClick}
          >
            <NavIcon component={EmptySvg} />
            <ListItemText>{conversation.first_query}</ListItemText>
          </LinkedMenuItem>
        );
      });
    }
  };

  const handleLogout = () => {
    keycloak.logout();
    setAsideOpen(false);
  };

  const viewAll = (path: string) => {
    if (conversations.length > 0) {
      return (
        <LinkedMenuItem
          open={asideOpen}
          to={path}
          sx={{ marginBottom: "2rem" }}
          onClick={handleLinkedMenuItemClick}
        >
          <NavIcon component={EmptySvg} />
          <ListItemText className={styles.viewAll}>
            View All <KeyboardBackspace fontSize="small" />
          </ListItemText>
        </LinkedMenuItem>
      );
    } else {
      return (
        <MenuItem>
          <NavIcon component={EmptySvg} />
          <ListItemText>No recent conversations</ListItemText>
        </MenuItem>
      );
    }
  };

  return (
    <aside
      className={`${styles.aside} ${asideOpen ? styles.open : ""}`}
      style={asideBackgroundColor}
    >
      <MenuList className={styles.asideContent}>
        <UploadChat asideOpen={asideOpen} setAsideOpen={setAsideOpen} />

        <MenuItem>
          <NavIcon component={RecentIcon} />
          <ListItemText>Recents</ListItemText>
        </MenuItem>

        {history(conversations)}

        {viewAll("/history")}

        {/* <MenuItem>
                    <NavIcon component={PeopleOutlineOutlinedIcon} />
                    <ListItemText>Shared</ListItemText>
                </MenuItem> */}

        {/* {history(allSharedConversations)} */}

        {/* {viewAll('/shared')} */}

        <li className={`${styles.divider}`} style={dividerColor}></li>

        {role === "Admin" && (
          <>
            <LinkedMenuItem
              open={asideOpen}
              to="/data"
              onClick={handleLinkedMenuItemClick}
            >
              <NavIcon component={DatabaseIcon} />
              <ListItemText>Data Management</ListItemText>
            </LinkedMenuItem>
          </>
        )}

        <LinkedMenuItem open={asideOpen} to="/" onClick={handleLogout}>
          <NavIcon component={LogoutIcon} />
          <ListItemText>Log Out</ListItemText>
        </LinkedMenuItem>
      </MenuList>

      <Box className={styles.mobileUser}>
        <ThemeToggle />
        {userDetails && userDetails()}
      </Box>
    </aside>
  );
};

const SideBarSpacer: React.FC<SideBarProps> = ({ asideOpen }) => {
  return (
    <div
      className={`${styles.asideSpacer} ${asideOpen ? styles.asideSpacerOpen : ""}`}
    ></div>
  );
};

export { SideBar, SideBarSpacer };
