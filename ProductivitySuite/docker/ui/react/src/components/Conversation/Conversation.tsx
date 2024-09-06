// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { KeyboardEventHandler, SyntheticEvent, useEffect, useRef, useState } from 'react'
import styleClasses from "./conversation.module.scss"
import { ActionIcon, Group, Textarea, Title, Tooltip, rem } from '@mantine/core'
import { IconArrowDown, IconArrowRight, IconArrowUp, IconMessagePlus } from '@tabler/icons-react'
import { conversationSelector, doConversation, getAllConversations, newConversation, setSystemPrompt } from '../../redux/Conversation/ConversationSlice'
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
  const [updateSystemPrompt, setUpdateSystemPrompt] = useState(false)

  const dispatch = useAppDispatch();
  const promptInputRef = useRef<HTMLTextAreaElement>(null)

  const { conversations, onGoingResult, selectedConversationId, selectedConversationHistory, temperature, token, model, systemPrompt } = useAppSelector(conversationSelector)
  const { name } = useAppSelector(userSelector)
  const selectedConversation = conversations.find(x => x.id === selectedConversationId)

  const scrollViewport = useRef<HTMLDivElement>(null)

  const toSend = "Enter"

  const systemPromptObject: Message = {
    role: MessageRole.System,
    content: systemPrompt,
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

    messages = [systemPromptObject, ...(selectedConversationHistory)]

    doConversation({
      conversationId: selectedConversationId,
      userPrompt,
      messages,
      model,
      temperature,
      token
    })
    setPrompt("")
  }

  const scrollToBottom = () => {
    scrollViewport.current!.scrollTo({ top: scrollViewport.current!.scrollHeight })
  }

  useEffect(() => {
    if (name && name != "") {
      dispatch(getPrompts({ promptText: "" }))
      dispatch(getAllConversations({ user: name }))
    }
  }, [name]);

  useEffect(() => {
    scrollToBottom()
  }, [onGoingResult, selectedConversationHistory])

  const handleKeyDown: KeyboardEventHandler = (event) => {
    setUpdateSystemPrompt(false)
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

  const handleSystemPromptChange = (event: SyntheticEvent) => {
    event.preventDefault()
    dispatch(setSystemPrompt((event.target as HTMLTextAreaElement).value))
  }
  return (
    <div className={styleClasses.conversationWrapper}>
      <ConversationSideBar title={title} />
      <div className={styleClasses.conversationContent}>
        <div className={styleClasses.conversationContentMessages} style={updateSystemPrompt ? { gridTemplateRows: `60px 1fr 160px` } : {} }>
          <div className={styleClasses.conversationTitle}>
            <Title order={3} className={styleClasses.title}>{selectedConversation?.first_query || ""} </Title>
            <span className={styleClasses.spacer}></span>
            <Group>
              {(selectedConversation || selectedConversationHistory.length > 0) && (
                <ActionIcon onClick={handleNewConversation} disabled={onGoingResult != ""} size={32} variant="default">
                  <IconMessagePlus />
                </ActionIcon>
              )}
              
            </Group>
          </div>

          <div className={styleClasses.historyContainer} ref={scrollViewport}>

            {!(selectedConversation || selectedConversationHistory.length > 0) && (
              <div className={styleClasses.newConversation}>
                <div className={styleClasses.infoMessages}>
                  <div className="infoMessage">Start by asking a question</div>
                  <div className="infoMessage">You can update the system prompt by clicking on up arrow beside prompt field</div>
                  <div className="infoMessage">You can also upload your Documents in the Data Management Tab</div>
                </div>
                <PromptTemplate setPrompt={setPrompt} />

              </div>
            )}

            {selectedConversationHistory.map((message, index) => {
              return (message.role !== MessageRole.System && (<ConversationMessage key={`${index}_ai`} date={message.time ? +message.time * 1000 : getCurrentTimeStamp()} human={message.role == MessageRole.User} message={message.content} />))
            })
            }

            {onGoingResult && (
              <ConversationMessage key={`ongoing_ai`} date={Date.now()} human={false} message={onGoingResult} />
            )}
          </div>

          <div className={styleClasses.conversationActions}>
            <Textarea
              style={{
                display: updateSystemPrompt ? 'block' : 'none',
                marginBottom: '10px',
                marginLeft:'35px'
              }}
              radius="lg"
              size="md"
              placeholder="system prompt"
              onChange={handleSystemPromptChange}
              value={systemPrompt}
            />
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <Tooltip label="update system prompt">
                <ActionIcon onClick={() => setUpdateSystemPrompt((prev) => !prev)} size={32} radius="xl" variant="filled">
                  {updateSystemPrompt ? (<IconArrowDown style={{ width: rem(18), height: rem(18) }} stroke={1.5} />) :
                    (<IconArrowUp style={{ width: rem(18), height: rem(18) }} stroke={1.5} />)}
                </ActionIcon>
              </Tooltip>
              
              <Textarea
                radius="lg"
                size="md"
                style={{ flex: 90, marginLeft: '3px' }}
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
      </div>
    </div >
  )
}
export default Conversation;
