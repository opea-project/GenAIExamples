

python main.py --model $1 \
  --tasks humaneval \
  --codegen_url $2 \
  --max_length_generation 2048 \
  --batch_size 1  \
  --save_generations \
  --save_references \
  --allow_code_execution

