import subprocess

def github_issue_list():
    """Returns a list of issues from the current GitHub repo using gh CLI."""
    try:
        result = subprocess.run(['gh', 'issue', 'list', '--json', 'number,title,state'], capture_output=True, text=True, check=True)
        return result.stdout
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    print(github_issue_list())
