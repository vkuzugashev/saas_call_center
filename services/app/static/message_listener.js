 window.addEventListener("DOMContentLoaded", () => {
    const messages = document.createElement("ul");
    document.body.appendChild(messages);
    // Получаем текущий хост и порт
    var host = window.location.host;
    // удалим порт, если он есть
    var index = host.lastIndexOf(":");
    if (index != -1)
      host = host.substring(0, index);    
    // Создаем относительный адрес WebSocket
    var socketUrl = 'ws://' + host + ':5078/';
    const websocket = new WebSocket(socketUrl);
    websocket.onmessage = ({ data }) => {
      data = JSON.parse(data)
      console.log(data);
      $('#client_id').val(data.client_id);
      $('#caller').val(data.msisdn);
      $('#rows').empty();
      for (item of data.contracts){
        $('#rows').append(`<tr><td>${item.contract}</td><td>${item.status}</td></tr>`);
      }
      $('#callModal').modal('show');
    };
  });