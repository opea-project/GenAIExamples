## Launch 8 models on 8 separate Gaudi2 cards:

Add HuggingFace access token in  .env <br/>
Optinally change model name and linked volume direcotry to store downloaded model<br/><br/>
Run the following command in your terminal to launch nginx load balancer and 8 instances of tgi_gaudi containers (one for each Gaudi card):

```
docker compose up -f docker-compose.yml -d 
```
