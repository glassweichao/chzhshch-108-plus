
const fs = require('fs');
const path = require('path');

// 源文件命名规则：0187-486e105c01000461-001.md  /  -W004.md  /  -(4).md
// 仅匹配该规则的文件，从根本上避免把生成产物（108-All.md 等）当作源文件重复读入
// —— 这是原脚本「重复运行导致内容翻倍」陷阱的根因。
const SOURCE_RE = /^\d{4}-486e105c0100[\w]+-(\d{3}|W\d{3}|\(\d+\))\.md$/;
const LESSON_RE = /-(\d{3}|W\d{3}|\(\d+\))\.md$/;

// 排序：001..108 正式课文 → W 补遗 → (N) 括号补遗
function lessonKey(name) {
    const k = name.match(LESSON_RE)[1];
    const rank = k.startsWith('(') ? 2 : k.startsWith('W') ? 1 : 0;
    return rank * 1000 + parseInt(k.replace(/\D/g, ''), 10);
}

const mdFileList = fs.readdirSync('./108')
    .filter(f => SOURCE_RE.test(f))
    .sort((a, b) => lessonKey(a) - lessonKey(b));

let mdAllContent = "[toc]\r\n";
let mdArticleContent = "[toc]\r\n";

const readmeContent = fs.readFileSync("./README.md", 'utf-8');

// 全部
mdAllContent += readmeContent + "\r\n\r\n";

// 只包含课文
mdArticleContent += readmeContent + "\r\n\r\n";

for (const szMDFileName of mdFileList) {
    const realFileName = `./108/${szMDFileName}`;

    const oneMDContent = fs.readFileSync(realFileName, 'utf-8');
    const artileMDContent = oneMDContent.split("**本文评论获取自")[0];

    // 全部
    mdAllContent += oneMDContent + "\r\n\r\n";

    // 只包含课文
    mdArticleContent += artileMDContent + "\r\n\r\n";
}

fs.writeFileSync("./108/108-All.md", mdAllContent);
fs.writeFileSync("./108/108-artileOnly.md", mdArticleContent);

console.log(`✓ 已合并 ${mdFileList.length} 篇源文件 → 108/108-All.md、108/108-artileOnly.md`);
