art 4: Building Your Own MCP Server (To Receive Certification)
Final Project Requirements
Mandatory Features
Custom Features
Making Your Project Stand Out
How to Share Your Project
In the next lesson, you must attach a .txt file where you will include the link to your GitHub repository. Use this very simple format for the .txt file, with the URL of your GitHub project page:

⭐
🏆 Congratulations! You've just completed all the course lessons. That's a huge achievement. Just the project is left! One of the best ways to make it stick is to share your success publicly: it cements your learning, boosts your professional credibility, and can even open doors by showing your network your commitment to AI.

If you post about finishing and tag me, Louis-François Bouchard (ln, X, Insta), Paul Iusztin (In, X, Substack) and Towards AI (ln, X, Insta). We'll reshare it and celebrate your accomplishment with you 🚀🙌

In this final part of the course, you will build and submit your own MCP server. We will review your project at a high level to ensure it meets the requirements and to award you the course certification.

This final project must be an MCP server that demonstrates your understanding of the concepts covered in this course. You should create a server that implements several MCP tools and at least one MCP prompt. We strongly encourage you to build a domain-specific MCP server with a clear, real-world use case in mind. Design your project to solve a specific problem in a particular industry or domain that matches your interests or professional experience. This could be a specialized assistant for legal research, medical documentation, financial analysis, educational content creation, marketing automation, data analysis, developer productivity, research synthesis, or any other innovative application that leverages the power of MCP and AI agents to address a concrete need!

The goal is for you to create a polished, professional project that you can share publicly and demonstrate your newfound AI agent development skills. We want this to be something you're proud to showcase to potential employers, colleagues, or the broader AI community.

Final Project Requirements
For the final project, we are providing a list of required features and a list of custom features. To obtain your course certification, your project must meet all required features. You must also implement at least 4 of the custom features. The custom features are designed to give you flexibility in choosing how to extend your project based on your interests and to help you build a more comprehensive portfolio piece.

Mandatory Features
Here are the required features that you must include in your project:

It must be an MCP server built in Python using FastMCP.
The server must implement at least one MCP tool that provides meaningful functionality.
The server must include at least 1 MCP prompt that ties some of the MCP tools together into an agentic workflow. This workflow must include at least one step where user feedback or confirmation is needed (e.g., asking the user to review and approve generated content, select from multiple options, confirm an action, etc.).
The complete project must be published on a public GitHub repository.
The project must be initialized using uv for dependency management. Start by running uv init --python 3.14.0 . , which will initialize the project with Python 3.14 and all the required project management files such as pyproject.toml , .python-version and more.
The project should follow a clear, organized structure. Your code should live in a dedicated source directory (e.g. src/ or src/<your_module_name>/). The structure below is provided as a reference example (similar to the Nova or Brown project from the course), but you may adapt it to fit your specific use case as long as your chosen structure is well-organized, clearly documented, and explained in your README:
src/server.py: The main entry point that creates a FastMCP app instance and registers the routers.
src/routers/: Contains tools.py, resources.py, and prompts.py that import implementations and register them with FastMCP using decorators.
src/tools/, resources/, prompts/: Directories containing the business logic for each MCP capability.
src/app/: Functions implementing your core business logic.
src/utils/: Utility functions and helper code.
src/config/settings.py: Uses pydantic-settings to manage configurations such as server name, version, API keys, and model choices.
The repository must contain a comprehensive README.md file. A template for this README is provided here:
README.md9.1 KiB
You should copy this template, fill in all the placeholders (marked with square brackets like [your-server-name]), and replace them with your actual project information. Every placeholder must be replaced with appropriate content. The README must include:

A clear description of what your MCP server does and its use cases.
Step-by-step instructions for project setup, including how to clone the repository, install dependencies using uv, configure environment variables and run the project.
A list of all environment variables and API keys that need to be added to the .env file to run the project. Specify also how to get them if they are different from the ones used in the course.
A JSON configuration block showing how to connect to your MCP server from an MCP client like Cursor (see example below).
A section listing all the required features you implemented with a brief description of each.
A section listing all the custom features you implemented with a brief description of each.
You must NOT put your API keys or any sensitive credentials in the project folder or commit them to the repository. The README.md must clearly explain which API keys are needed and how to add them to the .env file. Provide also a .env.sample file with an example of the structure of the .env file and with fake values for the variables.
Here’s how the JSON configuration to connect Cursor to your MCP server could look like:

Copy
{
    "mcp_servers": {
        "your-server-name": {
            "command": "uv",
            "args": [
                "--directory",
                "/absolute/path/to/your/project",
                "run",
                "your-server-name"
            ],
            "env": {
                "YOUR_API_KEY": "your-api-key-here",
                "ANOTHER_KEY": "another-key-here"
            }
        }
    }
}
Custom Features
Here are custom features you may want to implement in your MCP server project. Each bullet point below represents one custom feature. Make sure at least 4 of these are implemented in your project.

The features are organized into categories below for clarity, but each individual bullet point counts as one feature.

Client & Integration:

Implement an MCP client application that demonstrates how to use your MCP server programmatically (not just through Cursor) and with custom orchestration/planning.
Integrate third-party APIs (e.g., web crawling, web search, weather data, financial data, social media APIs, etc.) to extend your server's functionality.
Implement useful MCP resources that provide contextual information or data to enhance your agent's capabilities.
Workflow & Agentic Patterns:

Implement at least 2-3 distinct workflow patterns in your MCP server (e.g., sequential workflows, parallel workflows, conditional branching, etc).
Implement at least one advanced agentic pattern such as ReAct (Reasoning and Acting), Plan-and-Execute, or other agent orchestration patterns. You could build agents within workflows, use agents as tools, or create nested agentic systems.
Advanced AI Patterns:

Implement Context-Augmented Generation (CAG). Only if it makes sense for your use case.
Implement Retrieval-Augmented Generation (RAG) by integrating a vector database or document retrieval system to ground your agent's responses in specific knowledge sources. Only if it makes sense for your use case.
Implement at least 3 long-term memory patterns (e.g. episodic, procedural, and semantic memory) to make your agent stateful and context-aware across sessions.
Human-in-the-Loop & UX:

Implement human-in-the-loop validation through an "AI Generation → Validation" pattern where the system generates content or decisions and explicitly waits for human review and approval before proceeding. This should go beyond the basic feedback step in prompts and focus on the overall UX of your application (e.g., suggesting edits to a document as diffs, generating a report draft and asking for approval before sending, suggesting multiple options and waiting for user selection, previewing changes before applying them).
Multi-Agent Systems:

Implement multi-agent orchestration where multiple specialized agents collaborate to solve complex tasks. This could include a manager agent coordinating worker agents, agents with different roles or expertise areas communicating with each other, or hierarchical agent structures.
Observability & Evaluation:

Add agent observability using a tool like Opik to track LLM calls, monitor token usage, log agent traces, and analyze the behavior of your AI app.
Implement an evaluation layer for your custom business use case by collecting a dataset of 20-30 samples and building a custom evaluator (e.g., LLM Judge) to measure the performance of your AI app (e.g., AI evals for your research agent).
Custom data:

Integrate custom data or datasets relevant to your domain (e.g., proprietary knowledge bases, industry-specific documents, curated collections of examples, historical data, user-generated content). Your agent should be able to process, analyze, or generate insights from this custom data to provide domain-specific value.
Multimodal:

Use multimodality by incorporating multimodal LLM calls (e.g., analyzing images, processing PDFs, generating images based on text, transcribing audio).
Code Quality & DevOps:

Set up comprehensive code quality tools including pre-commit hooks, linting with ruff, and code formatting to maintain professional code standards. Then, setup a CI pipeline in your GitHub by writing an appropriate YAML file in the .github folder. Containerize your MCP server using Docker and provide a Dockerfile and instructions for running the server in a container.
Implement MCP server authentication using a service like Descope to secure access to your agent's tools and prompts.
Database & Deployment:

Integrate a database backend (e.g., SQLite for lightweight applications or PostgreSQL for production-grade systems) to persist data, user interactions, or agent state. Provide setup instructions and include a docker-compose.yml file for easy database deployment alongside your MCP server.
Deploy your MCP server to a cloud platform like Google Cloud Platform (GCP), AWS, or Azure, and provide deployment instructions and configuration files in your repository.
Structured Outputs:

Use structured outputs in your LLM calls with Pydantic models to ensure consistent, validated responses from your agent.
We hope this project and certification will serve you either as:

A portfolio project for landing a job as an AI Agent Developer or AI Engineer (for one of the thousands of live AI jobs requiring parts of this skill set listed on our AI jobs board)
The foundation for bringing AI agent development skills into your current job and leading a new AI project or team at your company. We encourage you to make this project solve a real business problem or workflow challenge at your company or for your clients, creating a production-ready solution that demonstrates immediate value.
The seed of your revenue-generating side project, an ambitious startup, or a personal tool to boost your productivity in your work or hobbies.
Making Your Project Stand Out
Beyond meeting the requirements, we encourage you to make your project as polished and presentable as possible. This project can serve as a key piece of your professional portfolio when interviewing for AI engineering roles or showcasing your work to potential clients or collaborators.

Here are some recommendations for taking your project to the next level:

Make your repository look professional and welcoming. Write a compelling project description that clearly explains what problem your MCP server solves. Include badges in your README (e.g., Python version, license, build status if you set up CI). Add screenshots or GIFs demonstrating your agent in action. Consider adding a logo or banner image for your project. Include a clear, permissive license (e.g., MIT License) if you want others to be able to use and learn from your code.
A well-produced demo video can be incredibly powerful for showcasing your work. Your video should introduce the problem your MCP server solves, demonstrate your server in action with real examples, highlight the agentic workflow and show how user feedback is integrated, and explain any interesting technical decisions or challenges you overcame. Keep it concise (2-5 minutes is ideal) and engaging. You can either upload the video file directly to your GitHub repository and embed it in your README.md, or host it on YouTube, Loom, or another platform and link it in your README.md.
Strong documentation demonstrates professionalism and makes your project accessible. Write clear, step-by-step setup instructions with copy-paste ready commands that anyone can follow to get your project running. Include a "Common Issues" or "Troubleshooting" section if applicable. Document the purpose and parameters of each MCP tool. Explain the design of your agentic workflow and why you structured it that way. Consider adding architecture diagrams to visualize your system.
Clean, well-structured code makes a strong impression. Follow Python best practices and PEP 8 style guidelines. Use meaningful variable and function names. Add docstrings to your functions and classes. Structure your code into logical modules. Include error handling for edge cases. Also, highlight that the code passes the linting and formatting checks, along with the code tests.
A polished, well-documented project will not only help you earn your certification but will also be a valuable asset in your professional career as an AI engineer.

For inspiration, take a look at the following well-presented GitHub repositories:

GitHub GitHub - decodingai-magazine/second-brain-ai-assistant-course: Learn to build your Second Brain AI assistant with LLMs, agents, RAG, fine-tuning, LLMOps and AI systems techniques.GitHub GitHub - decodingai-magazine/second-brain-ai-assistant-course: Learn to build your Second Brain AI assistant with LLMs, agents, RAG, fine-tuning, LLMOps and AI systems techniques.
GitHub GitHub - PacktPublishing/LLM-Engineers-Handbook: The LLM's practical guide: From the fundamentals to deploying advanced LLM and RAG apps to AWS using LLMOps best practicesGitHub GitHub - PacktPublishing/LLM-Engineers-Handbook: The LLM's practical guide: From the fundamentals to deploying advanced LLM and RAG apps to AWS using LLMOps best practices
GitHub GitHub - neural-maze/philoagents-course: When Philosophy meets AIGitHub GitHub - neural-maze/philoagents-course: When Philosophy meets AI
GitHub GitHub - karpathy/nanoGPT: The simplest, fastest repository for training/finetuning medium-sized GPTs.GitHub GitHub - karpathy/nanoGPT: The simplest, fastest repository for training/finetuning medium-sized GPTs.
How to Share Your Project
First, double-check that your GitHub repository is public and that your README.md contains all the required sections as specified above.

In the next lesson, you must attach a .txt file where you will include the link to your GitHub repository. Use this very simple format for the .txt file, with the URL of your GitHub project page:

Copy
GitHub Repository: https://github.com/your-username/your-project-name
We'll get back to you within two weeks after receiving your project. If the checks are positive, we'll award your certification via the course platform. Otherwise, we'll give feedback on what is missing to achieve the certification.

Good luck with your project! We're excited to see what you build and look forward to awarding you your well-deserved certification. 🚀
