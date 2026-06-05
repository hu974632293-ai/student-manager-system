const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const weather = fs.readFileSync(path.join(root, "frontend", "src", "views", "WeatherView.vue"), "utf8");
const geocode = fs.readFileSync(path.join(root, "frontend", "src", "views", "GeocodeView.vue"), "utf8");

function assertIncludes(source, text, message) {
  if (!source.includes(text)) throw new Error(message);
}

assertIncludes(weather, "@submit.prevent=\"query\"", "天气查询缺少原生 submit 兜底");
assertIncludes(weather, "native-type=\"submit\"", "天气查询按钮不是 submit 按钮");
assertIncludes(weather, "form.latitude", "天气查询缺少纬度输入");
assertIncludes(weather, "form.longitude", "天气查询缺少经度输入");
assertIncludes(geocode, "@submit.prevent=\"query\"", "经纬度查询缺少原生 submit 兜底");
assertIncludes(geocode, "native-type=\"submit\"", "经纬度查询按钮不是 submit 按钮");
