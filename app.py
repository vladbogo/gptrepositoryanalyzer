from flask import Flask, request, jsonify
import git
import os
from werkzeug.exceptions import BadRequest, NotFound

app = Flask(__name__)
repos_dir = 'cloned_repos'  # Directory where repositories will be cloned
os.makedirs(repos_dir, exist_ok=True)  # Ensure the directory exists

@app.route('/commit/<repo_name>/<commit_hash>', methods=['GET'])
def get_commit_diff(repo_name, commit_hash):
    if not repo_name.endswith('.git'):
        repo_name += '.git'
    repo_path = os.path.join(repos_dir, repo_name)
    if not os.path.isdir(repo_path):
        raise NotFound(description='Repository not found.')

    try:
        repo = git.Repo(repo_path)
        commit = repo.commit(commit_hash)
        # Get the diff of the commit against its parent
        diffs = commit.diff('HEAD~1', create_patch=True)
        commit_changes = []
        for diff in diffs:
            # For each file changed, append the diff to the commit_changes list
            commit_changes.append({
                'file_path': diff.a_path,
                'diff': diff.diff.decode('utf-8') if diff.diff else '',
            })
        return jsonify(commit_changes), 200
    except ValueError as ve:
        # This occurs if the commit hash is not found in the repository
        raise NotFound(description='Commit not found.')
    except Exception as e:
        raise BadRequest(description=str(e))

@app.route('/clone_repo', methods=['POST'])
def clone_repo():
    data = request.json
    repo_url = data.get('url')
    if not repo_url:
        raise BadRequest(description='URL is required.')

    try:
        repo_name = repo_url.split('/')[-1]
        if not repo_name.endswith('.git'):
            repo_name += '.git'
        repo_path = os.path.join(repos_dir, repo_name)
        if os.path.isdir(repo_path):
            return jsonify({'message': 'Repository already cloned.'}), 200

        git.Repo.clone_from(repo_url, repo_path)
        return jsonify({'message': f'Repository cloned into {repo_path}'}), 201
    except Exception as e:
        raise BadRequest(description=str(e))

@app.route('/latest_changes/<repo_name>', methods=['GET'])
def latest_changes(repo_name):
    if not repo_name.endswith('.git'):
        repo_name += '.git'
    repo_path = os.path.join(repos_dir, repo_name)
    if not os.path.isdir(repo_path):
        raise NotFound(description='Repository not found.')

    try:
        repo = git.Repo(repo_path)
        # Determine the default branch
        default_branch = next((ref for ref in repo.remote().refs if ref.remote_head == 'HEAD'), None)
        if default_branch is None:
            raise ValueError("Default branch not found.")
        default_branch_name = default_branch.name.split('/')[-1]

        # Fetch the latest commits from the default branch
        commits = list(repo.iter_commits(default_branch_name, max_count=10))
        changes = [{'commit': commit.hexsha, 'message': commit.message} for commit in commits]
        return jsonify(changes), 200
    except Exception as e:
        raise BadRequest(description=str(e))

@app.route('/readme/<repo_name>', methods=['GET'])
def get_readme(repo_name):
    if not repo_name.endswith('.git'):
        repo_name += '.git'
    repo_path = os.path.join(repos_dir, repo_name)
    readme_path = os.path.join(repo_path, 'README.md')
    if not os.path.isfile(readme_path):
        raise NotFound(description='README.md not found.')

    try:
        with open(readme_path, 'r') as file:
            readme_content = file.read()
        return jsonify({'readme_content': readme_content}), 200
    except Exception as e:
        raise BadRequest(description=str(e))

if __name__ == '__main__':
    app.run(debug=True, port=5000)

