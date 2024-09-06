// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ActionIcon, Title } from "@mantine/core"

import contextStyles from "../../styles/components/context.module.scss"
import { useAppDispatch, useAppSelector } from "../../redux/store"
import { conversationSelector, deleteConversation, getConversationHistory, setSelectedConversationId } from "../../redux/Conversation/ConversationSlice"
import { useEffect } from "react"
import { userSelector } from "../../redux/User/userSlice"
import { IconTrash } from "@tabler/icons-react"
import Settings from "./settings"
// import { userSelector } from "../../redux/User/userSlice"

export interface ConversationContextProps {
    title: string
}

export function ConversationSideBar({ title }: ConversationContextProps) {
    const { conversations, selectedConversationId } = useAppSelector(conversationSelector)
    const { name } = useAppSelector(userSelector)
    // const user = useAppSelector(userSelector)
    const dispatch = useAppDispatch()

    useEffect(() => {
        if (selectedConversationId != "") {
            dispatch(getConversationHistory({ user: name, conversationId: selectedConversationId }))
        }
    }, [selectedConversationId])

    const handleDeleteConversation = (id: string) => {
        dispatch(deleteConversation({ user: name, conversationId: id }))
    }

    const conversationList = conversations?.map((curr) => (
        <div
            className={contextStyles.contextListItem}
            data-active={selectedConversationId === curr.id || undefined}
            onClick={(event) => {
                event.preventDefault()
                dispatch(setSelectedConversationId(curr.id))
            }}
            key={curr.id}
        >
            <div className={contextStyles.contextItemName} title={curr.first_query}>{curr.first_query}</div>
            {selectedConversationId === curr.id && (
                <ActionIcon onClick={() => handleDeleteConversation(curr.id)} size={30} variant="default">
                    <IconTrash />
                </ActionIcon>
            )}

        </div>
    ))

    return (
        <div className={contextStyles.contextWrapper}>
            <Title order={3} className={contextStyles.contextTitle}>
                {title}
            </Title>
            <div className={contextStyles.contextList}>{conversationList}</div>
            <div className={contextStyles.settings}>
                <Settings />
            </div>
        </div>
    )
}
