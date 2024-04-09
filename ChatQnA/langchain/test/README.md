## Performance measurement tests with langsmith

Pre-requisite: Signup in langsmith [https://www.langchain.com/langsmith] and get the api token <br />

### Steps to run perf measurements with tgi_gaudi.ipynb jupyter notebook

1. This dir is mounted at /test in qna-rag-redis-server
2. Make sure redis container and LLM serving is up and running
3. enter into qna-rag-redis-server container and start jupyter notebook server (can specify needed IP address and jupyter will run on port 8888)
   ```
   docker exec -it qna-rag-redis-server bash
   cd /test
   jupyter notebook --allow-root --ip=X.X.X.X
   ```
4. Launch jupyter notebook in your browser and open the tgi_gaudi.ipynb notebook
5. Update all the configuration parameters in the second cell of the notebook
6. Clear all the cells and run all the cells
7. The output of the last cell which calls client.run_on_dataset() will run the langchain Q&A test and captures measurements in the langsmith server. The URL to access the test result can be obtained from the output of the command
   <br/><br/>

### Steps to run perf measurements with end_to_end_rag_test.py python script

1. This dir is mounted at /test in qna-rag-redis-server
2. Make sure redis container and LLM serving is up and running
3. enter into qna-rag-redis-server container and run the python script
   ```
   docker exec -it qna-rag-redis-server bash
   cd /test
   python end_to_end_rag_test.py -l "<LLM model serving - TGI or VLLM>" -e <TEI embedding model serving> -m <LLM model name> -ht "<huggingface token>" -lt <langsmith api key> -dbs "<path to schema>" -dbu "<redis server URL>" -dbi "<DB Index name>" -d "<langsmith dataset name>"
   ```
4. Check the results in langsmith server
