#!/usr/bin/env bash
# 检查前端代码中是否有 any 类型残留
set -euo pipefail

echo "🔍 检查前端代码中的 any 类型..."

HAS_ANY=$(grep -rn "any" src/ --include="*.ts" --include="*.vue" 2>/dev/null | grep -v node_modules | grep -v "\.test\." | head -20 || true)

if [ -n "$HAS_ANY" ]; then
  echo "❌ 发现 any 类型使用："
  echo "$HAS_ANY"
  exit 1
else
  echo "✅ 前端代码无 any 类型"
fi
