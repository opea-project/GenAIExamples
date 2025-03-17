import {
  CheckCircleFilled,
  CloseCircleFilled,
  ExclamationCircleFilled,
  InfoCircleFilled,
} from "@ant-design/icons-vue";
import { notification } from "ant-design-vue";
interface NotificationIcon {
  icon: any;
  color: string;
}

const getNotificationIcon = (type: string): NotificationIcon => {
  switch (type) {
    case "success":
      return { icon: CheckCircleFilled, color: "--color-success" };
    case "error":
      return { icon: CloseCircleFilled, color: "--color-error" };
    case "warning":
      return { icon: ExclamationCircleFilled, color: "--color-warning" };
    case "info":
      return { icon: InfoCircleFilled, color: "--color-info" };
    default:
      return { icon: null, color: "" };
  }
};

export const customNotification = (
  type: "success" | "warning" | "error" | "info",
  message: string,
  description: string
) => {
  const { icon, color } = getNotificationIcon(type);

  const styledIcon = icon
    ? h(icon, { style: { color: `var(${color})` } })
    : null;

  notification[type]({
    message: message,
    description: description,
    icon: styledIcon,
  });
};
