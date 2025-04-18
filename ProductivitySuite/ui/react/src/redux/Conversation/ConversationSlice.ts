// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { PayloadAction, createSlice } from "@reduxjs/toolkit";
import { RootState, store } from "@redux/store";
import { fetchEventSource } from "@microsoft/fetch-event-source";
import {
  Message,
  MessageRole,
  ConversationReducer,
  ConversationRequest,
  Conversation,
  Model,
  UseCase,
  CodeRequest,
  SummaryFaqRequest,
} from "./Conversation";
import { getCurrentTimeStamp } from "@utils/utils";
import { createAsyncThunkWrapper } from "@redux/thunkUtil";
import axios from "axios";

import config, {
  CHAT_QNA_URL,
  DATA_PREP_URL,
  DATA_PREP_GET_URL,
  DATA_PREP_DELETE_URL,
  CHAT_HISTORY_CREATE,
  CHAT_HISTORY_GET,
  CHAT_HISTORY_DELETE,
  CODE_GEN_URL,
  DOC_SUM_URL,
  FAQ_GEN_URL,
} from "@root/config";
import { NotificationSeverity, notify } from "@components/Notification/Notification";
import { ChatBubbleOutline, CodeOutlined, Description, QuizOutlined } from "@mui/icons-material";

const urlMap: any = {
  summary: DOC_SUM_URL,
  faq: FAQ_GEN_URL,
  chat: CHAT_QNA_URL,
  code: CODE_GEN_URL,
};

const interactionTypes = [
  {
    key: "chat",
    name: "Chat Q&A",
    icon: ChatBubbleOutline,
    color: "#0ACA00",
  },
  {
    key: "summary",
    name: "Summarize Content",
    icon: Description,
    color: "#FF4FFC",
  },
  {
    key: "code",
    name: "Generate Code",
    icon: CodeOutlined,
    color: "#489BEA",
  },
  // TODO: Enable file upload support for faqgen endpoint similar to summary
  // {
  //     key: 'faq',
  //     name: 'Generate FAQ',
  //     icon: QuizOutlined,
  //     color: '#9D00FF'
  // },
];

const initialState: ConversationReducer = {
  conversations: [],
  sharedConversations: [],
  selectedConversationId: "",
  selectedConversationHistory: [],
  onGoingResult: "",
  isPending: false,
  filesInDataSource: [],
  dataSourceUrlStatus: "",

  useCase: "",
  useCases: [],
  model: "",
  models: [],
  type: "chat",
  types: interactionTypes,
  systemPrompt: config.defaultChatPrompt,
  minToken: 100,
  maxToken: 1000,
  token: 100,
  minTemperature: 0,
  maxTemperature: 1,
  temperature: 0.4,
  sourceType: "documents",
  sourceLinks: [],
  sourceFiles: [],

  abortController: null,

  uploadInProgress: false,
};

export const ConversationSlice = createSlice({
  name: "Conversation",
  initialState,
  reducers: {
    logout: (state) => {
      state.conversations = [];
      state.selectedConversationId = "";
      state.onGoingResult = "";
      state.selectedConversationHistory = [];
      state.filesInDataSource = [];
    },
    setIsPending: (state, action: PayloadAction<boolean>) => {
      state.isPending = action.payload;
    },
    setOnGoingResult: (state, action: PayloadAction<string>) => {
      state.onGoingResult = action.payload;
    },
    addMessageToMessages: (state, action: PayloadAction<Message>) => {
      state.selectedConversationHistory.push(action.payload);
    },
    newConversation: (state, action: PayloadAction<boolean>) => {
      state.selectedConversationId = "";
      state.onGoingResult = "";
      state.selectedConversationHistory = [];

      // full reset if true
      if (action.payload) {
        (state.sourceLinks = []), (state.sourceFiles = []);

        // in case of upload / history conversation that clears model name, we want to reset to defaults
        const currentType = state.type;
        if (currentType) {
          const approvedModel = state.models.find((item: Model) => item.types.includes(currentType));
          if (approvedModel) {
            state.model = approvedModel.model_name;
            state.token = approvedModel.minToken;
            state.temperature = 0.4;
          }
        }
      }
    },
    updatePromptSettings: (state, action: PayloadAction<any>) => {
      state.model = action.payload.model;
      state.token = action.payload.token;
      state.temperature = action.payload.temperature;
      state.type = action.payload.type;
    },
    setSelectedConversationId: (state, action: PayloadAction<string>) => {
      state.selectedConversationId = action.payload;
    },
    setSelectedConversationHistory: (state, action: PayloadAction<Message[]>) => {
      state.selectedConversationHistory = action.payload;
    },
    setTemperature: (state, action: PayloadAction<number>) => {
      state.temperature = action.payload;
    },
    setToken: (state, action: PayloadAction<number>) => {
      state.token = action.payload;
    },
    setModel: (state, action: PayloadAction<Model>) => {
      state.model = action.payload.model_name;
      state.maxToken = action.payload.maxToken;
      state.minToken = action.payload.minToken;
    },
    setModelName: (state, action: PayloadAction<string>) => {
      state.model = action.payload;
    },
    setModels: (state, action: PayloadAction<[]>) => {
      state.models = action.payload;
    },
    setUseCase: (state, action: PayloadAction<string>) => {
      state.useCase = action.payload;
    },
    setUseCases: (state, action: PayloadAction<[]>) => {
      state.useCases = action.payload;
    },
    setType: (state, action: PayloadAction<string>) => {
      state.type = action.payload;

      switch (action.payload) {
        case "summary":
        case "faq":
          state.systemPrompt = "";
          state.sourceType = "documents";
          break;
        case "chat":
        case "code":
          state.systemPrompt = config.defaultChatPrompt;
          state.sourceFiles = [];
          state.sourceLinks = [];
          break;
      }

      let firstModel = state.models.find((model: Model) => model.types.includes(action.payload));
      state.model = firstModel?.model_name || state.models[0].model_name;
    },
    setUploadInProgress: (state, action: PayloadAction<boolean>) => {
      state.uploadInProgress = action.payload;
    },
    setSourceLinks: (state, action: PayloadAction<string[]>) => {
      state.sourceLinks = action.payload;
    },
    setSourceFiles: (state, action: PayloadAction<any[]>) => {
      state.sourceFiles = action.payload;
    },
    setSourceType: (state, action: PayloadAction<string>) => {
      state.sourceType = action.payload;
    },
    setSystemPrompt: (state, action: PayloadAction<string>) => {
      state.systemPrompt = action.payload;
    },
    setAbortController: (state, action: PayloadAction<AbortController | null>) => {
      state.abortController = action.payload;
    },
    abortStream: (state) => {
      if (state.abortController) state.abortController.abort();

      const m: Message = {
        role: MessageRole.Assistant,
        content: state.onGoingResult,
        time: getCurrentTimeStamp().toString(),
      };

      // add last message before ending
      state.selectedConversationHistory.push(m);
      state.onGoingResult = "";
      state.abortController = null;
    },
    setDataSourceUrlStatus: (state, action: PayloadAction<string>) => {
      state.dataSourceUrlStatus = action.payload;
    },
    uploadChat: (state, action: PayloadAction<any>) => {
      state.selectedConversationHistory = action.payload.messages;
      state.model = action.payload.model;
      state.token = action.payload.token;
      state.temperature = action.payload.temperature;
      state.type = action.payload.type;
      state.sourceFiles = []; // only chat can be uploaded, empty if set
      state.sourceLinks = []; // only chat can be uploaded, empty if set
    },
  },
  extraReducers(builder) {
    builder.addCase(uploadFile.fulfilled, () => {
      notify("File Uploaded Successfully", NotificationSeverity.SUCCESS);
    });
    builder.addCase(uploadFile.rejected, () => {
      notify("Failed to Upload file", NotificationSeverity.ERROR);
    });
    builder.addCase(submitDataSourceURL.fulfilled, (state) => {
      notify("Submitted Successfully", NotificationSeverity.SUCCESS);
      state.dataSourceUrlStatus = ""; // watching for pending only on front
    });
    builder.addCase(submitDataSourceURL.rejected, (state) => {
      notify("Submit Failed", NotificationSeverity.ERROR);
      state.dataSourceUrlStatus = ""; // watching for pending only on front
    });
    builder.addCase(deleteConversation.rejected, () => {
      notify("Failed to Delete Conversation", NotificationSeverity.ERROR);
    });
    builder.addCase(getAllConversations.fulfilled, (state, action) => {
      state.conversations = action.payload;
    });
    builder.addCase(getConversationHistory.fulfilled, (state, action) => {
      state.selectedConversationHistory = action.payload;
    });
    builder.addCase(saveConversationtoDatabase.fulfilled, (state, action) => {
      if (state.selectedConversationId == "") {
        state.selectedConversationId = action.payload;
        state.conversations.push({
          id: action.payload,
          first_query: state.selectedConversationHistory[1].content,
        });
        window.history.pushState({}, "", `/chat/${action.payload}`);
      }
    });
    builder.addCase(getAllFilesInDataSource.fulfilled, (state, action) => {
      state.filesInDataSource = action.payload;
    });
  },
});

export const getSupportedUseCases = createAsyncThunkWrapper(
  "public/usecase_configs.json",
  async (_: void, { getState }) => {
    const response = await axios.get("/usecase_configs.json");
    store.dispatch(setUseCases(response.data));

    // @ts-ignore
    const state: RootState = getState();
    const userAccess = state.userReducer.role;
    const currentUseCase = state.conversationReducer.useCase;

    // setDefault use case if not stored / already set by localStorage
    if (!currentUseCase) {
      const approvedAccess = response.data.find((item: UseCase) => item.access_level === userAccess);
      if (approvedAccess) store.dispatch(setUseCase(approvedAccess));
    }

    return response.data;
  },
);

export const getSupportedModels = createAsyncThunkWrapper(
  "public/model_configs.json",
  async (_: void, { getState }) => {
    const response = await axios.get("/model_configs.json");
    store.dispatch(setModels(response.data));

    // @ts-ignore
    const state: RootState = getState();
    const currentModel = state.conversationReducer.model;
    const currentType = state.conversationReducer.type;

    // setDefault use case if not stored  / already set by localStorage
    // TODO: revisit if type also gets stored and not defaulted on state
    if (!currentModel && currentType) {
      const approvedModel = response.data.find((item: Model) => item.types.includes(currentType));
      if (approvedModel) store.dispatch(setModel(approvedModel));
    }

    return response.data;
  },
);

export const getAllConversations = createAsyncThunkWrapper(
  "conversation/getAllConversations",
  async ({ user, useCase }: { user: string; useCase: string }, {}) => {
    //TODO: Add useCase
    const response = await axios.post(CHAT_HISTORY_GET, {
      user,
    });

    return response.data.reverse();
  },
);

export const getConversationHistory = createAsyncThunkWrapper(
  "conversation/getConversationHistory",
  async ({ user, conversationId }: { user: string; conversationId: string }, {}) => {
    const response = await axios.post(CHAT_HISTORY_GET, {
      user,
      id: conversationId,
    });

    // update settings for response settings modal
    store.dispatch(
      updatePromptSettings({
        model: response.data.model,
        token: response.data.max_tokens,
        temperature: response.data.temperature,
        type: response.data.request_type,
      }),
    );

    return response.data.messages;
  },
);

export const submitDataSourceURL = createAsyncThunkWrapper(
  "conversation/submitDataSourceURL",
  async ({ link_list }: { link_list: string[] }, { dispatch }) => {
    dispatch(setDataSourceUrlStatus("pending"));
    const body = new FormData();
    body.append("link_list", JSON.stringify(link_list));
    // body.append("parent", "appData"); // TODO: this did not work, in an attempt to sort data types
    const response = await axios.post(DATA_PREP_URL, body);
    dispatch(getAllFilesInDataSource({ knowledgeBaseId: "default" }));
    return response.data;
  },
);

export const getAllFilesInDataSource = createAsyncThunkWrapper(
  "conversation/getAllFilesInDataSource",
  async ({ knowledgeBaseId }: { knowledgeBaseId: string }, {}) => {
    const body = {
      knowledge_base_id: knowledgeBaseId,
    };
    const response = await axios.post(DATA_PREP_GET_URL, body);
    return response.data;
  },
);

export const uploadFile = createAsyncThunkWrapper(
  "conversation/uploadFile",
  async ({ file }: { file: File }, { dispatch }) => {
    const body = new FormData();
    body.append("files", file);
    const response = await axios.post(DATA_PREP_URL, body);
    dispatch(getAllFilesInDataSource({ knowledgeBaseId: "default" }));
    return response.data;
  },
);

export const deleteMultipleInDataSource = createAsyncThunkWrapper(
  "conversation/deleteConversations",
  async ({ files }: { files: string[] }, { dispatch }) => {
    const promises = files.map((file) =>
      axios
        .post(DATA_PREP_DELETE_URL, {
          file_path: file.split("_")[1],
        })
        .then((response) => {
          return response.data;
        })
        .catch((err) => {
          notify("Error deleting file", NotificationSeverity.ERROR);
          console.error(`Error deleting file`, file, err);
        }),
    );

    await Promise.all(promises)
      .then(() => {
        notify("Files deleted successfully", NotificationSeverity.SUCCESS);
      })
      .catch((err) => {
        notify("Error deleting on or more of your files", NotificationSeverity.ERROR);
        console.error("Error deleting on or more of your files", err);
      })
      .finally(() => {
        dispatch(getAllFilesInDataSource({ knowledgeBaseId: "default" }));
      });
  },
);

export const deleteInDataSource = createAsyncThunkWrapper(
  "conversation/deleteInDataSource",
  async ({ file }: { file: any }, { dispatch }) => {
    const response = await axios.post(DATA_PREP_DELETE_URL, {
      file_path: file,
    });
    dispatch(getAllFilesInDataSource({ knowledgeBaseId: "default" }));
    return response.data;
  },
);

export const saveConversationtoDatabase = createAsyncThunkWrapper(
  "conversation/saveConversationtoDatabase",
  async ({ conversation }: { conversation: Conversation }, { dispatch, getState }) => {
    // @ts-ignore
    const state: RootState = getState();
    const selectedConversationHistory = state.conversationReducer.selectedConversationHistory;

    //TODO: if we end up with a systemPrompt for code change this
    const firstMessageIndex = state.conversationReducer.type === "code" ? 0 : 1;

    const response = await axios.post(CHAT_HISTORY_CREATE, {
      data: {
        user: state.userReducer.name,
        messages: selectedConversationHistory,
        time: getCurrentTimeStamp().toString(),
        model: state.conversationReducer.model,
        temperature: state.conversationReducer.temperature,
        max_tokens: state.conversationReducer.token,
        request_type: state.conversationReducer.type,
      },
      id: conversation.id == "" ? null : conversation.id,
      first_query: selectedConversationHistory[firstMessageIndex].content,
    });

    dispatch(
      getAllConversations({
        user: state.userReducer.name,
        useCase: state.conversationReducer.useCase,
      }),
    );
    return response.data;
  },
);

export const deleteConversations = createAsyncThunkWrapper(
  "conversation/deleteConversations",
  async (
    { user, conversationIds, useCase }: { user: string; conversationIds: string[]; useCase: string },
    { dispatch },
  ) => {
    const promises = conversationIds.map((id) =>
      axios
        .post(CHAT_HISTORY_DELETE, {
          user,
          id: id,
        })
        .then((response) => {
          return response.data;
        })
        .catch((err) => {
          notify("Error deleting conversation", NotificationSeverity.ERROR);
          console.error(`Error deleting conversation ${id}`, err);
        }),
    );

    await Promise.all(promises)
      .then(() => {
        notify("Conversations deleted successfully", NotificationSeverity.SUCCESS);
      })
      .catch((err) => {
        notify("Error deleting on or more of your conversations", NotificationSeverity.ERROR);
        console.error("Error deleting on or more of your conversations", err);
      })
      .finally(() => {
        dispatch(getAllConversations({ user, useCase }));
      });
  },
);

export const deleteConversation = createAsyncThunkWrapper(
  "conversation/delete",
  async (
    { user, conversationId, useCase }: { user: string; conversationId: string; useCase: string },
    { dispatch },
  ) => {
    const response = await axios.post(CHAT_HISTORY_DELETE, {
      user,
      id: conversationId,
    });

    dispatch(newConversation(false));
    dispatch(getAllConversations({ user, useCase }));
    return response.data;
  },
);

export const doConversation = (conversationRequest: ConversationRequest) => {
  store.dispatch(setIsPending(true));

  const { conversationId, userPrompt, messages, model, token, temperature, type } = conversationRequest;

  // TODO: MAYBE... check first message if 'system' already exists... on dev during page edits the
  // hot module reloads and instantly adds more system messages to the total messages
  if (messages.length === 1) store.dispatch(addMessageToMessages(messages[0])); // do not re-add system prompt
  store.dispatch(addMessageToMessages(userPrompt));

  const userPromptWithTime = {
    role: userPrompt.role,
    content: userPrompt.content,
    time: getCurrentTimeStamp().toString(),
  };

  const body = {
    messages: [...messages, userPromptWithTime],
    model: model,
    max_tokens: token,
    temperature: temperature,
  };

  eventStream(type, body, conversationId);
};

export const doSummaryFaq = (summaryFaqRequest: SummaryFaqRequest) => {
  store.dispatch(setIsPending(true));

  const { conversationId, model, token, temperature, type, messages, files, userPrompt } = summaryFaqRequest;

  const postWithFiles = files && files.length > 0;

  const body: any = {};
  const formData = new FormData();

  store.dispatch(addMessageToMessages(userPrompt));

  if (postWithFiles) {
    formData.append("messages", "");
    formData.append("model", model);
    formData.append("max_tokens", token.toString());
    formData.append("type", "text");
    formData.append("temperature", temperature.toString());

    files.forEach((file) => {
      formData.append("files", file.file);
    });

    formDataEventStream(urlMap[type], formData);
  } else {
    body.messages = messages;
    body.model = model;
    (body.max_tokens = token), (body.temperature = temperature);
    body.type = "text";

    eventStream(type, body, conversationId);
  }
};

export const doCodeGen = (codeRequest: CodeRequest) => {
  store.dispatch(setIsPending(true));

  const { conversationId, userPrompt, model, token, temperature, type } = codeRequest;

  store.dispatch(addMessageToMessages(userPrompt));

  const body = {
    messages: userPrompt.content,
    model: model, //'meta-llama/Llama-3.3-70B-Instruct',
    max_tokens: token,
    temperature: temperature,
  };

  eventStream(type, body, conversationId);
};

const eventStream = (type: string, body: any, conversationId: string = "") => {
  const abortController = new AbortController();
  store.dispatch(setAbortController(abortController));
  const signal = abortController.signal;

  let result = "";

  try {
    fetchEventSource(urlMap[type], {
      method: "POST",
      body: JSON.stringify(body),
      headers: {
        "Content-Type": "application/json",
      },
      signal,
      openWhenHidden: true,
      async onopen(response) {
        if (response.ok) {
          store.dispatch(setIsPending(false));
          return;
        } else if (response.status >= 400 && response.status < 500 && response.status !== 429) {
          const e = await response.json();
          console.log(e);
          throw Error(e.error.message);
        } else {
          console.log("error", response);
          notify("Error in opening stream", NotificationSeverity.ERROR);
        }
      },
      onmessage(msg) {
        if (msg?.data != "[DONE]") {
          try {
            if (type === "code") {
              const parsedData = JSON.parse(msg.data);
              result += parsedData.choices[0].text;
              store.dispatch(setOnGoingResult(result));
            }
            if (type !== "summary" && type !== "faq") {
              //parse content for data: "b"
              const match = msg.data.match(/b'([^']*)'/);
              if (match && match[1] != "</s>") {
                const extractedText = match[1];
                result += extractedText;
                store.dispatch(setOnGoingResult(result));
              }
            } else {
              //text summary/faq for data: "ops string"
              const res = JSON.parse(msg.data); // Parse valid JSON
              const logs = res.ops;
              logs.forEach((log: { op: string; path: string; value: string }) => {
                if (log.op === "add") {
                  if (
                    log.value !== "</s>" &&
                    log.path.endsWith("/streamed_output/-") &&
                    log.path.length > "/streamed_output/-".length
                  ) {
                    result += log.value;
                    if (log.value) store.dispatch(setOnGoingResult(result));
                  }
                }
              });
            }
          } catch (e) {
            console.log("something wrong in msg", e);
            notify("Error in message response", NotificationSeverity.ERROR);
            throw e;
          }
        }
      },
      onerror(err) {
        console.log("error", err);
        store.dispatch(setOnGoingResult(""));
        notify("Error streaming response", NotificationSeverity.ERROR);
        throw err;
      },
      onclose() {
        const m: Message = {
          role: MessageRole.Assistant,
          content: result,
          time: getCurrentTimeStamp().toString(),
        };

        store.dispatch(setOnGoingResult(""));
        store.dispatch(setAbortController(null));
        store.dispatch(addMessageToMessages(m));

        if (type === "chat") {
          store.dispatch(
            saveConversationtoDatabase({
              conversation: {
                id: conversationId,
              },
            }),
          );
        }
      },
    });
  } catch (err) {
    console.log(err);
  }
};

const formDataEventStream = async (url: string, formData: any) => {
  const abortController = new AbortController();
  store.dispatch(setAbortController(abortController));
  const signal = abortController.signal;

  let result = "";

  try {
    const response = await fetch(url, {
      method: "POST",
      body: formData,
      signal,
    });

    if (!response.ok) {
      throw new Error("Network response was not ok");
    }

    if (response && response.body) {
      store.dispatch(setIsPending(false));

      const reader = response.body.getReader();

      // Read the stream in chunks
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }

        // Process the chunk of data (e.g., convert to text)
        const textChunk = new TextDecoder().decode(value).trim();

        // sometimes double lines return
        const lines = textChunk.split("\n");

        for (let line of lines) {
          if (line.startsWith("data:")) {
            const jsonStr = line.replace(/^data:\s*/, ""); // Remove "data: "

            if (jsonStr !== "[DONE]") {
              try {
                // API Response for final output regularly returns incomplete JSON,
                // due to final response containing source summary content and exceeding
                // token limit in the response. We don't use it anyway so don't parse it.
                if (!jsonStr.includes('"path":"/streamed_output/-"')) {
                  const res = JSON.parse(jsonStr); // Parse valid JSON

                  const logs = res.ops;
                  logs.forEach((log: { op: string; path: string; value: string }) => {
                    if (log.op === "add") {
                      if (
                        log.value !== "</s>" &&
                        log.path.endsWith("/streamed_output/-") &&
                        log.path.length > "/streamed_output/-".length
                      ) {
                        result += log.value;
                        if (log.value) store.dispatch(setOnGoingResult(result));
                      }
                    }
                  });
                }
              } catch (error) {
                console.warn("Error parsing JSON:", error, "Raw Data:", jsonStr);
              }
            } else {
              const m: Message = {
                role: MessageRole.Assistant,
                content: result,
                time: getCurrentTimeStamp().toString(),
              };

              store.dispatch(setOnGoingResult(""));
              store.dispatch(addMessageToMessages(m));
              store.dispatch(setAbortController(null));
            }
          }
        }
      }
    }
  } catch (error: any) {
    if (error.name === "AbortError") {
      console.log("Fetch aborted successfully.");
    } else {
      console.error("Fetch error:", error);
    }
  }
};

export const {
  logout,
  setOnGoingResult,
  setIsPending,
  newConversation,
  updatePromptSettings,
  addMessageToMessages,
  setSelectedConversationId,
  setSelectedConversationHistory,
  setTemperature,
  setToken,
  setModel,
  setModelName,
  setModels,
  setType,
  setUploadInProgress,
  setSourceLinks,
  setSourceFiles,
  setSourceType,
  setUseCase,
  setUseCases,
  setSystemPrompt,
  setAbortController,
  abortStream,
  setDataSourceUrlStatus,
  uploadChat,
} = ConversationSlice.actions;
export const conversationSelector = (state: RootState) => state.conversationReducer;
export default ConversationSlice.reducer;
