# Explore Edge Craft RAG

[中文版](Explore_Edge_Craft_RAG_zh.md)

## ChatQnA with LLM Example in UI

### Create Pipeline

To create a default pipeline, you need to click the `Create Pipeline` button in the `Pipeline Setting` page.
![alt text](../assets/img/Explore_Edge_Craft_RAG_01.jpg)

Then, In ` Generator` config page, choose LLM Inference Type to `Vllm`.  
In `Large Language Model` field, input your LLM_MODEL name, e.g. 'Qwen/Qwen3-8B'.  
In `Vllm Url` field, you need to input 'IP:vllm_port' then click `Test` button. Note that defaultly vllm_port is '8086'  
(Note if the test fails, it might be because vLLM service not ready yet, you can wait for 30s and try again)
![alt text](../assets/img/Explore_Edge_Craft_RAG_02.jpg)

You can also create multiple pipelines or update/remove existing pipelines through the `Operation` field, but please note that active pipelines cannot be updated.
![alt text](../assets/img/Explore_Edge_Craft_RAG_03.jpg)

### Upload files & ChatQnA

After the pipeline creation, you can go to `Knowledge Base` page and click `Create Knowledge Base` button to create your knowledge base.
![alt text](../assets/img/Explore_Edge_Craft_RAG_04.jpg)

Then follow the knowledge base creation guide in UI to set your knowledge base, please note that in `Indexer Type` you can set MilvusVector as indexer(Please make sure Milvus is enabled before set MilvusVector as indexer, you can refer to [Enable Milvus](Advanced_Setup.md#deploy-the-service-on-intel-gpu-using-docker-compose)).  
if choosing MilvusVector, you need to verify vector uri first, please input 'Your_IP:milvus_port' then click `Test` button. Note that milvus_port is 19530
![alt text](../assets/img/Explore_Edge_Craft_RAG_05.jpg)

When creating Knowledge base, please choose `Activated` option, since only the files in activated Knowledge base can be retrieved in ChatQnA
![alt text](../assets/img/Explore_Edge_Craft_RAG_06.jpg)

After knowledge base creation, you can upload the documents for retrieval.
![alt text](../assets/img/Explore_Edge_Craft_RAG_07.jpg)

Then, you can submit messages in the chat box in `Chat` page.
![alt text](../assets/img/Explore_Edge_Craft_RAG_08.jpg)

## ChatQnA with Kbadmin in UI

### Kbadmin Knowledge Base

Go to `Knowledge Base` page and click `Create Knowledge Base` button to create your knowledge base.  
Please select 'kbadmin' in `Type`and select kb name from the kbs you created in kbadmin UI page. Loading kb name might be slow ,please wait with patient

![alt text](../assets/img/Explore_Edge_Craft_RAG_09.png)

Ten you can select embedding information in 'Indexer' page

![alt text](../assets/img/Explore_Edge_Craft_RAG_10.png)

After creation, you can see kbadmin tag in knowledge base then you can submit messages in the chat box in `Chat` page.
![alt text](../assets/img/Explore_Edge_Craft_RAG_11.png)
