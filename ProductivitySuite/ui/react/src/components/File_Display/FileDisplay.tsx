import { IconButton } from "@mui/material";
import { Close, TaskOutlined, Language } from "@mui/icons-material";
import styled from "styled-components";
import styles from "./FileDisplay.module.scss";

const FileWrap = styled("div")(({ theme }) => ({
  ...theme.customStyles.fileInput.file,
  ...theme.customStyles.gradientShadow,
}));

const IconWrap = styled("div")(({ theme }) => ({
  ...theme.customStyles.sources.iconWrap,
}));

interface FileProps {
  file: File;
  index: number;
  remove?: (value: number) => void;
  isWeb?: boolean;
}

const FileDispaly: React.FC<FileProps> = ({ file, index, remove, isWeb }) => {
  if (!file) return;

  let fileExtension = file.name.split(".").pop()?.toLowerCase();
  let fileName = isWeb ? file.name : file.name.split(".").shift();

  return (
    <FileWrap className={styles.file} title={file.name}>
      <IconWrap className={styles.iconWrap}>
        <TaskOutlined />
      </IconWrap>

      <div>
        <div className={styles.fileName} title={file.name}>
          {fileName}
        </div>
        {!isWeb && <div className={styles.fileExt}>.{fileExtension}</div>}
      </div>

      {remove && (
        <IconButton onClick={() => remove(index)}>
          <Close fontSize="small" />
        </IconButton>
      )}
      {isWeb && <Language />}
    </FileWrap>
  );
};

export default FileDispaly;
