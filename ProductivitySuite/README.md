# OPEA Productivity Suite Application

OPEA Productivity Suite streamlines your workflow to boost productivity. It leverages the OPEA microservices to provide a comprehensive suite of features to cater to the diverse needs of modern enterprises.

## Key Features

- Chat with Documents: Engage in intelligent conversations with your documents using our advanced RAG Capabilities. Our Retrieval-Augmented Generation (RAG) model allows you to ask questions, receive relevant information, and gain insights from your documents in real-time.

- Content Summarization: Save time and effort by automatically summarizing lengthy documents or articles, enabling you to quickly grasp the key takeaways.

- FAQ Generation: Effortlessly create comprehensive FAQs based on your documents, ensuring that your users have access to the information they need.

- Code Generation: Boost your coding productivity with our code generation feature. Simply provide a description of the functionality you require, and the application will generate the corresponding code snippets, saving you valuable time and effort.

- User Context Management: Maintain a seamless workflow by managing your user's context within the application. Our context management system keeps track of your documents and chat history, allowing for personalized experiences.

- Identity and access management: uses the open source platform Keycloak for single sign-on identity and access management.

Refer to the [Keycloak Configuration Guide](./docker_compose/intel/cpu/xeon/keycloak_setup_guide.md) for instructions to setup Keycloak.

Refer to the [Xeon Guide](./docker_compose/intel/cpu/xeon/README.md) for instructions to build docker images from source and running the application via docker compose.

Refer to the [Xeon Kubernetes Guide](./kubernetes/intel/README.md) for instructions to deploy the application via kubernetes.
