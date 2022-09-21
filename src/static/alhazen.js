
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

var error_handler = function(data){
    logging("ERROR:" + data);
    alert(data);
}

var clear_logger_area_view = function(){
	var el = document.getElementById("logger_area");
    if (window.confirm("comfirm clearing logs?") && el) {
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


var refresh_data_graph = function () {
	var object = {"command": "refresh_data_graph", "params": null};
	send_to_websocket_server(object);
};

var install_templates = function () {
    var _object = {"command": "install_templates", "params": null};
	send_to_websocket_server(_object);
    location.reload();
}

var on_file_selected = function (arg) {
	var _params = '';
    if (arg == 'structure') {
        _params = document.getElementById("structure_selector").value;
        _cmd = "structure_selected";
    } else if (arg == 'measure') {
        _params = document.getElementById("measure_selector").value;
        _cmd = "measure_selected";
    }
    var _object = {"command": _cmd, "params": _params};
	send_to_websocket_server(_object);
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
		error_handler("err:" + err);
	}
}

var close_btn_clicked = function () {
	try {
		ws_instance.close();
		ws_instance = null;
	} catch(err) {
		error_handler("err:" + err);
	}
}
var send_to_websocket_server = function (object) {
	if (ws_instance != null) {
		try {
			var msg_ = JSON.stringify(object);
			logging("send_to_websocket_server() msg_:'" + msg_ + "'");
			ws_instance.send(msg_);
		} catch(err) {
			error_handler("err:" + err);
		}
	} else {
		error_handler("Cannot send: the web socket is disconnected!");
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
	document.getElementById("close_btn").disabled = false; 

	refresh_data_graph();
}

var on_ws_close = function (evt) {
	logging("* ws connection closed *");
	ws_instance = null;
	document.getElementById("open_btn").disabled = false; 
	document.getElementById("open_btn").style.color = "red"; 
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
		error_handler("err:" + err);
	}
}

var init_wsocket = function () {
	 open_btn_clicked();
}

