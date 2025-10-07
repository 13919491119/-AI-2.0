# GitHub Chat Bot 示例（Python，适用于 GitHub Actions 或自托管机器人）
# 依赖 requests
# 用于监听 GitHub Issue/Discussion/PR 评论，自动调用玄机AI2.0 API 并回复

import os
import requests # pyright: ignore[reportMissingModuleSource]
from github import Github # pyright: ignore[reportMissingImports]
from flask import Flask, request, jsonify # pyright: ignore[reportMissingImports]

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
XUANJI_API_URL = os.environ.get("XUANJI_API_URL", "http://你的云服务器IP:8000/run_xuanji_ai")

app = Flask(__name__)

def call_xuanji_ai2(input_text):
    resp = requests.post(XUANJI_API_URL, json={"input": input_text}, timeout=30)
    return resp.json().get("result", "[AI2.0无响应]")

@app.route("/github_webhook", methods=["POST"])
def github_webhook():
    event = request.json
    # 监听 issue_comment、discussion_comment、pull_request_review_comment 等
    comment = None
    if "comment" in event:
        comment = event["comment"]["body"]
        comment_url = event["comment"]["url"]
    if comment and "运行玄机AI2.0" in comment:
        ai_result = call_xuanji_ai2(comment)
        # 回复评论
        g = Github(GITHUB_TOKEN)
        repo = event["repository"]["full_name"]
        issue_number = event.get("issue", {}).get("number")
        if issue_number:
            repo_obj = g.get_repo(repo)
            issue = repo_obj.get_issue(number=issue_number)
            issue.create_comment(f"[玄机AI2.0自动回复]:\n{ai_result}")
        else:
            # 其他类型评论（如PR review）可用 comment_url 回复
            requests.post(comment_url + "/replies", headers={"Authorization": f"token {GITHUB_TOKEN}"}, json={"body": f"[玄机AI2.0自动回复]:\n{ai_result}"})
    return jsonify({"msg": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)
