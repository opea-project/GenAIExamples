# 📝 Chat History Microservice

The Chat History Microservice is a scalable solution for storing, retrieving and managing chat conversations using various type of databases. This microservice is designed to seamlessly integrate with OPEA chat applications, enabling data persistence and efficient management of chat histories.

It can be integrated into application by making HTTP requests to the provided API endpoints as shown in the flow diagram below.

![Flow Chart](./assets/img/chathistory_flow.png)

---

## 🛠️ Features

- **Store Chat Conversations**: Save chat messages user information, and metadata associated with each conversation.
- **Retrieve Chat Histories**: Fetch chat histories for a specific user or retrieve a particular conversation by its unique identifier.
- **Update Chat Conversations**: Modify existing chat conversations by adding new messages or updating existing ones.
- **Delete Chat Conversations**: Remove chat conversations record from database.

---

## ⚙️ Implementation

The Chat History microservice able to support various database backends for storing the chat conversations.

### Chat History with MongoDB

For more detail, please refer to this [README](./mongo/README.md)
