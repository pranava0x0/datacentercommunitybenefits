ObjC.import('PDFKit');
function run(argv){ const d=$.PDFDocument.alloc.initWithURL($.NSURL.fileURLWithPath(argv[0])); return d.string.js; }
