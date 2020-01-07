
// ########################  begin DOMContentLoaded ########################
document.addEventListener('DOMContentLoaded', () => {

  var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);
  socket.on('connect', () => {

  }); // end on connect


  setup_toggle_stream()
  setup_log_listing(socket)

});
// ########################  end DOMContentLoaded ########################


// sets up stop/start button to respond to click
function setup_toggle_stream() {
  document.querySelector('#btn_toggle_stream').onclick = () => {
    toggle_stream();
  };
} // end setup_toggle_stream()

// will add post to the chat window and set appropriate screen elements
function toggle_stream() {
  let button = document.querySelector('#btn_toggle_stream');
  if (button.textContent==='Stop') {
    button.textContent = 'Start';
  } else {
    button.textContent = 'Stop';
  }
} // end toggle_stream()

function setup_log_listing(socket) {
  socket.on('update_log', log_data => {
    update_log(log_data);
  });
}

function update_log(log_data) {
  const new_log_item = document.createElement("div");
  const log_listing = document.querySelector("#log_listing")

  // set new element text to include logged data
  new_log_item.innerHTML = `${log_data}`;

  // add the new log element to the log listing
  log_listing.appendChild(new_log_item);

  // scroll to the bottom
  log_listing.scrollTop = log_listing.scrollHeight

}

