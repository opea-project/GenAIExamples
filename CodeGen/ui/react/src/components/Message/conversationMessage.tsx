// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { IconAi, IconUser } from "@tabler/icons-react"
import style from "./conversationMessage.module.scss"
import { Group, Text } from "@mantine/core"
import { DateTime } from "luxon"
import Markdown from "../Shared/Markdown/Markdown"

export interface ConversationMessageProps {
  message: string
  human: boolean
  date: number
}

export function ConversationMessage({ human, message, date }: ConversationMessageProps) {
  const dateFormat = () => {
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
      </Group>
      <Text pl={54} pt="sm" size="sm">
        {human? message : (<Markdown content={message}/>)}
      </Text>
    </div>
  )
}
