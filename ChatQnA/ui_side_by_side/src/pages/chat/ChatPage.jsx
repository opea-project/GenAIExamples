import "./chat-page.scss";

import { useEffect, useRef, useState } from "react";
import { SSE } from "sse.js";

import ResultsService from "../../service/ResultsService";
import PromptInput from "./components/prompt-input/PromptInput";
import ResultsCards from "./components/results-cards/ResultsCards";
import UploadFileDrawer from "./components/upload/UploadFileDrawer";
import UploadNotification from "./components/upload-notification/UploadNotification";

const { VITE_WITH_RAG_BASE_URL, VITE_WITHOUT_RAG_BASE_URL } = import.meta.env;

const RESULTS_DATA_LOCAL_STORAGE_KEY = "resultsData";

const resultsDataInitialState = {
  withoutRAG: [],
  withRAG: [],
};

const ChatPage = () => {
  const [resultsData, setResultsData] = useState(resultsDataInitialState);
  const [resultsLoading, setResultsLoading] = useState({
    withoutRAG: false,
    withRAG: false,
  });
  const withRAGAnswer = useRef("");
  const withoutRAGAnswer = useRef("");
  const [isPromptInputDisabled, setIsPromptInputDisabled] = useState(false);
  const [showUploadFileDrawer, setShowUploadFileDrawer] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [notification, setNotification] = useState({
    open: false,
    message: <span></span>,
    severity: "success",
  });
  const [isClearChatHistoryBtnDisabled, setIsClearChatHistoryBtnDisabled] = useState(true);
  const isMounted = useRef(false);

  useEffect(() => {
    const storedResultsData = JSON.parse(localStorage.getItem(RESULTS_DATA_LOCAL_STORAGE_KEY));
    if (storedResultsData) {
      setResultsData(storedResultsData);
    }
  }, []);

  useEffect(() => {
    if (isMounted.current) {
      window.localStorage.setItem(RESULTS_DATA_LOCAL_STORAGE_KEY, JSON.stringify(resultsData));
    } else {
      isMounted.current = true;
    }
  }, [resultsData]);

  useEffect(() => {
    setIsPromptInputDisabled(Object.values(resultsLoading).some((value) => value));
    if (!resultsLoading.withRAG) {
      withRAGAnswer.current = "";
    }
    if (!resultsLoading.withoutRAG) {
      withoutRAGAnswer.current = "";
    }
  }, [resultsLoading]);

  useEffect(() => {
    setIsClearChatHistoryBtnDisabled(
      Object.values(resultsLoading).some((value) => value) ||
        Object.values(resultsData).every((arr) => arr.length === 0)
    );
  }, [resultsData, resultsLoading]);

  const onConfirmPrompt = (prompt) => {
    localStorage.setItem("latency_without_rag", null);
    localStorage.setItem("llm_token_latency_without_rag", null);
    localStorage.setItem("latency_with_rag", null);
    localStorage.setItem("llm_token_latency_with_rag", null);
    localStorage.setItem("retriver_latency", null);
    localStorage.setItem("input_token_size_without_rag", null);
    localStorage.setItem("output_token_size_without_rag", null);
    localStorage.setItem("first_token_latency_without_rag", null);
    localStorage.setItem("input_token_size_with_rag", null);
    localStorage.setItem("output_token_size_with_rag", null);
    localStorage.setItem("first_token_latency_with_rag", null);

    setResultsLoading({
      withoutRAG: true,
      withRAG: true,
    });
    setIsPromptInputDisabled(true);

    setResultsData((prevState) => ({
      withoutRAG: [
        ...prevState.withoutRAG,
        {
          question: prompt,
          answer: "",
          sources: [],
        },
      ],
      withRAG: [
        ...prevState.withRAG,
        {
          question: prompt,
          answer: "",
          sources: [],
        },
      ],
    }));

    const urlWithoutRAG = VITE_WITHOUT_RAG_BASE_URL + "/chat_stream";
    const urlWithRAG = VITE_WITH_RAG_BASE_URL + "/chat_stream";

    const payload = {
      query: prompt,
      knowledge_base_id: "default",
    };

    const eventSourceWithRAG = new SSE(urlWithRAG, {
      headers: { "Content-Type": "application/json" },
      payload: JSON.stringify(payload),
    });

    const eventSourceWithoutRAG = new SSE(urlWithoutRAG, {
      headers: { "Content-Type": "application/json" },
      payload: JSON.stringify(payload),
    });

    eventSourceWithRAG.addEventListener("readystatechange", function (e) {
      if (e.readyState === 2) {
        setResultsLoading((prevState) => ({
          ...prevState,
          withRAG: false,
        }));
      }
    });

    eventSourceWithRAG.addEventListener("message", function (e) {
      const currentMsgData = e.data;
      if (currentMsgData !== "") {
        const response = JSON.parse(e.data);
        withRAGAnswer.current = response.streamed_text;
        const sources = Object.values(response.document_metadata).filter((url) => url !== null);
        setResultsData((prevState) => {
          const currentPrompt = prevState.withRAG[prevState.withRAG.length - 1];
          currentPrompt.answer = withRAGAnswer.current;
          if (sources.length > 0) {
            currentPrompt.sources = sources;
          }
          return {
            ...prevState,
            withRAG: [...prevState.withRAG.slice(0, -1), currentPrompt],
          };
        });

        // with rag metrics
        const {
          llm_e2e_latency,
          llm_token_latency,
          input_token_size,
          output_token_size,
          first_token_latency,
          retriver_latency,
        } = response;
        localStorage.setItem("latency_with_rag", llm_e2e_latency);
        localStorage.setItem("llm_token_latency_with_rag", llm_token_latency);
        localStorage.setItem("input_token_size_with_rag", input_token_size);
        localStorage.setItem("output_token_size_with_rag", output_token_size);
        localStorage.setItem("first_token_latency_with_rag", first_token_latency);
        localStorage.setItem("retriver_latency", retriver_latency);
      }
    });
    eventSourceWithRAG.stream();

    eventSourceWithoutRAG.addEventListener("readystatechange", function (e) {
      if (e.readyState === 2) {
        setResultsLoading((prevState) => ({
          ...prevState,
          withoutRAG: false,
        }));
      }
    });

    eventSourceWithoutRAG.addEventListener("message", function (e) {
      const currentMsgData = e.data;
      if (currentMsgData !== "") {
        const response = JSON.parse(e.data);
        withoutRAGAnswer.current = response.streamed_text;
        setResultsData((prevState) => {
          const currentPrompt = prevState.withoutRAG[prevState.withoutRAG.length - 1];
          currentPrompt.answer = withoutRAGAnswer.current;

          return {
            ...prevState,
            withoutRAG: [...prevState.withoutRAG.slice(0, -1), currentPrompt],
          };
        });

        // without rag metrics
        const {
          llm_e2e_latency,
          llm_token_latency,
          input_token_size,
          output_token_size,
          first_token_latency,
        } = response;
        localStorage.setItem("latency_without_rag", llm_e2e_latency);
        localStorage.setItem("llm_token_latency_without_rag", llm_token_latency);
        localStorage.setItem("input_token_size_without_rag", input_token_size);
        localStorage.setItem("output_token_size_without_rag", output_token_size);
        localStorage.setItem("first_token_latency_without_rag", first_token_latency);
      }
    });
    eventSourceWithoutRAG.stream();
  };

  const clearChatHistory = () => {
    setResultsData(resultsDataInitialState);
  };

  const onUploadBtnClick = () => {
    setShowUploadFileDrawer(true);
  };

  const onUploadFileDrawerClose = () => {
    setShowUploadFileDrawer(false);
  };

  const onConfirmUpload = async (file) => {
    onUploadFileDrawerClose();
    if (file instanceof File) {
      setIsUploading(true);
      try {
        const response = await ResultsService.uploadFile(file, file.name);
        if (response.ok) {
          setNotification({
            severity: "success",
            message: (
              <span>
                Your file <b>({file.name})</b> has been successfully uploaded
              </span>
            ),
            open: true,
          });
        } else {
          throw response;
        }
      } catch (error) {
        const { status, statusText } = error;
        setNotification({
          severity: "error",
          message: (
            <span>
              {statusText} ({status}) when uploading your file <b>({file.name})</b>
            </span>
          ),
          open: true,
        });
        console.error(error);
      } finally {
        setIsUploading(false);
      }
    }

    if (Array.isArray(file)) {
      setIsUploading(true);
      try {
        const response = await ResultsService.uploadFileLink(file);
        if (response.ok) {
          setNotification({
            severity: "success",
            message: <span>Your {file.length} file links have been successfully uploaded</span>,
            open: true,
          });
        } else {
          throw response;
        }
      } catch (error) {
        const { status, statusText } = error;
        setNotification({
          severity: "error",
          message: (
            <span>
              {statusText} ({status}) when uploading your file link <b>({file})</b>
            </span>
          ),
          open: true,
        });
        console.error(error);
      } finally {
        setIsUploading(false);
      }
    }
  };

  const onNotificationClose = () => {
    setNotification((prevState) => ({
      ...prevState,
      open: false,
    }));
  };

  return (
    <main className="chat-page">
      <PromptInput
        isDisabled={isPromptInputDisabled}
        isClearChatHistoryBtnDisabled={isClearChatHistoryBtnDisabled}
        isUploading={isUploading}
        onConfirmPrompt={onConfirmPrompt}
        onUploadBtnClick={onUploadBtnClick}
        onClearChatBtnClick={clearChatHistory}
      />
      <ResultsCards data={resultsData} />
      <UploadFileDrawer
        onConfirmUpload={onConfirmUpload}
        onUploadFileDrawerClose={onUploadFileDrawerClose}
        show={showUploadFileDrawer}
      />
      <UploadNotification notification={notification} onNotificationClose={onNotificationClose} />
    </main>
  );
};

export default ChatPage;
