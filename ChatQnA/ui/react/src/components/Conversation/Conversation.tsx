// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { KeyboardEventHandler, SyntheticEvent, useEffect, useRef, useState } from 'react'
import styleClasses from "./conversation.module.scss"
import { ActionIcon, Group, Textarea, Title, rem } from '@mantine/core'
import { IconArrowRight, IconFilePlus, IconMessagePlus } from '@tabler/icons-react'
import { conversationSelector, doConversation, newConversation } from '../../redux/Conversation/ConversationSlice'
import { ConversationMessage } from '../Message/conversationMessage'
import { useAppDispatch, useAppSelector } from '../../redux/store'
import { Message, MessageRole } from '../../redux/Conversation/Conversation'
import { getCurrentTimeStamp } from '../../common/util'
import { useDisclosure } from '@mantine/hooks'
import DataSource from './DataSource'
import { ConversationSideBar } from './ConversationSideBar'

type ConversationProps = {
  title:string
}

const Conversation = ({ title }: ConversationProps) => {

  const [prompt, setPrompt] = useState<string>("")
  const promptInputRef = useRef<HTMLTextAreaElement>(null)
  const [fileUploadOpened, { open: openFileUpload, close: closeFileUpload }] = useDisclosure(false);

  const { conversations, onGoingResult, selectedConversationId } = useAppSelector(conversationSelector)
  const dispatch = useAppDispatch();
  const selectedConversation = conversations.find(x=>x.conversationId===selectedConversationId)

  const scrollViewport = useRef<HTMLDivElement>(null)

  const toSend = "Enter"

  const systemPrompt: Partial<Message> = {
    role: MessageRole.System,
    content: "You are helpful assistant",
  };


  const handleSubmit = () => {

    const userPrompt: Message = {
      role: MessageRole.User,
      content: prompt,
      time: getCurrentTimeStamp()
    };
    let messages: Partial<Message>[] = [];
    if(selectedConversation){
      messages  = selectedConversation.Messages.map(message => {
        return {role:message.role, content:message.content}
      })
    }
    
    messages = [systemPrompt, ...messages]

    doConversation({
      conversationId: selectedConversationId,
      userPrompt,
      messages,
      model: "Qwen/Qwen2-7B",
    })
    setPrompt("")
  }

  const scrollToBottom = () => {
    scrollViewport.current!.scrollTo({ top: scrollViewport.current!.scrollHeight })
  }

  useEffect(() => {
    scrollToBottom()
  }, [onGoingResult, selectedConversation?.Messages])

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
      <ConversationSideBar title={title}/>
      <div className={styleClasses.conversationContent}>
        <div className={styleClasses.conversationContentMessages}>
          <div className={styleClasses.conversationTitle}>
            <Title order={3}>{selectedConversation?.title || ""} </Title>
            <span className={styleClasses.spacer}></span>
            <Group>
              {selectedConversation && selectedConversation?.Messages.length > 0 && (
                <ActionIcon onClick={handleNewConversation} disabled={onGoingResult != ""} size={32} variant="default">
                  <IconMessagePlus />
                </ActionIcon>
              )}
              <ActionIcon onClick={openFileUpload} size={32} variant="default">
                <IconFilePlus />
              </ActionIcon>
            </Group>
          </div>

          <div className={styleClasses.historyContainer} ref={scrollViewport}>

            {!selectedConversation && (
              <>
                <div className="infoMessage">Start by asking a question</div>
                <div className="infoMessage">You can also upload your Document by clicking on Document icon on top right corner</div>
              </>
            )}

            {selectedConversation?.Messages.map((message) => {
              return (<ConversationMessage key={`_ai`} date={message.time * 1000} human={message.role == MessageRole.User} message={message.content} />)
              })
            }

            {onGoingResult && (
              <ConversationMessage key={`_ai`} date={Date.now()} human={false} message={onGoingResult} />
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
      <DataSource opened={fileUploadOpened} onClose={closeFileUpload} />
    </div >
  )
}
export default Conversation;
