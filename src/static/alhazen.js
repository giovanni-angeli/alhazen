
var ws_instance;  
var ws_on_connect_call_back;  


/* functions used in setup */
var on_save_file_button_clicked = function() {
    const file_name = document.getElementById("view_file_name").value;
    const type = document.getElementById("view_file_type").innerHTML;
    const file_content = document.getElementById("view_file_content").innerHTML;
    if (confirm("confirm save: " + file_name + "?")) {
        var params = {'file_content': file_content, 'type': type, 'file_name': file_name};
        var object = {"command": "save_template", "params": params};
        send_to_websocket_server(object);
    }
}

var on_template_clicked = function(action, type, file_name) {
    if (confirm("confirm " + action + ": " + file_name + "?")) {
        var object = {"command": "on_template_clicked", "params": {'action': action, 'type': type, 'file_name': file_name}};
        send_to_websocket_server(object);

        //~ if (action != 'edit') {
            //~ setTimeout(function() { location.reload(); }, 200);
        //~ };
    };
}

var refresh_file_lists = function () {
    object = {"command": "refresh_file_lists", "params": {}};
    send_to_websocket_server(object);
};

var install_templates = function () {
    if (confirm("confirm install templates" + "?\n (will overwrite existent copies)")) {
        var _object = {"command": "install_templates", "params": null};
        send_to_websocket_server(_object);
    }
}
/* /functions used in setup */

/* main page actions */
var on_file_selected = function (arg) {

    /* if a file is selected (or the selection changed) in the main page, it
     * means that the plot must be refreshed. In addition, if the file is a
     * structure file, the structure dialog must also be refreshed
     */
    var _object = null;

    /* send a "command" to the frontend to apply the relative python
     * function there.
     */
    _object = {"command": arg+"_selected", "params": document.getElementById(arg+"_selector").value};
    send_to_websocket_server(_object);

    /* refresh the structure (call the functions below that send all the
     * necessary information to python to rebuild the plot.
     */
    refresh_plot();

    /* if the file selected is a structure file, it call the functions below
     * to refresh the structure
     */
    /*
    if (arg == "structure") {
        refresh_structure();
    }
    */
    refresh_structure();
}

var refresh_structure = function () {

    /* send to python the "command" to refresh the html containing the
     * structure description
     */
    var _object = null;

    _object = {"command": "refresh_structure", "params": document.getElementById("structure_selector").value}
    send_to_websocket_server(_object);
};

var refresh_plot = function () {

    /* TODO: rimuovere il chi2 da questa funzione!!! */

    var _object = null;

    var plot_formData = new FormData(document.getElementById('plot_edit_panel_form'));
    var model_formData = new FormData(document.getElementById('model_edit_panel_form'));
    var chi2_formData = new FormData(document.getElementById('chi2_panel_form'));
    _object = {
        "command": "refresh_plot", 
        "params": {
            'plot_edit_panel': Object.fromEntries(plot_formData.entries()),
            'model_edit_panel': Object.fromEntries(model_formData.entries()),
            'chi2_edit_panel': Object.fromEntries(chi2_formData.entries())
        }
    }
    send_to_websocket_server(_object);
};
/* /main page actions */

/* logging */
var logging = function(message){
    console.log(message);
    var el = document.getElementById("logger_area");
    if (el) {
        let s = new Date().toLocaleString();
        _ = el.innerHTML.substring(0, 10000);
        el.innerHTML = "[" + s + "]" + message.substring(0, 100) + "\n" + _;
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

var toggle_element_view = function(id){
    var el = document.getElementById(id);
    if (el) {
        //~ if (el.style.display == 'block'){
        if (el.style.visibility != "visible"){
            el.style.display = 'block';
            el.style.visibility = "visible";
        } else {
            el.style.display = 'none';
            el.style.visibility = "hidden";
        }
    }
};

/* websocket */
var open_btn_clicked = function () {
    init_wsocket();
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
            logging("send_to_websocket_server() msg_:'" + msg_.substring(0, 120) + "'");
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
    if (ws_on_connect_call_back ) {
        ws_on_connect_call_back();
    }
}

var on_ws_close = function (evt) {
    logging("* ws connection closed *");
    ws_instance = null;
    document.getElementById("open_btn").disabled = false; 
    document.getElementById("open_btn").style.color = "red"; 
    document.getElementById("close_btn").disabled = true; 
    document.getElementById("close_btn").style.color = "grey"; 
}

// augh: e` questa funzione che dovrebbe catturare l'evento websocket.
// qui si dovrebbe estrarre gli elementi e i valori da modificare (v. zim)
// "data" is the json form of the message; 
var on_ws_message = function (evt) {
    try {
        const data = JSON.parse(evt.data);            
            const el = document.getElementById(data.element_id)
            el.style.display = 'block';
            el.style.visibility = "visible";
            // che cosa e` data.paylod?
            el[data.target] = data.payload;
            if (data.class_name) {
                const els = document.getElementsByClassName(data.class_name);
                for (let i = 0; i < els.length; i++) {
                    els[i].style.visibility = "visible";
                    els[i].style.display = 'block';
                };
            }
            logging("on_ws_message() " + data.element_id + ', ' + data.target + ', ' + data.class_name + ', ' + data.payload.substring(0, 120));
    } catch(err) {
        error_handler("err:" + err);
    }
}

var init_wsocket = function (on_connect_call_back) {
    ws_on_connect_call_back = on_connect_call_back;
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

