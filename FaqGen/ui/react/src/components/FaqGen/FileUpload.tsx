import { Group, Text, rem } from '@mantine/core';
import { IconUpload, IconCloudUpload, IconX, IconFile } from '@tabler/icons-react';
import { } from '@tabler/icons-react';
import { Dropzone, DropzoneProps, FileWithPath } from '@mantine/dropzone';
import '@mantine/dropzone/styles.css';
import { useState } from 'react';

export function FileUpload(props: Partial<DropzoneProps>) {
    const [files, setFiles] = useState<FileWithPath[]>([])
    return (
        <Dropzone
            onDrop={(files) => { setFiles(files) }}
            onReject={() => { }}
            maxSize={5 * 1024 ** 2}
            multiple={false}
            accept={[
                // MIME_TYPES.png,
                // MIME_TYPES.jpeg,
                // MIME_TYPES.svg,
                // MIME_TYPES.gif,
                // MIME_TYPES.webp,
                // MIME_TYPES.doc,
                // MIME_TYPES.docx,
                // MIME_TYPES.pdf,
                // MIME_TYPES.xls,
                // MIME_TYPES.xlsx,
                "text/plain",
                // "application/json"
            ]}
            style={{ height: '220px', width: '100%', borderColor: 'var(--mantine-color-blue-6)' }}
            {...props}
        >
            <Group justify="center" gap="xl" mih={220} style={{ pointerEvents: 'none' }}>
                <Dropzone.Accept>
                    <IconUpload
                        style={{ width: rem(52), height: rem(52), color: 'var(--mantine-color-blue-6)' }}
                        stroke={1.5}
                    />
                </Dropzone.Accept>
                <Dropzone.Reject>
                    <IconX
                        style={{ width: rem(52), height: rem(52), color: 'var(--mantine-color-red-6)' }}
                        stroke={1.5}
                    />
                </Dropzone.Reject>
                <Dropzone.Idle>
                    {files.length > 0 ? (<IconFile
                        style={{ width: rem(52), height: rem(52), color: 'var(--mantine-color-dimmed)' }}
                        stroke={1.5}
                    />) : (<IconCloudUpload
                        style={{ width: rem(52), height: rem(52), color: 'var(--mantine-color-dimmed)' }}
                        stroke={1.5}
                    />)}
                </Dropzone.Idle>
                {files.length > 0 ? (
                    <div>
                        {files.map(file => (
                            <Text size="md" c="dimmed" inline mt={7}>
                                {file.name}
                            </Text>
                        ))}
                        </div>
            
                ) : (
                    <div>
                        <Text size="xl" inline>
                            Drag your file here or click to select file
                        </Text>
                        <Text size="md" c="dimmed" inline mt={7}>
                            .txt
                            {/* pdf, txt, doc, docx, png, jpg ..so on  */}
                        </Text>
                    </div>

                )}
            </Group>
        </Dropzone>
    );
}