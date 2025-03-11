Copyright (C) 2024 Advanced Micro Devices, Inc.

# Deploy Translation application

## 1. Clone repo and build Docker images

### 1.1. Cloning GenAIComps repo

Create an empty directory in home directory and navigate to it:

```bash
mkdir ~/translation-apps && cd ~/translation-apps
```

Cloning GenAIExamples repo for build Docker images:

```bash
git clone https://github.com/opea-project/GenAIExamples.git
```

### 1.2. Navigate to repo directory and switching to the desired version of the code:

If you are using the main branch, then you do not need to make the transition, the main branch is used by default

```bash
cd GenAIExamples
```

If you are using a specific branch or tag, then we perform git checkout to the desired version.

```bash
### Replace "v1.2" with the code version you need (branch or tag)
cd GenAIExamples && git checkout v1.2
```

### 1.3. Build Docker images

```bash
cd docker_image_build
git clone git clone https://github.com/opea-project/GenAIComps.git
service_list="translation translation-ui llm-textgen nginx vllm-rocm"
docker compose -f build.yaml build ${service_list} --no-cache
```

### 1.8. Checking for the necessary Docker images

After assembling the images, you can check their presence in the list of available images using the command:

```bash
docker image ls
```

The output of the command should contain images:

- opea/llm-vllm-rocm:latest
- opea/llm-textgen:latest
- opea/translation:latest
- opea/nginx:latest
- opea/retriever:latest
- opea/nginx:latest
- opea/llm-vllm-rocm
- opea/chatqna:latest
- opea/chatqna-ui:latest
- redis/redis-stack:7.2.0-v9
- ghcr.io/huggingface/text-embeddings-inference:cpu-1.5

## 2. Set deploy environment variables

### Setting variables in the operating system environment

#### Set variable HUGGINGFACEHUB_API_TOKEN:

```bash
### Replace the string 'your_huggingfacehub_token' with your HuggingFacehub repository access token.
export HUGGINGFACEHUB_API_TOKEN='your_huggingfacehub_token'
```

#### Set variables value in set_env_vllm.sh file:

```bash
cd ~/chatqna-apps/GenAIExamples/ChatQnA/docker_compose/amd/gpu/rocm
### The example uses the Nano text editor. You can use any convenient text editor
nano set_env_vllm.sh
```

If you are in a proxy environment, also set the proxy-related environment variables:

```bash
export http_proxy="Your_HTTP_Proxy"
export https_proxy="Your_HTTPs_Proxy"
```

Set the values of the variables:

- **HOST_IP, HOST_IP_EXTERNAL** - These variables are used to configure the name/address of the service in the operating system environment for the application services to interact with each other and with the outside world.

  If your server uses only an internal address and is not accessible from the Internet, then the values for these two variables will be the same and the value will be equal to the server's internal name/address.

  If your server uses only an external, Internet-accessible address, then the values for these two variables will be the same and the value will be equal to the server's external name/address.

  If your server is located on an internal network, has an internal address, but is accessible from the Internet via a proxy/firewall/load balancer, then the HOST_IP variable will have a value equal to the internal name/address of the server, and the EXTERNAL_HOST_IP variable will have a value equal to the external name/address of the proxy/firewall/load balancer behind which the server is located.

  We set these values in the file set_env_vllm.sh

- **Variables with names like "%%%%\_PORT"** - These variables set the IP port numbers for establishing network connections to the application services.
  The values shown in the file set_env_vllm.sh they are the values used for the development and testing of the application, as well as configured for the environment in which the development is performed. These values must be configured in accordance with the rules of network access to your environment's server, and must not overlap with the IP ports of other applications that are already in use.

#### Run set environment script:

```bash
. set_env_vllm.sh
```

## 3. Deploy application

### 3.1. Deploying applications using Docker Compose

```bash
docker compose -f compose_vllm.yaml up -d --force-recreate
```

After starting the containers, you need to view their status with the command:

```bash
docker compose -f compose_vllm.yaml ps
```

The following containers should be running:

- chatqna-backend-server
- chatqna-dataprep-service
- chatqna-nginx-server
- chatqna-redis-vector-db
- chatqna-retriever
- chatqna-tei-embedding-service
- chatqna-tei-reranking-service
- chatqna-ui-server
- chatqna-vllm-service

Containers should not restart.

#### 3.1.1. Configuring GPU forwarding

By default, in the Docker Compose file, compose_vllm.yaml is configured to forward all GPUs to the chatqna-vllm-service container. To use certain GPUs, you need to configure the forwarding of certain devices from the host system to the container.
The configuration must be done in:

```yaml
services:
  #######
  chatqna-vllm-service:
    devices:
```

Example for set isolation for 1 GPU

```
      - /dev/dri/card0:/dev/dri/card0
      - /dev/dri/renderD128:/dev/dri/renderD128
```

Example for set isolation for 2 GPUs

```
      - /dev/dri/card0:/dev/dri/card0
      - /dev/dri/renderD128:/dev/dri/renderD128
      - /dev/dri/card1:/dev/dri/card1
      - /dev/dri/renderD129:/dev/dri/renderD129
```

### 3.2. Checking the application services

#### 3.2.1. Checking chatqna-vllm-service

Verification is performed in two ways:

- Checking the container logs

  ```bash
  docker logs chatqna-vllm-service
  ```

  A message like this should appear in the logs:

  ```commandline
  INFO:     Started server process [1]
  INFO:     Waiting for application startup.
  INFO:     Application startup complete.
  INFO:     Uvicorn running on http://0.0.0.0:8011 (Press CTRL+C to quit)
  ```

- Сhecking the response from the service
  ```bash
  ### curl request
  curl http://${HOST_IP}:${CHATQNA_VLLM_SERVICE_PORT}/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
      "model": "meta-llama/Meta-Llama-3-8B-Instruct",
      "prompt": "What is a Deep Learning?",
      "max_tokens": 30,
      "temperature": 0
  }'
  ```
  The response from the service must be in the form of JSON:
  ```json
  {
    "id": "cmpl-1d7d175d36d0491cba3abaa8b5bd6991",
    "object": "text_completion",
    "created": 1740411135,
    "model": "meta-llama/Meta-Llama-3-8B-Instruct",
    "choices": [
      {
        "index": 0,
        "text": " Deep learning is a subset of machine learning that involves the use of artificial neural networks to analyze and interpret data. It is called \"deep\" because it",
        "logprobs": null,
        "finish_reason": "length",
        "stop_reason": null,
        "prompt_logprobs": null
      }
    ],
    "usage": { "prompt_tokens": 7, "total_tokens": 37, "completion_tokens": 30, "prompt_tokens_details": null }
  }
  ```
  The value of choice.text must contain a response from the service that makes sense.
  If such a response is present, then the chatqna-vllm-service is considered verified.

#### 3.2.2. Checking chatqna-redis-vector-db

The verification is performed using an analog of the service logs

```bash
docker logs chatqna-redis-vector-db
```

if the log output contains the string "Ready to accept tcp connections" and there are no obvious errors, then the service is considered successfully started.

#### 3.2.3. Checking chatqna-dataprep-service

It is performed using requests to the service

**Checking Upload file**

```bash
wget https://raw.githubusercontent.com/opea-project/GenAIComps/v1.1/comps/retrievers/redis/data/nke-10k-2023.pdf
curl -X POST "http://${HOST_IP}:${CHATQNA_REDIS_DATAPREP_PORT}/v1/dataprep/ingest" \
     -H "Content-Type: multipart/form-data" \
     -F "files=@./nke-10k-2023.pdf"
```

The response from the service must be in the form of JSON:

```json
{ "status": 200, "message": "Data preparation succeeded" }
```

If the response contains the string "Data preparation succeeded", then we consider the file upload operation to be successful.

**Checking the content list output:**

```bash
curl -X POST "http://${HOST_IP}:${CHATQNA_REDIS_DATAPREP_PORT}/v1/dataprep/get" \
     -H "Content-Type: application/json"
```

The response from the service must be in the form of JSON:

```json
[{ "name": "nke-10k-2023.pdf", "id": "nke-10k-2023.pdf", "type": "File", "parent": "" }]
```

If the response contains links to the content, then we consider the verification of the content listing operation to be successful.

**Checking the delete file:**

```bash
curl -X POST "http://${HOST_IP}:${CHATQNA_REDIS_DATAPREP_PORT}/v1/dataprep/delete" \
     -d '{"file_path": "nke-10k-2023.pdf"}' \
     -H "Content-Type: application/json"
```

The response from the service must be in the form of JSON:

```json
{ "status": true }
```

If the response contains "status:true", then we consider the verification of the file deletion operation to be successful.

#### 3.2.4. Checking chatqna-tei-embedding-service

It is performed using requests to the service

```bash
curl http://${HOST_IP}:${CHATQNA_TEI_EMBEDDING_PORT}/embed \
    -X POST \
    -d '{"inputs":"What is Deep Learning?"}' \
    -H 'Content-Type: application/json'
```

The response from the service must be in the form of JSON:

```json
[
  [
    0.00037115702, -0.06356819, 0.0024758505, -0.012360337, 0.050739925, 0.023380278, 0.022216318, 0.0008076447,
    -0.0003412891, -0.033479452, -0.024872458, 0.0064700204, -0.00731641, 0.06648339, 0.0013361155, 0.047004532,
    0.062838696, -0.021005465, 0.011151533, 0.044124223, -0.050683793, -0.062093593, -0.03992629, 0.017758112,
    -0.0013727234, 0.0022603935, -0.04363493, 0.012822347, -0.02408198, 0.011079012, 0.028809752, -0.008898206,
    0.037047423, -0.027456092, 0.016162485, 0.04173568, -0.039396558, -0.035203997, -0.022387454, -0.019808905,
    -0.01864915, -0.042313505, -0.0120891025, 0.048949677, -0.08100209, 0.017953783, -0.12084276, 0.0024097406,
    -0.022705944, -0.012279724, -0.07547717, 0.051262986, 0.03203861, -0.019056482, 0.04271625, 0.015248945,
    0.004222296, -0.08073051, 0.010240495, -0.05635268, 0.052041706, 0.03712775, -0.01854724, -0.02750096,
    -0.00096631586, -0.026202224, 0.024124105, 0.042904165, -0.023528703, -0.0034956702, -0.028778492, 0.029217377,
    -0.020601744, -0.0049860086, -0.05246627, -0.011162583, 0.012888553, 0.014507065, 0.08219481, -0.008273658,
    0.0036607939, 0.062248874, 0.042562004, 0.03170365, 0.0046070544, 0.00065274147, -0.019365542, -0.004698561,
    -0.0449053, 0.02275239, 0.01039843, -0.053169794, 0.060175993, 0.051545423, 0.014204941, 0.0076600607, 0.013906856,
    -0.035385784, -0.011683805, -0.014732695, -0.02331647, -0.059045117, -0.016870823, -0.014698294, -0.048483565,
    0.026726946, 0.05227064, -0.013973138, 0.014551645, -0.019573484, -0.0013427412, -0.008475066, -0.0025058866,
    -0.048502546, -0.043069497, -0.0077841803, -0.016379999, 0.0037450534, -0.025010578, -0.04592572, 0.034388185,
    0.03836159, 0.0019682923, 0.021373231, -0.03391387, 0.015393363, 0.003937917, 0.01832765, 0.0045520393, -0.02696203,
    0.020696502, 0.016930614, -0.007926859, 0.021834886, -0.014779224, 0.00073025556, -0.020250296, 0.006635754,
    0.025785012, 0.009847587, -0.002533611, -0.057919327, 0.03010091, -0.03554674, 0.054443054, -0.015446536,
    -0.0079982905, -0.0042982297, -0.018884834, 0.0027541735, -0.044417977, 0.05555447, -0.018901609, -0.049503766,
    0.008309782, 0.039867956, -0.0004423662, 0.0059798234, 0.03447887, 0.023205558, 0.058959927, -0.019526886,
    -0.054637823, -0.009800092, -0.024515655, -0.05426387, 0.05535355, 0.024482403, -0.020081121, 0.024965372,
    -0.002176406, -0.011429285, 0.02036594, -0.011996402, 0.011601014, 0.04732072, 0.028819714, 0.03407571, 0.0430521,
    0.05145868, -0.065615594, 0.046596047, -0.008815781, -0.0063788523, -0.044762302, -0.03171996, 0.04966251,
    -0.010887125, 0.036779672, 0.014379601, -0.06393863, -0.036413074, -0.033719108, -0.037734028, 0.033251368,
    -0.01693572, -0.015116194, 0.082118206, -0.011095621, 0.046565905, 0.054315507, -0.051471975, 0.0153609,
    -0.016379755, -0.02725454, 0.029903106, 0.01588181, -0.043773234, -0.0034126595, 0.0034703915, 0.0074963053,
    -0.049301904, -0.005326988, 0.0014556781, 0.043266784, 0.03043187, -0.008008064, -0.0047954894, 0.0065719066,
    -0.018209687, 0.00520577, -0.04222329, 0.024618099, 0.0030018033, 0.008215917, 0.088026844, 0.041226704,
    -0.05174175, 0.035067245, -0.037319127, 0.0037409177, 0.024523623, -0.0126059465, 0.019197112, 0.013823613,
    -0.02756309, 0.014537172, 0.010373209, 0.045283005, -0.033583794, -0.07042238, 0.0071703074, -0.047405772,
    0.052970607, 0.01187145, 0.009470498, 0.033309255, -0.014022496, -0.01466476, -0.016799983, -0.004560339,
    -0.00007741032, 0.016623817, 0.02886948, -0.023846539, -0.05926324, 0.0019861246, -0.0097210035, 0.10283416,
    0.027582858, -0.050722197, 0.051445477, -0.027595742, 0.022260211, -0.025540655, -0.09528184, -0.028447622,
    -0.020006616, 0.08766454, -0.014110661, 0.04828308, 0.0074301455, 0.03928737, -0.0000046884684, -0.026885474,
    0.005424345, 0.054999787, 0.055203326, -0.012640017, -0.0435913, -0.024285164, 0.06663095, 0.005627971,
    -0.015168387, 0.027197381, -0.026075814, -0.003045215, -0.008655605, -0.009072627, 0.004339306, 0.03589536,
    0.061759293, -0.04240408, 0.04873947, 0.021134883, 0.053518154, 0.045864865, -0.027563328, -0.01566489,
    0.00018125105, -0.007070503, 0.039647527, -0.021650534, 0.038786504, 0.02006178, -0.013114097, 0.07950984,
    -0.014730525, -0.19681875, -0.013000412, 0.018087342, -0.0073786196, 0.038186155, -0.059353005, -0.0058362517,
    -0.009970051, 0.0016716863, -0.023077143, -0.02714242, -0.006529649, 0.037998736, 0.025349554, 0.019855456,
    -0.016530242, 0.00880591, -0.016678277, -0.03673031, 0.045423195, -0.03146899, -0.029318942, -0.012635296,
    0.071473934, -0.02904274, 0.027330637, -0.084734075, -0.05050938, -0.0030655882, -0.0022098075, -0.02383695,
    -0.028460467, -0.03240081, 0.048773084, 0.023262978, 0.016216593, 0.027833678, -0.039854486, -0.002443358,
    0.01758309, -0.033520985, -0.04862155, 0.0030191801, -0.040858116, 0.045017388, 0.01576234, -0.09301789,
    -0.04828378, -0.014886363, 0.0012595668, -0.010673225, -0.02463904, -0.06783802, -0.0012545382, 0.015514673,
    -0.004911741, 0.0025960177, -0.012014308, -0.024893451, 0.036577918, -0.003223495, -0.020390507, -0.022805423,
    -0.059310623, -0.02081245, -0.023387661, -0.061122973, -0.06244, 0.017364288, 0.033477243, -0.010211365, 0.04805492,
    -0.0644543, -0.048770227, 0.0068986556, -0.025725175, -0.029574871, -0.00949049, 0.05490974, 0.027187059,
    0.00826158, -0.06282722, 0.035274204, 0.012130771, -0.009545266, -0.048487406, 0.04640102, -0.037075754,
    -0.020248186, -0.02851919, 0.064635284, -0.0064534973, -0.026640853, -0.026290758, 0.035040796, 0.020074066,
    0.0032996435, 0.02883776, -0.012944289, 0.019450067, -0.02121465, -0.024558635, -0.04377821, -0.016631315,
    -0.04083968, -0.021962307, -0.010120014, 0.02998998, 0.10129919, -0.0025703132, -0.03771752, 0.01426784,
    0.025374308, 0.00082124525, 0.00029568642, -0.030749727, 0.016260363, 0.0014756168, 0.018676473, -0.03861688,
    -0.032052398, 0.056064054, 0.005533946, 0.04515451, 0.015364342, -0.02965325, 0.0009782034, 0.01524649, 0.019077078,
    -0.025799321, 0.020865263, -0.00037949806, 0.012502633, 0.0090223905, -0.0015367466, -0.012833919, -0.011109666,
    -0.006981191, -0.009670439, 0.009430074, -0.007729517, 0.0016868497, 0.016697595, -0.015892748, -0.020780738,
    0.049529854, -0.07344469, 0.0607613, -0.0068755895, -0.014736902, 0.014770749, -0.028858911, 0.025249828,
    -0.058469485, 0.030096894, -0.007117604, 0.010155325, -0.0065526864, -0.028654601, -0.04420291, 0.009965181,
    0.030222228, -0.010007972, 0.0104629295, 0.05589087, 0.05443477, -0.02641796, -0.061689503, 0.03118466, 0.012150501,
    0.03404673, -0.029666431, -0.008654386, -0.031682808, -0.014843155, 0.036703967, 0.026411135, -0.005715008,
    0.024990784, 0.058862202, 0.017355891, 0.039204415, -0.0034798204, 0.033091135, 0.050439566, 0.032798093,
    -0.029705318, 0.005968363, -0.055048566, 0.028009748, -0.03823961, 0.024362633, -0.017294712, -0.019563003,
    -0.019944556, -0.027790153, -0.01866823, 0.047109686, -0.0033735516, -0.020653522, -0.039765686, -0.019055683,
    -0.0263571, -0.023188936, 0.049641415, -0.077975206, 0.030659853, 0.048734687, 0.044718176, 0.036765084,
    -0.011803315, -0.027699227, -0.07258002, -0.08741319, -0.0392474, -0.042096145, -0.0040325304, 0.01667375,
    0.026754893, -0.030304687, 0.029919326, 0.024295082, 0.011638254, -0.012232291, -0.047564257, -0.036413006,
    0.026577674, 0.036411874, 0.00057670544, 0.017877145, 0.009268524, -0.006965588, 0.011874776, -0.005112591,
    -0.034651127, 0.03160231, -0.052825063, 0.014719321, -0.0139615545, -0.016238235, 0.002020219, 0.02526055,
    -0.07056756, 0.010022732, -0.014104433, -0.005984697, -0.00897443, 0.021115793, -0.043804843, -0.027990978,
    0.060727082, 0.0040618493, -0.038511537, -0.048857935, 0.024104802, -0.059829835, -0.029107396, -0.05538522,
    -0.06930553, -0.0057559577, -0.022053827, -0.00876388, -0.0056931996, 0.029746206, 0.0224666, 0.008767829,
    -0.03966822, -0.006478918, 0.06567699, -0.01581077, -0.03742192, -0.06186453, -0.028619587, 0.08638498, 0.031267703,
    -0.0008673075, 0.003113204, 0.012213491, 0.020067157, -0.02849485, 0.0018909829, 0.02714576, 0.0026566028,
    -0.03609787, 0.0060567204, -0.047545094, -0.0046444787, -0.021402694, -0.023118727, -0.015218381, -0.043136228,
    -0.0438743, -0.005564044, -0.009355076, -0.028500054, 0.009921202, 0.027966693, 0.06036647, 0.06929019, 0.007004997,
    -0.024255225, 0.04914266, 0.0032520234, 0.0044063884, -0.029372599, 0.038042217, -0.035385627, -0.04905816,
    0.047601648, 0.0071805464, -0.008339494, -0.035425205, 0.036915354, 0.024695326, -0.038979523, 0.01886513,
    0.013804558, -0.04848749, -0.04819779, 0.022526458, -0.029244151, 0.041152976, 0.04666112, 0.020387372, 0.037857335,
    0.060002513, 0.011064769, -0.032094717, 0.070615225, 0.04814509, 0.017521046, 0.074162334, -0.04956284, 0.07335939,
    -0.009453019, -0.06289444, 0.024246441, 0.021851622, 0.01857824, 0.02037353, -0.017273203, 0.021301785, 0.05051385,
    0.053983003, -0.01588495, 0.054096334, 0.05107405, 0.0720548, -0.029601721, 0.04816011, 0.006444874, -0.02505102,
    0.013238045, -0.021370836, 0.025479412, -0.048463117, 0.03514722, 0.08079718, 0.00369719, -0.015530819,
    0.0021374116, 0.03247959, 0.11611161, -0.021934662, -0.029833768, 0.016046036, -0.00634777, -0.06037879,
    -0.005574648, 0.028324481, -0.021840915, 0.03284168, -0.022047363, -0.03463407, 0.011823492, -0.03520137,
    -0.014746701, -0.03972389, -0.02124471, 0.026924072, -0.0022506462, 0.04452787, -0.015707701, -0.0065392647,
    0.0066317394, -0.005149294, -0.07763598, 0.054278333, 0.027830306, -0.03989325, -0.026995605, -0.024925973,
    -0.0024197767, 0.07852477, -0.034251966, 0.03694585, 0.044244047, 0.012739273, 0.0037145729, 0.008245091,
    0.013920077, -0.010570776, -0.021823786, 0.057918977, -0.075884886, -0.054011993, 0.0039594076, 0.003970741,
    -0.038295034, -0.03029311, 0.063210145, -0.08822839, -0.061069354, 0.08516593, 0.020341832, 0.08075477, 0.03257605,
    0.0039170105, 0.029395742, 0.012290831, -0.06368765, 0.023519376, -0.0173505, -0.001395915, 0.017215127,
    0.043243848, 0.04967547, 0.028518617, 0.021273924, -0.0023932487, -0.030911915, -0.05524172, -0.045551147,
    0.042072143, -0.027773965, -0.03693362, 0.028450156, 0.06675585, -0.061626967, -0.08894698, 0.045917906,
    -0.00475913, 0.034920968, -0.0064531155, -0.00689886, -0.06119457, 0.021173967, -0.027787622, -0.02472986,
    0.03998034, 0.03737826, -0.0067949123, 0.022558564, -0.04570635, -0.033072025, 0.022725677, 0.016026087,
    -0.02125421, -0.02984927, -0.0049473033
  ]
]
```

If the response is a sequence of numbers similar to the example given, then we consider the service to be successfully launched.

#### 3.2.5. Checking chatqna-retriever

It is performed using requests to the service

```bash
export your_embedding=$(python3 -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")

curl http://${HOST_IP}:${CHATQNA_REDIS_RETRIEVER_PORT}/v1/retrieval \
  -X POST \
  -d "{\"text\":\"test\",\"embedding\":${your_embedding}}" \
  -H 'Content-Type: application/json'
```

The response from the service must be in the form of JSON:

```json
{ "id": "d01ec090bc1b3a1b85d7f8d4c7ab6e53", "retrieved_docs": [], "initial_query": "test", "top_n": 1, "metadata": [] }
```

If the response is similar to the above example, then we consider the service to be successfully launched.

#### 3.2.6. Checking chatqna-tei-reranking-service

It is performed using requests to the service

```bash
curl http://${HOST_IP}:${CHATQNA_TEI_RERANKING_PORT}/rerank \
    -X POST \
    -d '{"query":"What is Deep Learning?", "texts": ["Deep Learning is not...", "Deep learning is..."]}' \
    -H 'Content-Type: application/json'
```

The response from the service must be in the form of JSON:

```json
[
  { "index": 1, "score": 0.94238955 },
  { "index": 0, "score": 0.120219156 }
]
```

If the response is similar to the above example, then we consider the service to be successfully launched.

#### 3.2.7. Checking chatqna-backend-server (Megaservice)

It is performed using requests to the service

```bash
curl http://${HOST_IP}:${CHATQNA_BACKEND_SERVICE_PORT}/v1/chatqna -H "Content-Type: application/json" -d '{
       "messages": "What is the revenue of Nike in 2023?"
       }'
```

The response from the service must be in the form of JSON:

```textmate
...........
data: b' not'
data: b' publicly'
data: b' available'
data: b'.'
data: b''
data: b''
data: [DONE]
```

If the response contains a set of tokens and the end of the output contains "data: [Done]", then we consider the service to be successfully launched.