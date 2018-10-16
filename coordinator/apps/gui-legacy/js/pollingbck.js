    //stores ALL sorts, by threshold key as they primary key. On the secondary level of the 
    //multidimentional array it stores the switch origin, which helps determine what switch to get information from.
    //On that leve it also stores information for each flow for the threshold key in context.
    var ipfixFlowSignatures = [];
    
    //Stores flows whose plotting information/data already exists in the array containers
    var alreadyPlotted = [];
    
    //stores the (random) colour for each flow
    var fillColours = [];
    
    //stores the plotting data, this array will be directly fed into flot to plot the data
    var plottingData = [];
    
    //stores the ipfix object source so as to prevent duplicate ipfix information from another switch in the network
    var ipfixObjectSource = [];
    
    //ID of the app which will be registered on the NBI API
    var appId = ipfixConfig.appId;
    
    //port used on which either the app is found OR on which the port forwarding is done
    var port = ipfixConfig.port;

    var addr = ipfixConfig.addr;   
 
    //converts the metric from milliseconds to seconds.
    var toPerSecond = 1000;
    
    //The inversion converts from bytes to megabytes
    var toMegaBytes = 1000000;
    
    //stores the total number of flows per threshold
    var totalFlows = [];
    
    var thresholdsData;
    
    //stores a boolean indicating if the/a flow is exceeding the set threshold
    var flowsExceedingThreshold = [];
    
    var existingIpfixThresholdDivs = [];
    
    var mostRecentPlottedTime = [];
    
    //CSS for the tooltips on the interactive chart
    $(function() {
        /*
    //test class C
    console.log(checkIfIPInSubnetRange("192.168.1.100","192.168.1.16/29")===false);
    console.log(checkIfIPInSubnetRange("192.168.1.100","192.168.1.96/29")===true);
    console.log(checkIfIPInSubnetRange("192.168.1.1","192.168.1.0/29")===true);
    console.log(checkIfIPInSubnetRange("192.168.1.24","192.168.1.16/29")===false);
    console.log(checkIfIPInSubnetRange("192.168.1.24","192.168.1.24/29")===true);
    
    //test class B
    console.log(checkIfIPInSubnetRange("111.168.1.24","111.168.0.0/21")===true);
    console.log(checkIfIPInSubnetRange("111.168.1.35","111.168.3.0/21")===true);
    console.log(checkIfIPInSubnetRange("111.168.9.44","111.168.0.0/21")===false);
    console.log(checkIfIPInSubnetRange("111.168.8.71","111.168.0.0/21")===false);
    console.log(checkIfIPInSubnetRange("111.168.248.44","111.168.240.0/21")===false);
    console.log(checkIfIPInSubnetRange("111.168.247.255","111.168.240.0/21")===true);
    
    //test class A
    console.log(checkIfIPInSubnetRange("168.1.24.0","168.0.0.0/13")===true);
    console.log(checkIfIPInSubnetRange("168.1.35.3","168.3.0.0/13")===true);
    console.log(checkIfIPInSubnetRange("168.9.44.3","168.0.0.0/13")===false);
    console.log(checkIfIPInSubnetRange("168.8.71.7","168.0.0.0/13")===false);
    console.log(checkIfIPInSubnetRange("168.248.44.5","168.240.0.0/13")===false);
    console.log(checkIfIPInSubnetRange("168.247.255.3","168.240.0.0/13")===true);
       */ 
        
        $("<div id='tooltip'></div>").css({
            position: "absolute",
            display: "none",
            border: "1px solid #fdd",
            padding: "2px",
            "background-color": "#fee",
            opacity: 0.80
        }).appendTo("body");
        
        //register the APP
        $.post("http://"+addr+":"+port+"/tennison/app/register/"+appId, function(data, status){
            console.log("Data: " + data + "\nStatus: " + status);
            if(status != "success")
               $.notify("Failed to connect to coordinator", "error");
        });
        
        //TODO - get the existing thresholds. Probably need to get this all the time as well 
        //since they may change in real time in the future
        setInterval(getThresholds, 1000);

        if(getURLParameter("disable_graphs") == "true"){
             $.notify("Warning: graphs have been disabled!", "warn");
             console.log("Graphs not updated because graphs disabled selected");
             return;
        }
        else{
        //Calls the function that polls for data every X milliseconds
        setInterval(getLatestIPFixFLows, 10000);}

    });


    function getThresholds(){
        
            //$.getJSON("js/thresholds.json", function(data){
            $.getJSON("http://"+addr+":"+port+"/tennison/thresholds/ipfix/query", function(data){
                console.log("THRESHOLDS : " + JSON.stringify(data));
                thresholdsData = data;
            Object.keys(data).forEach(function(key) {
                
                if(!existingIpfixThresholdDivs.includes(key)){
                    $.notify("New IPFIX threshold found", "info");
 
                    //make a DIV for each threshold and in here you
                    // will put the corresponding threshold table
                    $("#accordion").append(
                            renderDivs(
                                key,
                                thresholdInfoDiv(data[key],key)
                            )
                        );
                    ipfixFlowSignatures[key] = [];
                    fillColours[key] = [];
                    //total flows per threshold
                    totalFlows[key] = 0;
                    //for tracking if it might exceed the thresholds, total is the number of flows e
                    flowsExceedingThreshold[key] = [];
                    flowsExceedingThreshold[key]["total"] = 0;
                    
                    //adding a new div into the list
                    existingIpfixThresholdDivs.push(key);
                }
            });
            
        });
    }
    
    /**
     * Renders the DIVS that are needed for each threshold to be monitored
     * @param {type} flotDivId
     * @param {type} dataHeading
     * @param {type} accordion
     * @returns {String}
     */
    function renderDivs(key,accordion){
        var flotDivId = key+"_flot";
        var thresholdDiv = 
                "<div class='col-lg-3'>"+
                    "<div class='panel'>"+
                        "<!-- /.panel-heading -->"+
                        "<div class='panel-body'  style='width:100%;height:300px'>"+
                        "<div class='panel-group'>"+accordion+"</div>"+
                      "  </div>"+
                     "   <!-- /.panel-body -->"+
                    "</div>"+
                    "<!-- /.panel -->"+
                "</div>";
        
        var flotDiv = 
                "<div class='col-lg-9'>"+
                    "<div class='panel'>"+
                        "<div class='panel-body' id="+flotDivId+" style='width:100%;height:500px'>"+
                            //chart comes here
                      "  </div>"+
                     "   <!-- /.panel-body -->"+
                    "</div>"+
                    "<!-- /.panel -->"+
                "</div> ";
        
        var legendKeysDiv =                    
                "<div class='col-lg-12'>"+
                "<div class='panel'>"+
                        "<div class='panel-body'>"+
                      "<div id='"+flotDivId+"_legend'></div>"+
                                            "  </div>"+
                     "   <!-- /.panel-body -->"+
                                          "</div>"+
                    "<!-- /.panel -->"+
                "</div> ";
        
        var accordionElement = 
                "<div class='panel panel-default'>"+
                    "<div class='panel-heading'>"+
                        "<h4 class='panel-title'>"+
                            "<a data-toggle='collapse' data-parent='#accordion' href='#collapse"+flotDivId+"' aria-expanded='true' class=''>Threshold : "+key+"</a>"+
                        "</h4>"+
                    "</div>"+
                    "<div id='collapse"+flotDivId+"' class='panel-collapse collapse ' aria-expanded='false'>"+
                        "<div class='panel-body'>"+
                        flotDiv + thresholdDiv + "<br>"+legendKeysDiv+"<br>"+"<br><br><hr>"+
                        "</div>"+
                    "</div>"+
                "</div>";
        
        
        return accordionElement;
    }
    
    
    /**
     * Not using an accordion anymore really. Renders a div that shows live information on the threshold and its flows
     * @param {type} thresholdInfo
     * @param {type} thresholdDivId
     * @returns {String}
     */
    function thresholdInfoDiv(thresholdInfo, thresholdDivId){
        var thr = ("threshold" in thresholdInfo) ? thresholdInfo.threshold/toMegaBytes : "not set";
        var accordion = 
                    "<div class='panel-body'>"+
                    "<b>Flows Active :</b> <span id = '"+thresholdDivId+"_active'></span><br><br>" +
                    "<b>Exceeding Threshold :</b> <span id = '"+thresholdDivId+"_exceeding'>0</span><br><br>" +
                    "<b>Threshold :</b> <span id = '"+thresholdDivId+"_current_threshold'>" + thr + "</span> MBytes/s<br><br>" +
                    "<b>Treatment :</b> <span id = '"+thresholdDivId+"_current_treatment'>" + thresholdInfo.treatment + "</span><br>" +
                    "</div>";
        return accordion;
    }
    
    /**
     * Adds legend keys for the corresponding chart
     * @param {type} thresholdId ID of the threshold whose chart one is getting legend keys for
     * @param {type} objectId Unique flow ID
     * @param {type} legendColor Colour of Unique flow ID on the chart
     * @param {type} action Boolean that indicated whether one is to add/remove the legend key
     * @returns {undefined}
     */
    function addLegendObjects(thresholdId, objectId, legendColor, action){
        if(action===true){
            //add legend key
            $("#"+thresholdId+"_flot_legend")
                    .append("<p id='"+objectId+"'><span class='legendcolors' style='background:"+legendColor+"'></span> : "+objectId+"</p>");
        }else{
            //remove legend key
            $("p").remove("#"+objectId);
        }
    }
    
    /**
     * Generates random colour for the flow on the chart. Let's hope on demo day it doesn't generate #FFFFFF :-)
     * @returns {String} Colour for the flow.
     */
    function generateRandomColour(){
        var result = '';
        var chars = "0123456789abcdef";
        for (var i = 6; i > 0; --i) result += chars[Math.floor(Math.random() * chars.length)];
        return "#"+result;
    }
    
    function updateThresholdInfoDiv(thresholdObject, key){
                //if threshold doesnt have a thresold limit, return with 0;
        if(("threshold" in thresholdObject)){
            //convert the threshold to Mbytes for fair comparison to throughput
            var thresholdInMbps = thresholdObject.threshold;
            if(thresholdObject.threshold > 0){
                thresholdInMbps = thresholdObject.threshold/toMegaBytes;
            }

            //update the thresholdInfo div with the current threshold
            $("#"+key+"_current_threshold").html(thresholdInMbps);
        }else{
            $("#"+key+"_current_threshold").html("Not set");
        }
        
        
        if(thresholdObject.treatment){
            $("#"+key+"_current_treatment").html(thresholdObject.treatment);
        }
        
        
    }
    
    function updateActiveFlowCount(){
        console.log("=======================****========================");
        console.log(mostRecentPlottedTime);
        for(thresholdId in mostRecentPlottedTime){
            for(uniqueFlowKey in mostRecentPlottedTime[thresholdId]){
                console.log(mostRecentPlottedTime[thresholdId][uniqueFlowKey]);
                if(new Date().getTime() - mostRecentPlottedTime[thresholdId][uniqueFlowKey] >= ipfixConfig.flowActiveDuration 
                        && mostRecentPlottedTime[thresholdId][uniqueFlowKey]!==0){
                    
                    //var currentCount = parseInt($("#"+thresholdId+"_active").html());
                    if(totalFlows[thresholdId]>0){
                        totalFlows[thresholdId]-=1;
                        $("#"+thresholdId+"_active").html(totalFlows[thresholdId]);
                        //$("#"+thresholdId+"_active").html(currentCount-1);
                        mostRecentPlottedTime[thresholdId][uniqueFlowKey] = 0;
                    }
                }
            }
        }
        console.log("=======================**========================");
        console.log(mostRecentPlottedTime);
    }
    

    /**
     * Updates the exceeding flows on the chart
     * @param {type} thresholdObject
     * @param {type} key
     * @param {type} uniqueFlowKey
     * @param {type} throughput
     * @returns {undefined}
     */
    function updateTotalExceedingFlows(thresholdObject, key, uniqueFlowKey, throughput){
        
        //if threshold doesnt have a thresold limit, return
        if(!("threshold" in thresholdObject)){
            return;
        }
        
        //convert the threshold to Mbytes for fair comparison to throughput
        var thresholdInMbps = thresholdObject.threshold;
        if(thresholdObject.threshold > 0){
            thresholdInMbps = thresholdObject.threshold/toMegaBytes;
        }
        
        //update the thresholdInfo div with the current threshold
        ///$("#"+key+"_current_threshold").html(thresholdInMbps);
        
        //if there's no record of this flow being put against the threshold then make it false
        if (typeof flowsExceedingThreshold[key][uniqueFlowKey] === 'undefined') {
            flowsExceedingThreshold[key][uniqueFlowKey] = false;
        }
        
        if(flowsExceedingThreshold[key][uniqueFlowKey]===true && (throughput > thresholdInMbps)){
            //do nothing...
        }else if(flowsExceedingThreshold[key][uniqueFlowKey]===false && (throughput > thresholdInMbps)){
            flowsExceedingThreshold[key][uniqueFlowKey]=true;
            flowsExceedingThreshold[key]["total"]+=1;
            $("#"+key+"_exceeding").html(flowsExceedingThreshold[key]["total"]);
        }else if(flowsExceedingThreshold[key][uniqueFlowKey]===false && (throughput <= thresholdInMbps)){
            //do nothing
        }else{
            flowsExceedingThreshold[key][uniqueFlowKey]=false;
            if(flowsExceedingThreshold[key]["total"]>0){
                flowsExceedingThreshold[key]["total"]-=1;
                $("#"+key+"_exceeding").html(flowsExceedingThreshold[key]["total"]);
            }
        }
        /*
        console.log("UniK: "+uniqueFlowKey+" Original Threshold : "+thresholdObject.threshold 
        + " Megabyte Converted : "+thresholdInMbps 
        + " Throughput : "+ throughput
        + " FLT Set : " + flowsExceedingThreshold[key][uniqueFlowKey]);
        */
    }
    
    function checkIfIPInSubnetRange(ip, range){
        //let's check the range first
        var subnetInfo = range.split("/");
        var subnet = subnetInfo[0];
        var subnetLength = parseInt(subnetInfo[1]) - ( (Math.floor(parseInt(subnetInfo[1])/8))*8 );
        var hostsExponentialIndex = 8 - subnetLength;
        var hostsTotal = Math.pow(2, hostsExponentialIndex);
        var octetToDealWith = Math.floor(parseInt(subnetInfo[1])/8);
        
        ipOctets = ip.split("\.");
        subnetClassBits = subnet.split("\.");
        //calculates the range start according to the appropriate octet OR IP address class (A, B, C)
        var rangeStart = Math.floor(parseInt(subnetClassBits[octetToDealWith]) / hostsTotal) * hostsTotal;

        rangeStart = Math.floor(parseInt(subnetClassBits[octetToDealWith]) / hostsTotal) * hostsTotal;
        //console.log("IP : " + ip + "  - Range : " + range);
        if(rangeStart===0){
            //range is x.x.x.0 - x.x.x.hostsTotal OR x.x.0.x - x.x.hostsTotal.255  : ..... etc
            //check if IP is in that range
            return parseInt(ipOctets[octetToDealWith]) < hostsTotal;
        }else{
            var unreachableEnd = rangeStart + hostsTotal;
            return (parseInt(ipOctets[octetToDealWith]) >=rangeStart) && (parseInt(ipOctets[octetToDealWith]) < unreachableEnd);
        }
    }
    
    function ipAddressIsARange(range){
        return range.includes("/");
    }

    function getURLParameter(name) {
    return decodeURIComponent((new RegExp('[?|&]' + name + '=' + '([^&;]+?)(&|#|;|$)').exec(location.search) || [null, ''])[1].replace(/\+/g, '%20')) || null;
    }	

    function getLatestIPFixFLows(){
        if(getURLParameter("disable_graphs")){
             $.notify("Warning, graphs have been disabled!");
             console.log("Graphs not updated because graphs disabled selected");
             return;
        }
        console.log("getting IPfix flows every 10 seconds");
        /**
         * General options for the chart
         * @type type
         */

        
        var options = {
			series: {
				shadowSize: 0,
                                stack: false,

			},
                        legend:{position:"nw"},
                        //points: { show: true },
                        yaxis: {
                            color: "black",
                            axisLabel: "Throughput (MB/s)",
                            axisLabelUseCanvas: true,
                            axisLabelFontSizePixels: 12,
                            axisLabelFontFamily: 'Verdana, Arial',
                            axisLabelPadding: 3
                        },
                        xaxis: {
                            mode: "time",
                            tickSize: [plotConfig.axisIntervalsInMinutes, "minute"],
                            tickLength: 10,
                            color: "black",
                            axisLabel: "Time",
                            axisLabelUseCanvas: true,
                            axisLabelFontSizePixels: 12,
                            axisLabelFontFamily: 'Verdana, Arial',
                            axisLabelPadding: 10
                        },
                        
                        grid: {
                            hoverable: true,
                            clickable: true,
                            borderWidth: 2,        
                            backgroundColor: { colors: ["#EDF5FF", "#ffffff"] }
                        }
		};
        
        
        //look for new divs to put in
        getThresholds();

        updateActiveFlowCount();

        $.getJSON("http://"+addr+":"+port+"/tennison/ipfix/query/"+appId, function(data){
            //loop through the Data to see if there's any matching ipfix data with each loop
            Object.keys(data).forEach(function(ipfixKey) {
                var ipfixObject = data[ipfixKey];

                //console.log("ipfixKey : " + ipfixKey + JSON.stringify(ipfixObject));
                //check if churned out data matches any thresholds
                Object.keys(thresholdsData).forEach(function(key) {
                    
                    //update thresholdInfo div
                    updateThresholdInfoDiv(thresholdsData[key], key);
                    
                    var thresholdObject = thresholdsData[key];
                    var fullThresholdFieldsMatch = 0; // if all fields of an IPFix match then this should remain at 0
                    Object.keys(thresholdObject.fields).forEach(function(fkey){
                        //check specifically for IP ranges in source and destination IP fields of the threshold
                        if((fkey === "sourceIPv4Address" || fkey === "destinationIPv4Address") && ipAddressIsARange(thresholdObject.fields[fkey])){
                             if(fkey in ipfixObject && checkIfIPInSubnetRange(ipfixObject[fkey],thresholdObject.fields[fkey])){
                                //do nothing, match found
                            }else{
                                fullThresholdFieldsMatch++;
                            } 
                        }else{
                             if(fkey in ipfixObject && thresholdObject.fields[fkey]===ipfixObject[fkey]){
                                //do nothing, match found
                            }else{
                                fullThresholdFieldsMatch++;
                            }                           
                        }
                    }); 

                    //unique key for each flow - made from dstIp:dstPort & srcIp:srcPort
                    var uniqueFlowKey  = key + " D="+ipfixObject.destinationIPv4Address +":"+ ipfixObject.destinationTransportPort +" " +
                            "S="+ipfixObject.sourceIPv4Address +":"+ ipfixObject.sourceTransportPort;
                   
                   //logic to check if the switch we are using for information is not a duplicate information source
                    if(!(uniqueFlowKey in ipfixObjectSource)){
                        ipfixObjectSource[uniqueFlowKey] = ipfixObject.exporterIPv6Address;
                    }else{
                        if(ipfixObjectSource[uniqueFlowKey] !== ipfixObject.exporterIPv6Address){
                            return;
                        }
                    }
                   
                    //If the threshold matches the ipfix object and IPFix object hasn't already been plotted
                    if(fullThresholdFieldsMatch===0 && !((key+ipfixKey) in alreadyPlotted)){
                        //ALL the thresholds of this ipfix theshold have been matched by the current IPFix object
                        //draw charts in the respective DIV

                        var dataHolder = {};
                        if(!(uniqueFlowKey in ipfixFlowSignatures[key])){
                            if(!(key in plottingData) ){
                                plottingData[key] = [];
                            }
                            
                            if(!(key in mostRecentPlottedTime) ){
                                mostRecentPlottedTime[key] = [];
                            }
                            //initialising it because I don't know how to declare it :-(
                            mostRecentPlottedTime[key][uniqueFlowKey] = new Date().getTime();
                            
                            ipfixFlowSignatures[key][uniqueFlowKey] = [];
                            ipfixFlowSignatures[key]["sourceSwitch"] = [];
                            ipfixFlowSignatures[key]["sourceSwitch"][uniqueFlowKey] = ipfixObject.exporterIPv6Address;
                            if(!("lastMeasuredOctet" in ipfixFlowSignatures[key])){
                                ipfixFlowSignatures[key]["lastMeasuredOctet"] = [];
                            }
                            ipfixFlowSignatures[key]["lastMeasuredOctet"][uniqueFlowKey] = [];
                            fillColours[uniqueFlowKey] = generateRandomColour();
                            dataHolder['label'] = uniqueFlowKey;
                            //new flow, update the totals to reflect an additional flow
                            totalFlows[key]+=1;
                            $("#"+key+"_active").html(totalFlows[key]);
                            addLegendObjects(key,uniqueFlowKey,fillColours[uniqueFlowKey],true);
                            
                            //add a unique flow ID and its last plotted time, so that we can decrease flows
                        }

                        var thresholdDataHolder = {};
                        if(!(key in ipfixFlowSignatures[key])){
                            ipfixFlowSignatures[key][key] = []; //stores the threshold data
                            thresholdDataHolder['label'] = "Threshold level";
                            addLegendObjects(key,"Threshold","#000000",true);
                            
                            
                        }
                        
                        var signaturesSize = ipfixFlowSignatures[key][uniqueFlowKey].length;
                        
                        //stores lastMeasuredOctetCount
                        var lastSignatureMeasuredOctetArray = ipfixFlowSignatures[key]["lastMeasuredOctet"][uniqueFlowKey].length;
                        
                        //stores the last given octet count
                        var lastMeasuredOctetCount;
                        //console.log("My size is : "+signaturesSize + " lastoctetCOntainerSize = " + lastSignatureMeasuredOctetArray);
                        var lastSignature;
                        var dataToPlot;
                        var flowendTimeDifference;
                        var throughput;
                        if(signaturesSize > 0){
                            lastMeasuredOctetCount = ipfixFlowSignatures[key]["lastMeasuredOctet"][uniqueFlowKey][lastSignatureMeasuredOctetArray-1];
                            lastSignature = ipfixFlowSignatures[key][uniqueFlowKey][signaturesSize-1];
                            //console.log("Last Signature : " +lastSignature + " : lastOctetCount : " + lastMeasuredOctetCount);
                            var octetCountDifference = ipfixObject["octetDeltaCount"] - lastMeasuredOctetCount;
                            
                            //if latest octetCount from IPFIX is smaller than the lastPlotted one 
                            //then there must have been a restart of the flow with the same signature
                            if(ipfixObject["octetDeltaCount"] < lastMeasuredOctetCount){
                                octetCountDifference = ipfixObject["octetDeltaCount"];
                            }
                            
                            flowendTimeDifference = new Date(ipfixObject.flowEndMilliseconds).getTime() - lastSignature[0];
                            throughput = (toPerSecond/toMegaBytes) * (octetCountDifference / flowendTimeDifference);
                            dataToPlot = [new Date(ipfixObject.flowEndMilliseconds).getTime(), throughput];
                            ipfixFlowSignatures[key]["lastMeasuredOctet"][uniqueFlowKey].push(ipfixObject["octetDeltaCount"]);
                            
                            //update span for flows going over the thresholds
                            updateTotalExceedingFlows(thresholdObject, key, uniqueFlowKey, throughput);
                            
                        }else{
                            if(new Date(ipfixObject.flowEndMilliseconds).getTime() > new Date(ipfixObject.flowStartMilliseconds).getTime()){
                                flowendTimeDifference = new Date(ipfixObject.flowEndMilliseconds).getTime() - new Date(ipfixObject.flowStartMilliseconds).getTime();
                                console.log("FLOWTIMEDIFF" + flowendTimeDifference);
                                throughput = (toPerSecond/toMegaBytes) * (ipfixObject["octetDeltaCount"] / flowendTimeDifference);
                                dataToPlot = [new Date(ipfixObject.flowEndMilliseconds).getTime(),throughput];
                                ipfixFlowSignatures[key]["lastMeasuredOctet"][uniqueFlowKey].push(ipfixObject["octetDeltaCount"]);
                            
                                //update span for flows going over the thresholds
                                updateTotalExceedingFlows(thresholdObject, key, uniqueFlowKey, throughput);
                                
                            }else{
                                dataToPlot = [new Date(ipfixObject.flowEndMilliseconds).getTime(),0];
                                ipfixFlowSignatures[key]["lastMeasuredOctet"][uniqueFlowKey].push(0);
                            }
                        }
                        
                        mostRecentPlottedTime[key][uniqueFlowKey] = new Date(ipfixObject.flowEndMilliseconds).getTime();
                        //console.log("Data To plot " + dataToPlot +": Current OctetCount :" + ipfixObject["octetDeltaCount"]);
                        
                        
                        if(ipfixObject.subtype==="interfix"){
                            ipfixFlowSignatures[key][uniqueFlowKey].push(
                                //[new Date(ipfixObject.flowEndMilliseconds).getTime(),ipfixObject["octetDeltaCount"]]
                                dataToPlot
                            );                            
                        }else if(ipfixObject.subtype==="prefix"){
                            ipfixFlowSignatures[key][uniqueFlowKey].push(
                                [new Date(ipfixObject.flowStartMilliseconds).getTime(),0], //start of a flow
                                //[new Date(ipfixObject.flowEndMilliseconds).getTime(),ipfixObject["octetDeltaCount"]]
                                dataToPlot
                            );
                        }else{
                            ipfixFlowSignatures[key][uniqueFlowKey].push(
                                //[new Date(ipfixObject.flowEndMilliseconds).getTime(),ipfixObject["octetDeltaCount"]],
                                dataToPlot,
                                [new Date(ipfixObject.time).getTime(),0] //why 0? Because the flow has ended and the area should reflect so
                            );    
                        }

                        //also sort out plotting for the threshold line
                        ipfixFlowSignatures[key][key].push([new Date(ipfixObject.flowEndMilliseconds).getTime(), thresholdObject.threshold/toMegaBytes]);

                        dataHolder['lines'] = {show:true, fill:true};
                        //dataHolder['points'] = {show:true};
                        dataHolder['color'] = fillColours[uniqueFlowKey];
                        dataHolder['data'] = ipfixFlowSignatures[key][uniqueFlowKey];

                        //get threshold data as well to put on the graph
                        thresholdDataHolder['lines'] = {show:true, steps:true};
                        //thresholdDataHolder['points'] = {show:true};
                        thresholdDataHolder['color'] = "#000000";
                        thresholdDataHolder['data'] =  ipfixFlowSignatures[key][key];
                        //console.log(thresholdDataHolder);
                        //console.log("====================");
                        //console.log(dataHolder);
                        //console.log("====================");
                        plottingData[key].push(dataHolder,thresholdDataHolder);
                        alreadyPlotted[key+ipfixKey] = [ipfixKey];


                        //===================TOOLTIPS====================//
                        $.fn.UseTooltip = function () {
                            $(this).bind("plothover", function (event, pos, item) {
                                if (item) {
                                        var x = item.datapoint[0],
                                                y = item.datapoint[1].toFixed(3);

                                        $("#tooltip").html( new Date(x) + " <br>Throughput : " + y + "MBytes/s")
                                                .css({top: item.pageY+5, left: item.pageX+5})
                                                .fadeIn(200);
                                } else {
                                        $("#tooltip").hide();
                                }
                            });
                        };
                        //================================================//

                        $.plot($('#'+key+'_flot'), plottingData[key], options);
                        $('#'+key+'_flot').UseTooltip();
                    }

                });

            });

        });
    }
