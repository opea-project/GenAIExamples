import "./upload-file-drawer.scss";

import CloseIcon from "@mui/icons-material/Close";
import { Button, Drawer, IconButton, Tab, Tabs, TextField } from "@mui/material";
import { bool, func } from "prop-types";
import { useRef, useState } from "react";
import { v4 as uuidv4 } from "uuid";

const initialFileInputState = {
  value: undefined,
  error: false,
};

const initialFileLinksListState = [];

const UploadFileDrawer = ({ show, onUploadFileDrawerClose, onConfirmUpload }) => {
  const [selectedTab, setSelectedTab] = useState(0); // 0 - file, 1 - link
  const [fileInput, setFileInput] = useState(initialFileInputState);
  const fileRef = useRef();
  const [fileLinksList, setFileLinksList] = useState(initialFileLinksListState);

  const resetUploadFileDrawer = () => {
    setFileInput(initialFileInputState);
    fileRef.current = null;
    setFileLinksList(initialFileLinksListState);
    setSelectedTab(0);
  };

  const onTabChange = (_, value) => {
    setSelectedTab(value);
  };

  const onUploadedFileChange = (event) => {
    if (
      event.target.files &&
      event.target.files.length > 0 &&
      event.target.files[0] instanceof File
    ) {
      const file = event.target.files[0];
      const isFileTypePDF = file.type === "application/pdf";
      setFileInput({
        value: file,
        error: !isFileTypePDF,
      });
    }
  };

  const addFileLinkToList = () => {
    setFileLinksList((prevState) => [
      ...prevState,
      {
        id: `file-link-${uuidv4()}`,
        value: "",
      },
    ]);
  };

  const removeFileLinkFromList = (linkID) => {
    setFileLinksList((prevState) => prevState.filter((link) => link.id !== linkID));
  };

  const onFileLinkInputChange = (event) => {
    setFileLinksList((prevState) =>
      prevState.map((link) =>
        link.id === event.target.id
          ? {
              ...link,
              value: event.target.value,
            }
          : link
      )
    );
  };

  const onConfirmUploadBtnPress = () => {
    // 0 - file, 1 - link
    if (selectedTab === 0) {
      onConfirmUpload(fileInput.value);
    } else if (selectedTab === 1) {
      onConfirmUpload(fileLinksList.map((link) => link.value));
    }
    resetUploadFileDrawer();
  };

  const onClose = () => {
    onUploadFileDrawerClose();
    resetUploadFileDrawer();
  };

  const isConfirmUploadBtnDisabled =
    (selectedTab === 0 && fileInput.value === undefined) ||
    (selectedTab === 0 && fileInput.error === true) ||
    (selectedTab === 1 && fileLinksList.length === 0) ||
    (selectedTab === 1 && fileLinksList.some((link) => link.value === ""));

  return (
    <Drawer className="upload-drawer" open={show} anchor="right" onClose={onClose}>
      <section className="upload-drawer-content">
        <header>
          <h3>Upload your data source</h3>
          <p>
            Please upload your local file or paste a remote file link.
            <br />
            Chat will respond based on the content of the uploaded file.
          </p>
        </header>
        <main>
          <Tabs value={selectedTab} onChange={onTabChange}>
            <Tab label="Upload File" className="tab-item" />
            <Tab label="Paste File Links" className="tab-item" />
          </Tabs>
          {selectedTab === 0 && (
            <div className="upload-file-tab">
              <label htmlFor="file" className="main-label">
                Choose file to upload
              </label>
              <label htmlFor="file" className="sub-label">
                Supported formats: PDF
              </label>
              <input
                type="file"
                accept=".pdf"
                className="file-input"
                onChange={onUploadedFileChange}
                ref={fileRef}
              />
              {fileInput.error && (
                <p className="file-input__error-msg">Your file must be in PDF format</p>
              )}
            </div>
          )}
          {selectedTab === 1 && (
            <div className="file-link-tab">
              <Button variant="outlined" className="add-link-btn" onClick={addFileLinkToList}>
                Add File Link
              </Button>
              <div className="file-links-list">
                {fileLinksList.length === 0 && (
                  <div className="no-file-links-msg">
                    <p>Please use the button above to add your file links</p>
                  </div>
                )}
                {fileLinksList.map(({ id, value }, index) => (
                  <div key={id} className="file-link-item">
                    <label>{index + 1}</label>
                    <TextField
                      type="text"
                      id={id}
                      name={id}
                      inputProps={{
                        style: {
                          fontFamily: "IntelOneText",
                          padding: "8px 12px",
                        },
                      }}
                      fullWidth
                      size="small"
                      value={value}
                      onChange={onFileLinkInputChange}
                    />
                    <IconButton
                      className="delete-file-link-item-btn"
                      onClick={() => removeFileLinkFromList(id)}
                    >
                      <CloseIcon fontSize="small" color="error" />
                    </IconButton>
                  </div>
                ))}
              </div>
            </div>
          )}
        </main>
        <footer>
          <Button
            variant="contained"
            className="confirm-btn"
            disabled={isConfirmUploadBtnDisabled}
            onClick={onConfirmUploadBtnPress}
          >
            Send to Chat
          </Button>
          <Button className="cancel-btn" onClick={onClose}>
            Cancel
          </Button>
        </footer>
      </section>
    </Drawer>
  );
};

UploadFileDrawer.propTypes = {
  show: bool,
  onUploadFileDrawerClose: func,
  onConfirmUpload: func,
};

export default UploadFileDrawer;
