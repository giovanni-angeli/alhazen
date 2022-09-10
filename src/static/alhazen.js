
var ws_instance;  

var logging = function(data){
	console.log(data);
	var el = document.getElementById("logger_area");
	if (el) {
		let s = new Date().toLocaleString();
		_ = el.innerHTML.substring(0, 10000);
		el.innerHTML = "[" + s + "]" + data.substring(0, 100) + "\n" + _;
	}
};

var clear_logger_area_view = function(){
	var el = document.getElementById("logger_area");
	if (el) {
		el.innerHTML = '';
	}
};

var toggle_logger_area_view = function(){
	var el = document.getElementById("logger_area");
	if (el) {
		if (el.style.display == 'block'){
			el.style.display = 'none';
		} else {
			el.style.display = 'block';
		}
	}
};

var reset_model_params = function () {
	var object = {"command": "reset_model_params", "params": {}};
	send_to_websocket_server(object);
}

var refresh_data_graph = function () {
	var model_param_elements = Array.from(document.getElementsByClassName("model_param"));
	function get_id_value(item) {
		return [item.id, item.value];
	}
	var model_params = model_param_elements.map(get_id_value);
	var object = {"command": "refresh_data_graph", "params": model_params};
	send_to_websocket_server(object);
};

var import_model = function () {
	var model_ = document.getElementById("model_selector").value;
	var object = {"command": "import_model", "params": model_};
	send_to_websocket_server(object);
	refresh_data_graph();
}

var open_btn_clicked = function () {

	var host = document.getElementById("host").value;
	var port = document.getElementById("port").value;
	var uri  = document.getElementById("uri").value;
	try {

		if (ws_instance) {
			ws_instance.close();
		}
		var resource = "ws://" + host + ":" + port + uri;
		logging("connecting to: " + resource);
		ws_instance = new WebSocket(resource);
		ws_instance.onerror   = on_ws_error  ; 
		ws_instance.onopen    = on_ws_open   ;  
		ws_instance.onclose   = on_ws_close  ;
		ws_instance.onmessage = on_ws_message;
	} catch(err) {
		logging("err:" + err);
	}
}

var close_btn_clicked = function () {
	try {
		ws_instance.close();
		ws_instance = null;
	} catch(err) {
		logging("err:" + err);
	}
}
var send_btn_clicked = function () {
	var value = document.getElementById("message").value;
	for (i = 0; i < 10; i++) { 
		var object = {"command": "test", "params": value + " (" + i + ")"};
		send_to_websocket_server(object);
	}
}

var send_to_websocket_server = function (object) {
	var msg_ = JSON.stringify(object);
	logging("send_to_websocket_server() msg_:'" + msg_ + "'");
	ws_instance.send(msg_);
}

var on_ws_error = function (evt) {
	logging("error: " + evt.data);
	alert("error: " + evt.data);
}

var on_ws_open = function (evt) {
	logging("* ws connection open *");
	document.getElementById("open_btn").disabled = true; 
	document.getElementById("open_btn").style.color = "gray"; 
	document.getElementById("send_btn").disabled = false; 
	document.getElementById("close_btn").disabled = false; 

	reset_model_params();
	refresh_data_graph();
}

var on_ws_close = function (evt) {
	logging("* ws connection closed *");
	document.getElementById("open_btn").disabled = false; 
	document.getElementById("open_btn").style.color = "red"; 
	document.getElementById("send_btn").disabled = true; 
	document.getElementById("close_btn").disabled = true; 
	document.getElementById("close_btn").style.color = "grey"; 
}

var on_ws_message = function (evt) {
	try {
		var data = JSON.parse(evt.data);            
		//~ if ((data.innerHTML) && (data.element_id)) {
		if ((data.innerHTML != null) && (data.element_id)) {
			var el = document.getElementById(data.element_id)
			if (el) { 
				el.style.display = 'block';
				el.innerHTML = data.innerHTML; 
			}
		}
	} catch(err) {
		logging("err:" + err);
	}
}

var init_alhazen = function () {
	 open_btn_clicked();
}

