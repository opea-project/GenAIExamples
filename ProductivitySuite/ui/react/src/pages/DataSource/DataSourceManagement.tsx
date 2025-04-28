import {
  Box,
  Checkbox,
  FormControlLabel,
  List,
  ListItem,
  Typography,
  FormGroup,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { useEffect, useState } from "react";
import styles from "./DataSourceManagement.module.scss";
import { useAppDispatch, useAppSelector } from "@redux/store";
import {
  conversationSelector,
  deleteInDataSource,
  getAllFilesInDataSource,
  deleteMultipleInDataSource,
} from "@redux/Conversation/ConversationSlice";
import { file } from "@redux/Conversation/Conversation";
import DropDown from "@components/DropDown/DropDown";
import DataWebInput from "@components/Data_Web/DataWebInput";
import FileInput from "@components/File_Input/FileInput";
import SearchInput from "@components/SearchInput/SearchInput";
import {
  DeleteButton,
  SolidButton,
  TextButton,
} from "@root/shared/ActionButtons";

const DataSourceManagement = () => {
  const dispatch = useAppDispatch();

  const theme = useTheme();

  const { filesInDataSource } = useAppSelector(conversationSelector);

  const [dataList, setDataList] = useState<file[]>([]);
  const [activeSourceType, setActiveSourceType] = useState<string>("documents");
  const [selectActive, setSelectActive] = useState(false);
  const [selectAll, setSelectAll] = useState(false);
  const [checkedItems, setCheckedItems] = useState<Record<string, boolean>>({});

  useEffect(() => {
    dispatch(getAllFilesInDataSource({ knowledgeBaseId: "default" }));
  }, []);

  const sortFiles = () => {
    if (activeSourceType === "web") {
      let webFiles = filesInDataSource.filter((file) =>
        file.name.startsWith("http"),
      );
      return webFiles;
    } else {
      let otherFiles = filesInDataSource.filter(
        (file) => !file.name.startsWith("http"),
      );
      return otherFiles;
    }
  };

  useEffect(() => {
    setDataList(sortFiles());
  }, [filesInDataSource, activeSourceType]);

  const handleCheckboxChange = (conversationId: string) => {
    setCheckedItems((prev) => ({
      ...prev,
      [conversationId]: !prev[conversationId],
    }));
  };

  const displayFiles = () => {
    return dataList.map((file: file) => {
      const isChecked = !!checkedItems[file.id];

      const fileText = (
        <>
          <Typography variant="h2">{file.name}</Typography>
          {/* TODO: timestamp for all conversations? */}
          {/* <Typography variant="caption">Last message {convertTime(conversation.updated_at)}</Typography> */}
        </>
      );

      const controlCheckBox = (
        <Checkbox
          id={`check_${file.id}`}
          onChange={() => handleCheckboxChange(file.id)}
          checked={isChecked}
        />
      );

      return (
        <Box className={styles.dataItem} component={ListItem} key={file.id}>
          {selectActive ? (
            <FormControlLabel
              sx={{ ...theme.customStyles.gradientBlock }}
              className={styles.dataName}
              control={controlCheckBox}
              label={fileText}
            />
          ) : (
            <Typography
              variant="body1"
              component={"div"}
              sx={{ ...theme.customStyles.gradientBlock }}
              className={styles.dataName}
            >
              {fileText}
            </Typography>
          )}
        </Box>
      );
    });
  };

  const cancelSelect = () => {
    setSelectActive(false);
    setSelectAll(false);
    setCheckedItems({});
  };

  const deleteSelected = () => {
    setSelectActive(false);

    let files = [];
    for (const [key, value] of Object.entries(checkedItems)) {
      if (value === true) {
        files.push(key);
      }
    }

    if (files.length > 0) {
      //update current state
      setDataList((prev) => prev.filter((item) => !checkedItems[item.id]));
      dispatch(deleteMultipleInDataSource({ files: files }));
    }
  };

  const handleSelectAll = () => {
    const newSelectAll = !selectAll;
    setSelectAll(newSelectAll);

    // Add all items' checked state
    const updatedCheckedItems: Record<string, boolean> = {};
    dataList.forEach((file) => {
      updatedCheckedItems[file.id] = newSelectAll;
    });

    setCheckedItems(updatedCheckedItems);
  };

  const handleSearch = (value: string) => {
    const filteredList = dataList;
    const searchResults = filteredList.filter((file: file) =>
      file.name?.toLowerCase().includes(value.toLowerCase()),
    );
    setDataList(value ? searchResults : sortFiles());
  };

  const updateSource = (value: string) => {
    setActiveSourceType(value);
  };

  const displayInput = () => {
    let input = null;
    if (activeSourceType === "documents")
      input = <FileInput dataManagement={true} />;
    if (activeSourceType === "web") input = <DataWebInput />;
    if (activeSourceType === "images")
      input = <FileInput dataManagement={true} imageInput={true} />;

    return <Box className={styles.dataInputWrapper}>{input}</Box>;
  };

  return (
    <Box className={styles.dataView}>
      <Box>
        <FormGroup sx={{ marginRight: "1.5rem" }}>
          <FormControlLabel
            sx={{ margin: "0 auto" }}
            label="Data Source"
            labelPlacement="start"
            control={
              <DropDown
                options={[
                  { name: "Web", value: "web" },
                  { name: "Documents", value: "documents" },
                  // { name: 'Images', value: 'images' }
                ]}
                border={true}
                value={activeSourceType}
                handleChange={updateSource}
              />
            }
          />
        </FormGroup>
      </Box>

      {displayInput()}

      <SearchInput handleSearch={handleSearch} />

      <Box
        display={"flex"}
        flexDirection={"row"}
        justifyContent={"space-between"}
      >
        <Typography>
          You have {dataList.length} file{dataList.length !== 1 && "s"}
        </Typography>

        {dataList.length > 0 && (
          <Box className={styles.actions}>
            {selectActive ? (
              <TextButton onClick={() => handleSelectAll()}>
                Select All
              </TextButton>
            ) : (
              <TextButton onClick={() => setSelectActive(true)}>
                Select
              </TextButton>
            )}

            {selectActive && (
              <>
                <SolidButton onClick={() => cancelSelect()}>Cancel</SolidButton>
                <DeleteButton onClick={() => deleteSelected()}>
                  Delete Selected
                </DeleteButton>
              </>
            )}
          </Box>
        )}
      </Box>

      <List>{displayFiles()}</List>
    </Box>
  );
};

export default DataSourceManagement;
