#!/usr/bin/env bash
# ShortPFAS-Net 一键发布脚本
# 用法: bash publish.sh <你的GitHub用户名>
# 例如: bash publish.sh stephen

set -euo pipefail

cd "$(dirname "$0")"

REPO_NAME="short-pfas-net"
GITHUB_USER="${1:-}"

if [ -z "$GITHUB_USER" ]; then
  echo "用法: bash publish.sh <你的GitHub用户名>"
  echo "例如: bash publish.sh stephen"
  exit 1
fi

echo "==> 清理可能残留的 git 锁文件"
rm -f .git/index.lock .git/config.lock 2>/dev/null || true

echo "==> 初始化 git 仓库（如尚未初始化）"
if [ ! -d .git ]; then
  git init
fi

echo "==> 配置 git 用户信息（如未配置，可手动改成你的真实信息）"
git config user.name  "Stephen"           || true
git config user.email "stephen@example.com" || true

echo "==> 暂存所有正式文件"
git add -A

echo "==> 提交（首次提交）"
if git rev-parse --verify HEAD >/dev/null 2>&1; then
  echo "已有提交，跳过首次提交"
else
  git commit -m "Initial commit: ShortPFAS-Net multi-modal deep learning for short-chain PFAS removal prediction"
fi

echo "==> 检查是否已关联远程仓库"
if git remote get-url origin >/dev/null 2>&1; then
  echo "远程仓库已关联: $(git remote get-url origin)"
else
  echo "==> 请先在 GitHub 网页上手动创建空仓库: https://github.com/new"
  echo "    仓库名建议: $REPO_NAME"
  echo "    不要勾选 Initialize with README（我们本地已有）"
  echo ""
  echo "    创建完成后，执行下面命令关联并推送（把 GITHUB_USER 换成你的用户名）:"
  echo ""
  echo "    git remote add origin https://github.com/$GITHUB_USER/$REPO_NAME.git"
  echo "    git branch -M main"
  echo "    git push -u origin main"
  echo ""
  echo "    如果你已安装 GitHub CLI (gh)，也可以直接运行:"
  echo "    gh repo create $REPO_NAME --public --source=. --remote=origin --push"
fi

echo ""
echo "==> 完成。以下信息供你参考:"
echo "    仓库名: $REPO_NAME"
echo "    当前分支: $(git branch --show-current 2>/dev/null || echo 'main')"
