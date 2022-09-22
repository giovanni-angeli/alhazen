
var ws_instance;  


var on_template_clicked = function(action, type, file_name) {
    if (confirm("confirm " + action + ": " + file_name + "?")) {
        if (action == 'edit') {
            alert("Sorry, action edit is not yet implemented.");
            return;
        };
        var object = {"command": "on_template_clicked", "params": {'action': action, 'type': type, 'file_name': file_name}};
        send_to_websocket_server(object);

        setTimeout(function() { location.reload(); }, 200);
    };
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

var refresh_data_graph = function () {
    var params = {};
    const editable_parameters = document.getElementsByClassName('editable_parameter');
    for (let i = 0; i < editable_parameters.length; i++) {
        params[editable_parameters[i].name] = editable_parameters[i].value;
    };
	var object = {"command": "refresh_data_graph", "params": params};
	send_to_websocket_server(object);
};

var install_templates = function () {
    var _object = {"command": "install_templates", "params": null};
	send_to_websocket_server(_object);

    setTimeout(function() { location.reload(); }, 200);
}

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
		//~ console.log(JSON.stringify(data));
		//~ console.log(JSON.stringify(data.data));
		//~ console.log(JSON.stringify(data.innerHTML));
		//~ console.log(JSON.stringify(data.id));
        var el = document.getElementById(data.element_id)
        if (el) {
            el.style.display = 'block';
            if (data.innerHTML != null) {
                if (el) { 
                    el.innerHTML = data.innerHTML; 
                }
            } else if (data.data != null) {
                var el = document.getElementById(data.element_id)
                if (el) { 
                    el.data = data.data; 
                    el.width = 1200;
                    el.height = 600;
                }
            }
		}
	} catch(err) {
		error_handler("err:" + err);
	}
}

var init_wsocket = function () {
	 open_btn_clicked();
}
