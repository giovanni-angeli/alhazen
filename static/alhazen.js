
var ws_instance;  

var logging = function(data){
	_ = document.getElementById("logger_area").innerHTML;
	document.getElementById("logger_area").innerHTML = data.substring(0, 500) + "\n" + _;
	console.log(data);
};

var reset_model_params = function () {
	var msg_ = JSON.stringify({"command": "reset_model_params", "params": {}});
	ws_instance.send(msg_);
}

var refresh_data_graph = function () {
	var model_param_elements = Array.from(document.getElementsByClassName("model_param"));
	function get_id_value(item) {
		return [item.id, item.value];
	}
	var model_params = model_param_elements.map(get_id_value);
	var msg_ = JSON.stringify({"command": "refresh_data_graph", "params": model_params});
	ws_instance.send(msg_);
};

var import_model = function () {
	var model_ = document.getElementById("model_selector").value;
	var msg_ = JSON.stringify({"command": "import_model", "params": model_});
	logging(msg_);
	ws_instance.send(msg_);
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
		var msg_ = JSON.stringify({"command": "test", "params": value + " (" + i + ")"});
		logging("sending message to ws: '" + msg_ + "'");
		ws_instance.send(msg_);
	}
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

