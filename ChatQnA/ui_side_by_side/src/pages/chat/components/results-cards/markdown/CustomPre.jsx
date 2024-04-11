import "./custom-pre.scss";

import CheckIcon from "@mui/icons-material/Check";
import CloseIcon from "@mui/icons-material/Close";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import { IconButton } from "@mui/material";
import { arrayOf, node, oneOfType } from "prop-types";
import { useState } from "react";

const CopyCodeButton = () => {
  const [copyBtnState, setCopyBtnState] = useState("idle");

  const onClick = (event) => {
    if (copyBtnState === "idle") {
      const copyButtonElement = event.target;
      const codeSnippetElement = copyButtonElement.nextElementSibling;
      const codeSnippetText = codeSnippetElement.innerText;

      navigator.clipboard
        .writeText(codeSnippetText)
        .then(() => {
          setCopyBtnState("success");
        })
        .catch((error) => {
          setCopyBtnState("error");
          console.error(error);
        })
        .finally(() => {
          setTimeout(() => {
            setCopyBtnState("idle");
          }, 1000);
        });
    }
  };

  return (
    <IconButton
      className="copy-code-btn"
      disableRipple={true}
      disableFocusRipple={true}
      onClick={onClick}
    >
      {copyBtnState === "idle" && <ContentCopyIcon className="icon" fontSize="small" />}
      {copyBtnState === "success" && <CheckIcon className="icon success" fontSize="small" />}
      {copyBtnState === "error" && <CloseIcon className="icon error" fontSize="small" />}
    </IconButton>
  );
};

const CustomPre = ({ children }) => (
  <pre className="custom-pre-wrapper">
    {window.isSecureContext && <CopyCodeButton />}
    {children}
  </pre>
);

CustomPre.propTypes = {
  children: oneOfType([arrayOf(node), node]),
};

export default CustomPre;
