const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const source = fs.readFileSync(path.join(root, "frontend", "src", "views", "LoginView.vue"), "utf8");

const requiredSnippets = [
  "loginBackgrounds",
  "currentBackgroundIndex",
  "setInterval",
  "onMounted",
  "onBeforeUnmount",
  "carousel-dot",
  "login-bg-layer",
  "login-glass-card",
  "login-bg-campus-entrance.png",
  "login-bg-campus-corridor.png",
  "login-bg-student-service.png",
  "login-bg-campus-courtyard.png",
];

const missing = requiredSnippets.filter((snippet) => !source.includes(snippet));

if (missing.length > 0) {
  console.error(`登录页轮播实现缺少关键片段: ${missing.join(", ")}`);
  process.exit(1);
}

const assetNames = [
  "login-bg-campus-entrance.png",
  "login-bg-campus-corridor.png",
  "login-bg-student-service.png",
  "login-bg-campus-courtyard.png",
];

const missingAssets = assetNames.filter(
  (name) => !fs.existsSync(path.join(root, "frontend", "src", "assets", name)),
);

if (missingAssets.length > 0) {
  console.error(`登录页轮播背景资源缺失: ${missingAssets.join(", ")}`);
  process.exit(1);
}

console.log("frontend login carousel check passed");
