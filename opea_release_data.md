# OPEA Release Data

This page shows the benchmark data of GenAIExamples. More data for different examples will be submitted in the future release.

## ChatQnA

| **Docker Images for Test**                            |
| ----------------------------------------------------- |
| opea/embedding-tei:v0.9                               |
| ghcr.io/huggingface/text-embeddings-inference:cpu-1.5 |
| opea/llm-tgi:v0.9                                     |
| ghcr.io/huggingface/tgi-gaudi:2.0.1                   |
| opea/dataprep-redis:v0.9                              |
| redis/redis-stack:7.2.0-v9                            |
| opea/reranking-tei:v0.9                               |
| opea/tei-gaudi:v0.9                                   |
| opea/retriever-redis:v0.9                             |
| opea/chatqna:v0.9                                     |

System Summary:  
1-node, 2x Intel(R) Xeon(R) Platinum 8380 CPU @ 2.30GHz, 40 cores, 270W TDP, HT On, Turbo On, NUMA 2, Integrated Accelerators Available [used]: DLB 0 [0], DSA 0 [0], IAA 0 [0], QAT 0 [0], Total Memory 1024GB (32x32GB DDR4 3200 MT/s [3200 MT/s]), BIOS ETM02, microcode 0xd0003b9, 8x Habana Labs Ltd., 4x MT28800 Family [ConnectX-5 Ex], 4x 7T INTEL SSDPF2KX076TZ, 2x 894.3G SAMSUNG MZ1L2960HCJR-00A07, Ubuntu 22.04.3 LTS, 5.15.0-92-generic. Software: WORKLOAD+VERSION, COMPILER, LIBRARIES, OTHER_SW. Test by Intel as of 08/20/24.

### Performance Data

| 1Node E2E Performance (Sec) | Gaudi nodes | Concurrency | Input | Output | Average Latency | P90 Total latency |
| :-------------------------: | :---------: | :---------: | :---: | :----: | :-------------: | :---------------: |
|      OOB w/o Reranking      |      1      |     128     |  128  |  128   |      5.597      |       7.59        |
|      OOB w/ Reranking       |      1      |     128     |  128  |  128   |      6.003      |       8.123       |

| 2Nodes E2E Performance (Sec) | Gaudi nodes | Concurrency | Input | Output | Average Latency | P90 Total latency |
| :--------------------------: | :---------: | :---------: | :---: | :----: | :-------------: | :---------------: |
|      OOB w/o Reranking       |      2      |     256     |  128  |  128   |      7.05       |       9.122       |
|       OOB w/ Reranking       |      2      |     256     |  128  |  128   |      7.26       |       9.239       |

| 4Nodes E2E Performance (Sec) | Gaudi nodes | Concurrency | Input | Output | Average Latency | P90 Total latency |
| :--------------------------: | :---------: | :---------: | :---: | :----: | :-------------: | :---------------: |
|      OOB w/o Reranking       |      4      |     512     |  128  |  128   |     16.293      |      21.169       |
|       OOB w/ Reranking       |      4      |     512     |  128  |  128   |      17.22      |      21.942       |

Go to Benchmark [README](./ChatQnA/benchmark/README.md) for reproduce steps, tuned performance data will be released soon.

### Accuracy Data

|        Test Case        | Hits@10 | Hits@4 | MAP@10 | MRR@10 |
| :---------------------: | :-----: | :----: | :----: | :----: |
| Retrieval w/o Reranking | 66.16%  | 49.80% | 17.62% | 39.75% |
| Retrieval w/ Reranking  | 72.28%  | 63.24% | 24.97% | 56.79% |

Go to Accuracy [README](https://github.com/opea-project/GenAIEval/tree/main/evals/evaluation/rag_eval#multihop-english-dataset) for reproduce steps.
