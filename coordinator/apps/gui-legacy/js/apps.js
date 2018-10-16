	//port used on which either the app is found OR on which the port forwarding is done
    var port = ipfixConfig.port;
    var addr = ipfixConfig.addr;

	$(function() {
		getApps();
	});

	function getApps(){
		$.getJSON("http://"+ addr  +":" + port + "/tennison/app/query", function(data){

            $("#app_panel").html('');
	        Object.keys(data).forEach(function(key) {
	        	$("#app_panel").append(appDiv(key, data[key]))

                if (data[key]['status'] != 'not_installed') {
                    getAppConfig(key);
                    getAppLog(key);
                }
	        });
          
        });
    }

    function updateApps(){
        $.getJSON("http://"+ addr  +":" + port + "/tennison/app/query", function(data){

            Object.keys(data).forEach(function(key) {
                updateAppView(key, data[key])

                if (data[key]['status'] != 'not_installed') {
                    getAppConfig(key);
                    getAppLog(key);
                }
            });
            
        });
    }

    function appDiv(key, data){

        var btn = "";
        if (data['status'] == 'active') {
            btn = "<button type='button' id='activate-"+key+"' class='btn btn-danger pull-right' onclick='deactivateApp(\""+key+"\")'>Deactivate</button>";
        } else if (data['status'] == 'not_active') {
            btn = "<button type='button' id='activate-"+key+"' class='btn btn-success pull-right' onclick='activateApp(\""+key+"\")'>Activate</button>";
        } else {
            btn = "<button type='button' id='activate-"+key+"' class='btn btn-default pull-right' disabled='true'>Not installed</button>";
        }

    	var div = 
            "<div class='panel panel-default'>"+
                "<div class='panel-heading clearfix'>"+
                    "<h4 class='panel-title pull-left'>"+
                        "<a data-toggle='collapse' href='#collapse"+key+"' aria-expanded='true' class=''>" + key + "</a>"+
                    "</h4>"+
                    btn+
                "</div>"+
                "<div id='collapse"+key+"' class='panel-collapse collapse ' aria-expanded='false'>"+
                    "<div class='panel-body'><h4>Status</h4><pre id='status-"+key+"'>"+
                    		JSON.stringify(data, null, 2)+
                    "</pre></div>"+
                    "<div class='panel-body'><h4>Config</h4><pre id='config-"+key+"'>"+
                    "</pre></div>"+
                    "<div class='panel-body'><h4>Log</h4><pre id='log-"+key+"'>"+
                    "</pre></div>"+
                "</div>"+
            "</div>";
		return div;
    }

    function activateApp(app){
        console.log("Starting app " + app);
        $.post("http://" +addr+":" + port + "/tennison/app/start/" + app, function(data){
            console.log(data);
            updateApps();
        });
    }

    function deactivateApp(app){
        console.log("Stopping app " + app);
        $.post("http://"+addr+":" + port + "/tennison/app/stop/" + app, function(data){
            console.log(data);
            updateApps();
        });
    }

    function updateAppView(app, data){

        // Update JSON
        $('#status-'+app).html(JSON.stringify(data, null, 2));

        // Update button
        if (data['status'] == 'active') {
            $('#activate-'+app).html('Deactivate');
            $('#activate-'+app).removeClass('btn-success');
            $('#activate-'+app).addClass('btn-danger');
            $('#activate-'+app).attr('onclick', 'deactivateApp("'+app+'")');    
        } else if (data['status'] == 'not_active') {
            $('#activate-'+app).html('Activate');
            $('#activate-'+app).removeClass('btn-danger');
            $('#activate-'+app).addClass('btn-success'); 
            $('#activate-'+app).attr('onclick', 'activateApp("'+app+'")');    
        }
    }

    function getAppConfig(app){
        $.getJSON("http://"+addr+":" + port + "/tennison/app/query/" + app + "/config", function(data){
            $('#config-'+app).html(JSON.stringify(data, null, 2));
        });
    }

    function getAppLog(app){
        $.getJSON("http://"+addr+":" + port + "/tennison/app/query/" + app + "/log", function(data){
            $('#log-'+app).html(data['log']);
        });
    }
