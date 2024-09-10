// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { KeyboardEventHandler, SyntheticEvent, useEffect, useRef, useState } from 'react'
import styleClasses from "./codeGen.module.scss"
import { ActionIcon, Textarea, Title, rem } from '@mantine/core'
import { IconArrowRight } from '@tabler/icons-react'
import { ConversationMessage } from '../Message/conversationMessage'
import { fetchEventSource } from '@microsoft/fetch-event-source'
import { CODE_GEN_URL } from '../../config'



const CodeGen = () => {
    const [prompt, setPrompt] = useState<string>("")
    const [submittedPrompt, setSubmittedPrompt] = useState<string>("")
    const [response,setResponse] = useState<string>("");
    const promptInputRef = useRef<HTMLTextAreaElement>(null)
    const scrollViewport = useRef<HTMLDivElement>(null)

    const toSend = "Enter"

    const handleSubmit = async () => {
        setResponse("")
        setSubmittedPrompt(prompt)
        const body = {
            messages:prompt
        }
        fetchEventSource(CODE_GEN_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept":"*/*"
            },
            body: JSON.stringify(body),
            openWhenHidden: true,
            async onopen(response) {
                if (response.ok) {
                    return;
                } else if (response.status >= 400 && response.status < 500 && response.status !== 429) {
                    const e = await response.json();
                    console.log(e);
                    throw Error(e.error.message);
                } else {
                    console.log("error", response);
                }
            },
            onmessage(msg) {
                if (msg?.data != "[DONE]") {
                    try {
                        const match = msg.data.match(/b'([^']*)'/);
                        if (match && match[1] != "</s>") {
                            const extractedText = match[1].replace(/\\n/g, "\n");
                            setResponse(prev=>prev+extractedText);
                        }
                    } catch (e) {
                        console.log("something wrong in msg", e);
                        throw e;
                    }
                }
            },
            onerror(err) {
                console.log("error", err);
                setResponse("")
                throw err;
            },
            onclose() {
                setPrompt("")
            },
        });

    }

    const scrollToBottom = () => {
        scrollViewport.current!.scrollTo({ top: scrollViewport.current!.scrollHeight })
    }

    useEffect(() => {
        scrollToBottom()
    }, [response])

    const handleKeyDown: KeyboardEventHandler = (event) => {
        if (!event.shiftKey && event.key === toSend) {
            handleSubmit()
            setTimeout(() => {
                setPrompt("")
            }, 1)
        }
    }

    const handleChange = (event: SyntheticEvent) => {
        event.preventDefault()
        setPrompt((event.target as HTMLTextAreaElement).value)
    }
    return (
        <div className={styleClasses.codeGenWrapper}>
            <div className={styleClasses.codeGenContent}>
                <div className={styleClasses.codeGenContentMessages}>
                    <div className={styleClasses.codeGenTitle}>
                        <Title order={3}>CodeGen</Title>
                    </div>

                    <div className={styleClasses.historyContainer} ref={scrollViewport}>
                        {!submittedPrompt && !response && 
                            (<>
                                <div className="infoMessage">Start by asking a question</div>
                            </>)
                        }
                        {submittedPrompt && (
                            <ConversationMessage key={`_human`} date={Date.now()} human={true} message={submittedPrompt} />
                        )}
                        {response && (
                            <ConversationMessage key={`_ai`} date={Date.now()} human={false} message={response} />
                        )}
                    </div>

                    <div className={styleClasses.codeGenActions}>
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
export default CodeGen;
