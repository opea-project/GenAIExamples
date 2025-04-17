import React, { useContext } from "react";
import { styled } from "@mui/material/styles";
import { Switch, Typography, Box } from "@mui/material";
import { ThemeContext } from "@contexts/ThemeContext";
import styles from "./ThemeToggle.module.scss";

const MaterialUISwitch = styled(Switch)(({ theme }) => ({
  ...theme.customStyles.themeToggle,
}));

const ThemeToggle: React.FC = () => {
  const { darkMode, toggleTheme } = useContext(ThemeContext);
  const [checked, setChecked] = React.useState(darkMode);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setChecked(event.target.checked);
    toggleTheme();
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter" || event.key === " ") {
      handleChange({
        target: { checked: !checked },
      } as React.ChangeEvent<HTMLInputElement>);
    }
  };

  return (
    <Box
      className={`${styles.toggleWrapper} themeToggle`}
      justifyContent={darkMode ? "flex-start" : "flex-end"}
      gap={2}
    >
      <Typography className={styles.copy}>
        {checked ? "Dark" : "Light"}
      </Typography>
      <MaterialUISwitch
        sx={{ m: 1 }}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        checked={checked}
        className={styles.toggle}
      />
    </Box>
  );
};

export default ThemeToggle;
