## Performance measurements of chain with langsmith
Pre-requisite: Signup in langsmith [https://www.langchain.com/langsmith] and get the api token <br />
### Steps to run perf measurements
1. Build langchain-rag container with most updated Dockerfile
2. Start tgi server on system with Gaudi
3. Statr redis container with docker-compose-redis.yml
4. Add your hugging face access token in docker-compose-langchain.yml and start langchain-rag-server container
5. enter into langchain-rag-server container and start jupyter notebook server (can specify needed IP address and jupyter will run on port 8888)

```
docker exec -it langchain-rag-server bash
cd /test
jupyter notebook --allow-root --ip=X.X.X.X
```

6. Launch jupyter notebook in your browser and open the tgi_gaudi.ipynb notebook
7. Add langsmith api key in first cell of the notebook [os.environ["LANGCHAIN_API_KEY"] = "add-your-langsmith-key"  # Your API key]
8. Clear all the cells and run all the cells
9. The output of the last cell which calls client.run_on_dataset() will run the langchain Q&A test and captures measurements in the langsmith server. The URL to access the test result can be obtained from the output of the command

