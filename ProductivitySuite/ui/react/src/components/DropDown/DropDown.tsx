import React, { useState } from "react";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import {
  List,
  ListItemButton,
  ListItemText,
  MenuItem,
  Menu,
  Typography,
  ListItemIcon,
  styled,
  Box,
} from "@mui/material";
import styles from "./DropDown.module.scss";

interface DropDownProps {
  options: { name: string; value: string }[];
  value?: string;
  handleChange: (value: string) => void;
  readOnly?: boolean;
  border?: boolean;
  ellipsis?: true;
}

const CustomMenuItem = styled(MenuItem)(({ theme }) => ({
  ...theme.customStyles.dropDown,
}));

const DropDownWrapper = styled(Box)(({ theme }) => ({
  ...theme.customStyles.dropDown.wrapper,
}));

const DropDown: React.FC<DropDownProps> = ({
  options,
  value,
  handleChange,
  readOnly,
  border,
  ellipsis,
}) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const foundIndex = options.findIndex((option) => option.value === value);

  const [selectedIndex, setSelectedIndex] = useState(
    foundIndex !== -1 ? foundIndex : 0,
  );

  const open = Boolean(anchorEl);
  const handleClickListItem = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuItemClick = (index: number) => {
    setSelectedIndex(index);
    setAnchorEl(null);
    handleChange(options[index].value);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  if (readOnly) {
    let name = foundIndex === -1 ? "Unknown" : options[selectedIndex].name;
    return <Typography className={styles.leftGap}>{name}</Typography>;
  }

  const Wrapper = border ? DropDownWrapper : Box;

  return options.length === 0 ? (
    <></>
  ) : (
    <Wrapper className={`${styles.dropDown} ${border ? styles.border : ""}`}>
      <List>
        <ListItemButton onClick={handleClickListItem}>
          <ListItemText
            className={`${styles.noWrap} ${ellipsis ? styles.ellipsis : ""}`}
            primary={options[selectedIndex].name}
          />
          <ListItemIcon className={styles.unsetMin}>
            <KeyboardArrowDownIcon
              fontSize="small"
              className={`${styles.chevron} ${open ? styles.open : ""}`}
            />
          </ListItemIcon>
        </ListItemButton>
      </List>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        slotProps={{
          paper: {
            style: {
              maxHeight: 250,
            },
          },
        }}
      >
        {options.map((option, index) => (
          <CustomMenuItem
            className={styles.noWrap}
            key={index}
            value={option.value}
            selected={index === selectedIndex}
            onClick={() => handleMenuItemClick(index)}
          >
            {option.name}
          </CustomMenuItem>
        ))}
      </Menu>
    </Wrapper>
  );
};

export default DropDown;
