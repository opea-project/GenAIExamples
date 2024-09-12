// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ScrollAreaAutosize, Title } from "@mantine/core"

import contextStyles from "../../styles/components/context.module.scss"
import { useAppDispatch, useAppSelector } from "../../redux/store"
import { conversationSelector, setSelectedConversationId } from "../../redux/Conversation/ConversationSlice"
// import { userSelector } from "../../redux/User/userSlice"

export interface ConversationContextProps {
    title: string
}

export function ConversationSideBar({ title }: ConversationContextProps) {
    const { conversations, selectedConversationId } = useAppSelector(conversationSelector)
    // const user = useAppSelector(userSelector)
    const dispatch = useAppDispatch()

    const conversationList = conversations?.map((curr) => (
        <div
            className={contextStyles.contextListItem}
            data-active={selectedConversationId === curr.conversationId || undefined}
            onClick={(event) => {
                event.preventDefault()
                dispatch(setSelectedConversationId(curr.conversationId))
                // dispatch(getConversationById({ user, conversationId: curr.conversationId }))
            }}
            key={curr.conversationId}
        >
            <div className={contextStyles.contextItemName} title={curr.title}>{curr.title}</div>
        </div>
    ))

    return (
        <div className={contextStyles.contextWrapper}>
            <Title order={3} className={contextStyles.contextTitle}>
                {title}
            </Title>
            <ScrollAreaAutosize type="hover" scrollHideDelay={0}>
                <div className={contextStyles.contextList}>{conversationList}</div>
            </ScrollAreaAutosize>
        </div>
    )
}
