# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import Any

from edgecraftrag.base import BaseComponent, CompType, NodeParserType
from edgecraftrag.utils import IMG_OUTPUT_DIR, DocxParagraphPicturePartitioner
from llama_index.core.node_parser import HierarchicalNodeParser, SentenceSplitter, SentenceWindowNodeParser
from llama_index.readers.file import UnstructuredReader
from pydantic import model_serializer
from unstructured.partition.docx import register_picture_partitioner


class SimpleNodeParser(BaseComponent, SentenceSplitter):

    # Use super for SentenceSplitter since it's __init__ will cleanup
    # BaseComponent fields
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.comp_type = CompType.NODEPARSER
        self.comp_subtype = NodeParserType.SIMPLE

    def run(self, **kwargs) -> Any:
        for k, v in kwargs.items():
            if k == "docs":
                return self.get_nodes_from_documents(v, show_progress=False)

        return None

    @model_serializer
    def ser_model(self):
        set = {
            "idx": self.idx,
            "parser_type": self.comp_subtype,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
        }
        return set


class HierarchyNodeParser(BaseComponent, HierarchicalNodeParser):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.comp_type = CompType.NODEPARSER
        self.comp_subtype = NodeParserType.HIERARCHY

    def run(self, **kwargs) -> Any:
        for k, v in kwargs.items():
            if k == "docs":
                return self.get_nodes_from_documents(v, show_progress=False)

        return None

    @model_serializer
    def ser_model(self):
        set = {
            "idx": self.idx,
            "parser_type": self.comp_subtype,
            "chunk_size": self.chunk_sizes,
            "chunk_overlap": None,
        }
        return set


class SWindowNodeParser(BaseComponent, SentenceWindowNodeParser):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.comp_type = CompType.NODEPARSER
        self.comp_subtype = NodeParserType.SENTENCEWINDOW

    def run(self, **kwargs) -> Any:
        for k, v in kwargs.items():
            if k == "docs":
                return self.get_nodes_from_documents(v, show_progress=False)

        return None

    @model_serializer
    def ser_model(self):
        set = {
            "idx": self.idx,
            "parser_type": self.comp_subtype,
            "chunk_size": None,
            "chunk_overlap": None,
        }
        return set


class UnstructedNodeParser(BaseComponent, UnstructuredReader):
    """UnstructedNodeParser is a component that processes unstructured data.

    Args:
        chunk_size (int): Size of each chunk for processing. Default is 250.
        chunk_overlap (int): Overlap size between chunks. Default is 0.
        **kwargs: Additional keyword arguments.

    Methods:
        run(**kwargs) -> Any:
            Processes the documents and returns a list of nodes.

        ser_model() -> dict:W
            Serializes the model and returns a dictionary with its attributes.
    """

    def __init__(self, chunk_size: int = 250, chunk_overlap: int = 0, **kwargs):
        super().__init__(**kwargs)
        UnstructuredReader.__init__(self, excluded_metadata_keys=["fake"], **kwargs)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.comp_type = CompType.NODEPARSER
        self.comp_subtype = NodeParserType.UNSTRUCTURED
        # excluded metadata
        self._excluded_embed_metadata_keys = [
            "file_size",
            "creation_date",
            "last_modified_date",
            "last_accessed_date",
            "orig_elements",
        ]
        self._excluded_llm_metadata_keys = ["orig_elements"]
        # PDF image extraction parameters
        self._extract_images_in_pdf = True
        self._image_output_dir = IMG_OUTPUT_DIR
        self._image_language = ["eng", "chi_sim", "chi"]

    def run(self, **kwargs) -> Any:
        for k, v in kwargs.items():
            if k == "docs":
                register_picture_partitioner(DocxParagraphPicturePartitioner)
                nodelist = []
                processed_paths = set()
                for document in v:
                    if "file_path" in document.metadata and document.metadata["file_path"] not in processed_paths:
                        file_path = document.metadata["file_path"]
                        nodes = self.load_data(
                            file=file_path,
                            unstructured_kwargs={
                                "strategy": "hi_res",
                                "extract_images_in_pdf": self._extract_images_in_pdf,
                                "extract_image_block_types": ["Image"],
                                "extract_image_block_output_dir": self._image_output_dir,
                                "languages": self._image_language,
                                "chunking_strategy": "basic",
                                "overlap_all": True,
                                "max_characters": self.chunk_size,
                                "overlap": self.chunk_overlap,
                            },
                            split_documents=True,
                            document_kwargs={
                                "excluded_embed_metadata_keys": self._excluded_embed_metadata_keys,
                                "excluded_llm_metadata_keys": self._excluded_llm_metadata_keys,
                            },
                        )
                        nodelist += nodes
                        processed_paths.add(file_path)
                return nodelist

        return None

    @model_serializer
    def ser_model(self):
        set = {
            "idx": self.idx,
            "parser_type": self.comp_subtype,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
        }
        return set
