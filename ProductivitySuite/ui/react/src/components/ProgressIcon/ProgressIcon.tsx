import { CircularProgress, styled } from "@mui/material";

const ProgressIconStyle = styled(CircularProgress)(({ theme }) => ({
  "svg circle": {
    stroke: theme.customStyles.audioProgress?.stroke,
  },
}));

const ProgressIcon = () => {
  return <ProgressIconStyle size={20} />;
};

export default ProgressIcon;
