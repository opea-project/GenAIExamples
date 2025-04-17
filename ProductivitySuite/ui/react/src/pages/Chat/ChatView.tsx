import { useEffect, useRef, JSX } from "react";
import styles from "./ChatView.module.scss";
import { useLocation, useNavigate, useParams } from "react-router-dom";

import { Box } from "@mui/material";
import PrimaryInput from "@components/PrimaryInput/PrimaryInput";

import { useAppDispatch, useAppSelector } from "@redux/store";
import {
  abortStream,
  conversationSelector,
  doCodeGen,
  doConversation,
  doSummaryFaq,
  getConversationHistory,
  newConversation,
  setSelectedConversationId,
} from "@redux/Conversation/ConversationSlice";
import { userSelector } from "@redux/User/userSlice";
import ChatUser from "@components/Chat_User/ChatUser";
import ChatAssistant from "@components/Chat_Assistant/ChatAssistant";
import { Message, MessageRole } from "@redux/Conversation/Conversation";
import { getCurrentTimeStamp, readFilesAndSummarize } from "@utils/utils";
import ChatSources from "@components/Chat_Sources/ChatSources";

const ChatView = () => {
  const { name } = useAppSelector(userSelector);
  const {
    selectedConversationHistory,
    type,
    sourceLinks,
    sourceFiles,
    temperature,
    token,
    model,
    systemPrompt,
    selectedConversationId,
    onGoingResult,
    isPending,
  } = useAppSelector(conversationSelector);

  const systemPromptObject: Message = {
    role: MessageRole.System,
    content: systemPrompt,
  };

  const dispatch = useAppDispatch();
  const navigate = useNavigate();

  // existing chat
  const { conversation_id } = useParams();

  // new chat
  const { state } = useLocation();
  const initialMessage = state?.initialMessage || null;
  const isSummary = type === "summary" || false;
  const isCodeGen = type === "code" || false;
  const isChat = type === "chat" || false;
  const isFaq = type === "faq" || false;

  const fromHome = useRef(false);
  const newMessage = useRef(false);

  const scrollContainer = useRef<HTMLDivElement | null>(null);
  const autoScroll = useRef<boolean>(true);
  const scrollTimeout = useRef<NodeJS.Timeout | null>(null);

  const messagesBeginRef = useRef<HTMLDivElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Scroll to top of fetched message
  const scrollToTop = () => {
    messagesBeginRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Scroll to the latest message
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleUserScroll = () => {
    if (scrollContainer.current) {
      const { scrollTop, scrollHeight, clientHeight } = scrollContainer.current;

      // Disable autoscroll if the user scrolls up significantly
      if (scrollTop + clientHeight < scrollHeight - 50) {
        autoScroll.current = false;
      } else {
        // Use a timeout to delay re-enabling autoscroll, preventing rapid toggling
        if (scrollTimeout.current) clearTimeout(scrollTimeout.current);
        scrollTimeout.current = setTimeout(() => {
          autoScroll.current = true;
        }, 500); // Delay auto-scroll reactivation
      }
    }
  };

  useEffect(() => {
    const container = scrollContainer.current;
    if (!container) return;

    container.addEventListener("scroll", handleUserScroll);

    return () => {
      container.removeEventListener("scroll", handleUserScroll);
      if (scrollTimeout.current) clearTimeout(scrollTimeout.current);
      if (onGoingResult) dispatch(abortStream());
      console.log("Reset Convo, preserve settings");
      dispatch(newConversation(false));
    };
  }, []);

  useEffect(() => {
    if (onGoingResult && autoScroll.current) {
      scrollToBottom();
    }
  }, [onGoingResult]);

  useEffect(() => {
    if (!name) return;

    // reset view (not full reset)
    // dispatch(newConversation(false)) // moved to useEffect unmount

    // convo starting, new conversation id inboud
    if (!conversation_id) fromHome.current = true;

    // existing convo, load and scroll up
    if (conversation_id && conversation_id !== "new") {
      dispatch(setSelectedConversationId(conversation_id));
      dispatch(
        getConversationHistory({ user: name, conversationId: conversation_id }),
      );
      scrollToTop();
      return;
    } else if (conversation_id === "new") {
      // new convo
      fromHome.current = true;

      if (
        (isSummary || isFaq) &&
        ((sourceLinks && sourceLinks.length > 0) ||
          (sourceFiles && sourceFiles.length > 0) ||
          initialMessage)
      ) {
        // console.log('SUMMARY/FAQ')
        newSummaryOrFaq();
        return;
      }

      if (isCodeGen && initialMessage) {
        // console.log('CODE')
        newCodeGen();
        return;
      }

      if (isChat && initialMessage) {
        // console.log('NEW CHAT')
        newChat();
        return;
      }

      // no match for view, go home
      console.log("Go Home");
      navigate("/");
    }
  }, [conversation_id, name]);

  const newSummaryOrFaq = async () => {
    const userPrompt: Message = {
      role: MessageRole.User,
      content: initialMessage,
      time: getCurrentTimeStamp().toString(),
    };

    let prompt = {
      conversationId: selectedConversationId,
      userPrompt,
      messages: initialMessage,
      model,
      files: sourceFiles,
      temperature,
      token,
      type, // TODO: cannot past type
    };

    doSummaryFaq(prompt);
  };

  const newChat = () => {
    const userPrompt: Message = {
      role: MessageRole.User,
      content: initialMessage,
      time: getCurrentTimeStamp().toString(),
    };

    let messages: Message[] = [];
    messages = [systemPromptObject, ...selectedConversationHistory];

    let prompt = {
      conversationId: selectedConversationId,
      userPrompt,
      messages,
      model,
      temperature,
      token,
      time: getCurrentTimeStamp().toString(), // TODO: cannot past time
      type, // TODO: cannot past type
    };

    doConversation(prompt);
  };

  const newCodeGen = () => {
    const userPrompt: Message = {
      role: MessageRole.User,
      content: initialMessage,
      time: getCurrentTimeStamp().toString(),
    };

    let prompt = {
      conversationId: selectedConversationId,
      userPrompt: userPrompt,
      messages: [],
      model,
      temperature,
      token,
      time: getCurrentTimeStamp().toString(), // TODO: cannot past time
      type, // TODO: cannot past type
    };

    doCodeGen(prompt);
  };

  // ADD to existing conversation
  const addMessage = (query: string) => {
    const userPrompt: Message = {
      role: MessageRole.User,
      content: query,
      time: getCurrentTimeStamp().toString(),
    };

    let messages: Message[] = [];

    messages = [...selectedConversationHistory];

    let prompt = {
      conversationId: selectedConversationId,
      userPrompt,
      messages,
      model,
      temperature,
      token,
      type,
    };

    doConversation(prompt);
  };

  const handleSendMessage = async (messageContent: string) => {
    newMessage.current = true;
    addMessage(messageContent);
  };

  const displayChatUser = (message: Message) => {
    // file post will not have message, will display file.extension instead
    if ((isSummary || isFaq) && !message.content) return;

    // normal message
    if (message.role === MessageRole.User) {
      return <ChatUser content={message.content} />;
    }
  };

  const displayMessage = () => {
    let messagesDisplay: JSX.Element[] = [];

    selectedConversationHistory.map((message, messageIndex) => {
      const timestamp = message.time || Math.random();
      if (message.role !== MessageRole.System) {
        messagesDisplay.push(
          <Box
            className={styles.messageContent}
            key={`${timestamp}_${messageIndex}`}
          >
            {displayChatUser(message)}
            {message.role === MessageRole.Assistant && (
              <ChatAssistant message={message} />
            )}
          </Box>,
        );
      }
    });

    if (onGoingResult) {
      const continueMessage: Message = {
        role: MessageRole.Assistant,
        content: onGoingResult,
        time: Date.now().toString(),
      };

      messagesDisplay.push(
        <Box key={Math.random()} className={styles.messageContent}>
          <ChatAssistant key={`ongoing_ai`} message={continueMessage} />
        </Box>,
      );
    } else if (isPending) {
      const continueMessage: Message = {
        role: MessageRole.Assistant,
        content: "",
        time: Date.now().toString(),
      };

      messagesDisplay.push(
        <Box key={Math.random()} className={styles.messageContent}>
          <ChatAssistant
            key={`ongoing_ai`}
            message={continueMessage}
            pending={true}
          />
        </Box>,
      );
    }

    return messagesDisplay;
  };

  return !selectedConversationHistory ? (
    <></>
  ) : (
    <div className={styles.chatView}>
      <div ref={scrollContainer} className={styles.messagesWrapper}>
        <div ref={messagesBeginRef} />

        <ChatSources />

        {displayMessage()}

        <div ref={messagesEndRef} />
      </div>

      <div className={styles.inputWrapper}>
        <PrimaryInput onSend={handleSendMessage} />
      </div>
    </div>
  );
};

export default ChatView;
