# AgentQnA

## 📸 Project Screenshots

![project-screenshot](../../assets/img/agent_ui.png)
![project-screenshot](../../assets/img/agent_ui_result.png)

## 🧐 Features

Here're some of the project's features:

- Create Agent：Provide more precise answers based on user queries, showcase the high-quality output process of complex queries across different dimensions, and consolidate information to present comprehensive answers.

## 🛠️ Get it Running

1. Clone the repo.

2. cd command to the current folder.

   ```
   cd AgentQnA/ui/svelte
   ```

3. Modify the required .env variables. The `AGENT_URL` should be in the form of the following:

   ```
   AGENT_URL = "http://${ip_address}:${agent_port}/v1/chat/completions"
   ```

   For example: assume that the ip address of the host machine is 10.10.10.1, and the agent port is 9090,then

   ```
   AGENT_URL = "http://10.10.10.1:9090/v1/chat/completions"
   ```

   You can get the ip address of the host machine by running the command below:

   ```bash
    export ip_address=$(hostname -I | awk '{print $1}')
   ```

4. **For Local Development:**

- Install the dependencies:

  ```
  npm install
  ```

- Start the development server:

  ```
  npm run dev
  ```

- The application will be available at `http://localhost:5173`.

5. **For Docker Setup:**

- Build the Docker image:

  ```
  docker build -t opea:agent-ui .
  ```

- Run the Docker container:

  ```
  docker run -d -p 5173:5173 --name agent-ui opea:agent-ui
  ```

- The application will be available at `http://${ip_address}:5173`. You can access it with a web browser on your laptop. Note the `ip_address` should be the ip address of the host machine where the UI container runs.
