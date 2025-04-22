import { AlertColor, IconButton, styled } from "@mui/material";
import {
  SnackbarProvider,
  useSnackbar,
  MaterialDesignContent,
  closeSnackbar,
} from "notistack";
import { useEffect } from "react";
import { Subject } from "rxjs";
import {
  TaskAlt,
  WarningAmberOutlined,
  ErrorOutlineOutlined,
  InfoOutlined,
  Close,
} from "@mui/icons-material";

interface NotificationDataProps {
  message: string;
  variant: AlertColor;
}

type NotificationSeverity = "error" | "info" | "success" | "warning";

export const NotificationSeverity = {
  SUCCESS: "success" as NotificationSeverity,
  ERROR: "error" as NotificationSeverity,
  WARNING: "warning" as NotificationSeverity,
  INFO: "info" as NotificationSeverity,
};

const severityColor = (variant: string) => {
  switch (variant) {
    case "success":
      return "#388e3c";
    case "error":
      return "#d32f2f";
    case "warning":
      return "#f57c00";
    case "info":
      return "#0288d1";
    default:
      return "rgba(0, 0, 0, 0.87)";
  }
};

const StyledMaterialDesignContent = styled(MaterialDesignContent)<{
  severity: AlertColor;
}>(({ variant }) => ({
  backgroundColor: (() => {
    switch (variant) {
      case "success":
        return "rgb(225,238,226)";
      case "error":
        return "rgb(248,224,224)";
      case "warning":
        return "rgb(254,235,217)";
      case "info":
        return "rgb(217,237,248)";
      default:
        return "rgb(225,238,226)";
    }
  })(),
  border: `1px solid ${severityColor(variant)}`,
  color: severityColor(variant),
  ".MuiAlert-action": {
    paddingTop: 0,
    scale: 0.8,
    borderLeft: `1px solid ${severityColor(variant)}`,
    marginLeft: "1rem",
  },
  svg: {
    marginRight: "1rem",
  },
  "button svg": {
    marginRight: "0",
    path: {
      fill: severityColor(variant),
    },
  },
}));

const CloseIcon = styled(IconButton)(() => ({
  minWidth: "unset",
}));

const Notify = new Subject<NotificationDataProps>();

export const notify = (message: string, variant: AlertColor) => {
  if (!variant) variant = NotificationSeverity.SUCCESS;
  Notify.next({ message, variant });
};

const NotificationComponent = () => {
  const { enqueueSnackbar } = useSnackbar();

  useEffect(() => {
    const subscription = Notify.subscribe({
      next: (notification) => {
        enqueueSnackbar(notification.message, {
          variant: notification.variant,
          action: (key) => (
            <CloseIcon
              onClick={() => closeSnackbar(key)}
              variant={notification.variant}
            >
              <Close />
            </CloseIcon>
          ),
        });
      },
    });

    return () => subscription.unsubscribe();
  }, []);

  return <></>;
};

const Notification = () => {
  return (
    <SnackbarProvider
      maxSnack={3}
      autoHideDuration={3000}
      anchorOrigin={{ horizontal: "right", vertical: "top" }}
      iconVariant={{
        success: <TaskAlt />,
        warning: <WarningAmberOutlined />,
        error: <ErrorOutlineOutlined />,
        info: <InfoOutlined />,
      }}
      Components={{
        success: StyledMaterialDesignContent,
        warning: StyledMaterialDesignContent,
        error: StyledMaterialDesignContent,
        info: StyledMaterialDesignContent,
      }}
    >
      <NotificationComponent />
    </SnackbarProvider>
  );
};

export default Notification;
