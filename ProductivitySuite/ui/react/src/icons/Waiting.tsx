import { useTheme } from "styled-components";

const WaitingIcon = () => {
  const theme = useTheme();
  const iconColor = theme.customStyles.icon?.main;

  return (
    <svg
      width="100"
      height="30"
      viewBox="0 0 100 30"
      xmlns="http://www.w3.org/2000/svg"
    >
      <circle cx="20" cy="15" r="5" fill={iconColor}>
        <animate
          attributeName="r"
          values="5;8;5"
          dur="1.2s"
          repeatCount="indefinite"
          begin="0s"
        />
      </circle>
      <circle cx="50" cy="15" r="5" fill={iconColor}>
        <animate
          attributeName="r"
          values="5;8;5"
          dur="1.2s"
          repeatCount="indefinite"
          begin="0.2s"
        />
      </circle>
      <circle cx="80" cy="15" r="5" fill={iconColor}>
        <animate
          attributeName="r"
          values="5;8;5"
          dur="1.2s"
          repeatCount="indefinite"
          begin="0.4s"
        />
      </circle>
    </svg>
  );
};

export default WaitingIcon;
