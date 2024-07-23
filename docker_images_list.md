# Description

A list of released OPEA docker images in https://hub.docker.com/, contains all relevant images from the GenAIExamples, GenAIComps and GenAIInfra projects. Please expect more public available images in the future release.

Take ChatQnA for example. ChatQnA is a chatbot application service based on the Retrieval Augmented Generation (RAG) architecture. It consists of <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/embedding-tei">opea/embedding-tei</a></td>, <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/retriever-redis">opea/retriever-redis</a></td>, <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/reranking-tei">opea/reranking-tei</a></td>, <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/llm-tgi">opea/llm-tgi</a></td>, <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/dataprep-redis">opea/dataprep-redis</a></td>, <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/chatqna">opea/chatqna</a></td>, <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/chatqna-ui">opea/chatqna-ui</a></td> and <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/chatqna-conversation-ui">opea/chatqna-conversation-ui</a></td> (Optional) multiple microservices. Other services are similar, see the corresponding README for details.

# Example images

<table class="tg"><thead>
  <tr>
    <th class="tg-cly1">Example Images</th>
    <th class="tg-cly1">Dockerfile</th>
  </tr></thead>
<tbody>
  <tr>
    <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/chatqna">opea/chatqna</a></td>
    <td class="tg-yk8o"><a href="https://github.com/opea-project/GenAIExamples/blob/main/ChatQnA/docker/Dockerfile">Link</a></td>
  </tr>
  <tr>
    <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/chatqna-ui">opea/chatqna-ui</a></td>
    <td class="tg-yk8o"><a href="https://github.com/opea-project/GenAIExamples/blob/main/ChatQnA/docker/ui/docker/Dockerfile">Link</a></td>
  </tr>
  <tr>
    <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/chatqna-conversation-ui">opea/chatqna-conversation-ui</a></td>
    <td class="tg-yk8o"><a href="https://github.com/opea-project/GenAIExamples/blob/main/ChatQnA/docker/ui/docker/Dockerfile.react">Link</a></td>
  </tr>
  <tr>
    <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/docsum">opea/docsum</a></td>
    <td class="tg-yk8o"><a href="https://github.com/opea-project/GenAIExamples/blob/main/DocSum/docker/Dockerfile">Link</a></td>
  </tr>
  <tr>
    <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/docsum-ui">opea/docsum-ui</a></td>
    <td class="tg-yk8o"><a href="https://github.com/opea-project/GenAIExamples/blob/main/DocSum/docker/ui/docker/Dockerfile">Link</a></td>
  </tr>
  <tr>
    <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/codetrans">opea/codetrans</a></td>
    <td class="tg-yk8o"><a href="https://github.com/opea-project/GenAIExamples/blob/main/CodeTrans/docker/Dockerfile">Link</a></td>
  </tr>
  <tr>
    <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/codetrans-ui">opea/codetrans-ui</a></td>
    <td class="tg-yk8o"><a href="https://github.com/opea-project/GenAIExamples/blob/main/CodeTrans/docker/ui/docker/Dockerfile">Link</a></td>
  </tr>
  <tr>
    <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/codegen">opea/codegen</a></td>
    <td class="tg-yk8o"><a href="https://github.com/opea-project/GenAIExamples/blob/main/CodeGen/docker/Dockerfile">Link</a></td>
  </tr>
  <tr>
    <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/codegen-ui">opea/codegen-ui</a></td>
    <td class="tg-yk8o"><a href="https://github.com/opea-project/GenAIExamples/blob/main/CodeGen/docker/ui/docker/Dockerfile">Link</a></td>
  </tr>
  <tr>
    <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/searchqna/tags">opea/searchqna</a></td>
    <td class="tg-yk8o"><a href="https://github.com/opea-project/GenAIExamples/blob/main/SearchQnA/docker/Dockerfile">Link</a></td>
  </tr>
</tbody></table>

# Microservice images

<table class="tg"><thead>
  <tr>
    <th class="tg-cly1">Microservice Images</th>
    <th class="tg-cly1">Dockerfile</th>
  </tr></thead>
<tbody>
  <tr>
    <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/tei-gaudi/tags">opea/tei-gaudi</a></td>
    <td class="tg-yk8o"><a href="https://github.com/huggingface/tei-gaudi/blob/habana-main/Dockerfile-hpu">Link</a></td>
  </tr>
  <tr>
    <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/web-retriever-chroma">opea/web-retriever-chroma</a></td>
    <td class="tg-yk8o"><a href="https://github.com/opea-project/GenAIComps/tree/main/comps/web_retrievers/langchain/chroma/docker">Link</a></td>
  </tr>
  <tr>
    <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/retriever-redis">opea/retriever-redis</a></td>
    <td class="tg-yk8o"><a href="https://github.com/opea-project/GenAIComps/blob/main/comps/retrievers/langchain/redis/docker/Dockerfile">Link</a></td>
  </tr>
  <tr>
    <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/reranking-tei">opea/reranking-tei</a></td>
    <td class="tg-yk8o"><a href="https://github.com/opea-project/GenAIComps/blob/main/comps/reranks/tei/docker/Dockerfile">Link</a></td>
  </tr>
  <tr>
    <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/llm-tgi">opea/llm-tgi</a></td>
    <td class="tg-yk8o"><a href="https://github.com/opea-project/GenAIComps/blob/main/comps/llms/text-generation/tgi/Dockerfile">Link</a></td>
  </tr>
  <tr>
    <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/llm-docsum-tgi">opea/llm-docsum-tgi</a></td>
    <td class="tg-yk8o"><a href="https://github.com/opea-project/GenAIComps/blob/main/comps/llms/summarization/tgi/Dockerfile">Link</a></td>
  </tr>
  <tr>
    <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/llm-vllm">opea/llm-vllm</a></td>
    <td class="tg-yk8o"><a href="https://github.com/opea-project/GenAIComps/blob/main/comps/llms/text-generation/vllm/docker/Dockerfile.microservice">Link</a></td>
  </tr>
  <tr>
    <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/llm-ray">opea/llm-ray</a></td>
    <td class="tg-yk8o"><a href="https://github.com/opea-project/GenAIComps/blob/main/comps/llms/text-generation/ray_serve/docker/Dockerfile.microservice">Link</a></td>
  </tr>
  <tr>
    <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/guardrails-pii-detection">opea/guardrails-pii-detection</a></td>
    <td class="tg-yk8o"><a href="https://github.com/opea-project/GenAIComps/blob/main/comps/guardrails/pii_detection/docker/Dockerfile">Link</a></td>
  </tr>
  <tr>
    <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/embedding-tei">opea/embedding-tei</a></td>
    <td class="tg-yk8o"><a href="https://github.com/opea-project/GenAIComps/blob/main/comps/embeddings/langchain/docker/Dockerfile">Link</a></td>
  </tr>
  <tr>
    <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/dataprep-on-ray-redis">opea/dataprep-on-ray-redis</a></td>
    <td class="tg-yk8o"><a href="https://github.com/opea-project/GenAIComps/blob/main/comps/dataprep/redis/langchain_ray/docker/Dockerfile">Link</a></td>
  </tr>
  <tr>
    <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/dataprep-redis">opea/dataprep-redis</a></td>
    <td class="tg-yk8o"><a href="https://github.com/opea-project/GenAIComps/blob/main/comps/dataprep/redis/langchain/docker/Dockerfile">Link</a></td>
  </tr>
  <tr>
    <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/knowledge_graphs">opea/knowledge_graphs</a></td>
    <td class="tg-yk8o"><a href="https://github.com/opea-project/GenAIComps/blob/main/comps/knowledgegraphs/langchain/docker/Dockerfile">Link</a></td>
  </tr>
  <tr>
    <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/gmcrouter">opea/gmcrouter</a></td>
    <td class="tg-yk8o"><a href="https://github.com/opea-project/GenAIInfra/blob/main/microservices-connector/Dockerfile.manager">Link</a></td>
  </tr>
  <tr>
    <td class="tg-yk8o"><a href="https://hub.docker.com/r/opea/gmcmanager">opea/gmcmanager</a></td>
    <td class="tg-yk8o"><a href="https://github.com/opea-project/GenAIInfra/blob/main/microservices-connector/Dockerfile.router">Link</a></td>
  </tr>
</tbody></table>
