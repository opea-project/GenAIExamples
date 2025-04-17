import * as React from "react";
import { styled } from "@mui/material/styles";
import { Slider, Grid2, Typography } from "@mui/material";
import styles from "./Slider.module.scss";

const StyledSlider = styled(Slider)(({ theme }) => ({
  ...theme.customStyles.styledSlider,
}));

interface CustomSliderProps {
  value: number;
  handleChange: (value: number) => void;
  readOnly?: boolean;
}

const CustomSlider: React.FC<CustomSliderProps> = ({
  value,
  handleChange,
  readOnly,
}) => {
  if (readOnly) {
    return <Typography marginLeft={".5rem"}>{value}</Typography>;
  }

  const handleSlideUpdate = (event: Event, value: number) => {
    handleChange(value);
  };

  return (
    <Grid2 container className={styles.sliderWrapper}>
      <Grid2 className={styles.start}>0</Grid2>
      <Grid2 className={styles.trackWrapper}>
        <StyledSlider
          className={styles.styledSlider}
          value={value ?? 0.4}
          step={0.05}
          min={0}
          max={1}
          // disabled={readOnly}
          onChange={handleSlideUpdate}
          valueLabelDisplay="auto"
        />
      </Grid2>
      <Grid2>1</Grid2>
    </Grid2>
  );
};

export default CustomSlider;
