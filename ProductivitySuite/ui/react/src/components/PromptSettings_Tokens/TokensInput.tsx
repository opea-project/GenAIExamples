import * as React from "react";
import { styled } from "@mui/material/styles";

import { Typography } from "@mui/material";
import styles from "./TokensInput.module.scss";

interface NumberInputProps {
  value?: number;
  handleChange: (value: number) => void;
  error: boolean;
  readOnly?: boolean;
}

const StyledInput = styled("input")(({ theme }) => ({
  ...theme.customStyles.tokensInput,
}));

const TokensInput: React.FC<NumberInputProps> = ({
  value = 1,
  handleChange,
  error,
  readOnly,
}) => {
  if (readOnly) {
    return <Typography>{value}</Typography>;
  }

  return (
    <div className={`${styles.numberInput}`}>
      <StyledInput
        type="number"
        className={`${error ? styles.error : ""}`}
        min={1}
        max={4096}
        step={2}
        defaultValue={value}
        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
          handleChange(parseInt(e.target.value, 10))
        }
        aria-label="Quantity Input"
      />
    </div>
  );
};

export default TokensInput;
