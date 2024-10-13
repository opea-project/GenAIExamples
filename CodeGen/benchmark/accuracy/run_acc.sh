
python main.py --model Qwen/CodeQwen1.5-7B-Chat \
  --tasks humaneval \
  --codegen_url $CODEGEN_ENDPOINT \
  --max_length_generation 2048 \
  --batch_size 1  \
  --save_generations \
  --save_references \
  --allow_code_execution

