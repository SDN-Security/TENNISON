    var dummyIpfixThresholddata = 
   {
  "default_ipfix_0": {
    "fields": {
      "sourceIPv4Address": "10.0.0.1"
    },
    "metric": "total_bps",
    "priority": 10,
    "subtype": "prefix",
    "threshold": 1,
    "treatment": "snort_mirror"
  },
  "default_ipfix_1": {
    "fields": {
      "destinationIPv4Address": "10.0.0.1"
    },
    "metric": "total_bps",
    "priority": 10,
    "subtype": "prefix",
    "threshold": 45,
    "treatment": "snort_mirror"
  },
  "default_ipfix_2": {
    "fields": {
      "destinationIPv4Address": "8.8.8.8",
      "sourceIPv4Address": "10.0.0.1"
    },
    "metric": "total_bps",
    "priority": 10,
    "subtype": "prefix",
    "threshold": 1,
    "treatment": "snort_mirror"
  },
  "default_ipfix_3": {
    "fields": {
      "sourceIPv4Address": "10.0.0.20"
    },
    "interval": 10,
    "metric": "delta_bps",
    "priority": 10,
    "subtype": "ipfix",
    "threshold": 10000,
    "treatment": "snort_mirror"
  },
  "shabba" : {
    "subtype": "interfix", 
    "treatment": "snort_mirror", 
    "fields":{
         "sourceIPv4Address": "10.0.0.255"
    },
    "treatment_fields":{
        "sourceIPv4Address": "10.0.0.255"
    },
    "priority": 10,
    "metric": "delta_bps", 
    "threshold": 10000
  }
};

var dummySnortThresholdData = 
    { 
        "supersnort" :{
            "alertmsg": "none", 
            "priority": 40, 
            "treatment": "block", 
            "treatment_fields":{  
                "sourceIPv4Address":"none",
                "sourceTransportPort":32,
                "destinationMacAddress":"none",
                "destinationTransportPort":24,
                "sourceMacAddress":"none",
                "protocolIdentifier":"none",
                "destinationIPv4Address":"none"
            }
        }
    };
    
    
    //ID of the app which will be registered on the NBI API
    var appId = ipfixConfig.appId;
    
    //port used on which either the app is found OR on which the port forwarding is done
    var port = ipfixConfig.port;

    var addr = ipfixConfig.addr;
    
    var fields = ["sourceTransportPort", "destinationTransportPort",
        "sourceIPv4Address","destinationIPv4Address", "protocolIdentifier"];
    
    var treatmentFields = ["sourceTransportPort", "destinationMacAddress",
        "destinationTransportPort", "sourceMacAddress",
        "sourceIPv4Address", "protocolIdentifier",
        "destinationIPv4Address"];
    
    var allPossibleIpfixKeys = ["subtype","treatment","fields","treatment_fields","priority","metric","threshold"];
    
    var allPossibleSnortKeys = ["alertmsg","priority","rule","treatment","treatment_fields"];
    
    var existingThresholdNames = [];
    
    existingThresholdNames["ipfix"] = [];
    
    existingThresholdNames["snort"] = [];
    
    $(document).ready(function() {

        renderThresholds("ipfix");
        renderThresholds("snort");
        
                
        $("#submit_ipfix").click(function(){
            //console.log("1. SOMETHING SUBMITTED");
            var formdata = $("#add_ipfix").serializeArray(); 
            //console.log("ipfix dataToBeAdded : " + JSON.stringify(formdata));
            //var referenceThreshold = (id==="add_ipfix") ? referenceIpFixThreshold:referenceSnortThreshold ;
            var thresholdToSubmit = JSON.parse(JSON.stringify(referenceIpFixThreshold));

            var thresholdName;

            formdata.forEach(function(o){
                //only update values which are not empty and which exist in the threshold to be submitted
                if(o.value){
                    //assign threshold name
                    if(o.name==="ipfix_name"){
                        thresholdName = o.value;
                    }
                    
                    if(o.name.includes("\.")){
                        var key = o.name.split("\.")[0];
                        var subKey = o.name.split("\.")[1];
                        //check if keys and subkeys exist before editing them
                        if(key in thresholdToSubmit && isJson(thresholdToSubmit[key])){
                            thresholdToSubmit[key][subKey] = changeToProperInteger(subKey, o.value, digitIpfixThresholdFields);
                        }
                        //otherwise do nothing
                    }else{
                        if(o.name in thresholdToSubmit){
                            thresholdToSubmit[o.name] = changeToProperInteger(o.name, o.value, digitIpfixThresholdFields);
                        }
                    }
                }
            });
                
            if(existingThresholdNames["ipfix"].includes(thresholdName)){
                console.log("Threshold "+thresholdName+" exists already");
                $("#ipfix_add_alert").css("color","red").html("Threshold "+thresholdName+" exists already").show().delay(5000).fadeOut('slow');
                return;
            }
            
            //console.log("1. "+JSON.stringify(thresholdToSubmit));
            //remove all empty values
            thresholdToSubmit = removeEmptyAttributesFromJsonObject(thresholdToSubmit);
            thresholdToSubmit.fields = removeEmptyAttributesFromJsonObject(thresholdToSubmit.fields);
            thresholdToSubmit.treatment_fields = removeEmptyAttributesFromJsonObject(thresholdToSubmit.treatment_fields);
            
            //console.log("2. "+JSON.stringify(thresholdToSubmit));
            //check if at least one threshold field is inserted
            var thresholdFieldExists = false;
            Object.keys(thresholdToSubmit.fields).forEach(function(key){
                if(thresholdToSubmit.fields[key]==="none" || thresholdToSubmit.fields[key]===-1){
                    //do nothing
                }else{
                    thresholdFieldExists = true;
                }
            });
            
            if(thresholdFieldExists===true){
                //safe to submit here
                submitThreshold("add","ipfix",thresholdName, thresholdToSubmit);
                //renderThresholds("ipfix");
                //add threshold to UI
                $("#ipfix_accordion_parent").append(makeEditableDiv("ipfix",thresholdName,thresholdToSubmit));
            }else{
                $("#alert_ipfix").html("<h3>You must submit atleast 1 threshold field option</h3>").css("color","red").show().delay(5000).fadeOut('slow');
            }

        });
        
        
        $("#submit_snort").click(function(){
            console.log("1. SOMETHING SUBMITTED");
            var formdata = $("#add_snort").serializeArray(); 
            //console.log("snort dataToBeAdded : " + JSON.stringify(formdata));
            //var referenceThreshold = (id==="add_ipfix") ? referenceIpFixThreshold:referenceSnortThreshold ;
            var thresholdToSubmit = JSON.parse(JSON.stringify(referenceSnortThreshold));

            var thresholdName;

            formdata.forEach(function(o){
                //only update values which are not empty and which exist in the threshold to be submitted
                if(o.value){
                    //assign threshold name
                    if(o.name==="snort_name"){
                        thresholdName = o.value;
                    }
                    
                    if(o.name.includes("\.")){
                        var key = o.name.split("\.")[0];
                        var subKey = o.name.split("\.")[1];
                        //check if keys and subkeys exist before editing them
                        if(key in thresholdToSubmit && isJson(thresholdToSubmit[key])){
                            thresholdToSubmit[key][subKey] = changeToProperInteger(subKey, o.value, digitSnortThresholdFields);
                        }
                        //otherwise do nothing
                    }else{
                        if(o.name in thresholdToSubmit){
                            thresholdToSubmit[o.name] = changeToProperInteger(o.name, o.value, digitSnortThresholdFields);
                        }
                    }
                }
                
            });
            

            if(existingThresholdNames["snort"].includes(thresholdName)){
                console.log("Threshold "+thresholdName+" exists already");
                $("#snort_add_alert").css("color","red").html("Threshold "+thresholdName+" exists already").show().delay(5000).fadeOut('slow');
                return;
            }            
            //remove all empty values
            thresholdToSubmit = removeEmptyAttributesFromJsonObject(thresholdToSubmit);
            thresholdToSubmit.treatment_fields = removeEmptyAttributesFromJsonObject(thresholdToSubmit.treatment_fields);
            
            //safe to submit here
            submitThreshold("add","snort",thresholdName, thresholdToSubmit);
            //add threshold to UI
            $("#snort_accordion_parent").append(makeEditableDiv("snort",thresholdName,thresholdToSubmit));
            
        });       
        
        
        /**
        We're defining the event on the `body` element, 
        because we know the `body` is not going away.
        Second argument makes sure the callback only fires when 
        the `click` event happens only on elements marked as `data-editable`
        */
        $('body').on('click', '[data-editable]', function(){

            var $el = $(this);
            var thresholdType = $(this).attr("data-thresholdtype");
            var oldId = $(this).attr("id");
            var oldClass = $(this).attr("class");
            var $input = $('<input id='+oldId+' class="'+oldClass+' form-control" placeholder="none"/>').val( $el.text() );
            $el.replaceWith( $input );

            var save = function(){
                //edit the JSON here
                var thresholdId = oldId.split("___")[0];
                var jsonToBeEdited = JSON.parse( $("#"+thresholdId+"_jsontxt").text() );
                
                //if input value is empty then we should default to a value of "none" and remove the element from the JSON
                var newInputValue = ( $input.val() ) ? $input.val() : "none";
                
                //if it's a JSON object within a JSON object and the details to be edited are in the embedded object
                if(oldId.split("___").length>2){
                    var json_key = oldClass.split("___")[0];
                    var json_subkey = oldClass.split("___")[1];
                    (newInputValue==="none")?delete jsonToBeEdited[json_key][json_subkey]:jsonToBeEdited[json_key][json_subkey] = changeToProperInteger(json_subkey,newInputValue,digitIpfixThresholdFields);
                }else{
                    (newInputValue==="none")?delete jsonToBeEdited[oldClass]:jsonToBeEdited[oldClass] = changeToProperInteger(oldClass,newInputValue,digitIpfixThresholdFields);
                }

                
                //submit the JSON here
                submitThreshold("update",thresholdType, thresholdId, jsonToBeEdited);
                
                //the below then should be done when the JSON has been posted successfully
                $("#"+thresholdId+"_jsontxt").text(JSON.stringify(jsonToBeEdited));
                var $p = $('<span data-thresholdtype="'+thresholdType+'" data-editable id="'+oldId+'" class="'+oldClass+'"/>').text( newInputValue );
                $input.replaceWith( $p );
            };

            /**
              We're defining the callback with `one`, because we know that
              the element will be gone just after that, and we don't want 
              any callbacks leftovers take memory. 
              Next time `p` turns into `input` this single callback 
              will be applied again.
            */
            $input.one('blur', save).focus();

        });
        
        
        $('body').on('click','[data-deletable]', function(){
            //delete thresholds from here
            var thresholdId = $(this).attr("id");
            var thresholdType = $(this).attr("data-thresholdtype");
            
            submitThreshold("remove",thresholdType, thresholdId, {});
            
            $("#collapse"+thresholdId).parent().remove();
            
        });
        
        
    });
    
    
    
    function renderThresholds(thresholdType){
        
        
        //empty div first
        $("#"+thresholdType+"_accordion_parent").empty();
        $("#"+thresholdType+"_accordion_parent").append(makeEmptyAdditionDiv(thresholdType));
        //var data = (thresholdType==="ipfix")?dummyIpfixThresholddata : dummySnortThresholdData ;
        
        $.getJSON("http://"+addr+":"+port+"/tennison/thresholds/"+thresholdType+"/query", function(data){
        //$.getJSON("js/"+thresholdType+"_thresholds.json", function(data){
            //console.log("Data thee" + JSON.stringify(data));
            Object.keys(data).forEach(function(key){
                $("#"+thresholdType+"_accordion_parent").append(makeEditableDiv(thresholdType,key,data[key]));
                existingThresholdNames[thresholdType].push(key);
            });
        
        });
        
    }
    
    
    function getExistingThresholdsByType(thresholdType){
        var thresholdData;
        $.getJSON("http://"+addr+":"+port+"/tennison/thresholds/"+thresholdType+"/query", function(data){
            thresholdData = data;
        });
        return thresholdData;
    }
    
    
    function removeEmptyAttributesFromJsonObject(json){
        Object.keys(json).forEach(function(key){
            //check if it's null first
            if(json[key]){
                if(json[key]==="none" || json[key]===-1 || json[key]==="-1"){
                    delete json[key];
                }
            }else{
                //it's null anyway
                delete json[key];
            }
        });
        
        return json;
    }
    
    
    function submitThreshold(postType,threshold_type, threshold_id, postedData){
                //postType is either "add" OR "update"
        var successful = false;
        var settings = {
          "async": true,
          "crossDomain": true,
          "url": "http://"+addr+":"+port+"/tennison/thresholds/"+threshold_type+"/"+postType+"/"+threshold_id,
          "method": "POST",
          "headers": {
            "content-type": "application/json",
            "cache-control": "no-cache"
          },
          "processData": false,
          "data": JSON.stringify(postedData)
        };

        $.ajax(settings).done(function (response) {
            if(response.success==="ok"){
                successful=true;
                if(postType==="add"){
                    //add threshold to known names so that there will be no threshold with duplicate names registered
                    existingThresholdNames[threshold_type].push(threshold_id);
                }else if(postType==="remove"){
                    //remove threshold name from known names
                    existingThresholdNames[threshold_type].splice(existingThresholdNames[threshold_type].indexOf(threshold_id),1);
                }
            }
            console.log(response);
        });
        return successful;
    }
    
    
    function makeEditableDiv(thresholdType,id,thresholdInfo){
        //get all possible temp keys for the threshold type 
        var tmpPossibleKeys = (thresholdType==="ipfix") ? allPossibleIpfixKeys.slice(0, allPossibleIpfixKeys.length) : allPossibleSnortKeys.slice(0, allPossibleSnortKeys.length) ;
        var thrdiv = 
            //"<h3>"+id+"</h3>"+
            "<pre><code id='"+id+"_jsontxt'>"+JSON.stringify(thresholdInfo)+"</code></pre>"+
            //"<button id='threshold_expand_"+id+"' class='btn btn-primary'>Click edit</button>"+
            "<div id='alert_"+id+"' hidden='hidden'></div>"+
            "<br><br><div id='"+id+"' class='col-xs-3'>";
            Object.keys(thresholdInfo).forEach(function(key){
                var data = thresholdInfo[key];
                if(isJson(data)){
                    thrdiv+="<p>"+key+" : </p>";
                    //for ease of editing and adding new fields while editing, we want to make sure that ALL POSSIBLE fields are there
                    var tmpPossibleFields = (key==="fields") ? fields.slice(0,fields.length) : treatmentFields.slice(0, treatmentFields.length) ;
                    Object.keys(data).forEach(function(subkey){
                        thrdiv+="<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                                +subkey+" : <span id='"+id+"___"+key+"___"+subkey+"' class='"+key+"___"+subkey+"' data-thresholdtype='"+thresholdType+"' data-editable >"+data[subkey]+"</span></p>";
                        tmpPossibleFields.splice(tmpPossibleFields.indexOf(subkey),1);
                    });
                    
                    //now render the remaining replacement fields which do not exist
                    for(index in tmpPossibleFields){
                        remainingSubKey = tmpPossibleFields[index];
                        thrdiv+="<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                                +remainingSubKey+" : <span id='"+id+"___"+key+"___"+remainingSubKey+"' class='"+key+"___"+remainingSubKey+"' data-thresholdtype='"+thresholdType+"' data-editable >none</span></p>";
                    }
                    
                    //remove rendered keys from tmpPossibleKeys so thar you are left with what's not rendered
                    tmpPossibleKeys.splice(tmpPossibleKeys.indexOf(key),1);
                    
                }else{    
                    thrdiv+="<p>"+key+" : <span id='"+id+"___"+key+"' class='"+key+"' data-thresholdtype='"+thresholdType+"' data-editable >"+data+"</span></p>";
                    tmpPossibleKeys.splice(tmpPossibleKeys.indexOf(key),1);
                }
                
            });
            
            for (index in tmpPossibleKeys){
                var remainingKey = tmpPossibleKeys[index];
                if(remainingKey==="fields" || remainingKey==="treatment_fields"){
                    thrdiv+="<p>"+remainingKey+" : </p>";
                    var remainingKeyTmpPossibleFields  = (remainingKey==="fields") ? fields.slice(0,fields.length) : treatmentFields.slice(0, treatmentFields.length) ;
                    for(subIndex in remainingKeyTmpPossibleFields){
                        var subKeyOfRemainingField = remainingKeyTmpPossibleFields[subIndex];
                        thrdiv+="<p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                            +subKeyOfRemainingField+" : <span id='"+id+"___"+remainingKey+"___"+subKeyOfRemainingField+"' class='"+remainingKey+"___"+subKeyOfRemainingField+"' data-thresholdtype='"+thresholdType+"' data-editable >none</span></p>";
                    }
                }else{
                    thrdiv+="<p>"+remainingKey+" : <span id='"+id+"___"+remainingKey+"' class='"+remainingKey+"' data-thresholdtype='"+thresholdType+"' data-editable >none</span></p>";
                }
            }
            
            //render what's left out.
            console.log("left "+tmpPossibleKeys);
            //console.log("OBJ KEYS "+Object.keys(referenceIpFixThreshold));
            
        thrdiv+="<br><input type='button' id='"+id+"' class='btn btn-primary' value ='Remove Threshold' data-thresholdtype='"+thresholdType+"' data-deletable>";
        thrdiv+="</div>";
        return getAccordionElement(thresholdType, id, thrdiv);
    }
    
    
    function getAccordionElement(thresholdType, id, content){
        if(id.includes(" ")){
            id = id.replace(/\s+/g, "_");
        }
        var accordionElement = 
            "<div class='panel panel-default'>"+
                "<div class='panel-heading'>"+
                    "<h4 class='panel-title'>"+
                        "<a data-toggle='collapse' data-parent='#"+thresholdType+"_accordion_parent' href='#collapse"+id+"' aria-expanded='true' class=''>Threshold : "+id+"</a>"+
                    "</h4>"+
                "</div>"+
                "<div id='collapse"+id+"' class='panel-collapse collapse ' aria-expanded='false'>"+
                    "<div class='panel-body'>"+
                    content+
                    "</div>"+
                "</div>"+
            "</div>";

        return accordionElement;
    }
    
    
    function makeEmptyAdditionDiv(thresholdType){
        var additionDiv = "<div id='add_"+thresholdType+"threshold'>"+
            "<form id='add_"+thresholdType+"' action='' method='post' role='form' class='col-xs-4' >";
        additionDiv+="<div class='form-group'>"+
            "<label>Threshold Name</label>"+
            "<input class='form-control' placeholder='none' name='"+thresholdType+"_name' required />"+
            "</div>";
        
        var referenceThreshold = (thresholdType==="ipfix") ? referenceIpFixThreshold:referenceSnortThreshold ;
        var mandatoryFields = (thresholdType==="ipfix") ? mandatoryIpFixThresholdFields:mandatorySnortThresholdFields ;
        Object.keys(referenceThreshold).forEach(function(key){
            var required = "";
            var number = "";
            if (mandatoryFields.includes(key)){
                required="required";
            }
            
            if(isJson(referenceIpFixThreshold[key])){
                Object.keys(referenceIpFixThreshold[key]).forEach(function(subkey){
                    
                if(digitIpfixThresholdFields.includes(subkey)){
                    number = "type='number'";
                }else{
                    number = "";
                }
                    
                    additionDiv+=
                        "<div class='form-group'>"+
                            "<label>"+key+"."+subkey+"</label>"+
                            "<input "+number+"  class='form-control' placeholder='none' name='"+key+"."+subkey+"' />"+
                        "</div>";
                });
            }else{
                if(digitIpfixThresholdFields.includes(key)){
                    number = "type='number'";
                }else{
                    number = "";
                }
                additionDiv+="<div class='form-group'>"+
                            "<label>"+key+"</label>"+
                            "<input "+number+"  class='form-control' placeholder='none' name='"+key+"' "+required+" />"+
                        "</div>";
            }
        });
        
        additionDiv+="<input type='button' id='submit_"+thresholdType+"' class='btn btn-primary' value='ADD "+thresholdType+"'>"+
        "<br><div id='"+thresholdType+"_add_alert' hidden='hidden'></div>";
        additionDiv+="</form></div>";
        
        return getAccordionElement(thresholdType, "ADD A NEW "+thresholdType + " THRESHOLD", additionDiv);
        
    }

    
    function isJson(item) {
        item = typeof item !== "string"
            ? JSON.stringify(item)
            : item;

        try {
            item = JSON.parse(item);
        } catch (e) {
            return false;
        }
        if (typeof item === "object" && item !== null) {
            return true;
        }
        return false;
    }
    
    function changeToProperInteger(key, value, listToCheckAgainst){
        if(listToCheckAgainst.includes(key)){
            return parseInt(value);
        }
        return value;
    }
