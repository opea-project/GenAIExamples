# LLM Chatbot GUI

## 📸 Project Screenshots

![project-screenshot](https://i.imgur.com/2Q1tkW3.png)
![project-screenshot](https://i.imgur.com/ERaSnYi.png)

## Requirements

- [Node.js](https://nodejs.org/) version v18.0.0 or higher
- [npm](https://www.npmjs.com/) version 9.6.5 or higher

To check if both were successfully installed run the following commands:

```bash
node --version
```

```bash
npm --version
```

_`--version` option can be replaced with `-v` shorthand_

## Setup

### Environment variables

Create `.env` file in this folder. It has to contain the following variables that represent corresponding endpoints
for communication with **without RAG** and **with RAG** backend:

```
VITE_WITH_RAG_BASE_URL = 'http://<ip-address>:<port>/v1/rag'
VITE_WITHOUT_RAG_BASE_URL = 'http://<ip-address>:<port>/v1/rag'
```

### Install dependencies

```bash
npm install
```

## Start GUI

Execute the following command to start GUI:

```bash
npm run dev
```

By default, UI will run on `http://localhost:5147`.
The port and IP address that the UI will be served on can be changed by modifying npm `dev` script
in `package.json`.

The following example presents how to change port and IP address by setting corresponding options: `--port`
and `--host`.

```json
"dev": "vite dev --port 9090 --host 0.0.0.0",
```

This also can be set via CLI by adding `-- --port <port> --host <ip>` :

```bash
npm run dev -- --port 9090 --host 0.0.0.0
```

In case of any configuring issues please refer to https://vitejs.dev/config/server-options.
