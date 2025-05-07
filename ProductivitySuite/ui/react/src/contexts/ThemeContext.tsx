import React, { createContext, useState, useEffect, useCallback } from "react";
import { ThemeProvider as MuiThemeProvider, CssBaseline } from "@mui/material";
import { themeCreator } from "../theme/theme";

interface ThemeContextType {
  darkMode: boolean;
  toggleTheme: () => void;
}

export const ThemeContext = createContext<ThemeContextType>({
  darkMode: false,
  toggleTheme: () => {},
});

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const savedTheme = localStorage.getItem("theme") === "dark";
  const [darkMode, setDarkMode] = useState(savedTheme);

  const toggleTheme = useCallback(() => {
    setDarkMode((prevMode) => !prevMode);
  }, []);

  useEffect(() => {
    localStorage.setItem("theme", darkMode ? "dark" : "light");
  }, [darkMode]);

  const theme = themeCreator(darkMode ? "dark" : "light");

  return (
    <ThemeContext.Provider value={{ darkMode, toggleTheme }}>
      <MuiThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </MuiThemeProvider>
    </ThemeContext.Provider>
  );
};
