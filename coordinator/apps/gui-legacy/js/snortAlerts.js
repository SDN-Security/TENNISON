/* 
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */

var addr = ipfixConfig.addr;
var port = ipfixConfig.port;
var snortAlertFields = ["alertmsg","time","pkt"];

$(function(){
    
        $("#snortalerts_accordion_parent").append(renderBaseTimeline());
        $.getJSON("http://"+addr+":"+port+"/tennison/snort/query/"+appId, function(data){
            $("#snortalert_timeline").prepend(prependAlertToTimeline(data));
        });
        
        setInterval(getLatestSnortAlerts, 10000);
    
});


    function getLatestSnortAlerts(){
        $.getJSON("http://"+addr+":"+port+"/tennison/snort/query/"+appId, function(data){
            $("#snortalert_timeline").prepend(prependAlertToTimeline(data));
        });
    }


    function renderBaseTimeline(){
           var timeline = "<div class='bar'></div><div class='timeline' id='snortalert_timeline'></div>";
           return timeline;
    }


    function sortAlerts(){

    }

    function prependAlertToTimeline(finalData){
        console.log(JSON.stringify(finalData));
        var toPrepend;
        Object.keys(finalData).forEach(function(key){

            $.notify("Snort alert");
            toPrepend = "<div class='entry'>"+
            "<table class='table-hover'>"+
            "<thead class='thead-inverse'><tr><th>Property</th><th>Data</th></tr></thead>"+
            "<tbody>"+
            "<tr><td><b>Date</b></td><td>"+new Date(finalData[key].time)+"</td>"+
            "<tr><td><b>Alert</b></td><td>"+finalData[key].alertmsg+"</td>";
            Object.keys(finalData[key].pkt).forEach(function(pktKey){
                toPrepend+="<tbody> <tr><td><b>"+pktKey+"</b> </td> <td>" + finalData[key].pkt[pktKey] + "</td> </tr>";
            });
            toPrepend += "</table>" + "</div>";
        });
        return toPrepend;
    }

