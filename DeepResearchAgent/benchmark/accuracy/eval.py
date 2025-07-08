import argparse
import concurrent.futures
import json
import os
import time
from typing import Any, Tuple
from datasets import load_dataset
import requests

def load_questions(dataset_names: list[str] | None = None) -> list[dict[str, str]]:
    """
    Load questions from the specified Hugging Face dataset configurations.

    Args:
        dataset_names: List of dataset configurations to load
                      Options:
                          "smolagents:simpleqa",
                          "hotpotqa",
                          "simpleqa",
                          "together-search-bench"
                      If None, all available configurations except hotpotqa will be loaded

    Returns:
        List of question-answer pairs
    """
    if dataset_names is None:
        dataset_names = ["smolagents:simpleqa"]

    all_questions = []

    for dataset_name in dataset_names:
        print(f"Loading dataset: {dataset_name}")

        try:
            if dataset_name == "together-search-bench":
                # Load Together-Search-Bench dataset
                dataset_path = "togethercomputer/together-search-bench"
                ds = load_dataset(dataset_path)
                if "test" in ds:
                    split_data = ds["test"]
                else:
                    print(
                        f"No 'test' split found in dataset at {dataset_path}")
                    continue

                for i in range(len(split_data)):
                    item = split_data[i]
                    question_data = {
                        "question": item["question"],
                        "answer": item["answer"],
                        "dataset": item.get("dataset", "together-search-bench"),
                    }
                    all_questions.append(question_data)

                print(
                    f"Loaded {len(split_data)} questions from together-search-bench dataset")
                continue

            elif dataset_name == "hotpotqa":
                # Load HotpotQA dataset (using distractor version for validation)
                ds = load_dataset("hotpotqa/hotpot_qa",
                                  "distractor", trust_remote_code=True)
                split_name = "validation"
            elif dataset_name == "simpleqa":
                ds = load_dataset("basicv8vc/SimpleQA")
                split_name = "test"
            else:
                # Strip "smolagents:" prefix when loading the dataset
                actual_dataset = dataset_name.split(":")[-1]
                ds = load_dataset("smolagents/benchmark-v1", actual_dataset)
                split_name = "test"

        except Exception as e:
            print(f"Failed to load dataset {dataset_name}: {str(e)}")
            continue  # Skip this dataset if it fails to load


        print(f"Dataset structure for {dataset_name}: {ds}")
        print(f"Available splits: {list(ds)}")

        split_data = ds[split_name]  # type: ignore

        for i in range(len(split_data)):
            item = split_data[i]

            if dataset_name == "hotpotqa":
                # we remove questions that are easy or medium (if any) just to reduce the number of questions
                if item["level"] != "hard":
                    continue

                question_data = {
                    "question": item["question"],
                    "answer": item["answer"],
                    "dataset": dataset_name,
                }
            elif dataset_name == "simpleqa":
                # Handle SimpleQA dataset format
                question_data = {
                    "question": item["problem"],
                    "answer": item["answer"],
                    "dataset": dataset_name,
                }
            else:
                question_data = {
                    "question": item["question"],
                    "answer": item["true_answer"],
                    "dataset": dataset_name,
                }

            all_questions.append(question_data)

    print(f"Loaded {len(all_questions)} questions in total")
    return all_questions


def process_single_question(
    question_data: dict[str, str],
    idx: int,
    total: int,
    callback: ScoringFunction,
    agent_config: str = "../configs/base_llm_config.yaml",
) -> dict[str, Any]:
    """
    Process a single benchmark question with the agent.

    Args:
        question_data: Dictionary containing question and answer
        idx: Index of the current question
        total: Total number of questions
        model: LLM model to use
        max_steps: Maximum steps for the agent
        callback: Optional callback function for evaluation
        agent_config: Path to the agent config (default: ../configs/base_llm_config.yaml)

    Returns:
        Dictionary with question, answers and evaluation results
    """
    question = question_data["question"]
    correct_answer = question_data["answer"]


    """


    """

    result = Result(question=question, agent_answer=agent_answer,
                    correct_answer=correct_answer)

    evaluation = callback(result)

    single_benchmark_result = {
        "question": question,
        "correct_answer": correct_answer,
        "agent_answer": agent_answer,
        "evaluation": evaluation,
        "metadata": {k: v for k, v in question_data.items() if k not in ["question", "answer"]},
    }
    print(single_benchmark_result)

    return single_benchmark_result


def run_benchmark(
    questions: list[dict[str, str]],
    callback: ScoringFunction,
    agent_config: str = "../configs/base_llm_config.yaml",
    max_workers: int = 2,
) -> Tuple[float, list[dict[str, Any]]]:
    """
    Run the benchmark on a list of questions concurrently.

    Args:
        questions: List of question-answer pairs
        callback: Function to evaluate agent answers against ground truth
        model: LLM model to use for the agent
        max_steps: Maximum number of steps the agent can take
        max_workers: Number of concurrent threads to use
        agent_type: Type of agent to create (default: research_agent)

    Returns:
        Tuple of (accuracy score, detailed results)
    """

    results = []
    total_questions = len(questions)
    details = []

    # Use ThreadPoolExecutor to run questions concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Create a list of future objects
        future_to_idx = {
            executor.submit(process_single_question, question_data, idx, total_questions, callback, agent_config): idx
            for idx, question_data in enumerate(questions)
        }

        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                result = future.result()
                results.append(result["evaluation"])
                details.append(result)
                print(f"Completed question {idx+1}/{total_questions}")
            except Exception as exc:
                import traceback
                traceback.print_exc()
                print(f"Question {idx+1} generated an exception: {exc}")
                results.append(0)
                details.append({"question": questions[idx]["question"], "agent_answer": str(
                    exc), "evaluation": 0})

    return sum(results) / len(results), details


def main():
    """
    Main function to run the benchmark.
    """

    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Run scoring with benchmarking options")
    parser.add_argument(
        "--datasets",
        nargs="+",
        choices=["smolagents:simpleqa", "hotpotqa",
                 "simpleqa", "together-search-bench"],
        help="Specific datasets to load (default: all)",
        default=["together-search-bench"],
    )
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit number of questions to process (default: all)")
    parser.add_argument(
        "--service-url",
        default="http://localhost:8022/v1/deep_research_agent",
        help="the endpoint of deep research agent.",
    )
    parser.add_argument(
        "--llm-endpoint",
        default="http://localhost:8000/v1/",
        help="llm service for llm-as-judge.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=1,
        help="Number of concurrent workers (default: 1)",
    )

    args = parser.parse_args()

    questions = load_questions(args.datasets)


    if args.limit is not None:
        questions = questions[: args.limit]
        print(f"Limited to {len(questions)} questions")

    results, details = run_benchmark(
        questions,
        callback=llm_as_a_judge_scoring,
        max_workers=args.max_workers,
        agent_config=args.agent_config,
    )

    print(f"Completed benchmark with {results} accuracy")

    benchmark_results_dir = os.path.join(os.path.dirname(
        os.path.dirname(__file__)), "benchmark", "benchmark_results")
    os.makedirs(benchmark_results_dir, exist_ok=True)

    output_file = os.path.join(
        benchmark_results_dir,
        f"benchmark_{'_'.join(args.datasets)}_{time.strftime('%Y-%m-%d_%H-%M-%S', time.localtime())}.json",
    )

    output_data = {
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "datasets": args.datasets,
            "agent_config": args.agent_config,
            "scoring_method": "llm_as_a_judge_scoring",
            "sample_count": len(questions),
        },
        "overall_accuracy": results,
        "question_details": details,
    }

    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)

    return results


if __name__ == "__main__":
    main()

