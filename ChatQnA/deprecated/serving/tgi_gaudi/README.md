[TGI-Gaudi](https://github.com/huggingface/tgi-gaudi) provides many parameters aimed at optimizing performance for text generation inference tasks. By optimizing these parameters, users can achieve the best results in terms of inference speed, memory usage, and overall efficiency. These parameters cover various aspects such as maximum sequence length, batch size, Gaudi processor utilization, and environment configurations. By carefully adjusting these parameters according to the specific requirements of the workload and hardware environment, users can unlock the full potential of TGI-Gaudi for the text generation tasks.

# Knowledeges about TGI-Gaudi performance tuning

## Adjusting TGI parameters

Maximum sequence length is controlled by two arguments:

- `--max-input-length` is the maximum possible input prompt length. Default value is `1024`.
- `--max-total-tokens` is the maximum possible total length of the sequence (input and output). Default value is `2048`.

Maximum batch size is controlled by two arguments:

- For prefill operation, please set `--max-prefill-total-tokens` as `bs * max-input-length`, where `bs` is your expected maximum prefill batch size.
- For decode operation, please set `--max-batch-total-tokens` as `bs * max-total-tokens`, where `bs` is your expected maximum decode batch size.
- Please note that batch size will be always padded to the nearest multiplication of `BATCH_BUCKET_SIZE` and `PREFILL_BATCH_BUCKET_SIZE`.

To ensure greatest performance results, at the beginning of each server run, warmup is performed. It's designed to cover major recompilations while using HPU Graphs. It creates queries with all possible input shapes, based on provided parameters (described in this section) and runs basic TGI operations on them (prefill, decode, concatenate).

Except those already mentioned, there are other parameters that need to be properly adjusted to improve performance or memory usage:

- `PAD_SEQUENCE_TO_MULTIPLE_OF` determines sizes of input length buckets. Since warmup creates several graphs for each bucket, it's important to adjust that value proportionally to input sequence length. Otherwise, some out of memory issues can be observed.
- `ENABLE_HPU_GRAPH` enables HPU graphs usage, which is crucial for performance results. Recommended value to keep is `true` .

For more information and documentation about Text Generation Inference, checkout [the README](https://github.com/huggingface/text-generation-inference#text-generation-inference) of the original repo.

## Environment Variable HABANA_VISIBLE_MODULES

To run a workload with part of the available Gaudi processors, you need to set the module IDs of the used Gaudi processors in the environment, HABANA_VISIBLE_MODULES. In general, there are eight Gaudi processors on a node, so the module IDs would be in the range of 0 ~ 7. If you want to run a 4-Gaudi workload, you can set the below before you run the workload:

```bash
export HABANA_VISIBLE_MODULES="0,1,2,3"
```

If you want to run another 4-Gaudi workload in parallel, you can set the below before running the second workload to let it use the rest of the available four Gaudi processors.

```bash
export HABANA_VISIBLE_MODULES="4,5,6,7"
```

Though using partial Gaudi in a workload is possible, only 2-Gaudi and 4-Gaudi scenarios are supported. It is highly recommended to set HABANA_VISIBLE_MODULES using the combinations listed below:

- 2-Gaudi - “0,1”, “2,3”, “4,5” or “6,7”
- 4-Gaudi - “0,1,2,3” or “4,5,6,7”

For the details please check [Multiple_Workloads_Single_Docker](https://docs.habana.ai/en/latest/PyTorch/Reference/PT_Multiple_Tenants_on_HPU/Multiple_Workloads_Single_Docker.html)

## Environment Variable HABANA_VISIBLE_DEVICES

There are some guidelines on setting HABANA_VISIBLE_DEVICES, however, you need to know how to find the mapping between the index and module ID of the Gaudi processors before reading the guidelines. The below command is a sample output of the mapping between index and module ID of the Gaudi processors:

```bash
hl-smi -Q index,module_id -f csv
```

| index | module_id |
| :---: | :-------: |
|   3   |     6     |
|   1   |     4     |
|   2   |     7     |
|   0   |     5     |
|   4   |     2     |
|   6   |     0     |
|   7   |     3     |
|   3   |     1     |

With the mapping between index and module ID, you can set `HABANA_VISIBLE_DEVICES` properly with the guidelines below:

- Mount two Gaudi Processors or four Gaudi Processors in the docker container. Even though using partial Gaudi in a distributed workload is possible, only 2-Gaudi and 4-Gaudi scenario are allowed.
- Since `HABANA_VISIBLE_DEVICES` accepts index instead of module ID, you need to leverage the above command to figure out the corresponding indices for a set of module IDs.
- Avoid mounting the same index on multiple containers. Since multiple workloads might run in parallel, avoiding mounting the same Gaudi to multiple docker containers can prevent reusing the same Gaudi in different workloads.

For the details please check [Multiple Dockers Each with a Single Workload](https://docs.habana.ai/en/latest/PyTorch/Reference/PT_Multiple_Tenants_on_HPU/Multiple_Dockers_each_with_Single_Workload.html)

For the System Management Interface Tool please check [hl-smi](https://docs.habana.ai/en/latest/Management_and_Monitoring/Embedded_System_Tools_Guide/System_Management_Interface_Tool.html)

# Verified Docker commands with tuned parameters for best performance

## Docker command for 70B model

```bash
docker run -p 8080:80 -v $volume:/data --runtime=habana -e HUGGING_FACE_HUB_TOKEN=$HUGGINGFACEHUB_API_TOKEN -e PT_HPU_ENABLE_LAZY_COLLECTIVES=true -e HABANA_VISIBLE_DEVICES="6,7,4,5" -e HABANA_VISIBLE_MODULES="0,1,2,3" -e BATCH_BUCKET_SIZE=22 -e PREFILL_BATCH_BUCKET_SIZE=1 -e MAX_BATCH_PREFILL_TOKENS=5102 -e MAX_BATCH_TOTAL_TOKENS=32256 -e MAX_INPUT_LENGTH=1024 -e PAD_SEQUENCE_TO_MULTIPLE_OF=1024 -e MAX_WAITING_TOKENS=5 -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host tgi_gaudi --model-id $model --sharded true --num-shard 4
```

## Docker command for 13B model

```bash
docker run -p 8080:80 -v $volume:/data --runtime=habana -e HUGGING_FACE_HUB_TOKEN=$HUGGINGFACEHUB_API_TOKEN -e PT_HPU_ENABLE_LAZY_COLLECTIVES=true -e PAD_SEQUENCE_TO_MULTIPLE_OF=128  -e HABANA_VISIBLE_DEVICES="4" -e BATCH_BUCKET_SIZE=16 -e PREFILL_BATCH_BUCKET_SIZE=1 -e MAX_BATCH_PREFILL_TOKENS=4096 -e MAX_BATCH_TOTAL_TOKENS=18432 -e PAD_SEQUENCE_TO_MULTIPLE_OF=1024 -e MAX_INPUT_LENGTH=1024 -e MAX_TOTAL_TOKENS=1152  -e OMPI_MCA_btl_vader_single_copy_mechanism=none --cap-add=sys_nice --ipc=host tgi_gaudi --model-id $model
```
