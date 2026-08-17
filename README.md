# Merchant Release Writer

一个独立的商家产品发布 AI skill：把 PRD、原型、截图或已有稿件转换为事实准确的商家发布稿、配图计划和发布交接包。

## Skill

`skill/merchant-release-writer/`

支持 skill 文件的 AI agent 可以复制该目录并按产品说明启用。不支持安装 skill 的 AI，也可以读取 `SKILL.md`、模板、参考资料和脚本后执行相同工作流。

## 验证

```bash
python3 /path/to/skill-creator/scripts/quick_validate.py skill/merchant-release-writer
python3 -m compileall -q skill/merchant-release-writer
python3 skill/merchant-release-writer/scripts/validate_release_package.py --draft <draft.md> --type single
```

## 安全边界

- 不保存密码、Cookie、token、个人 UID 或内部系统 ID。
- 不把测试内容写入生产环境。
- 最终正式提交、发布或更新默认由用户亲自完成。

## License

MIT
