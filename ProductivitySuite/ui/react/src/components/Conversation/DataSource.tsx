// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ActionIcon, Button, Container, FileInput, Text, TextInput, Title } from '@mantine/core'
import { IconFile, IconTrash } from '@tabler/icons-react'
import { SyntheticEvent, useEffect, useState } from 'react'
import { useAppDispatch, useAppSelector } from '../../redux/store'
import { conversationSelector, deleteInDataSource, getAllFilesInDataSource, submitDataSourceURL, uploadFile } from '../../redux/Conversation/ConversationSlice'
import styleClasses from './dataSource.module.scss'



export default function DataSource() {
  const [file, setFile] = useState<File | null>();
  const [isFile, setIsFile] = useState<boolean>(true);
  const [url, setURL] = useState<string>("");
  const dispatch = useAppDispatch()
  const { filesInDataSource } = useAppSelector(conversationSelector)
  
  const handleFileUpload = () => {
    if (file)
      dispatch(uploadFile({ file }))
  }

  const handleChange = (event: SyntheticEvent) => {
    event.preventDefault()
    setURL((event.target as HTMLTextAreaElement).value)
  }

  const handleSubmit = () => {
    dispatch(submitDataSourceURL({ link_list: url.split(";") }))
  }

  const handleDelete = (file: string) => {
    dispatch(deleteInDataSource({file}))
  }

  useEffect(()=>{
    dispatch(getAllFilesInDataSource({knowledgeBaseId:"default"}))
  },[])

  return (
    <div className={styleClasses.dataSourceWrapper}>
      <Title order={3}>
        Data Source
      </Title>
      <Text size="sm">
        Please upload your local file or paste a remote file link, and Chat will respond based on the content of the uploaded file.
      </Text>


      <Container styles={{
        root: { paddingTop: '40px', display:'flex', flexDirection:'column', alignItems:'center' }
      }}>
        <Button.Group styles={{ group:{alignSelf:'center'}}} >
          <Button variant={isFile ? 'filled' : 'default'} onClick={() => setIsFile(true)}>Upload File</Button>
          <Button variant={!isFile ? 'filled' : 'default'} onClick={() => setIsFile(false)}>Use Link</Button>
        </Button.Group>
      </Container>

      <Container styles={{root:{paddingTop: '40px'}}}>
        <div>
          {isFile ? (
            <>
              <FileInput value={file} onChange={setFile} placeholder="Choose File" description={"choose a file to upload for RAG"}/>
              <Button style={{marginTop:'5px'}} onClick={handleFileUpload} disabled={!file}>Upload</Button>
            </>
          ) : (
            <>
              <TextInput value={url} onChange={handleChange} placeholder='URL' description={"Use semicolons (;) to separate multiple URLs."} />
                <Button style={{ marginTop: '5px' }} onClick={handleSubmit} disabled={!url}>Upload</Button>
            </>
          )}
        </div>
      </Container>
      <Container styles={{ root: { paddingTop: '40px' } }}>
        <Title order={2} styles={{ root: { margin: '10px' } }}>
          Files
        </Title>
        {filesInDataSource.map(file=> {
          return (
            <div style={{display:'flex' }}>
              <IconFile />
              <Text>{file.name}</Text>
              <ActionIcon onClick={()=>handleDelete(file.name)} size={32} variant="default">
                <IconTrash />
              </ActionIcon>              
            </div>
        )})}
      </Container>
    </div>
  )
}