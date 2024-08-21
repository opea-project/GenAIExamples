import styleClasses from './docSum.module.scss'
import { Button, Text, Textarea, Title } from '@mantine/core'
import { FileUpload } from './FileUpload'
import { useEffect, useState } from 'react'
import Markdown from '../Shared/Markdown/Markdown'
import { fetchEventSource } from '@microsoft/fetch-event-source'
import { notifications } from '@mantine/notifications'
import { DOC_SUM_URL } from '../../config'
import { FileWithPath } from '@mantine/dropzone'


const DocSum = () => {
    const [isFile, setIsFile] = useState<boolean>(false);
    const [files, setFiles] = useState<FileWithPath[]>([])
    const [isGenerating, setIsGenerating] = useState<boolean>(false);
    const [value, setValue] = useState<string>('');
    const [fileContent, setFileContent] = useState<string>('');
    const [response, setResponse] = useState<string>('');
    
    useEffect(() => {
        if(isFile){
            setValue('')
        }
    },[isFile])

    useEffect(()=>{
        if (files.length) {
            const reader = new FileReader()
            reader.onload = async () => {
                const text = reader.result?.toString()
                setFileContent(text || '')
            };
            reader.readAsText(files[0])
        }
    },[files])

    
    const handleSubmit = async () => {
        setResponse("")
    if(!isFile && !value){
        notifications.show({
            color: "red",
            id: "input",
            message: "Please Upload Content",
        })
        return 
    }

    setIsGenerating(true)
    const body = {
            messages: isFile ? fileContent : value
    }
    fetchEventSource(DOC_SUM_URL, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Accept": "*/*"
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
                    const res = JSON.parse(msg.data)
                    const logs = res.ops;
                    logs.forEach((log: { op: string; path: string; value: string }) => {
                        if (log.op === "add") {
                            if (
                                log.value !== "</s>" && log.path.endsWith("/streamed_output/-") && log.path.length > "/streamed_output/-".length
                            ) {
                               setResponse(prev=>prev+log.value);
                            }
                        }
                    });
                } catch (e) {
                    console.log("something wrong in msg", e);
                    throw e;
                }
            }
        },
        onerror(err) {
            console.log("error", err);
            setIsGenerating(false) 
            throw err;
        },
        onclose() {
           setIsGenerating(false) 
        },
    });
}


    return (
        <div className={styleClasses.docSumWrapper}>
            <div className={styleClasses.docSumContent}>
                <div className={styleClasses.docSumContentMessages}>
                    <div className={styleClasses.docSumTitle}>
                        <Title order={3}>Doc Summary</Title>
                    </div>
                    <div>
                        <Text size="lg" >Please upload file or paste content for summarization.</Text>
                    </div>
                    <div className={styleClasses.docSumContentButtonGroup}>
                        <Button.Group styles={{ group: { alignSelf: 'center' } }} >
                            <Button variant={!isFile ? 'filled' : 'default'} onClick={() => setIsFile(false)}>Paste Text</Button>
                            <Button variant={isFile ? 'filled' : 'default'} onClick={() => setIsFile(true)}>Upload File</Button>
                        </Button.Group>
                    </div>
                    <div className={styleClasses.docSumInput} >
                        {isFile ? (
                            <div className={styleClasses.docSumFileUpload}>
                                <FileUpload onDropAny={(files) => { setFiles(files) }} />
                            </div>
                        ) : (
                                <div className={styleClasses.docSumPasteText}>
                                <Textarea
                                    autosize
                                    autoFocus
                                    placeholder='Paste the text information you need to summarize'
                                    minRows={10}
                                    value={value}
                                    onChange={(event) => setValue(event.currentTarget.value)}
                                />
                            </div>
                        )}
                    </div>
                    <div>
                        <Button loading={isGenerating} loaderProps={{ type: 'dots' }} onClick={handleSubmit}>Generate Summary</Button>
                    </div>
                    {response && (
                        <div className={styleClasses.docSumResult}>
                            <Markdown content={response} />
                        </div>
                    )}
                    
                </div>
            </div>
        </div >
    )
}

export default DocSum