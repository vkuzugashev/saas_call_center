window.addEventListener("DOMContentLoaded", () => {
    const messages = document.createElement("ul");
    document.body.appendChild(messages);
  
    const websocket = new WebSocket("ws://localhost:5078/");
    websocket.onmessage = ({ data }) => {
      data = JSON.parse(data)
      console.log(data);
      $('#client_id').val(data.client_id);
      $('#caller').val(data.msisdn);
      $('#rows').empty();
      for (item of data.contracts){
        $('#rows').append(`<tr><td>${item.contract}</td><td>${item.status}</td></tr>`);
      }
      $('#exampleModal').modal('show');
    };
  });