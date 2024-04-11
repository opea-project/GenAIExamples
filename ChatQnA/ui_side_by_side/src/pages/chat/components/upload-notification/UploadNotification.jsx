import { Alert, Snackbar } from "@mui/material";
import { bool, func, node, oneOf, shape } from "prop-types";

const UploadNotification = ({ notification, onNotificationClose }) => (
  <Snackbar
    open={notification.open}
    anchorOrigin={{ vertical: "top", horizontal: "right" }}
    autoHideDuration={6000}
    onClose={onNotificationClose}
  >
    <Alert
      severity={notification.severity}
      variant="filled"
      sx={{ fontFamily: "IntelOneText, sans-serif" }}
      onClose={onNotificationClose}
    >
      {notification.message}
    </Alert>
  </Snackbar>
);

UploadNotification.propTypes = {
  notification: shape({
    open: bool,
    severity: oneOf(["success", "info", "warning", "error"]),
    message: node,
  }).isRequired,
  onNotificationClose: func.isRequired,
};

export default UploadNotification;
