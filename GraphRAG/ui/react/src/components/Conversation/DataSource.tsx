// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Button, Container, Drawer, FileInput, Text, TextInput } from '@mantine/core'
import { SyntheticEvent, useState } from 'react'
import { useAppDispatch } from '../../redux/store'
import { submitDataSourceURL, uploadFile } from '../../redux/Conversation/ConversationSlice'

type Props = {
  opened: boolean
  onClose: () => void
}

export default function DataSource({ opened, onClose }: Props) {
  const title = "Data Source"
  const [file, setFile] = useState<File | null>();
  const [isFile, setIsFile] = useState<boolean>(true);
  const [url, setURL] = useState<string>("");
  const dispatch = useAppDispatch()
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

  return (
    <Drawer title={title} position="right" opened={opened} onClose={onClose} withOverlay={false}>
      <Text size="sm">
        Please upload your local file or paste a remote file link, and Chat will respond based on the content of the uploaded file.
      </Text>


      <Container styles={{
        root: { paddingTop: '40px', display:'flex', flexDirection:'column', alignItems:'center' }
      }}>
        <Button.Group styles={{ group:{alignSelf:'center'}}} >
          <Button variant={isFile ? 'filled' : 'default'} onClick={() => setIsFile(true)}>Upload FIle</Button>
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
    </Drawer>
  )
}
