import { useEffect, useState } from "react";

import DropDown from "@components/DropDown/DropDown";
import CustomSlider from "@components/PromptSettings_Slider/Slider";
import { Box, FormGroup, FormControlLabel } from "@mui/material";
import styles from "./PromptSettings.module.scss";
import TokensInput from "@components/PromptSettings_Tokens/TokensInput";
import FileInput from "@components/File_Input/FileInput";
import WebInput from "@components/Summary_WebInput/WebInput";

import { useAppDispatch, useAppSelector } from "@redux/store";
import { Model } from "@redux/Conversation/Conversation";
import {
  conversationSelector,
  setModel,
  setSourceType,
  setTemperature,
  setToken,
} from "@redux/Conversation/ConversationSlice";

interface AvailableModel {
  name: string;
  value: string;
}

interface PromptSettingsProps {
  readOnly?: boolean;
}

const PromptSettings: React.FC<PromptSettingsProps> = ({
  readOnly = false,
}) => {
  const dispatch = useAppDispatch();

  const { models, type, sourceType, model, token, maxToken, temperature } =
    useAppSelector(conversationSelector);

  const [tokenError, setTokenError] = useState(false);

  const filterAvailableModels = (): AvailableModel[] => {
    if (!models || !type) return [];

    let typeModels: AvailableModel[] = [];

    models.map((model: Model) => {
      if (model.types.includes(type)) {
        typeModels.push({
          name: model.displayName,
          value: model.model_name,
        });
      }
    });

    return typeModels;
  };

  const [formattedModels, setFormattedModels] = useState<AvailableModel[]>(
    filterAvailableModels(),
  );

  useEffect(() => {
    setFormattedModels(filterAvailableModels());
  }, [type, models]);

  useEffect(() => {
    if (!model) return;
    setTokenError(token > maxToken);
  }, [model, token]);

  const updateTemperature = (value: number) => {
    dispatch(setTemperature(Number(value)));
  };

  const updateTokens = (value: number) => {
    dispatch(setToken(Number(value)));
  };

  const updateModel = (value: string) => {
    const selectedModel = models.find(
      (model: Model) => model.model_name === value,
    );
    if (selectedModel) {
      dispatch(setModel(selectedModel));
    }
  };

  const updateSource = (value: string) => {
    dispatch(setSourceType(value));
  };

  const cursorDisable = () => {
    return readOnly ? { pointerEvents: "none" } : {};
  };

  const displaySummarySource = () => {
    if ((type !== "summary" && type !== "faq") || readOnly) return;

    let input = null;
    if (sourceType === "documents") input = <FileInput maxFileCount={1} />;
    if (sourceType === "web") input = <WebInput />;
    if (sourceType === "images" && type === "summary")
      input = <FileInput imageInput={true} />;

    return <div className={styles.summarySource}>{input}</div>;
  };

  // in the off chance specific types do not use these,
  // they have been pulled into their own function
  const tokenAndTemp = () => {
    return (
      <>
        <FormGroup sx={{ marginRight: "1.5rem" }}>
          <FormControlLabel
            sx={cursorDisable()}
            control={
              <Box sx={{ marginLeft: "0.5rem" }}>
                <TokensInput
                  value={token}
                  handleChange={updateTokens}
                  error={tokenError}
                  readOnly={readOnly}
                />
              </Box>
            }
            label={`Tokens${readOnly ? ": " : ""}`}
            labelPlacement="start"
          />
        </FormGroup>

        <FormGroup>
          <FormControlLabel
            sx={cursorDisable()}
            control={
              <CustomSlider
                value={temperature}
                handleChange={updateTemperature}
                readOnly={readOnly}
              />
            }
            label={`Temperature${readOnly ? ": " : ""}`}
            labelPlacement="start"
          />
        </FormGroup>
      </>
    );
  };

  const displaySettings = () => {
    if (type === "summary" || type === "faq") {
      //TODO: Supporting only documents to start
      return (
        <>
          <FormGroup sx={{ marginRight: "1.5rem", marginTop: "2rem" }}>
            <FormControlLabel
              sx={cursorDisable()}
              control={
                <DropDown
                  options={[
                    { name: "Web", value: "web" },
                    { name: "Documents", value: "documents" },
                    { name: "Images", value: "images" },
                  ]}
                  border={true}
                  value={sourceType}
                  handleChange={updateSource}
                />
              }
              label="Summary Source"
              labelPlacement="start"
            />
          </FormGroup>
        </>
      );
    } else {
      return <></>; // tokenAndTemp() // see line 113, conditional option
    }
  };

  return (
    <Box className={styles.promptSettingsWrapper}>
      <Box
        className={`${styles.promptSettings} ${readOnly ? styles.readOnly : ""}`}
      >
        {formattedModels && formattedModels.length > 0 && (
          <FormGroup key={formattedModels[0].name}>
            <FormControlLabel
              sx={cursorDisable()}
              control={
                <DropDown
                  options={formattedModels}
                  value={model}
                  handleChange={updateModel}
                  readOnly={readOnly}
                  border={true}
                  ellipsis={true}
                />
              }
              label={`Model${readOnly ? ": " : ""}`}
              labelPlacement="start"
            />
          </FormGroup>
        )}

        {tokenAndTemp()}
      </Box>

      {/* TODO: Expand source options and show label with dropdown after expansion */}
      {/* {displaySettings()} */}

      {displaySummarySource()}
    </Box>
  );
};

export default PromptSettings;
