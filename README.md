# LLM-Driven Conversational Movie Recommendation & Taste Graph Service

This repository contains the implementation for our course final project: an end-to-end movie recommendation system powered by LLMs, personalized taste embeddings, and agentic workflows.

To ensure smooth collaboration and integration across team members, please follow the guidelines below.

### python version: Python 3.11.14

---

## 📁 Project Structure
```
COMS6998FinalProject/
│
├── TasteEmbeddingGenerator/   # Task 1: User/Movie embedding generation
│   ├── README.md
│   └── ...
│
├── Demo/                      # Task 2: Conversational recommendation demo UI
│   ├── README.md
│   └── ...
│
├── AgenticFlow/               # Task 3: Agent-based LLM reasoning & retrieval pipeline
│   ├── README.md
│   └── ...
│
├── Dataset/                   # Raw & processed datasets
│   ├── README.md
│   └── ...
│
└── README.md                  # Collaboration guidelines (this file)

```


### **Task-to-Directory Mapping**

| Task | Description | Directory |
|------|-------------|-----------|
| **Task 1** | Generate user/movie embeddings and taste graph components | `TasteEmbeddingGenerator/` |
| **Task 2** | Build and run the recommendation demo | `Demo/` |
| **Task 3** | Agentic flow for conversational recommendation and tool reasoning | `AgenticFlow/` |

---

## 🧑‍💻 Collaboration Guidelines

### **1. Work Inside Your Assigned Directory**
Each member should implement features **within the directory corresponding to their assigned task**.

When your module is ready to push, please include:
- A brief explanation (`README.md` or `.txt`) describing:
  - What was implemented  
  - How to run or test it  
  - Any assumptions or design choices  

This helps team members understand updates quickly and integrate modules smoothly.

---

## 📦 Virtual Environment & Dependencies

We will use a **virtual environment** throughout the project.

### **When pushing code:**
1. Update `requirements.txt` if new dependencies were added.
2. Before pushing changes:

```bash
pip freeze > requirements.txt
```
3. Commit and push the updated file.

This keeps dependency management consistent for all modules.

---

## 🔄 Integration Workflow

When pushing major updates:

1. Add a short summary in the associated directory (README or notes file).
2. Ensure your code runs using only packages listed in requirements.txt.
3. Avoid breaking imports in other directories.
4. If shared utilities are needed later, we will add a utils/ directory.

---

## 🚀 Setup Instructions

To create a virtual environment and install dependencies:

```bash
python3 -m venv .YOURVENV
source .YOURVENV/bin/activate
pip install -r requirements.txt
```

Always install dependencies this way before testing integration.