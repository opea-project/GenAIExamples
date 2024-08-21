// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { KeyboardEventHandler, SyntheticEvent, useEffect, useRef, useState } from 'react'
import styleClasses from "./conversation.module.scss"
import { ActionIcon, Group, Textarea, Title, rem } from '@mantine/core'
import { IconArrowRight, IconMessagePlus } from '@tabler/icons-react'
import { conversationSelector, doConversation, getAllConversations, newConversation } from '../../redux/Conversation/ConversationSlice'
import { ConversationMessage } from '../Message/conversationMessage'
import { useAppDispatch, useAppSelector } from '../../redux/store'
import { Message, MessageRole } from '../../redux/Conversation/Conversation'
import { getCurrentTimeStamp } from '../../common/util'

import { ConversationSideBar } from './ConversationSideBar'
import { getPrompts } from '../../redux/Prompt/PromptSlice'
import { userSelector } from '../../redux/User/userSlice'
import PromptTemplate from './PromptTemplate'

type ConversationProps = {
  title: string
}

const Conversation = ({ title }: ConversationProps) => {
  const [prompt, setPrompt] = useState<string>("")

  const dispatch = useAppDispatch();
  const promptInputRef = useRef<HTMLTextAreaElement>(null)

  const { conversations, onGoingResult, selectedConversationId,selectedConversationHistory } = useAppSelector(conversationSelector)
  const { name } = useAppSelector(userSelector)
  const selectedConversation = conversations.find(x => x.id === selectedConversationId)

  const scrollViewport = useRef<HTMLDivElement>(null)

  const toSend = "Enter"

  const systemPrompt: Message = {
    role: MessageRole.System,
    content: "You are helpful assistant",
  };


  const handleSubmit = () => {

    const userPrompt: Message = {
      role: MessageRole.User,
      content: prompt,
      time: getCurrentTimeStamp().toString()
    };
    let messages: Message[] = [];
    // if (selectedConversation) {
    //   messages = selectedConversation.Messages.map(message => {
    //     return { role: message.role, content: message.content }
    //   })
    // }

    messages = [systemPrompt, ...(selectedConversationHistory) ]

    doConversation({
      conversationId: selectedConversationId,
      userPrompt,
      messages,
      model: "Intel/neural-chat-7b-v3-3",
    })
    setPrompt("")
  }

  const scrollToBottom = () => {
    scrollViewport.current!.scrollTo({ top: scrollViewport.current!.scrollHeight })
  }

  useEffect(() => {
    if(name && name!=""){
      dispatch(getPrompts({ promptText: "" }))
      dispatch(getAllConversations({ user: name }))
    }
  }, [name]);

  useEffect(() => {
    scrollToBottom()
  }, [onGoingResult, selectedConversationHistory])

  const handleKeyDown: KeyboardEventHandler = (event) => {
    if (!event.shiftKey && event.key === toSend) {
      handleSubmit()
      setTimeout(() => {
        setPrompt("")
      }, 1)
    }
  }



  const handleNewConversation = () => {
    dispatch(newConversation())
  }

  const handleChange = (event: SyntheticEvent) => {
    event.preventDefault()
    setPrompt((event.target as HTMLTextAreaElement).value)
  }
  return (
    <div className={styleClasses.conversationWrapper}>
      <ConversationSideBar title={title} />
      <div className={styleClasses.conversationContent}>
        <div className={styleClasses.conversationContentMessages}>
          <div className={styleClasses.conversationTitle}>
            <Title order={3}>{selectedConversation?.first_query || ""} </Title>
            <span className={styleClasses.spacer}></span>
            <Group>
              {(selectedConversation || selectedConversationHistory.length > 0) && (
                <ActionIcon onClick={handleNewConversation} disabled={onGoingResult != ""} size={32} variant="default">
                  <IconMessagePlus  />
                </ActionIcon>
              )}
              
            </Group>
          </div>

          <div className={styleClasses.historyContainer} ref={scrollViewport}>

            {!(selectedConversation || selectedConversationHistory.length > 0) && (
              <div className={styleClasses.newConversation}>
                <div className={styleClasses.infoMessages}>
                  <div className="infoMessage">Start by asking a question</div>
                  <div className="infoMessage">You can also upload your Document by clicking on Document icon on top right corner</div>
                </div>
                <PromptTemplate setPrompt={setPrompt} />

              </div>
            )}

            {selectedConversationHistory.map((message,index) => {
              return (message.role!== MessageRole.System && (<ConversationMessage key={`${index}_ai`} date={message.time ? +message.time * 1000 : getCurrentTimeStamp()} human={message.role == MessageRole.User} message={message.content} />))
            })
            }

            {onGoingResult && (
              <ConversationMessage key={`ongoing_ai`} date={Date.now()} human={false} message={onGoingResult} />
            )}
          </div>

          <div className={styleClasses.conversationActions}>
            <Textarea
              radius="xl"
              size="md"
              placeholder="Ask a question"
              ref={promptInputRef}
              onKeyDown={handleKeyDown}
              onChange={handleChange}
              value={prompt}
              rightSectionWidth={42}
              rightSection={
                <ActionIcon onClick={handleSubmit} size={32} radius="xl" variant="filled">
                  <IconArrowRight style={{ width: rem(18), height: rem(18) }} stroke={1.5} />
                </ActionIcon>
              }
            // {...props}
            />
          </div>
        </div>
      </div>
    </div >
  )
}
export default Conversation;
