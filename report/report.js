$(document).ready(function() {
    makeTables();
});

function makeTables(){
    // fields table 
    $.get('https://raw.githubusercontent.com/cloudmesh/metric/master/report/data-fos.csv', function(csv) {
        populateTable('pubsByField-table', 'Pubs by Field', csv, ['fos', '# of Pubs']);
    });
}

function populateTable(id, title, csv, fields){
    var $div = $('#' + id);
    var $table = $('<table>');
    
    var data = CSV2JSON(csv);
    
    //table title
    if(title){
        $div.append('<h3>' + title + '</h3>');
    }
    
    //get table headers, indexes    
    $row = $('<tr>');
    var header;
    for(var i = 0, max = fields.length; i < max; i++){
        header = fields[i];
        if(fields.indexOf(header) != -1){
            $row.append('<th>' + header + '</th>');
        }
    }
    $table.append($row);
    
    //sort by # of pubs
    data.sort(function(a, b) {
        return b['# of Pubs'] - a['# of Pubs'];
    });
    
    //populate table
    var row;
    var field;
    for(var i = 0, max = data.length; i < max; i++){
        row = data[i];
        $row = $('<tr>');
        for(var j = 0, jmax = fields.length; j < jmax; j++){
            field = fields[j];
            $row.append('<td>' + row[field] + '</td>');
        }
        $table.append($row);
    }
    
    $div.append($table);
}

// state map
$.get('https://raw.githubusercontent.com/cloudmesh/metric/master/report/data-org.csv', function(csv) {
    var json = CSV2JSON(csv.replace('location_state', 'code').replace('# of Pubs','value'));
	var data = collapse_data(json);
  
    Highcharts.mapChart('container', {
        chart: {
            borderWidth: 1
        },

        title: {
            text: 'Number of Publications by State'
        },

        mapNavigation: {
            enabled: true
        },

        colorAxis: {
            min: 1,
            type: 'logarithmic',
            minColor: '#EEEEFF',
            maxColor: '#000022',
            stops: [
                [0, '#EFEFFF'],
                [0.67, '#4444FF'],
                [1, '#000022']
            ]
        },

        series: [{
            data: data,
            mapData: Highcharts.maps['countries/us/us-all'],
            joinBy: ['postal-code', 'code'],
            dataLabels: {
                enabled: true,
                color: '#FFFFFF',
                format: '{point.code}'
            },
            name: 'Scientific Impact',
            tooltip: {
                pointFormat: '{point.code}: {point.value} publication(s)'
            }
        }]
    });
    
    var chartData = CSV2JSON(csv.replace('Organization', 'name').replace('# of Pubs','data'));
    chartData = chartData.map(function(d){
        return {name: d['name'], data: [parseInt(d['data'])]};
    });
    
    chartData.sort(function(a, b){
        return b['data'] - a['data'];
    });
    
    categories = chartData.map(function(d){
        return d['name'];
    })
    
    Highcharts.chart('orgsChart', {
        chart: {
            type: 'bar'
        },
        
        legend: {
            enabled: false
        },
        
        title: {
            text: 'Publications by Organization'
        },
        
        xAxis: {
            categories: categories
        },
        
        yAxis: {
            title: {
                text: 'Publications'
            }
        },
        
        series: chartData
    });
});

/* 
    CSVToArray and CSV2JSON functions from
    user: sturtevant
    url: https://jsfiddle.net/sturtevant/AZFvQ/
    (with minor corrections)
*/

function CSVToArray(strData, strDelimiter) {
    // Check to see if the delimiter is defined. If not,
    // then default to comma.
    strDelimiter = (strDelimiter || ",");
    // Create a regular expression to parse the CSV values.
    var objPattern = new RegExp((
    // Delimiters.
    "(\\" + strDelimiter + "|\\r?\\n|\\r|^)" +
    // Quoted fields.
    "(?:\"([^\"]*(?:\"\"[^\"]*)*)\"|" +
    // Standard fields.
    "([^\"\\" + strDelimiter + "\\r\\n]*))"), "gi");
    // Create an array to hold our data. Give the array
    // a default empty first row.
    var arrData = [[]];
    // Create an array to hold our individual pattern
    // matching groups.
    var arrMatches = null;
    // Keep looping over the regular expression matches
    // until we can no longer find a match.
    while (arrMatches = objPattern.exec(strData)) {
        // Get the delimiter that was found.
        var strMatchedDelimiter = arrMatches[1];
        // Check to see if the given delimiter has a length
        // (is not the start of string) and if it matches
        // field delimiter. If id does not, then we know
        // that this delimiter is a row delimiter.
        if (strMatchedDelimiter.length && (strMatchedDelimiter != strDelimiter)) {
            // Since we have reached a new row of data,
            // add an empty row to our data array.
            arrData.push([]);
        }
        // Now that we have our delimiter out of the way,
        // let's check to see which kind of value we
        // captured (quoted or unquoted).
        if (arrMatches[2]) {
            // We found a quoted value. When we capture
            // this value, unescape any double quotes.
            var strMatchedValue = arrMatches[2].replace(
            new RegExp("\"\"", "g"), "\"");
        } else {
            // We found a non-quoted value.
            var strMatchedValue = arrMatches[3];
        }
        // Now that we have our value string, let's add
        // it to the data array.
        arrData[arrData.length - 1].push(strMatchedValue);
    }
    // Return the parsed data.
    return (arrData);
}

// need js object, not json
function CSV2JSON(csv) {
    var array = CSVToArray(csv);
    var objArray = [];
    for (var i = 1; i < array.length - 1; i++) {
        objArray[i - 1] = {};
        for (var k = 0; k < array[0].length && k < array[i].length; k++) {
            var key = array[0][k];
            objArray[i - 1][key] = array[i][k]
        }
    }

    /*var json = JSON.stringify(objArray);
    var str = json.replace(/},/g, "},\r\n");

    return str;*/
    return objArray;
}

function collapse_data(json){
	obj = {};
    ignore = ['PR', 'VI']
  
	for(var i = 0, max = json.length; i < max; i++){
        item = json[i];
        if(item['code'] && item['value'] && ignore.indexOf(item['code']) == -1){
            if(obj.hasOwnProperty(item['code'])){
                obj[item['code']] += parseInt(item['value']);
            } else {
                obj[item['code']] = parseInt(item['value']);
            }
        }
	}
    
    data = []
    for (var key in obj) {
        if (obj.hasOwnProperty(key)) {
            data.push({code: key, value: obj[key]});
        }
	}
    
    return data;
}
