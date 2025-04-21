import * as React from "react";
import {
  Box,
  Typography,
  Modal,
  IconButton,
  styled,
  Tooltip,
} from "@mui/material";
import SettingsApplicationsOutlinedIcon from "@mui/icons-material/SettingsApplicationsOutlined";
import PromptSettings from "@components/PromptSettings/PromptSettings";
import { Close } from "@mui/icons-material";
import ModalBox from "@root/shared/ModalBox/ModalBox";

const ChatSettingsModal = () => {
  const [open, setOpen] = React.useState(false);
  const handleOpen = () => setOpen(true);
  const handleClose = () => setOpen(false);

  return (
    <div>
      <Tooltip title="Chat settings" arrow>
        <IconButton onClick={handleOpen}>
          <SettingsApplicationsOutlinedIcon />
        </IconButton>
      </Tooltip>

      <ModalBox open={open} onClose={handleClose}>
        <Typography id="modal-modal-title" variant="h6" component="h2">
          Response Settings
          <IconButton onClick={() => setOpen(false)}>
            <Close fontSize="small" />
          </IconButton>
        </Typography>
        <Box id="modal-modal-description">
          <PromptSettings readOnly={true} />
        </Box>
      </ModalBox>
    </div>
  );
};

export default ChatSettingsModal;
