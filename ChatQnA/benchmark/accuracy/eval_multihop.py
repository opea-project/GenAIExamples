#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import argparse
import json
import os

import requests
from evals.evaluation.rag_eval import Evaluator
from evals.metrics.ragas import RagasMetric
from evals.metrics.retrieval import RetrievalBaseMetric
from tqdm import tqdm


class MultiHop_Evaluator(Evaluator):
    def get_ground_truth_text(self, data: dict):
        return data["answer"]

    def get_query(self, data: dict):
        return data["query"]

    def get_template(self):
        return None

    def get_reranked_documents(self, query, docs, arguments):
        data = {
            "initial_query": query,
            "retrieved_docs": [{"text": doc} for doc in docs],
            "top_n": 10,
        }
        headers = {"Content-Type": "application/json"}

        response = requests.post(arguments.reranking_endpoint, data=json.dumps(data), headers=headers)
        if response.ok:
            reranked_documents = response.json()["documents"]
            return reranked_documents
        else:
            print(f"Request for retrieval failed due to {response.text}.")
            return []

    def get_retrieved_documents(self, query, arguments):
        data = {"inputs": query}
        headers = {"Content-Type": "application/json"}
        response = requests.post(arguments.tei_embedding_endpoint + "/embed", data=json.dumps(data), headers=headers)
        if response.ok:
            embedding = response.json()[0]
        else:
            print(f"Request for embedding failed due to {response.text}.")
            return []
        data = {
            "text": query,
            "embedding": embedding,
            "search_type": arguments.search_type,
            "k": arguments.retrival_k,
            "fetch_k": arguments.fetch_k,
            "lambda_mult": arguments.lambda_mult,
        }
        response = requests.post(arguments.retrieval_endpoint, data=json.dumps(data), headers=headers)
        if response.ok:
            retrieved_documents = response.json()["retrieved_docs"]
            return [doc["text"] for doc in retrieved_documents]
        else:
            print(f"Request for retrieval failed due to {response.text}.")
            return []

    def get_retrieval_metrics(self, all_queries, arguments):
        print("start to retrieve...")
        metric = RetrievalBaseMetric()
        hits_at_10 = 0
        hits_at_4 = 0
        map_at_10 = 0
        mrr_at_10 = 0
        total = 0
        for data in tqdm(all_queries):
            if data["question_type"] == "null_query":
                continue
            query = data["query"]
            retrieved_documents = self.get_retrieved_documents(query, arguments)
            if arguments.rerank:
                retrieved_documents = self.get_reranked_documents(query, retrieved_documents, arguments)
            golden_context = [each["fact"] for each in data["evidence_list"]]
            test_case = {
                "input": query,
                "golden_context": golden_context,
                "retrieval_context": retrieved_documents,
            }
            results = metric.measure(test_case)
            hits_at_10 += results["Hits@10"]
            hits_at_4 += results["Hits@4"]
            map_at_10 += results["MAP@10"]
            mrr_at_10 += results["MRR@10"]
            total += 1

        # Calculate average metrics over all queries
        hits_at_10 = hits_at_10 / total
        hits_at_4 = hits_at_4 / total
        map_at_10 = map_at_10 / total
        mrr_at_10 = mrr_at_10 / total

        return {
            "Hits@10": hits_at_10,
            "Hits@4": hits_at_4,
            "MAP@10": map_at_10,
            "MRR@10": mrr_at_10,
        }

    def evaluate(self, all_queries, arguments):
        results = []
        accuracy = 0
        index = 0
        for data in tqdm(all_queries):
            if data["question_type"] == "null_query":
                continue

            generated_text = self.send_request(data, arguments)
            data["generated_text"] = generated_text

            # same method with paper: https://github.com/yixuantt/MultiHop-RAG/issues/8
            if data["answer"] in generated_text:
                accuracy += 1
            result = {"id": index, **self.scoring(data)}
            results.append(result)
            index += 1

        valid_results = self.remove_invalid(results)

        try:
            overall = self.compute_overall(valid_results) if len(valid_results) > 0 else {}
        except Exception as e:
            print(repr(e))
            overall = dict()

        overall.update({"accuracy": accuracy / len(results)})
        return overall

    def get_ragas_metrics(self, all_queries, arguments):
        from langchain_huggingface import HuggingFaceEndpointEmbeddings

        embeddings = HuggingFaceEndpointEmbeddings(model=arguments.tei_embedding_endpoint)

        metric = RagasMetric(threshold=0.5, model=arguments.llm_endpoint, embeddings=embeddings)
        all_answer_relevancy = 0
        all_faithfulness = 0
        ragas_inputs = {
            "question": [],
            "answer": [],
            "ground_truth": [],
            "contexts": [],
        }

        for data in tqdm(all_queries):
            if data["question_type"] == "null_query":
                continue
            retrieved_documents = self.get_retrieved_documents(data["query"], arguments)
            generated_text = self.send_request(data, arguments)
            data["generated_text"] = generated_text

            ragas_inputs["question"].append(data["query"])
            ragas_inputs["answer"].append(generated_text)
            ragas_inputs["ground_truth"].append(data["answer"])
            ragas_inputs["contexts"].append(retrieved_documents[:3])

            if len(ragas_inputs["question"]) >= arguments.limits:
                break

        ragas_metrics = metric.measure(ragas_inputs)
        return ragas_metrics


def args_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--service_url", type=str, default="http://localhost:8888/v1/chatqna", help="Service URL address."
    )
    parser.add_argument("--output_dir", type=str, default="./output", help="Directory to save evaluation results.")
    parser.add_argument(
        "--temperature", type=float, default=0.1, help="Controls the randomness of the model's text generation"
    )
    parser.add_argument(
        "--max_new_tokens", type=int, default=1280, help="Maximum number of new tokens to be generated by the model"
    )
    parser.add_argument(
        "--chunk_size", type=int, default=256, help="the maximum number of characters that a chunk can contain"
    )
    parser.add_argument(
        "--chunk_overlap",
        type=int,
        default=100,
        help="the number of characters that should overlap between two adjacent chunks",
    )
    parser.add_argument("--search_type", type=str, default="similarity", help="similarity type")
    parser.add_argument("--retrival_k", type=int, default=10, help="Number of Documents to return.")
    parser.add_argument(
        "--fetch_k", type=int, default=20, help="Number of Documents to fetch to pass to MMR algorithm."
    )
    parser.add_argument(
        "--lambda_mult",
        type=float,
        default=0.5,
        help="Number between 0 and 1 that determines the degree of diversity among the results with 0 corresponding to maximum diversity and 1 to minimum diversity. Defaults to 0.5.",
    )
    parser.add_argument("--dataset_path", default=None, help="Path to the dataset")
    parser.add_argument("--docs_path", default=None, help="Path to the retrieval documents")

    # Retriever related options
    parser.add_argument("--ingest_docs", action="store_true", help="Whether to ingest documents to vector database")
    parser.add_argument("--retrieval_metrics", action="store_true", help="Whether to compute retrieval metrics.")
    parser.add_argument("--ragas_metrics", action="store_true", help="Whether to compute ragas metrics.")
    parser.add_argument("--limits", type=int, default=100, help="Number of examples to be evaluated by llm-as-judge")
    parser.add_argument(
        "--database_endpoint", type=str, default="http://localhost:6007/v1/dataprep/ingest", help="Service URL address."
    )
    parser.add_argument(
        "--embedding_endpoint", type=str, default="http://localhost:6000/v1/embeddings", help="Service URL address."
    )
    parser.add_argument(
        "--tei_embedding_endpoint",
        type=str,
        default="http://localhost:8090",
        help="Service URL address of tei embedding.",
    )
    parser.add_argument(
        "--retrieval_endpoint", type=str, default="http://localhost:7000/v1/retrieval", help="Service URL address."
    )
    parser.add_argument("--rerank", action="store_true", help="Whether to use rerank microservice.")
    parser.add_argument(
        "--reranking_endpoint", type=str, default="http://localhost:8000/v1/reranking", help="Service URL address."
    )
    parser.add_argument("--llm_endpoint", type=str, default=None, help="Service URL address.")
    parser.add_argument(
        "--show_progress_bar", action="store", default=True, type=bool, help="Whether to show a progress bar"
    )
    parser.add_argument("--contain_original_data", action="store_true", help="Whether to contain original data")

    args = parser.parse_args()
    return args


def main():
    args = args_parser()

    evaluator = MultiHop_Evaluator()

    with open(args.docs_path, "r") as file:
        doc_data = json.load(file)

    documents = []
    for doc in doc_data:
        metadata = {"title": doc["title"], "published_at": doc["published_at"], "source": doc["source"]}
        documents.append(doc["body"])

    # save docs to a tmp file
    tmp_corpus_file = "tmp_corpus.txt"
    with open(tmp_corpus_file, "w") as f:
        for doc in documents:
            f.write(doc + "\n")

    if args.ingest_docs:
        evaluator.ingest_docs(tmp_corpus_file, args.database_endpoint, args.chunk_size, args.chunk_overlap)

    with open(args.dataset_path, "r") as file:
        all_queries = json.load(file)

    # get retrieval quality
    if args.retrieval_metrics:
        retrieval_metrics = evaluator.get_retrieval_metrics(all_queries, args)
        print(retrieval_metrics)

    # get rag quality
    if args.ragas_metrics:
        ragas_metrics = evaluator.get_ragas_metrics(all_queries, args)
        print(ragas_metrics)


if __name__ == "__main__":
    main()
