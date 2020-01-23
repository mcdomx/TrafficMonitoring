
const socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

// ########################  begin DOMContentLoaded ########################
document.addEventListener('DOMContentLoaded', () => {


  socket.on('connect', () => {
    log_text(location.protocol + '//' + document.domain + ':' + location.port);
    log_text("Socket connected on client!")
  }); // end on connect

  setup_buttons();
  setup_log_listing(socket);
  setup_vid_stats(socket);
  setup_app_log(socket)

});
// ########################  end DOMContentLoaded ########################


// sets up stop/start button to respond to click
function setup_buttons() {
  document.querySelector('#btn_toggle_stream').onclick = () => {
    toggle_stream();
  };

//  document.querySelector("#btn_increase").onclick = () => {
//    increase(socket);
//  };
//
//  document.querySelector("#btn_decrease").onclick = () => {
//    decrease(socket);
//  };

  document.querySelector("#btn_toggle_monitoring").onclick = () => {
    toggle_ONOFF("#monitoring_status", "#btn_toggle_monitoring");
  };

  document.querySelector("#btn_toggle_logging").onclick = () => {
    toggle_ONOFF("#logging_status", "#btn_toggle_logging");
  };

} // end setup_buttons()

// BUTTON TOGGLES #############################
// will add post to the chat window and set appropriate screen elements
function toggle_stream() {
  let button = document.querySelector('#btn_toggle_stream');
  if (button.textContent==='Stop') {
    button.textContent = 'Start';
  } else {
    button.textContent = 'Stop';
  }
} // end toggle_stream()

function toggle_ONOFF(btn_id) {

  let button = document.querySelector(btn_id);

  if (button.innerHTML==='ON') {
    button.innerHTML = 'OFF';
  } else {
    button.innerHTML = 'ON';
  }
}

// END BUTTON TOGGLES #############################


// CHECK BOXES #############################
function checkbox_click(checkboxElem) {
  let val = checkboxElem.id.split("_");
  log_text("item checked: " + val[0] + " " + val[1] + " " + checkboxElem.checked)
  socket.emit(val[0], val[1])
}
// END CHECK BOXES #############################


// LOG LISTING ################################
function setup_log_listing(socket) {
  socket.on('update_log', log_data => {
    update_log(log_data);
  });
}

function _make_table_row(c1_data, c2_data, c3_data) {

  let c1 = document.createElement("td");
  // c1.className = "col-4";
  c1.innerHTML = `${c1_data}`;

  let c2 = document.createElement("td");
  // c2.className = "col-4";
  c2.innerHTML = `${c2_data}`;

  let c3 = document.createElement("td");
  // c3.className = "col-4";
  c3.innerHTML = `${c3_data}`;

  // add the data element to the row as a child
  let table_row = document.createElement('tr');
  table_row.appendChild(c1);
  table_row.appendChild(c2);
  table_row.appendChild(c3);

  return table_row
}

function update_log(log_data) {
  // convert data into js objects
  let json_data = JSON.parse(log_data);


  // iterate over json data adding row for each k-v pair
  let first_item = true;
  for ( let k in json_data ) {

    if (k==='time_stamp')
      {continue;}

    // define data elements
    let c1_data = "";
    if (first_item === true) {
      c1_data = `${json_data['time_stamp']}`;
      first_item = false
    }

    let c2_data = " - - ";
    let c3_data = " - - ";
    if (json_data.hasOwnProperty(k)) {
      c2_data = `${k}`;
      c3_data = (Math.round(parseFloat(json_data[k])*10000)/10000).toString();
    } // end if

    // create the html row
    let new_row = _make_table_row(c1_data, c2_data, c3_data);

    // add the row to the table as a child
    let log_body = document.querySelector("#log_body");
    log_body.appendChild(new_row);

    // if entries greater than max setting, remove oldest entry

    if (log_body.childElementCount > 100) {
      log_text("Removed log item ... ");
      log_body.removeChild(log_body.childNodes[0]);
    }
  } // end for loop

  // scroll to the bottom
  let log_container = document.querySelector("#log_container");
  log_container.scrollTop = log_container.scrollHeight

} // end function
// END LOG LISTING ################################

// APPLICATION LOG ################################
function log_text(log_text){

  let log_update = document.createElement("p");
  log_update.innerHTML = log_text;

  let log = document.querySelector("#app_log");
  log.appendChild(log_update) ;

  // scroll to the bottom
  log.scrollTop = log.scrollHeight

}

function setup_app_log(socket) {
  socket.on('app_log', log_text => {
    log_text(log_text);
  });
}


// END APPLICATION LOG ################################

// VIDEO STATISTICS SIZE ################################
function setup_vid_stats(socket){
  socket.on('update_vid_stats', vid_stats => {
    update_vid_stats(vid_stats);
  });
}

//function increase(socket) {
//  socket.emit('increase');
//}
//
//function decrease(socket) {
//  socket.emit('decrease');
//}

function update_vid_stats(vid_stats){
  let json_data = JSON.parse(vid_stats);

  if (json_data.hasOwnProperty('buffer_size')) {
    let bsize = document.querySelector("#buffer_size");
    bsize.innerHTML = `${json_data['buffer_size']}`
  }

  if (json_data.hasOwnProperty('ttl_delay')) {
    let bsize = document.querySelector("#ttl_delay");
    bsize.innerHTML = `${json_data['ttl_delay']}`
  }

}

// END VIDEO STATISTICS SIZE ################################
