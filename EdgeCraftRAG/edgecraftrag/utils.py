# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import io, os
from docx.text.paragraph import Paragraph
from typing import Iterator
from unstructured.documents.elements import Image, ElementMetadata
from unstructured.partition.docx import DocxPartitionerOptions
from PIL import Image as Img

GRADIO_TEMP_DIR = os.getenv("GRADIO_TEMP_DIR", "/home/user/gradio_cache")
IMG_OUTPUT_DIR = os.path.join(GRADIO_TEMP_DIR, "pic")
os.makedirs(IMG_OUTPUT_DIR, exist_ok=True)

class DocxParagraphPicturePartitioner:
    @classmethod
    def iter_elements(
        cls, paragraph: Paragraph, opts: DocxPartitionerOptions
    ) -> Iterator[Image]:
        imgs = paragraph._element.xpath('.//pic:pic')
        if imgs:
            for img in imgs:
                embed = img.xpath('.//a:blip/@r:embed')[0]
                related_part = opts.document.part.related_parts[embed]
                image_blob = related_part.blob
                image = Img.open(io.BytesIO(image_blob))
                image_path = os.path.join(IMG_OUTPUT_DIR, str(embed) + related_part.sha1 + ".png")
                image.save(image_path)
                element_metadata = ElementMetadata(
                    image_path=image_path
                )
            yield Image(text="IMAGE", metadata=element_metadata)