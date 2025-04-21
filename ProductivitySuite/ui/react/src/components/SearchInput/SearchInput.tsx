import { InputAdornment, styled, TextField } from "@mui/material";
import styles from "./SearchInput.module.scss";
import { Close, Search } from "@mui/icons-material";
import { useRef, useState } from "react";

const StyledSearchInput = styled(TextField)(({ theme }) => ({
  ...theme.customStyles.webInput,
}));

interface SearchInputProps {
  handleSearch: (value: string) => void;
}

const SearchInput: React.FC<SearchInputProps> = ({ handleSearch }) => {
  const [hasValue, setHasValue] = useState(false);

  const inputRef = useRef<HTMLElement>(null);

  const clearSearch = () => {
    if (inputRef.current) {
      const input = inputRef.current.querySelector("input");
      if (input) input.value = "";
    }
    handleSearch("");
    setHasValue(false);
  };

  const search = (value: string) => {
    handleSearch(value);
    setHasValue(value !== "");
  };

  return (
    <StyledSearchInput
      className={styles.searchInput}
      ref={inputRef}
      variant="outlined"
      placeholder="Search..."
      onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
        search(e.target.value)
      }
      InputProps={{
        startAdornment: (
          <InputAdornment position="start">
            <Search />
          </InputAdornment>
        ),
        endAdornment: hasValue && (
          <InputAdornment
            position="end"
            onClick={clearSearch}
            sx={{ cursor: "pointer" }}
          >
            <Close />
          </InputAdornment>
        ),
      }}
      fullWidth
    />
  );
};

export default SearchInput;
