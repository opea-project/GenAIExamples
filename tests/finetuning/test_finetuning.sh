#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

set -x

WORKPATH=$(dirname "$PWD")
LOG_PATH="$WORKPATH/tests"
ip_address=$(hostname -I | awk '{print $1}')
finetuning_service_port=8015
ray_port=8265

function build_docker_images() {
    cd $WORKPATH
    echo $(pwd)
    docker build -t opea/finetuning:comps --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy --build-arg HF_TOKEN=$HF_TOKEN -f comps/finetuning/Dockerfile .
    if [ $? -ne 0 ]; then
        echo "opea/finetuning built fail"
        exit 1
    else
        echo "opea/finetuning built successful"
    fi
}

function start_service() {
    export no_proxy="localhost,127.0.0.1,"${ip_address}
    docker run -d --name="test-comps-finetuning-server" -p $finetuning_service_port:$finetuning_service_port -p $ray_port:$ray_port --runtime=runc --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e no_proxy=$no_proxy opea/finetuning:comps
    sleep 1m
}

function validate_upload() {
    local URL="$1"
    local SERVICE_NAME="$2"
    local DOCKER_NAME="$3"
    local EXPECTED_PURPOSE="$4"
    local EXPECTED_FILENAME="$5"

    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -F "file=@./$EXPECTED_FILENAME" -F purpose="$EXPECTED_PURPOSE" -H 'Content-Type: multipart/form-data' "$URL")
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')

    # Parse the JSON response
    purpose=$(echo "$RESPONSE_BODY" | jq -r '.purpose')
    filename=$(echo "$RESPONSE_BODY" | jq -r '.filename')

    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs $DOCKER_NAME >> ${LOG_PATH}/finetuning-server_upload_file.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi

    # Check if the parsed values match the expected values
    if [[ "$purpose" != "$EXPECTED_PURPOSE" || "$filename" != "$EXPECTED_FILENAME" ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        docker logs $DOCKER_NAME >> ${LOG_PATH}/finetuning-server_upload_file.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi

    sleep 10s
}

function validate_finetune() {
    local URL="$1"
    local SERVICE_NAME="$2"
    local DOCKER_NAME="$3"
    local EXPECTED_DATA="$4"
    local INPUT_DATA="$5"

    HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -H 'Content-Type: application/json' -d "$INPUT_DATA" "$URL")
    HTTP_STATUS=$(echo $HTTP_RESPONSE | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
    FINTUNING_ID=$(echo "$RESPONSE_BODY" | jq -r '.id')

    # Parse the JSON response
    purpose=$(echo "$RESPONSE_BODY" | jq -r '.purpose')
    filename=$(echo "$RESPONSE_BODY" | jq -r '.filename')

    if [ "$HTTP_STATUS" -ne "200" ]; then
        echo "[ $SERVICE_NAME ] HTTP status is not 200. Received status was $HTTP_STATUS"
        docker logs $DOCKER_NAME >> ${LOG_PATH}/finetuning-server_create.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] HTTP status is 200. Checking content..."
    fi

    # Check if the parsed values match the expected values
    if [[ "$RESPONSE_BODY" != *"$EXPECTED_DATA"* ]]; then
        echo "[ $SERVICE_NAME ] Content does not match the expected result: $RESPONSE_BODY"
        docker logs $DOCKER_NAME >> ${LOG_PATH}/finetuning-server_create.log
        exit 1
    else
        echo "[ $SERVICE_NAME ] Content is as expected."
    fi

    sleep 10s

    # check finetuning job status
    URL="$URL/retrieve"
    for((i=1;i<=10;i++));
    do
	HTTP_RESPONSE=$(curl --silent --write-out "HTTPSTATUS:%{http_code}" -X POST -H "Content-Type: application/json" -d '{"fine_tuning_job_id": "'$FINTUNING_ID'"}' "$URL")
	echo $HTTP_RESPONSE
	RESPONSE_BODY=$(echo $HTTP_RESPONSE | sed -e 's/HTTPSTATUS\:.*//g')
	STATUS=$(echo "$RESPONSE_BODY" | jq -r '.status')
	if [[ "$STATUS" == "succeeded" ]]; then
	    echo "training: succeeded."
	    break
	elif [[ "$STATUS" == "failed" ]]; then
	    echo "training: failed."
	    exit 1
	else
	    echo "training: '$STATUS'"
	fi
	sleep 1m
    done
}

function validate_microservice() {
    cd $LOG_PATH
    export no_proxy="localhost,127.0.0.1,"${ip_address}

    ##########################
    #    general test         #
    ##########################
    # test /v1/dataprep upload file
    echo '[{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."},{"instruction": "Give three tips for staying healthy.", "input": "", "output": "1.Eat a balanced diet and make sure to include plenty of fruits and vegetables. \n2. Exercise regularly to keep your body active and strong. \n3. Get enough sleep and maintain a consistent sleep schedule."}]' > $LOG_PATH/test_data.json
    validate_upload \
        "http://${ip_address}:$finetuning_service_port/v1/files" \
        "general - upload" \
        "test-comps-finetuning-server" \
        "fine-tune" \
        "test_data.json"

    # test /v1/fine_tuning/jobs
    validate_finetune \
        "http://${ip_address}:$finetuning_service_port/v1/fine_tuning/jobs" \
        "general - finetuning" \
        "test-comps-finetuning-server" \
        '{"id":"ft-job' \
        '{"training_file": "test_data.json","model": "facebook/opt-125m"}'


    ##########################
    #    rerank test         #
    ##########################
    # test /v1/dataprep upload file
    cat <<EOF > test_data_rerank.json
{"query": "Five women walk along a beach wearing flip-flops.", "pos": ["Some women with flip-flops on, are walking along the beach"], "neg": ["The 4 women are sitting on the beach.", "There was a reform in 1996.", "She's not going to court to clear her record.", "The man is talking about hawaii.", "A woman is standing outside.", "The battle was over. ", "A group of people plays volleyball."]}
{"query": "A woman standing on a high cliff on one leg looking over a river.", "pos": ["A woman is standing on a cliff."], "neg": ["A woman sits on a chair.", "George Bush told the Republicans there was no way he would let them even consider this foolish idea, against his top advisors advice.", "The family was falling apart.", "no one showed up to the meeting", "A boy is sitting outside playing in the sand.", "Ended as soon as I received the wire.", "A child is reading in her bedroom."]}
{"query": "Two woman are playing instruments; one a clarinet, the other a violin.", "pos": ["Some people are playing a tune."], "neg": ["Two women are playing a guitar and drums.", "A man is skiing down a mountain.", "The fatal dose was not taken when the murderer thought it would be.", "Person on bike", "The girl is standing, leaning against the archway.", "A group of women watch soap operas.", "No matter how old people get they never forget. "]}
{"query": "A girl with a blue tank top sitting watching three dogs.", "pos": ["A girl is wearing blue."], "neg": ["A girl is with three cats.", "The people are watching a funeral procession.", "The child is wearing black.", "Financing is an issue for us in public schools.", "Kids at a pool.", "It is calming to be assaulted.", "I face a serious problem at eighteen years old. "]}
{"query": "A yellow dog running along a forest path.", "pos": ["a dog is running"], "neg": ["a cat is running", "Steele did not keep her original story.", "The rule discourages people to pay their child support.", "A man in a vest sits in a car.", "Person in black clothing, with white bandanna and sunglasses waits at a bus stop.", "Neither the Globe or Mail had comments on the current state of Canada's road system. ", "The Spring Creek facility is old and outdated."]}
{"query": "It sets out essential activities in each phase along with critical factors related to those activities.", "pos": ["Critical factors for essential activities are set out."], "neg": ["It lays out critical activities but makes no provision for critical factors related to those activities.", "People are assembled in protest.", "The state would prefer for you to do that.", "A girl sits beside a boy.", "Two males are performing.", "Nobody is jumping", "Conrad was being plotted against, to be hit on the head."]}
EOF
    validate_upload \
        "http://${ip_address}:$finetuning_service_port/v1/files" \
        "rerank - upload" \
        "test-comps-finetuning-server" \
        "fine-tune" \
        "test_data_rerank.json"

    # test /v1/fine_tuning/jobs
    validate_finetune \
        "http://${ip_address}:$finetuning_service_port/v1/fine_tuning/jobs" \
        "rerank - finetuning" \
        "test-comps-finetuning-server" \
        '{"id":"ft-job' \
        '{"training_file": "test_data_rerank.json","model": "BAAI/bge-reranker-base","General":{"task":"rerank","lora_config":null}}'


    ##########################
    #    llm pretrain test   #
    ##########################
    # test /v1/dataprep upload file
    cat <<EOF > test_data_pretrain.json
{"text": "Five women walk along a beach wearing flip-flops."}
{"text": "A woman standing on a high cliff on one leg looking over a river."}
{"text": "Two woman are playing instruments; one a clarinet, the other a violin."}
{"text": "A girl with a blue tank top sitting watching three dogs."}
{"text": "A yellow dog running along a forest path."}
{"text": "It sets out essential activities in each phase along with critical factors related to those activities."}
EOF
    validate_upload \
        "http://${ip_address}:$finetuning_service_port/v1/files" \
        "pretrain - upload" \
        "test-comps-finetuning-server" \
        "fine-tune" \
        "test_data_pretrain.json"

    # test /v1/fine_tuning/jobs
    validate_finetune \
        "http://${ip_address}:$finetuning_service_port/v1/fine_tuning/jobs" \
        "pretrain - finetuning" \
        "test-comps-finetuning-server" \
        '{"id":"ft-job' \
        '{"training_file": "test_data_pretrain.json","model": "facebook/opt-125m","General":{"task":"pretraining","lora_config":null}}'


    ##########################
    #    dpo test   #
    ##########################
    # test /v1/dataprep upload file
    cat <<EOF > test_data_dpo.jsonl
{"system": "", "question": "You will be given a definition of a task first, then some input of the task.\nThis task is about using the specified sentence and converting the sentence to Resource Description Framework (RDF) triplets of the form (subject, predicate object). The RDF triplets generated must be such that the triplets accurately capture the structure and semantics of the input sentence. The input is a sentence and the output is a list of triplets of the form [subject, predicate, object] that capture the relationships present in the sentence. When a sentence has more than 1 RDF triplet possible, the output must contain all of them.\n\nAFC Ajax (amateurs)'s ground is Sportpark De Toekomst where Ajax Youth Academy also play.\nOutput:", "chosen": "[\n  [\"AFC Ajax (amateurs)\", \"has ground\", \"Sportpark De Toekomst\"],\n  [\"Ajax Youth Academy\", \"plays at\", \"Sportpark De Toekomst\"]\n]", "rejected": " Sure, I'd be happy to help! Here are the RDF triplets for the input sentence:\n\n[AFC Ajax (amateurs), hasGround, Sportpark De Toekomst]\n[Ajax Youth Academy, playsAt, Sportpark De Toekomst]\n\nExplanation:\n\n* AFC Ajax (amateurs) is the subject of the first triplet, and hasGround is the predicate that describes the relationship between AFC Ajax (amateurs) and Sportpark De Toekomst.\n* Ajax Youth Academy is the subject of the second triplet, and playsAt is the predicate that describes the relationship between Ajax Youth Academy and Sportpark De Toekomst.\n\nNote that there may be other possible RDF triplets that could be derived from the input sentence, but the above triplets capture the main relationships present in the sentence."}
{"system": "You are an AI assistant. You will be given a task. You must generate a detailed and long answer.", "question": "Generate an approximately fifteen-word sentence that describes all this data: Midsummer House eatType restaurant; Midsummer House food Chinese; Midsummer House priceRange moderate; Midsummer House customer rating 3 out of 5; Midsummer House near All Bar One", "chosen": "Midsummer House is a moderately priced Chinese restaurant with a 3/5 customer rating, located near All Bar One.", "rejected": " Sure! Here's a sentence that describes all the data you provided:\n\n\"Midsummer House is a moderately priced Chinese restaurant with a customer rating of 3 out of 5, located near All Bar One, offering a variety of delicious dishes.\""}
EOF
    validate_upload \
        "http://${ip_address}:$finetuning_service_port/v1/files" \
        "dpo - upload" \
        "test-comps-finetuning-server" \
        "fine-tune" \
        "test_data_dpo.jsonl"

    # test /v1/fine_tuning/jobs
    validate_finetune \
        "http://${ip_address}:$finetuning_service_port/v1/fine_tuning/jobs" \
        "dpo - finetuning" \
        "test-comps-finetuning-server" \
        '{"id":"ft-job' \
        '{"training_file": "test_data_dpo.jsonl","model": "facebook/opt-125m","General":{"task":"dpo"}}'

}

function stop_docker() {
    cid=$(docker ps -aq --filter "name=test-comps-finetuning-server*")
    if [[ ! -z "$cid" ]]; then docker stop $cid && docker rm $cid && sleep 1s; fi
}

function main() {

    stop_docker

    build_docker_images
    start_service

    validate_microservice

    stop_docker
    echo y | docker system prune

}

main
