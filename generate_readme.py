import os
import glob
from typing import TypedDict
from github import Github
from langchain_ollama import OllamaLLM
from langgraph.graph import StateGraph, END

# --- CONFIGURATION ---
REPO_PATH = "./"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "YOUR_PERSONAL_ACCESS_TOKEN")
GITHUB_REPO_NAME = "your-username/your-repo-name"
OLLAMA_MODEL = "llama3.2"

# Extensions that reveal project structure & story
INCLUDED_EXTENSIONS = (".py", ".json", ".yaml", ".yml", ".sh", ".md", "Dockerfile")
EXCLUDE_DIRS = ("venv", "__pycache__", ".git", ".idea", "node_modules")

class GraphState(TypedDict):
    tree_structure: str
    code_summary: str
    readme_content: str

# Node 1: Read whole folder structure + all key files
def read_code_node(state: GraphState) -> GraphState:
    tree = []
    combined_code = []

    for root, dirs, files in os.walk(REPO_PATH):
        # Skip excluded virtualenv/cache directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        level = root.replace(REPO_PATH, '').count(os.sep)
        indent = ' ' * 4 * (level)
        tree.append(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 4 * (level + 1)

        for file in files:
            tree.append(f"{subindent}{file}")
            file_path = os.path.join(root, file)
            
            # Read relevant source & config files
            if file.endswith(INCLUDED_EXTENSIONS) and not file.startswith('.'):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        # Limit individual file length if massive
                        combined_code.append(f"--- File: {file_path} ---\n{content[:4000]}\n")
                except Exception as e:
                    print(f"Skipping {file_path}: {e}")

    state["tree_structure"] = "\n".join(tree)
    state["code_summary"] = "\n".join(combined_code)
    return state

# Node 2: Generate README telling the whole narrative
def generate_readme_node(state: GraphState) -> GraphState:
    llm = OllamaLLM(model=OLLAMA_MODEL)
    
    prompt = f"""
You are a Principal Software Architect and Technical Author. 
Analyze the full directory structure and file contents below to write a comprehensive, narrative-driven README.md.

Tell the complete "story" of this project:
1. **Overview & Mission**: What real-world problem does this project solve? What is its core story?
2. **Directory Architecture**: Explain how the folders/modules interact based on this structure:
{state['tree_structure']}

3. **Core Workflow & Components**: Walk through how data/control flows across the modules.
4. **Key Features**: Highlight technical capabilities.
5. **Setup & Execution**: Prerequisites, environment variables, step-by-step launch instructions.
6. **Screenshot / UI / Output Placeholders**: Use exact tags like:
   `> 📸 **Screenshot Placeholder:** Describe the visual/log output to display here.`
   `![Description](path/to/image.png)`

Source Code & Configuration Data:
{state['code_summary'][:20000]}
"""
    
    response = llm.invoke(prompt)
    state["readme_content"] = response
    return state

# Node 3: Save locally & Push to GitHub
def push_to_github_node(state: GraphState) -> GraphState:
    readme_text = state["readme_content"]
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_text)
    print("✅ Saved README.md locally.")

    if GITHUB_TOKEN != "YOUR_PERSONAL_ACCESS_TOKEN":
        try:
            g = Github(GITHUB_TOKEN)
            repo = g.get_repo(GITHUB_REPO_NAME)
            try:
                contents = repo.get_contents("README.md")
                repo.update_file("README.md", "docs: update comprehensive README via LangGraph", readme_text, contents.sha)
                print("✅ Updated README.md on GitHub!")
            except Exception:
                repo.create_file("README.md", "docs: create comprehensive README via LangGraph", readme_text)
                print("✅ Created README.md on GitHub!")
        except Exception as e:
            print(f"⚠️ GitHub Push skipped/failed: {e}")
    else:
        print("ℹ️ Set GITHUB_TOKEN environment variable to enable direct GitHub commits.")
        
    return state

# --- BUILD WORKFLOW ---
workflow = StateGraph(GraphState)
workflow.add_node("read_code", read_code_node)
workflow.add_node("generate_readme", generate_readme_node)
workflow.add_node("push_to_github", push_to_github_node)

workflow.set_entry_point("read_code")
workflow.add_edge("read_code", "generate_readme")
workflow.add_edge("generate_readme", "push_to_github")
workflow.add_edge("push_to_github", END)

app = workflow.compile()

if __name__ == "__main__":
    print("🚀 Running complete codebase analysis & README generator...")
    app.invoke({"tree_structure": "", "code_summary": "", "readme_content": ""})
       
