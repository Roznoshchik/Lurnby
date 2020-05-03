
var path = require("path");
var fs = require("fs");

var url = require("url");

const JSDOM = require('jsdom').JSDOM


// We want to load Readability, which isn't set up as commonjs libraries,
// and so we need to do some hocus-pocus with 'vm' to import them on a separate scope
// (identical) scope context.
var vm = require("vm");
var readabilityPath = path.join(__dirname, "Readability.js");

var scopeContext = {};
// We generally expect dump() and console.{whatever} to work, so make these available
// in the scope we're using:
scopeContext.dump = console.log;
scopeContext.console = console;
scopeContext.URL = url.URL;
scopeContext.JSDOM = JSDOM;

// Actually load files. NB: if either of the files has parse errors,
// node is dumb and shows you a syntax error *at this callsite* . Don't try to find
// a syntax error on this line, there isn't one. Go look in the file it's loading instead.
vm.runInNewContext(fs.readFileSync(readabilityPath), scopeContext, readabilityPath);

var Readability = scopeContext.Readability;

var argv = require('minimist')(process.argv.slice(2));

function readFile(filePath) {
  return fs.readFileSync(filePath, {encoding: "utf-8"}).trim();
}
function writeFile(data, filePath) {
  return fs.writeFileSync(filePath, data, {encoding: "utf-8"});
}

var inFilePath = argv['i'];
var outFilePath;

if (typeof(argv['o']) !== 'undefined') {
    outFilePath = argv['o'];
} else {
    outFilePath = inFilePath + ".simple.json";
}
var html = readFile(inFilePath);

var doc = new scopeContext.JSDOM(html).window.document;
var article = new scopeContext.Readability(doc).parse();

writeFile(JSON.stringify(article), outFilePath);