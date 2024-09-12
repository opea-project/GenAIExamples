// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { IconAi, IconPlus, IconUser } from "@tabler/icons-react"
import style from "./conversationMessage.module.scss"
import { ActionIcon, Group, Text, Tooltip } from "@mantine/core"
import { DateTime } from "luxon"
import Markdown from "../Shared/Markdown/Markdown"
import { addPrompt } from "../../redux/Prompt/PromptSlice"
import { useAppDispatch } from "../../redux/store"

export interface ConversationMessageProps {
  message: string
  human: boolean
  date: number
}

export function ConversationMessage({ human, message, date }: ConversationMessageProps) {
  const dispatch = useAppDispatch();
  const dateFormat = () => {
    // console.log(date)
    // console.log(new Date(date))
    return DateTime.fromJSDate(new Date(date)).toLocaleString(DateTime.DATETIME_MED)
  }

  return (
    <div className={style.conversationMessage}>
      <Group>
        {human && <IconUser />}
        {!human && <IconAi />}

        <div>
          <Text size="sm">
            {human && "You"} {!human && "Assistant"}
          </Text>
          <Text size="xs" c="dimmed">
            {dateFormat()}
          </Text>
        </div>
        {human && (
          <Tooltip label="Add prompt to prompt registry">
          <ActionIcon onClick={
            () => dispatch(addPrompt({promptText:message}))
        } size={20} variant="filled">
          <IconPlus />
        </ActionIcon>
          </Tooltip>)
        }
      </Group>
      <Text pl={54} pt="sm" size="sm">
        {human? message : (<Markdown content={message}/>)}
      </Text>

      {/* <div className={style.header}>
        {human && <IconUser />}
        {!human && <IconAi />}
      </div>

      <div className={style.message}>{message}</div> */}
    </div>
  )
}
