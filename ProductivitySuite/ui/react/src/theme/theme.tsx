import { createTheme } from "@mui/material/styles";
import moonIcon from "@assets/icons/moon.svg";
import sunIcon from "@assets/icons/sun.svg";

const lightBg = "#F2F3FF";

const lightGrey = "#1f2133";

const lightPurple = "#e3e5fd";
const deepPurple = "#3D447F";
const darkPurple = "#222647";
const brightPurple = "#6b77db";
const white60 = "#ffffff60";

export const themeCreator = (mode: "light" | "dark") => {
  return createTheme({
    palette: {
      mode: mode, // Default mode
      primary: {
        main: mode === "dark" ? "#ffffff" : "#ffffff",
        contrastText: "#000000",
      },
      secondary: {
        main: deepPurple,
        contrastText: "#ffffff",
      },
      background: {
        default: mode === "dark" ? "#090B1C" : lightBg,
        paper: mode === "dark" ? "#161b22" : "#ffffff",
      },
      text: {
        primary: mode === "dark" ? "#c9d1d9" : "#000000",
        secondary: mode === "dark" ? "#ffffff" : deepPurple,
      },
    },
    typography: {
      fontFamily: "Roboto, Arial, sans-serif",
      h1: {
        fontWeight: 700,
        fontSize: "2rem",
        lineHeight: 1.5,
        color: mode === "dark" ? "#ffffff" : deepPurple,
      },
      h2: {
        fontWeight: 500,
        fontSize: "1rem",
        lineHeight: 1.4,
        color: mode === "dark" ? "#ffffff" : deepPurple,
      },
      body1: {
        fontSize: "1rem",
        fontWeight: 300,
        lineHeight: 1.5,
        color: mode === "dark" ? "#ffffff" : deepPurple,
      },
      button: {
        textTransform: "none",
        fontWeight: 600,
      },
    },
    components: {
      MuiIconButton: {
        styleOverrides: {
          root: ({ theme }) => ({
            svg: {
              fill: theme.customStyles.icon?.main,
            },
          }),
        },
      },

      MuiCheckbox: {
        styleOverrides: {
          root: ({ theme }) => ({
            color: theme.customStyles.icon?.main,
            "&.Mui-checked": {
              color: theme.customStyles.icon?.main,
            },
          }),
        },
      },
      MuiTooltip: {
        styleOverrides: {
          tooltip: {
            backgroundColor: mode === "dark" ? lightGrey : darkPurple,
          },
          arrow: {
            color: mode === "dark" ? lightGrey : darkPurple,
          },
        },
      },
    },
    customStyles: {
      header: {
        backgroundColor: mode === "dark" ? "#090B1C" : lightBg,
        boxShadow: mode === "dark" ? "none" : "0px 1px 24.1px 0px #4953D526",
        borderBottom: mode === "dark" ? `1px solid ${deepPurple}7A` : "none",
      },
      aside: {
        main: mode === "dark" ? lightGrey : "#E5E7FE",
      },
      customDivider: {
        main: mode === "dark" ? white60 : deepPurple,
      },
      user: {
        main: mode === "dark" ? "#161b22" : "#E3E5FD",
      },
      icon: {
        main: mode === "dark" ? "#E5E7FE" : deepPurple,
      },
      input: {
        main: mode === "dark" ? "#ffffff" : "#ffffff", // background color
        primary: mode === "dark" ? "#c9d1d9" : "#000000",
        secondary: mode === "dark" ? "#ffffff" : "#6b7280",
      },
      code: {
        // title: mode === 'dark' ? '#2b2b2b' : '#2b2b2b',
        primary: mode === "dark" ? "#5B5D74" : "#B6B9D4",
        // text: mode === 'dark' ? '#ffffff' : '#ffffff',
        // secondary: mode === 'dark' ? '#141415' : '#141415',
      },
      gradientShadow: {
        border: `1px solid ${mode === "dark" ? "#ffffff20" : deepPurple + "10"}`,
        boxShadow:
          mode === "dark"
            ? "0px 0px 10px rgba(0, 0, 0, 0.7)"
            : "0px 0px 10px rgba(0, 0, 0, 0.1)",
      },
      gradientBlock: {
        background:
          mode === "dark"
            ? `linear-gradient(180deg, ${lightGrey} 0%, rgba(61, 68, 127, 0.15)100%)`
            : "linear-gradient(180deg, rgba(230, 232, 253, 0.50) 0%, rgba(61, 68, 127, 0.15) 100%)",
        "&:hover": {
          background:
            mode === "dark"
              ? `linear-gradient(180deg, rgba(61, 68, 127, 0.15) 0%, ${lightGrey} 100%)`
              : "linear-gradient(180deg, rgba(61, 68, 127, 0.15) 0%, rgba(230, 232, 253, 0.50) 100%)",
        },

        ".MuiChip-root": {
          backgroundColor: "#fff",
        },
      },
      sources: {
        iconWrap: {
          background: "linear-gradient(90deg, #C398FA -56.85%, #7E6DBB 21.46%)",
          svg: {
            fill: "#ffffff !important",
            color: "#ffffff",
          },
        },
        sourceWrap: {
          background: mode === "dark" ? "#1a1b27" : "#ffffff70",
          border: `1px solid ${mode === "dark" ? "rgba(230, 232, 253, 0.30)" : lightPurple}`,
          color: mode === "dark" ? "#fff" : deepPurple,
        },
        sourceChip: {
          background: mode === "dark" ? "#1a1b27" : "#ffffff",
          border: `1px solid ${mode === "dark" ? "#c398fa" : "rgba(73, 83, 213, 0.40)"}`,
          color: mode === "dark" ? "#fff" : "#444",
        },
      },
      audioProgress: {
        stroke: mode === "dark" ? "#c9d1d9" : "#6b7280",
      },
      audioEditButton: {
        boxShadow: "none",
        border: "none",
        backgroundColor: "transparent",
        color: mode === "dark" ? "#fff" : deepPurple,
        "&:hover": {
          backgroundColor: mode === "dark" ? deepPurple : deepPurple + "40",
        },
      },
      homeTitle: {
        background:
          mode === "dark"
            ? "#fff"
            : `linear-gradient(271deg, #C398FA -56.85%, #7E6DBB 21.46%, ${deepPurple} 99.77%)`,
      },
      homeButtons: {
        borderRadius: "25px",
        border: `1px solid ${mode === "dark" ? white60 : deepPurple + "60"}`, // take purple down some it down some
        backgroundColor: mode === "dark" ? "#161b22" : lightBg,
        color: mode === "dark" ? "#fff" : deepPurple,

        boxShadow:
          mode === "dark"
            ? "0px 4px 10px rgba(0, 0, 0, 0.7)"
            : "0px 4px 10px rgba(0, 0, 0, 0.1)",
        "&:hover": {
          backgroundColor: mode === "dark" ? darkPurple : lightPurple,
        },
        fontWeight: 300,
        '&[aria-selected="true"]': {
          fontWeight: 600,
          backgroundColor: mode === "dark" ? darkPurple : lightPurple,
        },
      },
      promptExpandButton: {
        borderRadius: "25px",
        border: `1px solid ${mode === "dark" ? white60 : deepPurple + "60"}`, // take purple down some it down some
        backgroundColor: mode === "dark" ? "#161b22" : lightBg,
        color: mode === "dark" ? "#fff" : deepPurple,

        boxShadow:
          mode === "dark"
            ? "0px 4px 10px rgba(0, 0, 0, 0.7)"
            : "0px 4px 10px rgba(0, 0, 0, 0.1)",
        "&:hover": {
          backgroundColor: mode === "dark" ? deepPurple : lightPurple,
        },
      },
      promptButton: {
        backgroundColor: mode === "dark" ? lightGrey : lightBg,
        color: `${mode === "dark" ? "#fff" : deepPurple} !important`,
        "&:hover": {
          backgroundColor: mode === "dark" ? darkPurple : lightPurple,
          color: mode === "dark" ? "#ffffff" : deepPurple,
        },
      },
      promptListWrapper: {
        backgroundColor: mode === "dark" ? lightGrey : lightBg,
        boxShadow:
          mode === "dark"
            ? "0px 4px 10px rgba(0, 0, 0, 0.7)"
            : "0px 4px 10px rgba(0, 0, 0, 0.1)",
      },
      primaryInput: {
        inputWrapper: {
          backgroundColor: mode === "dark" ? lightGrey : lightPurple,
          border: `1px solid ${mode === "dark" ? "#ffffff20" : deepPurple + "10"}`,
          boxShadow:
            mode === "dark"
              ? "0px 0px 10px rgba(0, 0, 0, 0.3)"
              : "0px 0px 10px rgba(0, 0, 0, 0.1)",
          "&:hover, &.active, &:focus": {
            border: `1px solid ${mode === "dark" ? "#ffffff20" : deepPurple + "60"}`,
          },
        },
        textInput: {
          color: mode === "dark" ? "#fff" : "#3D447F",
          "&::placeholder": {
            color: mode === "dark" ? "#ffffff90" : "#6b7280",
          },
        },
        circleButton: {
          backgroundColor: mode === "dark" ? "transparent" : deepPurple + "80",
          border: `1px solid ${mode === "dark" ? white60 : "transparent"}`,
          "svg path": {
            fill: mode === "dark" ? "#c9d1d9" : "#D9D9D9",
          },
          "&.active": {
            backgroundColor: mode === "dark" ? deepPurple : lightGrey,
            "svg path": {
              fill: mode === "dark" ? "#c9d1d9" : "#D9D9D9",
            },
          },
          "&:hover": {
            backgroundColor: mode === "dark" ? "#646999" : "#003E71",
            "svg path": {
              fill: mode === "dark" ? "#c9d1d9" : "#D9D9D9",
            },
          },
        },
      },
      tokensInput: {
        color: mode === "dark" ? "#fff" : deepPurple,
        backgroundColor: "transparent",
        border: `1px solid ${mode === "dark" ? white60 : deepPurple + "70"}`,
        boxShadow: "none",

        "&:hover": {
          borderColor: deepPurple,
        },

        "&:focus": {
          borderColor: deepPurple,
        },

        "&[aria-invalid]": {
          borderColor: "#cc0000 !important",
          color: "#cc0000",
        },
      },
      webInput: {
        backgroundColor: mode === "dark" ? lightGrey : lightPurple,
        ".Mui-focused": {
          color: mode === "dark" ? "#ffffff" : deepPurple,
          ".MuiOutlinedInput-notchedOutline": {
            border: `1px solid ${mode === "dark" ? white60 : `${deepPurple}22`}`,
          },
        },
      },
      fileInputWrapper: {
        backgroundColor: `${deepPurple}10`,
        border: `1px dashed ${mode === "dark" ? white60 : `${deepPurple}22`}`,
      },
      fileInput: {
        wrapper: {
          backgroundColor: `${deepPurple}10`,
          border: `1px dashed ${mode === "dark" ? white60 : `${deepPurple}22`}`,
        },
        file: {
          backgroundColor:
            mode === "dark" ? "rgba(255,255,255,0.1)" : "rgba(255,255,255,0.7)",
        },
      },
      actionButtons: {
        text: {
          boxShadow: "none",
          background: "none",
          fontWeight: "400",
          color: mode === "dark" ? "#ffffff" : "#007ce1",
          "&:disabled": {
            opacity: 0.5,
            color: mode === "dark" ? "#ffffff" : "#007ce1",
          },
          "&:hover": {
            background: mode === "dark" ? "#007ce1" : "#ffffff",
            color: mode === "dark" ? "#ffffff" : "#007ce1",
          },
        },
        delete: {
          boxShadow: "none",
          background: "#f15346",
          fontWeight: "400",
          color: "#fff",
          "&:hover": {
            background: "#cc0000",
          },
          "&:disabled": {
            opacity: 0.5,
            color: "#fff",
          },
        },
        solid: {
          boxShadow: "none",
          background: deepPurple,
          fontWeight: "400",
          color: "#fff",
          "&:hover": {
            background: deepPurple,
          },
          "&:disabled": {
            opacity: 0.5,
            color: "#fff",
          },
        },
        outline: {
          boxShadow: "none",
          background: "transparent",
          fontWeight: "400",
          color: mode === "dark" ? "#ffffff" : "#007ce1",
          border: `1px solid ${mode === "dark" ? "#ffffff" : "#007ce1"}`,
          "&:hover": {
            background: mode === "dark" ? "#007ce1" : "#ffffff",
            color: mode === "dark" ? "#ffffff" : "#007ce1",
          },
          "&.active": {
            background: mode === "dark" ? "#ffffff" : "#007ce1",
            color: mode === "dark" ? "#007ce1" : "#ffffff",
          },
        },
      },
      themeToggle: {
        ".MuiSwitch-switchBase.Mui-checked": {
          ".MuiSwitch-thumb:before": {
            backgroundImage: `url(${moonIcon})`,
          },
        },
        "& .MuiSwitch-thumb": {
          backgroundColor: mode === "dark" ? "#fff" : "transparent",
          border: `1px solid ${mode === "dark" ? "#090B1C" : deepPurple}`,
          "svg path": {
            fill: mode === "dark" ? "#E5E7FE" : deepPurple,
          },
          "&::before": {
            backgroundImage: `url(${sunIcon})`,
          },
        },
        "& .MuiSwitch-track": {
          border: `1px solid ${mode === "dark" ? "#fff" : deepPurple}`,
          backgroundColor: mode === "dark" ? "#8796A5" : "transparent",
        },
      },
      dropDown: {
        "&:hover, &:focus": {
          backgroundColor:
            mode === "dark" ? "rgba(0,0,0, 0.5)" : "rgba(230, 232, 253, 0.50)",
        },
        "&.Mui-selected": {
          backgroundColor:
            mode === "dark" ? "rgba(0,0,0, 1)" : "rgba(230, 232, 253, 0.75)",
        },
        "&.Mui-selected:hover, &.Mui-selected:focus": {
          backgroundColor:
            mode === "dark" ? "rgba(0,0,0, 1)" : "rgba(230, 232, 253, 0.75)",
        },
        wrapper: {
          border: `1px solid ${mode === "dark" ? white60 : deepPurple + "70"}`,
        },
      },
      settingsModal: {
        boxShadow: " 0px 0px 20px rgba(0,0,0,0.5)",
        border: "1px solid #000",
        background: mode === "dark" ? lightGrey : lightBg,
        "#modal-modal-title": {
          backgroundColor: "#e5e7fe",
          color: deepPurple,

          svg: {
            fill: deepPurple,
          },
        },
      },
      styledSlider: {
        color: mode === "dark" ? brightPurple : deepPurple,

        "&.disabled": {
          color: mode === "dark" ? brightPurple : deepPurple,
        },

        ".MuiSlider-rail": {
          backgroundColor: mode === "dark" ? brightPurple : deepPurple,
        },

        ".MuiSlider-track": {
          backgroundColor: mode === "dark" ? brightPurple : deepPurple,
        },

        ".MuiSlider-thumb": {
          backgroundColor: mode === "dark" ? brightPurple : deepPurple,

          "&:hover": {
            boxShadow: `0 0 0 6px rgba(61,68,127,0.3)`,
          },

          "&.focusVisible": {
            boxShadow: `0 0 0 8px rgba(61,68,127,0.5)`,
          },

          "&.active": {
            boxShadow: `0 0 0 8px rgba(61,68,127,0.5)`,
          },

          "&.disabled": {
            backgroundColor: mode === "dark" ? brightPurple : deepPurple,
          },
        },
      },
    },
  });
};
deepPurple;
