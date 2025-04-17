import React, { useEffect, useReducer, useRef, useState } from "react";
import {
  Box,
  Button,
  Typography,
  Paper,
  IconButton,
  styled,
} from "@mui/material";
import {
  UploadFile,
  Close,
  ExpandMore,
  FileUploadOutlined,
} from "@mui/icons-material";
import styles from "./FileInput.module.scss";
import {
  NotificationSeverity,
  notify,
} from "@components/Notification/Notification";
import { useAppDispatch, useAppSelector } from "@redux/store";
import {
  conversationSelector,
  setSourceFiles,
  setUploadInProgress,
  uploadFile,
} from "@redux/Conversation/ConversationSlice";
import ModalBox from "@shared/ModalBox/ModalBox";
import { OutlineButton, SolidButton } from "@shared/ActionButtons";
import { Link } from "react-router-dom";
import FileDispaly from "@components/File_Display/FileDisplay";
import ProgressIcon from "@components/ProgressIcon/ProgressIcon";

const ExpandButton = styled(Button)(({ theme }) => ({
  ...theme.customStyles.promptExpandButton,
}));

interface FileWithPreview {
  file: File;
  preview: string;
}

interface FileInputProps {
  imageInput?: boolean;
  maxFileCount?: number;
  confirmationModal?: boolean;
  dataManagement?: boolean;
}

const imageExtensions = ["jpg", "jpeg", "png", "gif"];
const docExtensions = ["txt"];
const dataExtensions = [
  "txt",
  "pdf",
  "csv",
  "xls",
  "xlsx",
  "json" /*"doc", "docx", "md", "ppt", "pptx", "html", "xml", "xsl", "xslt", "rtf", "v", "sv"*/,
];
const maxImageSize = 3 * 1024 * 1024; // 3MB
const maxDocSize = 200 * 1024 * 1024; // 200MB

const FileInputWrapper = styled(Paper)(({ theme }) => ({
  ...theme.customStyles.fileInput.wrapper,
}));

const FileInput: React.FC<FileInputProps> = ({
  maxFileCount = 5,
  imageInput,
  dataManagement,
}) => {
  const { model, models, useCase, filesInDataSource, uploadInProgress, type } =
    useAppSelector(conversationSelector);
  // const { filesInDataManagement, uploadInProgress } = useAppSelector(dataManagementSelector);

  const dispatch = useAppDispatch();
  const [confirmUpload, setConfirmUpload] = useState<boolean>(false);
  const [filesToUpload, setFilesToUpload] = useState<
    (FileWithPreview | File)[]
  >([]);
  const [details, showDetails] = useState<boolean>(filesToUpload.length === 0);

  const inputRef = useRef<HTMLInputElement>(null);

  const extensions = imageInput
    ? imageExtensions
    : dataManagement
      ? dataExtensions
      : docExtensions;
  const maxSize = imageInput ? maxImageSize : maxDocSize;

  const [insightToken, setInsightToken] = useState<number>(0);

  useEffect(() => {
    showDetails(filesToUpload.length === 0);

    // summary / faq
    if (!dataManagement && filesToUpload.length > 0) {
      dispatch(setSourceFiles(filesToUpload));
    }
  }, [filesToUpload]);

  useEffect(() => {
    // model sets insight token in summary/faq
    if (!dataManagement) {
      let selectedModel = models.find(
        (thisModel) => thisModel.model_name === model,
      );
      if (selectedModel) setInsightToken(selectedModel.maxToken);
    }
  }, [model, models]);

  useEffect(() => {
    setFilesToUpload([]);
    dispatch(setSourceFiles([]));
  }, [type]);

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const droppedFiles = Array.from(e.dataTransfer.files);
    validateFiles(droppedFiles);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      const validated = validateFiles(selectedFiles);
      if (validated) e.target.value = ""; // Clear input
    }
  };

  const validateFiles = (newFiles: File[]) => {
    if (newFiles.length + filesToUpload.length > maxFileCount) {
      notify(
        `You can only upload a maximum of ${maxFileCount} file${maxFileCount > 1 ? "s" : ""}.`,
        NotificationSeverity.ERROR,
      );
      return;
    }

    const validFiles = newFiles.filter((file) => {
      const fileExtension = file.name.split(".").pop()?.toLowerCase();
      const isSupportedExtension = extensions.includes(fileExtension || "");
      const isWithinSizeLimit = file.size <= maxSize;

      const compareTo = dataManagement ? filesInDataSource : filesToUpload;

      let duplicate = compareTo.some((f: any) => {
        return f.name === file.name;
      });

      // duplicate file check, currently data management only (summary/faq single file)
      if (duplicate) {
        notify(
          `File "${file.name}" is already added.`,
          NotificationSeverity.ERROR,
        );
        return false;
      }

      if (!isSupportedExtension) {
        notify(
          `File "${file.name}" has an unsupported file type.`,
          NotificationSeverity.ERROR,
        );
        return false;
      }

      if (!isWithinSizeLimit) {
        notify(
          `File "${file.name}" exceeds the maximum size limit of ${imageInput ? "3MB" : "200MB"}.`,
          NotificationSeverity.ERROR,
        );
        return false;
      }

      return isSupportedExtension && isWithinSizeLimit;
    });

    if (validFiles.length > 0) {
      addToQueue(validFiles);
    }

    return true;
  };

  const addToQueue = async (newFiles: File[]) => {
    const filteredFiles = newFiles.filter((file: File | FileWithPreview) => {
      let activeFile = "file" in file ? file.file : file;
      return !filesToUpload.some((f: File | FileWithPreview) => {
        let comparedFile = "file" in f ? f.file : f;
        return comparedFile.name === activeFile.name;
      });
    });

    const filesWithPreview = filteredFiles.map((file) => ({
      file,
      preview: URL.createObjectURL(file),
    }));

    setFilesToUpload([...filesToUpload, ...filesWithPreview]);
  };

  const removeFile = (index: number) => {
    let updatedFiles = filesToUpload.filter(
      (file, fileIndex) => index !== fileIndex,
    );
    setFilesToUpload(updatedFiles);
  };

  const uploadFiles = async () => {
    dispatch(setUploadInProgress(true));

    const responses = await Promise.all(
      filesToUpload.map((file: any) => {
        dispatch(uploadFile({ file: file.file }));
      }),
    );

    dispatch(setUploadInProgress(false));

    setConfirmUpload(false);
    setFilesToUpload([]);
  };

  const showConfirmUpload = () => {
    setConfirmUpload(true);
  };

  const filePreview = () => {
    if (filesToUpload.length > 0) {
      return (
        <Box className={styles.previewFiles}>
          <Box className={styles.fileList}>
            {filesToUpload.map((file, fileIndex) => {
              let activeFile = "file" in file ? file.file : file;
              return (
                <span key={fileIndex}>
                  <FileDispaly
                    index={fileIndex}
                    file={activeFile}
                    remove={removeFile}
                  />
                </span>
              );
            })}
          </Box>
        </Box>
      );
    } else {
      return (
        <Typography variant="h6" gutterBottom color="secondary">
          Upload or Drop Files Here
        </Typography>
      );
    }
  };

  const renderConfirmUpload = () => {
    if (confirmUpload) {
      return (
        <ModalBox>
          <Typography id="modal-modal-title" variant="h6" component="h2">
            Uploading files
            <IconButton onClick={() => setConfirmUpload(false)}>
              <Close fontSize="small" />
            </IconButton>
          </Typography>
          <Box id="modal-modal-description">
            <p>
              I hereby certify that the content uploaded is free from any
              personally identifiable information or other private data that
              would violate applicable privacy laws and regulations.
            </p>
            <div>
              <SolidButton onClick={() => uploadFiles()}>
                Agree and Continue
              </SolidButton>
              <OutlineButton onClick={() => setConfirmUpload(false)}>
                Cancel
              </OutlineButton>
            </div>
          </Box>
        </ModalBox>
      );
    }
  };

  if (uploadInProgress) {
    return (
      <Box className={styles.fileInputWrapper}>
        <FileInputWrapper className={styles.inputWrapper}>
          <ProgressIcon />
        </FileInputWrapper>
      </Box>
    );
  }

  return (
    <Box className={styles.fileInputWrapper}>
      <FileInputWrapper
        onDrop={handleDrop}
        onDragOver={(e: any) => e.preventDefault()}
        className={styles.inputWrapper}
      >
        {filePreview()}

        <div>
          {filesToUpload.length !== maxFileCount && (
            <SolidButton onClick={() => inputRef.current?.click()}>
              <UploadFile sx={{ marginRight: "5px" }} /> Browse Files
              <input
                ref={inputRef}
                type="file"
                multiple
                accept={`.${extensions.join(",.")}`}
                /*multiple*/ hidden
                onChange={handleFileSelect}
              />
            </SolidButton>
          )}

          {dataManagement && (
            <SolidButton
              className={styles.upload}
              onClick={showConfirmUpload}
              disabled={filesToUpload.length === 0}
            >
              <FileUploadOutlined sx={{ marginRight: "5px" }} /> Upload
            </SolidButton>
          )}
        </div>

        {filesToUpload.length > 0 && (
          <ExpandButton
            className={`${styles.expand} ${details ? styles.open : ""}`}
            onClick={() => showDetails(!details)}
          >
            <ExpandMore fontSize="small" />
          </ExpandButton>
        )}

        <div
          className={`${styles.details} ${details ? styles.detailsOpen : styles.detailGap}`}
        >
          <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
            Limit {imageInput ? "3MB" : "200MB"} per file.
          </Typography>

          <Typography variant="body2" color="textSecondary" sx={{ mt: 0.5 }}>
            Valid file formats are {extensions.join(", ").toUpperCase()}.
          </Typography>

          <Typography variant="body2" color="textSecondary" sx={{ mt: 0.5 }}>
            You can select maximum of {maxFileCount} valid file
            {maxFileCount > 1 ? "s" : ""}.
          </Typography>

          {!dataManagement && (
            <Typography variant="body2" color="textSecondary" sx={{ mt: 0.5 }}>
              Max supported input tokens for {imageInput && "images"} data
              insight is{" "}
              {insightToken >= 1000 ? insightToken / 1000 + "K" : insightToken}
            </Typography>
          )}
        </div>
      </FileInputWrapper>

      {renderConfirmUpload()}
    </Box>
  );
};

export default FileInput;
